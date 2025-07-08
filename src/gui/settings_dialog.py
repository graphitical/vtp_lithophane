# src/gui/settings_dialog.py

import os

from PySide6.QtCore import QDir, QSettings, Qt, Signal
from PySide6.QtWidgets import (QDialog, QDialogButtonBox, QDoubleSpinBox,
                               QFileDialog, QFormLayout, QHBoxLayout, QLabel,
                               QLineEdit, QPushButton, QSpinBox, QTabWidget,
                               QVBoxLayout, QWidget)

from gcode.gcode_generator import parse_line_spacing_list
from gcode.parameters import PrintParameters


class ProcessSettingsDialog(QDialog):
    """Dialog for configuring G-code generation parameters."""

    image_selected = Signal(str)

    def __init__(self, parent=None, image_path=None):
        super().__init__(parent)
        self.setWindowTitle("Process Settings")
        self.setMinimumWidth(500)

        # Settings
        self.settings = QSettings("VTP", "Lithophane")

        self.setup_ui()
        self.load_settings()

        print(image_path)
        if image_path:
            self.image_path.setText(image_path)
        else:
            self.image_path.setText("")

    def setup_ui(self):
        """Set up the user interface."""
        main_layout = QVBoxLayout(self)

        # Tabs for organizing parameters
        tab_widget = QTabWidget()
        main_layout.addWidget(tab_widget)

        process_tab = QWidget()
        process_layout = QFormLayout(process_tab)
        tab_widget.addTab(process_tab, "Process Parameters")

        # Image and Dimensions Fields
        self.image_path = QLineEdit()
        self.image_path.setReadOnly(True)
        # browse_image_btn = QPushButton("Browse...")
        # browse_image_btn.clicked.connect(self.browse_image)
        image_layout = QHBoxLayout()
        image_layout.addWidget(self.image_path)
        # image_layout.addWidget(browse_image_btn)
        process_layout.addRow("Image File:", image_layout)

        self.physical_width = QDoubleSpinBox()
        self.physical_width.setRange(1, 1000)
        self.physical_width.setValue(100)
        self.physical_width.setSuffix(" mm")
        process_layout.addRow("Physical Width:", self.physical_width)

        self.sampling_resolution = QDoubleSpinBox()
        self.sampling_resolution.setRange(0.1, 10.0)
        self.sampling_resolution.setSingleStep(0.1)
        self.sampling_resolution.setValue(1.0)
        self.sampling_resolution.setSuffix(" mm")
        process_layout.addRow("Sampling Resolution:",
                              self.sampling_resolution)

        self.layers = QSpinBox()
        self.layers.setRange(1, 1000)
        self.layers.setValue(4)
        process_layout.addRow("Number of Layers:", self.layers)

        # VTP Parameters Tab
        vtp_tab = QWidget()
        vtp_layout = QFormLayout(vtp_tab)
        tab_widget.addTab(vtp_tab, "VTP Parameters")

        # VTP Specific Parameters
        self.v_star_hd = QDoubleSpinBox()
        self.v_star_hd.setRange(0.01, 1.0)
        self.v_star_hd.setSingleStep(0.01)
        self.v_star_hd.setValue(0.15)
        vtp_layout.addRow("V* High Density:", self.v_star_hd)

        self.h_star_hd = QDoubleSpinBox()
        self.h_star_hd.setRange(0.1, 50.0)
        self.h_star_hd.setSingleStep(0.1)
        self.h_star_hd.setValue(6.93)
        vtp_layout.addRow("H* High Density:", self.h_star_hd)

        self.v_star_ld = QDoubleSpinBox()
        self.v_star_ld.setRange(0.01, 1.0)
        self.v_star_ld.setSingleStep(0.01)
        self.v_star_ld.setValue(0.4)
        vtp_layout.addRow("V* Low Density:", self.v_star_ld)

        self.h_star_ld = QDoubleSpinBox()
        self.h_star_ld.setRange(0.1, 50.0)
        self.h_star_ld.setSingleStep(0.1)
        self.h_star_ld.setValue(14.81)
        vtp_layout.addRow("H* Low Density:", self.h_star_ld)

        self.line_spacing = QDoubleSpinBox()
        self.line_spacing.setRange(0.1, 100.0)
        self.line_spacing.setSingleStep(0.1)
        self.line_spacing.setValue(1.2)
        self.line_spacing.setSuffix(" mm")
        vtp_layout.addRow("Line Spacing (dL):", self.line_spacing)

        self.line_spacing_list = QLineEdit()
        self.line_spacing_list.setText("1.5,2.0,2.5")
        vtp_layout.addRow("Line Spacing List:", self.line_spacing_list)

        self.layer_height = QDoubleSpinBox()
        self.layer_height.setRange(0.1, 10.0)
        self.layer_height.setSingleStep(0.1)
        self.layer_height.setValue(1.27)
        self.layer_height.setSuffix(" mm")
        vtp_layout.addRow("Layer Height (dZ):", self.layer_height)

        self.alpha = QDoubleSpinBox()
        self.alpha.setRange(0.1, 10.0)
        self.alpha.setSingleStep(0.01)
        self.alpha.setValue(1.0)
        vtp_layout.addRow("Die Swell (Alpha):", self.alpha)

        self.e_dot = QDoubleSpinBox()
        self.e_dot.setRange(1.0, 500.0)
        self.e_dot.setValue(50.0)
        self.e_dot.setSuffix(" mm/min")
        vtp_layout.addRow("Material Flow Rate (Ė):", self.e_dot)

        # Printer Parameters Tab
        printer_tab = QWidget()
        printer_layout = QFormLayout(printer_tab)
        tab_widget.addTab(printer_tab, "Printer Parameters")

        self.travel_speed = QDoubleSpinBox()
        self.travel_speed.setRange(100.0, 10000.0)
        self.travel_speed.setValue(3000.0)
        self.travel_speed.setSuffix(" mm/min")
        printer_layout.addRow("Travel Speed:", self.travel_speed)

        self.nozzle_diameter = QDoubleSpinBox()
        self.nozzle_diameter.setRange(0.1, 2.0)
        self.nozzle_diameter.setSingleStep(0.1)
        self.nozzle_diameter.setValue(0.4)
        self.nozzle_diameter.setSuffix(" mm")
        printer_layout.addRow("Nozzle Diameter:", self.nozzle_diameter)

        self.filament_diameter = QDoubleSpinBox()
        self.filament_diameter.setRange(1.0, 3.0)
        self.filament_diameter.setSingleStep(0.05)
        self.filament_diameter.setValue(1.75)
        self.filament_diameter.setSuffix(" mm")
        printer_layout.addRow("Filament Diameter:", self.filament_diameter)

        # New Nozzle Temp, Bed Temp, and Extrusion Multiplier fields
        self.nozzle_temp = QDoubleSpinBox()
        self.nozzle_temp.setRange(0, 500)
        self.nozzle_temp.setValue(270)
        self.nozzle_temp.setSuffix(" °C")
        printer_layout.addRow("Nozzle Temp:", self.nozzle_temp)

        self.bed_temp = QDoubleSpinBox()
        self.bed_temp.setRange(0, 150)
        self.bed_temp.setValue(50)
        self.bed_temp.setSuffix(" °C")
        printer_layout.addRow("Bed Temp:", self.bed_temp)

        # Retraction settings
        self.retract_length = QDoubleSpinBox()
        self.retract_length.setRange(0, 10)
        self.retract_length.setValue(5.0)
        self.retract_length.setSingleStep(0.5)
        self.retract_length.setSuffix(" mm")
        printer_layout.addRow("Retraction Length:", self.retract_length)

        self.retract_speed = QDoubleSpinBox()
        self.retract_speed.setRange(100, 5000)
        self.retract_speed.setValue(2000.0)
        self.retract_speed.setSingleStep(100)
        self.retract_speed.setSuffix(" mm/min")
        printer_layout.addRow("Retraction Speed:", self.retract_speed)

        self.extrusion_multiplier = QDoubleSpinBox()
        self.extrusion_multiplier.setRange(0.01, 10.0)
        self.extrusion_multiplier.setValue(1.2)
        self.extrusion_multiplier.setSingleStep(0.1)
        printer_layout.addRow("Extrusion Multiplier:",
                              self.extrusion_multiplier)

        # Bed size (width × height)
        bed_size_layout = QHBoxLayout()
        self.bed_width = QDoubleSpinBox()
        self.bed_width.setRange(50, 1000)
        self.bed_width.setValue(255)
        self.bed_width.setSuffix(" mm")
        self.bed_height = QDoubleSpinBox()
        self.bed_height.setRange(50, 1000)
        self.bed_height.setValue(210)
        self.bed_height.setSuffix(" mm")
        bed_size_layout.addWidget(self.bed_width)
        bed_size_layout.addWidget(QLabel("×"))
        bed_size_layout.addWidget(self.bed_height)
        printer_layout.addRow("Bed Size:", bed_size_layout)

        # G-code Files Tab
        gcode_tab = QWidget()
        gcode_layout = QFormLayout(gcode_tab)
        tab_widget.addTab(gcode_tab, "G-code Files")

        # Start G-code section
        self.start_gcode = QLineEdit()
        browse_start_btn = QPushButton("Browse...")
        browse_start_btn.clicked.connect(lambda: self.browse_file(
            self.start_gcode, "Select Start G-code"))

        # Add a "View Variables" button for start G-code
        view_start_vars_btn = QPushButton("View Variables")
        view_start_vars_btn.clicked.connect(
            lambda: self.show_template_variables("start"))

        start_layout = QHBoxLayout()
        start_layout.addWidget(self.start_gcode)
        start_layout.addWidget(browse_start_btn)
        start_layout.addWidget(view_start_vars_btn)
        gcode_layout.addRow("Start G-code File:", start_layout)

        # End G-code section
        self.end_gcode = QLineEdit()
        browse_end_btn = QPushButton("Browse...")
        browse_end_btn.clicked.connect(
            lambda: self.browse_file(self.end_gcode, "Select End G-code"))

        # Add a "View Variables" button for end G-code
        view_end_vars_btn = QPushButton("View Variables")
        view_end_vars_btn.clicked.connect(
            lambda: self.show_template_variables("end"))

        end_layout = QHBoxLayout()
        end_layout.addWidget(self.end_gcode)
        end_layout.addWidget(browse_end_btn)
        end_layout.addWidget(view_end_vars_btn)
        gcode_layout.addRow("End G-code File:", end_layout)

        # Information label about templates
        template_info = QLabel(
            "Note: G-code templates can contain variables like {bed_temp} that will be replaced with actual values.")
        template_info.setWordWrap(True)
        gcode_layout.addRow(template_info)

        # Button Box
        self.button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        main_layout.addWidget(self.button_box)

    def browse_image(self):
        """Open file dialog to select an image file."""
        # Get last directory from QSettings
        last_dir = str(self.settings.value(
            "last_image_directory", QDir.homePath()))

        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Image File", last_dir,
            "Images (*.png *.jpg *.jpeg *.bmp *.tif *.tiff)"
        )
        if file_path:
            # Save directory for next time
            self.settings.setValue(
                "last_image_directory", os.path.dirname(file_path))
            self.image_path.setText(file_path)
            # Emit signal to notify parent about the selected image
            self.image_selected.emit(file_path)

    def browse_file(self, line_edit, title):
        """Open file dialog to select any file."""
        # Get last directory, defaulting to home if not set
        last_dir = str(self.settings.value(
            "last_generic_file_directory", QDir.homePath()))

        file_path, _ = QFileDialog.getOpenFileName(
            self, title, last_dir, "All Files (*.*)"
        )
        if file_path:
            # Save directory for next time
            self.settings.setValue(
                "last_generic_file_directory", os.path.dirname(file_path))
            line_edit.setText(file_path)

    def show_template_variables(self, template_type):
        """Show a dialog with the variables available in the template."""
        from gcode.template_handler import GcodeTemplateHandler

        try:
            handler = GcodeTemplateHandler()

            # Get the template path based on type
            if template_type.lower() == "start":
                template_path = self.start_gcode.text()
            else:
                template_path = self.end_gcode.text()

            # If the path is empty, use default template
            if not template_path:
                template_path = handler.get_default_template_path(
                    template_type)

            # Get variables from the template
            variables = handler.get_template_variables(template_path)

            if variables:
                # Create message with variables
                var_list = "\n".join([f"  - {{{var}}}" for var in variables])
                message = f"The following variables can be used in the {template_type} G-code template:\n\n{var_list}"
            else:
                message = f"No variables found in the {template_type} G-code template."

            # Show in a message box
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.information(self, "Template Variables", message)

        except Exception as e:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(
                self, "Error", f"Could not read template variables: {str(e)}")

    def save_settings(self):
        """Save settings to QSettings."""
        self.settings.setValue("image_path", self.image_path.text())
        self.settings.setValue("physical_width", self.physical_width.value())
        self.settings.setValue("layers", self.layers.value())
        self.settings.setValue("v_star_hd", self.v_star_hd.value())
        self.settings.setValue("v_star_ld", self.v_star_ld.value())
        self.settings.setValue("h_star_hd", self.h_star_hd.value())
        self.settings.setValue("h_star_ld", self.h_star_ld.value())
        self.settings.setValue("alpha", self.alpha.value())
        self.settings.setValue("e_dot", self.e_dot.value())
        self.settings.setValue("line_spacing", self.line_spacing.value())
        self.settings.setValue("sampling_resolution",
                               self.sampling_resolution.value())
        self.settings.setValue("layer_height", self.layer_height.value())
        self.settings.setValue("travel_speed", self.travel_speed.value())
        self.settings.setValue("nozzle_diameter", self.nozzle_diameter.value())
        self.settings.setValue("filament_diameter",
                               self.filament_diameter.value())
        self.settings.setValue("nozzle_temp", self.nozzle_temp.value())
        self.settings.setValue("bed_temp", self.bed_temp.value())
        self.settings.setValue("retract_length", self.retract_length.value())
        self.settings.setValue("retract_speed", self.retract_speed.value())
        self.settings.setValue("extrusion_multiplier",
                               self.extrusion_multiplier.value())
        self.settings.setValue("bed_width", self.bed_width.value())
        self.settings.setValue("bed_height", self.bed_height.value())
        self.settings.setValue("start_gcode", self.start_gcode.text())
        self.settings.setValue("end_gcode", self.end_gcode.text())

    def load_settings(self):
        """Load settings from QSettings."""
        if self.settings.contains("image_path"):
            self.image_path.setText(self.settings.value("image_path"))
        if self.settings.contains("physical_width"):
            self.physical_width.setValue(
                float(self.settings.value("physical_width")))
        if self.settings.contains("layers"):
            self.layers.setValue(int(self.settings.value("layers")))
        if self.settings.contains("v_star_hd"):
            self.v_star_hd.setValue(float(self.settings.value("v_star_hd")))
        if self.settings.contains("v_star_ld"):
            self.v_star_ld.setValue(float(self.settings.value("v_star_ld")))
        if self.settings.contains("h_star_hd"):
            self.h_star_hd.setValue(float(self.settings.value("h_star_hd")))
        if self.settings.contains("h_star_ld"):
            self.h_star_ld.setValue(float(self.settings.value("h_star_ld")))
        if self.settings.contains("alpha"):
            self.alpha.setValue(float(self.settings.value("alpha")))
        if self.settings.contains("e_dot"):
            self.e_dot.setValue(float(self.settings.value("e_dot")))
        if self.settings.contains("line_spacing"):
            self.line_spacing.setValue(
                float(self.settings.value("line_spacing")))
        if self.settings.contains("sampling_resolution"):
            self.sampling_resolution.setValue(
                float(self.settings.value("sampling_resolution")))
        if self.settings.contains("layer_height"):
            self.layer_height.setValue(
                float(self.settings.value("layer_height")))
        if self.settings.contains("travel_speed"):
            self.travel_speed.setValue(
                float(self.settings.value("travel_speed")))
        if self.settings.contains("nozzle_diameter"):
            self.nozzle_diameter.setValue(
                float(self.settings.value("nozzle_diameter")))
        if self.settings.contains("filament_diameter"):
            self.filament_diameter.setValue(
                float(self.settings.value("filament_diameter")))
        if self.settings.contains("nozzle_temp"):
            self.nozzle_temp.setValue(
                float(self.settings.value("nozzle_temp")))
        if self.settings.contains("bed_temp"):
            self.bed_temp.setValue(float(self.settings.value("bed_temp")))
        if self.settings.contains("retract_length"):
            self.retract_length.setValue(
                float(self.settings.value("retract_length")))
        if self.settings.contains("retract_speed"):
            self.retract_speed.setValue(
                float(self.settings.value("retract_speed")))
        if self.settings.contains("extrusion_multiplier"):
            self.extrusion_multiplier.setValue(
                float(self.settings.value("extrusion_multiplier")))
        if self.settings.contains("bed_width"):
            self.bed_width.setValue(float(self.settings.value("bed_width")))
        if self.settings.contains("bed_height"):
            self.bed_height.setValue(float(self.settings.value("bed_height")))

        start_gcode_value = str(self.settings.value("start_gcode", ""))
        if start_gcode_value:
            self.start_gcode.setText(start_gcode_value)
        else:
            self.start_gcode.setText("gcode/templates/default_start.gcode")

        end_gcode_value = str(self.settings.value("end_gcode", ""))
        if end_gcode_value:
            self.end_gcode.setText(end_gcode_value)
        else:
            self.end_gcode.setText("gcode/templates/default_end.gcode")

    def accept(self):
        """Override of accept to save settings."""
        self.save_settings()
        super().accept()

    def get_print_parameters(self):
        """
        Creates and returns a PrintParameters object with the current settings.

        Args:
            None
        Returns:
            A PrintParameters object
        """
        # # Validate file paths
        # if not os.path.exists(self.image_path.text()):
        #     raise FileNotFoundError(
        #         f"Image file not found: {self.image_path.text()}")
        # if not os.path.exists(self.start_gcode.text()):
        #     raise FileNotFoundError(
        #         f"Start G-code file not found: {self.start_gcode.text()}")
        # if not os.path.exists(self.end_gcode.text()):
        #     raise FileNotFoundError(
        #         f"End G-code file not found: {self.end_gcode.text()}")

        return PrintParameters(
            image_filepath=self.image_path.text(),
            physical_print_width_mm=self.physical_width.value(),
            num_layers=self.layers.value(),
            v_star_hd=self.v_star_hd.value(),
            v_star_ld=self.v_star_ld.value(),
            h_star_hd=self.h_star_hd.value(),
            h_star_ld=self.h_star_ld.value(),
            alpha=self.alpha.value(),
            e_dot=self.e_dot.value(),
            line_spacing_mm=self.line_spacing.value(),
            line_spacing_list=parse_line_spacing_list(
                self.line_spacing_list.text()),
            sampling_resolution_mm=self.sampling_resolution.value(),
            dz_mm=self.layer_height.value(),
            start_gcode_filepath=self.start_gcode.text(),
            end_gcode_filepath=self.end_gcode.text(),
            f_travel=self.travel_speed.value(),
            D_N=self.nozzle_diameter.value(),
            D_F=self.filament_diameter.value(),
            bed_temp=self.bed_temp.value(),
            nozzle_temp=self.nozzle_temp.value(),
            retract_length=self.retract_length.value(),
            retract_speed=self.retract_speed.value(),
            printer_bed_size_mm=(self.bed_width.value(),
                                 self.bed_height.value()),
            extrusion_multiplier=self.extrusion_multiplier.value()*100,
            dL_hd=parse_line_spacing_list(self.line_spacing_list.text())[0],
            dL_ld=parse_line_spacing_list(self.line_spacing_list.text())[-1],
        )
