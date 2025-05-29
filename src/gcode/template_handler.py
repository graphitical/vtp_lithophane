# src/gcode/template_handler.py

import os
import re
import string
from pathlib import Path
from typing import Any, Dict, List, Optional, Union


class GcodeTemplateHandler:
    """
    A class for handling G-code templates with variable replacement.
    """

    def __init__(self):
        """Initialize the GcodeTemplateHandler."""
        self.template_dir = Path(os.path.dirname(os.path.dirname(
            os.path.dirname(__file__)))) / "gcode" / "templates"

    def get_default_template_path(self, template_type: str) -> Path:
        """
        Get the default template path for a specific template type.

        Args:
            template_type: Either "start" or "end"

        Returns:
            Path to the default template file
        """
        if template_type.lower() == "start":
            return self.template_dir / "template_start.gcode"
        elif template_type.lower() == "end":
            return self.template_dir / "template_end.gcode"
        else:
            raise ValueError(
                f"Invalid template type: {template_type}. Must be 'start' or 'end'")

    def list_available_templates(self, template_type: Optional[str] = None) -> List[str]:
        """
        List available templates in the template directory.

        Args:
            template_type: Optional filter for "start" or "end" templates

        Returns:
            List of template filenames
        """
        templates = []
        for file in self.template_dir.glob("*.gcode"):
            if template_type:
                if template_type.lower() == "start" and "start" in file.name.lower():
                    templates.append(file.name)
                elif template_type.lower() == "end" and "end" in file.name.lower():
                    templates.append(file.name)
            else:
                templates.append(file.name)
        return templates

    def process_template(self, template_path: Union[str, Path], variables: Dict[str, Any]) -> List[str]:
        """
        Process a G-code template by replacing variables with their values.

        Args:
            template_path: Path to the template file
            variables: Dictionary of variables to replace in the template

        Returns:
            List of processed G-code lines
        """
        template_path = Path(template_path)
        if not template_path.exists():
            raise FileNotFoundError(
                f"Template file not found: {template_path}")

        try:
            with open(template_path, 'r') as f:
                template_lines = [line.strip() for line in f if line.strip()]

            processed_lines = []
            for line in template_lines:
                # Use string formatting to replace variables
                try:
                    # Handle both {variable} and {variable:.2f} formatting
                    processed_line = line

                    # Find all variables in the format {name} in the line
                    matches = re.findall(r'\{([^{}:]+)(:[^{}]+)?\}', line)

                    # If any variables are found, process them with string formatting
                    if matches:
                        try:
                            processed_line = line.format(**variables)
                        except KeyError as e:
                            # If a variable is missing, keep the template as is and add a comment
                            processed_line = line + \
                                f" ; WARNING: Missing variable {e}"

                    processed_lines.append(processed_line)
                except Exception as e:
                    # If there's an error, add a comment and keep the original line
                    processed_lines.append(f"{line} ; ERROR: {str(e)}")

            return processed_lines
        except Exception as e:
            raise RuntimeError(
                f"Error processing template {template_path}: {str(e)}")

    def get_template_variables(self, template_path: Union[str, Path]) -> List[str]:
        """
        Extract variable names from a template file.

        Args:
            template_path: Path to the template file

        Returns:
            List of variable names found in the template
        """
        template_path = Path(template_path)
        if not template_path.exists():
            raise FileNotFoundError(
                f"Template file not found: {template_path}")

        with open(template_path, 'r') as f:
            content = f.read()

        # Find all variables in the format {name} or {name:format}
        variables = set(re.findall(r'\{([^{}:]+)(:[^{}]+)?\}', content))
        # Extract just the variable name without formatting
        return [var[0] for var in variables]


if __name__ == "__main__":
    # Example usage
    handler = GcodeTemplateHandler()

    # Print available templates
    print("Available templates:")
    templates = handler.list_available_templates()
    for template in templates:
        print(f"  - {template}")

    # Example of processing a start template
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
        for line in processed_lines[:5]:  # Print first 5 lines as example
            print(f"  {line}")
        print("  ...")

    except Exception as e:
        print(f"Error: {str(e)}")
