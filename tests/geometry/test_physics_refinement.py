import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

import pytest
from ausolveris.geometry.model import GeometryModel
from ausolveris.geometry.physics import flare_law_acoustic_objective

def test_empty_model_returns_neutral():
    model = GeometryModel()
    model.points = {}
    model.edges = {}
    score = flare_law_acoustic_objective(model)
    assert score == 0.0

def test_valid_geometry_deterministic():
    model = GeometryModel()
    model.points = {"A": (0,0,0), "B": (1,1,0)}
    model.edges = {"AB": ("A","B")}
    score1 = flare_law_acoustic_objective(model)
    score2 = flare_law_acoustic_objective(model)
    assert score1 == score2

def test_normalization_bounds():
    # Create a deliberately bad flare (large area variation)
    model = GeometryModel()
    model.points = {
        "A": (0, 0, 0),
        "B": (1, 10, 0),   # large radius
        "C": (2, 0, 0)
    }
    model.edges = {"AB": ("A","B"), "BC": ("B","C")}
    score = flare_law_acoustic_objective(model)
    assert 0.0 <= score <= 1.0

def test_invalid_input_handled_consistently():
    model = GeometryModel()
    model.points = {"A": (0,0,0), "B": (1,1,0)}
    model.edges = {}  # missing edges
    score = flare_law_acoustic_objective(model)
    assert score == 1.0

def test_single_point_returns_worst():
    model = GeometryModel()
    model.points = {"A": (0,0,0)}
    model.edges = {}
    score = flare_law_acoustic_objective(model)
    assert score == 1.0

def test_perfect_uniformity_returns_zero():
    # All points same radius
    model = GeometryModel()
    model.points = {
        "A": (0, 1, 0),
        "B": (1, 1, 0),
        "C": (2, 1, 0)
    }
    model.edges = {"AB": ("A","B"), "BC": ("B","C")}
    score = flare_law_acoustic_objective(model)
    assert score == 0.0

def test_missing_point_in_edge_returns_one():
    model = GeometryModel()
    model.points = {"A": (0,0,0)}
    model.edges = {"AB": ("A","B")}  # B missing
    score = flare_law_acoustic_objective(model)
    assert score == 1.0

def test_repeated_calls_stable():
    model = GeometryModel()
    model.points = {"A": (0,0,0), "B": (1,2,0)}
    model.edges = {"AB": ("A","B")}
    scores = [flare_law_acoustic_objective(model) for _ in range(5)]
    assert all(s == scores[0] for s in scores)

def test_normalization_caps_at_one():
    # Extreme variance should saturate at 1.0
    model = GeometryModel()
    model.points = {
        "A": (0, 0, 0),
        "B": (1, 100, 0),   # huge radius
        "C": (2, 0, 0)
    }
    model.edges = {"AB": ("A","B"), "BC": ("B","C")}
    score = flare_law_acoustic_objective(model)
    assert score == 1.0  # capped

def test_negative_coordinates_handled_gracefully():
    model = GeometryModel()
    model.points = {"A": (0, -1, 0), "B": (1, 0, 0)}  # r = 1.0 for A
    model.edges = {"AB": ("A","B")}
    score = flare_law_acoustic_objective(model)
    assert 0.0 <= score <= 1.0
