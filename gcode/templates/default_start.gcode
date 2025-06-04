; Dummy Start Gcode
G21 ; Set units to millimeters
G90 ; Use absolute positioning
M83 ; E axis to relative mode
G28 ; Auto home
G1 Z5.0 F300 ; Lift nozzle after homing
G1 X0.0 Y0.0 F2000 ; Move to origin
G92 E0 ; Reset extruder position

; Set temperatures
M104 S{nozzle_temp} ; Set extruder temperature
M140 S{bed_temp} ; Set bed temperature
M190 S{bed_temp} ; Wait for bed to reach temperature
M109 S{nozzle_temp} ; Wait for extruder to reach temperature

; Set units and positioning
G21 ; Set units to millimeters
G90 ; Use absolute positioning
M83 ; E axis to relative mode

; Print settings: Nozzle Temp={nozzle_temp}°C, Bed Temp={bed_temp}°C
; Filament: Diameter={filament_diameter}mm
; Nozzle: Diameter={nozzle_diameter}mm