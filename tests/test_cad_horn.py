from itertools import permutations
import unittest

import numpy as np
from scipy.special import j1, struve

from ausolveris.geometry.cad_horn import prepare_cad_horn, solve_cad_horn


def duct_mesh(width, height, length, layers):
    points = np.array([(x, y, z) for z in np.linspace(0, length, layers + 1)
                       for y in (0, height) for x in (0, width)])
    cells = [[4*i, 4*i+a, 4*i+a+b, 4*i+7] for i in range(layers)
             for a, b, _ in permutations((1, 2, 4))]
    inlet = np.array([[0, 1, 3], [0, 3, 2]])
    return points, cells, inlet, inlet[:, ::-1] + 4*layers


class TestCadHorn(unittest.TestCase):
    def test_straight_duct_transfer_and_power(self):
        width, height, length = .08, .05, .18
        area = width * height
        mesh = duct_mesh(width, height, length, 60)
        for hz in (110., 370., 710.):
            with self.subTest(hz=hz):
                horn = solve_cad_horn(*mesh, hz, density=1.17, sound_speed=340.)
                k = 2*np.pi*hz / 340.
                radius = np.sqrt(area / np.pi)
                ka = k * radius
                rc = 1.17 * 340.
                load = rc * (1 - j1(2*ka)/ka - 1j*struve(1, 2*ka)/ka)
                c, s = np.cos(k*length), np.sin(k*length)
                v = 1 / (c - 1j*s*load/rc)
                p = (c*load - 1j*s*rc) * v
                np.testing.assert_allclose(horn.throat_impedance, p/area, rtol=.002)
                np.testing.assert_allclose(horn.outlet_velocity_m_s, v, rtol=.002)
                power = .5 * area**2 * horn.throat_impedance.real
                self.assertGreater(power, 0)
                np.testing.assert_allclose(power, .5 * area * load.real
                                           * abs(horn.outlet_velocity_m_s)**2, rtol=1e-9)

                # Independent on-axis disk solution and hemisphere power integral.
                z = .07
                expected = rc*v*(np.exp(1j*k*z) - np.exp(1j*k*np.hypot(z, radius)))
                np.testing.assert_allclose(horn.exterior_pressure([[0, 0, z]]), expected, rtol=.002)
                nodes, weights = np.polynomial.legendre.leggauss(12)
                mu = (1 + nodes)/2
                distance = 100.
                observers = distance * np.column_stack((np.sqrt(1-mu**2), 0*mu, mu))
                field = horn.exterior_pressure(observers)
                radiated = np.pi * distance**2 * np.dot(weights, abs(field)**2) / (2*rc)
                np.testing.assert_allclose(radiated, power, rtol=1e-6)

    def test_prepared_mesh_frequency_sweep(self):
        mesh = duct_mesh(.08, .05, .18, 12)
        settings = [(110., 1.21, 343.), (710., 1.17, 340.), (110., 1.21, 343.)]
        expected = [solve_cad_horn(*mesh, hz, density=rho, sound_speed=c)
                    for hz, rho, c in settings]
        prepared = prepare_cad_horn(*mesh)
        # Prepared operators must be independent of the importer's mesh buffers.
        mesh[0][:] = np.nan
        mesh[1].clear()
        mesh[2][:] = 0
        mesh[3][:] = 0
        for (hz, rho, c), reference in zip(settings, expected):
            with self.subTest(hz=hz):
                result = prepared.solve(hz=hz, density=rho, sound_speed=c)
                self.assertEqual(result, reference)

    def test_invalid_volume_topology(self):
        points = np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0], [0, 0, 1],
                           [0, 0, -1], [1, 1, 1], [1, 1, 0], [1, 0, 1]])
        first = [0, 1, 2, 3]
        cases = [
            ("Duplicate", [first, first[::-1]]),
            ("Nonmanifold", [first, [0, 1, 2, 4], [0, 1, 2, 5]]),
            ("Disconnected", [first, [0, 1, 5, 6]]),  # shared edge only
            ("Disconnected", [first, [4, 5, 6, 7]]),  # separate component
        ]
        for error, cells in cases:
            with self.subTest(cells=cells), self.assertRaisesRegex(ValueError, error):
                prepare_cad_horn(points, cells, [[0, 2, 3]], [[1, 2, 3]])

    def test_mesh_frame_and_tetrahedron_winding(self):
        points, cells, inlet, outlet = duct_mesh(.08, .05, .18, 12)
        # Skew and flare the duct, moving the outlet away from the global origin.
        points[:, 0] *= 1 + 2*points[:, 2]
        points[:, 1] += .3*points[:, 2]
        a = solve_cad_horn(points, cells, inlet, outlet, 370.)
        rotated = points[:, [2, 0, 1]] + [3., -2., 1.]
        b = solve_cad_horn(rotated, np.asarray(cells)[:, ::-1], inlet[:, ::-1], outlet, 370.)
        np.testing.assert_allclose(a.throat_impedance, b.throat_impedance, rtol=1e-9)
        observers = [[.01, -.02, .03]]
        np.testing.assert_allclose(a.exterior_pressure(observers), b.exterior_pressure(observers),
                                   rtol=1e-9)

    def test_ports_must_be_distinct_exterior_faces(self):
        points, cells, inlet, outlet = duct_mesh(.1, .1, .2, 2)
        for bad in (inlet, inlet + 4, outlet[[0, 0]]):
            with self.assertRaises(ValueError):
                solve_cad_horn(points, cells, inlet, bad, 300.)


if __name__ == '__main__':
    unittest.main()
