# vtp_lithophane/gcode/gcode_generator.py
import os
from enum import Enum

import numpy as np
from PIL import Image

from .image_utils import LithophaneImage
from .parameters import PrintParameters


class Point2D:
    def __init__(self, x, y):
        self._arr = np.array([x, y], dtype=float)

    def __array__(self, dtype=None):
        return self._arr.astype(dtype) if dtype else self._arr

    def __add__(self, other):
        return Point2D(*(self._arr + np.asarray(other)))

    def __sub__(self, other):
        return Point2D(*(self._arr - np.asarray(other)))

    def __mul__(self, other):
        return Point2D(*(self._arr * np.asarray(other)))

    def __truediv__(self, other):
        return Point2D(*(self._arr / np.asarray(other)))

    def __getitem__(self, idx):
        return self._arr[idx]

    def __setitem__(self, idx, val):
        self._arr[idx] = val

    def __repr__(self):
        return f"Point2D({self._arr[0]}, {self._arr[1]})"

    @property
    def x(self):
        """Returns the X coordinate."""
        return self._arr[0]

    @property
    def y(self):
        """Returns the Y coordinate."""
        return self._arr[1]

    def copy(self):
        """Returns a copy of the Point2D instance."""
        return Point2D(*self._arr)


class GCodeType(Enum):
    G0 = 0  # Travel move
    G1 = 1  # Linear move with extrusion


class GCommand:
    def __init__(self,
                 type: GCodeType = GCodeType.G1,
                 x: float | None = None,
                 y: float | None = None,
                 z: float | None = None,
                 e: float | None = None,
                 f: float | None = None,
                 comment: str = ''):
        self.type = type
        self.values = dict(
            X=x,
            Y=y,
            Z=z,
            E=e,
            F=f,
        )
        self.comment = comment

    def __str__(self):
        command_parts = [f"{self.type.name}"]

        # Add parameters if they are not None
        # Use appropriate formatting for float values
        for k, v in self.values.items():
            if v is not None:
                try:
                    v = float(v)
                    if k in ['X', 'Y', 'Z']:
                        # micron level precision
                        command_parts.append(f"{k}{v:.3f}")
                    elif k == 'E':
                        # E typically needs higher precision
                        command_parts.append(f"{k}{v:.5f}")
                    elif k == 'F':
                        # F often has lower precision
                        command_parts.append(f"{k}{v:.1f}")
                    else:
                        # Fallback for other potential parameters
                        command_parts.append(f"{k}{v}")
                except (TypeError, ValueError):
                    print(
                        f"Warning: Invalid value for {k}: {v}. Outputting as a comment.")
                    command_parts.append(f";{k}{v}")

        if self.comment:
            command_parts.append(f"; {self.comment}")

        return ' '.join(command_parts)

    @property
    def pos(self) -> np.ndarray:
        """
        Returns the position as a numpy array.
        If X, Y, or Z are not set, they will be NaN.
        """
        pos_values = [self.values[key] if self.values[key]
                      is not None else np.nan for key in ['X', 'Y', 'Z']]

        return np.array(pos_values, dtype=np.float64)


def _calculate_build_plate_offset(params: PrintParameters,
                                  physical_print_width: float,
                                  physical_print_height: float) -> Point2D:
    """Calculates the X and Y offset to center the print volume on the build plate."""
    print("Determining build plate dimensions")
    build_plate_width, build_plate_height = params.printer_bed_size_mm
    offset_x = (build_plate_width - physical_print_width) / 2.0
    offset_y = (build_plate_height - physical_print_height) / 2.0
    return Point2D(offset_x, offset_y)
    # return 0., 0. # For testing only


def _add_segment_if_moved(
    segments_list: list,
    layer_idx: int,
    start_pt: Point2D,
    end_pt: Point2D,
    epsilon: float
):
    """
    Helper to add a segment only if it represents actual movement.
    Modifies segments_list in place.
    """
    if np.linalg.norm(end_pt - start_pt) > epsilon:
        segments_list.append((layer_idx, start_pt, end_pt))


def _execute_single_raster_pass(
    tool_pos_current: Point2D,
    is_x_primary_pass: bool,
    physical_print_width: float,
    physical_print_height: float,
    short_step: float,
    overall_scan_direction_fwd: bool,
    layer_idx: int,
    epsilon: float
) -> tuple[Point2D, list[tuple[int, Point2D, Point2D]]]:
    """Generates segments for one complete raster fill pass."""
    segments_this_pass = []
    # Create a mutable copy of the current tool position
    tool_pos_arr = tool_pos_current.copy()

    # Define primary/secondary axis properties based on pass type
    if is_x_primary_pass:
        primary_max, secondary_max = physical_print_width, physical_print_height
        primary_axis_idx, secondary_axis_idx = 0, 1
    else:  # Y-primary pass
        primary_max, secondary_max = physical_print_height, physical_print_width
        primary_axis_idx, secondary_axis_idx = 1, 0

    # Adjust primary and secondary max values to be multiples of short_step
    # We do this so that the toolpath aligns with the step size in both directions.
    # This implicitly happens for the secondary axis already because of the stepover logic when next_scan_coord_on_secondary is calculated and the next step is out of bounds, but we do it for the primary axis too to ensure consistency.
    primary_max = np.floor(primary_max / short_step) * short_step
    secondary_max = np.floor(secondary_max / short_step) * short_step
    if primary_max <= epsilon or secondary_max <= epsilon:
        print("Warning: Primary or secondary dimension is too small or zero.")
        return tool_pos_current, segments_this_pass

    scan_coord_on_secondary = tool_pos_arr[secondary_axis_idx]

    # Determine step direction along the secondary axis
    if secondary_max <= epsilon:  # Negligible secondary dimension
        step_dir_secondary = short_step  # Arbitrary; loop will likely exit quickly
    elif abs(scan_coord_on_secondary - secondary_max) < epsilon:
        step_dir_secondary = -short_step
    elif abs(scan_coord_on_secondary - 0.0) < epsilon:
        step_dir_secondary = short_step
    else:
        step_dir_secondary = short_step if scan_coord_on_secondary < secondary_max / \
            2.0 else -short_step

    # Refine step direction if secondary dimension is very small (but not zero)
    if epsilon < secondary_max < short_step:
        if abs(scan_coord_on_secondary - 0.0) < epsilon:
            step_dir_secondary = short_step
        elif abs(scan_coord_on_secondary - secondary_max) < epsilon:
            step_dir_secondary = -short_step

    line_in_pass_idx = 0
    while True:
        # 1. Align tool to current scan_coord_on_secondary (if needed after conceptual step)
        #    This ensures tool_pos[secondary_axis_idx] is correctly set for the scan.
        #    Typically, after the first iteration, tool_pos is already aligned by the stepover move.
        pt_before_align = Point2D(*tool_pos_arr)
        tool_pos_arr[secondary_axis_idx] = scan_coord_on_secondary
        _add_segment_if_moved(segments_this_pass, layer_idx,
                              pt_before_align, Point2D(*tool_pos_arr), epsilon)

        # 2. Perform the primary scan line
        current_line_is_fwd_in_serpentine = (line_in_pass_idx % 2 == 0)
        effective_scan_fwd_primary = (
            overall_scan_direction_fwd == current_line_is_fwd_in_serpentine)
        target_primary_coord = primary_max if effective_scan_fwd_primary else 0.0

        pt_before_scan = Point2D(*tool_pos_arr)
        tool_pos_arr[primary_axis_idx] = target_primary_coord
        _add_segment_if_moved(segments_this_pass, layer_idx,
                              pt_before_scan, Point2D(*tool_pos_arr), epsilon)

        line_in_pass_idx += 1

        # 3. Calculate next coordinate for stepover and check bounds
        next_scan_coord_on_secondary = scan_coord_on_secondary + step_dir_secondary
        is_out_of_bounds = (step_dir_secondary > 0 and next_scan_coord_on_secondary > secondary_max + epsilon) or \
                           (step_dir_secondary <
                            0 and next_scan_coord_on_secondary < 0 - epsilon)

        if is_out_of_bounds or (secondary_max <= epsilon and line_in_pass_idx > 1):
            break  # Done with this raster pass

        # 4. Make the stepover move
        pt_before_stepover = Point2D(*tool_pos_arr)
        scan_coord_on_secondary = next_scan_coord_on_secondary
        # Update tool's actual position
        tool_pos_arr[secondary_axis_idx] = scan_coord_on_secondary
        _add_segment_if_moved(segments_this_pass,
                              layer_idx,
                              pt_before_stepover,
                              Point2D(*tool_pos_arr),
                              epsilon)

    return Point2D(*tool_pos_arr), segments_this_pass


def _generate_entire_toolpath(params: PrintParameters, physical_print_width: float, physical_print_height: float) -> list[tuple[int, Point2D, Point2D]]:
    """
    Generates the start and end points (relative to print volume 0,0) for all passes across all layers.
    Returns:
        A list of tuples, each containing:
        - layer index (int)
        - start point (Point2D)
        - end point (Point2D)
    """
    paths_list = []
    short_step = params.line_spacing_mm
    num_layers = params.num_layers  # Total number of X or Y raster fill passes

    tool_pos = Point2D(0.0, 0.0)  # Tool starts at origin

    # First X-pass: initial scan lines go 0 -> Width
    x_pass_overall_fwd_direction = True
    y_pass_first_overall_fwd_direction: bool | None = None
    y_pass_execution_count = 0

    epsilon = 1e-6

    if short_step <= epsilon:
        print(
            f"Warning: line_spacing_mm {short_step:.2e} is critically small or zero. No toolpath will be generated.")
        return []

    for layer_idx in range(num_layers):
        is_x_pass = layer_idx % 2 == 0

        current_pass_overall_fwd_direction: bool
        if is_x_pass:
            current_pass_overall_fwd_direction = x_pass_overall_fwd_direction
        else:  # Y-pass: determine its specific overall forward direction
            if y_pass_first_overall_fwd_direction is None:
                y_coord, h_val = tool_pos.y, physical_print_height
                if abs(y_coord - 0.0) < epsilon:
                    current_pass_overall_fwd_direction = True
                elif abs(y_coord - h_val) < epsilon:
                    current_pass_overall_fwd_direction = False
                else:
                    current_pass_overall_fwd_direction = y_coord < h_val / 2.0
                y_pass_first_overall_fwd_direction = current_pass_overall_fwd_direction
            else:
                current_pass_overall_fwd_direction = (
                    y_pass_first_overall_fwd_direction
                    if y_pass_execution_count % 2 == 0
                    else not y_pass_first_overall_fwd_direction
                )

        tool_pos, segments_this_pass = _execute_single_raster_pass(
            tool_pos_current=tool_pos,
            is_x_primary_pass=is_x_pass,
            physical_print_width=physical_print_width,
            physical_print_height=physical_print_height,
            short_step=short_step,
            overall_scan_direction_fwd=current_pass_overall_fwd_direction,
            layer_idx=layer_idx,
            epsilon=epsilon
        )

        paths_list.extend(segments_this_pass)
        # tool_pos is already updated to new_tool_pos by reassignment from helper return

        if is_x_pass:
            x_pass_overall_fwd_direction = not x_pass_overall_fwd_direction
        else:
            y_pass_execution_count += 1

    return paths_list


_parameter_state = {'prev_v_star': 0., 'prev_h_star': 0.}


def _refine_segments_along_path(
    params: PrintParameters,
    lithophane_image: LithophaneImage,
    # Start of the entire path segment from toolpath generator
    start_point_path_bp: Point2D,
    end_point_path_bp: Point2D,   # End of the entire path segment
    layer_base_z: float,
    offset_x: float,
    offset_y: float,
    current_e_absolute: float,  # Current total accumulated E value
    # Currently not implemented
    adaptive_refinement: bool = False
) -> tuple[list[GCommand], float, Point2D]:  # Return GCommand objects, new E, final tool pos
    """
    Generates Gcode segments for a path, using adaptive segmentation if enabled.
    Returns: (list of GCommand objects, updated_current_e_absolute, end_tool_position_bp).
    """
    path_gcommands = []
    limg = lithophane_image
    current_tool_pos_bp = start_point_path_bp.copy()
    target_end_path_bp = end_point_path_bp.copy()
    offset_bp_vec = Point2D(offset_x, offset_y)

    path_vec_bp = target_end_path_bp - current_tool_pos_bp
    path_length_mm = np.linalg.norm(path_vec_bp)
    epsilon = 1e-6  # Small tolerance

    if path_length_mm <= epsilon:
        print(
            "Warning: Path length is too small or zero. No segments generated.")
        return [], current_e_absolute, Point2D(*current_tool_pos_bp)

    path_unit_vec = path_vec_bp / path_length_mm
    sample_step_mm = params.sampling_resolution_mm
    min_sampling_step_mm = limg.physical_print_width_mm / 1000.0  # 0.1% of the width
    if sample_step_mm < min_sampling_step_mm:
        print(
            f"Requested sample step {sample_step_mm} mm is smaller than the minimum allowed {min_sampling_step_mm} mm. Using minimum instead.")
        sample_step_mm = min_sampling_step_mm

    if adaptive_refinement:
        print(
            f"Adaptive refinement is not yet implemented. Resorting to constant step refinement with step size {sample_step_mm:.3f} mm instead.")

    distance_along_path = 0.0
    while distance_along_path < path_length_mm - epsilon:
        actual_step_taken = np.minimum(sample_step_mm,
                                       path_length_mm - distance_along_path)
        segment_actual_end_bp = (current_tool_pos_bp
                                 + path_unit_vec * actual_step_taken)

        seg_length_mm = actual_step_taken

        if seg_length_mm > epsilon:
            query_point = segment_actual_end_bp - offset_bp_vec
            v_star, h_star = _calc_VH_stars(params, limg, query_point)

            # Check if parameters changed significantly from last point
            # If so we want to do a quick jump to the new height and speed
            param_changed = False
            prev_v_star = _parameter_state['prev_v_star']
            prev_h_star = _parameter_state['prev_h_star']
            p_change = params.param_change_threshold
            if p_change > 0:
                if prev_v_star > 0 and prev_h_star > 0:
                    v_change = abs(v_star - prev_v_star)
                    h_change = abs(h_star - prev_h_star)
                    if v_change > p_change or h_change > p_change:
                        param_changed = True
                        # Insert G0 travel move with high speed
                        Z = _calculate_ZFdE(
                            params,
                            layer_base_z,
                            v_star,
                            h_star,
                            seg_length_mm,
                            epsilon=epsilon)[0]
                        travel_command = GCommand(
                            type=GCodeType.G0,
                            x=segment_actual_end_bp[0],
                            y=segment_actual_end_bp[1],
                            z=Z,
                            f=params.f_travel,
                            comment=f"Param jump: V* {v_star:.2f}, H* {h_star:.2f}"
                        )
                        path_gcommands.append(travel_command)

            # Update state
            _parameter_state['prev_v_star'] = v_star
            _parameter_state['prev_h_star'] = h_star

            # Only perform extrusion if not a parameter change travel move
            if not param_changed:
                Z, F, dE = _calculate_ZFdE(params,
                                           layer_base_z,
                                           v_star,
                                           h_star,
                                           seg_length_mm,
                                           epsilon=epsilon)

                current_e_absolute += dE

                gcommand = GCommand(
                    type=GCodeType.G1,
                    x=segment_actual_end_bp[0],
                    y=segment_actual_end_bp[1],
                    z=Z,
                    e=dE,
                    f=F,
                    comment=f"V* {v_star:.2f}, H* {h_star:.2f}",
                )
                path_gcommands.append(gcommand)

        # Move tool to end of this segment
        current_tool_pos_bp = segment_actual_end_bp.copy()
        distance_along_path += actual_step_taken

    return path_gcommands, current_e_absolute, Point2D(*current_tool_pos_bp)


def _calc_VH_stars(params: PrintParameters,
                   limg: LithophaneImage,
                   query_point_relative: Point2D) -> tuple[float, float]:
    """
    Calculates the V* and H* values based on the pixel values at the query point.
    Clips the query point to ensure it is within the image bounds.
    Returns:
        v_star: The V* value for the segment.
        h_star: The H* value for the segment.
    """
    clipped_query_point_array = np.clip(query_point_relative, [0., 0.],
                                        [limg.physical_print_width_mm,
                                         limg.physical_print_height_mm
                                         ])  # Ensure within bounds
    clipped_query_point = Point2D(*clipped_query_point_array)
    if not np.allclose(clipped_query_point, query_point_relative):
        print(
            f"Warning: Query point {query_point_relative} clipped to {clipped_query_point} to fit within image bounds.")
    r, g, _ = limg.get_pixel_value(
        clipped_query_point.x, clipped_query_point.y, binarize=False)

    v_star = r * params.v_star_ld + (1 - r) * params.v_star_hd
    h_star = g * params.h_star_ld + (1 - g) * params.h_star_hd
    return v_star, h_star


def _calculate_ZFdE(params,
                    layer_base_z,
                    v_star,
                    h_star,
                    seg_length_mm,
                    epsilon=1e-6) -> tuple[float, float, float]:
    """
    Calculates the Z position, F speed, and delta E for a segment based on v_star and h_star.
    Returns:
        segment_Z: The Z position for the segment.
        segment_F: The feed rate for the segment.
        delta_E: The change in extrusion length for the segment.
    """
    segment_Z = layer_base_z + params.alpha * h_star * params.D_N
    segment_F = (v_star * params.e_dot * (params.A_F / params.A_T)
                 if abs(v_star) > epsilon else params.f_travel)

    delta_E = ((seg_length_mm / v_star) * (params.A_T / params.A_F)
               if abs(v_star) > epsilon else 0.0)

    return float(segment_Z), float(segment_F), float(delta_E)


def generate_gcode(params: PrintParameters,
                   lithophane_image: LithophaneImage) -> tuple[list[str], list[GCommand]]:
    """
    Generates Gcode for a lithophane based on the provided parameters and image.

    Args:
        params: An instance of the PrintParameters dataclass.
        lithophane_image: An instance of the LithophaneImage class.

    Returns:
        A list of strings, where each string is a line of Gcode.
    """
    from src.gcode.template_handler import GcodeTemplateHandler

    print("Generating GCode")
    gcode_strs = []
    gcommands = []
    print_start_pt_bp = Point2D(0.0, 0.0)  # Start point on the build plate

    # 1. Include Start Gcode with variable replacement
    try:
        template_handler = GcodeTemplateHandler()

        # Prepare variables for template replacement
        template_variables = {
            "bed_temp": params.bed_temp,
            "nozzle_temp": params.nozzle_temp,
            "travel_speed": params.f_travel,
            "priming_line_length": 120,  # Default value
            "filament_diameter": params.D_F,
            "nozzle_diameter": params.D_N,
            "extrusion_multiplier": params.extrusion_multiplier,
            # Add any additional variables that might be needed
        }

        processed_start_gcode = template_handler.process_template(
            params.start_gcode_filepath, template_variables)
        gcode_strs.extend(processed_start_gcode)
        gcode_strs.append("; --- START GCODE ---")
    except Exception as e:
        print(f"Error processing start Gcode template: {e}")
        # Insert error message instead of reading raw file
        gcode_strs.append("; --- START GCODE TEMPLATE ERROR ---")
        gcode_strs.append(
            f"; Error: Could not process template {params.start_gcode_filepath}")
        gcode_strs.append(f"; Details: {str(e)}")
        gcode_strs.append(
            "; WARNING: Start G-code not included - manual setup required")
        gcode_strs.append("; --- END START GCODE ERROR ---")

    gcode_strs.append("; ###SIMULATION START###")
    current_e = 0.0

    # Calculate offset to center the print volume on the build plate
    physical_print_width = lithophane_image.physical_print_width_mm
    physical_print_height = lithophane_image.physical_print_height_mm
    offset = _calculate_build_plate_offset(
        params, physical_print_width, physical_print_height)
    gcode_strs.append(
        f"; Centering print volume ({physical_print_width:.2f}x{physical_print_height:.2f} mm) on build plate ({params.printer_bed_size_mm[0]:.2f}x{params.printer_bed_size_mm[1]:.2f} mm) with offset ({offset.x:.2f}, {offset.y:.2f}) mm")

    # --- Generate all passes first, then iterate to generate Gcode ---
    all_passes_relative = _generate_entire_toolpath(
        params, physical_print_width, physical_print_height)

    if len(all_passes_relative) != 0:
        # Start with the intro line to the first pass
        current_pos_bp = print_start_pt_bp.copy()  # The staring point of the intro line
        # The ending point of the intro line
        end_pt_bp = all_passes_relative[0][1] + offset

        v_star, h_star = _calc_VH_stars(
            params, lithophane_image, all_passes_relative[0][1])
        # Calculate Z, F, and dE for the first move
        length = np.linalg.norm(end_pt_bp - current_pos_bp)
        Z, F, dE = _calculate_ZFdE(params, 0., v_star, h_star, length)
        gc = GCommand(
            type=GCodeType.G1,
            x=end_pt_bp.x,
            y=end_pt_bp.y,
            z=Z,
            e=dE,
            f=F,
            comment=f"Intro line: V* {v_star:.2f}, H* {h_star:.2f}")
        gcommands.append(gc)
        gcode_strs.append(str(gc))
        print('new gcode command:', gc)

        print("Refining segments...")
        for pass_idx_global, (layer, start_pt_rel, end_pt_rel) in enumerate(all_passes_relative):

            # Convert relative coordinates to absolute build plate coordinates
            current_pos_bp = start_pt_rel + offset
            end_pt_bp = end_pt_rel + offset
            # layer number is zero indexed
            layer_z = layer * params.dz_mm

            # Generate segments along the pass
            segment_commands, current_e, current_pos_bp = _refine_segments_along_path(
                params, lithophane_image, current_pos_bp, end_pt_bp, layer_z, offset.x, offset.y, current_e)
            gcode_strs.extend([str(g) for g in segment_commands])
            gcommands.extend(segment_commands)
        gcode_strs.append("; ###SIMULATION END###")

    gcode_strs.append("; --- END GCODE ---")
    try:
        # Calculate estimated values for template variables
        filament_used = current_e  # Total extruded filament in mm
        # Rough estimate: 30 seconds per pass
        print_time_seconds = len(all_passes_relative) * 30
        print_time_hours = print_time_seconds // 3600
        print_time_minutes = (print_time_seconds % 3600) // 60
        print_time_str = f"{print_time_hours}h {print_time_minutes}m"

        # Prepare end gcode template variables
        template_variables = {
            "retract_length": params.retract_length,
            "retract_speed": params.retract_speed,
            "z_lift": 100,  # Default z lift height
            "travel_speed": params.f_travel,
            "print_time": print_time_str,
            "filament_used": f"{filament_used:.2f}",
            "alpha": params.alpha,
            "e_dot": params.e_dot,
            "nozzle_diameter": params.D_N,
            "filament_diameter": params.D_F,
        }

        # Process end gcode template
        template_handler = GcodeTemplateHandler()
        processed_end_gcode = template_handler.process_template(
            params.end_gcode_filepath, template_variables)
        gcode_strs.extend(processed_end_gcode)
    except Exception as e:
        print(f"Error processing end Gcode template: {e}")
        # Insert error message instead of reading raw file
        gcode_strs.append("; --- END GCODE TEMPLATE ERROR ---")
        gcode_strs.append(
            f"; Error: Could not process template {params.end_gcode_filepath}")
        gcode_strs.append(f"; Details: {str(e)}")
        gcode_strs.append(
            "; WARNING: End G-code not included - manual cleanup required")
        gcode_strs.append("; --- END END GCODE ERROR ---")

    return gcode_strs, gcommands


# Example Usage (for testing the generator function - requires dummy files and LithophaneImage)
if __name__ == '__main__':
    print("Running example usage of Gcode generation")
    # Create dummy files and LithophaneImage object for testing
    dummy_image_path = "dummy_image_gen_test.png"
    dummy_start_gcode_path = "dummy_start_gen_test.gcode"
    dummy_end_gcode_path = "dummy_end_gen_gen_test.gcode"
    output_gcode_filename = ''

    # Create a dummy binary image (white with a black square)
    dummy_img_size_px = (100, 100)  # Example image size
    dummy_img_data = Image.new('L', dummy_img_size_px, color=255)
    pixels = dummy_img_data.load()
    if pixels is None:
        raise RuntimeError("Failes to load pixel access object.")
    # Draw a black square in the center
    square_size_px = (20, 20)
    square_start_x = (dummy_img_size_px[0] - square_size_px[0]) // 2
    square_start_y = (dummy_img_size_px[1] - square_size_px[1]) // 2
    for x in range(square_start_x, square_start_x + square_size_px[0]):
        for y in range(square_start_y, square_start_y + square_size_px[1]):
            pixels[x, y] = 0  # Black pixel
    dummy_img_data.save(dummy_image_path)

    # Create dummy start Gcode
    if not os.path.exists(dummy_start_gcode_path):
        with open(dummy_start_gcode_path, "w") as f:
            f.write("; Dummy Start Gcode\n")
            f.write("G21 ; Set units to millimeters\n")
            f.write("G90 ; Use absolute positioning\n")
            # Assuming absolute extrusion
            f.write("M82 ; E axis to absolute mode\n")
            f.write("G28 ; Auto home\n")  # Home all axes
            # Lift nozzle after homing
            f.write("G1 Z5.0 F300 ; Lift nozzle after homing\n")
            f.write("G1 X0.0 Y0.0 F2000 ; Move to origin\n")  # Move to origin
            f.write("G92 E0 ; Reset extruder position\n")  # Reset E

    # Create dummy end Gcode
    if not os.path.exists(dummy_end_gcode_path):
        with open(dummy_end_gcode_path, "w") as f:
            f.write("; Dummy End Gcode\n")
            f.write("M104 S0 ; Turn off nozzle temp\n")
            f.write("M140 S0 ; Turn off bed temp\n")
            f.write("G91 ; Relative positioning\n")
            f.write("G1 E-5 F2000 ; Retract\n")
            f.write("G90 ; Absolute positioning\n")
            f.write("G1 Z100 F3000 ; Lift nozzle\n")
            f.write("G28 X Y ; Home X and Y\n")
        # M84 ; Disable motors - Let start gcode handle this if needed

    try:
        # Define parameters
        test_params = PrintParameters(
            image_filepath=dummy_image_path,
            physical_print_width_mm=20.0,
            num_layers=10,
            v_star_hd=0.15,
            v_star_ld=0.4,
            h_star_hd=6.93,
            h_star_ld=14.81,
            alpha=1.,
            D_N=0.4,
            D_F=1.75,
            e_dot=50.0,  # mm/min
            line_spacing_mm=1.2,
            sampling_resolution_mm=1.,
            dz_mm=1.27,
            start_gcode_filepath=dummy_start_gcode_path,
            end_gcode_filepath=dummy_end_gcode_path,
            printer_bed_size_mm=(250.0, 210.0),  # Prusa Mk4 build plate size
        )

        # Create LithophaneImage object
        test_lithophane_image = LithophaneImage(
            test_params.image_filepath, test_params.physical_print_width_mm)

        # Generate Gcode
        generated_gcode = generate_gcode(test_params, test_lithophane_image)[0]

        # Save generated Gcode to a file
        output_gcode_filename = "gcode/outputs/dummy_lithophane_output.gcode"
        with open(output_gcode_filename, "w") as f:
            for gcommand in generated_gcode:
                f.write(str(gcommand) + "\n")

        print(f"\nGenerated Gcode saved to {output_gcode_filename}")

    except (FileNotFoundError, ValueError, IOError) as e:
        print(f"Error during Gcode generation example: {e}")
    except Exception as e:
        print(
            f"An unexpected error occurred during Gcode generation example: {e}")
    finally:
        # Clean up dummy files
        if os.path.exists(dummy_image_path):
            os.remove(dummy_image_path)
        if os.path.exists(dummy_start_gcode_path):
            os.remove(dummy_start_gcode_path)
        if os.path.exists(dummy_end_gcode_path):
            os.remove(dummy_end_gcode_path)
        # if output_gcode_filename and os.path.exists(output_gcode_filename):
            # os.remove(output_gcode_filename)
