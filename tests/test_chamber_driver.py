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
class ChamberDriverTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from ausolveris.geometry.round_horn import solve_round_horn

        cls.profile = [(0., .0127), (.12, .06)]
        cls.hz = 600.
        cls.area = np.pi * cls.profile[0][1]**2
        cls.horn = solve_round_horn(cls.profile, cls.hz)
        cls.driver = Driver("motor", 6., .0001, 4., .002, .0003, 1., 5*cls.area,
                            "front", "rear", 2.)

    def drive(self, front, rear=None, **kwargs):
        from ausolveris.geometry.chamber_driver import drive_chamber_horn

        params = dict(throat_area_m2=self.area, front_volume_m3=front, rear_volume_m3=rear)
        return drive_chamber_horn(self.horn, self.hz, self.driver, **(params | kwargs))

    def test_independent_circuit_and_radiation(self):
        from ausolveris.geometry.round_horn import solve_round_horn

        d, h = self.driver, self.horn
        s = -2j*np.pi*self.hz
        bulk = h.density*h.sound_speed**2
        for rear in (None, 0.0002):
            with self.subTest(rear=rear):
                front = 0.0001
                result = self.drive(front, rear)
                # Independent branch equations for I, piston speed, front pressure,
                # rear pressure and throat volume flow, all in the horn convention.
                mech = d.Rms + s*d.Mms + 1/(s*d.Cms)
                rear_row = [0, d.Sd, 0, s*rear/bulk, 0] if rear else [0, 0, 0, 1, 0]
                matrix = [[d.Re + s*d.Le, d.Bl, 0, 0, 0],
                          [-d.Bl, mech, d.Sd, -d.Sd, 0],
                          [0, -d.Sd, s*front/bulk, 0, 1],
                          rear_row,
                          [0, 0, 1, 0, -h.throat_impedance]]
                current, speed, _, _, flow = np.linalg.solve(matrix, [d.source_voltage_rms, 0, 0, 0, 0])
                np.testing.assert_allclose(
                    [result.current_rms, result.electrical_impedance,
                     result.diaphragm_velocity_rms, result.throat_velocity_rms],
                    [current, d.source_voltage_rms/current, speed, flow/self.area])
                peak = solve_round_horn(self.profile, self.hz, throat_velocity=np.sqrt(2)*flow/self.area)
                points = [[0, 0, 1], [.6, 0, .8]]
                np.testing.assert_allclose(result.exterior_pressure_rms(points),
                                           peak.exterior_pressure(points)/np.sqrt(2))

    def test_zero_front_volume(self):
        from ausolveris.geometry.chamber_driver import drive_chamber_horn
        from ausolveris.geometry.driven_round_horn import _drive

        result = self.drive(0)
        np.testing.assert_allclose(self.area*result.throat_velocity_rms,
                                   self.driver.Sd*result.diaphragm_velocity_rms)

        driver = replace(self.driver, Sd=self.area)
        direct = _drive(self.horn, self.hz, driver, self.area, None)
        chamber = drive_chamber_horn(self.horn, self.hz, driver, throat_area_m2=self.area,
                                     front_volume_m3=0)
        np.testing.assert_allclose(chamber.current_rms, direct.current_rms)
        np.testing.assert_allclose(chamber.throat_velocity_rms, direct.throat_velocity_rms)

    def test_large_front_compliance_limit(self):
        # Formal circuit limit beyond the physical compact-cavity regime.
        result = self.drive(1e5)
        d = self.driver
        s = -2j*np.pi*self.hz
        mech = d.Rms + s*d.Mms + 1/(s*d.Cms)
        unloaded = d.Re + s*d.Le + d.Bl**2/mech
        np.testing.assert_allclose(result.electrical_impedance, unloaded, rtol=1e-8)
        self.assertLess(abs(result.throat_velocity_rms*self.area),
                        1e-8*abs(result.diaphragm_velocity_rms*d.Sd))

    def test_invalid_dimensions(self):
        for params in (dict(front_volume_m3=-1), dict(front_volume_m3=np.nan),
                       dict(throat_area_m2=0), dict(throat_area_m2=np.inf),
                       dict(rear_volume_m3=0)):
            with self.subTest(params=params), self.assertRaises(ValueError):
                self.drive(0, **params)
