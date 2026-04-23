import sys
from pathlib import Path
# Fix sys.path to include 'src' so 'ausolveris' package is found
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

import pytest
from ausolveris.geometry.model import GeometryModel
from ausolveris.geometry.solver import optimize
from ausolveris.geometry.physics import flare_law_acoustic_objective

def test_loop_runs_without_error():
    model = GeometryModel()
    model.points = {"A": (0,0,0), "B": (1,0,0)}
    model.edges = {"AB": ("A", "B")}
    result = optimize(model, max_steps=3)
    assert isinstance(result, GeometryModel)

def test_score_improves_or_stays_stable():
    model = GeometryModel()
    # Create a non-optimal flare (variance > 0)
    model.points = {
        "A": (0.0, 0.0, 0.0),
        "B": (1.0, 1.0, 0.0),
        "C": (2.0, 2.0, 0.0)
    }
    model.edges = {"AB": ("A", "B"), "BC": ("B", "C")}
    original_score = flare_law_acoustic_objective(model)
    optimized = optimize(model, max_steps=5)
    new_score = flare_law_acoustic_objective(optimized)
    # Score should not increase (should decrease or stay same)
    assert new_score <= original_score + 1e-9

def test_max_steps_respected():
    model = GeometryModel()
    model.points = {"A": (0,0,0), "B": (1,0,0)}
    model.edges = {"AB": ("A", "B")}
    result0 = optimize(model, max_steps=0)
    # Should be a deep copy, same points
    assert result0.points == model.points
    # Running more steps should not crash
    result5 = optimize(model, max_steps=5)
    assert isinstance(result5, GeometryModel)

def test_zero_steps_returns_copy():
    model = GeometryModel()
    model.points = {"P": (1,2,3)}
    model.edges = {}
    result = optimize(model, max_steps=0)
    assert result is not model  # different object
    assert result.points == model.points
    assert result.edges == model.edges

def test_original_model_not_mutated():
    model = GeometryModel()
    model.points = {"A": (0,0,0), "B": (1,0,0)}
    model.edges = {"AB": ("A", "B")}
    original_points = dict(model.points)
    optimize(model, max_steps=3)
    assert model.points == original_points

def test_negative_max_steps_raises():
    model = GeometryModel()
    with pytest.raises(ValueError, match="non-negative"):
        optimize(model, max_steps=-1)

def test_empty_model_optimize_returns_empty():
    model = GeometryModel()
    result = optimize(model, max_steps=5)
    assert result.points == {}
    assert result.edges == {}

def test_single_point_model_stays_single_point():
    model = GeometryModel()
    model.points = {"A": (1,2,3)}
    model.edges = {}
    result = optimize(model, max_steps=5)
    # Ensure it returns a model with the same point count
    assert len(result.points) == 1

def test_optimize_with_disconnected_model_returns_inf_but_no_crash():
    model = GeometryModel()
    model.points = {"A": (0,0,0), "B": (1,0,0), "C": (2,0,0)}
    model.edges = {"AB": ("A", "B")}  # C disconnected
    # This is invalid geometry -> objective returns inf. No crash expected.
    result = optimize(model, max_steps=2)
    assert isinstance(result, GeometryModel)

def test_pipeline_roundtrip_with_export():
    model = GeometryModel()
    model.points = {"A": (0,0,0), "B": (1,1,0)}
    model.edges = {"AB": ("A", "B")}
    optimized = optimize(model, max_steps=3)
    # Use export (from GEO-002) to verify structure
    from ausolveris.geometry.serialization import export_geometry_summary
    summary = export_geometry_summary(optimized)
    assert "primitives" in summary
    assert "points" in summary["primitives"]
