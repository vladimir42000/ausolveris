"""Pointwise reference operators for centroid collocation with body-outward normals."""

import math

from .bem import helmholtz_green_function


def target_normal_derivative(target, source, target_normal, k_rad_m):
    """Evaluate n(x) · grad_x G(x,y) for distinct points in three dimensions."""
    if any(len(vector) != 3 for vector in (target, source, target_normal)):
        raise ValueError("Expected three-dimensional coordinates and normal")
    if not math.isclose(math.hypot(*target_normal), 1.0, rel_tol=1e-12):
        raise ValueError("Expected a unit target normal")

    displacement = tuple(x - y for x, y in zip(target, source))
    radius = math.hypot(*displacement)
    green = helmholtz_green_function(radius, k_rad_m)
    projection = sum(n * (d / radius) for n, d in zip(target_normal, displacement))
    return projection * (1j * k_rad_m - 1.0 / radius) * green


def exterior_neumann_trace(principal_value, density):
    """Apply the exterior jump at a smooth point or inside a flat panel."""
    return principal_value - 0.5 * density
