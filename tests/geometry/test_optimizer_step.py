import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

import pytest
import copy
from ausolveris.geometry.model import GeometryModel
from ausolveris.geometry.optimizer import (
    structure_complexity_v1, 
    compute_gradient, 
    newton_step, 
    apply_step
)

def test_zero_step_on_minimum():
    model = GeometryModel()
    model.points = {"O": (0.0, 0.0, 0.0)}
    step = newton_step(model)
    dx, dy, dz = step["O"]
    assert abs(dx) < 1e-5
    assert abs(dy) < 1e-5
    assert abs(dz) < 1e-5

def test_gradient_direction_correct():
    model = GeometryModel()
    model.points = {"P": (1.0, 0.0, 0.0)}
    grad = compute_gradient(model, structure_complexity_v1)
    # For x^2, grad at x=1 is 2. 
    assert grad["P"][0] > 0
    step = newton_step(model)
    # Step should be negative (towards origin)
    assert step["P"][0] < 0

def test_step_size_bounded():
    model = GeometryModel()
    model.points = {"P": (100.0, 0.0, 0.0)}
    # Gradient will be ~200, step_size 0.1 -> raw step ~20.
    step = newton_step(model, step_size=0.1, max_step_norm=1.0)
    dx, dy, dz = step["P"]
    norm = (dx**2 + dy**2 + dz**2)**0.5
    assert norm <= 1.000001

def test_pipeline_roundtrip():
    model = GeometryModel()
    model.points = {"A": (1.0, 1.0, 1.0)}
    step = newton_step(model, step_size=0.5)
    new_model = apply_step(model, step)
    assert new_model.points["A"][0] < 1.0
    assert len(new_model.points) == 1

def test_objective_decreases():
    model = GeometryModel()
    model.points = {"A": (2.0, 2.0, 2.0)}
    obj_before = structure_complexity_v1(model)
    step = newton_step(model, step_size=0.1)
    new_model = apply_step(model, step)
    obj_after = structure_complexity_v1(new_model)
    assert obj_after < obj_before

def test_empty_model():
    model = GeometryModel()
    grad = compute_gradient(model, structure_complexity_v1)
    step = newton_step(model)
    assert grad == {}
    assert step == {}

def test_step_does_not_mutate_original():
    model = GeometryModel()
    model.points = {"A": (1.0, 1.0, 1.0)}
    original_coords = model.points["A"]
    step = newton_step(model)
    apply_step(model, step)
    assert model.points["A"] == original_coords

def test_multiple_points_independent():
    model = GeometryModel()
    model.points = {"A": (1.0, 0.0, 0.0), "B": (0.0, 1.0, 0.0)}
    step = newton_step(model, step_size=0.1)
    
    # Check A moves towards origin on X, stays put on Y/Z
    assert step["A"][0] < 0
    assert abs(step["A"][1]) < 2e-6  # Loosened for finite-difference noise
    assert abs(step["A"][2]) < 2e-6
    
    # Check B moves towards origin on Y, stays put on X/Z
    assert step["B"][1] < 0
    assert abs(step["B"][0]) < 2e-6
    assert abs(step["B"][2]) < 2e-6
