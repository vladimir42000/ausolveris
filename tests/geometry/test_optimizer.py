"""Tests for OPT-001 structural observable scoring stub (6 tests)."""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

import pytest
from pathlib import Path
from src.ausolveris.geometry.model import GeometryModel, Part, Frame, Anchor, Boundary
from src.ausolveris.geometry.serializer import geometry_model_to_yaml_string, geometry_model_to_yaml_file
from src.ausolveris.geometry.optimizer import (
    score_solver_observables,
    score_geometry_yaml_string,
    score_geometry_yaml_file,
)


def make_test_model() -> GeometryModel:
    """Create a model with known counts: root_part_count=1, total_part_count=2,
    frame_count=1, anchor_count=1, boundary_count=1, max_hierarchy_depth=2."""
    frame = Frame(id="f1")
    anchor = Anchor(id="a1", frame_id="f1")
    boundary = Boundary(id="b1")
    child = Part(id="p2", name="Child", anchors={"a1": anchor}, boundaries={"b1": boundary})
    root = Part(id="p1", name="Root", children=[child])
    return GeometryModel(
        id="test_model",
        name="TestModel",
        parts={"p1": root},
        frames={"f1": frame},
    )


def test_score_solver_observables_empty_model():
    """Empty model: all counts zero -> score 0."""
    from src.ausolveris.geometry.solver import run_geometry_solver_stub
    empty = GeometryModel(name="Empty", parts={}, frames={})
    obs = run_geometry_solver_stub(empty)
    result = score_solver_observables(obs)
    assert result["model_name"] == "Empty"
    assert result["score_name"] == "structure_complexity_v1"
    assert result["score_value"] == 0
    assert result["components"]["root_part_count"] == 0
    assert result["components"]["total_part_count"] == 0
    assert result["components"]["frame_count"] == 0
    assert result["components"]["anchor_count"] == 0
    assert result["components"]["boundary_count"] == 0
    assert result["components"]["max_hierarchy_depth"] == 0


def test_score_solver_observables_non_empty():
    """Non-empty model: score equals negative sum of counts."""
    model = make_test_model()
    from src.ausolveris.geometry.solver import run_geometry_solver_stub
    obs = run_geometry_solver_stub(model)
    result = score_solver_observables(obs)
    # Expected: root=1, total=2, frames=1, anchors=1, boundaries=1, depth=2 => penalty=8, score=-8
    assert result["score_value"] == -8
    assert result["components"]["root_part_count"] == 1
    assert result["components"]["total_part_count"] == 2
    assert result["components"]["frame_count"] == 1
    assert result["components"]["anchor_count"] == 1
    assert result["components"]["boundary_count"] == 1
    assert result["components"]["max_hierarchy_depth"] == 2


def test_score_solver_observables_missing_key():
    """Missing required observable key raises ValueError."""
    incomplete = {"model_id": "x", "model_name": "x", "root_part_count": 1}
    with pytest.raises(ValueError, match="Missing required observable keys"):
        score_solver_observables(incomplete)


def test_score_solver_observables_non_numeric_value():
    """Non-numeric count value raises TypeError."""
    bad = {
        "model_id": "x", "model_name": "x",
        "root_part_count": "one",  # string not allowed
        "total_part_count": 0,
        "frame_count": 0,
        "anchor_count": 0,
        "boundary_count": 0,
        "max_hierarchy_depth": 0,
    }
    with pytest.raises(TypeError, match="must be numeric"):
        score_solver_observables(bad)


def test_score_geometry_yaml_string_end_to_end(tmp_path):
    """YAML string -> pipeline -> score works."""
    model = make_test_model()
    yaml_text = geometry_model_to_yaml_string(model)
    result = score_geometry_yaml_string(yaml_text)
    assert result["score_name"] == "structure_complexity_v1"
    assert result["score_value"] == -8


def test_score_geometry_yaml_file_end_to_end(tmp_path):
    """YAML file -> pipeline -> score works."""
    model = make_test_model()
    yaml_path = tmp_path / "model.yaml"
    geometry_model_to_yaml_file(model, yaml_path)
    result = score_geometry_yaml_file(yaml_path)
    assert result["score_name"] == "structure_complexity_v1"
    assert result["score_value"] == -8
