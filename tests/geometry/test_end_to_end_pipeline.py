import sys
import yaml
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

import pytest
from ausolveris.geometry.pipeline import run_end_to_end_pipeline_stub, PipelineStageError

def test_phy001_valid_flow():
    yaml_str = """
    case_id: phy001_free_field_monopole_pressure
    frequency_hz: 100.0
    source_distance_m: 1.0
    topology:
      is_benchmark_ready: true
      patches:
        p1: {source_group: "g1"}
      observers:
        o1: {}
    """
    pkg = run_end_to_end_pipeline_stub(yaml_str)
    assert pkg.selected_case_id == "phy001_free_field_monopole_pressure"
    assert "score_package_id" in pkg.score_summary
    assert pkg.stage_status["score_stage"] == "passed"

def test_phy002_valid_flow():
    yaml_str = """
    case_id: phy002_rigid_cavity_compliance
    cavity_volume_m3: 0.05
    topology:
      is_benchmark_ready: true
      patches:
        p1: {source_group: "g1"}
      observers:
        o1: {}
    """
    pkg = run_end_to_end_pipeline_stub(yaml_str)
    assert pkg.selected_case_id == "phy002_rigid_cavity_compliance"
    assert "score_package_id" in pkg.score_summary

def test_phy002_phy003_lem001_valid_flow():
    yaml_str = """
    case_id: phy002_rigid_cavity_compliance
    cavity_volume_m3: 0.05
    effective_port_length_m: 0.15
    port_area_m2: 0.01
    coupling_mode: lem001_port_cavity_resonance_sanity
    topology:
      is_benchmark_ready: true
      patches:
        p1: {source_group: "g1"}
      observers:
        o1: {}
    """
    pkg = run_end_to_end_pipeline_stub(yaml_str)
    assert pkg.coupling_summary is not None
    assert "resonance_hz" in pkg.coupling_summary
    assert "score_package_id" in pkg.score_summary

def test_invalid_geometry_rejected():
    with pytest.raises(PipelineStageError) as exc:
        run_end_to_end_pipeline_stub("invalid: [yaml: oops")
    assert exc.value.stage == "geometry_stage"

def test_invalid_topology_metadata_rejected():
    yaml_str = "case_id: phy001_free_field_monopole_pressure"
    with pytest.raises(PipelineStageError) as exc:
        run_end_to_end_pipeline_stub(yaml_str)
    assert exc.value.stage == "topology_stage"

def test_invalid_benchmark_descriptor_rejected():
    yaml_str = """
    case_id: phy001_free_field_monopole_pressure
    topology:
      is_benchmark_ready: false
    """
    with pytest.raises(PipelineStageError) as exc:
        run_end_to_end_pipeline_stub(yaml_str)
    assert exc.value.stage == "benchmark_stage"

def test_unsupported_formulation_case_rejected():
    yaml_str = """
    case_id: general_bem
    topology:
      is_benchmark_ready: true
      patches:
        p1: {source_group: "g1"}
      observers:
        o1: {}
    """
    with pytest.raises(PipelineStageError) as exc:
        run_end_to_end_pipeline_stub(yaml_str)
    assert exc.value.stage == "formulation_stage"

def test_invalid_driver_coupling_rejected():
    yaml_str = """
    case_id: phy002_rigid_cavity_compliance
    cavity_volume_m3: 0.05
    coupling_mode: lem001_closed_box_resonance_sanity
    driver:
      fs_hz: -10
      qts: 0.5
      vas_m3: 0.1
    topology:
      is_benchmark_ready: true
      patches:
        p1: {source_group: "g1"}
      observers:
        o1: {}
    """
    with pytest.raises(PipelineStageError) as exc:
        run_end_to_end_pipeline_stub(yaml_str)
    assert exc.value.stage == "coupling_stage"

def test_pipeline_determinism():
    yaml_str = """
    case_id: phy002_rigid_cavity_compliance
    cavity_volume_m3: 0.05
    topology:
      is_benchmark_ready: true
      patches:
        p1: {source_group: "g1"}
      observers:
        o1: {}
    """
    pkg1 = run_end_to_end_pipeline_stub(yaml_str)
    pkg2 = run_end_to_end_pipeline_stub(yaml_str)
    assert pkg1.pipeline_package_id == pkg2.pipeline_package_id
    assert pkg1.score_summary["score_package_id"] == pkg2.score_summary["score_package_id"]

def test_end_to_end_metadata_states():
    yaml_str = """
    case_id: phy001_free_field_monopole_pressure
    topology:
      is_benchmark_ready: true
      patches:
        p1: {source_group: "g1"}
      observers:
        o1: {}
    """
    pkg = run_end_to_end_pipeline_stub(yaml_str)
    assert pkg.pipeline_stage == "end_to_end_pipeline_stub"
    assert pkg.physical_solver is False
    assert pkg.optimization_performed is False
    assert pkg.visualization_generated is False
    assert pkg.batch_mode is False
    assert pkg.supported_cases_only is True
