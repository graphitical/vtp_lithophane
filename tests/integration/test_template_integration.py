#!/usr/bin/env python
"""
Integration tests for G-code template handling.
"""
from src.gcode.template_handler import GcodeTemplateHandler
from src.gcode.parameters import PrintParameters
from src.gcode.gcode_generator import generate_gcode
import os
import sys
import tempfile
import unittest
from pathlib import Path

# Add the project root directory to the path
sys.path.insert(0, os.path.abspath(
    os.path.join(os.path.dirname(__file__), '../..')))

# Import the modules to test


class TestTemplateIntegration(unittest.TestCase):
    """Integration tests for the template handling in G-code generation."""

    def setUp(self):
        """Set up the test environment."""
        # Create temporary template files
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_path = Path(self.temp_dir.name)

        # Create a start G-code template
        self.start_template_path = self.temp_path / "test_start.gcode"
        with open(self.start_template_path, 'w') as f:
            f.write("; Test Start G-code\n")
            f.write("M140 S{bed_temp} ; Set bed temperature\n")
            f.write(
                "M109 S{nozzle_temp} ; Set and wait for nozzle temperature\n")
            f.write("G1 X0 Y0 F{travel_speed} ; Move to origin\n")

        # Create an end G-code template
        self.end_template_path = self.temp_path / "test_end.gcode"
        with open(self.end_template_path, 'w') as f:
            f.write("; Test End G-code\n")
            f.write("G1 E-{retract_length} F{retract_speed} ; Retract\n")
            f.write("M104 S0 ; Turn off nozzle\n")
            f.write("M140 S0 ; Turn off bed\n")
            f.write("; Print completed in {print_time}\n")
            f.write("; Used {filament_used}mm of filament\n")

        # Create a mock image file
        self.mock_image_path = self.temp_path / "test_image.png"
        with open(self.mock_image_path, 'w') as f:
            f.write("mock image content")

        # Create the handler
        self.handler = GcodeTemplateHandler()

    def tearDown(self):
        """Clean up after the test."""
        self.temp_dir.cleanup()

    def test_template_processing(self):
        """Test that templates are processed correctly."""
        # Test variables
        variables = {
            "bed_temp": 60,
            "nozzle_temp": 210,
            "travel_speed": 3000,
            "retract_length": 5.0,
            "retract_speed": 2000,
            "print_time": "1h 30m",
            "filament_used": "120.5"
        }

        # Process start template
        start_lines = self.handler.process_template(
            self.start_template_path, variables)
        self.assertEqual(len(start_lines), 4)
        self.assertIn("M140 S60", start_lines[1])
        self.assertIn("M109 S210", start_lines[2])
        self.assertIn("G1 X0 Y0 F3000", start_lines[3])

        # Process end template
        end_lines = self.handler.process_template(
            self.end_template_path, variables)
        self.assertEqual(len(end_lines), 6)
        self.assertIn("G1 E-5.0 F2000", end_lines[1])
        self.assertIn("Print completed in 1h 30m", end_lines[4])
        self.assertIn("Used 120.5mm of filament", end_lines[5])

    def test_template_variable_extraction(self):
        """Test that variables are correctly extracted from templates."""
        # Extract variables from start template
        start_vars = self.handler.get_template_variables(
            self.start_template_path)
        self.assertIn("bed_temp", start_vars)
        self.assertIn("nozzle_temp", start_vars)
        self.assertIn("travel_speed", start_vars)

        # Extract variables from end template
        end_vars = self.handler.get_template_variables(self.end_template_path)
        self.assertIn("retract_length", end_vars)
        self.assertIn("retract_speed", end_vars)
        self.assertIn("print_time", end_vars)
        self.assertIn("filament_used", end_vars)


if __name__ == "__main__":
    unittest.main()
