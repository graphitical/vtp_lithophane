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
                            "-o", f"gcode/outputs/grayscale{i:03d}.gcode"])
        if os.path.exists(f"gcode/outputs/grayscale{i:03d}.gcode"):
            subprocess.run(["python", "analyze_gcode.py", f"gcode/outputs/grayscale{i:03d}.gcode"])
