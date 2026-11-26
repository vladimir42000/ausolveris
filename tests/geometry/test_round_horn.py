import numpy as np
from scipy.special import j1, struve

from ausolveris.geometry.round_horn import _mouth_load, solve_round_horn


def test_uniform_disk_mean_impedance_matches_bessel_struve_reference():
    edges = np.linspace(0, .06, 9)
    area = np.diff(edges**2)
    for ka in (0.5, 2., 6., 33.):
        actual = area @ _mouth_load(edges, ka/edges[-1]).sum(axis=1) / area.sum()
        exact = 1 - j1(2*ka)/ka - 1j*struve(1, 2*ka)/ka
        np.testing.assert_allclose(actual, exact, rtol=2e-5)


def test_straight_duct_mean_pressure_obeys_lossless_transfer():
    length, radius, f = .12, .025, 1500.
    result = solve_round_horn([(0, radius), (length, radius)], f, axial_cells=100)
    areas = np.pi*np.diff(result.mouth_edges_m**2)
    p_out = areas @ result.mouth_pressure_pa / areas.sum()
    u_out = areas @ result.mouth_velocity_m_s / areas.sum()
    kl = 2*np.pi*f*length/343
    p_in = np.cos(kl)*p_out - 1j*1.21*343*np.sin(kl)*u_out
    np.testing.assert_allclose(result.throat_impedance*areas.sum(), p_in, rtol=.001)
    inlet_power = result.throat_impedance.real*areas.sum()**2/2
    outlet_power = (areas @ (result.mouth_pressure_pa*result.mouth_velocity_m_s.conj())).real/2
    np.testing.assert_allclose(inlet_power, outlet_power, rtol=1e-9)
    assert inlet_power > 0


def test_flare_refinement_and_drive_scaling():
    profile = [[0,.0127],[.12,.060]]
    a = solve_round_horn(profile, 3000, axial_cells=48, radial_cells=8)
    b = solve_round_horn(profile, 3000, throat_velocity=2j, axial_cells=96, radial_cells=16)
    np.testing.assert_allclose(a.throat_impedance, b.throat_impedance, rtol=.015)
    points = [[0,0,1],[.6,0,.8]]
    np.testing.assert_allclose(a.exterior_pressure(points), b.exterior_pressure(points)/(2j), rtol=.015)


def test_annular_power_at_ultrasonic_limit_matches_far_field_integral():
    # Integrate the analytical far field of concentric disk sources over the
    # hemisphere. The mouth operator obtains its power from surface pressure.
    radius = .060
    k = 33 / radius
    edges = np.linspace(0, radius, 17)
    areas = np.pi * np.diff(edges**2)
    velocity = np.exp(3j * edges[1:] / radius) * (1 + edges[1:] / radius)
    surface_power = np.real(np.vdot(velocity, areas * (_mouth_load(edges, k) @ velocity)))

    nodes, weights = np.polynomial.legendre.leggauss(80)
    cos_theta = (nodes + 1) / 2
    sin_theta = np.sqrt(1 - cos_theta**2)
    argument = k * sin_theta[:, None] * edges[None, 1:]
    disk_pattern = np.pi * edges[1:]**2 * 2 * j1(argument) / argument
    jumps = -np.diff(velocity, append=0j)
    # Common factors rho*c/2 cancel from both powers.
    far_power = k**2 / (2*np.pi) * np.dot(weights/2, abs(disk_pattern @ jumps)**2)
    np.testing.assert_allclose(surface_power, far_power, rtol=2e-5)
