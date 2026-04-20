from typing import Dict, Tuple, Optional
import matplotlib.pyplot as plt
from .model import GeometryModel

class GeometryVisualizer:
    """Renders points (x,y from 3D) and edges from a GeometryModel."""
    
    def __init__(self, figsize: tuple = (8, 6)):
        self.figsize = figsize
        self.fig = None
        self.ax = None
    
    def create_figure(self):
        self.fig, self.ax = plt.subplots(figsize=self.figsize)
        self.ax.set_aspect('equal')
        self.ax.grid(True)
    
    def render_model(self, model: GeometryModel,
                     point_color='blue', point_marker='o', point_size=50,
                     edge_color='black', edge_linewidth=1):
        """Render all points and edges from a GeometryModel.
        Points are stored as (x, y, z); uses x, y only."""
        if not model.points:
            return
        # Points: dict id -> (x, y, z)
        xs = [p[0] for p in model.points.values()]
        ys = [p[1] for p in model.points.values()]
        self.ax.scatter(xs, ys, color=point_color, marker=point_marker, s=point_size)
        
        # Edges: dict id -> (start_id, end_id)
        for start_id, end_id in model.edges.values():
            if start_id in model.points and end_id in model.points:
                start = model.points[start_id]
                end = model.points[end_id]
                self.ax.plot([start[0], end[0]], [start[1], end[1]],
                             color=edge_color, linewidth=edge_linewidth)
    
    def save_png(self, filepath: str, dpi=150):
        if self.fig is None:
            raise RuntimeError("No figure created. Call create_figure() first.")
        self.fig.savefig(filepath, dpi=dpi, bbox_inches='tight')
        plt.close(self.fig)
    
    def show(self):
        if self.fig:
            plt.show()
