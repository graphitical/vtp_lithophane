# src/gui/menu_bar.py

from PySide6.QtGui import QAction, QKeySequence
# QMenuBar is typically part of QMainWindow
from PySide6.QtWidgets import QMenuBar


def create_main_menu(main_window):
    """
    Creates and returns the main QMenuBar for the application.

    Args:
        main_window: The QMainWindow instance to which actions will be connected
                     and parented.
    """
    # Get the menuBar from the main_window instance itself, or create a new one if needed.
    # QMainWindow already has a menuBar() method to get its menu bar.
    menu_bar = main_window.menuBar()  # Use the existing menu bar from the QMainWindow

    # --- File Menu ---
    file_menu = menu_bar.addMenu("&File")

    open_action = QAction("&Open", main_window)
    open_action.setShortcut(QKeySequence.StandardKey.Open)
    # Connect to main_window's method
    open_action.triggered.connect(main_window.open_file)
    file_menu.addAction(open_action)

    save_action = QAction("&Save", main_window)
    save_action.setShortcut(QKeySequence.StandardKey.Save)
    save_action.triggered.connect(main_window.save_file)
    file_menu.addAction(save_action)

    file_menu.addSeparator()

    import_action = QAction("&Import Image", main_window)
    import_action.setShortcut(QKeySequence("Ctrl+I"))
    import_action.triggered.connect(main_window.import_image)
    file_menu.addAction(import_action)

    file_menu.addSeparator()

    exit_action = QAction("E&xit", main_window)
    exit_action.setShortcut(QKeySequence.StandardKey.Quit)
    # Connect to QMainWindow's close slot
    exit_action.triggered.connect(main_window.close)
    file_menu.addAction(exit_action)

    # --- Process Menu ---
    process_menu = menu_bar.addMenu("&Process")

    settings_action = QAction("&Settings...", main_window)
    settings_action.setShortcut(QKeySequence("Ctrl+Shift+S"))
    settings_action.triggered.connect(main_window.open_process_settings)
    process_menu.addAction(settings_action)

    generate_action = QAction("&Generate G-code", main_window)
    generate_action.setShortcut(QKeySequence("Ctrl+G"))
    generate_action.triggered.connect(main_window.generate_gcode)
    process_menu.addAction(generate_action)

    return menu_bar  # Return the populated menuBar
