import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

import pytest
from ausolveris.geometry.model import GeometryModel
from ausolveris.geometry.physics import flare_law_acoustic_objective

def test_empty_geometry_zero_score():
    model = GeometryModel()
    model.points = {}
    model.edges = {}
    assert flare_law_acoustic_objective(model) == 0.0

def test_simple_flare_positive_score():
    model = GeometryModel()
    model.points = {
        "A": (0.0, 0.0, 0.0),
        "B": (1.0, 0.5, 0.0),
        "C": (2.0, 1.0, 0.0),
        "D": (3.0, 0.5, 0.0),
        "E": (4.0, 0.0, 0.0)
    }
    model.edges = {
        "AB": ("A", "B"),
        "BC": ("B", "C"),
        "CD": ("C", "D"),
        "DE": ("D", "E")
    }
    score = flare_law_acoustic_objective(model)
    assert 0.0 < score <= 1.0

def test_invalid_geometry_missing_edges_returns_one():
    model = GeometryModel()
    model.points = {"A": (0,0,0), "B": (1,0,0)}
    model.edges = {}
    assert flare_law_acoustic_objective(model) == 1.0

def test_single_point_returns_one():
    model = GeometryModel()
    model.points = {"A": (0,0,0)}
    model.edges = {}
    assert flare_law_acoustic_objective(model) == 1.0

def test_deterministic():
    model = GeometryModel()
    model.points = {"A": (0,0,0), "B": (1,1,0)}
    model.edges = {"AB": ("A", "B")}
    assert flare_law_acoustic_objective(model) == flare_law_acoustic_objective(model)

def test_uniform_cylinder_zero_variance():
    model = GeometryModel()
    model.points = {
        "A": (0.0, 1.0, 0.0),
        "B": (1.0, 1.0, 0.0),
        "C": (2.0, 1.0, 0.0)
    }
    model.edges = {"AB": ("A", "B"), "BC": ("B", "C")}
    assert flare_law_acoustic_objective(model) == 0.0

def test_disconnected_components_returns_one():
    model = GeometryModel()
    model.points = {"A": (0,0,0), "B": (1,0,0), "C": (2,0,0)}
    model.edges = {"AB": ("A", "B")}  # C isolated
    assert flare_law_acoustic_objective(model) == 1.0

def test_negative_coordinates_handled():
    model = GeometryModel()
    model.points = {"A": (0.0, -1.0, 0.0), "B": (1.0, -2.0, 0.0)}
    model.edges = {"AB": ("A", "B")}
    assert 0.0 <= flare_law_acoustic_objective(model) <= 1.0

def test_edges_not_covering_all_points_returns_one():
    model = GeometryModel()
    model.points = {"A": (0,0,0), "B": (1,0,0), "C": (2,0,0)}
    model.edges = {"AB": ("A", "B")}
    assert flare_law_acoustic_objective(model) == 1.0

def test_large_flare_scales_correctly():
    model = GeometryModel()
    points = {}
    edges = {}
    for i in range(10):
        points[f"p{i}"] = (float(i), float(i), 0.0)
        if i > 0:
            edges[f"e{i}"] = (f"p{i-1}", f"p{i}")
    model.points = points
    model.edges = edges
    assert 0.0 < flare_law_acoustic_objective(model) <= 1.0
