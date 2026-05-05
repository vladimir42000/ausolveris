"""
BEM-006A: Regular exterior observer H-matrix prototype tests.
Exactly 10 tests as required by the handover document.
"""

import cmath
import pytest

from ausolveris.geometry.benchmark import build_rigid_sphere_benchmark_fixture
from ausolveris.geometry.bem import (
    build_exterior_observer_scaffold,
    ExteriorObserverScaffold,
    HMatrixPrototype,
    assemble_regular_h_matrix_prototype,
    helmholtz_green_function,
)

SUPPORTED_ID = "ben004_rigid_sphere_scattering_registered"
SPHERE_RADIUS = 1.0
K = 2.0
_OBSERVER_POSITIONS = [(2.0, 0.0, 0.0), (0.0, 2.0, 0.0), (0.0, 0.0, 2.0)]
_SELECTED = [0, 2, 4]


# ---------------------------------------------------------------------------
# Module-scoped fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def sphere_fixture():
    return build_rigid_sphere_benchmark_fixture(SUPPORTED_ID, subdivision_level=1)


@pytest.fixture(scope="module")
def observer_scaffold():
    return build_exterior_observer_scaffold(SUPPORTED_ID, SPHERE_RADIUS, _OBSERVER_POSITIONS)


@pytest.fixture(scope="module")
def h_proto(sphere_fixture, observer_scaffold):
    return assemble_regular_h_matrix_prototype(
        sphere_fixture, _SELECTED, observer_scaffold, K
    )


# ---------------------------------------------------------------------------
# Test 1: Valid inputs are accepted; returns HMatrixPrototype.
# ---------------------------------------------------------------------------

def test_1_valid_inputs_accepted(sphere_fixture, observer_scaffold):
    """Valid fixture, observer scaffold, panel subset, and wavenumber are accepted."""
    proto = assemble_regular_h_matrix_prototype(
        sphere_fixture, _SELECTED, observer_scaffold, K
    )
    assert isinstance(proto, HMatrixPrototype)
    assert proto.benchmark_id == SUPPORTED_ID


# ---------------------------------------------------------------------------
# Test 2: Invalid observer scaffold is rejected with controlled ValueError.
# ---------------------------------------------------------------------------

def test_2_invalid_observer_scaffold_rejected(sphere_fixture):
    """Non-ExteriorObserverScaffold raises controlled ValueError."""
    with pytest.raises(ValueError, match="ExteriorObserverScaffold"):
        assemble_regular_h_matrix_prototype(
            sphere_fixture, _SELECTED, "not a scaffold", K
        )
    with pytest.raises(ValueError, match="ExteriorObserverScaffold"):
        assemble_regular_h_matrix_prototype(
            sphere_fixture, _SELECTED, None, K
        )


# ---------------------------------------------------------------------------
# Test 3: Panel subset count outside 3–6 is rejected with controlled ValueError.
# ---------------------------------------------------------------------------

def test_3_invalid_panel_count_rejected(sphere_fixture, observer_scaffold):
    """Panel subsets with fewer than 3 or more than 6 indices raise ValueError."""
    with pytest.raises(ValueError, match="3 to 6"):
        assemble_regular_h_matrix_prototype(
            sphere_fixture, [0, 1], observer_scaffold, K
        )
    with pytest.raises(ValueError, match="3 to 6"):
        assemble_regular_h_matrix_prototype(
            sphere_fixture, [0, 1, 2, 3, 4, 5, 6], observer_scaffold, K
        )


# ---------------------------------------------------------------------------
# Test 4: H-matrix dimensions match observer_count × panel_count.
# ---------------------------------------------------------------------------

def test_4_h_matrix_dimensions(h_proto):
    """H-matrix is observer_count rows × panel_count columns."""
    n_obs = h_proto.observer_count
    n_pan = h_proto.panel_count
    assert n_obs == len(_OBSERVER_POSITIONS)
    assert n_pan == len(_SELECTED)
    assert len(h_proto.h_matrix) == n_obs
    for row in h_proto.h_matrix:
        assert len(row) == n_pan


# ---------------------------------------------------------------------------
# Test 5: H-matrix entries are deterministic complex values matching the
#          single-layer kernel G(r,k)*area.
# ---------------------------------------------------------------------------

def test_5_h_matrix_entries_deterministic(h_proto, sphere_fixture, observer_scaffold):
    """Each H[i,j] == G(|x_obs_i - centroid_j|, k) * area_j (BEM-003 kernel)."""
    sorted_idx = sorted(_SELECTED)
    for i, obs in enumerate(observer_scaffold.observer_positions):
        for j, pidx in enumerate(sorted_idx):
            panel = sphere_fixture.panels[pidx]
            cx, cy, cz = panel.centroid
            ox, oy, oz = obs
            r = ((ox-cx)**2 + (oy-cy)**2 + (oz-cz)**2) ** 0.5
            expected = helmholtz_green_function(r, K) * panel.area
            assert abs(h_proto.h_matrix[i][j] - expected) < 1e-14


# ---------------------------------------------------------------------------
# Test 6: Package ID is SHA-256-like and stable for identical inputs.
# ---------------------------------------------------------------------------

def test_6_package_id_stable(sphere_fixture, observer_scaffold):
    """Package ID is 64-char hex and identical across two identical calls."""
    p1 = assemble_regular_h_matrix_prototype(
        sphere_fixture, _SELECTED, observer_scaffold, K
    )
    p2 = assemble_regular_h_matrix_prototype(
        sphere_fixture, _SELECTED, observer_scaffold, K
    )
    pid = p1.deterministic_package_id
    assert isinstance(pid, str)
    assert len(pid) == 64
    assert all(c in "0123456789abcdef" for c in pid)
    assert pid == p2.deterministic_package_id


# ---------------------------------------------------------------------------
# Test 7: Package ID changes when assembly inputs change.
# ---------------------------------------------------------------------------

def test_7_package_id_changes_with_different_inputs(sphere_fixture, observer_scaffold):
    """Different wavenumber produces a different package ID."""
    p1 = assemble_regular_h_matrix_prototype(
        sphere_fixture, _SELECTED, observer_scaffold, K
    )
    p2 = assemble_regular_h_matrix_prototype(
        sphere_fixture, _SELECTED, observer_scaffold, K * 2.0
    )
    assert p1.deterministic_package_id != p2.deterministic_package_id

    # Different observer positions also change the ID
    alt_obs = build_exterior_observer_scaffold(
        SUPPORTED_ID, SPHERE_RADIUS, [(3.0, 0.0, 0.0), (0.0, 3.0, 0.0), (0.0, 0.0, 3.0)]
    )
    p3 = assemble_regular_h_matrix_prototype(
        sphere_fixture, _SELECTED, alt_obs, K
    )
    assert p1.deterministic_package_id != p3.deterministic_package_id


# ---------------------------------------------------------------------------
# Test 8: physical_h_matrix_assembled=True; singular_quadrature_implemented=False.
# ---------------------------------------------------------------------------

def test_8_physical_assembled_singular_gated(h_proto):
    """Package correctly reports H assembled but singular quadrature absent."""
    assert h_proto.physical_h_matrix_assembled is True
    assert h_proto.singular_quadrature_implemented is False
    assert h_proto.matrix_stage == "bem006a_regular_h_matrix_prototype"


# ---------------------------------------------------------------------------
# Test 9: reconstruction_performed, analytical_reference_comparison, and
#          tolerance_policy all False.
# ---------------------------------------------------------------------------

def test_9_no_reconstruction_no_comparison_no_tolerance(h_proto):
    """No reconstruction, no analytical comparison, no tolerance policy applied."""
    assert h_proto.reconstruction_performed is False
    assert h_proto.analytical_reference_comparison_performed is False
    assert h_proto.tolerance_policy_applied is False


# ---------------------------------------------------------------------------
# Test 10: No SPL/directivity/impedance; result is explicitly non_physical.
# ---------------------------------------------------------------------------

def test_10_no_spl_directivity_impedance_non_physical(h_proto):
    """Output carries no derived acoustic quantities and is marked non_physical."""
    assert h_proto.spl_computed is False
    assert h_proto.directivity_computed is False
    assert h_proto.impedance_computed is False
    assert h_proto.non_physical is True
