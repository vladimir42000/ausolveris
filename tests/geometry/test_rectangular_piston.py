import numpy as np
from scipy.integrate import dblquad

from ausolveris.geometry.rectangular_piston import rectangular_piston_pressure


def test_far_field_signed_pattern_and_absolute_pressure():
    width, height, hz, radius = .12, .06, 30000, 10000.
    k = 2*np.pi*hz/343.
    first_null = 343./(hz*width)
    directions = np.array([[0., 0.], [first_null, 0.], [1.5*first_null, 0.],
                           [0., first_null], [.13, .21]])
    points = radius*np.column_stack((directions, np.sqrt(1 - (directions**2).sum(axis=1))))
    p = rectangular_piston_pressure(width, height, hz, 1j, points)
    axial = 1.21*hz*width*height*np.exp(1j*k*radius)/radius
    expected = np.sinc(hz*width*directions[:, 0]/343.)*np.sinc(hz*height*directions[:, 1]/343.)
    np.testing.assert_allclose(p/axial, expected, atol=5e-5, rtol=0)


def test_near_field_off_axis():
    width, height, hz = .12, .06, 1200.
    x, y, z = .042, -.018, .015
    def kernel(v, u):
        distance = np.sqrt((x-u)**2 + (y-v)**2 + z**2)
        return np.exp(2j*np.pi*hz*distance/343.)/distance
    def integrate(part):
        return dblquad(lambda v, u: part(kernel(v, u)), -width/2, width/2,
                       -height/2, height/2)[0]
    expected = -1j*1.21*hz*(integrate(np.real) + 1j*integrate(np.imag))
    actual = rectangular_piston_pressure(width, height, hz, 1., [[x, y, z]])
    np.testing.assert_allclose(actual, expected, rtol=1e-8)


def test_small_patch_batch_matches_independent_point_integrals():
    # Exercise several batches and both off-axis directions.
    width, height, hz = .003, .0015, 30000.
    theta = np.linspace(0, 1.4, 259)
    points = np.column_stack((.1*np.sin(theta), .04*np.sin(2*theta), .1*np.cos(theta)))
    pressure = rectangular_piston_pressure(width, height, hz, 1j, points)
    for index in (0, 128, 258):
        x, y, z = points[index]
        def kernel(v, u):
            distance = np.sqrt((x-u)**2 + (y-v)**2 + z*z)
            return np.exp(2j*np.pi*hz*distance/343.)/distance
        def integrate(part):
            return dblquad(lambda v, u: part(kernel(v, u)), -width/2, width/2,
                           -height/2, height/2)[0]
        expected = 1.21*hz*(integrate(np.real) + 1j*integrate(np.imag))
        np.testing.assert_allclose(pressure[index], expected, rtol=1e-10)
