# src/gui/main_window.py

import os
import sys
from pathlib import Path

import numpy as np
from PySide6.QtCore import QDir, QSettings, Qt, Slot
from PySide6.QtWidgets import (QApplication, QFileDialog, QHBoxLayout,
                               QMainWindow, QMessageBox, QSizePolicy, QWidget)

from gcode.gcode_generator import generate_gcode
from gcode.image_utils import LithophaneImage
from gcode.parameters import PrintParameters
from gui.gcode_view_widget import GCodeViewWidget
from gui.image_view_widget import ImageViewWidget
from gui.menu_bar import create_main_menu
from gui.settings_dialog import ProcessSettingsDialog

script_dir = os.path.dirname(os.path.realpath(__file__))


class DualViewWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("VTP Lithophane Designer")
        self.setGeometry(100, 100, 1200, 600)

        # Add this line to initialize QSettings
        self.settings = QSettings("VTP", "Lithophane")

        self.current_image_path = None
        self.settings_dialog = ProcessSettingsDialog(
            parent=self, image_path="")

        create_main_menu(self)

        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)

        main_layout = QHBoxLayout(central_widget)

        # --- Left View: Image Display ---
        self.image_view = ImageViewWidget()  # Use the custom widget
        main_layout.addWidget(self.image_view, 1)

        # --- Right View: GCode View ---
        params = self.settings_dialog.get_print_parameters()
        self.gcode_view = GCodeViewWidget(params.printer_bed_size_mm)
        main_layout.addWidget(self.gcode_view, 1)

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

    def load_image(self):
        """Opens a dialog to import an image and tells ImageViewWidget to display it."""
        # Get last used directory from settings
        last_dir = str(self.settings.value(
            "last_image_directory", QDir.homePath()))

        image_path, _ = QFileDialog.getOpenFileName(
            self, "Import Image", last_dir,
            "Images (*.png *.jpg *.jpeg *.bmp *.tiff);;All Files (*.*)"
        )

        if image_path:
            # Store the directory for next time
            self.settings.setValue(
                "last_image_directory", os.path.dirname(image_path))
            self.current_image_path = image_path

            # self.image_view.set_image_path(image_path)
            self.render_image()

            if hasattr(self, 'settings_dialog') and self.settings_dialog:
                self.settings_dialog.image_path.setText(
                    self.current_image_path)

    def render_image(self) -> None:
        if self.current_image_path is None:
            QMessageBox.warning(
                self, "No Image Loaded to Render", "Please load an image first.")
            return
        params = self.settings_dialog.get_print_parameters()
        if not params:
            QMessageBox.warning(
                self, "Invalid Settings", "Please configure the print settings first.")
            return

        lithophane_image = LithophaneImage(
            filepath=self.current_image_path,
            physical_print_width_mm=params.physical_print_width_mm
        )
        qlvls = self.settings_dialog.quantization_levels.value()
        if qlvls > 0:
            lithophane_image.quantize_img(qlvls)
        self.image_view.set_lithophane_image(lithophane_image)

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
            self.render_image()  # Reload image with new settings
        else:
            # User clicked Cancel - do not update settings
            QMessageBox.information(
                self, "Settings Cancelled", "Process settings were not changed.")

    def generate_gcode(self):
        """Generate G-code based on current settings."""
        try:
            # First check if settings dialog exists and has valid input
            if not self.settings_dialog:
                self.open_process_settings()
                if not self.settings_dialog:
                    return

            # Get last used directory from settings
            last_dir = str(self.settings.value(
                "last_gcode_directory", QDir.homePath()))

            # Ask for output file location
            output_path, _ = QFileDialog.getSaveFileName(
                self, "Save G-code", last_dir,
                "G-code Files (*.gcode);;All Files (*.*)"
            )

            if not output_path:
                return  # User cancelled

            output_path = Path(output_path)
            if output_path.suffix != ".gcode":
                output_path = output_path.with_suffix(".gcode")

            # Store directory for next time
            self.settings.setValue(
                "last_gcode_directory", os.path.dirname(str(output_path)))

            output_path = str(output_path)

            # Get the parameters from the settings dialog
            params = self.settings_dialog.get_print_parameters()

            # Create LithophaneImage object
            lithophane_image = LithophaneImage(
                filepath=params.image_filepath,
                physical_print_width_mm=params.physical_print_width_mm
            )

            # Generate G-code and render it
            gcode_lines, gcommands = generate_gcode(params, lithophane_image)
            points = []
            for command in gcommands:
                points.append(command.pos)
            points = np.array(points)
            # Replace NaN with previous value in the toolpath
            points[0, np.isnan(points[0])] = 0.0  # Ensure no Nan to start
            for row in range(1, points.shape[0]):
                points[row, np.isnan(points[row])] = points[row-1,
                                                            np.isnan(points[row])]

            if points.shape[0] > 2:
                self.gcode_view.add_lines(points, color='blue', width=1.0)
            else:
                QMessageBox.warning(
                    self, "Insufficient Data", "Not enough points to render G-code.")

            # Write G-code to output file
            with open(output_path, 'w') as f:
                f.write("\n".join(gcode_lines))

            QMessageBox.information(self, "G-code Generated",
                                    f"G-code successfully saved to {output_path}")

        except Exception as e:
            QMessageBox.critical(
                self, "Error", f"Failed to generate G-code: {str(e)}")
