"""Experimental dense exterior Neumann benchmark for a unit sound-hard sphere."""

import numpy as np

from .bem import bem007b_regular_triangle_quadrature_rule
from .benchmark import build_rigid_sphere_benchmark_fixture
from .neumann import exterior_neumann_trace


_RULE = bem007b_regular_triangle_quadrature_rule()
_BARY = np.array([point for point, _ in _RULE])
_WEIGHTS = np.array([weight for _, weight in _RULE])


def _panel_integrals(triangles, target, normal, k):
    """Integrate G or its target-normal derivative for off-surface targets.

    Refine source tiles until their enclosing ball is small relative to both
    target distance and wavelength. Every child keeps its parent panel index.
    """
    indices = np.arange(len(triangles))
    values = np.zeros(len(triangles), dtype=complex)
    for depth in range(15):
        centers = triangles.mean(axis=1)
        radius = np.linalg.norm(triangles - centers[:, None], axis=2).max(axis=1)
        distance = np.linalg.norm(target - centers, axis=1)
        refine = (distance < 4 * radius) | (k * radius > 0.5)
        tiles = triangles[~refine]
        if len(tiles):
            sources = np.einsum('qv,tvc->tqc', _BARY, tiles)
            delta = target - sources
            r = np.linalg.norm(delta, axis=2)
            kernel = np.exp(1j * k * r) / (4 * np.pi * r)
            if normal is not None:
                kernel *= ((1j * k - 1 / r) / r) * (delta @ normal)
            jacobian = np.linalg.norm(np.cross(tiles[:, 1] - tiles[:, 0],
                                               tiles[:, 2] - tiles[:, 0]), axis=1)
            np.add.at(values, indices[~refine], jacobian * (kernel @ _WEIGHTS))
        if not refine.any():
            return values
        if depth == 14:
            raise ValueError("Panel integral exceeded refinement limit")
        a, b, c = triangles[refine].transpose(1, 0, 2)
        ab, bc, ca = (a + b) / 2, (b + c) / 2, (c + a) / 2
        triangles = np.concatenate([np.stack(vertices, axis=1) for vertices in
                                    [(a, ab, ca), (ab, b, bc), (ca, bc, c), (ab, bc, ca)]])
        indices = np.tile(indices[refine], 4)


def rigid_sphere_scattered_pressure(k, subdivision_level, observers):
    """Return complex scattered Pa for a 1 Pa plane wave travelling along +x.

    Uses a unit-radius sphere at the origin, outward flat panels and constant
    densities. Intended for small benchmark meshes away from interior resonances.
    """
    if not np.isfinite(k) or not 0 < k <= 2:
        raise ValueError("Unit-sphere benchmark supports 0 < ka <= 2")
    if not isinstance(subdivision_level, (int, np.integer)) or not 0 <= subdivision_level <= 3:
        raise ValueError("Supported benchmark levels are 0 through 3")
    observers = np.asarray(observers, dtype=float)
    if (observers.ndim != 2 or observers.shape[1] != 3 or not np.isfinite(observers).all()
            or np.any(np.linalg.norm(observers, axis=1) <= 1)):
        raise ValueError("Expected exterior observer coordinates")
    fixture = build_rigid_sphere_benchmark_fixture(
        "ben004_rigid_sphere_scattering_registered", subdivision_level=subdivision_level)
    triangles = np.array(fixture.vertices)[[p.vertex_indices for p in fixture.panels]]
    normals = np.array([p.outward_normal for p in fixture.panels])
    centers = triangles.mean(axis=1)
    matrix = np.empty((len(centers), len(centers)), dtype=complex)
    for index, (target, normal) in enumerate(zip(centers, normals)):
        other = np.arange(len(centers)) != index
        matrix[index, other] = _panel_integrals(triangles[other], target, normal, k)
        matrix[index, index] = exterior_neumann_trace(0, 1)
    rhs = -1j * k * normals[:, 0] * np.exp(1j * k * centers[:, 0])
    density = np.linalg.solve(matrix, rhs)
    return np.array([_panel_integrals(triangles, target, None, k) @ density
                     for target in observers])
