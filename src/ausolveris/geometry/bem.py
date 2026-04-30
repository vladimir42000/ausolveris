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