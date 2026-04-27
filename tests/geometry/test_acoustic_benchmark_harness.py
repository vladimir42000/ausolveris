import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

import pytest
import yaml
from ausolveris.geometry.acoustic_view import AcousticTopologyView, AcousticPatch, AcousticInterface, AcousticObserver
from ausolveris.geometry.benchmark import (
    AcousticBenchmarkDescriptor,
    AcousticBenchmarkReadinessResult,
    validate_acoustic_benchmark_descriptor,
    evaluate_acoustic_benchmark_readiness,
)

def test_valid_benchmark_descriptor_accepted():
    desc = AcousticBenchmarkDescriptor(
        benchmark_id="b01",
        label="rigid wall",
        category="rigid_wall",
        required_patch_kinds=["rigid_wall"],
        required_interface_count=0,
        required_observer_count=1,
    )
    errors = validate_acoustic_benchmark_descriptor(desc)
    assert errors == []

def test_missing_topology_precondition_rejected():
    desc = AcousticBenchmarkDescriptor(
        benchmark_id="b02",
        label="needs interface",
        category="interface",
        required_interface_count=1,
    )
    view = AcousticTopologyView(interfaces={})
    result = evaluate_acoustic_benchmark_readiness(view, desc)
    assert not result.is_ready
    assert any("Interface count 0 < required 1" in r for r in result.reasons)

def test_missing_observer_definition_rejected():
    desc = AcousticBenchmarkDescriptor(
        benchmark_id="b03",
        label="needs observer",
        category="observer",
        required_observer_count=1,
    )
    view = AcousticTopologyView(observers={})
    result = evaluate_acoustic_benchmark_readiness(view, desc)
    assert not result.is_ready
    assert any("Observer count 0 < required 1" in r for r in result.reasons)

def test_invalid_interface_side_metadata_rejected():
    desc = AcousticBenchmarkDescriptor(
        benchmark_id="b04",
        label="interface side",
        category="interface",
        require_interface_side_metadata=True,
    )
    # side_a == side_b
    view = AcousticTopologyView(
        interfaces={"i1": AcousticInterface("i1", "same", "same")}
    )
    result = evaluate_acoustic_benchmark_readiness(view, desc)
    assert not result.is_ready
    assert any("Interface side metadata invalid" in r for r in result.reasons)

def test_unsupported_enclosure_label_rejected():
    desc = AcousticBenchmarkDescriptor(
        benchmark_id="b05",
        label="bad",
        category="sealed_box_solver",   # forbidden
    )
    errors = validate_acoustic_benchmark_descriptor(desc)
    assert any("Unsupported enclosure‑specific category" in e for e in errors)

def test_benchmark_fixture_loading_deterministic():
    desc = AcousticBenchmarkDescriptor(
        benchmark_id="b06",
        label="det",
        category="det",
    )
    view = AcousticTopologyView()
    result1 = evaluate_acoustic_benchmark_readiness(view, desc)
    result2 = evaluate_acoustic_benchmark_readiness(view, desc)
    assert result1.is_ready == result2.is_ready
    assert result1.reasons == result2.reasons

def test_yaml_roundtrip_preserves_metadata():
    desc = AcousticBenchmarkDescriptor(
        benchmark_id="b07",
        label="yaml",
        category="test",
        require_source_group=True,
    )
    yaml_str = yaml.dump(desc.__dict__)
    loaded_dict = yaml.safe_load(yaml_str)
    loaded_desc = AcousticBenchmarkDescriptor(**loaded_dict)
    assert loaded_desc.benchmark_id == desc.benchmark_id
    assert loaded_desc.require_source_group == desc.require_source_group

def test_harness_consumes_acoustic_view_only():
    # This test ensures that benchmark does not access raw GeometryModel.
    # We can't easily test negative, but we check that evaluate_acoustic_benchmark_readiness
    # takes an AcousticTopologyView, not a GeometryModel.
    view = AcousticTopologyView()
    desc = AcousticBenchmarkDescriptor(benchmark_id="b08", label="test", category="test")
    result = evaluate_acoustic_benchmark_readiness(view, desc)
    # If it accepts a view, that's the contract.
    assert isinstance(result, AcousticBenchmarkReadinessResult)

def test_source_group_readiness_structural_only():
    desc = AcousticBenchmarkDescriptor(
        benchmark_id="b09",
        label="source group",
        category="source_group",
        require_source_group=True,
    )
    view = AcousticTopologyView(
        patches={
            "p1": AcousticPatch("p1", "owner1", "frame1", (1,0,0), source_group="groupA")
        }
    )
    result = evaluate_acoustic_benchmark_readiness(view, desc)
    assert result.is_ready
    assert result.has_source_group is True
    # No acoustic numerical fields
    assert not hasattr(result, 'spl')
    assert not hasattr(result, 'impedance')

def test_readiness_output_contains_only_structural_fields():
    desc = AcousticBenchmarkDescriptor(benchmark_id="b10", label="test", category="test")
    view = AcousticTopologyView()
    result = evaluate_acoustic_benchmark_readiness(view, desc)
    # Allowed fields: descriptor_id, is_ready, reasons, patch_count, interface_count,
    # observer_count, has_source_group, has_orientation_metadata, has_frame_metadata,
    # has_interface_side_metadata
    for field in ['descriptor_id', 'is_ready', 'reasons', 'patch_count', 'interface_count',
                  'observer_count', 'has_source_group', 'has_orientation_metadata',
                  'has_frame_metadata', 'has_interface_side_metadata']:
        assert hasattr(result, field)
    # No acoustic numerics
    assert not hasattr(result, 'pressure')
    assert not hasattr(result, 'velocity')
