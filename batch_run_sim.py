import os
os.chdir("../elasticrods/build")
import subprocess

timestep = "1e-4"
damping = "0.05"
lame1 = "20"
lame2 = "20"

# ./extrusion -F ../gcode/PLA_Spread.gcode --headless -T 1e-4 -D 0.05 -L 140 -M 30
# ./extrusion -F ../../vtp_lithophane/gcode/outputs/ST_test_grid_31.gcode -T 1e-4 -D 0.1 -L 20 -M 20

# for file in os.listdir("../../vtp_lithophane/gcode/outputs"):
#     if file.endswith(".gcode") and file.startswith("test_grid_"):
#         gcode_file = f"../../vtp_lithophane/gcode/outputs/{file}"
#         output_file = f"../outputs/{file.split('.')[0]}"
#         print(" ".join(["./extrusion", "--headless", "-F", gcode_file, "-O", output_file, "-T", timestep, "-D", damping, "-L", lame1, "-M", lame2]))
#         subprocess.run(["./extrusion", "--headless", "-F", gcode_file, "-O", output_file, "-T", timestep, "-D", damping, "-L", lame1, "-M", lame2])

for file in os.listdir("../../vtp_lithophane/gcode/outputs"):
    if file.endswith(".gcode") and file.startswith("edot100"):
        gcode_file = f"../../vtp_lithophane/gcode/outputs/{file}"
        output_file = f"../outputs/{file.split('.')[0]}"
        print(" ".join(["./extrusion", "--headless", "-F", gcode_file, "-O", output_file, "-T", timestep, "-D", damping, "-L", lame1, "-M", lame2]))
        subprocess.run(["./extrusion", "--headless", "-F", gcode_file, "-O", output_file, "-T", timestep, "-D", damping, "-L", lame1, "-M", lame2])


# for file in os.listdir("../../vtp_lithophane/gcode/outputs"):
#     if file.endswith(".gcode") and file.startswith("grayscale"):
#         filename = file.split("/")[-1].split(".")[0]
#         print("\n=====================================", flush=True)
#         print(f"Running extrusion for {filename}", flush=True)
#         subprocess.run(["./extrusion", "--headless", "-F", f"../../vtp_lithophane/gcode/outputs/{file}", "-O", f"../outputs/{filename}", "-T", timestep])#, "-D", damping])
