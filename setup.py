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

    # --- Package Discovery ---
    package_dir={'': 'src'},
    packages=find_packages(where='src'),

    # --- Dependencies ---
    install_requires=[
        "numpy",
        "Pillow",
        "matplotlib",
        "PySide6",
    ],

    # --- Python version requirement ---
    python_requires=">=3.9",

    # --- Entry Points ---
    # Add ability to run 'vtp-lithophane-gui' from the command line.
    entry_points={
        'console_scripts': [
            'vtp-lithophane-gui=gui.app:run',
        ],
    },
    # --- Additional Metadata ---
    # classifiers?
)
