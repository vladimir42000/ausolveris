#!/usr/bin/env python3
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from ausolveris.geometry.model import GeometryModel
from ausolveris.geometry.visualizer import GeometryVisualizer

def main():
    model = GeometryModel()
    
    # Triangle (3D points, z=0)
    model.points = {
        "A": (0.0, 0.0, 0.0),
        "B": (1.0, 0.0, 0.0),
        "C": (0.5, 0.866, 0.0)
    }
    model.edges = {
        "AB": ("A", "B"),
        "BC": ("B", "C"),
        "CA": ("C", "A")
    }
    
    # Square
    model.points.update({
        "D": (2.0, 0.0, 0.0),
        "E": (3.0, 0.0, 0.0),
        "F": (3.0, 1.0, 0.0),
        "G": (2.0, 1.0, 0.0)
    })
    model.edges.update({
        "DE": ("D", "E"),
        "EF": ("E", "F"),
        "FG": ("F", "G"),
        "GD": ("G", "D")
    })
    
    viz = GeometryVisualizer()
    viz.create_figure()
    viz.render_model(model, point_color='red', edge_color='blue')
    viz.save_png("triangle_square.png")
    print("Demo completed: triangle_square.png saved")

if __name__ == "__main__":
    main()
