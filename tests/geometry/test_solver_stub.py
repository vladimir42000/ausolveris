import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

import yaml
import pytest

from src.ausolveris.geometry.model import GeometryModel, Part, Frame, Anchor, Boundary
from src.ausolveris.geometry.solver import run_geometry_solver_stub
from src.ausolveris.geometry.benchmark import (
    solver_observables_to_yaml_string,
    solver_observables_to_yaml_file,
)


def test_empty_model_observables():
    model = GeometryModel(name="", parts={}, frames={})
    obs = run_geometry_solver_stub(model)
    assert obs["root_part_count"] == 0
    assert obs["total_part_count"] == 0
    assert obs["frame_count"] == 0
    assert obs["anchor_count"] == 0
    assert obs["boundary_count"] == 0
    assert obs["max_hierarchy_depth"] == 0


def test_single_part_counts_and_depth():
    part = Part(id="p1", name="Part 1")
    model = GeometryModel(name="single", parts={"p1": part}, frames={})
    obs = run_geometry_solver_stub(model)
    assert obs["root_part_count"] == 1
    assert obs["total_part_count"] == 1
    assert obs["max_hierarchy_depth"] == 1


def test_nested_hierarchy_counts_and_depth():
    grandchild = Part(id="p3", name="Part 3")
    child = Part(id="p2", name="Part 2", children=[grandchild])
    root = Part(id="p1", name="Part 1", children=[child])
    model = GeometryModel(name="nested", parts={"p1": root}, frames={})
    obs = run_geometry_solver_stub(model)
    assert obs["total_part_count"] == 3
    assert obs["max_hierarchy_depth"] == 3


def test_anchor_and_boundary_counts():
    frame = Frame(id="f1")
    anchor = Anchor(id="a1", frame_id="f1")
    boundary = Boundary(id="b1")
    child = Part(id="c1", name="Child", anchors={"a1": anchor}, boundaries={"b1": boundary})
    root = Part(id="r1", name="Root", children=[child])
    model = GeometryModel(name="counts", parts={"r1": root}, frames={"f1": frame})
    obs = run_geometry_solver_stub(model)
    assert obs["frame_count"] == 1
    assert obs["anchor_count"] == 1
    assert obs["boundary_count"] == 1


def test_solver_output_yaml_safe_and_serializable():
    part = Part(id="p1", name="Part 1")
    model = GeometryModel(name="yaml", parts={"p1": part}, frames={})
    obs = run_geometry_solver_stub(model)
    yaml_text = solver_observables_to_yaml_string(obs)
    loaded = yaml.safe_load(yaml_text)
    assert loaded == obs


def test_benchmark_yaml_file_export(tmp_path):
    part = Part(id="p1", name="Part 1")
    model = GeometryModel(name="file", parts={"p1": part}, frames={})
    obs = run_geometry_solver_stub(model)
    out = tmp_path / "observables.yaml"
    solver_observables_to_yaml_file(obs, out)
    loaded = yaml.safe_load(out.read_text(encoding="utf-8"))
    assert loaded == obs


def test_non_geometry_model_rejected():
    with pytest.raises(TypeError, match="GeometryModel"):
        run_geometry_solver_stub({"not": "a model"})
