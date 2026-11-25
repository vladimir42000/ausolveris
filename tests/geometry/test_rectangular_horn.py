import numpy as np

from ausolveris.geometry.rectangular_duct import solve_rectangular_duct
from ausolveris.geometry.rectangular_horn import solve_rectangular_horn


def test_constant_section_agrees_with_finite_volume_duct():
    section = (.12, .06)
    fem = solve_rectangular_horn(section, section, .12, 1000)
    fv = solve_rectangular_duct(*section, .12, 1000)
    np.testing.assert_allclose(fem.throat_impedance, fv.throat_impedance, rtol=.012)
    points = [[0, 0, 1], [.6, 0, .8], [0, .6, .8]]
    np.testing.assert_allclose(fem.exterior_pressure(points), fv.exterior_pressure(points), rtol=.008)


def test_flare_conserves_power_and_exchanges_principal_cuts_on_rotation():
    throat, mouth = (.025, .020), (.120, .060)
    a = solve_rectangular_horn(throat, mouth, .12, 6000, cells=(4, 2, 24))
    b = solve_rectangular_horn(throat[::-1], mouth[::-1], .12, 6000, cells=(2, 4, 24))
    power = np.prod(mouth)*np.mean((a.mouth_pressure_pa*a.mouth_velocity_m_s.conj()).real)
    assert power > 0
    np.testing.assert_allclose(power, a.throat_impedance.real*np.prod(throat)**2, rtol=1e-9)
    np.testing.assert_allclose(a.mouth_velocity_m_s, b.mouth_velocity_m_s.T, rtol=1e-9)
    points = np.array([[.5, 0, .866], [0, .5, .866]])
    np.testing.assert_allclose(a.exterior_pressure(points), b.exterior_pressure(points[::-1]), rtol=1e-9)
