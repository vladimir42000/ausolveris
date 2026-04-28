import sys, math
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))
import pytest
from ausolveris.geometry.acoustic_view import AcousticTopologyView, AcousticPatch, AcousticObserver
from ausolveris.geometry.solver import AcousticOperatorAssemblyPackage, evaluate_phy001_single_case, SingleCaseAcousticFormulationInput, evaluate_phy002_first_enclosure_case, FirstEnclosureFormulationInput, PortInertanceFormulationInput, evaluate_phy003_port_inertance

@pytest.fixture
def valid_topology():
    view = AcousticTopologyView(patches={"p1": AcousticPatch("p1", "o1", "f1", (1,0,0), source_group="sg1")}, observers={"obs1": AcousticObserver("pt1")})
    view.is_benchmark_ready = True
    return view

@pytest.fixture
def valid_input(valid_topology):
    pkg = AcousticOperatorAssemblyPackage(operator_package_id="pkg1", topology_signature="sig", benchmark_descriptor_id="phy003_simple_port_inertance", non_physical=True)
    return PortInertanceFormulationInput(topology_view=valid_topology, operator_package=pkg, benchmark_id="phy003_simple_port_inertance", effective_port_length_m=0.15, port_area_m2=0.01, rho0=1.21)

def test_phy003_case_accepted(valid_input):
    res = evaluate_phy003_port_inertance(valid_input)
    assert res.physical_case == "phy003_simple_port_inertance"
    assert res.acoustic_inertance_kg_per_m4 > 0

def test_inertance_value_matches(valid_input):
    res = evaluate_phy003_port_inertance(valid_input)
    assert math.isclose(res.acoustic_inertance_kg_per_m4, (valid_input.rho0 * valid_input.effective_port_length_m) / valid_input.port_area_m2, rel_tol=1e-9)

def test_phy001_remains_supported(valid_topology):
    pkg = AcousticOperatorAssemblyPackage(operator_package_id="p1", topology_signature="s", benchmark_descriptor_id="phy001_free_field_monopole_pressure", non_physical=True)
    inp = SingleCaseAcousticFormulationInput(topology_view=valid_topology, operator_package=pkg, benchmark_id="phy001_free_field_monopole_pressure", frequency_hz=100.0, source_distance_m=1.0)
    assert evaluate_phy001_single_case(inp).physical_case == "phy001_free_field_monopole_pressure"

def test_phy002_remains_supported(valid_topology):
    pkg = AcousticOperatorAssemblyPackage(operator_package_id="p2", topology_signature="s", benchmark_descriptor_id="phy002_rigid_cavity_compliance", non_physical=True)
    inp = FirstEnclosureFormulationInput(topology_view=valid_topology, operator_package=pkg, benchmark_id="phy002_rigid_cavity_compliance", cavity_volume_m3=0.05)
    assert evaluate_phy002_first_enclosure_case(inp).physical_case == "phy002_rigid_cavity_compliance"

def test_unsupported_coupled_case_rejected(valid_input):
    valid_input.benchmark_id = "bass_reflex_solver"
    with pytest.raises(ValueError, match="Unsupported benchmark case"): evaluate_phy003_port_inertance(valid_input)

def test_invalid_topology_rejected(valid_input):
    valid_input.topology_view.is_benchmark_ready = False
    with pytest.raises(ValueError, match="Topology is not benchmark-ready"): evaluate_phy003_port_inertance(valid_input)

def test_missing_port_area_rejected(valid_input):
    valid_input.port_area_m2 = None
    with pytest.raises(ValueError, match="Missing port area"): evaluate_phy003_port_inertance(valid_input)

def test_non_positive_port_dimensions_rejected(valid_input):
    valid_input.port_area_m2 = -0.01
    with pytest.raises(ValueError, match="Port area must be strictly positive"): evaluate_phy003_port_inertance(valid_input)

def test_operator_package_not_marked_non_physical_rejected(valid_input):
    valid_input.operator_package.non_physical = False
    with pytest.raises(ValueError, match="must be explicitly marked non_physical"): evaluate_phy003_port_inertance(valid_input)

def test_result_metadata_explicitly_single_case(valid_input):
    res = evaluate_phy003_port_inertance(valid_input)
    assert not res.bass_reflex_solver and not res.automatic_end_correction
