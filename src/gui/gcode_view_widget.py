# src/gui/pyvista_widget.py

import numpy as np
import pyvista as pv
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QSizePolicy, QVBoxLayout, QWidget
from pyvistaqt import QtInteractor  # PyVista's Qt interactor


class GCodeViewWidget(QWidget):
    """
    A QWidget that embeds a PyVista 3D scene, displaying a representation of a print bed.
    """

    def __init__(self, bed_size_mm=(100, 100), parent=None):  # Added bed dimensions
        super().__init__(parent)

        self.bed_x_mm = bed_size_mm[0]
        self.bed_y_mm = bed_size_mm[1]

        self.setSizePolicy(QSizePolicy.Policy.Expanding,
                           QSizePolicy.Policy.Expanding)
        self.setMinimumSize(300, 300)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.plotter = QtInteractor(self)
        layout.addWidget(self.plotter.interactor)

        self.plotter.set_background("white")  # White color
        self.create_bed_mesh()  # Renamed method

    def create_bed_mesh(self):  # Renamed from create_square_mesh
        """Creates a mesh representing the print bed and adds it to the plotter."""
        width = self.bed_x_mm
        height = self.bed_y_mm

        # Vertices of the bed rectangle, centered at origin on Z=0 plane
        # X corresponds to width, Y corresponds to depth
        points = np.array([
            [0, 0, 0.],  # Bottom-left
            [width, 0, 0.],  # Bottom-right
            [width,  height, 0.],  # Top-right
            [0,  height, 0.]  # Top-left
        ])

        # Faces (two triangles to form the rectangle)
        faces = np.hstack([
            # First triangle (bottom-left, bottom-right, top-right)
            [3, 0, 1, 2],
            [3, 0, 2, 3]   # Second triangle (bottom-left, top-right, top-left)
        ])

        bed_mesh = pv.PolyData(points, faces=faces)

        self.plotter.add_mesh(bed_mesh, color='lightblue',
                              show_edges=True, edge_color='black')

        # Adjust camera to view the bed appropriately
        self.plotter.camera_position = 'xy'  # View from +Z axis looking down
        self.plotter.camera.azimuth = 0
        self.plotter.camera.elevation = 0
        self.plotter.camera.roll = 0

        # Calculate a reasonable zoom factor based on bed size
        # This is a heuristic; might need adjustment
        # Larger of width/depth will determine initial view distance
        max_dim = max(self.bed_x_mm, self.bed_y_mm)
        # Base zoom on a reference size, e.g., if 200mm bed uses zoom 1.5
        # A larger bed needs to be "zoomed out" more (smaller zoom value for plotter.camera.zoom)
        # This logic might need refinement. PyVista's reset_camera often does a good job.
        # For now, let reset_camera handle the initial view based on the new mesh.

        self.plotter.remove_bounds_axes()
        self.plotter.reset_camera()  # Fit the new bed mesh into view

    def update_bed_mesh(self, new_width, new_depth):
        """Clears existing bed and creates a new one with specified dimensions."""
        self.bed_x_mm = new_width
        self.bed_y_mm = new_depth
        self.plotter.clear_actors()  # Clear previous bed mesh
        self.create_bed_mesh()  # Create and add the new one
        # self.plotter.reset_camera() # Already called in create_bed_mesh

    def clear_scene(self):
        """Removes all actors (meshes) from the PyVista plotter."""
        self.plotter.clear_actors()
        self.plotter.reset_camera()
