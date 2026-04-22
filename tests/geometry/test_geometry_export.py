import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

import pytest
from ausolveris.geometry.model import GeometryModel
from ausolveris.geometry.serialization import export_geometry_summary

def test_empty_model_export():
    model = GeometryModel()
    # No parts, frames, primitives set
    result = export_geometry_summary(model)
    assert "parts" in result and result["parts"] == {}
    assert "frames" in result and result["frames"] == {}
    assert "primitives" not in result  # omitted when absent

def test_populated_model_export():
    model = GeometryModel()
    model.parts = {"neck": (0, 1)}
    model.frames = {"main": (0, 0, 0)}
    model.points = {"A": (0,0,0), "B": (1,0,0)}
    model.edges = {"AB": ("A", "B")}
    result = export_geometry_summary(model)
    assert result["parts"] == {"neck": (0, 1)}
    assert result["frames"] == {"main": (0, 0, 0)}
    assert "primitives" in result
    assert result["primitives"]["points"] == {"A": (0,0,0), "B": (1,0,0)}
    assert result["primitives"]["edges"] == {"AB": ("A", "B")}

def test_primitives_included_when_present():
    model = GeometryModel()
    model.points = {"X": (5,5,5)}
    # no edges
    result = export_geometry_summary(model)
    assert "primitives" in result
    assert "points" in result["primitives"]
    assert result["primitives"]["points"] == {"X": (5,5,5)}
    # edges is None/absent in implementation logic, so it is omitted
    assert "edges" not in result["primitives"]

def test_primitives_omitted_when_absent():
    model = GeometryModel()
    # No points, no edges set
    result = export_geometry_summary(model)
    assert "primitives" not in result

def test_export_deterministic():
    model = GeometryModel()
    model.parts = {"a": 1}
    model.frames = {"b": 2}
    model.points = {"c": (0,0,0)}
    result1 = export_geometry_summary(model)
    result2 = export_geometry_summary(model)
    assert result1 == result2

def test_export_shallow_copy_not_mutating_original():
    model = GeometryModel()
    model.points = {"P": (1,2,3)}
    result = export_geometry_summary(model)
    # Modify exported dict
    result["primitives"]["points"]["P"] = (9,9,9)
    # Original model unchanged
    assert model.points["P"] == (1,2,3)

def test_parts_and_frames_default_to_empty_dict():
    model = GeometryModel()
    # Ensure export returns {} for None attributes
    if hasattr(model, 'parts'):
        model.parts = None
    if hasattr(model, 'frames'):
        model.frames = None
    result = export_geometry_summary(model)
    assert result["parts"] == {}
    assert result["frames"] == {}

def test_export_with_only_edges_no_points():
    model = GeometryModel()
    model.edges = {"E": ("A","B")}
    # points is None, edges exists
    result = export_geometry_summary(model)
    assert "primitives" in result
    assert "edges" in result["primitives"]
    assert "points" not in result["primitives"]  # points absent
    assert result["primitives"]["edges"] == {"E": ("A","B")}
