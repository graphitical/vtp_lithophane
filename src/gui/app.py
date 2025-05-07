# src/gui/app.py
import sys

from PySide6.QtWidgets import QApplication

# Assuming main_window.py is in the same gui directory
from .main_window import DualViewWindow


def run():
    app = QApplication(sys.argv)
    window = DualViewWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    run()  # Allows running python src/gui/app.py directly too
