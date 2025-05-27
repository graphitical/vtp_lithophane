import subprocess
import os

for i in range(101):
    if os.path.exists(f"images/grayscale{i:03d}.png") and not os.path.exists(f"gcode/outputs/grayscale{i:03d}.gcode"):
        subprocess.run(["python", "lithophize.py",
                        "-i", f"images/grayscale{i:03d}.png",
                        "-w", "10",
                        "-o", f"gcode/outputs/grayscale{i:03d}.gcode",
                        "--start-gcode", "",
                        "--end-gcode", ""])
