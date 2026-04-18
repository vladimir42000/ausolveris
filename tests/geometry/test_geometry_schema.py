"""Unit tests for geometry YAML schema validation and serialization (10 tests)."""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

import pytest
import yaml

from src.ausolveris.geometry.model import GeometryModel, Part, Frame, Anchor, Boundary
from src.ausolveris.geometry.schema import validate_geometry_dict
from src.ausolveris.geometry.serializer import (
    geometry_model_to_yaml_string,
    yaml_string_to_geometry_model,
    geometry_model_to_yaml_file,
    yaml_file_to_geometry_model,
)


def create_valid_model() -> GeometryModel:
    frame1 = Frame(id="frame_1", origin=(0, 0, 0), orientation=((1, 0, 0), (0, 1, 0), (0, 0, 1)), units="mm")
    frame2 = Frame(id="frame_2", origin=(10, 0, 0), orientation=((1, 0, 0), (0, 1, 0), (0, 0, 1)), units="mm")
    frames = {"frame_1": frame1, "frame_2": frame2}

    anchor1 = Anchor(id="anchor_1", frame_id="frame_1")
    anchor2 = Anchor(id="anchor_2", frame_id=None)
    anchors = {"anchor_1": anchor1, "anchor_2": anchor2}

    boundary1 = Boundary(id="boundary_1")
    boundaries = {"boundary_1": boundary1}

    child_part = Part(
        id="part_child",
        name="Child Part",
        children=[],
        anchors={},
        boundaries={},
        metadata={"type": "child"},
    )

    root_part = Part(
        id="part_root",
        name="Root Part",
        children=[child_part],
        anchors=anchors,
        boundaries=boundaries,
        metadata={"version": 1},
    )

    parts = {"part_root": root_part}
    return GeometryModel(id="model_1", name="Test Model", parts=parts, frames=frames)


class TestSchemaValidation:
    def test_valid_model_dict(self):
        model = create_valid_model()
        data = model.to_dict()
        validate_geometry_dict(data)

    def test_missing_top_level_key(self):
        data = {"name": "test", "parts": {}}
        with pytest.raises(ValueError, match="Missing required top-level keys"):
            validate_geometry_dict(data)

    def test_unknown_top_level_key(self):
        data = {"name": "test", "parts": {}, "frames": {}, "extra": "bad"}
        with pytest.raises(ValueError, match="Unknown top-level keys"):
            validate_geometry_dict(data)

    def test_frame_id_mismatch(self):
        model = create_valid_model()
        data = model.to_dict()
        data["frames"]["frame_1"]["id"] = "wrong"
        with pytest.raises(ValueError, match="Frame dict key 'frame_1' does not match 'id' field 'wrong'"):
            validate_geometry_dict(data)

    def test_anchor_frame_id_nonexistent(self):
        model = create_valid_model()
        data = model.to_dict()
        data["parts"]["part_root"]["anchors"]["anchor_1"]["frame_id"] = "nonexistent"
        with pytest.raises(ValueError, match="references unknown frame 'nonexistent'"):
            validate_geometry_dict(data)


class TestSerializationRoundTrip:
    def test_yaml_string_round_trip(self):
        original = create_valid_model()
        yaml_str = geometry_model_to_yaml_string(original)
        reconstructed = yaml_string_to_geometry_model(yaml_str)
        assert original.to_dict() == reconstructed.to_dict()

    def test_yaml_file_round_trip(self, tmp_path):
        original = create_valid_model()
        file_path = tmp_path / "test_model.yaml"
        geometry_model_to_yaml_file(original, file_path)
        loaded = yaml_file_to_geometry_model(file_path)
        assert original.to_dict() == loaded.to_dict()

    def test_invalid_yaml_string_raises(self):
        invalid_yaml = "name: test\nparts: {invalid"
        with pytest.raises(yaml.YAMLError):
            yaml_string_to_geometry_model(invalid_yaml)


class TestValidationErrorsOnDeserialization:
    def test_deserialize_invalid_schema_unknown_key(self):
        invalid_data = {
            "name": "bad",
            "parts": {},
            "frames": {},
            "extra_key": "not allowed",
        }
        yaml_str = yaml.safe_dump(invalid_data)
        with pytest.raises(ValueError, match="Unknown top-level keys"):
            yaml_string_to_geometry_model(yaml_str)

    def test_deserialize_duplicate_part_id(self):
        model = create_valid_model()
        data = model.to_dict()
        duplicate_child = data["parts"]["part_root"]["children"][0].copy()
        duplicate_child["id"] = "part_root"
        duplicate_child["name"] = "Duplicate Child"
        data["parts"]["part_root"]["children"].append(duplicate_child)
        yaml_str = yaml.safe_dump(data)
        with pytest.raises(ValueError, match="Duplicate part id 'part_root'"):
            yaml_string_to_geometry_model(yaml_str)

def test_valid_minimal_yaml_to_model():
    yaml_str = yaml.safe_dump({
        "name": "",
        "parts": {},
        "frames": {},
    })
    model = yaml_string_to_geometry_model(yaml_str)
    assert isinstance(model, GeometryModel)
    assert model.name == ""
    assert model.parts == {}
    assert model.frames == {}


def test_non_mapping_yaml_root_rejected():
    yaml_str = yaml.safe_dump(["not", "a", "mapping"])
    with pytest.raises(ValueError, match="YAML root must be a mapping"):
        yaml_string_to_geometry_model(yaml_str)
