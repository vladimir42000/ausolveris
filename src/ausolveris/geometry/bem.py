
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

# ============================================================================
# BEM-005A: Observer reconstruction scaffold (non-physical)
# ============================================================================

import hashlib
import json
from typing import Any, Dict, List, Tuple, Union


class ObserverReconstructionScaffold:
    """
    Non-physical scaffold for boundary-to-observer reconstruction.
    Does not assemble H operator or perform actual reconstruction.
    """

    def __init__(self, observer_scaffold, boundary_solution_stub):
        """
        Args:
            observer_scaffold: BEM-004E exterior observer scaffold (with .observer_positions)
            boundary_solution_stub: stub package containing boundary data (any dict with required keys? but not used)
        """
        # Validate observer scaffold
        if not hasattr(observer_scaffold, 'observer_positions'):
            raise ValueError("Observer scaffold must have 'observer_positions' attribute")
        points = observer_scaffold.observer_positions
        if not isinstance(points, (list, tuple)) or len(points) == 0:
            raise ValueError("Observer scaffold observer_positions must be non-empty list/tuple")
        for i, p in enumerate(points):
            if len(p) != 3:
                raise ValueError(f"Point {i} is not (x,y,z) triple")
        self.observer_positions = points

        # Validate boundary solution stub (minimally, must be a dict with a key 'boundary_data_present')
        # We'll just check it's a dict (stub can be anything, but for deterministic ID we need to incorporate it)
        if not isinstance(boundary_solution_stub, dict):
            raise ValueError("Boundary solution stub must be a dictionary")
        self.boundary_stub = boundary_solution_stub

        # Define H descriptor (stub)
        self.H = {
            "operator_type": "boundary_to_observer_stub",
            "assembled": False,
            "singular_quadrature_used": False
        }

    def reconstruct(self) -> Dict[str, Any]:
        """
        Return deterministic scaffold package with placeholder pressure arrays.
        Does NOT perform physical reconstruction.
        """
        n = len(self.observer_positions)
        # Placeholder pressures: zero complex numbers (non-physical)
        placeholder = [0j] * n

        result = {
            "reconstructed_incident_pressure": placeholder.copy(),
            "reconstructed_scattered_pressure": placeholder.copy(),
            "reconstructed_total_pressure": placeholder.copy(),
            "H_descriptor": self.H,
            "metadata": {
                "reconstruction_stage": "bem005a_observer_reconstruction_scaffold",
                "benchmark_id": "ben004_rigid_sphere_scattering_registered",
                "reconstruction_scaffold_assembled": True,
                "boundary_to_observer_operator_assembled": False,
                "reconstruction_performed": False,
                "analytical_reference_comparison_performed": False,
                "tolerance_policy_applied": False,
                "singular_quadrature_implemented": False,
                "spl_computed": False,
                "directivity_computed": False,
                "impedance_computed": False,
                "non_physical": True
            }
        }
        # Add package ID
        result["package_id"] = self._compute_package_id(result)
        return result

    def _compute_package_id(self, result: Dict) -> str:
        """Deterministic SHA-256 of the result structure (excluding package_id itself)."""
        data = {
            "observer_positions": self.observer_positions,
            "boundary_stub": self.boundary_stub,
            "reconstructed_incident_pressure": [[z.real, z.imag] for z in result["reconstructed_incident_pressure"]],
            "reconstructed_scattered_pressure": [[z.real, z.imag] for z in result["reconstructed_scattered_pressure"]],
            "reconstructed_total_pressure": [[z.real, z.imag] for z in result["reconstructed_total_pressure"]],
            "H_descriptor": self.H,
            "metadata": result["metadata"]
        }
        json_str = json.dumps(data, sort_keys=True, separators=(',', ':'))
        return hashlib.sha256(json_str.encode()).hexdigest()
# ============================================================================
# BEM-005B: Boundary-to-observer reconstruction execution gate
# ============================================================================

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Dict, List, Tuple


@dataclass
class ReconstructionGateRequest:
    """Validated request for the BEM-005B reconstruction execution gate."""
    gate_stage: str
    benchmark_id: str
    request_validated: bool
    boundary_solution_package_id: str
    observer_scaffold_package_id: str
    observer_count: int
    observer_positions: List[Tuple[float, float, float]]


@dataclass
class ReconstructionGateResult:
    """Non-physical gated result for BEM-005B."""
    reconstruction_stage: str
    benchmark_id: str
    request_validated: bool
    execution_gated: bool
    physical_h_matrix_assembled: bool
    physical_reconstruction_performed: bool
    analytical_reference_comparison_performed: bool
    tolerance_policy_applied: bool
    singular_quadrature_implemented: bool
    spl_computed: bool
    directivity_computed: bool
    impedance_computed: bool
    non_physical: bool
    reconstructed_incident_pressure: List[complex]
    reconstructed_scattered_pressure: List[complex]
    reconstructed_total_pressure: List[complex]
    deterministic_package_id: str


def build_reconstruction_gate_request(
    boundary_solution: "RegularizedSolvePrototype",
    observer_scaffold: "ExteriorObserverScaffold",
    reconstruction_scaffold: "ObserverReconstructionScaffold",
) -> ReconstructionGateRequest:
    """
    Validate structural consistency of the three input packages and return a
    ReconstructionGateRequest.  Raises ValueError on any structural failure.
    request_validated=True appears only after all checks pass.

    Parameters
    ----------
    boundary_solution : RegularizedSolvePrototype
        BEM-004C prototype boundary solution package.
    observer_scaffold : ExteriorObserverScaffold
        BEM-004E exterior observer scaffold.
    reconstruction_scaffold : ObserverReconstructionScaffold
        BEM-005A observer reconstruction scaffold.
    """
    # --- type guards (controlled ValueError, not accidental AttributeError) ---
    if not isinstance(boundary_solution, RegularizedSolvePrototype):
        raise ValueError(
            "boundary_solution must be a RegularizedSolvePrototype instance"
        )
    if not isinstance(observer_scaffold, ExteriorObserverScaffold):
        raise ValueError(
            "observer_scaffold must be an ExteriorObserverScaffold instance"
        )
    if not isinstance(reconstruction_scaffold, ObserverReconstructionScaffold):
        raise ValueError(
            "reconstruction_scaffold must be an ObserverReconstructionScaffold instance"
        )

    # --- benchmark ID checks ---
    _BID = "ben004_rigid_sphere_scattering_registered"
    if boundary_solution.benchmark_id != _BID:
        raise ValueError(
            f"boundary_solution.benchmark_id must be {_BID!r}; "
            f"got {boundary_solution.benchmark_id!r}"
        )
    if observer_scaffold.benchmark_id != _BID:
        raise ValueError(
            f"observer_scaffold.benchmark_id must be {_BID!r}; "
            f"got {observer_scaffold.benchmark_id!r}"
        )

    # --- observer position consistency ---
    # Both ExteriorObserverScaffold and ObserverReconstructionScaffold now use
    # the canonical observer_positions attribute (BEM-005-PATCH).
    obs_pos = list(observer_scaffold.observer_positions)
    rec_pts = list(reconstruction_scaffold.observer_positions)
    if obs_pos != rec_pts:
        raise ValueError(
            "observer_scaffold.observer_positions does not match "
            "reconstruction_scaffold.observer_positions; packages are inconsistent"
        )

    # --- all checks passed: request_validated=True now ---
    return ReconstructionGateRequest(
        gate_stage="bem005b_reconstruction_execution_gate",
        benchmark_id=_BID,
        request_validated=True,
        boundary_solution_package_id=boundary_solution.deterministic_package_id,
        observer_scaffold_package_id=observer_scaffold.deterministic_package_id,
        observer_count=observer_scaffold.observer_count,
        observer_positions=obs_pos,
    )


def execute_reconstruction_gate(
    request: ReconstructionGateRequest,
) -> ReconstructionGateResult:
    """
    Execute the BEM-005B gate.  Physical reconstruction is explicitly blocked.
    Returns a deterministic non-physical result package.

    Parameters
    ----------
    request : ReconstructionGateRequest
        A validated request produced by build_reconstruction_gate_request.
    """
    if not isinstance(request, ReconstructionGateRequest):
        raise ValueError(
            "request must be a ReconstructionGateRequest instance"
        )
    if not request.request_validated:
        raise ValueError(
            "request.request_validated is False; only validated requests may be executed"
        )

    n = request.observer_count
    placeholder = [0j] * n

    # --- deterministic package ID ---
    id_lines = [
        "gate_stage=bem005b_reconstruction_execution_gate",
        f"benchmark_id={request.benchmark_id}",
        f"boundary_solution_package_id={request.boundary_solution_package_id}",
        f"observer_scaffold_package_id={request.observer_scaffold_package_id}",
        f"observer_positions={request.observer_positions}",
    ]
    hash_input = "\n".join(id_lines)
    package_id = hashlib.sha256(hash_input.encode("utf-8")).hexdigest()

    return ReconstructionGateResult(
        reconstruction_stage="bem005b_reconstruction_execution_gate",
        benchmark_id=request.benchmark_id,
        request_validated=True,
        execution_gated=True,
        physical_h_matrix_assembled=False,
        physical_reconstruction_performed=False,
        analytical_reference_comparison_performed=False,
        tolerance_policy_applied=False,
        singular_quadrature_implemented=False,
        spl_computed=False,
        directivity_computed=False,
        impedance_computed=False,
        non_physical=True,
        reconstructed_incident_pressure=list(placeholder),
        reconstructed_scattered_pressure=list(placeholder),
        reconstructed_total_pressure=list(placeholder),
        deterministic_package_id=package_id,
    )

# ============================================================================
# BEM-005C: Analytical reference matching and tolerance scaffold
# ============================================================================

import math


@dataclass
class ReferenceMatchingReport:
    """
    BEM-005C matching/tolerance scaffold result.
    Compares analytical total pressure (BEM-004F) against reconstructed total
    pressure (BEM-005B).  Under current gated-zero reconstruction, benchmark_passed
    is always False.  No physical reconstruction is performed here.
    """
    validation_stage: str
    benchmark_id: str
    observer_count: int
    relative_l2_error: float
    max_abs_error: float
    relative_pressure_tolerance: float
    absolute_pressure_tolerance: float
    benchmark_passed: bool
    reference_matching_performed: bool
    tolerance_policy_applied: bool
    physical_h_matrix_assembled: bool
    singular_quadrature_implemented: bool
    spl_computed: bool
    directivity_computed: bool
    impedance_computed: bool
    non_physical: bool
    analytical_package_id: str
    reconstruction_package_id: str
    deterministic_package_id: str


def build_analytical_matching_report(
    analytical_package: dict,
    reconstruction_result: "ReconstructionGateResult",
) -> ReferenceMatchingReport:
    """
    Validate structural consistency of the BEM-004F analytical package and the
    BEM-005B gated reconstruction result, compute comparison metrics, apply
    tolerance thresholds, and return a ReferenceMatchingReport.

    Because BEM-005B returns zeroed non-physical pressure arrays, the benchmark
    deterministically fails (benchmark_passed=False).  This is expected behaviour
    at the current phase.

    Parameters
    ----------
    analytical_package : dict
        Package returned by AnalyticalRigidSphereReferenceEvaluator.evaluate().
        Must contain keys: "total_pressure", "metadata" (with "benchmark_id"),
        "package_id".
    reconstruction_result : ReconstructionGateResult
        Gated result produced by execute_reconstruction_gate().

    Raises
    ------
    ValueError
        On any structural inconsistency, benchmark_id mismatch, length mismatch,
        or zero analytical norm.
    """
    _BID = "ben004_rigid_sphere_scattering_registered"
    _REL_TOL = 1.0e-2
    _ABS_TOL = 1.0e-6

    # --- type / key guards ---
    if not isinstance(analytical_package, dict):
        raise ValueError(
            "analytical_package must be a dict from AnalyticalRigidSphereReferenceEvaluator.evaluate()"
        )
    if "metadata" not in analytical_package or "total_pressure" not in analytical_package \
            or "package_id" not in analytical_package:
        raise ValueError(
            "analytical_package must contain keys 'metadata', 'total_pressure', 'package_id'"
        )
    if not isinstance(reconstruction_result, ReconstructionGateResult):
        raise ValueError(
            "reconstruction_result must be a ReconstructionGateResult instance"
        )

    # --- benchmark ID checks ---
    anal_bid = analytical_package["metadata"].get("benchmark_id", "")
    if anal_bid != _BID:
        raise ValueError(
            f"analytical_package benchmark_id must be {_BID!r}; got {anal_bid!r}"
        )
    if reconstruction_result.benchmark_id != _BID:
        raise ValueError(
            f"reconstruction_result.benchmark_id must be {_BID!r}; "
            f"got {reconstruction_result.benchmark_id!r}"
        )

    # --- extract pressure arrays ---
    p_anal = list(analytical_package["total_pressure"])
    p_rec = list(reconstruction_result.reconstructed_total_pressure)

    # --- length consistency ---
    if len(p_anal) != len(p_rec):
        raise ValueError(
            f"Pressure array length mismatch: analytical has {len(p_anal)} points, "
            f"reconstruction has {len(p_rec)} points"
        )

    n = len(p_anal)

    # --- compute metrics ---
    norm_anal_sq = sum(abs(v) ** 2 for v in p_anal)
    norm_anal = math.sqrt(norm_anal_sq)
    if norm_anal == 0.0:
        raise ValueError(
            "Analytical total pressure norm is zero; relative_l2_error is undefined. "
            "Ensure a non-trivial analytical field is evaluated."
        )

    diff = [p_anal[i] - p_rec[i] for i in range(n)]
    norm_diff = math.sqrt(sum(abs(d) ** 2 for d in diff))
    relative_l2_error = norm_diff / norm_anal
    max_abs_error = max(abs(d) for d in diff)

    # --- tolerance policy ---
    benchmark_passed = (relative_l2_error <= _REL_TOL) and (max_abs_error <= _ABS_TOL)

    # --- deterministic package ID ---
    id_lines = [
        "validation_stage=bem005c_analytical_matching_scaffold",
        f"benchmark_id={_BID}",
        f"analytical_package_id={analytical_package['package_id']}",
        f"reconstruction_package_id={reconstruction_result.deterministic_package_id}",
        f"relative_l2_error={relative_l2_error!r}",
        f"max_abs_error={max_abs_error!r}",
    ]
    package_id = hashlib.sha256("\n".join(id_lines).encode("utf-8")).hexdigest()

    return ReferenceMatchingReport(
        validation_stage="bem005c_analytical_matching_scaffold",
        benchmark_id=_BID,
        observer_count=n,
        relative_l2_error=relative_l2_error,
        max_abs_error=max_abs_error,
        relative_pressure_tolerance=_REL_TOL,
        absolute_pressure_tolerance=_ABS_TOL,
        benchmark_passed=benchmark_passed,
        reference_matching_performed=True,
        tolerance_policy_applied=True,
        physical_h_matrix_assembled=False,
        singular_quadrature_implemented=False,
        spl_computed=False,
        directivity_computed=False,
        impedance_computed=False,
        non_physical=True,
        analytical_package_id=analytical_package["package_id"],
        reconstruction_package_id=reconstruction_result.deterministic_package_id,
        deterministic_package_id=package_id,
    )

# ============================================================================
# BEM-006A: Regular exterior observer H-matrix prototype
# ============================================================================


@dataclass
class HMatrixPrototype:
    """
    BEM-006A regular exterior observer H-matrix prototype package.

    Stores the boundary-to-observer interaction matrix assembled using the
    same single-layer Green-function kernel as BEM-003 (H[i,j] = G(r_ij,k)*area_j),
    applied from strictly exterior observer positions to the controlled panel
    subset centroids.

    No reconstruction is performed. No validation is claimed. The package is
    explicitly non_physical as a solver result because no H @ boundary_unknowns
    multiplication has been executed.
    """
    matrix_stage: str
    benchmark_id: str
    observer_count: int
    panel_count: int
    selected_panel_indices: List[int]
    k_rad_m: float
    observer_positions: List[Tuple[float, float, float]]
    panel_centroids: List[Tuple[float, float, float]]
    panel_areas: List[float]
    h_matrix: List[List[complex]]          # shape: observer_count × panel_count
    physical_h_matrix_assembled: bool
    singular_quadrature_implemented: bool
    reconstruction_performed: bool
    analytical_reference_comparison_performed: bool
    tolerance_policy_applied: bool
    spl_computed: bool
    directivity_computed: bool
    impedance_computed: bool
    non_physical: bool
    deterministic_package_id: str


def assemble_regular_h_matrix_prototype(
    fixture: "RigidSphereMeshFixture",
    selected_indices: List[int],
    observer_scaffold: ExteriorObserverScaffold,
    k_rad_m: float,
) -> HMatrixPrototype:
    """
    Assemble a regular exterior observer boundary-to-observer H-matrix
    prototype for a controlled 3–6 panel subset on the rigid-sphere benchmark.

    Kernel convention (identical to BEM-003 single-layer):
        H[i, j] = G(|x_obs_i − centroid_j|, k) * area_j

    Observers must be strictly exterior (guaranteed by ExteriorObserverScaffold
    domain validation). No near-singular or singular quadrature is applied.
    No reconstruction is executed. No matrix-vector multiplication is performed.

    Parameters
    ----------
    fixture : RigidSphereMeshFixture
        Must be the ben004_rigid_sphere_scattering_registered fixture.
    selected_indices : list of int
        Panel indices to include (3–6 unique valid indices).
    observer_scaffold : ExteriorObserverScaffold
        BEM-004E exterior observer scaffold carrying canonical observer_positions.
    k_rad_m : float
        Wavenumber in rad/m (finite, >= 0).

    Returns
    -------
    HMatrixPrototype

    Raises
    ------
    ValueError
        On any structural inconsistency or out-of-range input.
    """
    _BID = "ben004_rigid_sphere_scattering_registered"

    # --- type and benchmark guards ---
    if not isinstance(observer_scaffold, ExteriorObserverScaffold):
        raise ValueError(
            "observer_scaffold must be an ExteriorObserverScaffold instance"
        )
    if fixture.benchmark_id != _BID:
        raise ValueError(
            f"fixture.benchmark_id must be {_BID!r}; got {fixture.benchmark_id!r}"
        )
    if observer_scaffold.benchmark_id != _BID:
        raise ValueError(
            f"observer_scaffold.benchmark_id must be {_BID!r}; "
            f"got {observer_scaffold.benchmark_id!r}"
        )

    # --- panel subset validation ---
    if not (3 <= len(selected_indices) <= 6):
        raise ValueError(
            f"selected_indices must contain 3 to 6 panels; got {len(selected_indices)}"
        )
    if len(set(selected_indices)) != len(selected_indices):
        raise ValueError("Duplicate panel indices are not allowed")
    if not all(isinstance(i, int) and 0 <= i < len(fixture.panels)
               for i in selected_indices):
        raise ValueError("Invalid panel index – must exist in fixture")

    # --- wavenumber guard ---
    if not math.isfinite(k_rad_m) or k_rad_m < 0.0:
        raise ValueError("k_rad_m must be finite and non-negative")

    # --- extract geometry ---
    sorted_idx = sorted(selected_indices)
    n_panels = len(sorted_idx)
    centroids = [fixture.panels[idx].centroid for idx in sorted_idx]
    areas = [fixture.panels[idx].area for idx in sorted_idx]
    obs_positions = list(observer_scaffold.observer_positions)
    n_obs = len(obs_positions)

    # --- assemble H matrix: shape (n_obs, n_panels) ---
    # Kernel: H[i,j] = G(|x_obs_i - centroid_j|, k) * area_j
    # Identical single-layer convention to BEM-003 operator assembly.
    # All interactions are regular (observers strictly exterior; no self-panel).
    h_matrix = []
    for i in range(n_obs):
        row = []
        for j in range(n_panels):
            r = _distance(obs_positions[i], centroids[j])
            G = helmholtz_green_function(r, k_rad_m)
            row.append(G * areas[j])
        h_matrix.append(row)

    # --- deterministic package ID ---
    id_lines = [
        "matrix_stage=bem006a_regular_h_matrix_prototype",
        f"benchmark_id={_BID}",
        f"fixture_hash={fixture.fixture_hash}",
        f"k_rad_m={k_rad_m:.15e}",
        f"selected_panel_indices={sorted_idx}",
        f"observer_positions={obs_positions}",
    ]
    for row in h_matrix:
        for z in row:
            id_lines.append(f"{z.real:.15e}+{z.imag:.15e}j")
    package_id = hashlib.sha256(
        "\n".join(id_lines).encode("utf-8")
    ).hexdigest()

    return HMatrixPrototype(
        matrix_stage="bem006a_regular_h_matrix_prototype",
        benchmark_id=_BID,
        observer_count=n_obs,
        panel_count=n_panels,
        selected_panel_indices=sorted_idx,
        k_rad_m=k_rad_m,
        observer_positions=obs_positions,
        panel_centroids=centroids,
        panel_areas=areas,
        h_matrix=h_matrix,
        physical_h_matrix_assembled=True,
        singular_quadrature_implemented=False,
        reconstruction_performed=False,
        analytical_reference_comparison_performed=False,
        tolerance_policy_applied=False,
        spl_computed=False,
        directivity_computed=False,
        impedance_computed=False,
        non_physical=True,
        deterministic_package_id=package_id,
    )

# ============================================================================
# BEM-006B: Gated exterior reconstruction prototype
# ============================================================================


@dataclass
class ReconstructedObserverPressure:
    """
    BEM-006B gated exterior reconstruction result.

    Contains numerically reconstructed observer-pressure arrays produced by
    the prototype matrix-vector multiplication p_scattered = H @ x, where H
    is the BEM-006A regular H-matrix prototype and x is the BEM-004C
    artificially regularized boundary solution vector.

    The package is non_physical=True as a validation result: it is based on
    a toy regularized 3–6 panel prototype and is not compared against the
    BEM-004F analytical reference.  The BEM-005C matching gate is not invoked.
    """
    reconstruction_stage: str
    benchmark_id: str
    observer_count: int
    panel_count: int
    reconstructed_incident_pressure: List[complex]
    reconstructed_scattered_pressure: List[complex]
    reconstructed_total_pressure: List[complex]
    incident_pressure_supplied: bool
    physical_h_matrix_assembled: bool
    physical_reconstruction_performed: bool
    singular_quadrature_implemented: bool
    analytical_reference_comparison_performed: bool
    tolerance_policy_applied: bool
    spl_computed: bool
    directivity_computed: bool
    impedance_computed: bool
    non_physical: bool
    h_matrix_package_id: str
    boundary_solution_package_id: str
    deterministic_package_id: str


def reconstruct_exterior_observer_pressure(
    h_matrix_prototype: "HMatrixPrototype",
    boundary_solution: "RegularizedSolvePrototype",
    incident_pressure: "List[complex] | None" = None,
) -> ReconstructedObserverPressure:
    """
    Execute the prototype boundary-to-observer matrix-vector multiplication:

        p_scattered[i] = sum_j( H[i,j] * x[j] )

    where H is the BEM-006A regular H-matrix and x is the BEM-004C regularized
    boundary solution vector.

    Incident pressure policy
    ------------------------
    If `incident_pressure` is supplied, it must have length equal to
    `h_matrix_prototype.observer_count` and is used directly:
        p_total = p_incident + p_scattered

    If `incident_pressure` is None (default), a deterministic zero array is
    used as placeholder:
        p_incident = [0j] * observer_count
        p_total    = p_scattered   (same object, since zeros add nothing)

    This choice is documented here and in the validation doc.  No controlled
    ValueError is raised for absent incident pressure; the zero-array behaviour
    is intentional and clearly marked in the output via `incident_pressure_supplied`.

    Analytical comparison is NOT performed.  BEM-005C is NOT called.
    Tolerance policy is NOT applied.

    Parameters
    ----------
    h_matrix_prototype : HMatrixPrototype
        BEM-006A regular exterior H-matrix prototype package.
    boundary_solution : RegularizedSolvePrototype
        BEM-004C artificially regularized boundary solution package.
    incident_pressure : list of complex or None
        Optional incident pressure at each observer point.  If None, a
        deterministic zero placeholder is used.

    Returns
    -------
    ReconstructedObserverPressure

    Raises
    ------
    ValueError
        On type error, benchmark ID mismatch, or dimension incompatibility.
    """
    _BID = "ben004_rigid_sphere_scattering_registered"

    # --- type guards ---
    if not isinstance(h_matrix_prototype, HMatrixPrototype):
        raise ValueError(
            "h_matrix_prototype must be an HMatrixPrototype instance"
        )
    if not isinstance(boundary_solution, RegularizedSolvePrototype):
        raise ValueError(
            "boundary_solution must be a RegularizedSolvePrototype instance"
        )

    # --- benchmark ID checks ---
    if h_matrix_prototype.benchmark_id != _BID:
        raise ValueError(
            f"h_matrix_prototype.benchmark_id must be {_BID!r}; "
            f"got {h_matrix_prototype.benchmark_id!r}"
        )
    if boundary_solution.benchmark_id != _BID:
        raise ValueError(
            f"boundary_solution.benchmark_id must be {_BID!r}; "
            f"got {boundary_solution.benchmark_id!r}"
        )

    # --- dimension compatibility ---
    n_obs = h_matrix_prototype.observer_count
    n_pan = h_matrix_prototype.panel_count
    n_sol = len(boundary_solution.solution)
    if n_pan != n_sol:
        raise ValueError(
            f"Dimension mismatch: H has {n_pan} columns (panels) but "
            f"boundary solution vector has length {n_sol}"
        )

    # --- incident pressure ---
    if incident_pressure is not None:
        if len(incident_pressure) != n_obs:
            raise ValueError(
                f"incident_pressure length {len(incident_pressure)} does not match "
                f"observer_count {n_obs}"
            )
        p_inc = list(incident_pressure)
        inc_supplied = True
    else:
        p_inc = [0j] * n_obs
        inc_supplied = False

    # --- H @ x  (pure Python, no new dependency) ---
    x = boundary_solution.solution
    H = h_matrix_prototype.h_matrix
    p_scat = [
        sum(H[i][j] * x[j] for j in range(n_pan))
        for i in range(n_obs)
    ]

    # --- total pressure ---
    p_total = [p_inc[i] + p_scat[i] for i in range(n_obs)]

    # --- deterministic package ID ---
    id_lines = [
        "reconstruction_stage=bem006b_gated_exterior_reconstruction",
        f"benchmark_id={_BID}",
        f"h_matrix_package_id={h_matrix_prototype.deterministic_package_id}",
        f"boundary_solution_package_id={boundary_solution.deterministic_package_id}",
        f"incident_pressure_supplied={inc_supplied}",
    ]
    for v in p_scat:
        id_lines.append(f"{v.real:.15e}+{v.imag:.15e}j")
    package_id = hashlib.sha256(
        "\n".join(id_lines).encode("utf-8")
    ).hexdigest()

    return ReconstructedObserverPressure(
        reconstruction_stage="bem006b_gated_exterior_reconstruction",
        benchmark_id=_BID,
        observer_count=n_obs,
        panel_count=n_pan,
        reconstructed_incident_pressure=p_inc,
        reconstructed_scattered_pressure=p_scat,
        reconstructed_total_pressure=p_total,
        incident_pressure_supplied=inc_supplied,
        physical_h_matrix_assembled=True,
        physical_reconstruction_performed=True,
        singular_quadrature_implemented=False,
        analytical_reference_comparison_performed=False,
        tolerance_policy_applied=False,
        spl_computed=False,
        directivity_computed=False,
        impedance_computed=False,
        non_physical=True,
        h_matrix_package_id=h_matrix_prototype.deterministic_package_id,
        boundary_solution_package_id=boundary_solution.deterministic_package_id,
        deterministic_package_id=package_id,
    )

# ============================================================================
# BEM-006C: Pipeline integration report (expected-failure comparison)
# ============================================================================


@dataclass
class PipelineIntegrationReport:
    """
    BEM-006C pipeline integration expected-failure report.

    Connects BEM-006B's real numerical reconstructed pressure arrays to the
    BEM-005C-style analytical matching pipeline.  The benchmark deterministically
    fails because the prototype is based on a toy 3–6 panel regular-only
    reconstruction and is not a validated full BEM solve.

    This failure is expected and correct.  It is not a software defect.
    """
    validation_stage: str
    benchmark_id: str
    observer_count: int
    relative_l2_error: float
    max_abs_error: float
    relative_pressure_tolerance: float
    absolute_pressure_tolerance: float
    benchmark_passed: bool
    numerical_data_consumed: bool
    analytical_reference_matched: bool
    tolerance_policy_applied: bool
    error_norms_computed: bool
    physical_h_matrix_assembled: bool
    singular_quadrature_implemented: bool
    non_physical_prototype_warning: bool
    spl_computed: bool
    directivity_computed: bool
    impedance_computed: bool
    reconstruction_package_id: str
    analytical_package_id: str
    deterministic_package_id: str


def build_pipeline_integration_report(
    analytical_package: dict,
    reconstructed_pressure: "ReconstructedObserverPressure",
) -> PipelineIntegrationReport:
    """
    Integrate BEM-006B reconstructed pressure into the analytical matching
    pipeline and return an expected-failure report.

    Computes:
        relative_l2_error = ||p_anal_total - p_rec_total||_2 / ||p_anal_total||_2
        max_abs_error     = max(|p_anal_total[i] - p_rec_total[i]|)

    The benchmark deterministically fails because the reconstructed pressure
    comes from a regular-only 3–6 panel prototype with an artificially
    regularized boundary solution, not a validated full BEM solve.

    Parameters
    ----------
    analytical_package : dict
        Package returned by AnalyticalRigidSphereReferenceEvaluator.evaluate().
        Must contain: "total_pressure", "metadata" (with "benchmark_id"),
        "package_id".
    reconstructed_pressure : ReconstructedObserverPressure
        BEM-006B gated exterior reconstruction result.

    Returns
    -------
    PipelineIntegrationReport

    Raises
    ------
    ValueError
        On type error, benchmark ID mismatch, length mismatch, or zero
        analytical norm.
    """
    _BID = "ben004_rigid_sphere_scattering_registered"
    _REL_TOL = 1.0e-2
    _ABS_TOL = 1.0e-6

    # --- type guards ---
    if not isinstance(analytical_package, dict):
        raise ValueError(
            "analytical_package must be a dict from "
            "AnalyticalRigidSphereReferenceEvaluator.evaluate()"
        )
    for key in ("metadata", "total_pressure", "package_id"):
        if key not in analytical_package:
            raise ValueError(
                f"analytical_package missing required key: {key!r}"
            )
    if not isinstance(reconstructed_pressure, ReconstructedObserverPressure):
        raise ValueError(
            "reconstructed_pressure must be a ReconstructedObserverPressure instance"
        )

    # --- benchmark ID checks ---
    anal_bid = analytical_package["metadata"].get("benchmark_id", "")
    if anal_bid != _BID:
        raise ValueError(
            f"analytical_package benchmark_id must be {_BID!r}; got {anal_bid!r}"
        )
    if reconstructed_pressure.benchmark_id != _BID:
        raise ValueError(
            f"reconstructed_pressure.benchmark_id must be {_BID!r}; "
            f"got {reconstructed_pressure.benchmark_id!r}"
        )

    # --- extract and check pressure arrays ---
    p_anal = list(analytical_package["total_pressure"])
    p_rec  = list(reconstructed_pressure.reconstructed_total_pressure)

    if len(p_anal) != len(p_rec):
        raise ValueError(
            f"Pressure array length mismatch: analytical has {len(p_anal)} "
            f"points, reconstructed has {len(p_rec)} points"
        )

    n = len(p_anal)

    # --- assert numerical data was consumed (non-zero reconstruction) ---
    # This flag documents that we are using real H@x output, not the
    # BEM-005B gated-zero placeholders.
    numerical_data_consumed = reconstructed_pressure.physical_reconstruction_performed

    # --- compute error norms ---
    norm_anal_sq = sum(abs(v) ** 2 for v in p_anal)
    norm_anal = math.sqrt(norm_anal_sq)
    if norm_anal == 0.0:
        raise ValueError(
            "Analytical total pressure norm is zero; relative_l2_error is "
            "undefined.  Ensure a non-trivial analytical field is evaluated."
        )

    diff = [p_anal[i] - p_rec[i] for i in range(n)]
    norm_diff = math.sqrt(sum(abs(d) ** 2 for d in diff))
    relative_l2_error = norm_diff / norm_anal
    max_abs_error = max(abs(d) for d in diff)

    # --- tolerance policy (benchmark expected to fail) ---
    benchmark_passed = (relative_l2_error <= _REL_TOL) and (max_abs_error <= _ABS_TOL)

    # --- deterministic package ID ---
    id_lines = [
        "validation_stage=bem006c_pipeline_integration_report",
        f"benchmark_id={_BID}",
        f"analytical_package_id={analytical_package['package_id']}",
        f"reconstruction_package_id={reconstructed_pressure.deterministic_package_id}",
        f"relative_l2_error={relative_l2_error!r}",
        f"max_abs_error={max_abs_error!r}",
    ]
    package_id = hashlib.sha256(
        "\n".join(id_lines).encode("utf-8")
    ).hexdigest()

    return PipelineIntegrationReport(
        validation_stage="bem006c_pipeline_integration_report",
        benchmark_id=_BID,
        observer_count=n,
        relative_l2_error=relative_l2_error,
        max_abs_error=max_abs_error,
        relative_pressure_tolerance=_REL_TOL,
        absolute_pressure_tolerance=_ABS_TOL,
        benchmark_passed=benchmark_passed,
        numerical_data_consumed=numerical_data_consumed,
        analytical_reference_matched=True,
        tolerance_policy_applied=True,
        error_norms_computed=True,
        physical_h_matrix_assembled=True,
        singular_quadrature_implemented=False,
        non_physical_prototype_warning=True,
        spl_computed=False,
        directivity_computed=False,
        impedance_computed=False,
        reconstruction_package_id=reconstructed_pressure.deterministic_package_id,
        analytical_package_id=analytical_package["package_id"],
        deterministic_package_id=package_id,
    )

# BEGIN BEM-007B REGULAR OFF-DIAGONAL QUADRATURE PROTOTYPE
import cmath as _bem007b_cmath
import hashlib as _bem007b_hashlib
import json as _bem007b_json
import math as _bem007b_math

BEM007B_REGULAR_QUADRATURE_METADATA = {
    "quadrature_stage": "bem007b_regular_off_diagonal_prototype",
    "benchmark_id": "ben004_rigid_sphere_scattering_registered",
    "regular_quadrature_implemented": True,
    "singular_quadrature_implemented": False,
    "physical_a_matrix_assembled": False,
    "adaptive_integration_used": False,
    "flat_panels_only": True,
    "benchmark_passed": False,
    "non_physical": True,
}

_BEM007B_REFERENCE_TRIANGLE_RULE = (
    ((1.0 / 3.0, 1.0 / 3.0, 1.0 / 3.0), 0.11250000000000000),
    ((0.47014206410511505, 0.47014206410511505, 0.05971587178976981), 0.06619707639425308),
    ((0.47014206410511505, 0.05971587178976981, 0.47014206410511505), 0.06619707639425308),
    ((0.05971587178976981, 0.47014206410511505, 0.47014206410511505), 0.06619707639425308),
    ((0.10128650732345634, 0.10128650732345634, 0.79742698535308720), 0.06296959027241357),
    ((0.10128650732345634, 0.79742698535308720, 0.10128650732345634), 0.06296959027241357),
    ((0.79742698535308720, 0.10128650732345634, 0.10128650732345634), 0.06296959027241357),
)


def bem007b_regular_triangle_quadrature_rule():
    """Return the fixed regular triangle rule used by BEM-007B.

    Weights are expressed on the reference triangle whose area is 0.5.
    The physical integral is obtained by multiplying each reference weight
    by the physical triangle Jacobian, i.e. ``2 * physical_area``.
    """

    return tuple((tuple(barycentric), float(weight)) for barycentric, weight in _BEM007B_REFERENCE_TRIANGLE_RULE)


def _bem007b_as_point3(value, label):
    if not isinstance(value, (list, tuple)) or len(value) != 3:
        raise ValueError(f"{label} must be a 3D point")
    try:
        point = tuple(float(component) for component in value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{label} must contain finite numeric coordinates") from exc
    if not all(_bem007b_math.isfinite(component) for component in point):
        raise ValueError(f"{label} must contain finite numeric coordinates")
    return point


def _bem007b_subtract(a, b):
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def _bem007b_cross(a, b):
    return (
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    )


def _bem007b_norm(a):
    return _bem007b_math.sqrt(a[0] * a[0] + a[1] * a[1] + a[2] * a[2])


def _bem007b_triangle_jacobian(vertices):
    edge_01 = _bem007b_subtract(vertices[1], vertices[0])
    edge_02 = _bem007b_subtract(vertices[2], vertices[0])
    return _bem007b_norm(_bem007b_cross(edge_01, edge_02))


def _bem007b_validate_triangle(panel, label):
    if not isinstance(panel, (list, tuple)) or len(panel) != 3:
        raise ValueError(f"{label} must be exactly one flat triangular panel with 3 vertices")
    vertices = tuple(_bem007b_as_point3(vertex, f"{label}[{index}]") for index, vertex in enumerate(panel))
    jacobian = _bem007b_triangle_jacobian(vertices)
    if jacobian <= 1.0e-14:
        raise ValueError(f"{label} is degenerate and cannot be used for regular quadrature")
    return vertices


def _bem007b_centroid(vertices):
    return (
        (vertices[0][0] + vertices[1][0] + vertices[2][0]) / 3.0,
        (vertices[0][1] + vertices[1][1] + vertices[2][1]) / 3.0,
        (vertices[0][2] + vertices[1][2] + vertices[2][2]) / 3.0,
    )


def _bem007b_barycentric_point(vertices, barycentric):
    return (
        barycentric[0] * vertices[0][0] + barycentric[1] * vertices[1][0] + barycentric[2] * vertices[2][0],
        barycentric[0] * vertices[0][1] + barycentric[1] * vertices[1][1] + barycentric[2] * vertices[2][1],
        barycentric[0] * vertices[0][2] + barycentric[1] * vertices[1][2] + barycentric[2] * vertices[2][2],
    )


def _bem007b_point_distance(a, b):
    return _bem007b_norm(_bem007b_subtract(a, b))


def _bem007b_panels_share_vertex(source_vertices, target_vertices):
    for source in source_vertices:
        for target in target_vertices:
            if _bem007b_point_distance(source, target) <= 1.0e-12:
                return True
    return False


def _bem007b_normalized_number(value):
    return format(float(value), ".17g")


def _bem007b_normalized_panel(vertices):
    return [[_bem007b_normalized_number(component) for component in vertex] for vertex in vertices]


def _bem007b_package_id(source_vertices, target_vertices, wavenumber, rule_id):
    payload = {
        "contract": "bem007b_regular_off_diagonal_triangle_quadrature",
        "source_panel": _bem007b_normalized_panel(source_vertices),
        "target_panel": _bem007b_normalized_panel(target_vertices),
        "wavenumber": _bem007b_normalized_number(wavenumber),
        "rule_id": rule_id,
        "metadata": BEM007B_REGULAR_QUADRATURE_METADATA,
    }
    encoded = _bem007b_json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return _bem007b_hashlib.sha256(encoded).hexdigest()


def evaluate_regular_off_diagonal_triangle_quadrature(source_panel, target_panel, wavenumber):
    """Evaluate a regular indirect single-layer source-panel integral.

    The target collocation point is the centroid of ``target_panel``.  This is
    a pairwise regular off-diagonal utility only.  It rejects self/coincident
    and vertex-touching panels instead of attempting singular or near-singular
    treatment.
    """

    source_vertices = _bem007b_validate_triangle(source_panel, "source_panel")
    target_vertices = _bem007b_validate_triangle(target_panel, "target_panel")
    try:
        k = float(wavenumber)
    except (TypeError, ValueError) as exc:
        raise ValueError("wavenumber must be a finite numeric value") from exc
    if not _bem007b_math.isfinite(k):
        raise ValueError("wavenumber must be a finite numeric value")

    if source_vertices == target_vertices:
        raise ValueError("regular off-diagonal quadrature requires distinct source and target panels")
    if _bem007b_panels_share_vertex(source_vertices, target_vertices):
        raise ValueError("regular off-diagonal quadrature rejects touching or coincident panels")

    target_point = _bem007b_centroid(target_vertices)
    source_jacobian = _bem007b_triangle_jacobian(source_vertices)
    rule = bem007b_regular_triangle_quadrature_rule()
    value = 0.0 + 0.0j
    minimum_distance = float("inf")

    for barycentric, reference_weight in rule:
        source_point = _bem007b_barycentric_point(source_vertices, barycentric)
        radius = _bem007b_point_distance(target_point, source_point)
        minimum_distance = min(minimum_distance, radius)
        if radius <= 1.0e-12:
            raise ValueError("regular off-diagonal quadrature encountered a non-regular collocation distance")
        green = _bem007b_cmath.exp(1j * k * radius) / (4.0 * _bem007b_math.pi * radius)
        value += reference_weight * source_jacobian * green

    rule_id = "dunavant_degree5_reference_area_0p5_fixed7"
    return {
        "value": value,
        "package_id": _bem007b_package_id(source_vertices, target_vertices, k, rule_id),
        "metadata": dict(BEM007B_REGULAR_QUADRATURE_METADATA),
        "quadrature_rule_id": rule_id,
        "reference_weight_sum": sum(weight for _, weight in rule),
        "source_area": 0.5 * source_jacobian,
        "target_collocation_point": target_point,
        "minimum_collocation_distance": minimum_distance,
    }


# Explicit milestone alias for tests and future grep-based audits.
bem007b_evaluate_regular_off_diagonal_triangle_quadrature = evaluate_regular_off_diagonal_triangle_quadrature
# END BEM-007B REGULAR OFF-DIAGONAL QUADRATURE PROTOTYPE

