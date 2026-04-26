import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

import pytest
from ausolveris.geometry.acoustic_view import AcousticTopologyView, AcousticPatch, AcousticInterface, AcousticObserver
from ausolveris.geometry.solver import consume_acoustic_topology

def test_valid_empty_view():
    view = AcousticTopologyView()
    res = consume_acoustic_topology(view)
    assert res['patch_count'] == 0
    assert res['owner_count'] == 0

def test_invalid_view_raises_error():
    view = AcousticTopologyView(errors=["Some error occurred"])
    with pytest.raises(ValueError, match="Invalid acoustic topology"):
        consume_acoustic_topology(view)

def test_counts_are_accurate():
    view = AcousticTopologyView(
        patches={
            "b1": AcousticPatch("b1", "o1", "f1", (1,0,0)),
            "b2": AcousticPatch("b2", "o2", "f1", (0,1,0))
        },
        interfaces={"i1": AcousticInterface("i1", "b1", "b2")},
        observers={"obs1": AcousticObserver("p1")}
    )
    res = consume_acoustic_topology(view)
    assert res['patch_count'] == 2
    assert res['interface_count'] == 1
    assert res['observer_count'] == 1
    assert res['owner_count'] == 2

def test_source_groups_counted_distinctly():
    view = AcousticTopologyView(
        patches={
            "b1": AcousticPatch("b1", "o1", "f1", (1,0,0), source_group="g1"),
            "b2": AcousticPatch("b2", "o2", "f1", (0,1,0), source_group="g1"),
            "b3": AcousticPatch("b3", "o3", "f1", (0,0,1), source_group="g2")
        }
    )
    res = consume_acoustic_topology(view)
    assert res['source_group_count'] == 2

def test_interface_pairs_extracted():
    view = AcousticTopologyView(
        interfaces={
            "i1": AcousticInterface("i1", "b1", "b2"),
            "i2": AcousticInterface("i2", "b3", "b4")
        }
    )
    res = consume_acoustic_topology(view)
    assert ("b1", "b2") in res['interface_side_pairs']
    assert ("b3", "b4") in res['interface_side_pairs']
    assert len(res['interface_side_pairs']) == 2

def test_orientation_metadata_flag():
    view = AcousticTopologyView(
        patches={"b1": AcousticPatch("b1", "o1", "f1", (1,0,0))}
    )
    res = consume_acoustic_topology(view)
    assert res['orientation_metadata_present'] is True

def test_owner_count_deduplication():
    view = AcousticTopologyView(
        patches={
            "b1": AcousticPatch("b1", "o1", "f1", (1,0,0)),
            "b2": AcousticPatch("b2", "o1", "f1", (0,1,0))
        }
    )
    res = consume_acoustic_topology(view)
    assert res['owner_count'] == 1

def test_no_unresolved_observers_on_valid_view():
    view = AcousticTopologyView(observers={"obs1": AcousticObserver("p1")})
    res = consume_acoustic_topology(view)
    assert res['unresolved_observers'] == []

def test_duplicate_ownership_detected_false():
    view = AcousticTopologyView(patches={"b1": AcousticPatch("b1", "o1", "f1", (1,0,0))})
    res = consume_acoustic_topology(view)
    assert res['duplicate_ownership_detected'] is False

def test_structural_keys_present():
    view = AcousticTopologyView()
    res = consume_acoustic_topology(view)
    expected_keys = [
        'patch_count', 'interface_count', 'observer_count', 'source_group_count',
        'owner_count', 'interface_side_pairs', 'orientation_metadata_present',
        'duplicate_ownership_detected', 'unresolved_observers'
    ]
    for key in expected_keys:
        assert key in res
