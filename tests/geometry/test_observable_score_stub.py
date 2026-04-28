import sys
import yaml
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

import pytest
from ausolveris.geometry.solver import (
    SingleCaseAcousticFormulationResult,
    FirstEnclosureFormulationResult,
    PortInertanceFormulationResult
)
from ausolveris.geometry.optimizer import (
    ObservableScoreDescriptor,
    ObservableScorePackage,
    compute_observable_score_stub
)

@pytest.fixture
def desc():
    return ObservableScoreDescriptor(descriptor_id="opt01", target_observable="stub_metric", metadata={"key": "val"})

def test_phy001_maps_to_stub(desc):
    res = SingleCaseAcousticFormulationResult(
        frequency_hz=100.0, pressure_complex=1j, pressure_magnitude=1.0, 
        source_observer_distance_m=1.0, rho0=1.21, c0=343.0, volume_velocity_m3_s=0.01, 
        wavenumber_rad_m=1.8, angular_frequency_rad_s=628.0
    )
    pkg = compute_observable_score_stub(res, desc)
    assert pkg.source_physical_case == "phy001_free_field_monopole_pressure"

def test_phy002_maps_to_stub(desc):
    res = FirstEnclosureFormulationResult(
        cavity_volume_m3=0.05, rho0=1.21, c0=343.0, acoustic_compliance_m5_per_n=0.0001
    )
    pkg = compute_observable_score_stub(res, desc)
    assert pkg.source_physical_case == "phy002_rigid_cavity_compliance"

def test_phy003_maps_to_stub(desc):
    res = PortInertanceFormulationResult(
        port_area_m2=0.01, effective_port_length_m=0.15, rho0=1.21, acoustic_inertance_kg_per_m4=18.15
    )
    pkg = compute_observable_score_stub(res, desc)
    assert pkg.source_physical_case == "phy003_simple_port_inertance"

def test_unsupported_output_rejected(desc):
    class BadResult:
        physical_case = "bass_reflex"
    with pytest.raises(ValueError, match="Unsupported formulation output case"):
        compute_observable_score_stub(BadResult(), desc)

def test_sha256_deterministic_id(desc):
    res = FirstEnclosureFormulationResult(
        cavity_volume_m3=0.05, rho0=1.21, c0=343.0, acoustic_compliance_m5_per_n=0.0001
    )
    pkg = compute_observable_score_stub(res, desc)
    assert pkg.score_package_id.startswith("score_")
    assert len(pkg.score_package_id) == 6 + 16 # "score_" + 16 hex chars

def test_repeated_computation_stable(desc):
    res = FirstEnclosureFormulationResult(cavity_volume_m3=0.05, rho0=1.21, c0=343.0, acoustic_compliance_m5_per_n=0.0001)
    pkg1 = compute_observable_score_stub(res, desc)
    pkg2 = compute_observable_score_stub(res, desc)
    assert pkg1.score_package_id == pkg2.score_package_id
    assert pkg1.input_signature == pkg2.input_signature

def test_yaml_roundtrip_preserves_descriptor_metadata():
    desc1 = ObservableScoreDescriptor(descriptor_id="opt02", target_observable="test", metadata={"param_a": 42})
    yaml_str = yaml.dump(desc1.__dict__)
    loaded = yaml.safe_load(yaml_str)
    desc2 = ObservableScoreDescriptor(**loaded)
    assert desc1.descriptor_id == desc2.descriptor_id
    assert desc1.metadata["param_a"] == desc2.metadata["param_a"]

def test_marked_non_physical_score(desc):
    res = PortInertanceFormulationResult(port_area_m2=0.01, effective_port_length_m=0.15, rho0=1.21, acoustic_inertance_kg_per_m4=18.15)
    pkg = compute_observable_score_stub(res, desc)
    assert pkg.non_physical_score is True
    assert pkg.score_stage == "observable_score_stub"

def test_optimization_performed_false(desc):
    res = PortInertanceFormulationResult(port_area_m2=0.01, effective_port_length_m=0.15, rho0=1.21, acoustic_inertance_kg_per_m4=18.15)
    pkg = compute_observable_score_stub(res, desc)
    assert pkg.optimization_performed is False
    assert pkg.fitness_function == "none"
    assert pkg.ranking_performed is False

def test_no_forbidden_fields(desc):
    res = FirstEnclosureFormulationResult(cavity_volume_m3=0.05, rho0=1.21, c0=343.0, acoustic_compliance_m5_per_n=0.0001)
    pkg = compute_observable_score_stub(res, desc)
    forbidden_fields = ["spl_score", "impedance_score", "bass_reflex_score", "design_quality", "optimized_parameters", "gradient", "objective_value", "best_candidate", "recommendation"]
    for field in forbidden_fields:
        assert not hasattr(pkg, field)
