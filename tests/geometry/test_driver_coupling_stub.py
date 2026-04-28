import sys
import math
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

import pytest
from ausolveris.geometry.solver import (
    FirstEnclosureFormulationResult,
    PortInertanceFormulationResult,
    DriverMetadata,
    DriverCouplingPackage,
    evaluate_lem001_driver_coupling_stub
)

@pytest.fixture
def valid_cavity():
    return FirstEnclosureFormulationResult(
        cavity_volume_m3=0.05, rho0=1.21, c0=343.0, acoustic_compliance_m5_per_n=0.00035
    )

@pytest.fixture
def valid_port():
    return PortInertanceFormulationResult(
        port_area_m2=0.01, effective_port_length_m=0.15, rho0=1.21, acoustic_inertance_kg_per_m4=18.15
    )

@pytest.fixture
def valid_driver():
    return DriverMetadata(fs_hz=35.0, qts=0.4, vas_m3=0.1)

def test_closed_box_sanity_produces_package(valid_cavity, valid_driver):
    pkg = evaluate_lem001_driver_coupling_stub(
        "lem001_closed_box_resonance_sanity", valid_driver, valid_cavity
    )
    assert isinstance(pkg, DriverCouplingPackage)
    assert pkg.formula_id == "fc = fs * sqrt(1 + Vas/Vb)"

def test_port_cavity_sanity_produces_package(valid_cavity, valid_port, valid_driver):
    pkg = evaluate_lem001_driver_coupling_stub(
        "lem001_port_cavity_resonance_sanity", valid_driver, valid_cavity, valid_port
    )
    assert isinstance(pkg, DriverCouplingPackage)
    assert pkg.formula_id == "f = 1/(2*pi*sqrt(Ma*Ca))"

def test_closed_box_scalar_result_matches(valid_cavity, valid_driver):
    pkg = evaluate_lem001_driver_coupling_stub(
        "lem001_closed_box_resonance_sanity", valid_driver, valid_cavity
    )
    expected_fc = valid_driver.fs_hz * math.sqrt(1 + valid_driver.vas_m3 / valid_cavity.cavity_volume_m3)
    assert math.isclose(pkg.resonance_hz, expected_fc, rel_tol=1e-9)

def test_port_cavity_scalar_result_matches(valid_cavity, valid_port, valid_driver):
    pkg = evaluate_lem001_driver_coupling_stub(
        "lem001_port_cavity_resonance_sanity", valid_driver, valid_cavity, valid_port
    )
    ma = valid_port.acoustic_inertance_kg_per_m4
    ca = valid_cavity.acoustic_compliance_m5_per_n
    expected_f = 1.0 / (2.0 * math.pi * math.sqrt(ma * ca))
    assert math.isclose(pkg.resonance_hz, expected_f, rel_tol=1e-9)

def test_invalid_driver_metadata_rejected(valid_cavity):
    bad_fs = DriverMetadata(fs_hz=-1.0, qts=0.4, vas_m3=0.1)
    with pytest.raises(ValueError, match="fs_hz must be > 0"):
        evaluate_lem001_driver_coupling_stub("lem001_closed_box_resonance_sanity", bad_fs, valid_cavity)
        
    bad_qts = DriverMetadata(fs_hz=35.0, qts=0.0, vas_m3=0.1)
    with pytest.raises(ValueError, match="qts must be > 0"):
        evaluate_lem001_driver_coupling_stub("lem001_closed_box_resonance_sanity", bad_qts, valid_cavity)
        
    bad_vas = DriverMetadata(fs_hz=35.0, qts=0.4, vas_m3=0.0)
    with pytest.raises(ValueError, match="vas_m3 must be > 0"):
        evaluate_lem001_driver_coupling_stub("lem001_closed_box_resonance_sanity", bad_vas, valid_cavity)

def test_unsupported_coupling_mode_rejected(valid_cavity, valid_driver):
    with pytest.raises(ValueError, match="Unsupported coupling mode: bass_reflex_solver"):
        evaluate_lem001_driver_coupling_stub("bass_reflex_solver", valid_driver, valid_cavity)

def test_missing_cavity_compliance_rejected(valid_driver, valid_port):
    with pytest.raises(ValueError, match="Missing or invalid PHY-002 cavity compliance result"):
        evaluate_lem001_driver_coupling_stub("lem001_closed_box_resonance_sanity", valid_driver, None)

def test_port_cavity_missing_port_result_rejected(valid_cavity, valid_driver):
    with pytest.raises(ValueError, match="Missing or invalid PHY-003 port inertance"):
        evaluate_lem001_driver_coupling_stub("lem001_port_cavity_resonance_sanity", valid_driver, valid_cavity, None)

def test_deterministic_package_id(valid_cavity, valid_driver):
    pkg1 = evaluate_lem001_driver_coupling_stub("lem001_closed_box_resonance_sanity", valid_driver, valid_cavity)
    pkg2 = evaluate_lem001_driver_coupling_stub("lem001_closed_box_resonance_sanity", valid_driver, valid_cavity)
    assert pkg1.coupling_package_id == pkg2.coupling_package_id
    assert pkg1.coupling_package_id.startswith("lem_")

def test_metadata_states_no_lem_solver(valid_cavity, valid_driver):
    pkg = evaluate_lem001_driver_coupling_stub("lem001_closed_box_resonance_sanity", valid_driver, valid_cavity)
    assert pkg.scalar_sanity_only is True
    assert pkg.full_lem_solver is False
    assert pkg.impedance_computed is False
    assert pkg.spl_computed is False
    assert pkg.frequency_sweep_computed is False
    assert pkg.optimization_performed is False
    assert pkg.bass_reflex_solver is False
    assert pkg.closed_box_solver is False
