#!/usr/bin/env python
"""
Unit tests for G-code generation with templates.
"""
import os
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, mock_open, patch

from gcode.gcode_generator import GCodeType, GCommand, generate_gcode
from gcode.parameters import PrintParameters
from gcode.template_handler import GcodeTemplateHandler

# Add the project root directory to the path
sys.path.insert(0, os.path.abspath(
    os.path.join(os.path.dirname(__file__), '../..')))

# Import the modules to test


class TestGcodeGenerator(unittest.TestCase):
    """Tests for G-code generation with templates."""

    def setUp(self):
        """Set up the test environment."""
        # Create mock image and parameters for testing
        self.mock_image = MagicMock()
        self.mock_image.physical_print_width_mm = 20.0
        self.mock_image.physical_print_height_mm = 20.0
        self.mock_image.get_pixel_value.return_value = (
            0.5, 0.5, 0)  # Mock pixel values

        # Basic print parameters
        self.params = PrintParameters(
            image_filepath="dummy_image.png",
            physical_print_width_mm=20.0,
            num_layers=4,
            v_star_hd=0.15,
            v_star_ld=0.4,
            h_star_hd=6.93,
            h_star_ld=14.81,
            alpha=1.0,
            e_dot=50.0,
            line_spacing_mm=1.2,
            sampling_resolution_mm=1.0,
            dz_mm=1.27,
            start_gcode_filepath="gcode/templates/default_start.gcode",
            end_gcode_filepath="gcode/templates/default_end.gcode",
            bed_temp=60.0,
            nozzle_temp=210.0,
            retract_length=5.0,
            retract_speed=2000.0
        )

    @patch('gcode.gcode_generator._generate_entire_toolpath')
    @patch('gcode.gcode_generator._calculate_ZFdE')
    @patch('gcode.gcode_generator._calc_VH_stars')
    @patch('gcode.gcode_generator._refine_segments_along_path')
    @patch('gcode.template_handler.GcodeTemplateHandler')
    def test_gcode_generation_with_templates(self, mock_handler_class, mock_refine, mock_calc_stars, mock_calc_zfde, mock_toolpath):
        """Test that generate_gcode uses templates correctly."""
        # Configure mocks
        mock_handler = MagicMock()
        mock_handler_class.return_value = mock_handler

        # Mock the start and end G-code template processing
        mock_handler.process_template.side_effect = [
            ["M140 S60", "M109 S210", "G28"],  # Start G-code
            ["G1 E-5 F2000", "M104 S0", "M140 S0"]  # End G-code
        ]

        # Mock entire toolpath generation
        mock_toolpath.return_value = [(0, MagicMock(), MagicMock())]
        mock_calc_stars.return_value = (0.3, 10.0)  # v_star, h_star
        mock_calc_zfde.return_value = (1.0, 3000.0, 0.5)  # Z, F, dE
        # mock_refine.return_value = (
        # ["G1 X10 Y10 Z1.0 E0.5 F3000"], 0.5, MagicMock())
        gc = GCommand(
            type=GCodeType.G1,
            x=10.0,
            y=10.0,
            z=1.0,
            e=0.5,
            f=3000.0,
            comment="Test command"
        )
        mock_refine.return_value = ([gc], 0.5, MagicMock())

        # Run the function
        result = generate_gcode(self.params, self.mock_image)[0]

        # Check that the template handler was called correctly for start G-code
        mock_handler.process_template.assert_any_call(self.params.start_gcode_filepath, {
            'bed_temp': self.params.bed_temp,
            'nozzle_temp': self.params.nozzle_temp,
            'travel_speed': self.params.f_travel,
            'priming_line_length': 120,
            'filament_diameter': self.params.D_F,
            'nozzle_diameter': self.params.D_N,
        })

        # Check that the template handler was called correctly for end G-code
        # This call happens later in the function, so we check it separately
        second_call_args = mock_handler.process_template.call_args_list[1][0]
        self.assertEqual(second_call_args[0], self.params.end_gcode_filepath)
        self.assertEqual(
            second_call_args[1]['retract_length'], self.params.retract_length)
        self.assertEqual(
            second_call_args[1]['retract_speed'], self.params.retract_speed)
        self.assertEqual(
            second_call_args[1]['travel_speed'], self.params.f_travel)
        self.assertIn('print_time', second_call_args[1])
        self.assertIn('filament_used', second_call_args[1])

        # Check that the templates were included in the output
        self.assertIn("M140 S60", result)
        self.assertIn("M109 S210", result)
        self.assertIn("G28", result)
        self.assertIn("G1 E-5 F2000", result)
        self.assertIn("M104 S0", result)
        self.assertIn("M140 S0", result)

    @patch('builtins.open', new_callable=mock_open, read_data="; Dummy G-code")
    @patch('gcode.gcode_generator._generate_entire_toolpath')
    @patch('gcode.template_handler.GcodeTemplateHandler')
    def test_gcode_generation_with_fallback(self, mock_handler_class, mock_toolpath, mock_open_file):
        """Test error message insertion when template processing fails."""
        # Configure mocks
        mock_handler = MagicMock()
        mock_handler_class.return_value = mock_handler
        mock_handler.process_template.side_effect = RuntimeError(
            "Template processing failed")
        mock_toolpath.return_value = []

        self.params.num_layers = 0
        self.params.start_gcode_filepath = 'i_do_not_exist.gcode'
        self.params.end_gcode_filepath = 'i_also_do_not_exist.gcode'
        result = generate_gcode(self.params, self.mock_image)[0]

        # Check that error messages were inserted
        self.assertIn("START GCODE TEMPLATE ERROR", ''.join(result))
        self.assertIn("END GCODE TEMPLATE ERROR", ''.join(result))


if __name__ == "__main__":
    unittest.main()
