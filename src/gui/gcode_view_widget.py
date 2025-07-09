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

        self.line_actor_name = 'gcode_lines'

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

    def add_line(self, start_pt, end_pt, color='black', width=1.0):
        """
        Adds a line to the plotter.

        :param start_pt: Starting point of the line (x, y, z).
        :param end_pt: Ending point of the line (x, y, z).
        :param color: Color of the line.
        :param width: Width of the line.
        """
        line = pv.Line(start_pt, end_pt)
        self.plotter.add_mesh(line, color=color, line_width=width)

        return line

    def add_lines(self, points, **kwargs):
        """
        Updates the lines actor with new points.
        """

        if not isinstance(points, np.ndarray):
            raise ValueError("Points must be a numpy array.")

        if points.ndim != 2 or points.shape[1] != 3:
            raise ValueError("Points must be a 2D array with shape (N, 3).")

        # this does nothing if the actor does not exist
        self.plotter.remove_actor(self.line_actor_name)
        # self.plotter.add_lines(points,
        #                        name=self.line_actor_name,
        #                        connected=True,
        #                        **kwargs)

        lines = pv.lines_from_points(points, close=False)
        # Average Z between consecutive points
        z_avg = 0.5 * (points[:-1, 2] + points[1:, 2])
        lines.cell_data['z_height'] = z_avg

        self.plotter.add_mesh(
            lines,
            scalars='z_height',
            name=self.line_actor_name,
            cmap='viridis',
            line_width=kwargs.get('line_width', 1.0),
            show_scalar_bar=False,
            lighting=False,
        )
