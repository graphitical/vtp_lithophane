# VTP Lithophane G-code Generator

A "Viscous Thread Printing" (VTP) Lithophane G-code Generator with a GUI. This tool allows users to import an image and will (eventually) generate G-code suitable for VTP-style 3D printing of lithophanes.

## Features (Current & Planned)

* Image import and display
* G-code generation for VTP lithophanes
* 3D preview of the toolpath using PyVista
* UI configurable processing settings
* Color-coded toolpath by Z-height (a proxy for H*)
* (Planned) Color-coded toolpath for V*
* (Planned) Better image processing controls

## Requirements

This project was developed and tested using Python 3.13.3 in Ubuntu 22.04 via WSLg. 
While it may work with with other versions and systems, compatibility is not guaranteed.
All other dependencies are captured in the `environment.yml` file.

## Installation

Make sure you have Conda (Miniconda or Anaconda) installed. 
Alternatively you could use Mamba.

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/graphitical/vtp_lithophane.git
    cd vtp_lithophane
    ```

2. **Create and activate the Conda environment from the YAML file**

    ```bash
    conda env create -f environment.yml -n vtp_litho
    conda activate vtp_litho
    ```
    > Note: This may take a minute.

3.  **Install the project and its dependencies:**
    From the project root directory (where `setup.py` is located):
    ```bash
    pip install .
    ```
    This command installs the package and its dependencies into the current Python environment. 
    It also makes the `vtp-lithophane-gui` command-line entry point available for running the GUI.

    If you want to make edits to the code and have those changes immediately reflected in the application, you can install the package in "editable mode" by running:
    ```bash
    pip install -e .
    ```
    In editable mode, the installed package is linked to the source code directory, so any changes you make to the code will take effect without needing to reinstall the package.

## Running the Application

After successful installation, you can run the GUI from your terminal (ensure your conda environment is activated):

```bash
vtp-lithophane-gui
```

This command is made available via the `setup.py` entry points.

## Development

* **Code Structure:**
    * `gcode/`: The directory to store output G-code files as well as printer specific headers and footers. This directory structure is just a suggestion and you can store G-code files wherever you like.
        * `outputs/`: The designated directory for writing G-code files.
        * `templates/`: The designated directory for specific header and footer files.
    * `src/gcode/`: Core G-code generation logic.
        * `gcode_generator.py`: Handles the generation of G-code for VTP lithophanes.
        * `image_utils.py`: Provides utilities for loading and processing images.
        * `parameters.py`: Defines the `PrintParamters` dataclass, which encapsulates _most_ user-configurable settings for lithophane generation. (Note: there isn't parity between the Qt settings dialog and `PrintParameters`.)
        * `template_handler.py`: Manages G-code templates for start and end sequences by injecting print parameters into the specific G-code template files.
    * `src/gui/`: PySide6 GUI application code.
        * `app.py`: Main application entry point.
        * `main_window.py`: Defines the main application window.
        * `menu_bar.py`: Logic for creating the application's menu bar.
        * `image_view_widget.py`: Widget for displaying the imported image.
        * `gcode_view_widget.py`: Widget for embedding the PyVista 3D view.
        * `settings_dialog.py`: Dialog interface for configuring and saving G-code generation and printer settings using Qt's settings system for persistent storage.
    * `tests/`: Keeps all the tests sectioned off.
    * `analyze_gcode.py`: A script that will parse a G-code file and estimate metrics like amount of material fed in and time to complete the print. Useful for debugging difficult G-code files.
    * `lithophize.py`: A CLI interface to process an image and generate VTP lithophane G-code. Not necessarily maintained at parity with the GUI.
    * `run_tests.py`: Self-explanatory
    * `setup.py`: The setup file to install all the relevant packages and setup the `vtp-lithophane-gui` entry point.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
