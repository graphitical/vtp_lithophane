#!/usr/bin/env python3
import math
import sys
import re
import argparse

def parse_parameters(tokens):
    """
    Parse tokens such as ["X10", "Y20", "F1800"] into a dictionary.
    """
    params = {}
    for token in tokens:
        try:
            params[token[0].upper()] = float(token[1:])
        except (ValueError, IndexError):
            continue
    return params

def estimate_print_time(gcode_filename):
    """
    Estimate total print duration by processing movement commands (G0/G1) and dwell commands (G4).
    For movements, Euclidean distance is computed between successive positions (X, Y, Z) and divided by
    the current feed rate (converted from mm/min to mm/sec). Dwell commands add their delay.
    
    Reference: :contentReference[oaicite:2]{index=2}, :contentReference[oaicite:3]{index=3}.
    """
    total_time = 0.0  # seconds
    current_feed_rate = None  # mm/min; set by commands if available
    current_position = {'X': 0.0, 'Y': 0.0, 'Z': 0.0}

    with open(gcode_filename, 'r') as f:
        for line in f:
            # Remove comments and whitespace
            line = line.split(';')[0].strip()
            if not line:
                continue
            tokens = line.split()
            if not tokens:
                continue

            command = tokens[0].upper()
            params = parse_parameters(tokens[1:])

            if command in ('G0', 'G1'):
                # Update feed rate if provided.
                if 'F' in params:
                    current_feed_rate = params['F']
                new_position = current_position.copy()
                for axis in ['X', 'Y', 'Z']:
                    if axis in params:
                        new_position[axis] = params[axis]
                distance = math.sqrt(
                    (new_position['X'] - current_position['X'])**2 +
                    (new_position['Y'] - current_position['Y'])**2 +
                    (new_position['Z'] - current_position['Z'])**2
                )
                if current_feed_rate and current_feed_rate > 0:
                    # Convert feed rate from mm/min to mm/sec.
                    time_sec = distance / (current_feed_rate / 60.0)
                    total_time += time_sec
                current_position = new_position

            elif command == 'G4':
                # Dwell command: S (seconds) or P (milliseconds)
                if 'P' in params:
                    total_time += params['P'] / 1000.0
                elif 'S' in params:
                    total_time += params['S']

    return total_time

def analyze_gcode(gcode_filename, account_m221=False):
    """
    Analyze the G‑code file to compute total extruded filament length (mm).
    The function supports absolute (M82) and relative (M83) extrusion modes.
    If account_m221 is enabled, flow multiplier commands (M221) are applied.
    """
    total_extrusion = 0.0
    last_e = None
    extrusion_mode = "absolute"  # default mode
    flow_multiplier = 1.0        # default multiplier (100%)
    m221_warning_issued = False

    # Regex patterns for extracting extrusion (E) values and M221 commands.
    e_pattern = re.compile(r'\bE(-?\d+\.?\d*)')
    m221_pattern = re.compile(r'\bM221\b.*\bS(-?\d+\.?\d*)', re.IGNORECASE)

    with open(gcode_filename, 'r') as file:
        for line in file:
            # Remove comments and whitespace.
            line = line.split(';')[0].strip()
            if not line:
                continue

            m221_match = m221_pattern.search(line)
            if m221_match:
                if account_m221:
                    try:
                        s_val = float(m221_match.group(1))
                        flow_multiplier = s_val / 100.0
                    except ValueError:
                        pass
                else:
                    if not m221_warning_issued:
                        print("Warning: M221 command detected but flow multiplier accounting is disabled.",
                              file=sys.stderr)
                        m221_warning_issued = True

            # Update extrusion mode.
            if "M82" in line.upper():
                extrusion_mode = "absolute"
            elif "M83" in line.upper():
                extrusion_mode = "relative"

            # Process only movement commands.
            stripped_line = line.lstrip().upper()
            if not (stripped_line.startswith("G0") or stripped_line.startswith("G1")):
                continue

            match = e_pattern.search(line)
            if match:
                try:
                    current_e = float(match.group(1))
                except ValueError:
                    continue
                if extrusion_mode == "absolute":
                    if last_e is not None:
                        delta = current_e - last_e
                        if delta > 0:
                            total_extrusion += delta * flow_multiplier
                    last_e = current_e
                else:  # relative mode
                    if current_e > 0:
                        total_extrusion += current_e * flow_multiplier

    return total_extrusion

def main():
    parser = argparse.ArgumentParser(
        description="G-code post processing script: estimates print duration and analyzes extruded filament."
    )
    parser.add_argument("filename", help="Path to the ASCII G-code file")
    parser.add_argument("-d", "--diameter", type=float, default=1.75,
                        help="Filament diameter in mm (default: 1.75)")
    parser.add_argument("-r", "--density", type=float, default=1.0,
                        help="Filament density in g/cc (default: 1.0)")
    parser.add_argument("-v", "--object_volume", type=float, default=None,
                        help="Optional: Object volume in mm³ for relative volume calculation")
    parser.add_argument("--account-m221", action="store_true",
                        help="If set, account for flow multiplier (M221) commands in the G-code")
    args = parser.parse_args()

    print("Processing file: {}".format(args.filename))
    print("\nEstimating print duration...")
    duration_sec = estimate_print_time(args.filename)
    hours = int(duration_sec // 3600)
    minutes = int((duration_sec % 3600) // 60)
    seconds = int(duration_sec % 60)
    print("Estimated print duration: {:02d}:{:02d}:{:02d}".format(hours, minutes, seconds))

    print("\nAnalyzing extruded filament...")
    total_length = analyze_gcode(args.filename, account_m221=args.account_m221)
    area = math.pi * (args.diameter / 2) ** 2  # cross-sectional area in mm²
    total_volume = total_length * area        # extruded volume in mm³
    total_mass = (total_volume / 1000) * args.density  # converting mm³ to cc (1 cc = 1000 mm³)

    print("Total extruded length: {:.3f} mm".format(total_length))
    print("Extruded volume:       {:.3f} mm³".format(total_volume))
    print("Extruded mass:         {:.3f} g".format(total_mass))
    if args.object_volume:
        rel_vol = total_volume / args.object_volume
        print("Relative volume (extruded vol / object vol): {:.6f}".format(rel_vol))
    else:
        print("No object volume provided; relative volume not calculated.")

if __name__ == '__main__':
    main()

