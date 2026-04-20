import matplotlib
matplotlib.use('Agg')

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import pytest
from ausolveris.geometry.model import GeometryModel
from ausolveris.geometry.visualizer import GeometryVisualizer

def test_render_triangle(tmp_path):
    model = GeometryModel()
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
    viz = GeometryVisualizer()
    viz.create_figure()
    viz.render_model(model)
    out = tmp_path / "triangle.png"
    viz.save_png(str(out))
    assert out.exists() and out.stat().st_size > 0

def test_render_square(tmp_path):
    model = GeometryModel()
    model.points = {
        "A": (0.0, 0.0, 0.0),
        "B": (1.0, 0.0, 0.0),
        "C": (1.0, 1.0, 0.0),
        "D": (0.0, 1.0, 0.0)
    }
    model.edges = {
        "AB": ("A", "B"),
        "BC": ("B", "C"),
        "CD": ("C", "D"),
        "DA": ("D", "A")
    }
    viz = GeometryVisualizer()
    viz.create_figure()
    viz.render_model(model)
    out = tmp_path / "square.png"
    viz.save_png(str(out))
    assert out.exists() and out.stat().st_size > 0

def test_render_hierarchy(tmp_path):
    # alias for render_model – just ensure it doesn't crash
    model = GeometryModel()
    model.points = {"P": (1.0, 2.0, 3.0)}
    model.edges = {}
    viz = GeometryVisualizer()
    viz.create_figure()
    viz.render_model(model)
    out = tmp_path / "hierarchy.png"
    viz.save_png(str(out))
    assert out.exists()

def test_png_save_succeeds(tmp_path):
    viz = GeometryVisualizer()
    viz.create_figure()
    out = tmp_path / "empty.png"
    viz.save_png(str(out))
    assert out.exists() and out.stat().st_size > 0

def test_pipeline_roundtrip(tmp_path):
    model = GeometryModel()
    model.points = {"A": (0,0,0), "B": (1,0,0)}
    model.edges = {"AB": ("A","B")}
    viz = GeometryVisualizer()
    viz.create_figure()
    viz.render_model(model)
    out = tmp_path / "line.png"
    viz.save_png(str(out))
    assert out.stat().st_size > 100  # rough check

def test_render_empty_model(tmp_path):
    model = GeometryModel()
    model.points = {}
    model.edges = {}
    viz = GeometryVisualizer()
    viz.create_figure()
    viz.render_model(model)  # should not crash
    out = tmp_path / "empty.png"
    viz.save_png(str(out))
    assert out.exists()

def test_render_missing_edge_points(tmp_path):
    model = GeometryModel()
    model.points = {"A": (0,0,0)}
    model.edges = {"AB": ("A", "B")}  # B missing
    viz = GeometryVisualizer()
    viz.create_figure()
    viz.render_model(model)  # should skip missing point
    out = tmp_path / "missing.png"
    viz.save_png(str(out))
    assert out.exists()
