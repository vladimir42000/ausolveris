"""
BEM‑001 : Helmholtz Green‑function utility (scalar, free-space).
BEM‑003 : non‑singular operator prototype (off‑diagonal, controlled subset).

Convention:
    G(r, k) = exp(i * k * r) / (4 * pi * r)
"""

import math
import cmath
import hashlib
from dataclasses import dataclass
from typing import List

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
from dataclasses import field
from typing import Tuple, Optional

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

