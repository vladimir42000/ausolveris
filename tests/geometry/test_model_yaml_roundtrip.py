"""Tests for YAML serialization and deserialization of geometry models."""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

import yaml
import tempfile
import pytest
from src.ausolveris.geometry.model import GeometryModel, Part, Frame, Anchor, Boundary


def test_yaml_roundtrip_basic():
    """Test basic YAML serialization and deserialization."""
    # Create a simple model
    model = GeometryModel(
        name="Simple Model",
        parts={
            "root": Part(id="root", name="Root Part")
        },
        frames={
            "global": Frame(id="global", origin=(0, 0, 0))
        }
    )
    
    # Convert to dict
    data = model.to_dict()
    
    # Write to YAML string
    yaml_str = yaml.dump(data, default_flow_style=False)
    
    # Parse back
    loaded_data = yaml.safe_load(yaml_str)
    loaded_model = GeometryModel.from_dict(loaded_data)
    
    # Verify
    assert loaded_model.name == model.name
    assert loaded_model.parts["root"].id == "root"
    assert loaded_model.frames["global"].origin == (0, 0, 0)


def test_yaml_roundtrip_complex():
    """Test YAML roundtrip with complex hierarchy."""
    # Build nested parts
    inner = Part(id="inner", name="Inner Part")
    middle = Part(id="middle", name="Middle Part", children=[inner])
    outer = Part(id="outer", name="Outer Part", children=[middle])
    
    # Add anchors and boundaries with matching keys
    anchor = Anchor(id="top_anchor", frame_id="main_frame")
    boundary = Boundary(id="outer_boundary")
        
    outer.anchors = {"top_anchor": anchor}  # Key must match anchor.id
    outer.boundaries = {"outer_boundary": boundary}  # Key must match boundary.id
    
    # Add frame
    frame = Frame(
        id="main_frame",
        origin=(1.5, 2.5, 3.5),
        orientation=((0, 1, 0), (-1, 0, 0), (0, 0, 1)),
        units="millimeter"
    )
    
    model = GeometryModel(
        name="Complex Model",
        parts={"outer": outer},
        frames={"main_frame": frame}
    )
    
    # Roundtrip through YAML
    data = model.to_dict()
    yaml_str = yaml.dump(data, default_flow_style=False)
    loaded_data = yaml.safe_load(yaml_str)
    loaded_model = GeometryModel.from_dict(loaded_data)
    
    # Verify structure
    assert loaded_model.name == "Complex Model"
    assert loaded_model.parts["outer"].id == "outer"
    assert loaded_model.parts["outer"].children[0].id == "middle"
    assert loaded_model.parts["outer"].children[0].children[0].id == "inner"
    
    # Verify anchors and boundaries
    assert "top_anchor" in loaded_model.parts["outer"].anchors
    assert loaded_model.parts["outer"].anchors["top_anchor"].frame_id == "main_frame"
    assert "outer_boundary" in loaded_model.parts["outer"].boundaries
    
    # Verify frame
    assert loaded_model.frames["main_frame"].origin == (1.5, 2.5, 3.5)
    assert loaded_model.frames["main_frame"].units == "millimeter"


def test_yaml_file_roundtrip():
    """Test writing to and reading from a YAML file."""
    # Create a model
    part = Part(
        id="test_part",
        name="Test Part",
        metadata={"version": 1, "description": "A test part"}
    )
    frame = Frame(id="test_frame", origin=(10, 20, 30))
    
    model = GeometryModel(
        name="File Test Model",
        parts={"test_part": part},
        frames={"test_frame": frame}
    )
    
    # Write to temporary file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        data = model.to_dict()
        yaml.dump(data, f, default_flow_style=False)
        temp_path = f.name
    
    try:
        # Read back
        with open(temp_path, 'r') as f:
            loaded_data = yaml.safe_load(f)
        
        loaded_model = GeometryModel.from_dict(loaded_data)
        
        # Verify
        assert loaded_model.name == "File Test Model"
        assert loaded_model.parts["test_part"].metadata["version"] == 1
        assert loaded_model.frames["test_frame"].origin == (10, 20, 30)
    finally:
        os.unlink(temp_path)


def test_yaml_with_empty_model():
    """Test YAML serialization with empty model."""
    model = GeometryModel()
    data = model.to_dict()
    
    # Should have id, name, parts, frames
    assert 'id' in data
    assert 'name' in data
    assert 'parts' in data
    assert 'frames' in data
    
    # Serialize and deserialize
    yaml_str = yaml.dump(data, default_flow_style=False)
    loaded_data = yaml.safe_load(yaml_str)
    loaded_model = GeometryModel.from_dict(loaded_data)
    
    assert loaded_model.id == model.id
    assert loaded_model.name == model.name
    assert loaded_model.parts == {}
    assert loaded_model.frames == {}


def test_yaml_validation_on_load():
    """Test that validation occurs during from_dict."""
    # Invalid data: empty part id
    invalid_data = {
        "name": "Invalid Model",
        "parts": {
            "": {
                "id": "",
                "name": "Invalid Part",
                "children": [],
                "anchors": {},
                "boundaries": {},
                "metadata": {}
            }
        },
        "frames": {}
    }
    
    with pytest.raises(ValueError, match="Part id must be non-empty"):
        GeometryModel.from_dict(invalid_data)
    
    # Valid data should work
    valid_data = {
        "name": "Valid Model",
        "parts": {
            "part1": {
                "id": "part1",
                "name": "Valid Part",
                "children": [],
                "anchors": {},
                "boundaries": {},
                "metadata": {}
            }
        },
        "frames": {}
    }
    
    model = GeometryModel.from_dict(valid_data)
    assert model.parts["part1"].name == "Valid Part"
