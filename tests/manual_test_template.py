#!/usr/bin/env python
"""
Manual test script for verifying G-code template functionality.
"""
import os
import sys

from src.gcode.template_handler import GcodeTemplateHandler

# Add the project root directory to the path
sys.path.insert(0, os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..')))


def test_template_functionality():
    """Test the GcodeTemplateHandler functionality with manual verification."""
    print("Testing GcodeTemplateHandler functionality")

    handler = GcodeTemplateHandler()

    # Print available templates
    print("\nAvailable templates:")
    templates = handler.list_available_templates()
    for template in templates:
        print(f"  - {template}")

    # Test start template
    try:
        start_template = handler.get_default_template_path("start")
        variables_needed = handler.get_template_variables(start_template)
        print(f"\nVariables needed for {start_template.name}:")
        for var in variables_needed:
            print(f"  - {var}")

        # Example variable values
        variables = {
            "bed_temp": 60,
            "nozzle_temp": 210,
            "travel_speed": 3000,
            "priming_line_length": 120,
            "filament_diameter": 1.75,
            "nozzle_diameter": 0.4
        }

        # Process the template
        processed_lines = handler.process_template(start_template, variables)
        print("\nProcessed Start G-code:")
        for line in processed_lines[:10]:  # Print first 10 lines as example
            print(f"  {line}")
        print("  ...")

    except Exception as e:
        print(f"Error with start template: {str(e)}")

    # Test end template
    try:
        end_template = handler.get_default_template_path("end")
        variables_needed = handler.get_template_variables(end_template)
        print(f"\nVariables needed for {end_template.name}:")
        for var in variables_needed:
            print(f"  - {var}")

        # Example variable values
        variables = {
            "retract_length": 5.0,
            "retract_speed": 2000,
            "z_lift": 100,
            "travel_speed": 3000,
            "print_time": "1h 30m",
            "filament_used": "120.5"
        }

        # Process the template
        processed_lines = handler.process_template(end_template, variables)
        print("\nProcessed End G-code:")
        for line in processed_lines:  # Print all lines
            print(f"  {line}")

    except Exception as e:
        print(f"Error with end template: {str(e)}")


if __name__ == "__main__":
    test_template_functionality()
