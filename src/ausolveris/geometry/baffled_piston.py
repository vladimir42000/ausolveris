"""Rayleigh radiation from a uniformly moving circular disk in an infinite rigid baffle."""

from functools import lru_cache

import numpy as np


MAX_APERTURE_KA = 33.0


@lru_cache(maxsize=8)
def _unit_rule(order):
    nodes, weights = np.polynomial.legendre.leggauss(order)
    return (nodes + 1) / 2, weights / 2


def _angular_mean(radius, s, z, k, order):
    # Cast in-plane rays from the receiver projection, measuring angle toward
    # the disk centre. Mirror symmetry reduces the angular integral by half.
    u, weights = _unit_rule(order)
    if s < radius:
        phi = np.pi * u
        angular_weight = weights
    else:
        # Only the sector subtended by the disk intersects it. The substitution
        # flattens the square root at the tangent ray.
        alpha = np.arcsin(radius / s)
        phi = alpha * np.sin(np.pi * u / 2)
        angular_weight = weights * alpha / 2 * np.cos(np.pi * u / 2)
    along = s * np.cos(phi)
    across = s * np.sin(phi)
    half_chord = np.sqrt(np.maximum((radius - across) * (radius + across), 0))
    hi = np.maximum(along + half_chord, 0)
    lo = np.maximum(along - half_chord, 0)
    r0, r1 = np.hypot(z, lo), np.hypot(z, hi)
    # Integrate exp(ikR)/R analytically along the radial coordinate.
    # Rationalizing R1-R0 and using expm1 retains accuracy in the far field.
    width = 2 * half_chord if s >= radius else hi
    dr = width * ((hi + lo) / (r1 + r0))
    return -np.dot(angular_weight, np.exp(1j * k * r0) * np.expm1(1j * k * dr))


def baffled_piston_pressure(radius_m, frequency_hz, velocity_m_s, observers_m,
                            *, density_kg_m3=1.21, sound_speed_m_s=343.0):
    """Return complex peak pressure in Pa for N Cartesian microphone positions.

    The disk lies in z=0, centred at the origin. Positive velocity points into
    z>0. Phasors use exp(-i omega t). This benchmark covers 0 < ka <= 33.
    """
    for value in (radius_m, frequency_hz, density_kg_m3, sound_speed_m_s):
        if not np.isfinite(value) or value <= 0:
            raise ValueError("Radius, frequency, density and sound speed must be positive and finite")
    if not np.isfinite(velocity_m_s):
        raise ValueError("Velocity must be finite")
    k = 2 * np.pi * frequency_hz / sound_speed_m_s
    if k * radius_m > MAX_APERTURE_KA:
        raise ValueError(f"Piston benchmark supports ka up to {MAX_APERTURE_KA:g}")
    points = np.asarray(observers_m, dtype=float)
    if points.ndim != 2 or points.shape[1] != 3 or not np.isfinite(points).all():
        raise ValueError("Expected finite N by 3 microphone coordinates")
    if np.any(points[:, 2] <= 0):
        raise ValueError("Microphones must lie in the radiating half-space z > 0")

    values = []
    for x, y, z in points:
        s = np.hypot(x, y)
        previous = _angular_mean(radius_m, s, z, k, 32)
        for order in (64, 128, 256):
            current = _angular_mean(radius_m, s, z, k, order)
            scale = min(1.0, k * radius_m**2 / np.hypot(s, z))
            if abs(current - previous) <= 1e-9 * scale:
                break
            previous = current
        else:
            raise ArithmeticError("Angular quadrature failed to converge at this microphone")
        values.append(current)
    return density_kg_m3 * sound_speed_m_s * velocity_m_s * np.asarray(values, dtype=complex)
