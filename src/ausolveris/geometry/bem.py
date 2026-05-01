"""
BEM‑001 : Helmholtz Green‑function utility (scalar, free-space).
BEM‑003 : non‑singular operator prototype (off‑diagonal, controlled subset).
BEM‑004A : incident‑field and analytical‑reference scaffold.
BEM‑004B : sound‑hard Neumann RHS assembly, no solve.
BEM‑004C : tiny regularized linear‑solve prototype, controlled subset only.
"""

import math
import cmath
import hashlib
from dataclasses import dataclass, field
from typing import List, Tuple, Optional

from .benchmark import RigidSphereMeshFixture


# ---------------------------------------------------------------------------
# BEM‑001 : Green function and wavenumber
# ---------------------------------------------------------------------------

def helmholtz_green_function(r_m: float, k_rad_m: float) -> complex:
    """
    Evaluate the free‑space scalar Helmholtz Green function.

    Parameters
    ----------
    r_m : float
        Distance in metres. Must be finite and strictly positive.
    k_rad_m : float
        Wavenumber in rad/m. Must be finite and non‑negative.

    Returns
    -------
    complex
    """
    if not math.isfinite(r_m) or r_m <= 0.0:
        raise ValueError("r_m must be finite and strictly positive")
    if not math.isfinite(k_rad_m) or k_rad_m < 0.0:
        raise ValueError("k_rad_m must be finite and non‑negative")

    ikr = 1j * k_rad_m * r_m
    return cmath.exp(ikr) / (4.0 * math.pi * r_m)


def helmholtz_wavenumber(frequency_hz: float, sound_speed_m_s: float) -> float:
    """
    Compute the acoustic wavenumber.

    Parameters
    ----------
    frequency_hz : float
        Frequency in Hz. Must be finite and non‑negative.
    sound_speed_m_s : float
        Speed of sound in m/s. Must be finite and strictly positive.

    Returns
    -------
    float
        k = 2 * pi * f / c
    """
    if not math.isfinite(frequency_hz) or frequency_hz < 0.0:
        raise ValueError("frequency_hz must be finite and non‑negative")
    if not math.isfinite(sound_speed_m_s) or sound_speed_m_s <= 0.0:
        raise ValueError("sound_speed_m_s must be finite and strictly positive")

    return 2.0 * math.pi * frequency_hz / sound_speed_m_s


# ---------------------------------------------------------------------------
# BEM‑003 : non‑singular operator prototype
# ---------------------------------------------------------------------------

@dataclass
class NonSingularOperatorPrototype:
    """Container for a small, off‑diagonal, non‑singular interaction matrix."""
    matrix: List[List[complex]]
    selected_panel_indices: List[int]          # BEM‑004C extension (populated during assembly)
    assembly_stage: str
    benchmark_id: str
    non_singular_only: bool
    singular_terms_included: bool
    self_interaction_policy: str
    scattering_solve_performed: bool
    boundary_condition_enforced: bool
    full_bem_solver: bool
    spl_computed: bool
    impedance_computed: bool
    deterministic_package_id: str


def _distance(p: tuple, q: tuple) -> float:
    """Euclidean distance between two 3‑D points."""
    dx = p[0] - q[0]
    dy = p[1] - q[1]
    dz = p[2] - q[2]
    return math.sqrt(dx*dx + dy*dy + dz*dz)


def assemble_non_singular_prototype_operator(
    fixture: RigidSphereMeshFixture,
    selected_indices: List[int],
    k_rad_m: float,
    min_distance: float = 1e-9
) -> NonSingularOperatorPrototype:
    """
    Build a small, fully off‑diagonal interaction matrix for selected panels
    of a rigid‑sphere fixture.  Self‑interactions are excluded and singular
    self‑terms are never evaluated.

    Parameters
    ----------
    fixture : RigidSphereMeshFixture
        Must be the ben004_rigid_sphere_scattering_registered fixture.
    selected_indices : list of int
        Indices of the panels to use (3–6 unique valid indices).
    k_rad_m : float
        Wavenumber in rad/m (finite, >=0).
    min_distance : float
        Minimum allowed centroid distance between any pair of selected panels.
        Pairs closer than this threshold cause a ValueError.

    Returns
    -------
    NonSingularOperatorPrototype
    """
    # ---- input validation ----
    if fixture.benchmark_id != "ben004_rigid_sphere_scattering_registered":
        raise ValueError("Fixture must be ben004_rigid_sphere_scattering_registered")
    if not (3 <= len(selected_indices) <= 6):
        raise ValueError("selected_indices must contain 3 to 6 panels")
    if len(set(selected_indices)) != len(selected_indices):
        raise ValueError("Duplicate panel indices are not allowed")
    if not all(isinstance(idx, int) and 0 <= idx < len(fixture.panels) for idx in selected_indices):
        raise ValueError("Invalid panel index – must exist in fixture")
    if not math.isfinite(k_rad_m) or k_rad_m < 0.0:
        raise ValueError("k_rad_m must be finite and non‑negative")
    if not math.isfinite(min_distance) or min_distance < 0.0:
        raise ValueError("min_distance must be finite and non‑negative")

    n = len(selected_indices)
    centroids = [fixture.panels[idx].centroid for idx in selected_indices]
    areas = [fixture.panels[idx].area for idx in selected_indices]

    # ---- non‑singular distance guard ----
    for i in range(n):
        for j in range(i + 1, n):
            dist = _distance(centroids[i], centroids[j])
            if dist < min_distance:
                raise ValueError(
                    f"Panels {selected_indices[i]} and {selected_indices[j]} "
                    f"are too close: {dist} < {min_distance}"
                )

    # ---- assemble matrix (off‑diagonal only) ----
    matrix = [[0j] * n for _ in range(n)]
    for i in range(n):
        for j in range(n):
            if i == j:
                # self‑interaction policy: zero placeholder, no Green‑function call
                matrix[i][j] = 0j
            else:
                r = _distance(centroids[i], centroids[j])
                # Use BEM‑001 Green function
                G = helmholtz_green_function(r, k_rad_m)
                matrix[i][j] = G * areas[j]

    # ---- deterministic metadata & package ID ----
    meta_lines = []
    # sort indices for repeatable ordering
    sorted_idx = sorted(selected_indices)
    meta_lines.append(f"assembly_stage=bem003_non_singular_operator_prototype")
    meta_lines.append(f"benchmark_id={fixture.benchmark_id}")
    meta_lines.append(f"fixture_hash={fixture.fixture_hash}")
    meta_lines.append(f"k_rad_m={k_rad_m:.15e}")
    meta_lines.append(f"selected_indices={sorted_idx}")
    meta_lines.append("non_singular_only=True")
    meta_lines.append("singular_terms_included=False")
    meta_lines.append("self_interaction_policy=zero_placeholder_no_self_interaction")
    meta_lines.append("scattering_solve_performed=False")
    meta_lines.append("boundary_condition_enforced=False")
    meta_lines.append("full_bem_solver=False")
    meta_lines.append("spl_computed=False")
    meta_lines.append("impedance_computed=False")

    # include matrix entries with high precision
    for row in matrix:
        for z in row:
            meta_lines.append(f"{z.real:.15e}+{z.imag:.15e}j")

    hash_input = "\n".join(meta_lines)
    package_id = hashlib.sha256(hash_input.encode("utf-8")).hexdigest()

    return NonSingularOperatorPrototype(
        matrix=matrix,
        selected_panel_indices=sorted_idx,   # new field
        assembly_stage="bem003_non_singular_operator_prototype",
        benchmark_id=fixture.benchmark_id,
        non_singular_only=True,
        singular_terms_included=False,
        self_interaction_policy="zero_placeholder_no_self_interaction",
        scattering_solve_performed=False,
        boundary_condition_enforced=False,
        full_bem_solver=False,
        spl_computed=False,
        impedance_computed=False,
        deterministic_package_id=package_id,
    )


# ---------------------------------------------------------------------------
# BEM‑004A : incident‑field and analytical‑reference scaffold
# ---------------------------------------------------------------------------
@dataclass
class TolerancePolicyScaffold:
    """Declared tolerance policy for future reference comparison – not applied."""
    policy_status: str = "declared_not_applied"
    future_application_stage: str = "BEM-004D"
    complex_pressure_relative_tolerance: float = 1.0e-2
    complex_pressure_absolute_tolerance: float = 1.0e-6
    boundary_rhs_relative_tolerance: float = 1.0e-12
    boundary_rhs_absolute_tolerance: float = 1.0e-12
    comparison_norms_declared: List[str] = field(default_factory=lambda: [
        "max_abs_error", "relative_l2_error"
    ])
    comparison_executed: bool = False

@dataclass
class IncidentFieldReferenceScaffold:
    """BEM‑004A scaffold: incident field, Neumann RHS, tolerance policy."""
    scaffold_stage: str
    benchmark_id: str
    sound_hard_neumann_convention: bool
    incident_field_evaluated: bool
    neumann_rhs_scaffolded: bool
    scattering_solve_performed: bool
    bem_linear_system_solved: bool
    analytical_reference_evaluated: bool
    reference_matching_performed: bool
    spl_computed: bool
    impedance_computed: bool
    k_rad_m: float
    amplitude: complex
    incident_direction: Tuple[float, float, float]   # unit vector
    selected_panel_indices: List[int]
    # per‑panel data (length N)
    panel_centroids: List[Tuple[float, float, float]]
    panel_normals: List[Tuple[float, float, float]]
    incident_pressure: List[complex]          # p_inc at each centroid
    incident_normal_derivative: List[complex] # ∂p_inc/∂n
    neumann_rhs_scaffold: List[complex]       # -∂p_inc/∂n
    tolerance_policy: TolerancePolicyScaffold
    fixture_hash: str
    deterministic_package_id: str


def _dot(a: Tuple[float, float, float], b: Tuple[float, float, float]) -> float:
    return a[0]*b[0] + a[1]*b[1] + a[2]*b[2]


def _normalise_or_fail(v: Tuple[float, float, float]) -> Tuple[float, float, float]:
    norm = math.sqrt(v[0]*v[0] + v[1]*v[1] + v[2]*v[2])
    if norm == 0.0 or not math.isfinite(norm):
        raise ValueError("Incident direction must be nonzero and finite")
    return (v[0]/norm, v[1]/norm, v[2]/norm)


def build_incident_field_reference_scaffold(
    fixture: RigidSphereMeshFixture,
    k_rad_m: float,
    amplitude: complex,
    incident_direction: Tuple[float, float, float],
    selected_indices: List[int],
) -> IncidentFieldReferenceScaffold:
    """
    Create a scaffold containing incident pressure, its normal derivative, and
    the Neumann boundary‑data RHS for a selected set of panels on the rigid sphere.
    No BEM system is solved; only analytical expressions are evaluated.
    """
    if fixture.benchmark_id != "ben004_rigid_sphere_scattering_registered":
        raise ValueError("Fixture must be ben004_rigid_sphere_scattering_registered")
    if not math.isfinite(k_rad_m) or k_rad_m < 0.0:
        raise ValueError("k_rad_m must be finite and non‑negative")
    if not selected_indices:
        raise ValueError("selected_indices must not be empty")
    if len(set(selected_indices)) != len(selected_indices):
        raise ValueError("Duplicate panel indices are not allowed")
    if not all(isinstance(idx, int) and 0 <= idx < len(fixture.panels) for idx in selected_indices):
        raise ValueError("Invalid panel index – must exist in fixture")

    # Normalise incident direction
    d = _normalise_or_fail(incident_direction)

    N = len(selected_indices)
    centroids = [fixture.panels[idx].centroid for idx in selected_indices]
    normals = [fixture.panels[idx].outward_normal for idx in selected_indices]

    p_inc = []
    dpdn_inc = []
    rhs = []
    for i in range(N):
        x = centroids[i]
        n = normals[i]
        dx = _dot(d, x)
        p = amplitude * cmath.exp(1j * k_rad_m * dx)
        dp = 1j * k_rad_m * _dot(d, n) * p
        p_inc.append(p)
        dpdn_inc.append(dp)
        rhs.append(-dp)

    # ---- deterministic package ID ----
    id_lines = []
    id_lines.append(f"scaffold_stage=bem004a_incident_field_reference_scaffold")
    id_lines.append(f"benchmark_id={fixture.benchmark_id}")
    id_lines.append(f"fixture_hash={fixture.fixture_hash}")
    id_lines.append(f"k_rad_m={k_rad_m:.15e}")
    id_lines.append(f"amplitude={amplitude.real:.15e}+{amplitude.imag:.15e}j")
    id_lines.append(f"incident_direction={d[0]:.15e},{d[1]:.15e},{d[2]:.15e}")
    sorted_idx = sorted(selected_indices)
    id_lines.append(f"selected_indices={sorted_idx}")
    # include actual computed values
    for val in p_inc:
        id_lines.append(f"p_inc={val.real:.15e}+{val.imag:.15e}j")
    for val in dpdn_inc:
        id_lines.append(f"dpdn={val.real:.15e}+{val.imag:.15e}j")
    hash_input = "\n".join(id_lines)
    package_id = hashlib.sha256(hash_input.encode("utf-8")).hexdigest()

    return IncidentFieldReferenceScaffold(
        scaffold_stage="bem004a_incident_field_reference_scaffold",
        benchmark_id=fixture.benchmark_id,
        sound_hard_neumann_convention=True,
        incident_field_evaluated=True,
        neumann_rhs_scaffolded=True,
        scattering_solve_performed=False,
        bem_linear_system_solved=False,
        analytical_reference_evaluated=False,
        reference_matching_performed=False,
        spl_computed=False,
        impedance_computed=False,
        k_rad_m=k_rad_m,
        amplitude=amplitude,
        incident_direction=d,
        selected_panel_indices=sorted_idx,
        panel_centroids=centroids,
        panel_normals=normals,
        incident_pressure=p_inc,
        incident_normal_derivative=dpdn_inc,
        neumann_rhs_scaffold=rhs,
        tolerance_policy=TolerancePolicyScaffold(),
        fixture_hash=fixture.fixture_hash,
        deterministic_package_id=package_id,
    )


# ---------------------------------------------------------------------------
# BEM‑004B : sound‑hard Neumann RHS assembly, no solve
# ---------------------------------------------------------------------------
@dataclass
class BoundaryRHSPackage:
    """Deterministic package containing only the boundary RHS vector – no solve."""
    assembly_stage: str
    benchmark_id: str
    fixture_hash: str
    selected_panel_indices: List[int]
    k_rad_m: float
    amplitude: complex
    incident_direction: Tuple[float, float, float]
    rhs_values: List[complex]               # length N, deterministic order
    sound_hard_neumann: bool
    scattering_solve_performed: bool
    bem_linear_system_solved: bool
    operator_assembled: bool
    rhs_only: bool
    deterministic_package_id: str


def assemble_boundary_rhs(
    fixture: RigidSphereMeshFixture,
    k_rad_m: float,
    amplitude: complex,
    incident_direction: Tuple[float, float, float],
    selected_indices: List[int],
) -> BoundaryRHSPackage:
    """
    Build a deterministic RHS vector for the Neumann problem:
        rhs_j = -∂p_inc/∂n  (sound‑hard sphere)

    Uses the BEM‑004A scaffold internally but returns a minimal package.
    No BEM matrix, no operator application, no solve.
    """
    # Delegate incident computation to the existing scaffold (validates inputs)
    scaffold = build_incident_field_reference_scaffold(
        fixture=fixture,
        k_rad_m=k_rad_m,
        amplitude=amplitude,
        incident_direction=incident_direction,
        selected_indices=selected_indices,
    )

    rhs = scaffold.neumann_rhs_scaffold  # already computed as list

    # ---- Deterministic package ID (SHA‑256) ----
    id_lines = []
    id_lines.append("assembly_stage=bem004b_boundary_rhs_assembly_no_solve")
    id_lines.append(f"benchmark_id={fixture.benchmark_id}")
    id_lines.append(f"fixture_hash={fixture.fixture_hash}")
    id_lines.append(f"k_rad_m={k_rad_m:.15e}")
    id_lines.append(f"amplitude=({amplitude.real:.15e},{amplitude.imag:.15e})")
    id_lines.append(f"incident_direction=({incident_direction[0]:.15e},{incident_direction[1]:.15e},{incident_direction[2]:.15e})")
    sorted_idx = sorted(selected_indices)
    id_lines.append(f"selected_indices={sorted_idx}")
    for z in rhs:
        id_lines.append(f"rhs=({z.real:.15e},{z.imag:.15e})")
    hash_input = "\n".join(id_lines)
    package_id = hashlib.sha256(hash_input.encode("utf-8")).hexdigest()

    return BoundaryRHSPackage(
        assembly_stage="bem004b_boundary_rhs_assembly_no_solve",
        benchmark_id=fixture.benchmark_id,
        fixture_hash=fixture.fixture_hash,
        selected_panel_indices=sorted_idx,
        k_rad_m=k_rad_m,
        amplitude=amplitude,
        incident_direction=scaffold.incident_direction,
        rhs_values=rhs,
        sound_hard_neumann=True,
        scattering_solve_performed=False,
        bem_linear_system_solved=False,
        operator_assembled=False,
        rhs_only=True,
        deterministic_package_id=package_id,
    )


# ---------------------------------------------------------------------------
# BEM‑004C : tiny regularized linear‑solve prototype
# ---------------------------------------------------------------------------
from dataclasses import dataclass

@dataclass
class RegularizedSolvePrototype:
    """Result of the tiny regularized solve – prototype only, not physical."""
    solve_stage: str
    benchmark_id: str
    prototype_only: bool
    regularized_solve_performed: bool
    regularization_epsilon: float
    regularization_type: str
    regularization_physical: bool
    singular_integral_approximation: bool
    full_sphere_solve: bool
    boundary_integral_correctness_claim: bool
    scattered_pressure_computed: bool
    observer_pressure_computed: bool
    reference_matching_performed: bool
    tolerance_policy_applied: bool
    spl_computed: bool
    directivity_computed: bool
    impedance_computed: bool
    solution: List[complex]
    deterministic_package_id: str


def _complex_gaussian_elimination(A: List[List[complex]], b: List[complex]) -> List[complex]:
    """
    Solve A x = b for a small square complex matrix using Gaussian elimination
    with partial pivoting.  A and b are modified in place.
    Returns solution vector.
    """
    n = len(A)
    # forward elimination
    for col in range(n):
        # partial pivot
        max_row = max(range(col, n), key=lambda r: abs(A[r][col]))
        if col != max_row:
            A[col], A[max_row] = A[max_row], A[col]
            b[col], b[max_row] = b[max_row], b[col]
        # eliminate below
        for row in range(col+1, n):
            factor = A[row][col] / A[col][col]
            for j in range(col, n):
                A[row][j] -= factor * A[col][j]
            b[row] -= factor * b[col]
    # back substitution
    x = [0j] * n
    for i in range(n-1, -1, -1):
        s = sum(A[i][j] * x[j] for j in range(i+1, n))
        x[i] = (b[i] - s) / A[i][i]
    return x


def regularized_solve_prototype(
    operator_package: NonSingularOperatorPrototype,
    rhs_package: BoundaryRHSPackage,
    epsilon: float = 1.0e-6,
) -> RegularizedSolvePrototype:
    """
    Build and solve the tiny regularized system:
        (A + epsilon * I) x = rhs

    using the non‑singular operator prototype and the boundary RHS package.
    All inputs must match the ben004 benchmark and refer to the same panel subset.

    Parameters
    ----------
    operator_package : NonSingularOperatorPrototype
        The BEM‑003 operator prototype containing the off‑diagonal matrix.
    rhs_package : BoundaryRHSPackage
        The BEM‑004B RHS package containing the boundary vector.
    epsilon : float
        Artificial regularization diagonal value (must be > 0 and finite).

    Returns
    -------
    RegularizedSolvePrototype
        Solved algebraic unknown vector with full metadata.
    """
    # --- input validation ---
    if operator_package.benchmark_id != "ben004_rigid_sphere_scattering_registered":
        raise ValueError("Operator benchmark id must be ben004_rigid_sphere_scattering_registered")
    if rhs_package.benchmark_id != "ben004_rigid_sphere_scattering_registered":
        raise ValueError("RHS benchmark id must be ben004_rigid_sphere_scattering_registered")
    if operator_package.benchmark_id != rhs_package.benchmark_id:
        raise ValueError("Benchmark ids of operator and RHS packages differ")

    # selected indices consistency
    op_idx = sorted(operator_package.selected_panel_indices)
    rhs_idx = sorted(rhs_package.selected_panel_indices)
    if op_idx != rhs_idx:
        raise ValueError(
            f"Mismatched selected panel indices: operator {op_idx}, RHS {rhs_idx}"
        )

    n = len(op_idx)
    if not (3 <= n <= 6):
        raise ValueError("Selected panel count must be between 3 and 6")

    # matrix dimension must match RHS length
    if len(operator_package.matrix) != n or any(len(row) != n for row in operator_package.matrix):
        raise ValueError("Operator matrix dimensions do not match selected indices")
    if len(rhs_package.rhs_values) != n:
        raise ValueError("RHS length does not match selected indices")

    if not math.isfinite(epsilon) or epsilon <= 0.0:
        raise ValueError("epsilon must be finite and positive")

    # --- regularize and solve ---
    A = [row[:] for row in operator_package.matrix]  # deep copy
    for i in range(n):
        A[i][i] += epsilon

    b = list(rhs_package.rhs_values)

    x = _complex_gaussian_elimination(A, b)

    # --- deterministic package ID ---
    id_lines = []
    id_lines.append("solve_stage=bem004c_regularized_solve_prototype")
    id_lines.append(f"benchmark_id={operator_package.benchmark_id}")
    id_lines.append(f"op_package_id={operator_package.deterministic_package_id}")
    id_lines.append(f"rhs_package_id={rhs_package.deterministic_package_id}")
    id_lines.append(f"epsilon={epsilon:.15e}")
    id_lines.append(f"selected_indices={op_idx}")
    for val in x:
        id_lines.append(f"sol=({val.real:.15e},{val.imag:.15e})")
    hash_input = "\n".join(id_lines)
    package_id = hashlib.sha256(hash_input.encode("utf-8")).hexdigest()

    return RegularizedSolvePrototype(
        solve_stage="bem004c_regularized_solve_prototype",
        benchmark_id=operator_package.benchmark_id,
        prototype_only=True,
        regularized_solve_performed=True,
        regularization_epsilon=epsilon,
        regularization_type="artificial_diagonal_prototype",
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
        solution=x,
        deterministic_package_id=package_id,
    )


# ---------------------------------------------------------------------------
# BEM‑004D : prototype residual report (no analytical reference)
# ---------------------------------------------------------------------------

@dataclass
class PrototypeResidualReport:
    """Residuals of the regularized prototype solve – no scattering comparison."""
    # stage metadata
    report_stage: str
    benchmark_id: str
    prototype_only: bool

    # tolerance split
    residual_tolerance_applied: bool
    analytical_reference_comparison_performed: bool
    pressure_tolerance_applied: bool

    # residual quantities
    residual_vector: List[complex]
    max_abs_residual: float
    relative_l2_residual: float

    # copies from source packages for traceability
    solve_package_id: str
    operator_package_id: str
    rhs_package_id: str
    epsilon_used: float

    # explicit exclusion markers
    scattered_pressure_computed: bool
    observer_pressure_computed: bool
    analytical_pressure_evaluated: bool
    reference_matching_performed: bool
    spl_computed: bool
    directivity_computed: bool
    impedance_computed: bool

    deterministic_package_id: str


def compute_prototype_residual(
    solve_package: RegularizedSolvePrototype,
    operator_package: NonSingularOperatorPrototype,
    rhs_package: BoundaryRHSPackage,
) -> PrototypeResidualReport:
    """
    Compute the algebraic residual of the regularized prototype solve:
        r = (A + ε·I) x – rhs

    Returns a deterministic report with max‑abs and relative‑L2 residual norms.
    No analytical pressure or scattering comparison is performed.
    """
    # input validation
    if solve_package.benchmark_id != "ben004_rigid_sphere_scattering_registered":
        raise ValueError("Solve package must be ben004_rigid_sphere_scattering_registered")
    if operator_package.benchmark_id != "ben004_rigid_sphere_scattering_registered":
        raise ValueError("Operator package must be ben004_rigid_sphere_scattering_registered")
    if rhs_package.benchmark_id != "ben004_rigid_sphere_scattering_registered":
        raise ValueError("RHS package must be ben004_rigid_sphere_scattering_registered")

    # Dimension checks
    n = len(solve_package.solution)
    if len(operator_package.matrix) != n or any(len(row) != n for row in operator_package.matrix):
        raise ValueError("Operator matrix dimensions do not match solution length")
    if len(rhs_package.rhs_values) != n:
        raise ValueError("RHS length does not match solution length")

    epsilon = solve_package.regularization_epsilon
    if epsilon <= 0.0 or not math.isfinite(epsilon):
        raise ValueError("Regularization epsilon must be positive and finite")

    # reconstruct regularized matrix
    A = [row[:] for row in operator_package.matrix]  # copy
    for i in range(n):
        A[i][i] += epsilon

    x = solve_package.solution
    rhs = rhs_package.rhs_values

    # residual vector
    r = []
    for i in range(n):
        s = sum(A[i][j] * x[j] for j in range(n))
        r.append(s - rhs[i])

    # norms
    max_abs = max(abs(v) for v in r)
    rhs_l2 = math.sqrt(sum(abs(v)**2 for v in rhs))
    if rhs_l2 == 0.0:
        relative_l2 = 0.0
    else:
        residual_l2 = math.sqrt(sum(abs(v)**2 for v in r))
        relative_l2 = residual_l2 / rhs_l2

    # deterministic package ID
    id_lines = []
    id_lines.append("report_stage=bem004d_prototype_residual_report")
    id_lines.append(f"benchmark_id={solve_package.benchmark_id}")
    id_lines.append(f"solve_package_id={solve_package.deterministic_package_id}")
    id_lines.append(f"operator_package_id={operator_package.deterministic_package_id}")
    id_lines.append(f"rhs_package_id={rhs_package.deterministic_package_id}")
    id_lines.append(f"epsilon={epsilon:.15e}")
    for val in r:
        id_lines.append(f"res=({val.real:.15e},{val.imag:.15e})")
    id_lines.append(f"max_abs={max_abs:.15e}")
    id_lines.append(f"relative_l2={relative_l2:.15e}")
    hash_input = "\n".join(id_lines)
    package_id = hashlib.sha256(hash_input.encode("utf-8")).hexdigest()

    return PrototypeResidualReport(
        report_stage="bem004d_prototype_residual_report",
        benchmark_id=solve_package.benchmark_id,
        prototype_only=True,
        residual_tolerance_applied=True,
        analytical_reference_comparison_performed=False,
        pressure_tolerance_applied=False,
        residual_vector=r,
        max_abs_residual=max_abs,
        relative_l2_residual=relative_l2,
        solve_package_id=solve_package.deterministic_package_id,
        operator_package_id=operator_package.deterministic_package_id,
        rhs_package_id=rhs_package.deterministic_package_id,
        epsilon_used=epsilon,
        scattered_pressure_computed=False,
        observer_pressure_computed=False,
        analytical_pressure_evaluated=False,
        reference_matching_performed=False,
        spl_computed=False,
        directivity_computed=False,
        impedance_computed=False,
        deterministic_package_id=package_id,
    )

