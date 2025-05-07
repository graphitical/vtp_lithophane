# vtp_lithophane_project/setup.py

from setuptools import find_packages, setup

setup(
    name="vtp_lithophane",
    version="0.1.0",
    description="A VTP Lithophane G-code Generator with a GUI",
    author="Daniel Revier",
    author_email="revier.daniel@gmail.com",
    license="MIT",
    url="https://github.com/graphitical/vtp_lithophane",

    package_dir={'': 'src'},
    packages=find_packages(where='src'),

    install_requires=[
        "numpy",
        "Pillow",
        "matplotlib",  # For plotting (if needed)
        "PySide6",    # For the GUI
        "pyvista",    # For 3D visualization
        # For PyVista's Qt integration (specifically QtInteractor)
        "pyvistaqt",
    ],

    python_requires=">=3.9",

    entry_points={
        'console_scripts': [
            'vtp-lithophane-gui=gui.app:run',
        ],
    },

    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
        "Topic :: Multimedia :: Graphics :: 3D Modeling",
        "Environment :: X11 Applications :: Qt",  # For PySide6/Qt
    ],
)
