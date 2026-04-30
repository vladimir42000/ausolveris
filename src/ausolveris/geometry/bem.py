"""
BEM‑001 : Helmholtz Green‑function utility (scalar, free-space).

Convention:
    G(r, k) = exp(i * k * r) / (4 * pi * r)
"""

import math
import cmath

def helmholtz_green_function(r_m: float, k_rad_m: float) -> complex:
    """
    Evaluate the free‑space scalar Helmholtz Green function.

    Parameters
    ----------
    r_m : float
        Distance in metres. Must be finite and strictly positive.
    k_rad_m : float
        Wavenumber in rad/m. Must be finite and non‑negative.

    Returns
    -------
    complex
    """
    if not math.isfinite(r_m) or r_m <= 0.0:
        raise ValueError("r_m must be finite and strictly positive")
    if not math.isfinite(k_rad_m) or k_rad_m < 0.0:
        raise ValueError("k_rad_m must be finite and non‑negative")

    ikr = 1j * k_rad_m * r_m
    return cmath.exp(ikr) / (4.0 * math.pi * r_m)


def helmholtz_wavenumber(frequency_hz: float, sound_speed_m_s: float) -> float:
    """
    Compute the acoustic wavenumber.

    Parameters
    ----------
    frequency_hz : float
        Frequency in Hz. Must be finite and non‑negative.
    sound_speed_m_s : float
        Speed of sound in m/s. Must be finite and strictly positive.

    Returns
    -------
    float
        k = 2 * pi * f / c
    """
    if not math.isfinite(frequency_hz) or frequency_hz < 0.0:
        raise ValueError("frequency_hz must be finite and non‑negative")
    if not math.isfinite(sound_speed_m_s) or sound_speed_m_s <= 0.0:
        raise ValueError("sound_speed_m_s must be finite and strictly positive")

    return 2.0 * math.pi * frequency_hz / sound_speed_m_s
