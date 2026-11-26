"""Neumann reference operators for centroid collocation with body-outward normals."""

import math

from .bem import (
    _bem007b_barycentric_point,
    _bem007b_centroid,
    _bem007b_cross,
    _bem007b_subtract,
    _bem007b_triangle_jacobian,
    _bem007b_validate_triangle,
    bem007b_regular_triangle_quadrature_rule,
    helmholtz_green_function,
)


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


def separated_neumann_panel_integral(source_panel, target_panel, k_rad_m):
    """Integrate the target-normal derivative for unit, constant source density.

    The target is its panel centroid. Target vertex winding sets the normal.
    The composite rule applies seven points on each of four equal-area tiles.
    It accepts disjoint centroid bounding balls with
    a target point at least two source radii from the source centroid. This
    conservative far-panel test may decline valid disjoint pairs. Accuracy
    also depends on wavelength relative to source panel size.
    """
    source = _bem007b_validate_triangle(source_panel, "source_panel")
    target = _bem007b_validate_triangle(target_panel, "target_panel")
    source_center = _bem007b_centroid(source)
    target_center = _bem007b_centroid(target)
    source_radius = max(math.dist(v, source_center) for v in source)
    target_radius = max(math.dist(v, target_center) for v in target)
    distance = math.dist(source_center, target_center)
    if distance <= source_radius + target_radius or distance < 2 * source_radius:
        raise ValueError("Pair outside the separated-panel quadrature domain")

    normal = _bem007b_cross(_bem007b_subtract(target[1], target[0]),
                            _bem007b_subtract(target[2], target[0]))
    normal_length = math.hypot(*normal)
    unit_normal = tuple(component / normal_length for component in normal)
    a, b, c = source
    ab, bc, ca = (tuple((x + y) / 2 for x, y in zip(start, end))
                  for start, end in ((a, b), (b, c), (c, a)))
    tiles = ((a, ab, ca), (ab, b, bc), (ca, bc, c), (ab, bc, ca))
    tile_jacobian = _bem007b_triangle_jacobian(source) / 4
    rule = bem007b_regular_triangle_quadrature_rule()
    integral = 0j
    for tile in tiles:
        for barycentric, weight in rule:
            point = _bem007b_barycentric_point(tile, barycentric)
            integral += weight * target_normal_derivative(
                target_center, point, unit_normal, k_rad_m
            )
    return tile_jacobian * integral
