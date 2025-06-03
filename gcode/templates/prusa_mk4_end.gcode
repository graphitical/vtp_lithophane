; Prusa MK4 Specific End Gcode
; -------------------------
G0 F10800.000 
M104 S0 ; Turn off nozzle temp
M140 S0 ; Turn off bed temp
M107 ; turn off fan 
G91 ; Relative positioning
G1 E-{retract_length} F{retract_speed} ; Retract
G90 ; Absolute positioning
G1 Z{z_lift} F{travel_speed} ; Lift nozzle
G28 X Y ; Home X and Y
M84 ; Disable motors

; Print completed
; Estimated Duration: {print_time}
; Material used: {filament_used}mm
; Edot = {e_dot} mm/min
; alpha = {alpha}
; Nozzle diameter = {nozzle_diameter} mm
; Filament diameter = {filament_diameter} mm