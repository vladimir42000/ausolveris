import unittest
from dataclasses import replace

import numpy as np

try:
    from os_lem.model import Driver
except ModuleNotFoundError as error:
    if error.name != "os_lem":
        raise
    Driver = None


@unittest.skipIf(Driver is None, "requires the optional OS-LEM kernel")
class DrivenHornTest(unittest.TestCase):
    def setUp(self):
        from ausolveris.geometry.driven_round_horn import solve_driven_round_horn
        self.solve = solve_driven_round_horn
        self.profile = [(0., .0127), (.12, .06)]
        self.driver = Driver("motor", 6., .0001, 4., .002, .0003, 1., np.pi*.0127**2,
                             "front", "rear", 1.)

    def test_impedance_and_radiated_power(self):
        d = self.driver
        for frequency in (1000, 6000):
            with self.subTest(frequency=frequency):
                r = self.solve(self.profile, frequency, d)
                omega = 2*np.pi*frequency
                zm = d.Rms - 1j*(omega*d.Mms - 1/(omega*d.Cms))
                expected = d.Re - 1j*omega*d.Le + d.Bl**2/(zm + d.Sd**2*r.unit_horn.throat_impedance)
                np.testing.assert_allclose(r.electrical_impedance, expected)
                h, v = r.unit_horn, r.throat_velocity_rms
                areas = np.pi*np.diff(h.mouth_edges_m**2)
                mouth_power = areas @ (h.mouth_pressure_pa * h.mouth_velocity_m_s.conj()).real * abs(v)**2
                input_power = (d.source_voltage_rms*r.current_rms.conj()).real
                losses = d.Re*abs(r.current_rms)**2 + d.Rms*abs(v)**2
                self.assertGreater(mouth_power, 0)
                np.testing.assert_allclose(input_power - losses, mouth_power, rtol=1e-8)

    def test_voltage_scaling_and_complex_pressure(self):
        a = self.solve(self.profile, 1000, self.driver)
        b = self.solve(self.profile, 1000, replace(self.driver, source_voltage_rms=2.))
        observers = [[0, 0, 1], [.6, 0, .8]]
        p = a.exterior_pressure_rms(observers)
        np.testing.assert_allclose(b.exterior_pressure_rms(observers), 2*p)
        from ausolveris.geometry.round_horn import solve_round_horn
        driven = solve_round_horn(self.profile, 1000, throat_velocity=a.throat_velocity_rms*np.sqrt(2))
        np.testing.assert_allclose(p, driven.exterior_pressure(observers)/np.sqrt(2))

    def test_area_mismatch(self):
        with self.assertRaisesRegex(ValueError, "area"):
            self.solve(self.profile, 1000, replace(self.driver, Sd=self.driver.Sd*2))
