import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

import pytest
from ausolveris.geometry.model import GeometryModel
from ausolveris.geometry.solver import optimize
from ausolveris.geometry.physics import flare_law_acoustic_objective

def test_loop_runs_without_error():
    model = GeometryModel()
    model.points = {"A": (0,0,0), "B": (1,0,0)}
    model.edges = {"AB": ("A", "B")}
    result, _ = optimize(model, max_steps=3) # Updated for tuple
    assert isinstance(result, GeometryModel)

def test_score_improves_or_stays_stable():
    model = GeometryModel()
    model.points = {
        "A": (0.0, 0.0, 0.0),
        "B": (1.0, 1.0, 0.0),
        "C": (2.0, 2.0, 0.0)
    }
    model.edges = {"AB": ("A", "B"), "BC": ("B", "C")}
    original_score = flare_law_acoustic_objective(model)
    optimized, _ = optimize(model, max_steps=5) # Updated for tuple
    new_score = flare_law_acoustic_objective(optimized)
    assert new_score <= original_score + 1e-9

def test_max_steps_respected():
    model = GeometryModel()
    model.points = {"A": (0,0,0), "B": (1,0,0)}
    model.edges = {"AB": ("A", "B")}
    result0, info = optimize(model, max_steps=0)
    assert result0.points == model.points
    assert info['steps'] == 0
    result5, info5 = optimize(model, max_steps=5)
    assert info5['steps'] <= 5

def test_zero_steps_returns_copy():
    model = GeometryModel()
    model.points = {"P": (1,2,3)}
    model.edges = {}
    result, info = optimize(model, max_steps=0)
    assert result is not model
    assert result.points == model.points
    assert info['steps'] == 0

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
    result, info = optimize(model, max_steps=5)
    assert result.points == {}
    assert info['history'] == [0.0]

def test_single_point_model_stays_single_point():
    model = GeometryModel()
    model.points = {"A": (1,2,3)}
    model.edges = {}
    result, info = optimize(model, max_steps=5)
    assert len(result.points) == 1
    assert info['converged'] is True # Immediate convergence on invalid

def test_optimize_with_disconnected_model_returns_inf_but_no_crash():
    model = GeometryModel()
    model.points = {"A": (0,0,0), "B": (1,0,0), "C": (2,0,0)}
    model.edges = {"AB": ("A", "B")}
    result, info = optimize(model, max_steps=2)
    assert isinstance(result, GeometryModel)
    assert info['history'][0] == 1.0

def test_pipeline_roundtrip_with_export():
    model = GeometryModel()
    model.points = {"A": (0,0,0), "B": (1,1,0)}
    model.edges = {"AB": ("A", "B")}
    optimized, _ = optimize(model, max_steps=3)
    from ausolveris.geometry.serialization import export_geometry_summary
    summary = export_geometry_summary(optimized)
    assert "primitives" in summary
