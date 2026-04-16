"""Tests for geometry model validation."""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

import pytest
from src.ausolveris.geometry.model import (
    Part, Anchor, Frame, Boundary, GeometryModel
)


def test_part_validation():
    """Test basic part validation."""
    # Valid part
    part = Part(id="part1", name="My Part")
    assert part.id == "part1"
    assert part.name == "My Part"
    
    # Invalid: empty id
    with pytest.raises(ValueError, match="Part id must be non-empty"):
        Part(id="", name="Test")
    
    # Invalid: empty name
    with pytest.raises(ValueError, match="Part name must be non-empty"):
        Part(id="test", name="")
    
    # Part with children
    child = Part(id="child1", name="Child")
    parent = Part(id="parent1", name="Parent", children=[child])
    assert len(parent.children) == 1
    assert parent.children[0].id == "child1"


def test_anchor_validation():
    """Test anchor validation."""
    anchor = Anchor(id="anchor1")
    assert anchor.id == "anchor1"
    assert anchor.frame_id is None
    
    anchor_with_frame = Anchor(id="anchor2", frame_id="frame1")
    assert anchor_with_frame.frame_id == "frame1"
    
    with pytest.raises(ValueError, match="Anchor id must be non-empty"):
        Anchor(id="")


def test_frame_validation():
    """Test frame validation."""
    # Valid frame
    frame = Frame(id="frame1")
    assert frame.id == "frame1"
    assert frame.origin == (0.0, 0.0, 0.0)
    assert frame.units == "meter"
    
    # Custom origin
    frame2 = Frame(id="frame2", origin=(1.0, 2.0, 3.0))
    assert frame2.origin == (1.0, 2.0, 3.0)
    
    # Invalid origin length
    with pytest.raises(ValueError, match="Origin must have exactly three elements"):
        Frame(id="frame3", origin=(1.0, 2.0))
    
    # Invalid orientation shape
    with pytest.raises(ValueError, match="Orientation must have three rows"):
        Frame(id="frame4", orientation=((1,0,0),(0,1,0)))
    
    with pytest.raises(ValueError, match="Each orientation row must have three elements"):
        Frame(id="frame5", orientation=((1,0),(0,1),(0,0)))


def test_boundary_validation():
    """Test boundary validation."""
    boundary = Boundary(id="boundary1")
    assert boundary.id == "boundary1"
    
    with pytest.raises(ValueError, match="Boundary id must be non-empty"):
        Boundary(id="")


def test_geometry_model_validation():
    """Test geometry model validation."""
    # Empty model is valid
    model = GeometryModel()
    assert model.id is not None
    assert model.name == ""
    
    # Model with parts and frames
    part1 = Part(id="part1", name="Part 1")
    frame1 = Frame(id="frame1")
    model = GeometryModel(parts={"part1": part1}, frames={"frame1": frame1})
    assert "part1" in model.parts
    assert "frame1" in model.frames
    
    # Duplicate ids across parts and frames
    with pytest.raises(ValueError, match="Duplicate id across parts/frames"):
        GeometryModel(
            parts={"id1": Part(id="id1", name="Part")},
            frames={"id1": Frame(id="id1")}
        )
    
    # Anchor references non-existent frame
    anchor = Anchor(id="anchor1", frame_id="missing_frame")
    part_with_anchor = Part(
        id="part2",
        name="Part with anchor",
        anchors={"anchor1": anchor}
    )
    with pytest.raises(ValueError, match="references non-existent frame"):
        GeometryModel(
            parts={"part2": part_with_anchor},
            frames={}
        )
    
    # Valid anchor reference
    frame2 = Frame(id="frame2")
    anchor2 = Anchor(id="anchor2", frame_id="frame2")
    part2 = Part(
        id="part3",
        name="Part 3",
        anchors={"anchor2": anchor2}
    )
    model = GeometryModel(
        parts={"part3": part2},
        frames={"frame2": frame2}
    )
    assert model.parts["part3"].anchors["anchor2"].frame_id == "frame2"


def test_nested_parts():
    """Test model with nested parts."""
    grandchild = Part(id="grandchild", name="Grandchild")
    child = Part(id="child", name="Child", children=[grandchild])
    parent = Part(id="parent", name="Parent", children=[child])
    
    model = GeometryModel(parts={"parent": parent})
    assert model.parts["parent"].children[0].id == "child"
    assert model.parts["parent"].children[0].children[0].id == "grandchild"

def test_duplicate_part_id_in_hierarchy():
    """Test rejection of duplicate part ids anywhere in hierarchy."""
    # Create parts with same id at different levels
    child1 = Part(id="duplicate_id", name="Child 1")
    child2 = Part(id="child2", name="Child 2")
    parent = Part(id="parent", name="Parent", children=[child1, child2])
    
    # This should be fine because parent.id != child1.id
    model = GeometryModel(parts={"parent": parent})
    
    # Now create a hierarchy where a nested part has same id as a top-level part
    nested = Part(id="top_level", name="Nested")
    middle = Part(id="middle", name="Middle", children=[nested])
    top = Part(id="top_level", name="Top Level", children=[middle])
    
    # This should fail because top and nested have same id
    with pytest.raises(ValueError, match='Duplicate part id "top_level" found in hierarchy'):
        GeometryModel(parts={"top_level": top})

def test_cycle_detection_in_hierarchy():
    """Test rejection of cycles in part hierarchy."""
    # Create a cycle: part1 -> part2 -> part1
    # First, create parts without children
    part1 = Part(id="part1", name="Part 1", children=[])
    part2 = Part(id="part2", name="Part 2", children=[])
    
    # Set up the cycle by modifying children lists
    # This creates a direct cycle
    part1.children.append(part2)
    part2.children.append(part1)
    
    # The implementation must detect this cycle and raise the exact cycle error
    # We'll add part1 to the top-level parts (part2 is reachable through children)
    # The error message must be exactly: 'Cycle detected in part hierarchy involving part "part1"'
    # or similar with "part2", but it must be a cycle error, not a duplicate-id error
    with pytest.raises(ValueError, match=r'Cycle detected in part hierarchy involving part "part1"'):
        GeometryModel(parts={"part1": part1})

def test_valid_multi_level_hierarchy():
    """Test valid multi-level hierarchy passes validation."""
    level3 = Part(id="level3", name="Level 3")
    level2a = Part(id="level2a", name="Level 2A", children=[level3])
    level2b = Part(id="level2b", name="Level 2B")
    level1 = Part(id="level1", name="Level 1", children=[level2a, level2b])
    
    # This should not raise any errors
    model = GeometryModel(parts={"level1": level1})
    assert model.parts["level1"].children[0].id == "level2a"
    assert model.parts["level1"].children[1].id == "level2b"
    assert model.parts["level1"].children[0].children[0].id == "level3"


def test_key_id_mismatch_validation():
    """Test validation for mismatched dictionary keys and object IDs."""
    # Test part key mismatch
    part = Part(id="part1", name="Part One")
    with pytest.raises(ValueError, match='Part dictionary key "wrong_key" does not match contained Part.id "part1"'):
        GeometryModel(parts={"wrong_key": part})
    
    # Test frame key mismatch
    frame = Frame(id="frame1")
    with pytest.raises(ValueError, match='Frame dictionary key "wrong_key" does not match contained Frame.id "frame1"'):
        GeometryModel(frames={"wrong_key": frame})
    
    # Test anchor key mismatch within a part - should fail at Part creation
    anchor = Anchor(id="anchor1")
    with pytest.raises(ValueError, match='Anchor dictionary key "wrong_key" does not match contained Anchor.id "anchor1"'):
        Part(
            id="part2",
            name="Part Two",
            anchors={"wrong_key": anchor}
        )
    
    # Test boundary key mismatch within a part - should fail at Part creation
    boundary = Boundary(id="boundary1")
    with pytest.raises(ValueError, match='Boundary dictionary key "wrong_key" does not match contained Boundary.id "boundary1"'):
        Part(
            id="part3",
            name="Part Three",
            boundaries={"wrong_key": boundary}
        )
    
    # Test that correct key/id pairs don't raise errors
    part_correct = Part(
        id="part4",
        name="Part Four",
        anchors={"anchor2": Anchor(id="anchor2")},
        boundaries={"boundary2": Boundary(id="boundary2")}
    )
    frame_correct = Frame(id="frame2")
    model = GeometryModel(
        parts={"part4": part_correct},
        frames={"frame2": frame_correct}
    )
    assert model.parts["part4"].id == "part4"
    assert model.frames["frame2"].id == "frame2"


def test_to_dict_and_from_dict_consistency():
    """Test that to_dict and from_dict produce consistent results."""
    # Create a complex model
    frame = Frame(id="global_frame", origin=(1, 2, 3))
    anchor = Anchor(id="ref_point", frame_id="global_frame")
    boundary = Boundary(id="surface")
    child = Part(id="child", name="Child Part")
    parent = Part(
        id="parent",
        name="Parent Part",
        children=[child],
        anchors={"ref_point": anchor},  # Key must match anchor.id
        boundaries={"surface": boundary},  # Key must match boundary.id
        metadata={"material": "steel"}
    )
    
    model = GeometryModel(
        name="Test Model",
        parts={"parent": parent},
        frames={"global_frame": frame}
    )
    
    # Convert to dict and back
    data = model.to_dict()
    new_model = GeometryModel.from_dict(data)
    
    # Check consistency
    assert new_model.name == model.name
    assert new_model.parts["parent"].id == "parent"
    assert new_model.parts["parent"].children[0].id == "child"
    # The anchor key should be "ref_point" (matching the ID)
    assert new_model.parts["parent"].anchors["ref_point"].frame_id == "global_frame"
    assert new_model.frames["global_frame"].origin == (1, 2, 3)
