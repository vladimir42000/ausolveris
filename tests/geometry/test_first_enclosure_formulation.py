import sys, math
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))
import pytest
from ausolveris.geometry.acoustic_view import AcousticTopologyView, AcousticPatch, AcousticObserver
from ausolveris.geometry.solver import AcousticOperatorAssemblyPackage, FirstEnclosureFormulationInput, evaluate_phy002_first_enclosure_case, SingleCaseAcousticFormulationInput, evaluate_phy001_single_case

@pytest.fixture
def valid_topology():
    view = AcousticTopologyView(patches={"p1": AcousticPatch("p1", "o1", "f1", (1,0,0), source_group="sg1")}, observers={"obs1": AcousticObserver("pt1")})
    view.is_benchmark_ready = True
    return view

@pytest.fixture
def valid_input(valid_topology):
    pkg = AcousticOperatorAssemblyPackage(operator_package_id="pkg1", topology_signature="sig", benchmark_descriptor_id="phy002_rigid_cavity_compliance", non_physical=True)
    return FirstEnclosureFormulationInput(topology_view=valid_topology, operator_package=pkg, benchmark_id="phy002_rigid_cavity_compliance", cavity_volume_m3=0.05, rho0=1.21, c0=343.0)

def test_phy002_case_accepted(valid_input):
    res = evaluate_phy002_first_enclosure_case(valid_input)
    assert res.physical_case == "phy002_rigid_cavity_compliance"
    assert res.acoustic_compliance_m5_per_n > 0

def test_compliance_value_matches(valid_input):
    res = evaluate_phy002_first_enclosure_case(valid_input)
    assert math.isclose(res.acoustic_compliance_m5_per_n, valid_input.cavity_volume_m3 / (valid_input.rho0 * (valid_input.c0 ** 2)), rel_tol=1e-9)

def test_phy001_remains_supported(valid_topology):
    pkg = AcousticOperatorAssemblyPackage(operator_package_id="pkg001", topology_signature="sig", benchmark_descriptor_id="phy001_free_field_monopole_pressure", non_physical=True)
    inp = SingleCaseAcousticFormulationInput(topology_view=valid_topology, operator_package=pkg, benchmark_id="phy001_free_field_monopole_pressure", frequency_hz=100.0, source_distance_m=1.0)
    assert evaluate_phy001_single_case(inp).physical_case == "phy001_free_field_monopole_pressure"

def test_unsupported_enclosure_case_rejected(valid_input):
    valid_input.benchmark_id = "sealed_box_solver"
    with pytest.raises(ValueError, match="Unsupported benchmark case"): evaluate_phy002_first_enclosure_case(valid_input)

def test_invalid_topology_rejected(valid_input):
    valid_input.topology_view.is_benchmark_ready = False
    with pytest.raises(ValueError, match="Topology is not benchmark-ready"): evaluate_phy002_first_enclosure_case(valid_input)

def test_missing_cavity_volume_rejected(valid_input):
    valid_input.cavity_volume_m3 = None
    with pytest.raises(ValueError, match="Missing cavity volume"): evaluate_phy002_first_enclosure_case(valid_input)

def test_non_positive_cavity_volume_rejected(valid_input):
    valid_input.cavity_volume_m3 = -0.5
    with pytest.raises(ValueError, match="Cavity volume must be strictly positive"): evaluate_phy002_first_enclosure_case(valid_input)

def test_operator_package_not_marked_non_physical_rejected(valid_input):
    valid_input.operator_package.non_physical = False
    with pytest.raises(ValueError, match="must be explicitly marked non_physical"): evaluate_phy002_first_enclosure_case(valid_input)

def test_deterministic_output(valid_input):
    assert evaluate_phy002_first_enclosure_case(valid_input).acoustic_compliance_m5_per_n == evaluate_phy002_first_enclosure_case(valid_input).acoustic_compliance_m5_per_n

def test_result_metadata_explicitly_single_case(valid_input):
    res = evaluate_phy002_first_enclosure_case(valid_input)
    assert not res.enclosure_solver and not res.bem_implemented
