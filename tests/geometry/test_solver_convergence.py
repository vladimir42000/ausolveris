import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

import pytest
from ausolveris.geometry.model import GeometryModel
from ausolveris.geometry.solver import optimize

def test_converges_on_simple_case():
    model = GeometryModel()
    model.points = {"A": (0.0, 0.1, 0.0), "B": (1.0, 0.2, 0.0)}
    model.edges = {"AB": ("A", "B")}
    # Should move toward A=(0,0,0), B=(1,0,0) to minimize variance
    optimized, info = optimize(model, tolerance=1e-5, max_steps=100)
    assert info['converged'] is True
    assert info['history'][-1] < info['history'][0]

def test_respects_max_steps():
    model = GeometryModel()
    model.points = {"A": (0, 0.5, 0), "B": (1, 1.0, 0)}
    model.edges = {"AB": ("A", "B")}
    # Set max_steps very low
    _, info = optimize(model, max_steps=2, tolerance=1e-10)
    assert info['steps'] == 2
    assert info['converged'] is False

def test_tolerance_respected():
    model = GeometryModel()
    model.points = {"A": (0, 0.1, 0), "B": (1, 0.2, 0)}
    model.edges = {"AB": ("A", "B")}
    _, info = optimize(model, tolerance=1e-2)
    # Should stop early
    assert info['converged'] is True
    if info['steps'] > 1:
        change = abs(info['history'][-2] - info['history'][-1])
        assert change < 1e-2

def test_history_length():
    _, info = optimize(GeometryModel(), max_steps=5)
    assert len(info['history']) == info['steps'] + 1

def test_return_type():
    model = GeometryModel()
    res = optimize(model)
    assert isinstance(res, tuple)
    assert len(res) == 2
    assert isinstance(res[0], GeometryModel)
    assert isinstance(res[1], dict)
    for key in ['converged', 'steps', 'history']:
        assert key in res[1]


def test_verbose_no_crash(capsys):
    model = GeometryModel()
    # Use different radii (0.1 and 0.5) so the objective is > 0
    model.points = {"A": (0, 0.1, 0), "B": (1, 0.5, 0)} 
    model.edges = {"AB": ("A", "B")}
    optimize(model, max_steps=2, verbose=True)
    captured = capsys.readouterr()
    assert "Step" in captured.out
    
def test_empty_model():
    model = GeometryModel()
    res, info = optimize(model)
    assert res.points == {}
    assert info['history'] == [0.0]
    assert info['converged'] is True

def test_single_point():
    model = GeometryModel()
    model.points = {"A": (0,0,0)}
    res, info = optimize(model)
    assert info['history'] == [1.0]
    assert info['converged'] is True

def test_objective_monotonic_decrease():
    model = GeometryModel()
    model.points = {"A": (0, 0.1, 0), "B": (1, 0.5, 0)}
    model.edges = {"AB": ("A", "B")}
    _, info = optimize(model, step_size=0.01, max_steps=10)
    # Check that each step is non-increasing
    for i in range(len(info['history']) - 1):
        assert info['history'][i+1] <= info['history'][i] + 1e-12

def test_multiple_points_independent():
    model = GeometryModel()
    model.points = {"A": (0, 1, 0), "B": (1, 2, 0), "C": (2, 3, 0)}
    model.edges = {"AB": ("A", "B"), "BC": ("B", "C")}
    optimized, info = optimize(model, max_steps=5)
    assert info['history'][-1] <= info['history'][0]
