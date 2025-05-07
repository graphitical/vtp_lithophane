# src/gui/image_view_widget.py

import os

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPalette, QPixmap
from PySide6.QtWidgets import QApplication, QLabel, QMessageBox, QSizePolicy


class ImageViewWidget(QLabel):
    """
    A widget dedicated to displaying an image, handling loading,
    error states, and resizing.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_image_path = None
        self.original_pixmap = None  # Store the unscaled pixmap for quality resizing

        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setMinimumSize(300, 300)
        self.setSizePolicy(QSizePolicy.Policy.Expanding,
                           QSizePolicy.Policy.Expanding)
        self.setText(
            "Please load an image using File > Import Image (Ctrl+I).")
        self._set_prompt_appearance()

    def _set_prompt_appearance(self):
        """Sets the visual style for when no image is loaded or an error occurs."""
        palette = self.palette()
        palette.setColor(QPalette.ColorRole.Window, QColor("white"))
        self.setAutoFillBackground(True)
        self.setPalette(palette)

    def _set_error_appearance(self):
        """Sets the visual style for when an image loading error occurs."""
        palette = self.palette()
        palette.setColor(QPalette.ColorRole.Window, QColor("lightcoral"))
        self.setAutoFillBackground(True)
        self.setPalette(palette)

    def _set_success_appearance(self):
        """Resets appearance after successful image load."""
        self.setAutoFillBackground(False)
        self.setPalette(QApplication.style().standardPalette())

    def set_image_path(self, image_path):
        """
        Sets the image path and attempts to load and display the image.
        """
        self.current_image_path = image_path
        self.original_pixmap = None  # Clear previous pixmap
        self.setPixmap(QPixmap())   # Clear display immediately

        if not self.current_image_path or not os.path.exists(self.current_image_path):
            error_message = "Please load an image using File > Import Image (Ctrl+I)."
            if self.current_image_path:  # Only show detailed error if a path was attempted
                error_message = f"Error: Image not found or path is invalid.\nPath: '{self.current_image_path}'"
            print(error_message)
            self.setText(error_message)
            self._set_prompt_appearance()  # Or _set_error_appearance if path was given
            return

        loaded_pixmap = QPixmap(self.current_image_path)
        if loaded_pixmap.isNull():
            error_message = f"Error: Could not load image at {self.current_image_path}"
            print(error_message)
            self.setText(error_message)
            self._set_error_appearance()
        else:
            self.original_pixmap = loaded_pixmap
            self._set_success_appearance()
            self.setText("")  # Clear any previous text
            self._scale_and_display_pixmap()

    def clear_image(self):
        """Clears the displayed image and resets to the prompt state."""
        self.current_image_path = None
        self.original_pixmap = None
        self.setPixmap(QPixmap())
        self.setText(
            "Please load an image using File > Import Image (Ctrl+I).")
        self._set_prompt_appearance()

    def _scale_and_display_pixmap(self):
        """Scales the stored original_pixmap to fit the widget and displays it."""
        if self.original_pixmap and not self.original_pixmap.isNull():
            self.setPixmap(self.original_pixmap.scaled(
                self.size(),  # Scale to the current size of the QLabel
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            ))
        elif not self.current_image_path:  # If no image is supposed to be loaded
            self.setText(
                "Please load an image using File > Import Image (Ctrl+I).")
            self._set_prompt_appearance()

    def resizeEvent(self, event):
        """Handles widget resize events to rescale the displayed image."""
        super().resizeEvent(event)  # Call QLabel's resizeEvent
        # If an image is loaded, rescale it.
        # The check for self.original_pixmap handles cases where no image is set.
        if self.original_pixmap and not self.original_pixmap.isNull():
            self._scale_and_display_pixmap()
        # If no image, the text will reflow or be centered by QLabel's default behavior.
