import math

import numpy as np
import pytest

from ausolveris.geometry.bem import helmholtz_green_function
from ausolveris.geometry.neumann import exterior_neumann_trace, target_normal_derivative


def test_static_axial_point_source():
    value = target_normal_derivative((0, 0, 2), (0, 0, 0), (0, 0, 1), 0)
    assert value == pytest.approx(-1 / (16 * math.pi))
    assert target_normal_derivative((0, 0, 2), (0, 0, 0), (1, 0, 0), 0) == 0


def test_oblique_wave_kernel_against_target_displacement():
    target = np.array([1.0, -0.4, 2.0])
    source = np.array([0.2, 0.3, -0.1])
    normal = np.array([0.6, 0.0, 0.8])
    k = 2.75
    h = 1e-5

    def pressure(offset):
        return helmholtz_green_function(math.dist(target + offset * normal, source), k)

    derivative = (pressure(h) - pressure(-h)) / (2 * h)
    assert target_normal_derivative(target, source, normal, k) == pytest.approx(
        derivative, rel=1e-8
    )


def test_flat_panel_self_interaction_at_centroid():
    normal = (0, 0, 1)
    centroid = (1 / 3, 1 / 3, 0)
    assert target_normal_derivative(centroid, (0.2, 0.1, 0), normal, 2) == 0
    with pytest.raises(ValueError, match="positive"):
        target_normal_derivative(centroid, centroid, normal, 2)
    assert exterior_neumann_trace(0, 2 + 3j) == -1 - 1.5j


@pytest.mark.parametrize("radius", [0.5, 2.0])
def test_static_uniform_sphere_traces(radius):
    # Integrate K' at the north pole. Use axial symmetry and u = sin(theta/2),
    # so the ring area is 8*pi*a^2*u du and the singular endpoint is excluded.
    nodes, weights = np.polynomial.legendre.leggauss(12)
    principal_value = 0j
    for node, weight in zip(nodes, weights):
        u = (node + 1) / 2
        source = (2 * radius * u * math.sqrt(1 - u*u), 0, radius * (1 - 2*u*u))
        kernel = target_normal_derivative((0, 0, radius), source, (0, 0, 1), 0)
        principal_value += kernel * (8 * math.pi * radius**2 * u) * weight / 2

    # The exact potential is a inside and a^2/r outside. Its one-sided
    # derivatives at r=a are 0 and -1 for unit density.
    assert principal_value + 0.5 == pytest.approx(0, abs=1e-12)
    assert exterior_neumann_trace(principal_value, 1) == pytest.approx(-1, abs=1e-12)
