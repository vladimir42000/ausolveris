import math

import numpy as np
import pytest

from ausolveris.geometry.neumann import separated_neumann_panel_integral


SOURCE = ((-1, -1, 0), (1, -1, 0), (1, 1, 0))
TARGET = ((-1, -1, 4), (1, 0, 4), (0, 1, 4))
TILTED = ((-1, -1, 3), (1, 0, 5), (0, 1, 4))


def test_static_half_square_solid_angle():
    # At the square axis each diagonal half subtends half its solid angle.
    z = 4
    expected = -math.atan(1 / (z * math.sqrt(z*z + 2))) / (2 * math.pi)
    assert separated_neumann_panel_integral(SOURCE, TARGET, 0) == pytest.approx(
        expected, rel=1e-5
    )


def reference_pressure_derivative(k, depth):
    # Subdivide the physical source into four similar triangles at each level.
    # Integrate scalar pressure at displaced receivers, then difference it.
    tiles = np.array([SOURCE], dtype=float)
    for _ in range(depth):
        a, b, c = tiles.transpose(1, 0, 2)
        ab, bc, ca = (a+b)/2, (b+c)/2, (c+a)/2
        tiles = np.concatenate([np.stack(vertices, axis=1) for vertices in
                                [(a, ab, ca), (ab, b, bc), (ca, bc, c), (ab, bc, ca)]])
    centers = tiles.mean(axis=1)
    target = np.array(TILTED, dtype=float)
    normal = np.cross(target[1] - target[0], target[2] - target[0])
    normal /= np.linalg.norm(normal)
    step = 1e-5
    def pressure(offset):
        distances = np.linalg.norm(target.mean(axis=0) + offset * normal - centers, axis=1)
        return 2 * np.mean(np.exp(1j * k * distances) / (4 * np.pi * distances))
    return (pressure(step) - pressure(-step)) / (2 * step)


@pytest.mark.parametrize("k", [0.5, 2.0])
def test_complex_integral_against_refined_pressure_difference(k):
    coarse = reference_pressure_derivative(k, 7)
    fine = reference_pressure_derivative(k, 8)
    result = separated_neumann_panel_integral(SOURCE, TILTED, k)
    assert abs(coarse - fine) < 1e-5 * abs(fine)
    assert abs(result - fine) < 2e-4 * abs(fine)


def test_winding_selects_target_normal_only():
    value = separated_neumann_panel_integral(SOURCE, TILTED, 1.0)
    assert separated_neumann_panel_integral(SOURCE[::-1], TILTED, 1.0) == pytest.approx(value)
    assert separated_neumann_panel_integral(SOURCE, TILTED[::-1], 1.0) == pytest.approx(-value)


@pytest.mark.parametrize("panel", [SOURCE, ((1, 1, 0), (2, 1, 0), (1, 2, 0)),
                                   tuple((x, y, 0.01) for x, y, _ in SOURCE)])
def test_self_touching_and_close_pairs_are_declined(panel):
    with pytest.raises(ValueError, match="separated-panel"):
        separated_neumann_panel_integral(SOURCE, panel, 1.0)
