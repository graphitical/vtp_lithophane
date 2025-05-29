# vtp_lithophane/gcode_generator.py
import os
from enum import Enum

import numpy as np
from PIL import Image

from .image_utils import LithophaneImage
from .parameters import PrintParameters


class GCodeType(Enum):
    G0 = 0  # Travel move
    G1 = 1  # Linear move with extrusion


class GCommand:
    def __init__(self, type=GCodeType.G1, x=None, y=None, z=None, e=None, f=None, comment=''):
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

        if self.comment:
            command_parts.append(f"; {self.comment}")

        return ' '.join(command_parts)


def _calculate_build_plate_offset(params: PrintParameters, physical_print_width: float, physical_print_height: float) -> tuple[float, float]:
    """Calculates the X and Y offset to center the print volume on the build plate."""
    print("Determining build plate dimensions")
    build_plate_width, build_plate_height = params.printer_bed_size_mm
    offset_x = (build_plate_width - physical_print_width) / 2.0
    offset_y = (build_plate_height - physical_print_height) / 2.0
    return offset_x, offset_y
    # return 0., 0. # For testing only


def _add_segment_if_moved(
    segments_list: list, layer_idx: int, pt_start_tuple: tuple[float, float],
    pt_end_tuple: tuple[float, float], epsilon: float
):
    """Helper to add a segment only if it represents actual movement."""
    if np.linalg.norm(np.array(pt_end_tuple) - np.array(pt_start_tuple)) > epsilon:
        segments_list.append((layer_idx, pt_start_tuple, pt_end_tuple))


def _execute_single_raster_pass(
    tool_pos_current: np.ndarray,
    is_x_primary_pass: bool,
    physical_print_width: float,
    physical_print_height: float,
    short_step: float,
    overall_scan_direction_fwd: bool,
    layer_idx: int,
    epsilon: float
) -> tuple[np.ndarray, list[tuple[int, tuple[float, float], tuple[float, float]]]]:
    """Generates segments for one complete raster fill pass."""
    segments_this_pass = []
    tool_pos = tool_pos_current.copy()

    # Define primary/secondary axis properties based on pass type
    if is_x_primary_pass:
        primary_max, secondary_max = physical_print_width, physical_print_height
        primary_axis_idx, secondary_axis_idx = 0, 1
    else:  # Y-primary pass
        primary_max, secondary_max = physical_print_height, physical_print_width
        primary_axis_idx, secondary_axis_idx = 1, 0

    scan_coord_on_secondary = tool_pos[secondary_axis_idx]

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
        pt_before_align = tuple(tool_pos)
        tool_pos[secondary_axis_idx] = scan_coord_on_secondary
        _add_segment_if_moved(segments_this_pass, layer_idx,
                              pt_before_align, tuple(tool_pos), epsilon)

        # 2. Perform the primary scan line
        current_line_is_fwd_in_serpentine = (line_in_pass_idx % 2 == 0)
        effective_scan_fwd_primary = (
            overall_scan_direction_fwd == current_line_is_fwd_in_serpentine)
        target_primary_coord = primary_max if effective_scan_fwd_primary else 0.0

        pt_before_scan = tuple(tool_pos)
        tool_pos[primary_axis_idx] = target_primary_coord
        _add_segment_if_moved(segments_this_pass, layer_idx,
                              pt_before_scan, tuple(tool_pos), epsilon)

        line_in_pass_idx += 1

        # 3. Calculate next coordinate for stepover and check bounds
        next_scan_coord_on_secondary = scan_coord_on_secondary + step_dir_secondary
        is_out_of_bounds = (step_dir_secondary > 0 and next_scan_coord_on_secondary > secondary_max + epsilon) or \
                           (step_dir_secondary <
                            0 and next_scan_coord_on_secondary < 0 - epsilon)

        if is_out_of_bounds or (secondary_max <= epsilon and line_in_pass_idx > 0):
            break  # Done with this raster pass

        # 4. Make the stepover move
        pt_before_stepover = tuple(tool_pos)
        scan_coord_on_secondary = next_scan_coord_on_secondary
        # Update tool's actual position
        tool_pos[secondary_axis_idx] = scan_coord_on_secondary
        _add_segment_if_moved(segments_this_pass, layer_idx,
                              pt_before_stepover, tuple(tool_pos), epsilon)

    return tool_pos, segments_this_pass


def _generate_entire_toolpath(params: PrintParameters, physical_print_width: float, physical_print_height: float) -> list[tuple[int, tuple[float, float], tuple[float, float]]]:
    """
    Generates the start and end points (relative to print volume 0,0) for all passes across all layers.
    """
    paths_list = []
    short_step = params.line_spacing_mm
    num_layers = params.num_layers  # Total number of X or Y raster fill passes

    tool_pos = np.array([0.0, 0.0])  # Tool starts at origin

    # First X-pass: initial scan lines go 0 -> Width
    x_pass_overall_fwd_direction = True
    y_pass_first_overall_fwd_direction: bool | None = None
    y_pass_execution_count = 0

    epsilon = 1e-9

    if short_step <= epsilon:
        print("Warning: line_spacing_mm (short_step) is critically small or zero.")
        return []

    for layer_idx in range(num_layers):
        is_x_pass = layer_idx % 2 == 0

        current_pass_overall_fwd_direction: bool
        if is_x_pass:
            current_pass_overall_fwd_direction = x_pass_overall_fwd_direction
        else:  # Y-pass: determine its specific overall forward direction
            if y_pass_first_overall_fwd_direction is None:
                y_coord, h_val = tool_pos[1], physical_print_height
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


_parameter_state = {'prev_v_star': None, 'prev_h_star': None}


def _refine_segments_along_path(
    params: PrintParameters,
    lithophane_image: LithophaneImage,
    # Start of the entire path segment from toolpath generator
    start_point_path_bp: np.ndarray,
    end_point_path_bp: np.ndarray,   # End of the entire path segment
    layer_base_z: float,
    offset_x: float,
    offset_y: float,
    current_e_absolute: float,  # Current total accumulated E value
    # Default to False to keep old behavior if not specified
    adaptive_refinement: bool = False
) -> tuple[list[GCommand], float, np.ndarray]:  # Return GCommand objects, new E, final tool pos
    """
    Generates Gcode segments for a path, using adaptive segmentation if enabled.
    Returns: (list of GCommand objects, updated_current_e_absolute, end_tool_position_bp).
    """
    path_gcode_commands = []
    current_tool_pos_bp = np.asarray(start_point_path_bp)
    target_end_path_bp = np.asarray(end_point_path_bp)
    offset_bp_vec = np.asarray([offset_x, offset_y])

    path_vec_bp = target_end_path_bp - current_tool_pos_bp
    path_length_mm = np.linalg.norm(path_vec_bp)
    epsilon = 1e-6  # Small tolerance

    if path_length_mm <= epsilon:
        return [], current_e_absolute, current_tool_pos_bp

    path_unit_vec_bp = path_vec_bp / path_length_mm
    sampling_step_mm = max(params.sampling_resolution_mm,
                           0.1)  # Ensure step is not zero

    if adaptive_refinement:
        # --- Adaptive Refinement Logic ---
        # Currently not working as intended, but included for future use
        raise NotImplementedError(
            "Adaptive refinement is not yet implemented. Please use non-adaptive refinement.")
        # This segment_start_bp tracks the beginning of the G-code line being built
        current_gcode_segment_start_bp = current_tool_pos_bp.copy()
        # Image value for the G-code segment currently being built
        current_gcode_segment_img_val = lithophane_image.get_pixel_value(
            *(current_gcode_segment_start_bp - offset_bp_vec), binarize=True
        )

        # distance_along_path tracks total distance covered from start_point_path_bp
        distance_along_path = 0.0

        while distance_along_path < path_length_mm - epsilon:  # Loop until very near the end
            # Determine the next point to sample along the path
            # It's either a sampling_step_mm away, or the end of the path if closer
            next_sampling_distance = min(
                distance_along_path + sampling_step_mm, path_length_mm)
            point_to_sample_bp = start_point_path_bp + \
                path_unit_vec_bp * next_sampling_distance

            image_val_at_sample_point = lithophane_image.get_pixel_value(
                *(point_to_sample_bp - offset_bp_vec), binarize=True
            )

            is_value_change = (image_val_at_sample_point !=
                               current_gcode_segment_img_val)
            is_end_of_overall_path = (
                abs(next_sampling_distance - path_length_mm) < epsilon)

            if is_value_change or is_end_of_overall_path:
                # Conditions met to finalize the current G-code segment:
                # It ends at point_to_sample_bp (where value changed or path ends)
                segment_actual_end_bp = point_to_sample_bp

                seg_vec = segment_actual_end_bp - current_gcode_segment_start_bp
                seg_length_mm = np.linalg.norm(seg_vec)

                if seg_length_mm > epsilon:
                    # Use the image value from the START of this G-code segment for calculations
                    t = current_gcode_segment_img_val

                    v_star = t * params.v_star_ld + (1 - t) * params.v_star_hd
                    h_star = t * params.h_star_ld + (1 - t) * params.h_star_hd

                    segment_Z = layer_base_z + params.alpha * h_star * params.D_N
                    segment_F = (v_star * params.e_dot * (params.A_F / params.A_T)
                                 if abs(v_star) > epsilon else params.f_travel)

                    delta_E = ((seg_length_mm / v_star) * (params.A_T / params.A_F)
                               if abs(v_star) > epsilon else 0.0)

                    current_e_absolute += delta_E

                    gcommand = GCommand(
                        type=GCodeType.G1,
                        x=segment_actual_end_bp[0],
                        y=segment_actual_end_bp[1],
                        z=segment_Z,
                        e=current_e_absolute,  # Absolute E
                        f=segment_F,
                    )
                    path_gcode_commands.append(gcommand)
                    current_tool_pos_bp = segment_actual_end_bp.copy()

                # Setup for the NEXT G-code segment
                current_gcode_segment_start_bp = segment_actual_end_bp.copy()
                current_gcode_segment_img_val = image_val_at_sample_point  # Value at the new start

            distance_along_path = next_sampling_distance
            if is_end_of_overall_path:  # Ensure loop terminates if end is reached
                break

        # Final tool position after adaptive refinement should be the target end of the path
        current_tool_pos_bp = target_end_path_bp.copy()

    else:
        # --- Non-Adaptive Refinement Logic ---
        # Segments are cut at every sampling_step_mm
        distance_along_path = 0.0
        # current_tool_pos_bp is the start of the current small fixed-length segment

        while distance_along_path < path_length_mm - epsilon:
            # seg_start_bp_non_adaptive = current_tool_pos_bp.copy() # Not strictly needed for 't' calc anymore

            actual_step_taken = np.minimum(
                sampling_step_mm, path_length_mm - distance_along_path)
            segment_actual_end_bp = current_tool_pos_bp + \
                path_unit_vec_bp * actual_step_taken

            seg_length_mm = actual_step_taken

            if seg_length_mm > epsilon:
                # Cap the query point to the physical bounds
                query_point = segment_actual_end_bp - offset_bp_vec
                query_point[0] = min(
                    max(query_point[0], 0.),
                    lithophane_image.physical_print_width_mm)
                query_point[1] = min(
                    max(query_point[1], 0.),
                    lithophane_image.physical_print_height_mm)
                # We use the channels of the image to scale the V* and H* independently. Red is for V*, Green is for H*. I'm holding onto Blue for something else, possibly dL later on, but I need to work out how to integrate that.
                r, g, _ = lithophane_image.get_pixel_value(
                    # Sample at segment's END
                    *query_point, binarize=False
                )

                v_star = r * params.v_star_ld + (1 - r) * params.v_star_hd
                h_star = g * params.h_star_ld + (1 - g) * params.h_star_hd

                # Check if parameters changed significantly from last point
                param_changed = False
                if hasattr(params, 'param_change_threshold') and params.param_change_threshold > 0:
                    if _parameter_state['prev_v_star'] is not None:
                        v_change = abs(
                            v_star - _parameter_state['prev_v_star'])
                        h_change = abs(
                            h_star - _parameter_state['prev_h_star'])
                        if v_change > params.param_change_threshold or h_change > params.param_change_threshold:
                            param_changed = True
                            # Insert G0 travel move with high speed
                            travel_command = GCommand(
                                type=GCodeType.G0,
                                x=segment_actual_end_bp[0],
                                y=segment_actual_end_bp[1],
                                z=layer_base_z + params.alpha * h_star * params.D_N,
                                f=params.f_travel,
                                comment=f"Parameter change travel move: V* {_parameter_state['prev_v_star']:.2f}->{v_star:.2f}, H* {_parameter_state['prev_h_star']:.2f}-> {h_star:.2f}"
                            )
                            path_gcode_commands.append(str(travel_command))

                # Update state
                _parameter_state['prev_v_star'] = v_star
                _parameter_state['prev_h_star'] = h_star

                # Only perform extrusion if not a parameter change travel move
                if not param_changed:
                    segment_Z = layer_base_z + params.alpha * h_star * params.D_N
                    segment_F = (v_star * params.e_dot * (params.A_F / params.A_T)
                                 if abs(v_star) > epsilon else params.f_travel)

                    delta_E = ((seg_length_mm / v_star) * (params.A_T / params.A_F)
                               if abs(v_star) > epsilon else 0.0)

                    current_e_absolute += delta_E

                    gcommand = GCommand(
                        type=GCodeType.G1,
                        x=segment_actual_end_bp[0],
                        y=segment_actual_end_bp[1],
                        z=segment_Z,
                        e=delta_E,
                        f=segment_F,
                        comment=f"V* {v_star:.2f}, H* {h_star:.2f}",
                    )
                    path_gcode_commands.append(str(gcommand))

            # Move tool to end of this segment
            current_tool_pos_bp = segment_actual_end_bp.copy()
            distance_along_path += actual_step_taken

        # Ensure tool ends exactly at target_end_path_bp if minor float issues occurred
        if np.linalg.norm(current_tool_pos_bp - target_end_path_bp) > epsilon:
            # This case should ideally not be hit often if logic is correct
            # but as a safeguard, if not at the end, make a final small move.
            # This move would typically be non-extruding or use params of last point.
            # For simplicity here, we assume the loop got us close enough or to the end.
            # A more robust final step might be needed if precise endpoint is critical
            # and the loop undershoots.
            # However, the `min` in `actual_step_taken` should prevent overshooting
            # and `while distance_along_path < path_length_mm - epsilon` should make it stop right.
            # The main thing is that current_tool_pos_bp *is* the final position.
            pass  # current_tool_pos_bp reflects the true end.

    return path_gcode_commands, current_e_absolute, current_tool_pos_bp


def generate_gcode(params: PrintParameters, lithophane_image: LithophaneImage) -> list[str]:
    """
    Generates Gcode for a lithophane based on the provided parameters and image.

    Args:
        params: An instance of the PrintParameters dataclass.
        lithophane_image: An instance of the LithophaneImage class.

    Returns:
        A list of strings, where each string is a line of Gcode.
    """
    print("Generating GCode")
    gcode_lines = []

    # 1. Include Start Gcode
    try:
        with open(params.start_gcode_filepath, 'r') as f:
            gcode_lines.extend([line.strip() for line in f if line.strip()])
        gcode_lines.append("; --- Start Gcode Ends ---")
    except IOError as e:
        if os.path.exists(params.start_gcode_filepath):
            print(f"Error reading start Gcode file: {e}")
        else:
            print("No Start Gcode")

    current_e = 0.0

    # Calculate offset to center the print volume on the build plate
    physical_print_width = lithophane_image.physical_print_width_mm
    physical_print_height = lithophane_image.physical_print_height_mm
    offset_x, offset_y = _calculate_build_plate_offset(
        params, physical_print_width, physical_print_height)
    gcode_lines.append(
        f"; Centering print volume ({physical_print_width:.2f}x{physical_print_height:.2f} mm) on build plate ({params.printer_bed_size_mm[0]:.2f}x{params.printer_bed_size_mm[1]:.2f} mm) with offset ({offset_x:.2f}, {offset_y:.2f}) mm")

    # Initial position is assumed to be (0,0) after homing and initial Z lift from start gcode
    # The very first move will be to the start of the first pass at the calculated Z.
    # This will be updated after the first move
    current_pos_bp = np.array([0.0, 0.0])

    # --- Generate all passes first, then iterate to generate Gcode ---
    all_passes_relative = _generate_entire_toolpath(
        params, physical_print_width, physical_print_height)

    print("Refining segments...")
    for pass_idx_global, (layer, start_pt_rel, end_pt_rel) in enumerate(all_passes_relative):
        layer_base_z = layer * params.dz_mm

        # Apply offset to pass start and end points (build plate coordinates)
        start_pt_bp = np.array([
            start_pt_rel[0] + offset_x,
            start_pt_rel[1] + offset_y])
        end_pt_bp = np.array([
            end_pt_rel[0] + offset_x,
            end_pt_rel[1] + offset_y])

        # --- Handle transition to the start of the current pass (G1) ---
        # If it's the very first pass of the entire print (global index 0),
        # the start gcode should position the nozzle. The first G1 will move to the start point at calculated Z.
        # For all subsequent passes (global index > 0),
        # the nozzle is already at the end of the last segment of the previous pass.
        # The move to the start of the current pass is a G1 command that transitions XY and Z.

        # The start point of the current move is current_pos_bp (end of previous segment)
        # The end point of the current move is start_point_bp (start of current pass)

        # Generate segments for the move to the start of the current pass
        # This is only needed for passes after the very first one
        ENABLE_ADAPTIVE_REFINEMENT = False
        if pass_idx_global > 0:
            connecting_lines, current_e, current_pos_bp = _refine_segments_along_path(
                params, lithophane_image, current_pos_bp, start_pt_bp, layer_base_z, offset_x, offset_y, current_e, adaptive_refinement=ENABLE_ADAPTIVE_REFINEMENT
            )
            gcode_lines.extend(connecting_lines)
            # current_pos_bp is updated by _generate_segments_along_path to be the end of the connecting move (which is start_point_bp)
        else:
            # For the very first pass, the start gcode positions the nozzle.
            # The first generated G1 command will be for the first segment of the first pass.
            # current_pos_bp needs to be set to the start of the first pass for _generate_segments_along_path to work correctly.
            current_pos_bp = start_pt_bp

        # --- Generate segments along the pass ---
        # Break the long pass into segments of refinement_length_mm
        # current_pos_bp is already at the start of the pass from the previous move
        segment_lines, current_e, current_pos_bp = _refine_segments_along_path(
            params, lithophane_image, current_pos_bp, end_pt_bp, layer_base_z, offset_x, offset_y, current_e,
            adaptive_refinement=ENABLE_ADAPTIVE_REFINEMENT,
        )
        gcode_lines.extend(segment_lines)

    # --- End of Main Lithophane Generation Loop ---

    print("Adding final Z hop")
    # Add a final Z hop after the last layer
    final_z_hop = params.num_layers * params.dz_mm + \
        5.0  # Hop 5mm above the total print height
    # Use G0 for final travel
    gcode_lines.append(
        str(GCommand(type=GCodeType.G0, z=final_z_hop, f=300, comment="Final Z hop")))

    # 2. Include End Gcode
    gcode_lines.append("; --- End Gcode Starts ---")
    try:
        with open(params.end_gcode_filepath, 'r') as f:
            gcode_lines.extend([line.strip() for line in f if line.strip()])
    except IOError as e:
        if os.path.exists(params.end_gcode_filepath):
            print(f"Error reading end Gcode file: {e}")
        else:
            print("No End Gcode")

    return gcode_lines


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
        generated_gcode = generate_gcode(test_params, test_lithophane_image)

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
