# vtp_lithophane/lithophize.py - Main entry point for VTP Lithophane Generator

import argparse
import os
import sys
import time

from src.gcode.gcode_generator import generate_gcode
from src.gcode.image_utils import LithophaneImage
from src.gcode.parameters import PrintParameters


def create_parser() -> argparse.ArgumentParser:
    """Create and configure the argument parser for the lithophize program."""
    parser = argparse.ArgumentParser(
        description='VTP Lithophane Generator - Create 3D printable lithophanes with Viscous Thread Printing (VTP) method.',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    # Required arguments
    required = parser.add_argument_group('Required parameters')
    required.add_argument('-i', '--image', required=True, type=str,
                          help='Path to the input image file')
    required.add_argument('-w', '--width', required=True, type=float,
                          help='Physical print width in mm')
    required.add_argument('-o', '--output', required=True, type=str,
                          help='Output G-code file path')

    # VTP parameters
    vtp_params = parser.add_argument_group('VTP parameters')
    vtp_params.add_argument('--layers', type=int, default=4,
                            help='Number of layers for the lithophane')
    vtp_params.add_argument('--v-star-hd', type=float, default=0.25,
                            help='V* value for high density (dark areas)')
    vtp_params.add_argument('--v-star-ld', type=float, default=0.5,
                            help='V* value for low density (light areas)')
    vtp_params.add_argument('--h-star-hd', type=float, default=5.0,
                            help='H* value for high density (dark areas)')
    vtp_params.add_argument('--h-star-ld', type=float, default=10.0,
                            help='H* value for low density (light areas)')

    # Physical parameters
    physical = parser.add_argument_group('Physical parameters')
    physical.add_argument('--alpha', type=float, default=1.5,
                          help='Die swell constant')
    physical.add_argument('--in-flow-rate', type=float, default=50.0,
                          dest='e_dot',
                          help='Material flow rate (mm/min)')
    physical.add_argument('--line-spacing', type=float, default=1.39,
                          help='Line spacing in mm')
    physical.add_argument('--sample-res', type=float, default=0.5, dest='sampling_resolution_mm',
                          help='Physical distance step for image sampling in adaptive segmentation (mm)')
    physical.add_argument('--layer-height', type=float, default=1, dest='dz_mm',
                          help='Nominal layer height increment (mm)')

    # Printer parameters
    printer = parser.add_argument_group('Printer parameters')
    printer.add_argument('--travel-speed', type=float, default=3000.0, dest='f_travel',
                         help='Travel speed (mm/min)')
    printer.add_argument('--nozzle-diameter', type=float, default=0.4, dest='D_N',
                         help='Nozzle diameter (mm)')
    printer.add_argument('--filament-diameter', type=float, default=1.75, dest='D_F',
                         help='Filament diameter (mm)')
    printer.add_argument('--bed-size', type=str, default='255x210',
                         help='Printer bed size in mm (format: widthxheight, e.g., 255x210)')

    # G-code files
    gcode_files = parser.add_argument_group('G-code files')
    gcode_files.add_argument('--start-gcode', type=str, default='gcode/templates/default_start.gcode',
                             help='Path to start G-code file')
    gcode_files.add_argument('--end-gcode', type=str, default='gcode/templates/default_end.gcode',
                             help='Path to end G-code file')

    return parser


def parse_bed_size(bed_size_str: str) -> tuple[float, float]:
    """Parse the bed size string (format: widthxheight) to a tuple of floats."""
    try:
        width, height = bed_size_str.lower().split('x')
        return float(width), float(height)
    except ValueError:
        raise ValueError(
            f"Invalid bed size format: {bed_size_str}. Expected format: widthxheight (e.g., 235x235)")


def validate_files(args) -> None:
    """Validate that all required files exist."""
    files_to_check = [
        ('image', args.image),
        ('start G-code', args.start_gcode),
        ('end G-code', args.end_gcode)
    ]

    for file_type, file_path in files_to_check:
        if not os.path.exists(file_path):
            raise FileNotFoundError(
                f"The {file_type} file does not exist: {file_path}")

    # Check if output directory exists
    output_dir = os.path.dirname(args.output)
    if output_dir and not os.path.exists(output_dir):
        raise FileNotFoundError(
            f"The output directory does not exist: {output_dir}")


def main():
    """Main entry point for the lithophize program."""
    parser = create_parser()
    args = parser.parse_args()

    try:
        # Validate files
        validate_files(args)

        # Parse bed size
        bed_size = parse_bed_size(args.bed_size)

        print(f"Processing image: {args.image}")
        print(f"Output G-code will be saved to: {args.output}")

        # Create PrintParameters object
        params = PrintParameters(
            image_filepath=args.image,
            physical_print_width_mm=args.width,
            num_layers=args.layers,
            v_star_hd=args.v_star_hd,
            v_star_ld=args.v_star_ld,
            h_star_hd=args.h_star_hd,
            h_star_ld=args.h_star_ld,
            alpha=args.alpha,
            e_dot=args.e_dot,
            line_spacing_mm=args.line_spacing,
            sampling_resolution_mm=args.sampling_resolution_mm,
            dz_mm=args.dz_mm,
            start_gcode_filepath=args.start_gcode,
            end_gcode_filepath=args.end_gcode,
            f_travel=args.f_travel,
            D_N=args.D_N,
            D_F=args.D_F,
            printer_bed_size_mm=bed_size
        )

        # Create LithophaneImage object
        start_time = time.time()
        print("Loading and processing image...")
        lithophane_image = LithophaneImage(
            filepath=params.image_filepath,
            physical_print_width_mm=params.physical_print_width_mm
        )

        # Generate G-code
        print("Generating G-code...")
        gcode_lines = generate_gcode(params, lithophane_image)[0]

        # Write G-code to output file
        print(f"Writing G-code to {args.output}...")
        with open(args.output, 'w') as f:
            f.write("\n".join(gcode_lines))

        end_time = time.time()
        print(
            f"Done! Process completed in {end_time - start_time:.2f} seconds.")
        print(f"Generated {len(gcode_lines)} lines of G-code.")

    except (FileNotFoundError, ValueError, IOError) as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
