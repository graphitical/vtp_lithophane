import subprocess
import os
import argparse

argument_parser = argparse.ArgumentParser(description="Batch run lithophize gcode generation.")
argument_parser.add_argument(
    "-F", "--force_rewrite",
    default=False,
    action="store_true",
    help="Force overwrite existing G-code files."
)
argument_parser.add_argument(
    "-O", "--options",
    type=str,
    default="",
    help="The list of gcode files to generate."
)
args = argument_parser.parse_args()

overwrite = args.force_rewrite
options = args.options

args_spread = ["-w", "100",
               "--line-spacing", "50",
               "--in-flow-rate", "150",
               "--layers", "1"]

args_swatch = ["-w", "20",
               "--line-spacing", "1.5",
               "--in-flow-rate", "100",
            #    "-w", "10",
            #    "--priming-line-length", "10",
               "--layers", "1"]
            #    "--layers", "2"]

args_test_grid = ["-w", "60",
                  "--line-spacing", "1.5",
                  "--in-flow-rate", "50",
                  "--layers", "1",
                  "--priming-line-length", "10",
                #   "--start-gcode", "gcode/templates/template_start.gcode",
                #   "--end-gcode", "gcode/templates/template_end.gcode"
                ]

if "L" in options:
    for file in os.listdir("images"):
        if file == "test_grid.png":
            if overwrite or not os.path.exists(f"gcode/outputs/{file.replace('.png', '.gcode')}"):
                subprocess.run(["python", "lithophize.py",
                                "-i", f"images/{file}",
                                "-o", f"gcode/outputs/edot150_{file.replace('.png', '.gcode')}"] \
                                    + args_spread)

if "SG" in options:
    for i in range(101):
        if os.path.exists(f"images/grayscale{i:03d}.png"):
            if overwrite or not os.path.exists(f"gcode/outputs/grayscale{i:03d}.gcode"):
                subprocess.run(["python", "lithophize.py",
                                "-i", f"images/grayscale{i:03d}.png",
                                "-o", f"gcode/outputs/grayscale{i:03d}.gcode"]\
                                    + args_swatch)

if "ST" in options:
    for file in os.listdir("images"):
        if file.startswith("test_grid_") and file.endswith(".png"):
            if overwrite or not os.path.exists(f"gcode/outputs/ST_{file.replace('.png', '.gcode')}"):
                subprocess.run(["python", "lithophize.py",
                                "-i", f"images/{file}",
                                "-o", f"gcode/outputs/edot100_{file.replace('.png', '.gcode')}"] \
                                    + args_swatch)

if "TG" in options:
    subprocess.run(["python", "lithophize.py",
                    "-i", "images/test_grid.png",
                    "-o", "gcode/250702/test_grid.gcode"] \
                        + args_test_grid)

# for file in os.listdir("gcode/outputs"):
#     if file.endswith(".gcode"):
#         subprocess.run(["python", "analyze_gcode.py", f"gcode/outputs/{file}"])