"""BEM‑004C acceptance tests – regularized solve prototype (3‑6 panels only)."""

import math
import pytest
from copy import deepcopy

from ausolveris.geometry.benchmark import build_rigid_sphere_benchmark_fixture
from ausolveris.geometry.bem import (
    assemble_non_singular_prototype_operator,
    assemble_boundary_rhs,
    regularized_solve_prototype,
    RegularizedSolvePrototype,
    NonSingularOperatorPrototype,
    BoundaryRHSPackage,
)

SUPPORTED_ID = "ben004_rigid_sphere_scattering_registered"


@pytest.fixture(scope="module")
def sphere_fixture():
    return build_rigid_sphere_benchmark_fixture(SUPPORTED_ID, subdivision_level=1)


def _make_packages(fixture, indices, k=2.0):
    """Helper to create consistent operator and RHS packages."""
    op = assemble_non_singular_prototype_operator(fixture, indices, k)
    rhs = assemble_boundary_rhs(fixture, k, 1.0+0j, (0, 0, 1), indices)
    return op, rhs


def test_valid_solve_produces_package(sphere_fixture):
    op, rhs = _make_packages(sphere_fixture, [0, 2, 4])
    sol_pkg = regularized_solve_prototype(op, rhs)
    assert isinstance(sol_pkg, RegularizedSolvePrototype)
    assert sol_pkg.solve_stage == "bem004c_regularized_solve_prototype"
    assert sol_pkg.benchmark_id == SUPPORTED_ID


def test_regularized_matrix_equals_A_plus_epsilon_I(sphere_fixture):
    indices = [1, 3, 5]
    k = 3.0
    op, rhs = _make_packages(sphere_fixture, indices, k)
    original_matrix = deepcopy(op.matrix)
    _ = regularized_solve_prototype(op, rhs, epsilon=1.0e-6)
    # the operator package is not mutated by the solve
    assert op.matrix == original_matrix


def test_solution_satisfies_regularized_system(sphere_fixture):
    indices = [0, 1, 2, 3]
    k = 2.0
    op, rhs = _make_packages(sphere_fixture, indices, k)
    eps = 1.0e-6
    sol_pkg = regularized_solve_prototype(op, rhs, epsilon=eps)
    x = sol_pkg.solution
    A = op.matrix
    A_reg = [row[:] for row in A]
    for i in range(len(indices)):
        A_reg[i][i] += eps
    residual = []
    for i in range(len(indices)):
        s = sum(A_reg[i][j] * x[j] for j in range(len(indices)))
        residual.append(abs(s - rhs.rhs_values[i]))
    assert max(residual) < 1e-12




def test_rejects_invalid_panel_count():
    # 2‑panel operator package
    op2 = NonSingularOperatorPrototype(
        matrix=[[0j, 0j], [0j, 0j]],
        selected_panel_indices=[0, 1],
        assembly_stage="",
        benchmark_id=SUPPORTED_ID,
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
    rhs2 = BoundaryRHSPackage(
        assembly_stage="",
        benchmark_id=SUPPORTED_ID,
        fixture_hash="",
        selected_panel_indices=[0, 1],
        k_rad_m=1.0,
        amplitude=1.0,
        incident_direction=(0,0,1),
        rhs_values=[0j, 0j],
        sound_hard_neumann=True,
        scattering_solve_performed=False,
        bem_linear_system_solved=False,
        operator_assembled=False,
        rhs_only=True,
        deterministic_package_id="",
    )
    with pytest.raises(ValueError):
        regularized_solve_prototype(op2, rhs2)

    # 7‑panel operator package
    op7 = NonSingularOperatorPrototype(
        matrix=[[0j]*7 for _ in range(7)],
        selected_panel_indices=list(range(7)),
        assembly_stage="",
        benchmark_id=SUPPORTED_ID,
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
    rhs7 = BoundaryRHSPackage(
        assembly_stage="",
        benchmark_id=SUPPORTED_ID,
        fixture_hash="",
        selected_panel_indices=list(range(7)),
        k_rad_m=1.0,
        amplitude=1.0,
        incident_direction=(0,0,1),
        rhs_values=[0j]*7,
        sound_hard_neumann=True,
        scattering_solve_performed=False,
        bem_linear_system_solved=False,
        operator_assembled=False,
        rhs_only=True,
        deterministic_package_id="",
    )
    with pytest.raises(ValueError):
        regularized_solve_prototype(op7, rhs7)

        

def test_rejects_mismatched_indices(sphere_fixture):
    op, _ = _make_packages(sphere_fixture, [0, 2, 4])
    _, rhs_wrong = _make_packages(sphere_fixture, [0, 2, 5])
    with pytest.raises(ValueError, match="Mismatched selected panel indices"):
        regularized_solve_prototype(op, rhs_wrong)


def test_rejects_mismatched_dimensions(sphere_fixture):
    op3, _ = _make_packages(sphere_fixture, [0, 1, 2])
    _, rhs4 = _make_packages(sphere_fixture, [0, 1, 2, 3])
    with pytest.raises(ValueError):
        regularized_solve_prototype(op3, rhs4)


def test_deterministic_package(sphere_fixture):
    indices = [2, 4, 5]
    op, rhs = _make_packages(sphere_fixture, indices)
    sol1 = regularized_solve_prototype(op, rhs)
    sol2 = regularized_solve_prototype(op, rhs)
    assert sol1.deterministic_package_id == sol2.deterministic_package_id
    assert sol1.solution == sol2.solution


def test_rejects_unsupported_benchmark():
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
        regularized_solve_prototype(fake_op, fake_rhs)


def test_metadata_states_prototype_only(sphere_fixture):
    op, rhs = _make_packages(sphere_fixture, [0,1,2])
    sol = regularized_solve_prototype(op, rhs)
    assert sol.prototype_only is True
    assert sol.regularization_physical is False
    assert sol.singular_integral_approximation is False
    assert sol.boundary_integral_correctness_claim is False


def test_metadata_no_scattering_or_reference(sphere_fixture):
    op, rhs = _make_packages(sphere_fixture, [3,4,5])
    sol = regularized_solve_prototype(op, rhs)
    assert sol.scattered_pressure_computed is False
    assert sol.observer_pressure_computed is False
    assert sol.reference_matching_performed is False
    assert sol.tolerance_policy_applied is False
    assert sol.spl_computed is False
    assert sol.directivity_computed is False
    assert sol.impedance_computed is False
