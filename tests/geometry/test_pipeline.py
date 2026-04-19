import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

import yaml
import pytest

from src.ausolveris.geometry.model import GeometryModel, Part, Frame, Anchor, Boundary
from src.ausolveris.geometry.pipeline import (
    run_solver_pipeline_from_yaml_string,
    run_solver_pipeline_from_yaml_file,
    solver_pipeline_observables_to_yaml_string,
    solver_pipeline_observables_to_yaml_file,
)
from src.ausolveris.geometry.serializer import (
    geometry_model_to_yaml_string,
    geometry_model_to_yaml_file,
    yaml_string_to_geometry_model,
)
from src.ausolveris.geometry.solver import run_geometry_solver_stub


def make_minimal_model() -> GeometryModel:
    return GeometryModel(name="", parts={}, frames={})


def make_nested_model() -> GeometryModel:
    frame = Frame(id="f1")
    anchor = Anchor(id="a1", frame_id="f1")
    boundary = Boundary(id="b1")

    grandchild = Part(id="p3", name="Grandchild")
    child = Part(
        id="p2",
        name="Child",
        children=[grandchild],
        anchors={"a1": anchor},
        boundaries={"b1": boundary},
        metadata={"kind": "child"},
    )
    root = Part(
        id="p1",
        name="Root",
        children=[child],
        anchors={},
        boundaries={},
        metadata={"kind": "root"},
    )
    return GeometryModel(
        id="model_nested",
        name="Nested Model",
        parts={"p1": root},
        frames={"f1": frame},
    )


def test_valid_minimal_yaml_string_to_observables():
    yaml_text = geometry_model_to_yaml_string(make_minimal_model())
    observables = run_solver_pipeline_from_yaml_string(yaml_text)
    assert observables["root_part_count"] == 0
    assert observables["total_part_count"] == 0
    assert observables["frame_count"] == 0
    assert observables["anchor_count"] == 0
    assert observables["boundary_count"] == 0
    assert observables["max_hierarchy_depth"] == 0


def test_valid_nested_hierarchy_yaml_string_counts():
    yaml_text = geometry_model_to_yaml_string(make_nested_model())
    observables = run_solver_pipeline_from_yaml_string(yaml_text)
    assert observables["model_id"] == "model_nested"
    assert observables["model_name"] == "Nested Model"
    assert observables["root_part_count"] == 1
    assert observables["total_part_count"] == 3
    assert observables["frame_count"] == 1
    assert observables["anchor_count"] == 1
    assert observables["boundary_count"] == 1
    assert observables["max_hierarchy_depth"] == 3


def test_yaml_file_to_observables(tmp_path):
    model = make_nested_model()
    src = tmp_path / "model.yaml"
    geometry_model_to_yaml_file(model, src)
    observables = run_solver_pipeline_from_yaml_file(src)
    assert observables["model_id"] == "model_nested"
    assert observables["total_part_count"] == 3


def test_pipeline_yaml_string_export_produces_valid_yaml():
    yaml_text = geometry_model_to_yaml_string(make_nested_model())
    out_yaml = solver_pipeline_observables_to_yaml_string(yaml_text)
    loaded = yaml.safe_load(out_yaml)
    assert loaded["model_id"] == "model_nested"
    assert set(loaded.keys()) == {
        "model_id",
        "model_name",
        "root_part_count",
        "total_part_count",
        "frame_count",
        "anchor_count",
        "boundary_count",
        "max_hierarchy_depth",
    }


def test_pipeline_yaml_file_export_writes_valid_yaml(tmp_path):
    yaml_text = geometry_model_to_yaml_string(make_nested_model())
    out = tmp_path / "observables.yaml"
    solver_pipeline_observables_to_yaml_file(yaml_text, out)
    loaded = yaml.safe_load(out.read_text(encoding="utf-8"))
    assert loaded["model_name"] == "Nested Model"
    assert loaded["max_hierarchy_depth"] == 3


def test_malformed_yaml_string_is_rejected():
    bad_yaml = "name: [broken"
    with pytest.raises(yaml.YAMLError):
        run_solver_pipeline_from_yaml_string(bad_yaml)


def test_invalid_root_shape_is_rejected():
    yaml_text = yaml.safe_dump(["not", "a", "mapping"])
    with pytest.raises(ValueError, match="YAML root must be a mapping"):
        run_solver_pipeline_from_yaml_string(yaml_text)


def test_schema_invalid_yaml_is_rejected():
    yaml_text = yaml.safe_dump({
        "name": "bad",
        "parts": [],
        "frames": {},
    })
    with pytest.raises(ValueError, match="'parts' must be a dictionary"):
        run_solver_pipeline_from_yaml_string(yaml_text)


def test_pipeline_matches_direct_serializer_plus_solver():
    yaml_text = geometry_model_to_yaml_string(make_nested_model())
    pipeline_result = run_solver_pipeline_from_yaml_string(yaml_text)

    model = yaml_string_to_geometry_model(yaml_text)
    direct_result = run_geometry_solver_stub(model)

    assert pipeline_result == direct_result
