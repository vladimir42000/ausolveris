import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

import pytest
from ausolveris.geometry.model import GeometryModel, Boundary
from ausolveris.geometry.acoustic_view import (
    derive_acoustic_topology, AcousticPatch, AcousticInterface,
    AcousticObserver, AcousticTopologyView
)

def make_base_model():
    model = GeometryModel()
    model.boundaries = {"b1": Boundary(id="b1"), "b2": Boundary(id="b2")}
    model.points = {"p1": (0,0,0), "p2": (1,0,0)}
    return model

def test_empty_metadata_empty_view():
    model = make_base_model()
    view = derive_acoustic_topology(model, {})
    assert not view.patches
    assert not view.errors

def test_valid_patch_derived():
    model = make_base_model()
    meta = {'acoustic': {'patches': {'b1': {'owner': 'part1', 'frame': 'f1', 'normal': (1,0,0)}}}}
    view = derive_acoustic_topology(model, meta)
    assert 'b1' in view.patches
    assert view.patches['b1'].normal == (1,0,0)
    assert not view.errors

def test_patch_boundary_not_in_model():
    model = make_base_model()
    meta = {'acoustic': {'patches': {'unknown_b': {'owner': 'p', 'frame': 'f', 'normal': (1,0,0)}}}}
    view = derive_acoustic_topology(model, meta)
    assert len(view.errors) == 1
    assert "not found in model" in view.errors[0]

def test_patch_missing_required_fields():
    model = make_base_model()
    meta = {'acoustic': {'patches': {'b1': {'owner': 'part1'}}}}
    view = derive_acoustic_topology(model, meta)
    assert len(view.errors) == 1
    assert "missing required metadata" in view.errors[0]

def test_patch_invalid_normal_dimension():
    model = make_base_model()
    meta = {'acoustic': {'patches': {'b1': {'owner': 'p', 'frame': 'f', 'normal': (1,0)}}}}
    view = derive_acoustic_topology(model, meta)
    assert len(view.errors) == 1
    assert "normal must be 3D" in view.errors[0]

def test_valid_interface_derived():
    model = make_base_model()
    meta = {'acoustic': {
        'patches': {'b1': {'owner': 'p', 'frame': 'f', 'normal': (1,0,0)}},
        'interfaces': {'iface1': {'side_a': 'b1', 'side_b': 'b2'}}
    }}
    view = derive_acoustic_topology(model, meta)
    assert 'iface1' in view.interfaces
    assert view.interfaces['iface1'].side_a == 'b1'
    assert not view.errors

def test_interface_missing_sides():
    model = make_base_model()
    meta = {'acoustic': {'interfaces': {'iface1': {'side_a': 'b1'}}}}
    view = derive_acoustic_topology(model, meta)
    assert len(view.errors) == 1
    assert "missing side_a or side_b" in view.errors[0]

def test_interface_same_sides():
    model = make_base_model()
    meta = {'acoustic': {'interfaces': {'iface1': {'side_a': 'b1', 'side_b': 'b1'}}}}
    view = derive_acoustic_topology(model, meta)
    assert len(view.errors) == 1
    assert "side_a == side_b" in view.errors[0]

def test_interface_unknown_sides():
    model = make_base_model()
    meta = {'acoustic': {'interfaces': {'iface1': {'side_a': 'ghost1', 'side_b': 'ghost2'}}}}
    view = derive_acoustic_topology(model, meta)
    assert len(view.errors) == 2
    assert "not found" in view.errors[0]

def test_observer_valid_and_missing_point():
    model = make_base_model()
    meta = {'acoustic': {'observers': {
        'obs1': {'point_id': 'p1'},
        'obs2': {'point_id': 'ghost'},
        'obs3': {}
    }}}
    view = derive_acoustic_topology(model, meta)
    assert 'obs1' in view.observers
    assert len(view.errors) == 2
