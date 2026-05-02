
# ============================================================================
# BEM-004F: Analytical rigid-sphere reference evaluator
# ============================================================================
import math
import hashlib
from typing import Dict, Any, Optional
import numpy as np

def _spherical_jn(n: int, z: complex) -> complex:
    """Spherical Bessel j_n(z) for n=0..6, stable upward recurrence."""
    if n == 0:
        return np.sin(z) / z
    if n == 1:
        return np.sin(z) / z**2 - np.cos(z) / z
    j_prev2 = _spherical_jn(0, z)
    j_prev1 = _spherical_jn(1, z)
    for m in range(1, n):
        j_next = (2*m + 1) / z * j_prev1 - j_prev2
        j_prev2, j_prev1 = j_prev1, j_next
    return j_prev1

def _spherical_yn(n: int, z: complex) -> complex:
    """Spherical Neumann y_n(z) for n=0..6."""
    if n == 0:
        return -np.cos(z) / z
    if n == 1:
        return -np.cos(z) / z**2 - np.sin(z) / z
    y_prev2 = _spherical_yn(0, z)
    y_prev1 = _spherical_yn(1, z)
    for m in range(1, n):
        y_next = (2*m + 1) / z * y_prev1 - y_prev2
        y_prev2, y_prev1 = y_prev1, y_next
    return y_prev1

def _spherical_h1(n: int, z: complex) -> complex:
    """Outgoing spherical Hankel h_n^{(1)}(z) = j_n(z) + i y_n(z)."""
    return _spherical_jn(n, z) + 1j * _spherical_yn(n, z)

def _spherical_jn_deriv(n: int, z: complex) -> complex:
    """Derivative j_n'(z) = j_{n-1}(z) - (n+1)/z * j_n(z)."""
    if n == 0:
        # j_0'(z) = -sin(z)/z^2 + cos(z)/z
        return np.cos(z)/z - np.sin(z)/z**2
    j_n = _spherical_jn(n, z)
    j_nm1 = _spherical_jn(n-1, z)
    return j_nm1 - (n+1)/z * j_n

def _spherical_h1_deriv(n: int, z: complex) -> complex:
    """Derivative h_n^{(1)'}(z)."""
    if n == 0:
        # h_0'(z) = j_0'(z) + i y_0'(z)
        j0p = np.cos(z)/z - np.sin(z)/z**2
        y0p = np.sin(z)/z + np.cos(z)/z**2   # y_0'(z) = sin(z)/z + cos(z)/z^2
        return j0p + 1j * y0p
    h_n = _spherical_h1(n, z)
    h_nm1 = _spherical_h1(n-1, z)
    return h_nm1 - (n+1)/z * h_n

def _legendre_p(n: int, x: float) -> float:
    """Legendre polynomial P_n(x) for n=0..6 using recurrence."""
    if n == 0:
        return 1.0
    if n == 1:
        return x
    p_prev2 = 1.0
    p_prev1 = x
    for m in range(1, n):
        p_next = ((2*m + 1) * x * p_prev1 - m * p_prev2) / (m + 1)
        p_prev2, p_prev1 = p_prev1, p_next
    return p_prev1

class AnalyticalRigidSphereReferenceEvaluator:
    """
    BEM-004F: Bounded analytical reference evaluator for sound-hard sphere.
    Uses fixed series truncation n_max = 6, no adaptive logic.
    """

    def __init__(self, scaffold):
        """
        Parameters
        ----------
        scaffold : object
            Must provide attributes:
            - observers : ndarray, shape (N,3)
            - k : float, wavenumber
            - a : float, sphere radius
            - amplitude : complex, incident amplitude A
            - direction : ndarray, shape (3,), unit vector
        """
        self.scaffold = scaffold
        self._validate_scaffold()
        self.n_max = 6
        self.adaptive_truncation_used = False
        self.convergence_seeking_used = False
        self.reference_matching_performed = False
        self.tolerance_policy_applied = False
        self.bem_solution_consumed = False
        self.observer_reconstruction_performed = False
        self.spl_computed = False
        self.directivity_computed = False
        self.impedance_computed = False

    def _validate_scaffold(self):
        s = self.scaffold
        required = ['observers', 'k', 'a', 'amplitude', 'direction']
        for attr in required:
            if not hasattr(s, attr):
                raise ValueError(f"Scaffold missing required attribute: {attr}")
        if not isinstance(s.observers, np.ndarray) or s.observers.shape[1] != 3:
            raise ValueError("observers must be (N,3) numpy array")
        if s.k <= 0:
            raise ValueError("k must be positive")
        if s.a <= 0:
            raise ValueError("a must be positive")
        if np.abs(s.amplitude) == 0:
            raise ValueError("amplitude cannot be zero")
        if not np.allclose(np.linalg.norm(s.direction), 1.0):
            raise ValueError("direction must be unit vector")

    def compute_incident(self) -> np.ndarray:
        """Return incident pressure at all observers: A exp(i k d·x)."""
        s = self.scaffold
        dots = np.dot(s.observers, s.direction)
        return s.amplitude * np.exp(1j * s.k * dots)

    def compute_scattered(self) -> np.ndarray:
        """
        Compute scattered pressure using rigid-sphere series,
        fixed n_max = 6.
        """
        s = self.scaffold
        N = s.observers.shape[0]
        scattered = np.zeros(N, dtype=complex)

        # Pre-compute coefficients independent of observer
        ka = s.k * s.a
        # n from 0 to n_max
        coeffs = np.zeros(self.n_max + 1, dtype=complex)
        for n in range(self.n_max + 1):
            jn_ka = _spherical_jn(n, ka)
            hn_ka = _spherical_h1(n, ka)
            jn_deriv = _spherical_jn_deriv(n, ka)
            hn_deriv = _spherical_h1_deriv(n, ka)
            ratio = jn_deriv / hn_deriv
            i_pow_n = (1j) ** n
            coeffs[n] = -s.amplitude * (2*n + 1) * i_pow_n * ratio

        # Evaluate for each observer
        for i, obs in enumerate(s.observers):
            r = np.linalg.norm(obs)
            if r <= s.a:
                # observer inside/on sphere → not defined for scattered reference
                raise ValueError(f"Observer at r={r} <= a={s.a} is not exterior")
            cos_theta = np.dot(obs, s.direction) / r
            total = 0.0j
            for n in range(self.n_max + 1):
                hn_kr = _spherical_h1(n, s.k * r)
                Pn = _legendre_p(n, cos_theta)
                total += coeffs[n] * hn_kr * Pn
            scattered[i] = total
        return scattered

    def compute_total(self) -> np.ndarray:
        """Total = incident + scattered."""
        return self.compute_incident() + self.compute_scattered()

    def get_package(self) -> Dict[str, Any]:
        """
        Return analytical reference package with metadata and
        deterministic SHA-256 hash of the results.
        """
        p_inc = self.compute_incident()
        p_scat = self.compute_scattered()
        p_total = p_inc + p_scat

        # Create deterministic hash from flattened real/imag parts and parameters
        data_to_hash = np.concatenate([
            p_inc.view(float), p_scat.view(float), p_total.view(float),
            np.array([self.scaffold.k, self.scaffold.a, self.scaffold.amplitude.real,
                      self.scaffold.amplitude.imag], dtype=float)
        ])
        sha256 = hashlib.sha256(data_to_hash.tobytes()).hexdigest()

        return {
            "reference_stage": "bem004f_analytical_rigid_sphere_reference",
            "benchmark_id": "ben004_rigid_sphere_scattering_registered",
            "analytical_evaluator_implemented": True,
            "analytical_pressure_evaluated": True,
            "analytical_incident_pressure_computed": True,
            "analytical_scattered_pressure_computed": True,
            "analytical_total_pressure_computed": True,
            "series_truncation_n_max": self.n_max,
            "adaptive_truncation_used": self.adaptive_truncation_used,
            "convergence_seeking_used": self.convergence_seeking_used,
            "reference_matching_performed": self.reference_matching_performed,
            "tolerance_policy_applied": self.tolerance_policy_applied,
            "bem_solution_consumed": self.bem_solution_consumed,
            "observer_reconstruction_performed": self.observer_reconstruction_performed,
            "spl_computed": self.spl_computed,
            "directivity_computed": self.directivity_computed,
            "impedance_computed": self.impedance_computed,
            "incident_pressure": p_inc,
            "scattered_pressure": p_scat,
            "total_pressure": p_total,
            "package_sha256": sha256,
        }
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


# ---------------------------------------------------------------------------
# BEM‑004E : exterior observer scaffold and domain validation
# ---------------------------------------------------------------------------
from dataclasses import dataclass, field
from typing import List, Tuple
import math
import hashlib

class InvalidObserverDomainError(ValueError):
    """Raised when an observer point lies on or inside the rigid sphere."""
    pass

@dataclass
class DomainValidation:
    interior_points_rejected: bool = True
    boundary_points_rejected: bool = True

@dataclass
class ExteriorObserverScaffold:
    scaffold_stage: str
    benchmark_id: str
    sphere_radius: float
    domain: str
    observer_positions: List[Tuple[float, float, float]]
    observer_count: int
    domain_validation: DomainValidation
    analytical_evaluator_implemented: bool
    analytical_pressure_evaluated: bool
    observer_pressure_computed: bool
    scattered_pressure_computed: bool
    total_pressure_computed: bool
    boundary_to_observer_operator_assembled: bool
    reference_matching_performed: bool
    spl_computed: bool
    directivity_computed: bool
    impedance_computed: bool
    deterministic_package_id: str


def _validate_observer_domain(
    positions: List[Tuple[float, float, float]],
    sphere_radius: float
) -> None:
    """Raise InvalidObserverDomainError if any point is on or inside the sphere."""
    for x, y, z in positions:
        r = math.sqrt(x*x + y*y + z*z)
        if r <= sphere_radius:
            raise InvalidObserverDomainError(
                f"Observer ({x}, {y}, {z}) at distance {r} is on or inside the sphere "
                f"(radius {sphere_radius}). Only exterior domain allowed."
            )


def build_exterior_observer_scaffold(
    benchmark_id: str,
    sphere_radius: float,
    observer_positions: List[Tuple[float, float, float]],
) -> ExteriorObserverScaffold:
    """
    Create a deterministic exterior observer scaffold.

    All points must lie strictly outside the rigid sphere (r > sphere_radius).
    """
    # --- input validation ---
    if benchmark_id != "ben004_rigid_sphere_scattering_registered":
        raise ValueError("Only ben004_rigid_sphere_scattering_registered is supported")
    if not math.isfinite(sphere_radius) or sphere_radius <= 0.0:
        raise ValueError("sphere_radius must be finite and positive")
    if not observer_positions:
        raise ValueError("observer_positions must not be empty")
    for i, (x, y, z) in enumerate(observer_positions):
        if not all(math.isfinite(v) for v in (x, y, z)):
            raise ValueError(f"Observer position {i} contains non‑finite coordinates")

    # domain check
    _validate_observer_domain(observer_positions, sphere_radius)

    # --- deterministic package ID ---
    id_lines = []
    id_lines.append("scaffold_stage=bem004e_exterior_observer_scaffold")
    id_lines.append(f"benchmark_id={benchmark_id}")
    id_lines.append(f"sphere_radius={sphere_radius:.15e}")
    id_lines.append("domain=exterior_domain")
    # positions in caller order, preserved
    for x, y, z in observer_positions:
        id_lines.append(f"({x:.15e},{y:.15e},{z:.15e})")
    hash_input = "\n".join(id_lines)
    package_id = hashlib.sha256(hash_input.encode("utf-8")).hexdigest()

    return ExteriorObserverScaffold(
        scaffold_stage="bem004e_exterior_observer_scaffold",
        benchmark_id=benchmark_id,
        sphere_radius=sphere_radius,
        domain="exterior_domain",
        observer_positions=observer_positions,
        observer_count=len(observer_positions),
        domain_validation=DomainValidation(
            interior_points_rejected=True,
            boundary_points_rejected=True,
        ),
        analytical_evaluator_implemented=False,
        analytical_pressure_evaluated=False,
        observer_pressure_computed=False,
        scattered_pressure_computed=False,
        total_pressure_computed=False,
        boundary_to_observer_operator_assembled=False,
        reference_matching_performed=False,
        spl_computed=False,
        directivity_computed=False,
        impedance_computed=False,
        deterministic_package_id=package_id,
    )
# ============================================================================
# BEM-004F: Analytical rigid-sphere reference evaluator
# ============================================================================

import math
import cmath
import hashlib
import json
from typing import List, Tuple, Union, Dict, Any


# ----------------------------------------------------------------------------
# Spherical Bessel / Hankel and Legendre utilities (pure Python)
# ----------------------------------------------------------------------------

def spherical_bessel_j(n: int, z: complex) -> complex:
    """Spherical Bessel j_n(z) for n <= 6."""
    if n == 0:
        return cmath.sin(z) / z if z != 0 else 1.0
    if n == 1:
        return cmath.sin(z) / (z * z) - cmath.cos(z) / z
    # upward recurrence
    j_prev2 = spherical_bessel_j(0, z)
    j_prev1 = spherical_bessel_j(1, z)
    for m in range(1, n):
        j_next = (2 * m + 1) / z * j_prev1 - j_prev2
        j_prev2, j_prev1 = j_prev1, j_next
    return j_prev1


def spherical_bessel_derivative(n: int, z: complex, jn: complex = None) -> complex:
    """Derivative j_n'(z)."""
    if jn is None:
        jn = spherical_bessel_j(n, z)
    if n == 0:
        j1 = spherical_bessel_j(1, z)
        return -j1
    j_prev = spherical_bessel_j(n - 1, z) if n - 1 >= 0 else 0
    j_next = spherical_bessel_j(n + 1, z)
    return (n * j_prev - (n + 1) * j_next) / (2 * n + 1)


def spherical_hankel_h1(n: int, z: complex) -> complex:
    """Spherical Hankel of first kind h_n^(1)(z)."""
    if n == 0:
        return -1j * cmath.exp(1j * z) / z if z != 0 else complex('inf')
    if n == 1:
        return -cmath.exp(1j * z) / z * (1 + 1j / z)
    # upward recurrence
    h_prev2 = spherical_hankel_h1(0, z)
    h_prev1 = spherical_hankel_h1(1, z)
    for m in range(1, n):
        h_next = (2 * m + 1) / z * h_prev1 - h_prev2
        h_prev2, h_prev1 = h_prev1, h_next
    return h_prev1


def spherical_hankel_derivative(n: int, z: complex, hn: complex = None) -> complex:
    """Derivative h_n^(1)'(z)."""
    if hn is None:
        hn = spherical_hankel_h1(n, z)
    if n == 0:
        h1 = spherical_hankel_h1(1, z)
        return -h1
    h_prev = spherical_hankel_h1(n - 1, z) if n - 1 >= 0 else 0
    h_next = spherical_hankel_h1(n + 1, z)
    return (n * h_prev - (n + 1) * h_next) / (2 * n + 1)


def legendre_p(n: int, x: float) -> float:
    """Legendre polynomial P_n(x)."""
    if n == 0:
        return 1.0
    if n == 1:
        return x
    p_prev2 = 1.0
    p_prev1 = x
    for m in range(1, n):
        p_next = ((2 * m + 1) * x * p_prev1 - m * p_prev2) / (m + 1)
        p_prev2, p_prev1 = p_prev1, p_next
    return p_prev1


# ----------------------------------------------------------------------------
# Analytical evaluator for rigid sphere scattering
# ----------------------------------------------------------------------------

class AnalyticalRigidSphereReferenceEvaluator:
    """
    Bounded analytical evaluator for plane‑wave scattering by a sound‑hard sphere.
    Uses fixed n_max = 6, no adaptive truncation, no BEM consumption.
    """

    def __init__(self, sphere_radius: float, k: complex, amplitude: complex,
                 direction: Tuple[float, float, float], n_max: int = 6):
        """
        Args:
            sphere_radius: radius a of the sphere
            k: wavenumber (complex allowed, typically real positive)
            amplitude: incident plane‑wave amplitude A
            direction: incident direction vector (will be normalized)
            n_max: series truncation (fixed to 6 by project policy)
        """
        self.sphere_radius = sphere_radius
        self.k = k
        self.amplitude = amplitude
        norm = math.sqrt(sum(d * d for d in direction))
        if norm == 0:
            raise ValueError("Direction vector must be non-zero")
        self.direction = tuple(d / norm for d in direction)
        if n_max != 6:
            # Policy enforces n_max = 6, but we still allow construction.
            # The metadata will report the actual value.
            pass
        self.n_max = n_max
        self._coeffs = self._compute_coefficients()

    def _compute_coefficients(self) -> List[complex]:
        """Precompute A_n = - (j_n'(ka)/h_n^{(1)'}(ka)) * (2n+1) i^n."""
        ka = self.k * self.sphere_radius
        coeffs = []
        for n in range(0, self.n_max + 1):
            jn = spherical_bessel_j(n, ka)
            jn_prime = spherical_bessel_derivative(n, ka, jn)
            hn = spherical_hankel_h1(n, ka)
            hn_prime = spherical_hankel_derivative(n, ka, hn)
            factor = -(jn_prime / hn_prime) * (2 * n + 1) * (1j) ** n
            coeffs.append(factor)
        return coeffs

    def evaluate(self, observer_points) -> Dict[str, Any]:
        """
        Compute analytical pressures at exterior observer points.

        Args:
            observer_points: either an object with a `points` attribute (each point
                             a (x,y,z) triple) or an iterable of (x,y,z) triples.
                             All points must lie outside the sphere (r > radius).

        Returns:
            Dictionary containing:
                - incident_pressure: list of complex values
                - scattered_pressure: list of complex values
                - total_pressure: list of complex values
                - metadata: dict with flags required by the milestone
                - package_id: deterministic SHA‑256 hex digest
        """
        # Accept BEM-004E exterior observer scaffold (points attribute) or raw list
        if hasattr(observer_points, 'points'):
            points = observer_points.points
        else:
            points = observer_points

        points_list = []
        for idx, p in enumerate(points):
            if len(p) != 3:
                raise ValueError(f"Observer point {idx} is not (x,y,z) triple")
            x, y, z = p
            r = math.sqrt(x * x + y * y + z * z)
            if r <= self.sphere_radius:
                raise ValueError(f"Observer at {p} is not exterior (r <= sphere_radius)")
            points_list.append((x, y, z))

        n_pts = len(points_list)
        incident = [0j] * n_pts
        scattered = [0j] * n_pts
        total = [0j] * n_pts

        for idx, (x, y, z) in enumerate(points_list):
            r = math.sqrt(x * x + y * y + z * z)
            # Unit vector from origin to observer
            rx, ry, rz = x / r, y / r, z / r
            cos_theta = (self.direction[0] * rx +
                         self.direction[1] * ry +
                         self.direction[2] * rz)

            # Incident field: A exp(i k d·x)
            dot_d_x = (self.direction[0] * x +
                       self.direction[1] * y +
                       self.direction[2] * z)
            p_inc = self.amplitude * cmath.exp(1j * self.k * dot_d_x)
            incident[idx] = p_inc

            # Scattered field series
            kr = self.k * r
            p_scat = 0j
            for n in range(0, self.n_max + 1):
                hn = spherical_hankel_h1(n, kr)
                pn = legendre_p(n, cos_theta)
                p_scat += self.amplitude * self._coeffs[n] * hn * pn
            scattered[idx] = p_scat
            total[idx] = p_inc + p_scat

        result = {
            "incident_pressure": incident,
            "scattered_pressure": scattered,
            "total_pressure": total,
            "metadata": {
                "reference_stage": "bem004f_analytical_rigid_sphere_reference",
                "benchmark_id": "ben004_rigid_sphere_scattering_registered",
                "analytical_evaluator_implemented": True,
                "analytical_pressure_evaluated": True,
                "analytical_incident_pressure_computed": True,
                "analytical_scattered_pressure_computed": True,
                "analytical_total_pressure_computed": True,
                "series_truncation_n_max": self.n_max,
                "adaptive_truncation_used": False,
                "convergence_seeking_used": False,
                "reference_matching_performed": False,
                "tolerance_policy_applied": False,
                "bem_solution_consumed": False,
                "observer_reconstruction_performed": False,
                "boundary_to_observer_operator_assembled": False,
                "spl_computed": False,
                "directivity_computed": False,
                "impedance_computed": False
            }
        }
        result["package_id"] = self._compute_package_id(result)
        return result

    def _compute_package_id(self, result: Dict) -> str:
        """Deterministic SHA‑256 of the pressure arrays and metadata."""
        data = {
            "incident": [[z.real, z.imag] for z in result["incident_pressure"]],
            "scattered": [[z.real, z.imag] for z in result["scattered_pressure"]],
            "total": [[z.real, z.imag] for z in result["total_pressure"]],
            "metadata": result["metadata"]
        }
        json_str = json.dumps(data, sort_keys=True, separators=(',', ':'))
        return hashlib.sha256(json_str.encode()).hexdigest()
