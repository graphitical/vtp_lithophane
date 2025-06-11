import subprocess
import os
import sys

overwrite = len(sys.argv) > 1 and sys.argv[1] == "F"

args_spread = ["-w", "100",
               "--line-spacing", "50",
               "--layers", "1"]

args_swatch = ["-w", "10",
               "--layers", "2"]

for i in range(101):
    if os.path.exists(f"images/grayscale{i:03d}.png"):
        if overwrite or not os.path.exists(f"gcode/outputs/grayscale{i:03d}.gcode"):
            subprocess.run(["python", "lithophize.py",
                            "-i", f"images/grayscale{i:03d}.png",
                            "-o", f"gcode/outputs/grayscale{i:03d}.gcode"]\
                                + args_swatch)

for file in os.listdir("images"):
    if file.startswith("test_grid_") and file.endswith(".png"):
        if overwrite or not os.path.exists(f"gcode/outputs/{file.replace('.png', '.gcode')}"):
            subprocess.run(["python", "lithophize.py",
                            "-i", f"images/{file}",
                            "-o", f"gcode/outputs/{file.replace('.png', '.gcode')}"] \
                                + args_swatch)

for file in os.listdir("images"):
    if file == "test_grid.png":
        if overwrite or not os.path.exists(f"gcode/outputs/{file.replace('.png', '.gcode')}"):
            subprocess.run(["python", "lithophize.py",
                            "-i", f"images/{file}",
                            "-o", f"gcode/outputs/{file.replace('.png', '.gcode')}"] \
                                + args_spread)

# for file in os.listdir("gcode/outputs"):
#     if file.endswith(".gcode"):
#         subprocess.run(["python", "analyze_gcode.py", f"gcode/outputs/{file}"])