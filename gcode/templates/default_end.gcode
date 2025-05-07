; Dummy End Gcode
M104 S0 ; Turn off nozzle temp
M140 S0 ; Turn off bed temp
G91 ; Relative positioning
G1 E-5 F2000 ; Retract
G90 ; Absolute positioning
G1 Z100 F3000 ; Lift nozzle
G28 X Y ; Home X and Y
