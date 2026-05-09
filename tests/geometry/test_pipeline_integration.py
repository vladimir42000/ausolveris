"""
BEM-006C: Pipeline integration report tests.
Exactly 10 tests as required by the handover document.
"""

import pytest

from ausolveris.geometry.benchmark import build_rigid_sphere_benchmark_fixture
from ausolveris.geometry.bem import (
    assemble_non_singular_prototype_operator,
    assemble_boundary_rhs,
    regularized_solve_prototype,
    build_exterior_observer_scaffold,
    assemble_regular_h_matrix_prototype,
    reconstruct_exterior_observer_pressure,
    ReconstructedObserverPressure,
    AnalyticalRigidSphereReferenceEvaluator,
    PipelineIntegrationReport,
    build_pipeline_integration_report,
)

SUPPORTED_ID = "ben004_rigid_sphere_scattering_registered"
SPHERE_RADIUS = 1.0
K = 2.0
AMPLITUDE = 1.0 + 0j
DIRECTION = (0, 0, 1)
_OBSERVER_POSITIONS = [(2.0, 0.0, 0.0), (0.0, 2.0, 0.0), (0.0, 0.0, 2.0)]
_SELECTED = [0, 2, 4]


# ---------------------------------------------------------------------------
# Module-scoped fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def sphere_fixture():
    return build_rigid_sphere_benchmark_fixture(SUPPORTED_ID, subdivision_level=1)


@pytest.fixture(scope="module")
def analytical_package():
    """BEM-004F analytical reference package."""
    ev = AnalyticalRigidSphereReferenceEvaluator(
        sphere_radius=SPHERE_RADIUS, k=K,
        amplitude=AMPLITUDE, direction=DIRECTION,
    )
    return ev.evaluate(_OBSERVER_POSITIONS)


@pytest.fixture(scope="module")
def reconstructed_pressure(sphere_fixture):
    """BEM-006B real numerical reconstructed pressure (H @ x)."""
    op  = assemble_non_singular_prototype_operator(sphere_fixture, _SELECTED, k_rad_m=K)
    rhs = assemble_boundary_rhs(sphere_fixture, K, AMPLITUDE, DIRECTION, _SELECTED)
    bsol = regularized_solve_prototype(op, rhs)
    obs  = build_exterior_observer_scaffold(SUPPORTED_ID, SPHERE_RADIUS, _OBSERVER_POSITIONS)
    h    = assemble_regular_h_matrix_prototype(sphere_fixture, _SELECTED, obs, K)
    return reconstruct_exterior_observer_pressure(h, bsol)


@pytest.fixture(scope="module")
def report(analytical_package, reconstructed_pressure):
    """BEM-006C PipelineIntegrationReport."""
    return build_pipeline_integration_report(analytical_package, reconstructed_pressure)


# ---------------------------------------------------------------------------
# Test 1: Valid BEM-004F and BEM-006B packages are accepted.
# ---------------------------------------------------------------------------

def test_1_valid_inputs_accepted(analytical_package, reconstructed_pressure):
    """Real BEM-004F and BEM-006B packages produce a PipelineIntegrationReport."""
    assert isinstance(reconstructed_pressure, ReconstructedObserverPressure)
    assert reconstructed_pressure.physical_reconstruction_performed is True

    rpt = build_pipeline_integration_report(analytical_package, reconstructed_pressure)
    assert isinstance(rpt, PipelineIntegrationReport)
    assert rpt.benchmark_id == SUPPORTED_ID


# ---------------------------------------------------------------------------
# Test 2: Benchmark ID mismatch is rejected with controlled ValueError.
# ---------------------------------------------------------------------------

def test_2_benchmark_id_mismatch_rejected(analytical_package, reconstructed_pressure):
    """Wrong benchmark_id in either package raises controlled ValueError."""
    bad_anal = dict(analytical_package)
    bad_anal["metadata"] = dict(analytical_package["metadata"])
    bad_anal["metadata"]["benchmark_id"] = "wrong_id"
    with pytest.raises(ValueError, match="benchmark_id"):
        build_pipeline_integration_report(bad_anal, reconstructed_pressure)

    with pytest.raises(ValueError, match="ReconstructedObserverPressure"):
        build_pipeline_integration_report(analytical_package, {"not": "a result"})


# ---------------------------------------------------------------------------
# Test 3: Pressure array length mismatch is rejected with controlled ValueError.
# ---------------------------------------------------------------------------

def test_3_length_mismatch_rejected(analytical_package, reconstructed_pressure):
    """Analytical total_pressure with wrong length raises ValueError."""
    short = dict(analytical_package)
    short["total_pressure"] = list(analytical_package["total_pressure"])[:1]
    with pytest.raises(ValueError, match="length mismatch"):
        build_pipeline_integration_report(short, reconstructed_pressure)


# ---------------------------------------------------------------------------
# Test 4: Numerical reconstructed data is consumed, not gated-zero data.
# ---------------------------------------------------------------------------

def test_4_numerical_data_consumed(report, reconstructed_pressure):
    """numerical_data_consumed=True and reconstructed pressures are non-zero."""
    assert report.numerical_data_consumed is True
    assert reconstructed_pressure.physical_reconstruction_performed is True
    # At least one scattered pressure entry must be non-zero (real H@x result)
    assert any(
        abs(v) > 0.0
        for v in reconstructed_pressure.reconstructed_scattered_pressure
    )


# ---------------------------------------------------------------------------
# Test 5: relative_l2_error is computed from real complex arrays.
# ---------------------------------------------------------------------------

def test_5_relative_l2_error_from_real_arrays(report, analytical_package,
                                               reconstructed_pressure):
    """relative_l2_error matches manual computation from actual arrays."""
    import math
    p_anal = analytical_package["total_pressure"]
    p_rec  = reconstructed_pressure.reconstructed_total_pressure
    n = len(p_anal)
    norm_a = math.sqrt(sum(abs(v)**2 for v in p_anal))
    diff   = [p_anal[i] - p_rec[i] for i in range(n)]
    expected = math.sqrt(sum(abs(d)**2 for d in diff)) / norm_a
    assert abs(report.relative_l2_error - expected) < 1e-12
    assert isinstance(report.relative_l2_error, float)


# ---------------------------------------------------------------------------
# Test 6: max_abs_error is computed from real complex arrays.
# ---------------------------------------------------------------------------

def test_6_max_abs_error_from_real_arrays(report, analytical_package,
                                           reconstructed_pressure):
    """max_abs_error matches manual computation from actual arrays."""
    p_anal = analytical_package["total_pressure"]
    p_rec  = reconstructed_pressure.reconstructed_total_pressure
    n = len(p_anal)
    expected = max(abs(p_anal[i] - p_rec[i]) for i in range(n))
    assert abs(report.max_abs_error - expected) < 1e-12
    assert isinstance(report.max_abs_error, float)


# ---------------------------------------------------------------------------
# Test 7: Tolerance policy is applied; benchmark_passed remains False.
# ---------------------------------------------------------------------------

def test_7_tolerance_applied_benchmark_fails(report):
    """tolerance_policy_applied=True and benchmark_passed=False."""
    assert report.tolerance_policy_applied is True
    assert report.relative_pressure_tolerance == 1.0e-2
    assert report.absolute_pressure_tolerance == 1.0e-6
    assert report.benchmark_passed is False


# ---------------------------------------------------------------------------
# Test 8: Metadata states numerical_data_consumed, analytical_reference_matched,
#          and error_norms_computed all True.
# ---------------------------------------------------------------------------

def test_8_positive_metadata_flags(report):
    """Metadata correctly records what was consumed and computed."""
    assert report.numerical_data_consumed is True
    assert report.analytical_reference_matched is True
    assert report.error_norms_computed is True
    assert report.validation_stage == "bem006c_pipeline_integration_report"
    assert report.non_physical_prototype_warning is True


# ---------------------------------------------------------------------------
# Test 9: Metadata preserves no singular quadrature and no derived outputs.
# ---------------------------------------------------------------------------

def test_9_negative_capability_flags(report):
    """Absent capabilities are correctly flagged False."""
    assert report.singular_quadrature_implemented is False
    assert report.spl_computed is False
    assert report.directivity_computed is False
    assert report.impedance_computed is False
    assert report.physical_h_matrix_assembled is True


# ---------------------------------------------------------------------------
# Test 10: Package ID is SHA-256-like, stable, and changes with different inputs.
# ---------------------------------------------------------------------------

def test_10_deterministic_package_id(analytical_package, reconstructed_pressure,
                                      sphere_fixture):
    """Package ID is 64-char hex, stable for same inputs, different for changed inputs."""
    r1 = build_pipeline_integration_report(analytical_package, reconstructed_pressure)
    r2 = build_pipeline_integration_report(analytical_package, reconstructed_pressure)

    pid = r1.deterministic_package_id
    assert isinstance(pid, str)
    assert len(pid) == 64
    assert all(c in "0123456789abcdef" for c in pid)
    assert pid == r2.deterministic_package_id

    # Different observer positions → different reconstruction → different ID
    alt_pos = [(3.0, 0.0, 0.0), (0.0, 3.0, 0.0), (0.0, 0.0, 3.0)]
    alt_ev  = AnalyticalRigidSphereReferenceEvaluator(
        sphere_radius=SPHERE_RADIUS, k=K, amplitude=AMPLITUDE, direction=DIRECTION,
    )
    alt_anal = alt_ev.evaluate(alt_pos)
    alt_obs  = build_exterior_observer_scaffold(SUPPORTED_ID, SPHERE_RADIUS, alt_pos)
    alt_h    = assemble_regular_h_matrix_prototype(sphere_fixture, _SELECTED, alt_obs, K)
    op       = assemble_non_singular_prototype_operator(sphere_fixture, _SELECTED, k_rad_m=K)
    rhs      = assemble_boundary_rhs(sphere_fixture, K, AMPLITUDE, DIRECTION, _SELECTED)
    bsol     = regularized_solve_prototype(op, rhs)
    alt_rec  = reconstruct_exterior_observer_pressure(alt_h, bsol)
    alt_rpt  = build_pipeline_integration_report(alt_anal, alt_rec)
    assert alt_rpt.deterministic_package_id != pid
    assert len(alt_rpt.deterministic_package_id) == 64
