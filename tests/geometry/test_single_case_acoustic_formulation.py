import sys
import math
import cmath
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

import pytest
from ausolveris.geometry.acoustic_view import AcousticTopologyView, AcousticPatch, AcousticObserver
from ausolveris.geometry.solver import AcousticOperatorAssemblyPackage, SingleCaseAcousticFormulationInput, evaluate_phy001_single_case

@pytest.fixture
def valid_topology():
    view = AcousticTopologyView(
        patches={"p1": AcousticPatch("p1", "o1", "f1", (1,0,0), source_group="sg1")},
        observers={"obs1": AcousticObserver("pt1")}
    )
    view.is_benchmark_ready = True
    return view

@pytest.fixture
def valid_operator_pkg():
    return AcousticOperatorAssemblyPackage(
        operator_package_id="pkg1",
        topology_signature="sig",
        benchmark_descriptor_id="phy001_free_field_monopole_pressure",
        non_physical=True
    )

@pytest.fixture
def valid_input(valid_topology, valid_operator_pkg):
    return SingleCaseAcousticFormulationInput(
        topology_view=valid_topology,
        operator_package=valid_operator_pkg,
        benchmark_id="phy001_free_field_monopole_pressure",
        frequency_hz=100.0,
        source_distance_m=1.0,
        volume_velocity_m3_s=0.01,
        rho0=1.21,
        c0=343.0
    )

def test_canonical_case_accepted(valid_input):
    result = evaluate_phy001_single_case(valid_input)
    assert result.frequency_hz == 100.0
    assert result.pressure_magnitude > 0

def test_unsupported_benchmark_rejected(valid_input):
    valid_input.benchmark_id = "sealed_box"
    with pytest.raises(ValueError, match="Unsupported benchmark case: sealed_box"):
        evaluate_phy001_single_case(valid_input)

def test_invalid_topology_metadata_rejected(valid_input):
    valid_input.topology_view.observers["obs2"] = AcousticObserver("pt2")
    with pytest.raises(ValueError, match="Multiple observers not supported"):
        evaluate_phy001_single_case(valid_input)

def test_missing_benchmark_ready_rejected(valid_input):
    valid_input.topology_view.is_benchmark_ready = False
    with pytest.raises(ValueError, match="Topology is not benchmark-ready"):
        evaluate_phy001_single_case(valid_input)

def test_missing_source_group_rejected(valid_input):
    valid_input.topology_view.patches["p1"].source_group = None
    with pytest.raises(ValueError, match="Missing source-group declaration"):
        evaluate_phy001_single_case(valid_input)

def test_missing_observer_rejected(valid_input):
    valid_input.topology_view.observers = {}
    with pytest.raises(ValueError, match="Missing observer mapping"):
        evaluate_phy001_single_case(valid_input)

def test_invalid_distance_rejected(valid_input):
    valid_input.source_distance_m = -1.0
    with pytest.raises(ValueError, match="Source-observer distance must be strictly positive"):
        evaluate_phy001_single_case(valid_input)

def test_deterministic_output(valid_input):
    res1 = evaluate_phy001_single_case(valid_input)
    res2 = evaluate_phy001_single_case(valid_input)
    assert res1.pressure_complex == res2.pressure_complex

def test_analytical_sanity_comparison(valid_input):
    result = evaluate_phy001_single_case(valid_input)
    f = valid_input.frequency_hz
    omega = 2 * math.pi * f
    k = omega / valid_input.c0
    r = valid_input.source_distance_m
    Q = valid_input.volume_velocity_m3_s
    rho0 = valid_input.rho0
    
    expected_mag = (rho0 * omega * Q) / (4 * math.pi * r)
    expected_complex = 1j * expected_mag * cmath.exp(-1j * k * r)
    
    assert math.isclose(result.pressure_magnitude, expected_mag, rel_tol=1e-9)
    assert math.isclose(result.pressure_complex.real, expected_complex.real, rel_tol=1e-9)
    assert math.isclose(result.pressure_complex.imag, expected_complex.imag, rel_tol=1e-9)

def test_result_metadata_explicitly_single_case(valid_input):
    result = evaluate_phy001_single_case(valid_input)
    assert result.physical_case == "phy001_free_field_monopole_pressure"
    assert result.formulation_scope == "single_case_only"
    assert result.general_solver is False
    assert result.bem_implemented is False
    assert result.lem_implemented is False
    assert result.enclosure_model is False
