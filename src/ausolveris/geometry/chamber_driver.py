"""Small-signal piston coupling through a compact, uniform-pressure front cavity."""
from dataclasses import dataclass

import numpy as np

from .driven_round_horn import _drive
from .rectangular_duct import RectangularDuct
from .round_horn import RoundHornResult


@dataclass(frozen=True)
class _AcousticLoad:
    throat_impedance: complex
    density: float
    sound_speed: float


@dataclass
class ChamberHornResult:
    unit_horn: RoundHornResult | RectangularDuct
    electrical_impedance: complex
    current_rms: complex
    diaphragm_velocity_rms: complex
    throat_velocity_rms: complex

    def exterior_pressure_rms(self, points):
        """Complex RMS pressure in Pa at the unit horn's observer coordinates."""
        return self.unit_horn.exterior_pressure(points) * self.throat_velocity_rms


def drive_chamber_horn(horn, frequency_hz, driver, *, throat_area_m2, front_volume_m3,
                       rear_volume_m3=None):
    """Drive a horn solved at this frequency for uniform +1 m/s throat velocity.

    Supply the horn's actual inlet area and its pressure/volume-flow impedance.
    Results use exp(-i omega t). A zero front volume enforces equal volume
    flows even for unequal areas. None sets the rear pressure to zero.

    Both cavities are lossless compliances, valid for dimensions small relative
    to wavelength. The model omits cavity modes, leakage, and contraction
    inertance or losses. Exterior pressure includes only the horn radiation.
    """
    if not np.isfinite(frequency_hz) or frequency_hz <= 0 or frequency_hz != horn.frequency_hz:
        raise ValueError("Expected positive finite frequency matching the horn solve")
    if not np.isfinite(throat_area_m2) or throat_area_m2 <= 0:
        raise ValueError("Expected positive finite throat area in square metres")
    if not np.isfinite(front_volume_m3) or front_volume_m3 < 0:
        raise ValueError("Expected finite nonnegative front volume in cubic metres")

    compliance = front_volume_m3 / (horn.density * horn.sound_speed**2)
    # Continuity: Sd*v = Q_throat - i*omega*C*p, with p = Z_horn*Q_throat.
    flow_denominator = 1 - 2j*np.pi*frequency_hz*compliance*horn.throat_impedance
    if flow_denominator == 0:
        raise ValueError("Singular equivalent load at lossless front cavity resonance")
    load = _AcousticLoad(horn.throat_impedance / flow_denominator, horn.density, horn.sound_speed)
    # At the diaphragm port _drive's velocity is piston velocity, over area Sd.
    motor = _drive(load, frequency_hz, driver, driver.Sd, rear_volume_m3)
    diaphragm_velocity = motor.throat_velocity_rms
    throat_flow = driver.Sd * diaphragm_velocity / flow_denominator
    return ChamberHornResult(horn, motor.electrical_impedance, motor.current_rms,
                             diaphragm_velocity, throat_flow / throat_area_m2)
