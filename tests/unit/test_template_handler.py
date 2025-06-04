#!/usr/bin/env python
"""
Unit tests for the GcodeTemplateHandler class.
"""
import os
import sys
import unittest
from pathlib import Path
from unittest.mock import mock_open, patch

from gcode.template_handler import GcodeTemplateHandler

# Add the project root directory to the path
sys.path.insert(0, os.path.abspath(
    os.path.join(os.path.dirname(__file__), '../..')))

# Import the module to test


class TestGcodeTemplateHandler(unittest.TestCase):
    """Test cases for the GcodeTemplateHandler class."""

    def setUp(self):
        """Set up the test environment."""
        self.handler = GcodeTemplateHandler()
        self.test_template_dir = self.handler.template_dir

    def test_initialization(self):
        """Test that the handler initializes correctly."""
        self.assertIsInstance(self.handler, GcodeTemplateHandler)
        self.assertTrue(self.test_template_dir.exists(
        ), f"Template directory {self.test_template_dir} does not exist")

    def test_get_default_template_path(self):
        """Test the get_default_template_path method."""
        # Test for start template
        start_path = self.handler.get_default_template_path("start")
        self.assertEqual(start_path, self.test_template_dir /
                         "template_start.gcode")

        # Test for end template
        end_path = self.handler.get_default_template_path("end")
        self.assertEqual(end_path, self.test_template_dir /
                         "template_end.gcode")

        # Test for invalid template type
        with self.assertRaises(ValueError):
            self.handler.get_default_template_path("invalid")

    def test_list_available_templates(self):
        """Test the list_available_templates method."""
        templates = self.handler.list_available_templates()
        # Check that we have at least the default templates
        self.assertIn("template_start.gcode", templates)
        self.assertIn("template_end.gcode", templates)

        # Test with filter for start templates
        start_templates = self.handler.list_available_templates("start")
        for template in start_templates:
            self.assertIn("start", template.lower())

        # Test with filter for end templates
        end_templates = self.handler.list_available_templates("end")
        for template in end_templates:
            self.assertIn("end", template.lower())

    @patch("builtins.open", new_callable=mock_open, read_data="; Test header\nG1 X10 Y10 F{travel_speed}\nM104 S{nozzle_temp}\n")
    def test_process_template(self, mock_file):
        """Test the process_template method."""
        # Mock Path.exists to return True
        with patch.object(Path, "exists", return_value=True):
            variables = {
                "travel_speed": 3000,
                "nozzle_temp": 210
            }

            processed_lines = self.handler.process_template(
                "mock_path", variables)

            # Check that variables are replaced
            self.assertEqual(processed_lines, [
                "; Test header",
                "G1 X10 Y10 F3000",
                "M104 S210"
            ])

    @patch("builtins.open", new_callable=mock_open, read_data="G1 X10 Y10 F{travel_speed}\nM104 S{nozzle_temp}\nM140 S{bed_temp}\n")
    def test_process_template_missing_variable(self, mock_file):
        """Test the process_template method with missing variables."""
        # Mock Path.exists to return True
        with patch.object(Path, "exists", return_value=True):
            variables = {
                "travel_speed": 3000,
                # nozzle_temp and bed_temp are missing
            }

            # Should not raise an exception but add warnings
            processed_lines = self.handler.process_template(
                "mock_path", variables)

            # Check that the first variable is replaced but the missing one has a warning
            self.assertEqual(processed_lines[0], "G1 X10 Y10 F3000")
            self.assertIn("WARNING: Missing variable", processed_lines[1])
            self.assertIn("WARNING: Missing variable", processed_lines[2])

    def test_process_template_missing_file(self):
        """Test the process_template method with a missing file."""
        # The path doesn't exist
        with patch.object(Path, "exists", return_value=False):
            with self.assertRaises(FileNotFoundError):
                self.handler.process_template("nonexistent_path", {})

    @patch("builtins.open", new_callable=mock_open, read_data="G1 X10 Y10 F{travel_speed}\nM104 S{nozzle_temp:.1f}\nM140 S{bed_temp}\n")
    def test_get_template_variables(self, mock_file):
        """Test the get_template_variables method."""
        # Mock Path.exists to return True
        with patch.object(Path, "exists", return_value=True):
            variables = self.handler.get_template_variables("mock_path")

            # Check that all variables are extracted
            self.assertIn("travel_speed", variables)
            self.assertIn("nozzle_temp", variables)
            self.assertIn("bed_temp", variables)
            self.assertEqual(len(variables), 3)


if __name__ == "__main__":
    unittest.main()
