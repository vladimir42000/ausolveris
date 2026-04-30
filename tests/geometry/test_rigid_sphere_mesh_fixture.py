"""BEM‑002 acceptance tests – rigid‑sphere benchmark mesh fixture."""

import pytest
from ausolveris.geometry.benchmark import (
    build_rigid_sphere_benchmark_fixture,
    validate_rigid_sphere_mesh_fixture,
    RigidSphereMeshFixture,
)

SUPPORTED_ID = "ben004_rigid_sphere_scattering_registered"


def test_benchmark_id_accepted():
    fixture = build_rigid_sphere_benchmark_fixture(SUPPORTED_ID)
    assert fixture.benchmark_id == SUPPORTED_ID


def test_unsupported_benchmark_id_rejected():
    with pytest.raises(ValueError, match="Unsupported benchmark_id"):
        build_rigid_sphere_benchmark_fixture("ben999_invalid")


def test_sphere_metadata_valid():
    fixture = build_rigid_sphere_benchmark_fixture(SUPPORTED_ID)
    assert fixture.sphere_radius == 1.0
    assert fixture.sphere_center == (0.0, 0.0, 0.0)
    assert fixture.benchmark_id == SUPPORTED_ID


def test_mesh_triangular_and_stable_count():
    fixture = build_rigid_sphere_benchmark_fixture(SUPPORTED_ID, subdivision_level=1)
    assert len(fixture.panels) == 80  # 20 * 4^1
    for p in fixture.panels:
        assert len(p.vertex_indices) == 3


def test_mesh_closed():
    fixture = build_rigid_sphere_benchmark_fixture(SUPPORTED_ID)
    errors = validate_rigid_sphere_mesh_fixture(fixture)
    # closure error must not appear
    closure_errors = [e for e in errors if "non‑manifold" in e.lower()]
    assert not closure_errors, f"Closure errors: {closure_errors}"
    assert not any("not closed" in e for e in errors)


def test_no_duplicate_vertices_and_non_degenerate():
    fixture = build_rigid_sphere_benchmark_fixture(SUPPORTED_ID)
    # duplicate vertices
    vertex_set = set(fixture.vertices)
    assert len(vertex_set) == len(fixture.vertices), "Duplicate vertices found"
    # degenerate check is in validation
    errors = validate_rigid_sphere_mesh_fixture(fixture)
    assert not any("degenerate" in e.lower() for e in errors)


def test_panel_areas_positive():
    fixture = build_rigid_sphere_benchmark_fixture(SUPPORTED_ID)
    for p in fixture.panels:
        assert p.area > 0.0


def test_normals_outward():
    fixture = build_rigid_sphere_benchmark_fixture(SUPPORTED_ID)
    errors = validate_rigid_sphere_mesh_fixture(fixture)
    inward = [e for e in errors if "inward" in e.lower()]
    assert not inward, f"Inward normals: {inward}"
    assert fixture.normal_convention == "outward_to_exterior_acoustic_domain"


def test_determinism():
    f1 = build_rigid_sphere_benchmark_fixture(SUPPORTED_ID)
    f2 = build_rigid_sphere_benchmark_fixture(SUPPORTED_ID)
    # Same fixture hash
    assert f1.fixture_hash == f2.fixture_hash
    # Same vertex list
    assert f1.vertices == f2.vertices
    # Same panel order (compare vertex_indices)
    assert [p.vertex_indices for p in f1.panels] == [p.vertex_indices for p in f2.panels]


def test_fixture_metadata_no_solve():
    fixture = build_rigid_sphere_benchmark_fixture(SUPPORTED_ID)
    assert fixture.execution_status == "registered_not_executed"
    assert fixture.scattering_solve_performed is False
    assert fixture.bem_operator_assembled is False
    assert fixture.normal_convention == "outward_to_exterior_acoustic_domain"


def test_validation_passes_on_good_fixture():
    fixture = build_rigid_sphere_benchmark_fixture(SUPPORTED_ID)
    errors = validate_rigid_sphere_mesh_fixture(fixture)
    assert not errors, f"Unexpected validation errors: {errors}"