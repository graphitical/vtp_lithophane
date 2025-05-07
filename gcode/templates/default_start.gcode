; Dummy Start Gcode
G21 ; Set units to millimeters
G90 ; Use absolute positioning
M82 ; E axis to absolute mode
G28 ; Auto home
G1 Z5.0 F300 ; Lift nozzle after homing
G1 X0.0 Y0.0 F2000 ; Move to origin
G92 E0 ; Reset extruder position
