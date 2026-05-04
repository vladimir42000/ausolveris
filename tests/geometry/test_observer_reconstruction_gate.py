"""
BEM-005B: Observer reconstruction execution gate tests.
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
    ExteriorObserverScaffold,
    ObserverReconstructionScaffold,
    build_reconstruction_gate_request,
    execute_reconstruction_gate,
    ReconstructionGateRequest,
    ReconstructionGateResult,
)

SUPPORTED_ID = "ben004_rigid_sphere_scattering_registered"
SPHERE_RADIUS = 1.0
_OBSERVER_POSITIONS = [(2.0, 0.0, 0.0), (0.0, 2.0, 0.0), (0.0, 0.0, 2.0)]


# ---------------------------------------------------------------------------
# Shared helper: lightweight wrapper giving ObserverReconstructionScaffold
# the .points attribute it requires, identical pattern to BEM-005A tests.
# ---------------------------------------------------------------------------

class _Pts:
    """Minimal .points wrapper — same pattern used throughout BEM-005A tests."""
    def __init__(self, pts):
        self.points = pts


# ---------------------------------------------------------------------------
# Module-scoped fixtures (build once, shared across tests)
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def sphere_fixture():
    return build_rigid_sphere_benchmark_fixture(SUPPORTED_ID, subdivision_level=1)


@pytest.fixture(scope="module")
def boundary_solution(sphere_fixture):
    """Real BEM-004C RegularizedSolvePrototype package."""
    op = assemble_non_singular_prototype_operator(sphere_fixture, [0, 2, 4], k_rad_m=2.0)
    rhs = assemble_boundary_rhs(sphere_fixture, 2.0, 1.0 + 0j, (0, 0, 1), [0, 2, 4])
    return regularized_solve_prototype(op, rhs)


@pytest.fixture(scope="module")
def observer_scaffold():
    """Real BEM-004E ExteriorObserverScaffold."""
    return build_exterior_observer_scaffold(SUPPORTED_ID, SPHERE_RADIUS, _OBSERVER_POSITIONS)


@pytest.fixture(scope="module")
def reconstruction_scaffold():
    """Real BEM-005A ObserverReconstructionScaffold, using the approved .points wrapper."""
    return ObserverReconstructionScaffold(
        _Pts(_OBSERVER_POSITIONS),
        {"boundary_data_present": True, "stage": "bem004c_stub"},
    )


@pytest.fixture(scope="module")
def valid_request(boundary_solution, observer_scaffold, reconstruction_scaffold):
    """Fully validated ReconstructionGateRequest."""
    return build_reconstruction_gate_request(
        boundary_solution, observer_scaffold, reconstruction_scaffold
    )


@pytest.fixture(scope="module")
def gate_result(valid_request):
    """Executed ReconstructionGateResult from the valid request."""
    return execute_reconstruction_gate(valid_request)


# ---------------------------------------------------------------------------
# Test 1: Valid inputs are accepted; all three real structures are exercised.
# ---------------------------------------------------------------------------

def test_1_valid_request_accepts_real_packages(boundary_solution, observer_scaffold,
                                               reconstruction_scaffold):
    """Valid BEM-004C + BEM-004E + BEM-005A packages produce a validated request."""
    assert isinstance(boundary_solution, RegularizedSolvePrototype)
    assert isinstance(observer_scaffold, ExteriorObserverScaffold)
    assert isinstance(reconstruction_scaffold, ObserverReconstructionScaffold)

    request = build_reconstruction_gate_request(
        boundary_solution, observer_scaffold, reconstruction_scaffold
    )
    assert isinstance(request, ReconstructionGateRequest)
    assert request.request_validated is True
    assert request.benchmark_id == SUPPORTED_ID


# ---------------------------------------------------------------------------
# Test 2: Invalid or missing boundary solution is rejected with ValueError.
# ---------------------------------------------------------------------------

def test_2_invalid_boundary_solution_rejected(observer_scaffold, reconstruction_scaffold):
    """Non-RegularizedSolvePrototype boundary solution raises controlled ValueError."""
    with pytest.raises(ValueError, match="RegularizedSolvePrototype"):
        build_reconstruction_gate_request(
            {"not": "a package"}, observer_scaffold, reconstruction_scaffold
        )
    with pytest.raises(ValueError, match="RegularizedSolvePrototype"):
        build_reconstruction_gate_request(
            None, observer_scaffold, reconstruction_scaffold
        )


# ---------------------------------------------------------------------------
# Test 3: Invalid or missing observer scaffold is rejected with ValueError.
# ---------------------------------------------------------------------------

def test_3_invalid_observer_scaffold_rejected(boundary_solution, reconstruction_scaffold):
    """Non-ExteriorObserverScaffold observer scaffold raises controlled ValueError."""
    with pytest.raises(ValueError, match="ExteriorObserverScaffold"):
        build_reconstruction_gate_request(
            boundary_solution, "not a scaffold", reconstruction_scaffold
        )
    with pytest.raises(ValueError, match="ExteriorObserverScaffold"):
        build_reconstruction_gate_request(
            boundary_solution, 42, reconstruction_scaffold
        )


# ---------------------------------------------------------------------------
# Test 4: Invalid or missing reconstruction scaffold is rejected with ValueError.
# ---------------------------------------------------------------------------

def test_4_invalid_reconstruction_scaffold_rejected(boundary_solution, observer_scaffold):
    """Non-ObserverReconstructionScaffold raises controlled ValueError."""
    with pytest.raises(ValueError, match="ObserverReconstructionScaffold"):
        build_reconstruction_gate_request(
            boundary_solution, observer_scaffold, {"not": "a scaffold"}
        )
    with pytest.raises(ValueError, match="ObserverReconstructionScaffold"):
        build_reconstruction_gate_request(
            boundary_solution, observer_scaffold, None
        )


# ---------------------------------------------------------------------------
# Test 5: request_validated=True only for valid requests; False inputs block it.
# ---------------------------------------------------------------------------

def test_5_request_validated_only_for_valid_inputs(boundary_solution, observer_scaffold,
                                                   reconstruction_scaffold):
    """request_validated=True appears only after full structural validation."""
    # Valid path
    request = build_reconstruction_gate_request(
        boundary_solution, observer_scaffold, reconstruction_scaffold
    )
    assert request.request_validated is True

    # Inconsistent observer positions must raise before request_validated is set
    mismatched_scaffold = ObserverReconstructionScaffold(
        _Pts([(5.0, 0.0, 0.0)]),           # different positions from observer_scaffold
        {"boundary_data_present": True},
    )
    with pytest.raises(ValueError, match="inconsistent"):
        build_reconstruction_gate_request(
            boundary_solution, observer_scaffold, mismatched_scaffold
        )


# ---------------------------------------------------------------------------
# Test 6: Execution is gated; physical reconstruction is not performed.
# ---------------------------------------------------------------------------

def test_6_execution_gated_no_physical_reconstruction(gate_result):
    """Result states execution_gated=True and physical_reconstruction_performed=False."""
    assert gate_result.execution_gated is True
    assert gate_result.physical_reconstruction_performed is False
    assert gate_result.physical_h_matrix_assembled is False


# ---------------------------------------------------------------------------
# Test 7: Result exposes the three required pressure field keys.
# ---------------------------------------------------------------------------

def test_7_result_exposes_three_pressure_fields(gate_result):
    """Result carries reconstructed_incident/scattered/total_pressure attributes."""
    assert hasattr(gate_result, "reconstructed_incident_pressure")
    assert hasattr(gate_result, "reconstructed_scattered_pressure")
    assert hasattr(gate_result, "reconstructed_total_pressure")
    # Lengths match observer count
    n = len(_OBSERVER_POSITIONS)
    assert len(gate_result.reconstructed_incident_pressure) == n
    assert len(gate_result.reconstructed_scattered_pressure) == n
    assert len(gate_result.reconstructed_total_pressure) == n


# ---------------------------------------------------------------------------
# Test 8: Pressure arrays are deterministic non-physical placeholders (zero).
# ---------------------------------------------------------------------------

def test_8_pressure_arrays_are_non_physical_placeholders(gate_result):
    """All pressure placeholders are zero complex, explicitly non-physical."""
    assert gate_result.non_physical is True
    for val in gate_result.reconstructed_incident_pressure:
        assert val == 0j
    for val in gate_result.reconstructed_scattered_pressure:
        assert val == 0j
    for val in gate_result.reconstructed_total_pressure:
        assert val == 0j


# ---------------------------------------------------------------------------
# Test 9: Metadata states no H matrix, no singular quadrature, no analytical
#          comparison, no tolerance policy.
# ---------------------------------------------------------------------------

def test_9_metadata_no_physical_capabilities(gate_result):
    """Metadata fields correctly report all gated/absent capabilities."""
    assert gate_result.reconstruction_stage == "bem005b_reconstruction_execution_gate"
    assert gate_result.benchmark_id == SUPPORTED_ID
    assert gate_result.analytical_reference_comparison_performed is False
    assert gate_result.tolerance_policy_applied is False
    assert gate_result.singular_quadrature_implemented is False
    assert gate_result.spl_computed is False
    assert gate_result.directivity_computed is False
    assert gate_result.impedance_computed is False
    assert gate_result.non_physical is True


# ---------------------------------------------------------------------------
# Test 10: Deterministic package ID is SHA-256-like, stable, changes on
#           different inputs.
# ---------------------------------------------------------------------------

def test_10_deterministic_package_id(sphere_fixture, boundary_solution,
                                     observer_scaffold, reconstruction_scaffold):
    """Package ID is 64-char hex SHA-256, stable for same inputs, different for changed inputs."""
    req1 = build_reconstruction_gate_request(
        boundary_solution, observer_scaffold, reconstruction_scaffold
    )
    result1 = execute_reconstruction_gate(req1)
    result2 = execute_reconstruction_gate(req1)

    pid = result1.deterministic_package_id
    assert isinstance(pid, str)
    assert len(pid) == 64
    assert all(c in "0123456789abcdef" for c in pid)

    # Stable for identical inputs
    assert pid == result2.deterministic_package_id

    # Changes when observer positions change
    alt_positions = [(3.0, 0.0, 0.0), (0.0, 3.0, 0.0), (0.0, 0.0, 3.0)]
    alt_obs_scaffold = build_exterior_observer_scaffold(SUPPORTED_ID, SPHERE_RADIUS, alt_positions)
    alt_rec_scaffold = ObserverReconstructionScaffold(
        _Pts(alt_positions),
        {"boundary_data_present": True, "stage": "bem004c_stub"},
    )
    req_alt = build_reconstruction_gate_request(
        boundary_solution, alt_obs_scaffold, alt_rec_scaffold
    )
    result_alt = execute_reconstruction_gate(req_alt)
    assert result_alt.deterministic_package_id != pid
