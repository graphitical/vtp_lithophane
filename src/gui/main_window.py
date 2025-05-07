# src/gui/main_window.py

import os
import sys
from pathlib import Path

from PySide6.QtCore import QDir, Qt, Slot
from PySide6.QtWidgets import (QApplication, QFileDialog, QHBoxLayout,
                               QMainWindow, QMessageBox, QSizePolicy, QWidget)

from gcode.gcode_generator import generate_gcode
from gcode.image_utils import LithophaneImage
from gcode.parameters import PrintParameters

from .image_view_widget import ImageViewWidget
from .menu_bar import create_main_menu
from .pyvista_widget import PyVistaWidget
from .settings_dialog import ProcessSettingsDialog

script_dir = os.path.dirname(os.path.realpath(__file__))


class DualViewWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("VTP Lithophane Designer")
        self.setGeometry(100, 100, 1200, 600)

        self.current_image_path = None
        self.settings_dialog = None

        create_main_menu(self)

        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)

        main_layout = QHBoxLayout(central_widget)

        # --- Left View: Image Display ---
        self.image_view = ImageViewWidget()  # Use the custom widget
        main_layout.addWidget(self.image_view, 1)

        # --- Right View: Placeholder for PyVista ---
        # Pass initial bed dimensions from settings to the PyVistaWidget
        self.pyvista_view = PyVistaWidget()
        main_layout.addWidget(self.pyvista_view, 1)

        central_widget.setLayout(main_layout)

    def open_file(self):
        """Open a project file."""
        # Implement project file opening logic
        QMessageBox.information(self, "Not Implemented",
                                "Open file functionality not implemented yet.")

    def save_file(self):
        """Save the current project."""
        # Implement project saving logic
        QMessageBox.information(self, "Not Implemented",
                                "Save file functionality not implemented yet.")

    def import_image(self):
        """Opens a dialog to import an image and tells ImageViewWidget to display it."""
        start_dir = QDir.homePath()
        if self.current_image_path and os.path.exists(os.path.dirname(self.current_image_path)):
            start_dir = os.path.dirname(self.current_image_path)

        file_name, _ = QFileDialog.getOpenFileName(
            self,
            "Import Image",
            start_dir,
            "Image Files (*.png *.jpg *.jpeg *.bmp *.gif);;All Files (*)"
        )
        if file_name:
            self.current_image_path = file_name
            # Delegate to ImageViewWidget
            self.image_view.set_image_path(self.current_image_path)

    def open_process_settings(self):
        """Open the process settings dialog."""
        if not self.settings_dialog:
            image_path = self.current_image_path if self.current_image_path else ""
            self.settings_dialog = ProcessSettingsDialog(parent=self,
                                                         image_path=image_path)

            self.settings_dialog.image_selected.connect(
                self.image_view.set_image_path)

        if self.settings_dialog.exec():
            # User clicked OK - settings have been saved internally
            QMessageBox.information(
                self, "Settings Saved", "Process settings have been updated.")

    def generate_gcode(self):
        """Generate G-code based on current settings."""
        try:
            # First check if settings dialog exists and has valid input
            if not self.settings_dialog:
                self.open_process_settings()
                if not self.settings_dialog:
                    return

            # Ask for output file location
            output_path, _ = QFileDialog.getSaveFileName(
                self, "Save G-code", QDir.homePath(),
                "G-code Files (*.gcode);;All Files (*.*)"
            )

            if not output_path:
                return  # User cancelled

            output_path = Path(output_path)
            if output_path.suffix != ".gcode":
                output_path = output_path.with_suffix(".gcode")

            output_path = str(output_path)

            # Get the parameters from the settings dialog
            params = self.settings_dialog.get_print_parameters(output_path)

            # Create LithophaneImage object
            lithophane_image = LithophaneImage(
                filepath=params.image_filepath,
                physical_print_width_mm=params.physical_print_width_mm
            )

            # Generate G-code
            gcode_lines = generate_gcode(params, lithophane_image)

            # Write G-code to output file
            with open(output_path, 'w') as f:
                f.write("\n".join(gcode_lines))

            QMessageBox.information(self, "G-code Generated",
                                    f"G-code successfully saved to {output_path}")

        except Exception as e:
            QMessageBox.critical(
                self, "Error", f"Failed to generate G-code: {str(e)}")
