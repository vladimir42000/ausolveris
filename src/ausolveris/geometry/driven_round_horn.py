"""Direct piston-to-throat coupling with an open or lumped sealed rear volume."""
from dataclasses import dataclass

import numpy as np
from os_lem.assemble import assemble_system
from os_lem.model import Driver, NormalizedModel
from os_lem.solve import build_coupled_system

from .rectangular_duct import RectangularDuct, solve_rectangular_duct
from .round_horn import RoundHornResult, solve_round_horn


@dataclass
class DrivenRoundHorn:
    # RMS quantities use the horn's exp(-i omega t) convention.
    unit_horn: RoundHornResult | RectangularDuct
    current_rms: complex
    throat_velocity_rms: complex
    electrical_impedance: complex

    def exterior_pressure_rms(self, observers_m):
        return self.unit_horn.exterior_pressure(observers_m) * self.throat_velocity_rms


def solve_driven_round_horn(profile, frequency_hz, driver: Driver, *, rear_volume_m3=None, **mesh):
    """Solve at the RMS drive voltage. None sets rear pressure to zero."""
    horn = solve_round_horn(profile, frequency_hz, throat_velocity=1., **mesh)
    return _drive(horn, frequency_hz, driver, np.pi * profile[0][1]**2, rear_volume_m3)


def solve_driven_rectangular_duct(width_m, height_m, length_m, frequency_hz, driver: Driver,
                                  *, rear_volume_m3=None, **mesh):
    duct = solve_rectangular_duct(width_m, height_m, length_m, frequency_hz, **mesh)
    return _drive(duct, frequency_hz, driver, width_m*height_m, rear_volume_m3)


def _drive(horn, frequency_hz, driver, inlet_area, rear_volume_m3):
    if rear_volume_m3 is not None and (not np.isfinite(rear_volume_m3) or rear_volume_m3 <= 0):
        raise ValueError("Expected positive finite rear volume in cubic metres")
    parameters = (driver.Re, driver.Bl, driver.Mms, driver.Cms, driver.Rms,
                  driver.Sd, driver.source_voltage_rms)
    if any(not np.isfinite(x) or x <= 0 for x in parameters):
        raise ValueError("Expected positive finite motor parameters and RMS drive")
    if not np.isfinite(driver.Le) or driver.Le < 0:
        raise ValueError("Expected finite nonnegative coil inductance")
    if driver.node_front == driver.node_rear:
        raise ValueError("Expected distinct front and rear nodes")
    if not np.isclose(driver.Sd, inlet_area, rtol=1e-8, atol=0):
        raise ValueError("Direct coupling requires diaphragm area equal to throat area")

    model = NormalizedModel(driver=driver, node_order=[driver.node_front, driver.node_rear])
    system = assemble_system(model)
    coupled = build_coupled_system(model, system, frequency_hz)
    # OS-LEM uses exp(+i omega t). Set p_front = Z_horn * Sd * velocity
    # and p_rear = -Z_rear * Sd * velocity, preserving the kernel's electrical and mechanical rows.
    coupled.A[0] = [1, 0, 0, -horn.throat_impedance.conjugate() * driver.Sd]
    coupled.A[1] = [0, 1, 0, 0]
    if rear_volume_m3 is not None:
        compliance = rear_volume_m3 / (horn.density * horn.sound_speed**2)
        coupled.A[1, 3] = driver.Sd / (2j * np.pi * frequency_hz * compliance)
    _, _, current, velocity = np.linalg.solve(coupled.A, coupled.b).conj()
    return DrivenRoundHorn(horn, current, velocity, driver.source_voltage_rms / current)
