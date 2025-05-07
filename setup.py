# vtp_lithophane_project/setup.py

from setuptools import find_packages, setup

setup(
    name="vtp_lithophane",  # The name of your package on PyPI (if you publish)
    version="0.1.0",       # Your package's current version
    description="A VTP Lithophane G-code Generator",
    author="Daniel Revier",
    author_email="revier.daniel@gmail.com",
    license="MIT",
    url="https://github.com/graphitical/vtp_lithophane",

    package_dir={'': 'src'},
    # Automatically find packages in 'src'
    packages=find_packages(where='src'),

    # --- Dependencies ---
    install_requires=[
        "numpy",         # For numerical operations
        "Pillow",        # For image manipulation (PIL fork)
        "matplotlib",    # For plotting (if needed)
        # Add any other direct dependencies your project has
    ],

    # --- Python version requirement ---
    python_requires=">=3.9",  # Specify the minimum Python version
)
