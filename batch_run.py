import subprocess
import os
import sys

overwrite = len(sys.argv) > 1 and sys.argv[1] == "F"

for i in range(101):
    if os.path.exists(f"images/grayscale{i:03d}.png"):
        if overwrite or not os.path.exists(f"gcode/outputs/grayscale{i:03d}.gcode"):
            subprocess.run(["python", "lithophize.py",
                            "-i", f"images/grayscale{i:03d}.png",
                            "-w", "10",
                            "-o", f"gcode/outputs/grayscale{i:03d}.gcode",
                            "--sample-res", "5",
                            "--alpha", "1.5",
                            "--in-flow-rate", "200",
                            "--layers", "2"])

# for file in os.listdir("gcode/outputs"):
#     if file.endswith(".gcode"):
#         subprocess.run(["python", "analyze_gcode.py", f"gcode/outputs/{file}"])

for file in os.listdir("images"):
    if file.startswith("test_grid_") and file.endswith(".png"):
        if overwrite or not os.path.exists(f"gcode/outputs/{file.replace('.png', '.gcode')}"):
            subprocess.run(["python", "lithophize.py",
                            "-i", f"images/{file}",
                            "-w", "20",
                            "-o", f"gcode/outputs/{file.replace('.png', '.gcode')}",
                            "--sample-res", "5",
                            "--alpha", "1.5",
                            "--in-flow-rate", "200",
                            "--layers", "2"])
