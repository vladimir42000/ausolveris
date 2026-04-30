"""BEM‑003 acceptance tests: non‑singular operator prototype assembly."""

import math
import pytest

from ausolveris.geometry.benchmark import build_rigid_sphere_benchmark_fixture
from ausolveris.geometry.bem import (
    assemble_non_singular_prototype_operator,
    NonSingularOperatorPrototype,
    helmholtz_green_function,
)


SUPPORTED_ID = "ben004_rigid_sphere_scattering_registered"


@pytest.fixture(scope="module")
def sphere_fixture():
    return build_rigid_sphere_benchmark_fixture(SUPPORTED_ID, subdivision_level=1)


def test_green_function_reuse_in_off_diagonal_entry(sphere_fixture):
    indices = [0, 1, 2]
    k = 10.0
    op = assemble_non_singular_prototype_operator(sphere_fixture, indices, k)
    # Manually compute A_01 using helmholtz_green_function
    r = math.dist(
        sphere_fixture.panels[0].centroid,
        sphere_fixture.panels[1].centroid,
    )
    expected = helmholtz_green_function(r, k) * sphere_fixture.panels[1].area
    assert op.matrix[0][1] == expected


def test_controlled_subset_size_accepted(sphere_fixture):
    valid_sizes = [3, 4, 5, 6]
    for size in valid_sizes:
        op = assemble_non_singular_prototype_operator(
            sphere_fixture, list(range(size)), 1.0
        )
        assert len(op.matrix) == size

    # Too few / too many
    with pytest.raises(ValueError, match="3 to 6"):
        assemble_non_singular_prototype_operator(sphere_fixture, [0, 1], 1.0)
    with pytest.raises(ValueError, match="3 to 6"):
        assemble_non_singular_prototype_operator(
            sphere_fixture, [0, 1, 2, 3, 4, 5, 6], 1.0
        )


def test_panel_subset_extraction_deterministic(sphere_fixture):
    indices = [2, 5, 3, 1]  # unsorted
    op1 = assemble_non_singular_prototype_operator(sphere_fixture, indices, 1.0)
    op2 = assemble_non_singular_prototype_operator(sphere_fixture, indices, 1.0)
    assert op1.matrix == op2.matrix
    assert op1.deterministic_package_id == op2.deterministic_package_id


def test_self_interaction_excluded_and_no_green_at_r0(sphere_fixture, monkeypatch):
    # Monkeypatch helmholtz_green_function to fail if called with r=0
    orig = helmholtz_green_function
    calls = []
    def mock_g(r, k):
        assert r > 0.0, "Green function called with r=0"
        calls.append((r, k))
        return orig(r, k)
    monkeypatch.setattr(
        "ausolveris.geometry.bem.helmholtz_green_function", mock_g
    )
    op = assemble_non_singular_prototype_operator(sphere_fixture, [0, 1, 2], 1.0)
    # Diagonal entries must be exactly 0j
    for i in range(len(op.matrix)):
        assert op.matrix[i][i] == 0j
    # Ensure at least one off‑diagonal call happened (so monkeypatch is active)
    assert len(calls) > 0
    assert op.self_interaction_policy == "zero_placeholder_no_self_interaction"


def test_non_singular_distance_guard(sphere_fixture):
    # With a very large min_distance the real fixture is rejected
    with pytest.raises(ValueError, match="too close"):
        assemble_non_singular_prototype_operator(
            sphere_fixture, [0, 1, 2], k_rad_m=1.0, min_distance=1e6
        )

    # A valid small min_distance works
    op = assemble_non_singular_prototype_operator(
        sphere_fixture, [0, 1, 2], k_rad_m=1.0, min_distance=1e-12
    )
    assert len(op.matrix) == 3


def test_operator_matrix_shape(sphere_fixture):
    for size in [3, 4, 5, 6]:
        op = assemble_non_singular_prototype_operator(
            sphere_fixture, list(range(size)), 0.0
        )
        assert len(op.matrix) == size
        assert all(len(row) == size for row in op.matrix)


def test_kernel_symmetry(sphere_fixture):
    """A_ij / area_j == A_ji / area_i for i != j."""
    indices = [0, 2, 4, 5]  # 4 panels
    areas = [sphere_fixture.panels[i].area for i in indices]
    k = 10.0
    op = assemble_non_singular_prototype_operator(sphere_fixture, indices, k)
    n = len(indices)
    for i in range(n):
        for j in range(n):
            if i == j:
                continue
            left = op.matrix[i][j] / areas[j]
            right = op.matrix[j][i] / areas[i]
            assert math.isclose(abs(left - right), 0.0, rel_tol=1e-14)


def test_diagonal_policy_deterministic(sphere_fixture):
    op = assemble_non_singular_prototype_operator(sphere_fixture, [0, 1, 2], 5.0)
    for i in range(3):
        assert op.matrix[i][i] == 0j
    assert op.self_interaction_policy == "zero_placeholder_no_self_interaction"


def test_package_id_stable(sphere_fixture):
    indices = [1, 3, 5]
    k = 8.0
    id1 = assemble_non_singular_prototype_operator(sphere_fixture, indices, k
        ).deterministic_package_id
    id2 = assemble_non_singular_prototype_operator(sphere_fixture, indices, k
        ).deterministic_package_id
    assert id1 == id2
    # Different k gives different id
    id3 = assemble_non_singular_prototype_operator(sphere_fixture, indices, 9.0
        ).deterministic_package_id
    assert id1 != id3


def test_metadata_states_no_singular_no_scattering(sphere_fixture):
    op = assemble_non_singular_prototype_operator(sphere_fixture, [0, 1, 2], 0.0)
    assert op.assembly_stage == "bem003_non_singular_operator_prototype"
    assert op.benchmark_id == SUPPORTED_ID
    assert op.non_singular_only is True
    assert op.singular_terms_included is False
    assert op.scattering_solve_performed is False
    assert op.boundary_condition_enforced is False
    assert op.full_bem_solver is False
    assert op.spl_computed is False
    assert op.impedance_computed is False