# src/gui/placeholder_view_widget.py

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QLabel, QSizePolicy


class PlaceholderViewWidget(QLabel):
    """
    A simple placeholder widget, typically for a 3D view or other content.
    """

    def __init__(self, text="3D View (Not yet implemented)", parent=None):
        super().__init__(text, parent)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setMinimumSize(300, 300)
        self.setSizePolicy(QSizePolicy.Policy.Expanding,
                           QSizePolicy.Policy.Expanding)

        # Set a distinct background color
        palette = self.palette()
        palette.setColor(QPalette.ColorRole.Window, QColor("darkgray"))
        self.setAutoFillBackground(True)
        self.setPalette(palette)
