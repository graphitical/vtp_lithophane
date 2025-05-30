import re
import sys

import numpy as np

coords_regex = r'([XYZEF])(-?\d+\.?\d+)'
vtp_regex = r"V\*.*?(-?\d+\.?\d+).*?H\*.*?(-?\d+\.?\d+)"
alpha_regex = r".*?alpha\)? = (\d+\.?\d*)"
Edot_regex = r".*?Edot\)? = (\d+\.?\d*)"
diam_regex = r".*?[dD]iameter = (\d+\.?\d+)"


class Point3D:
    """
    A barebones 3D point class that can be converted to a numpy array.
    Useful for tracking positions in G-code validation.
    Supports X, Y, Z coordinates and can be used in numpy operations.
    Supports addition and subtraction with another Point2D instance.
    """

    def __init__(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z

    def __array__(self, dtype=np.float64, copy=True):
        arr = np.array([self.x, self.y, self.z], dtype=dtype)
        return arr.copy() if copy else arr

    def __repr__(self):
        return f"Point3D({self.x:.2f}, {self.y:.2f}, {self.z:.2f})"

    def copy(self):
        return Point3D(self.x, self.y, self.z)

    def __add__(self, other):
        return Point3D(self.x+other.x, self.y+other.y, self.z+other.z)

    def __sub__(self, other):
        return Point3D(self.x-other.x, self.y-other.y, self.z-other.z)


def main(args):
    if not args:
        print("Error: No filename provided.")
        sys.exit(1)

    fname = args[0]
    verbose = False
    if len(args) == 2 and args[1].lower() in ['-v', '--verbose']:
        verbose = True
    D_F = None
    D_N = None
    alpha = None
    Edot = None
    try:
        with open(fname) as f:
            lines = [line for line in f if line]
    except FileNotFoundError:
        print(f"Error: File '{fname}' not found.")
        sys.exit(1)

    datas = []
    for idx, line in enumerate(lines, 1):
        line = line.strip()
        if 'G1' in line or 'G0' in line:
            d = {'type': 'G1' if 'G1' in line else 'G0'}
            coord_matches = re.findall(coords_regex, line)
            d |= {k: float(v) for k, v in coord_matches}
            vtp_matches = re.findall(vtp_regex, line)
            if len(vtp_matches) == 1:
                d |= {'V*': float(vtp_matches[0][0]),
                      'H*': float(vtp_matches[0][1])}
            Edot_matches = re.search(Edot_regex, line)
            if Edot_matches:
                d |= {'Edot': float(Edot_matches.group(1))}
            datas.append(d | {'raw': line.strip(), 'line_num': idx})
        if 'alpha' in line:
            alpha_match = re.search(alpha_regex, line)
            if alpha_match:
                alpha = float(alpha_match.group(1))
                print(f"Found alpha to be {alpha:.2f}")
        if 'diameter' in line.lower():
            diam_match = re.search(diam_regex, line)
            if diam_match:
                if 'filament' in line.lower():
                    t = float(diam_match.group(1))
                    print(
                        f"Found filament diameter to be {t:.2f}")
                    D_F = t
                elif 'nozzle' in line.lower():
                    t = float(diam_match.group(1))
                    print(f"Found nozzle diameter to be {t:.2f}")
                    D_N = t
        if 'Edot' in line and 'V*' not in line:
            Edot_match = re.search(Edot_regex, line)
            if Edot_match:
                Edot = float(Edot_match.group(1))
                print(f"Found Edot to be {Edot:.3f}")

    current_pos = Point3D(0., 0., 0.)
    next_pos = Point3D(0., 0., 0.)
    current_F = 0.

    if not D_F or not D_N or not alpha or not Edot:
        print("Error: Missing required parameters in gcode (D_F, D_N, alpha, Edot).")
        sys.exit(1)

    A_F = np.pi * (D_F/2.)**2
    A_T = np.pi * (alpha*D_N/2.)**2

    all_pass = True
    failures = []
    for data in datas:
        is_close_line = True
        line_failures = {}
        # update command state, includes G0 and G1 commands
        next_pos, new_F = update_command_state(verbose, next_pos, data)
        if new_F is not None:
            current_F = new_F
            if verbose:
                print(
                    f"Line {data['line_num']} updated feedrate to {current_F:.2f}")
        if data['type'] == 'G0':
            if verbose:
                print(
                    f"Line {data['line_num']} is a G0 command. Skipping checks.")
            current_pos = next_pos.copy()
            continue
        if verbose:
            print(f"Processing line {data['line_num']} with data: {data}")

        # check Z
        if all(k in data.keys() for k in ['H*']):
            calc_Z = alpha * D_N * data['H*']
            is_close = np.allclose(calc_Z, next_pos.z, rtol=1e-1)
            is_close_line &= is_close
            if not is_close:
                line_failures['Z'] = {'actual': data['Z'], 'expected': calc_Z}
            if verbose:
                print(
                    f"Z is close? {is_close} -- Z: {data['Z']:.3f}, calc Z: {calc_Z:.3f}")
        else:
            if verbose:
                print(
                    f"Warning: No H* found in line {data['line_num']}. Skipping Z check.")
        # check F
        if all(k in data.keys() for k in ['V*']):
            # in case the line has its own Edot label
            # Edot = data.get('Edot', Edot)
            calc_F = data['V*'] * Edot * A_F / A_T
            is_close = np.allclose(calc_F, current_F, rtol=1e-1)
            is_close_line &= is_close
            if not is_close:
                line_failures['F'] = {'actual': data['F'], 'expected': calc_F}
            if verbose:
                print(
                    f"F is close? {is_close} -- F: {data['F']:.3f}, calc F: {calc_F:.3f}")
        else:
            if verbose:
                print(
                    f"Warning: No V* found in line {data['line_num']}. Skipping F check.")
        # check E
        if all(k in data.keys() for k in ['V*', 'E']):
            L = np.linalg.norm(np.array(next_pos) - np.array(current_pos))
            # assumed to be relative E values, not absolute
            calc_E = L / data['V*'] * A_T / A_F
            is_close = np.allclose(calc_E, data['E'], rtol=1e-1)
            is_close_line &= is_close
            if not is_close:
                line_failures['E'] = {'actual': data['E'], 'expected': calc_E}
            if verbose:
                print(
                    f"dE is close? {is_close} -- E: {data['E']:.3f}, calc E: {calc_E:.3f}")
        else:
            if verbose:
                print(
                    f"Warning: No V*, X, Y, or E found in line {data['line_num']}. Skipping E check.")
        # check Edot
        if Edot is not None:
            if all(k in data.keys() for k in ['V*', 'F']):
                calc_Edot = data['F'] / data['V*'] * A_T / A_F
                is_close = np.allclose(Edot, calc_Edot, rtol=1e-1)
                is_close_line &= is_close
                if not is_close:
                    line_failures['Edot'] = {
                        'actual': Edot, 'expected': calc_Edot}
                if verbose:
                    print(
                        f"Edot is close? {is_close} -- Global Edot: {Edot:.3f}, calc Edot: {calc_Edot:.3f}")
            else:
                if verbose:
                    print(
                        f"Warning: No V* or F found in line {data['line_num']}. Skipping Edot check.")
        else:
            if verbose:
                print("Warning: No global Edot set. Skipping Edot check.")

        all_pass &= is_close_line
        if verbose:
            if is_close_line:
                print(f"Line {data['line_num']} passes")
            else:
                print(f"Line {data['line_num']} failed")

        if not is_close_line:
            failures.append(
                {data['line_num']: {'raw': data['raw'], 'failures': line_failures}})

        current_pos = next_pos.copy()

    if all_pass:
        print("All passed!")
    else:
        print("Some lines failed validation. Please see output.")
        for failure in failures:
            for idx, details in failure.items():
                print(f"Line {idx}: {details['raw'].strip()}")
                for check, values in details['failures'].items():
                    print(
                        f"  - {check} failed: expected {values['expected']:.3f}, got {values['actual']:.3f}")


def update_command_state(verbose, next_pos, data) -> tuple[Point3D, float | None]:
    F = None
    pos = next_pos.copy()
    if any(k in data.keys() for k in ['X', 'Y', 'Z']):
        pos.x = data.get('X', pos.x)
        pos.y = data.get('Y', pos.y)
        pos.z = data.get('Z', pos.z)
        if verbose:
            print(f"Line {data['line_num']} position update")
    if 'F' in data.keys():
        F = data['F']
        if verbose:
            print(f"Line {data['line_num']} feedrate update: {F:.2f}")
    return pos, F


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(
            "Usage: python validate_vtp_params.py <gcode_file> [-v|--verbose]")
        sys.exit(1)
    if len(sys.argv) > 3:
        print(
            "Error: Too many arguments. Usage: python validate_vtp_params.py <gcode_file> [-v|--verbose]")
        sys.exit(1)

    main(sys.argv[1:])
