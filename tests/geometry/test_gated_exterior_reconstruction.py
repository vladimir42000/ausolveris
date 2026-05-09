"""
BEM-006B: Gated exterior reconstruction prototype tests.
Exactly 10 tests as required by the handover document.
"""

import pytest

from ausolveris.geometry.benchmark import build_rigid_sphere_benchmark_fixture
from ausolveris.geometry.bem import (
    assemble_non_singular_prototype_operator,
    assemble_boundary_rhs,
    regularized_solve_prototype,
    RegularizedSolvePrototype,
    build_exterior_observer_scaffold,
    assemble_regular_h_matrix_prototype,
    HMatrixPrototype,
    ReconstructedObserverPressure,
    reconstruct_exterior_observer_pressure,
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
def boundary_solution(sphere_fixture):
    """Real BEM-004C RegularizedSolvePrototype."""
    op = assemble_non_singular_prototype_operator(sphere_fixture, _SELECTED, k_rad_m=K)
    rhs = assemble_boundary_rhs(sphere_fixture, K, AMPLITUDE, DIRECTION, _SELECTED)
    return regularized_solve_prototype(op, rhs)


@pytest.fixture(scope="module")
def observer_scaffold():
    return build_exterior_observer_scaffold(SUPPORTED_ID, SPHERE_RADIUS, _OBSERVER_POSITIONS)


@pytest.fixture(scope="module")
def h_proto(sphere_fixture, observer_scaffold):
    """Real BEM-006A HMatrixPrototype."""
    return assemble_regular_h_matrix_prototype(sphere_fixture, _SELECTED, observer_scaffold, K)


@pytest.fixture(scope="module")
def reconstruction(h_proto, boundary_solution):
    """BEM-006B reconstruction without incident pressure (zero placeholder)."""
    return reconstruct_exterior_observer_pressure(h_proto, boundary_solution)


@pytest.fixture(scope="module")
def reconstruction_with_inc(h_proto, boundary_solution):
    """BEM-006B reconstruction with dummy incident pressure supplied."""
    n = len(_OBSERVER_POSITIONS)
    inc = [1.0 + 0.5j] * n
    return reconstruct_exterior_observer_pressure(h_proto, boundary_solution, inc)


# ---------------------------------------------------------------------------
# Test 1: Valid H-matrix prototype and boundary solution are accepted.
# ---------------------------------------------------------------------------

def test_1_valid_inputs_accepted(h_proto, boundary_solution):
    """Valid BEM-006A HMatrixPrototype and BEM-004C RegularizedSolvePrototype are accepted."""
    assert isinstance(h_proto, HMatrixPrototype)
    assert isinstance(boundary_solution, RegularizedSolvePrototype)

    result = reconstruct_exterior_observer_pressure(h_proto, boundary_solution)
    assert isinstance(result, ReconstructedObserverPressure)
    assert result.benchmark_id == SUPPORTED_ID


# ---------------------------------------------------------------------------
# Test 2: Invalid H-matrix package is rejected with controlled ValueError.
# ---------------------------------------------------------------------------

def test_2_invalid_h_matrix_rejected(boundary_solution):
    """Non-HMatrixPrototype h_matrix_prototype raises controlled ValueError."""
    with pytest.raises(ValueError, match="HMatrixPrototype"):
        reconstruct_exterior_observer_pressure({"not": "a prototype"}, boundary_solution)
    with pytest.raises(ValueError, match="HMatrixPrototype"):
        reconstruct_exterior_observer_pressure(None, boundary_solution)


# ---------------------------------------------------------------------------
# Test 3: Invalid boundary solution package is rejected with controlled ValueError.
# ---------------------------------------------------------------------------

def test_3_invalid_boundary_solution_rejected(h_proto):
    """Non-RegularizedSolvePrototype boundary_solution raises controlled ValueError."""
    with pytest.raises(ValueError, match="RegularizedSolvePrototype"):
        reconstruct_exterior_observer_pressure(h_proto, "not a solution")
    with pytest.raises(ValueError, match="RegularizedSolvePrototype"):
        reconstruct_exterior_observer_pressure(h_proto, 42)


# ---------------------------------------------------------------------------
# Test 4: Matrix/vector dimension mismatch is rejected with controlled ValueError.
# ---------------------------------------------------------------------------

def test_4_dimension_mismatch_rejected(sphere_fixture, observer_scaffold, boundary_solution):
    """H with different panel count than solution vector raises ValueError."""
    # Build H with a different panel subset (4 panels vs 3 in boundary_solution)
    alt_h = assemble_regular_h_matrix_prototype(
        sphere_fixture, [0, 2, 4, 6], observer_scaffold, K
    )
    with pytest.raises(ValueError, match="[Dd]imension"):
        reconstruct_exterior_observer_pressure(alt_h, boundary_solution)


# ---------------------------------------------------------------------------
# Test 5: reconstructed_scattered_pressure equals deterministic H @ x result.
# ---------------------------------------------------------------------------

def test_5_scattered_pressure_equals_hx(reconstruction, h_proto, boundary_solution):
    """p_scattered[i] == sum_j(H[i,j] * x[j]) for all observer points."""
    x = boundary_solution.solution
    H = h_proto.h_matrix
    n_pan = h_proto.panel_count
    n_obs = h_proto.observer_count
    for i in range(n_obs):
        expected = sum(H[i][j] * x[j] for j in range(n_pan))
        assert abs(reconstruction.reconstructed_scattered_pressure[i] - expected) < 1e-14


# ---------------------------------------------------------------------------
# Test 6: reconstructed_total_pressure includes incident pressure when provided.
# ---------------------------------------------------------------------------

def test_6_total_includes_incident_when_provided(reconstruction_with_inc, h_proto, boundary_solution):
    """p_total[i] = p_incident[i] + p_scattered[i] when incident is supplied."""
    assert reconstruction_with_inc.incident_pressure_supplied is True
    n = h_proto.observer_count
    for i in range(n):
        inc_i = reconstruction_with_inc.reconstructed_incident_pressure[i]
        scat_i = reconstruction_with_inc.reconstructed_scattered_pressure[i]
        total_i = reconstruction_with_inc.reconstructed_total_pressure[i]
        assert abs(total_i - (inc_i + scat_i)) < 1e-14

    # When no incident supplied: incident is zero, total == scattered
    result_no_inc = reconstruct_exterior_observer_pressure(h_proto, boundary_solution)
    assert result_no_inc.incident_pressure_supplied is False
    for i in range(n):
        assert result_no_inc.reconstructed_incident_pressure[i] == 0j
        assert abs(result_no_inc.reconstructed_total_pressure[i]
                   - result_no_inc.reconstructed_scattered_pressure[i]) < 1e-14


# ---------------------------------------------------------------------------
# Test 7: Package ID is SHA-256-like and stable for identical inputs.
# ---------------------------------------------------------------------------

def test_7_package_id_stable(h_proto, boundary_solution):
    """Package ID is 64-char hex and identical across two identical calls."""
    r1 = reconstruct_exterior_observer_pressure(h_proto, boundary_solution)
    r2 = reconstruct_exterior_observer_pressure(h_proto, boundary_solution)
    pid = r1.deterministic_package_id
    assert isinstance(pid, str)
    assert len(pid) == 64
    assert all(c in "0123456789abcdef" for c in pid)
    assert pid == r2.deterministic_package_id


# ---------------------------------------------------------------------------
# Test 8: Package ID changes when reconstruction inputs change.
# ---------------------------------------------------------------------------

def test_8_package_id_changes_with_inputs(h_proto, boundary_solution):
    """Package ID differs when incident pressure flag changes."""
    r_no_inc = reconstruct_exterior_observer_pressure(h_proto, boundary_solution)
    n = h_proto.observer_count
    r_with_inc = reconstruct_exterior_observer_pressure(
        h_proto, boundary_solution, [1.0 + 0j] * n
    )
    assert r_no_inc.deterministic_package_id != r_with_inc.deterministic_package_id


# ---------------------------------------------------------------------------
# Test 9: physical_h_matrix_assembled=True; physical_reconstruction_performed=True.
# ---------------------------------------------------------------------------

def test_9_physical_flags_true(reconstruction):
    """Metadata correctly reports physical assembly and reconstruction performed."""
    assert reconstruction.physical_h_matrix_assembled is True
    assert reconstruction.physical_reconstruction_performed is True
    assert reconstruction.reconstruction_stage == "bem006b_gated_exterior_reconstruction"


# ---------------------------------------------------------------------------
# Test 10: No analytical comparison, no tolerance policy, no singular quadrature,
#           no SPL/directivity/impedance, non_physical=True.
# ---------------------------------------------------------------------------

def test_10_all_negative_capability_flags(reconstruction):
    """All gated/absent capability flags are False; result is non_physical."""
    assert reconstruction.analytical_reference_comparison_performed is False
    assert reconstruction.tolerance_policy_applied is False
    assert reconstruction.singular_quadrature_implemented is False
    assert reconstruction.spl_computed is False
    assert reconstruction.directivity_computed is False
    assert reconstruction.impedance_computed is False
    assert reconstruction.non_physical is True
