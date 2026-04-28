import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

import pytest
from ausolveris.geometry.pipeline import EndToEndPipelinePackage
from ausolveris.geometry.optimizer import ObservableScorePackage
from ausolveris.geometry.visualizer import (
    ObservableVisualizationDescriptor,
    ObservableVisualizationPackage,
    build_observable_visualization_stub,
    validate_visualization_label
)

@pytest.fixture
def int_pkg():
    return EndToEndPipelinePackage(
        pipeline_package_id="pipe_123", selected_case_id="phy001",
        formulation_summary={}, coupling_summary={"resonance_hz": 50.0},
        score_summary={}, stage_status={}, input_signature="sig"
    )

@pytest.fixture
def opt_pkg():
    return ObservableScorePackage(
        score_package_id="score_456", source_physical_case="phy001",
        observable_labels=["obs1"], normalized_placeholder_score=0.5,
        input_signature="sig", supported_case_count=1, formulation_scope="single"
    )

def test_int002_accepted(int_pkg):
    desc = ObservableVisualizationDescriptor("valid_plot")
    vis = build_observable_visualization_stub(int_pkg, desc)
    assert vis.source_package_id == "pipe_123"
    assert isinstance(vis, ObservableVisualizationPackage)

def test_opt002_accepted(opt_pkg):
    desc = ObservableVisualizationDescriptor("valid_plot")
    vis = build_observable_visualization_stub(opt_pkg, desc)
    assert vis.source_package_id == "score_456"

def test_unsupported_rejected():
    desc = ObservableVisualizationDescriptor("valid_plot")
    with pytest.raises(TypeError, match="Unsupported package type"):
        build_observable_visualization_stub("just_a_string_not_a_pkg", desc)

def test_deterministic_id(int_pkg):
    desc = ObservableVisualizationDescriptor("valid_plot")
    vis1 = build_observable_visualization_stub(int_pkg, desc)
    vis2 = build_observable_visualization_stub(int_pkg, desc)
    assert vis1.plot_package_id == vis2.plot_package_id
    assert vis1.plot_package_id.startswith("vis_")

def test_required_markers(opt_pkg):
    desc = ObservableVisualizationDescriptor("valid_plot")
    vis = build_observable_visualization_stub(opt_pkg, desc)
    assert vis.visualization_stage == "visualization_stub"
    assert vis.non_physical_plot is True
    assert vis.spl_plot is False
    assert vis.frequency_response is False
    assert vis.impedance_plot is False
    assert vis.optimization_plot is False
    assert vis.cb_response_plot is False
    assert vis.br_response_plot is False

def test_rejected_labels(opt_pkg):
    with pytest.raises(ValueError, match="strictly forbidden"):
        build_observable_visualization_stub(opt_pkg, ObservableVisualizationDescriptor("spl"))
    
    with pytest.raises(ValueError, match="strictly forbidden"):
        build_observable_visualization_stub(opt_pkg, ObservableVisualizationDescriptor("impedance_curve"))

def test_placeholder_arrays_marked(opt_pkg):
    desc = ObservableVisualizationDescriptor("valid_plot", metadata={"include_placeholders": True})
    vis = build_observable_visualization_stub(opt_pkg, desc)
    assert len(vis.placeholder_x) > 0
    assert len(vis.placeholder_y) > 0
    assert vis.placeholder_data is True
    assert vis.physical_response is False
    assert vis.acoustic_units == "none"

def test_no_forbidden_fields(int_pkg):
    desc = ObservableVisualizationDescriptor("valid_plot")
    vis = build_observable_visualization_stub(int_pkg, desc)
    forbidden = ["spl", "impedance", "transfer_function", "cb_response", "br_response"]
    for f in forbidden:
        assert not hasattr(vis, f)

def test_lem_metadata_annotation(int_pkg):
    desc = ObservableVisualizationDescriptor("valid_plot")
    vis = build_observable_visualization_stub(int_pkg, desc)
    assert "lem_scalar_sanity" in vis.annotations
    assert vis.annotations["lem_scalar_sanity"]["resonance_hz"] == 50.0

def test_existing_behavior_unchanged(int_pkg):
    desc = ObservableVisualizationDescriptor("valid_plot")
    build_observable_visualization_stub(int_pkg, desc)
    assert int_pkg.pipeline_package_id == "pipe_123"
