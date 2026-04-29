import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

import pytest
from ausolveris.geometry.optimizer import (
    ObservableScorePackage,
    SingleObjectiveFitnessDescriptor,
    SingleObjectiveFitnessPackage,
    build_single_objective_fitness_descriptor_stub,
    validate_fitness_descriptor_label
)
from ausolveris.geometry.visualizer import ObservableVisualizationPackage

@pytest.fixture
def opt_pkg():
    return ObservableScorePackage(
        score_package_id="score_123", source_physical_case="phy001",
        observable_labels=["obs1"], normalized_placeholder_score=0.5,
        input_signature="sig", supported_case_count=1, formulation_scope="single"
    )

@pytest.fixture
def vis_pkg():
    return ObservableVisualizationPackage(
        plot_package_id="vis_456", source_package_id="score_123",
        plot_label="dummy_label", annotations={}, placeholder_x=[], placeholder_y=[]
    )

def test_opt002_accepted(opt_pkg):
    desc = SingleObjectiveFitnessDescriptor("valid_objective")
    fit = build_single_objective_fitness_descriptor_stub(opt_pkg, desc)
    assert fit.source_package_id == "score_123"
    assert fit.source_package_family == "OPT-002"

def test_vis001_accepted(vis_pkg):
    desc = SingleObjectiveFitnessDescriptor("valid_objective")
    fit = build_single_objective_fitness_descriptor_stub(vis_pkg, desc)
    assert fit.source_package_id == "vis_456"
    assert fit.source_package_family == "VIS-001"

def test_unsupported_type_rejected():
    desc = SingleObjectiveFitnessDescriptor("valid_objective")
    with pytest.raises(TypeError, match="Unsupported package type"):
        build_single_objective_fitness_descriptor_stub("bad_input_string", desc)

def test_deterministic_sha256_id(opt_pkg):
    desc = SingleObjectiveFitnessDescriptor("valid_objective")
    fit = build_single_objective_fitness_descriptor_stub(opt_pkg, desc)
    assert fit.fitness_package_id.startswith("fit_")
    assert len(fit.fitness_package_id) == 4 + 16

def test_repeated_generation_is_stable(opt_pkg):
    desc = SingleObjectiveFitnessDescriptor("valid_objective")
    fit1 = build_single_objective_fitness_descriptor_stub(opt_pkg, desc)
    fit2 = build_single_objective_fitness_descriptor_stub(opt_pkg, desc)
    assert fit1.fitness_package_id == fit2.fitness_package_id

def test_required_non_physical_markers_present(opt_pkg):
    desc = SingleObjectiveFitnessDescriptor("valid_objective")
    fit = build_single_objective_fitness_descriptor_stub(opt_pkg, desc)
    assert fit.fitness_stage == "single_objective_fitness_stub"
    assert fit.non_physical_fitness is True
    assert fit.optimization_performed is False
    assert fit.ranking_performed is False
    assert fit.design_quality_evaluated is False
    assert fit.spl_fitness is False
    assert fit.impedance_fitness is False
    assert fit.frequency_response_fitness is False

def test_forbidden_labels_blocked(opt_pkg):
    desc = SingleObjectiveFitnessDescriptor("spl_fitness")
    with pytest.raises(ValueError, match="strictly forbidden"):
        build_single_objective_fitness_descriptor_stub(opt_pkg, desc)
        
    desc2 = SingleObjectiveFitnessDescriptor("acoustic_merit")
    with pytest.raises(ValueError, match="strictly forbidden"):
        build_single_objective_fitness_descriptor_stub(opt_pkg, desc2)

def test_placeholder_scalar_markers(opt_pkg):
    desc = SingleObjectiveFitnessDescriptor("valid_objective")
    fit = build_single_objective_fitness_descriptor_stub(opt_pkg, desc)
    assert hasattr(fit, "placeholder_fitness_value")
    assert fit.placeholder_value_non_physical is True
    assert fit.acoustic_interpretation is False

def test_no_forbidden_fields(opt_pkg):
    desc = SingleObjectiveFitnessDescriptor("valid_objective")
    fit = build_single_objective_fitness_descriptor_stub(opt_pkg, desc)
    forbidden = [
        "spl_score", "impedance_score", "frequency_response_score",
        "acoustic_merit", "design_quality", "ranking", "rank",
        "recommendation", "optimized_parameters", "best_candidate",
        "target_curve_error", "objective_value_with_physical_meaning"
    ]
    for f in forbidden:
        assert not hasattr(fit, f)

def test_existing_behavior_unchanged(opt_pkg):
    assert opt_pkg.score_package_id == "score_123"
    desc = SingleObjectiveFitnessDescriptor("valid_objective")
    fit = build_single_objective_fitness_descriptor_stub(opt_pkg, desc)
    assert fit.fitness_package_id is not None
