"""BEM‑004B acceptance tests – sound‑hard Neumann RHS assembly (no solve)."""

import math
import pytest

from ausolveris.geometry.benchmark import build_rigid_sphere_benchmark_fixture
from ausolveris.geometry.bem import (
    assemble_boundary_rhs,
    BoundaryRHSPackage,
    build_incident_field_reference_scaffold,
)

SUPPORTED_ID = "ben004_rigid_sphere_scattering_registered"


@pytest.fixture(scope="module")
def sphere_fixture():
    """Return the standard BEN‑004 rigid‑sphere mesh fixture (one level subdivision)."""
    return build_rigid_sphere_benchmark_fixture(SUPPORTED_ID, subdivision_level=1)


def test_rhs_matches_expected_neumann_minus_dpdn(sphere_fixture):
    """RHS vector equals -∂p_inc/∂n, matching the BEM‑004A scaffold."""
    indices = [0, 3, 5]
    k = 2.0
    amp = 1.0 + 0j
    d = (0.0, 0.0, 1.0)
    pkg = assemble_boundary_rhs(sphere_fixture, k, amp, d, indices)
    scaffold = build_incident_field_reference_scaffold(sphere_fixture, k, amp, d, indices)
    for i, idx in enumerate(indices):
        expected = -scaffold.incident_normal_derivative[i]
        assert abs(pkg.rhs_values[i] - expected) < 1e-12


def test_selected_indices_are_valid(sphere_fixture):
    """Only valid panel indices are accepted."""
    # negative index
    with pytest.raises(ValueError):
        assemble_boundary_rhs(sphere_fixture, 1.0, 1.0, (0, 0, 1), [-1])
    # out‑of‑range
    with pytest.raises(ValueError):
        assemble_boundary_rhs(sphere_fixture, 1.0, 1.0, (0, 0, 1), [len(sphere_fixture.panels)])
    # empty list
    with pytest.raises(ValueError):
        assemble_boundary_rhs(sphere_fixture, 1.0, 1.0, (0, 0, 1), [])


def test_deterministic_package_id(sphere_fixture):
    """Package ID is stable across repeated calls."""
    args = (sphere_fixture, 4.567, 1.23 + 0.456j, (1, 0, 0), [2, 4, 6])
    id1 = assemble_boundary_rhs(*args).deterministic_package_id
    id2 = assemble_boundary_rhs(*args).deterministic_package_id
    assert id1 == id2


def test_different_k_produces_different_id(sphere_fixture):
    """Changing wavenumber changes the package ID."""
    id1 = assemble_boundary_rhs(sphere_fixture, 1.0, 1.0, (0, 0, 1), [0, 1, 2]
        ).deterministic_package_id
    id2 = assemble_boundary_rhs(sphere_fixture, 2.0, 1.0, (0, 0, 1), [0, 1, 2]
        ).deterministic_package_id
    assert id1 != id2


def test_package_metadata_no_solve(sphere_fixture):
    """All metadata flags confirm that no solve was performed."""
    pkg = assemble_boundary_rhs(sphere_fixture, 1.0, 1.0, (0, 0, 1), [0, 1, 2])
    assert pkg.assembly_stage == "bem004b_boundary_rhs_assembly_no_solve"
    assert pkg.benchmark_id == SUPPORTED_ID
    assert pkg.sound_hard_neumann is True
    assert pkg.scattering_solve_performed is False
    assert pkg.bem_linear_system_solved is False
    assert pkg.operator_assembled is False
    assert pkg.rhs_only is True


def test_fixture_hash_preserved(sphere_fixture):
    """The fixture object is not modified by RHS assembly."""
    original_hash = sphere_fixture.fixture_hash
    _ = assemble_boundary_rhs(sphere_fixture, 1.0, 1.0, (0, 0, 1), [0, 1, 2])
    assert sphere_fixture.fixture_hash == original_hash


def test_rejects_unsupported_benchmark():
    """A fixture without the correct benchmark ID is rejected."""
    from ausolveris.geometry.benchmark import RigidSphereMeshFixture
    fake_fixture = RigidSphereMeshFixture(
        benchmark_id="bem999",
        sphere_radius=1.0,
        sphere_center=(0, 0, 0),
        canonical_frame_metadata={},
        vertices=[(0, 0, 0)],
        panels=[],
        fixture_hash="nohash",
        execution_status="",
        scattering_solve_performed=False,
        bem_operator_assembled=False,
        normal_convention="",
    )
    with pytest.raises(ValueError, match="ben004_rigid_sphere_scattering_registered"):
        assemble_boundary_rhs(fake_fixture, 1.0, 1.0, (0, 0, 1), [0])


def test_invalid_k_rejected(sphere_fixture):
    """Negative wavenumber is rejected."""
    with pytest.raises(ValueError):
        assemble_boundary_rhs(sphere_fixture, -1.0, 1.0, (0, 0, 1), [0])


def test_invalid_direction_rejected(sphere_fixture):
    """Zero incident direction vector is rejected."""
    with pytest.raises(ValueError, match="nonzero"):
        assemble_boundary_rhs(sphere_fixture, 1.0, 1.0, (0, 0, 0), [0])


def test_rhs_length_matches_indices(sphere_fixture):
    """The returned RHS list has one entry per selected panel."""
    indices = [0, 2, 4, 5, 7]  # 5 panels
    pkg = assemble_boundary_rhs(sphere_fixture, 1.0, 1.0, (1, 0, 0), indices)
    assert len(pkg.rhs_values) == len(indices)
