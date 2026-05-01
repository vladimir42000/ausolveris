"""BEM‑004D acceptance tests – prototype residual report (no analytical reference)."""

import math
import pytest

from ausolveris.geometry.benchmark import build_rigid_sphere_benchmark_fixture
from ausolveris.geometry.bem import (
    assemble_non_singular_prototype_operator,
    assemble_boundary_rhs,
    regularized_solve_prototype,
    compute_prototype_residual,
    PrototypeResidualReport,
    NonSingularOperatorPrototype,
    BoundaryRHSPackage,
    RegularizedSolvePrototype,
)

SUPPORTED_ID = "ben004_rigid_sphere_scattering_registered"


@pytest.fixture(scope="module")
def sphere_fixture():
    return build_rigid_sphere_benchmark_fixture(SUPPORTED_ID, subdivision_level=1)


def _make_full_pipeline(fixture, indices, k=2.0):
    """Build operator, RHS, solve, return all three."""
    op = assemble_non_singular_prototype_operator(fixture, indices, k)
    rhs = assemble_boundary_rhs(fixture, k, 1.0+0j, (0, 0, 1), indices)
    sol = regularized_solve_prototype(op, rhs, epsilon=1.0e-6)
    return op, rhs, sol


def test_produces_residual_package(sphere_fixture):
    op, rhs, sol = _make_full_pipeline(sphere_fixture, [0, 2, 4])
    report = compute_prototype_residual(sol, op, rhs)
    assert isinstance(report, PrototypeResidualReport)
    assert report.report_stage == "bem004d_prototype_residual_report"
    assert report.benchmark_id == SUPPORTED_ID


def test_residual_vector_matches_Ax_minus_b(sphere_fixture):
    indices = [1, 3, 5]
    k = 3.0
    op, rhs, sol = _make_full_pipeline(sphere_fixture, indices, k)
    report = compute_prototype_residual(sol, op, rhs)
    # reconstruct A_reg and compute residual manually
    A = [row[:] for row in op.matrix]
    eps = sol.regularization_epsilon
    for i in range(len(indices)):
        A[i][i] += eps
    x = sol.solution
    manual_r = []
    for i in range(len(indices)):
        s = sum(A[i][j] * x[j] for j in range(len(indices)))
        manual_r.append(s - rhs.rhs_values[i])
    # compare
    for i, (a, b) in enumerate(zip(report.residual_vector, manual_r)):
        assert abs(a - b) < 1e-12, f"mismatch at {i}"


def test_max_abs_residual_correct(sphere_fixture):
    op, rhs, sol = _make_full_pipeline(sphere_fixture, [0, 1, 2, 3])
    report = compute_prototype_residual(sol, op, rhs)
    expected_max = max(abs(v) for v in report.residual_vector)
    assert abs(report.max_abs_residual - expected_max) < 1e-15


def test_relative_l2_residual_correct(sphere_fixture):
    op, rhs, sol = _make_full_pipeline(sphere_fixture, [0, 1, 2])
    report = compute_prototype_residual(sol, op, rhs)
    r = report.residual_vector
    res_l2 = math.sqrt(sum(abs(v)**2 for v in r))
    rhs_l2 = math.sqrt(sum(abs(v)**2 for v in rhs.rhs_values))
    expected_rel = res_l2 / rhs_l2 if rhs_l2 != 0 else 0.0
    assert abs(report.relative_l2_residual - expected_rel) < 1e-15


def test_deterministic_report_id(sphere_fixture):
    indices = [2, 4, 5]
    op, rhs, sol = _make_full_pipeline(sphere_fixture, indices)
    id1 = compute_prototype_residual(sol, op, rhs).deterministic_package_id
    id2 = compute_prototype_residual(sol, op, rhs).deterministic_package_id
    assert id1 == id2


def test_tolerance_split_markers(sphere_fixture):
    op, rhs, sol = _make_full_pipeline(sphere_fixture, [0, 1, 2])
    report = compute_prototype_residual(sol, op, rhs)
    assert report.residual_tolerance_applied is True
    assert report.analytical_reference_comparison_performed is False
    assert report.pressure_tolerance_applied is False


def test_no_scattering_or_reference_markers(sphere_fixture):
    op, rhs, sol = _make_full_pipeline(sphere_fixture, [0, 1, 2])
    report = compute_prototype_residual(sol, op, rhs)
    assert report.scattered_pressure_computed is False
    assert report.observer_pressure_computed is False
    assert report.analytical_pressure_evaluated is False
    assert report.reference_matching_performed is False
    assert report.spl_computed is False
    assert report.directivity_computed is False
    assert report.impedance_computed is False


def test_rejects_wrong_benchmark():
    # create a fake solve package with wrong benchmark id
    fake_solve = RegularizedSolvePrototype(
        solve_stage="",
        benchmark_id="bem999",
        prototype_only=True,
        regularized_solve_performed=True,
        regularization_epsilon=1e-6,
        regularization_type="",
        regularization_physical=False,
        singular_integral_approximation=False,
        full_sphere_solve=False,
        boundary_integral_correctness_claim=False,
        scattered_pressure_computed=False,
        observer_pressure_computed=False,
        reference_matching_performed=False,
        tolerance_policy_applied=False,
        spl_computed=False,
        directivity_computed=False,
        impedance_computed=False,
        solution=[0j],
        deterministic_package_id="",
    )
    fake_op = NonSingularOperatorPrototype(
        matrix=[[0j]],
        selected_panel_indices=[0],
        assembly_stage="",
        benchmark_id="bem999",
        non_singular_only=True,
        singular_terms_included=False,
        self_interaction_policy="",
        scattering_solve_performed=False,
        boundary_condition_enforced=False,
        full_bem_solver=False,
        spl_computed=False,
        impedance_computed=False,
        deterministic_package_id="",
    )
    fake_rhs = BoundaryRHSPackage(
        assembly_stage="",
        benchmark_id="bem999",
        fixture_hash="",
        selected_panel_indices=[0],
        k_rad_m=1.0,
        amplitude=1.0,
        incident_direction=(0,0,1),
        rhs_values=[0j],
        sound_hard_neumann=True,
        scattering_solve_performed=False,
        bem_linear_system_solved=False,
        operator_assembled=False,
        rhs_only=True,
        deterministic_package_id="",
    )
    with pytest.raises(ValueError, match="ben004"):
        compute_prototype_residual(fake_solve, fake_op, fake_rhs)


def test_rejects_dimension_mismatch(sphere_fixture):
    # 3-panel solve, 4-panel operator
    op3, rhs3, sol3 = _make_full_pipeline(sphere_fixture, [0, 1, 2])
    op4, _, _ = _make_full_pipeline(sphere_fixture, [0, 1, 2, 3])
    with pytest.raises(ValueError):
        compute_prototype_residual(sol3, op4, rhs3)
    # 3-panel solve, 4-panel RHS
    op4b, rhs4, _ = _make_full_pipeline(sphere_fixture, [0, 1, 2, 3])
    with pytest.raises(ValueError):
        compute_prototype_residual(sol3, op4b, rhs4)


def test_residual_near_zero_for_tiny_epsilon(sphere_fixture):
    indices = [0, 2, 4]
    op, rhs, sol = _make_full_pipeline(sphere_fixture, indices, k=0.0)
    report = compute_prototype_residual(sol, op, rhs)
    # with k=0, matrix is purely real, small epsilon, residual should be very small
    assert report.max_abs_residual < 1e-12
    assert report.relative_l2_residual < 1e-12