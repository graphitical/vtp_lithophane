#!/usr/bin/env python
"""
Unit tests for the PrintParameters class.
"""
from src.gcode.parameters import PrintParameters
import os
import sys
import unittest
from pathlib import Path

# Add the project root directory to the path
sys.path.insert(0, os.path.abspath(
    os.path.join(os.path.dirname(__file__), '../..')))

# Import the module to test


class TestPrintParameters(unittest.TestCase):
    """Test cases for the PrintParameters class."""

    def setUp(self):
        """Set up the test environment."""
        # Create dummy paths for required file parameters
        self.dummy_image_path = "dummy_image.png"
        self.dummy_start_gcode = "dummy_start.gcode"
        self.dummy_end_gcode = "dummy_end.gcode"

    def test_initialization_with_defaults(self):
        """Test initialization with default values."""
        params = PrintParameters(
            image_filepath=self.dummy_image_path,
            physical_print_width_mm=100.0,
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
            start_gcode_filepath=self.dummy_start_gcode,
            end_gcode_filepath=self.dummy_end_gcode
        )

        # Check default values for temperature and retraction settings
        self.assertEqual(params.bed_temp, 60.0,
                         "Default bed temperature should be 60.0°C")
        self.assertEqual(params.nozzle_temp, 200.0,
                         "Default nozzle temperature should be 200.0°C")
        self.assertEqual(params.retract_length, 5.0,
                         "Default retraction length should be 5.0mm")
        self.assertEqual(params.retract_speed, 2000.0,
                         "Default retraction speed should be 2000.0mm/min")

    def test_initialization_with_custom_values(self):
        """Test initialization with custom values."""
        params = PrintParameters(
            image_filepath=self.dummy_image_path,
            physical_print_width_mm=100.0,
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
            start_gcode_filepath=self.dummy_start_gcode,
            end_gcode_filepath=self.dummy_end_gcode,
            bed_temp=80.0,
            nozzle_temp=230.0,
            retract_length=6.5,
            retract_speed=2500.0
        )

        # Check custom values for temperature and retraction settings
        self.assertEqual(params.bed_temp, 80.0,
                         "Bed temperature should be set to 80.0°C")
        self.assertEqual(params.nozzle_temp, 230.0,
                         "Nozzle temperature should be set to 230.0°C")
        self.assertEqual(params.retract_length, 6.5,
                         "Retraction length should be set to 6.5mm")
        self.assertEqual(params.retract_speed, 2500.0,
                         "Retraction speed should be set to 2500.0mm/min")

    def test_post_init_calculations(self):
        """Test post-initialization calculations."""
        params = PrintParameters(
            image_filepath=self.dummy_image_path,
            physical_print_width_mm=100.0,
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
            start_gcode_filepath=self.dummy_start_gcode,
            end_gcode_filepath=self.dummy_end_gcode,
            D_F=1.75,  # 1.75mm filament
            D_N=0.4    # 0.4mm nozzle
        )

        # Check filament cross-sectional area calculation
        expected_filament_area = 3.14159 * (1.75 / 2) ** 2
        self.assertAlmostEqual(params.A_F, expected_filament_area, delta=0.001,
                               msg="Filament cross-sectional area calculation incorrect")

        # Check nozzle thread area calculation (including die swell)
        expected_thread_area = 3.14159 * (0.4 / 2) ** 2 * 1.0  # alpha=1.0
        self.assertAlmostEqual(params.A_T, expected_thread_area, delta=0.001,
                               msg="Nozzle thread area calculation incorrect")


if __name__ == "__main__":
    unittest.main()
