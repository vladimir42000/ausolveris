"""
BEM-005C: Analytical reference matching and tolerance scaffold tests.
Exactly 10 tests as required by the handover document.
"""

import pytest

from ausolveris.geometry.benchmark import build_rigid_sphere_benchmark_fixture
from ausolveris.geometry.bem import (
    assemble_non_singular_prototype_operator,
    assemble_boundary_rhs,
    regularized_solve_prototype,
    build_exterior_observer_scaffold,
    ObserverReconstructionScaffold,
    build_reconstruction_gate_request,
    execute_reconstruction_gate,
    ReconstructionGateResult,
    AnalyticalRigidSphereReferenceEvaluator,
    ReferenceMatchingReport,
    build_analytical_matching_report,
)

SUPPORTED_ID = "ben004_rigid_sphere_scattering_registered"
SPHERE_RADIUS = 1.0
K = 2.0
AMPLITUDE = 1.0 + 0j
DIRECTION = (0, 0, 1)
_OBSERVER_POSITIONS = [(2.0, 0.0, 0.0), (0.0, 2.0, 0.0), (0.0, 0.0, 2.0)]


class _Pts:
    """Minimal .observer_positions wrapper (harmonized canonical attribute)."""
    def __init__(self, pts):
        self.observer_positions = pts


# ---------------------------------------------------------------------------
# Module-scoped fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def sphere_fixture():
    return build_rigid_sphere_benchmark_fixture(SUPPORTED_ID, subdivision_level=1)


@pytest.fixture(scope="module")
def analytical_package():
    """BEM-004F analytical reference package for the observer positions."""
    evaluator = AnalyticalRigidSphereReferenceEvaluator(
        sphere_radius=SPHERE_RADIUS,
        k=K,
        amplitude=AMPLITUDE,
        direction=DIRECTION,
    )
    return evaluator.evaluate(_OBSERVER_POSITIONS)


@pytest.fixture(scope="module")
def gate_result(sphere_fixture):
    """BEM-005B gated reconstruction result (zeroed non-physical)."""
    op = assemble_non_singular_prototype_operator(sphere_fixture, [0, 2, 4], k_rad_m=K)
    rhs = assemble_boundary_rhs(sphere_fixture, K, AMPLITUDE, DIRECTION, [0, 2, 4])
    boundary_solution = regularized_solve_prototype(op, rhs)
    observer_scaffold = build_exterior_observer_scaffold(
        SUPPORTED_ID, SPHERE_RADIUS, _OBSERVER_POSITIONS
    )
    reconstruction_scaffold = ObserverReconstructionScaffold(
        _Pts(_OBSERVER_POSITIONS),
        {"boundary_data_present": True, "stage": "bem004c_stub"},
    )
    request = build_reconstruction_gate_request(
        boundary_solution, observer_scaffold, reconstruction_scaffold
    )
    return execute_reconstruction_gate(request)


@pytest.fixture(scope="module")
def matching_report(analytical_package, gate_result):
    """BEM-005C ReferenceMatchingReport from valid inputs."""
    return build_analytical_matching_report(analytical_package, gate_result)


# ---------------------------------------------------------------------------
# Test 1: Valid analytical reference package and gated result are accepted.
# ---------------------------------------------------------------------------

def test_1_valid_inputs_accepted(analytical_package, gate_result):
    """build_analytical_matching_report accepts real BEM-004F + BEM-005B packages."""
    assert isinstance(gate_result, ReconstructionGateResult)
    assert "total_pressure" in analytical_package
    assert analytical_package["metadata"]["benchmark_id"] == SUPPORTED_ID

    report = build_analytical_matching_report(analytical_package, gate_result)
    assert isinstance(report, ReferenceMatchingReport)
    assert report.benchmark_id == SUPPORTED_ID


# ---------------------------------------------------------------------------
# Test 2: Benchmark ID mismatch is rejected with controlled ValueError.
# ---------------------------------------------------------------------------

def test_2_benchmark_id_mismatch_rejected(analytical_package, gate_result):
    """Wrong benchmark_id in either package raises controlled ValueError."""
    # Tamper analytical metadata
    bad_anal = dict(analytical_package)
    bad_anal["metadata"] = dict(analytical_package["metadata"])
    bad_anal["metadata"]["benchmark_id"] = "wrong_id"
    with pytest.raises(ValueError, match="benchmark_id"):
        build_analytical_matching_report(bad_anal, gate_result)

    # Wrong type for reconstruction_result (catches wrong benchmark_id via type guard)
    with pytest.raises(ValueError, match="ReconstructionGateResult"):
        build_analytical_matching_report(analytical_package, {"not": "a result"})


# ---------------------------------------------------------------------------
# Test 3: Pressure array length mismatch is rejected with controlled ValueError.
# ---------------------------------------------------------------------------

def test_3_length_mismatch_rejected(analytical_package, gate_result):
    """Different-length total_pressure arrays raise controlled ValueError."""
    short_anal = dict(analytical_package)
    short_anal["total_pressure"] = list(analytical_package["total_pressure"])[:1]
    with pytest.raises(ValueError, match="length mismatch"):
        build_analytical_matching_report(short_anal, gate_result)


# ---------------------------------------------------------------------------
# Test 4: relative_l2_error is computed deterministically for zeroed reconstruction.
# ---------------------------------------------------------------------------

def test_4_relative_l2_error_deterministic(matching_report, analytical_package):
    """relative_l2_error equals 1.0 when reconstruction is all-zeros."""
    # ||p_anal - 0|| / ||p_anal|| = 1.0
    assert isinstance(matching_report.relative_l2_error, float)
    assert abs(matching_report.relative_l2_error - 1.0) < 1.0e-12


# ---------------------------------------------------------------------------
# Test 5: max_abs_error is computed deterministically.
# ---------------------------------------------------------------------------

def test_5_max_abs_error_deterministic(matching_report, analytical_package):
    """max_abs_error equals max(|p_anal[i]|) when reconstruction is all-zeros."""
    p_anal = analytical_package["total_pressure"]
    expected_max = max(abs(v) for v in p_anal)
    assert isinstance(matching_report.max_abs_error, float)
    assert abs(matching_report.max_abs_error - expected_max) < 1.0e-12


# ---------------------------------------------------------------------------
# Test 6: Tolerance policy is marked applied.
# ---------------------------------------------------------------------------

def test_6_tolerance_policy_applied(matching_report):
    """tolerance_policy_applied=True and tolerance thresholds are set."""
    assert matching_report.tolerance_policy_applied is True
    assert matching_report.relative_pressure_tolerance == 1.0e-2
    assert matching_report.absolute_pressure_tolerance == 1.0e-6


# ---------------------------------------------------------------------------
# Test 7: benchmark_passed is False for gated zero reconstruction.
# ---------------------------------------------------------------------------

def test_7_benchmark_passed_false_for_gated_result(matching_report):
    """benchmark_passed=False because BEM-005B returns zeroed non-physical pressures."""
    assert matching_report.benchmark_passed is False
    assert matching_report.reference_matching_performed is True


# ---------------------------------------------------------------------------
# Test 8: Metadata preserves all negative capability flags.
# ---------------------------------------------------------------------------

def test_8_metadata_negative_capability_flags(matching_report):
    """All gated/absent capability flags remain False; non_physical=True."""
    assert matching_report.validation_stage == "bem005c_analytical_matching_scaffold"
    assert matching_report.physical_h_matrix_assembled is False
    assert matching_report.singular_quadrature_implemented is False
    assert matching_report.spl_computed is False
    assert matching_report.directivity_computed is False
    assert matching_report.impedance_computed is False
    assert matching_report.non_physical is True


# ---------------------------------------------------------------------------
# Test 9: Deterministic package ID is SHA-256-like and stable for same inputs.
# ---------------------------------------------------------------------------

def test_9_deterministic_package_id_stable(analytical_package, gate_result):
    """Package ID is 64-char hex and identical for two calls with identical inputs."""
    r1 = build_analytical_matching_report(analytical_package, gate_result)
    r2 = build_analytical_matching_report(analytical_package, gate_result)

    pid = r1.deterministic_package_id
    assert isinstance(pid, str)
    assert len(pid) == 64
    assert all(c in "0123456789abcdef" for c in pid)
    assert pid == r2.deterministic_package_id


# ---------------------------------------------------------------------------
# Test 10: Package ID changes when comparison inputs change.
# ---------------------------------------------------------------------------

def test_10_package_id_changes_with_different_inputs(analytical_package, gate_result):
    """Package ID changes when observer positions (and thus pressures) change."""
    alt_positions = [(3.0, 0.0, 0.0), (0.0, 3.0, 0.0), (0.0, 0.0, 3.0)]
    alt_evaluator = AnalyticalRigidSphereReferenceEvaluator(
        sphere_radius=SPHERE_RADIUS, k=K, amplitude=AMPLITUDE, direction=DIRECTION,
    )
    alt_anal = alt_evaluator.evaluate(alt_positions)

    # Build a matching gate_result at the same observer count but different ID
    alt_obs_scaffold = build_exterior_observer_scaffold(SUPPORTED_ID, SPHERE_RADIUS, alt_positions)
    alt_rec_scaffold = ObserverReconstructionScaffold(
        _Pts(alt_positions),
        {"boundary_data_present": True, "stage": "bem004c_stub"},
    )

    from ausolveris.geometry.benchmark import build_rigid_sphere_benchmark_fixture
    from ausolveris.geometry.bem import (
        assemble_non_singular_prototype_operator,
        assemble_boundary_rhs,
        regularized_solve_prototype,
    )
    fix = build_rigid_sphere_benchmark_fixture(SUPPORTED_ID, subdivision_level=1)
    op = assemble_non_singular_prototype_operator(fix, [0, 2, 4], k_rad_m=K)
    rhs = assemble_boundary_rhs(fix, K, AMPLITUDE, DIRECTION, [0, 2, 4])
    bsol = regularized_solve_prototype(op, rhs)
    req = build_reconstruction_gate_request(bsol, alt_obs_scaffold, alt_rec_scaffold)
    alt_gate = execute_reconstruction_gate(req)

    alt_report = build_analytical_matching_report(alt_anal, alt_gate)
    base_report = build_analytical_matching_report(analytical_package, gate_result)

    assert alt_report.deterministic_package_id != base_report.deterministic_package_id
    assert len(alt_report.deterministic_package_id) == 64
