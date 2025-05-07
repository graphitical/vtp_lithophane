# VTP Lithophane G-code Generator

A "Viscous Thread Printing" (VTP) Lithophane G-code Generator with a GUI. This tool allows users to import an image and will (eventually) generate G-code suitable for VTP-style 3D printing of lithophanes.

## Features (Current & Planned)

* Image import and display
* (Planned) G-code generation for VTP lithophanes
* (Planned) 3D preview of the toolpath using Polyscope
* (Planned) Configurable processing settings

## Installation

It is highly recommended to use a Python virtual environment.

1.  **Clone the repository (if you haven't already):**
    ```bash
    git clone [https://github.com/graphitical/vtp_lithophane.git](https://github.com/graphitical/vtp_lithophane.git)
    cd vtp_lithophane
    ```

2.  **Create and activate a virtual environment:**
    * On macOS and Linux:
        ```bash
        python3 -m venv venv
        source venv/bin/activate
        ```
    * On Windows:
        ```bash
        python -m venv venv
        .\venv\Scripts\activate
        ```

3.  **Install the project and its dependencies:**
    From the project root directory (where `setup.py` is located):
    ```bash
    pip install -e .
    ```
    This command installs the package in "editable" mode, meaning changes to the source code will be immediately effective without needing to reinstall.

    **Note on Polyscope Installation:**
    This project uses Polyscope for 3D visualization.
    * The `pip install -e .` command should handle installing Polyscope via pip, which generally works.
    * If you attempt to install Polyscope using Conda and encounter `LibMambaUnsatisfiableError` or similar Python version conflicts (e.g., if your Conda environment has a very new Python like 3.12+), it's because Conda's Polyscope packages might not yet support the latest Python versions. In such cases, relying on pip for Polyscope within a compatible Python environment (e.g., Python 3.9-3.11) is the recommended workaround. The `python_requires=">=3.9"` in `setup.py` reflects this.

## Running the Application

After successful installation, you can run the GUI from your terminal (ensure your virtual environment is activated):

```bash
vtp-lithophane-gui
```

## Development

(You can add more details here later, e.g., how to run tests, build documentation, etc.)

* **Code Structure:**
    * `src/gcode/`: Core G-code generation logic.
    * `src/gui/`: PySide6 GUI application code.
        * `app.py`: Main application entry point.
        * `main_window.py`: Defines the main application window.
        * `menu_bar.py`: Logic for creating the application's menu bar.
        * `image_view_widget.py`: Widget for displaying the imported image.
        * `polyscope_widget.py`: Widget for embedding the Polyscope 3D view.

## License

This project is licensed under the MIT License - see the LICENSE file for details (though you'll need to create a LICENSE file if you want one).
