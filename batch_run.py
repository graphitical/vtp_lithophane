import subprocess
import os
import sys

overwrite = sys.argv[1] == "F"

for i in range(101):
    if os.path.exists(f"images/grayscale{i:03d}.png"):
        if overwrite or not os.path.exists(f"gcode/outputs/grayscale{i:03d}.gcode"):
            subprocess.run(["python", "lithophize.py",
                            "-i", f"images/grayscale{i:03d}.png",
                            "-w", "10",
                            "-o", f"gcode/outputs/grayscale{i:03d}.gcode"])
                            # "--start-gcode", "",
                            # "--end-gcode", ""])
