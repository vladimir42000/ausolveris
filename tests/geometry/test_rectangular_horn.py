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


def test_quadratic_axial_propagation_at_30khz():
    # In a straight duct the section averages propagate exactly as a plane wave,
    # even with higher transverse modes at the mouth.
    section = (.025, .020)
    length, hz = .12, 30000
    kl = 2*np.pi*hz*length/343.
    errors = []
    for order, cells in [(1, 96), (2, 48), (2, 96)]:
        h = solve_rectangular_horn(section, section, length, hz, axial_order=order,
                                   cells=(4, 3, cells))
        p_in = h.throat_impedance*np.prod(section)
        expected = (np.cos(kl)*h.mouth_pressure_pa.mean()
                    - 1j*h.density*h.sound_speed*np.sin(kl)*h.mouth_velocity_m_s.mean())
        errors.append(abs(p_in-expected)/abs(p_in))
        radiation = np.prod(section)*np.mean((h.mouth_pressure_pa*h.mouth_velocity_m_s.conj()).real)
        np.testing.assert_allclose(radiation, p_in.real*np.prod(section), rtol=1e-9)
    assert errors[1] < errors[0]/5
    assert errors[2] < .012
    assert errors[2] < errors[1]/10


def test_layered_elimination_matches_full_complex_solve():
    for order in (1, 2):
        for nz in (1, 9):
            args = ((.025, .02), (.12, .06), .12, 30000)
            direct = solve_rectangular_horn(*args, cells=(5, 3, nz), axial_order=order)
            layered = solve_rectangular_horn(*args, cells=(5, 3, nz), axial_order=order, layered=True)
            np.testing.assert_allclose(layered.throat_impedance, direct.throat_impedance, rtol=1e-9)
            np.testing.assert_allclose(layered.mouth_velocity_m_s, direct.mouth_velocity_m_s, rtol=1e-9)
