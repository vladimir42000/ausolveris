import numpy as np
import pytest

from ausolveris.geometry.rectangular_duct import solve_rectangular_duct


def test_plane_average_and_independent_radiation_power():
    width, height, length, hz = .12, .06, .12, 1000.
    duct = solve_rectangular_duct(width, height, length, hz, cells=(8, 4, 48))
    p, v = duct.mouth_pressure_pa, duct.mouth_velocity_m_s
    k = 2*np.pi*hz/duct.sound_speed
    rc = duct.density*duct.sound_speed
    area = width*height
    inlet_pressure = np.cos(k*length)*p.mean() - 1j*rc*np.sin(k*length)*v.mean()
    np.testing.assert_allclose(area*duct.throat_impedance, inlet_pressure, rtol=.002)
    np.testing.assert_allclose(v, v[::-1, ::-1], rtol=1e-10)
    assert np.ptp(abs(v)) > .1*abs(v.mean())

    # Integrate the independent analytical rectangular-patch far field.
    ny, nx = v.shape
    dx, dy = width/nx, height/ny
    y, x = np.indices(v.shape)
    phi = 2*np.pi*np.arange(64)/64
    nodes, weights = np.polynomial.legendre.leggauss(24)
    integral = 0.
    for mu, weight in zip((nodes+1)/2, weights/2):
        ux, uy = np.sqrt(1-mu**2)*np.array([np.cos(phi), np.sin(phi)])
        phase = np.exp(-1j*k*(ux[:, None]*dx*x.ravel() + uy[:, None]*dy*y.ravel()))
        field = dx*dy*(phase @ v.ravel())*np.sinc(k*dx*ux/(2*np.pi))*np.sinc(k*dy*uy/(2*np.pi))
        integral += weight*2*np.pi*np.mean(abs(field)**2)
    power = rc*(k/(2*np.pi))**2*integral
    np.testing.assert_allclose(power, area*np.mean((p*v.conj()).real), rtol=1e-8)


def test_one_volt_electrical_balance():
    Driver = pytest.importorskip("os_lem.model").Driver
    from ausolveris.geometry.driven_round_horn import solve_driven_rectangular_duct
    area = .12*.06
    driver = Driver("illustrative", 6., .0001, 4., .002, .0003, 1., area, "front", "rear", 1.)
    result = solve_driven_rectangular_duct(.12, .06, .12, 3000, driver)
    duct = result.unit_horn
    velocity = result.throat_velocity_rms
    radiation = area*np.mean((duct.mouth_pressure_pa*duct.mouth_velocity_m_s.conj()).real)*abs(velocity)**2
    losses = driver.Re*abs(result.current_rms)**2 + driver.Rms*abs(velocity)**2
    assert radiation > 0
    np.testing.assert_allclose(result.current_rms.real, losses+radiation, rtol=1e-9)
