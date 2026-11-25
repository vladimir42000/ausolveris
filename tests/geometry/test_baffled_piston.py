import numpy as np
import pytest

from ausolveris.geometry.baffled_piston import baffled_piston_pressure


@pytest.mark.parametrize("frequency", [1000, 10000, 30000])
def test_complex_axial_pressure_matches_exact_disk_solution(frequency):
    a, c, rho = 0.0127, 343, 1.21
    v = 0.2 - 0.7j
    k = 2 * np.pi * frequency / c
    z = np.array([0.001, 0.02, 0.3, 1.0])
    points = np.column_stack((0 * z, 0 * z, z))
    expected = rho * c * v * (np.exp(1j * k * z) - np.exp(1j * k * np.hypot(z, a)))
    np.testing.assert_allclose(baffled_piston_pressure(a, frequency, v, points), expected,
                               rtol=2e-10)


def test_near_field_against_independent_source_centred_surface_integration():
    a, f = 0.0127, 30000
    nodes, weights = np.polynomial.legendre.leggauss(48)
    radial = a * (nodes[:, None] + 1) / 2
    phi = 2 * np.pi * np.arange(256) / 256
    x, y = radial * np.cos(phi), radial * np.sin(phi)
    k = 2 * np.pi * f / 343
    points = np.array([(0.004, 0, 0.005), (0, a, 0.003), (0.021, -0.003, 0.004)])
    reference = []
    for mx, my, mz in points:
        r = np.sqrt((mx-x)**2 + (my-y)**2 + mz**2)
        rings = (np.exp(1j * k * r) / r).mean(axis=1)
        reference.append(-1j * 2 * np.pi * f * 1.21 * a / 2 * (weights * radial[:, 0]) @ rings)
    np.testing.assert_allclose(baffled_piston_pressure(a, f, 1, points), reference, rtol=1e-9)


def test_30khz_far_field_including_first_null_and_reversed_phase():
    # Independent 2*J1(x)/x values, x=ka sin(theta), evaluated with scipy.special.
    angles = np.deg2rad([0, 15, 30, 33.29922501165883, 45, 60, 75, 89])
    expected = [1, 0.643961186641, 0.081224141728, 0, -0.129520170513,
                -0.088597584036, -0.024591846664, -0.003222065472]
    points = 100 * np.column_stack((np.sin(angles), 0 * angles, np.cos(angles)))
    p = baffled_piston_pressure(0.0127, 30000, 1, points)
    np.testing.assert_allclose(p / p[0], expected, atol=1e-4, rtol=0)


@pytest.mark.parametrize("frequency, z", [(0, 1), (50000, 1), (1000, -1)])
def test_rejects_out_of_domain_inputs(frequency, z):
    with pytest.raises(ValueError):
        baffled_piston_pressure(0.0127, frequency, 1, [(0, 0, z)])
