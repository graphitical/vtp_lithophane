; Prusa MK4 Specific Start Gcode
; -------------------------

M73 P0 R0 
M201 X9000 Y9000 Z500 E10000 ; sets maximum accelerations, mm/sec^2 
M203 X500 Y500 Z12 E120 ; sets maximum feedrates, mm/sec 
M204 P2000 R1500 T2000 ; sets acceleration (P, T) and retract acceleration (R), mm/sec^2 
M205 X10.00 Y10.00 Z0.20 E4.50 ; sets the jerk limits, mm/sec 
M205 S0 T0 ; sets the minimum extruding and travel feed rate, mm/sec 
M107 ; turns off fan 
M862.3 P "MK4" ; printer model check 
M862.1 P0.4 ; nozzle diameter check 
G90 ; use absolute coordinates 
M83  ; extruder relative mode 

; Set temperatures
M104 S{nozzle_temp} ; Set extruder temperature
M140 S{bed_temp} ; Set bed temperature
M190 S{bed_temp} ; Wait for bed to reach temperature
M109 S{nozzle_temp} ; Wait for extruder to reach temperature

; Bed homing and leveling
G28 W; Auto home
; G80 ; Auto bed leveling
G0 Z5.0 F300 ; Lift nozzle after homing
G0 X0.0 Y0.0 F{travel_speed} ; Move to origin
G92 E0 ; Reset extruder position

; Set units and positioning
G21 ; Set units to millimeters
G90 ; Use absolute positioning
M83 ; E axis to relative mode

; Print settings: Nozzle Temp={nozzle_temp}°C, Bed Temp={bed_temp}°C
; Filament: Diameter={filament_diameter}mm
; Nozzle: Diameter={nozzle_diameter}mm
