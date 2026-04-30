"""BEM‑004A acceptance tests – incident‑field and analytical‑reference scaffold."""

import math
import pytest

from ausolveris.geometry.benchmark import build_rigid_sphere_benchmark_fixture
from ausolveris.geometry.bem import (
    build_incident_field_reference_scaffold,
    IncidentFieldReferenceScaffold,
    TolerancePolicyScaffold,
)


SUPPORTED_ID = "ben004_rigid_sphere_scattering_registered"

@pytest.fixture(scope="module")
def sphere_fixture():
    return build_rigid_sphere_benchmark_fixture(SUPPORTED_ID, subdivision_level=1)


def test_incident_pressure_matches_analytic():
    fixture = build_rigid_sphere_benchmark_fixture(SUPPORTED_ID, subdivision_level=1)
    k = 2.0
    amp = 1.5 + 0j
    d = (0.0, 0.0, 1.0)  # unit vector along z
    scaffold = build_incident_field_reference_scaffold(
        fixture, k, amp, d, [0]
    )
    # p_inc(0) = A * exp(i k d·x0)
    x0 = scaffold.panel_centroids[0]
    expected = amp * complex(math.cos(k * x0[2]), math.sin(k * x0[2]))
    assert abs(scaffold.incident_pressure[0] - expected) < 1e-12


def test_incident_direction_normalized():
    fixture = build_rigid_sphere_benchmark_fixture(SUPPORTED_ID, subdivision_level=1)
    d_raw = (2.0, 2.0, 2.0)   # not unit length
    scaffold = build_incident_field_reference_scaffold(
        fixture, 1.0, 1.0+0j, d_raw, [0]
    )
    d_stored = scaffold.incident_direction
    norm = math.sqrt(d_stored[0]**2 + d_stored[1]**2 + d_stored[2]**2)
    assert math.isclose(norm, 1.0)
    # Check it's a scaled version of original
    assert d_stored[0] > 0 and d_stored[1] > 0 and d_stored[2] > 0


def test_incident_normal_derivative():
    fixture = build_rigid_sphere_benchmark_fixture(SUPPORTED_ID, subdivision_level=1)
    # pick a panel whose normal is easy: top face? We'll use the fixture after subdivision,
    # but normals are already outward from sphere. We'll just test that the formula holds.
    k = 3.0
    amp = 1.0
    d = (0.0, 0.0, 1.0)
    scaffold = build_incident_field_reference_scaffold(
        fixture, k, amp, d, [0, 5, 10]
    )
    for i in range(len(scaffold.selected_panel_indices)):
        n = scaffold.panel_normals[i]
        p = scaffold.incident_pressure[i]
        manual_dp = 1j * k * (d[0]*n[0] + d[1]*n[1] + d[2]*n[2]) * p
        diff = abs(scaffold.incident_normal_derivative[i] - manual_dp)
        assert diff < 1e-12


def test_neumann_rhs_scaffold():
    fixture = build_rigid_sphere_benchmark_fixture(SUPPORTED_ID)
    scaffold = build_incident_field_reference_scaffold(
        fixture, 2.0, 1.0, (0,0,1), [0,1,2]
    )
    for i in range(3):
        assert scaffold.neumann_rhs_scaffold[i] == -scaffold.incident_normal_derivative[i]


def test_consumes_fixture_without_modifying():
    fixture = build_rigid_sphere_benchmark_fixture(SUPPORTED_ID)
    org_hash = fixture.fixture_hash
    org_panel_count = len(fixture.panels)
    _ = build_incident_field_reference_scaffold(
        fixture, 1.0, 1.0, (1,0,0), [0, 3, 5]
    )
    # fixture must be unchanged
    assert fixture.fixture_hash == org_hash
    assert len(fixture.panels) == org_panel_count


def test_unsupported_benchmark_rejected():
    from ausolveris.geometry.benchmark import RigidSphereMeshFixture
    fake_fixture = RigidSphereMeshFixture(
        benchmark_id="bem999",
        sphere_radius=1.0,
        sphere_center=(0,0,0),
        canonical_frame_metadata={},
        vertices=[(0,0,0)],
        panels=[],
        fixture_hash="nohash",
        execution_status="",
        scattering_solve_performed=False,
        bem_operator_assembled=False,
        normal_convention="",
    )
    with pytest.raises(ValueError, match="ben004_rigid_sphere_scattering_registered"):
        build_incident_field_reference_scaffold(
            fake_fixture, 1.0, 1.0, (0,0,1), [0]
        )


def test_invalid_k_or_direction_rejected():
    fixture = build_rigid_sphere_benchmark_fixture(SUPPORTED_ID)
    # negative k
    with pytest.raises(ValueError):
        build_incident_field_reference_scaffold(fixture, -1.0, 1.0, (0,0,1), [0])
    # zero direction vector (after normalization)
    with pytest.raises(ValueError, match="nonzero"):
        build_incident_field_reference_scaffold(fixture, 1.0, 1.0, (0,0,0), [0])


def test_deterministic_package_id():
    fixture = build_rigid_sphere_benchmark_fixture(SUPPORTED_ID)
    kwargs = dict(
        fixture=fixture,
        k_rad_m=4.567,
        amplitude=1.23+0.456j,
        incident_direction=(1, 0, 0),
        selected_indices=[2, 4, 6]
    )
    id1 = build_incident_field_reference_scaffold(**kwargs).deterministic_package_id
    id2 = build_incident_field_reference_scaffold(**kwargs).deterministic_package_id
    assert id1 == id2


def test_tolerance_policy_metadata():
    fixture = build_rigid_sphere_benchmark_fixture(SUPPORTED_ID)
    scaffold = build_incident_field_reference_scaffold(
        fixture, 1.0, 1.0, (0,0,1), [0,1,2]
    )
    tp = scaffold.tolerance_policy
    assert tp.policy_status == "declared_not_applied"
    assert tp.future_application_stage == "BEM-004D"
    assert tp.complex_pressure_relative_tolerance == 1.0e-2
    assert tp.complex_pressure_absolute_tolerance == 1.0e-6
    assert tp.boundary_rhs_relative_tolerance == 1.0e-12
    assert tp.boundary_rhs_absolute_tolerance == 1.0e-12
    assert "max_abs_error" in tp.comparison_norms_declared
    assert "relative_l2_error" in tp.comparison_norms_declared
    assert tp.comparison_executed == False


def test_output_markers_no_solve_or_reference():
    fixture = build_rigid_sphere_benchmark_fixture(SUPPORTED_ID)
    scaffold = build_incident_field_reference_scaffold(
        fixture, 1.0, 1.0, (0,0,1), [0,1,2]
    )
    assert scaffold.scaffold_stage == "bem004a_incident_field_reference_scaffold"
    assert scaffold.benchmark_id == SUPPORTED_ID
    assert scaffold.sound_hard_neumann_convention == True
    assert scaffold.incident_field_evaluated == True
    assert scaffold.neumann_rhs_scaffolded == True
    assert scaffold.scattering_solve_performed == False
    assert scaffold.bem_linear_system_solved == False
    assert scaffold.analytical_reference_evaluated == False
    assert scaffold.reference_matching_performed == False
    assert scaffold.spl_computed == False
    assert scaffold.impedance_computed == False
    # Also verify that the bem module does not expose any solve/evaluator functions
    # (we can simply check for known forbidden names)
    import ausolveris.geometry.bem as bem_mod
    forbidden = [
        "solve_scattering", "assemble_full_operator", "analytical_pressure",
        "compare_reference", "compute_spl"
    ]
    for name in forbidden:
        assert not hasattr(bem_mod, name), f"Forbidden name {name} found in bem module"