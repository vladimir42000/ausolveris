"""Rayleigh radiation from a uniform rectangular piston in an infinite baffle."""
import numpy as np

from .baffled_piston import _unit_rule


def _smooth_patch_integral(width, height, k, points, order):
    nodes, weights = _unit_rule(order)
    dx2 = (points[:, 0, None] - width*(nodes-.5))**2
    dy2 = (points[:, 1, None] - height*(nodes-.5))**2
    distance = np.sqrt(dx2[:, :, None] + dy2[:, None, :] + points[:, 2, None, None]**2)
    kernel = np.exp(1j*k*distance)/distance
    return (width*height*(kernel @ weights)) @ weights


def rectangular_piston_pressure(width_m, height_m, frequency_hz, velocity_m_s,
                                observers_m, *, density_kg_m3=1.21, sound_speed_m_s=343.):
    """Peak pressure for exp(-iωt); rectangle centred at the origin in z=0."""
    for value in (width_m, height_m, frequency_hz, density_kg_m3, sound_speed_m_s):
        if not np.isfinite(value) or value <= 0:
            raise ValueError("Expected positive finite dimensions, frequency and air properties")
    points = np.asarray(observers_m, dtype=float)
    if (points.ndim != 2 or points.shape[1] != 3 or not np.isfinite(points).all()
            or np.any(points[:, 2] <= 0) or not np.isfinite(velocity_m_s)):
        raise ValueError("Expected finite velocity and observers in the radiating half-space")
    k = 2*np.pi*frequency_hz/sound_speed_m_s
    # A distant observer sees a smooth kernel across a subwavelength patch.
    # Integrate the actual finite distances, with an independent quadrature
    # order check before accepting each batch.
    span = max(width_m, height_m)
    radii = np.linalg.norm(points, axis=1)
    if k*span <= 2 and np.all(radii >= 8*span):
        values = np.empty(len(points), complex)
        for first in range(0, len(points), 128):
            batch = slice(first, first+128)
            coarse = _smooth_patch_integral(width_m, height_m, k, points[batch], 6)
            fine = _smooth_patch_integral(width_m, height_m, k, points[batch], 8)
            if np.any(abs(fine-coarse) > 1e-9*width_m*height_m/radii[batch]):
                break
            values[batch] = fine
        else:
            return -1j*density_kg_m3*frequency_hz*velocity_m_s*values

    # Split each axis at the receiver projection so a close receiver's pressure
    # peak lies at a quadrature endpoint, including near a corner or an edge.
    def axis_rule(span, offset, nodes, weights):
        ends = np.unique([-span/2, np.clip(offset, -span/2, span/2), span/2])
        lengths = np.diff(ends)[:, None]
        return ((ends[:-1, None] - offset + lengths*nodes).ravel(),
                (lengths*weights).ravel())

    pressures = []
    for x, y, z in points:
        previous = None
        for order in (16, 32, 64, 128, 256):
            nodes, weights = _unit_rule(order)
            dx, wx = axis_rule(width_m, x, nodes, weights)
            dy, wy = axis_rule(height_m, y, nodes, weights)
            distance = np.sqrt(dx[:, None]**2 + dy**2 + z**2)
            integral = wx @ (np.exp(1j*k*distance)/distance) @ wy
            scale = width_m*height_m/np.hypot(np.hypot(x, y), z)
            if (previous is not None and order >= k*max(width_m, height_m)
                    and abs(integral - previous) <= 1e-9*max(abs(integral), min(scale, max(width_m, height_m)))):
                break
            previous = integral
        else:
            raise ArithmeticError("Rectangular aperture quadrature failed to converge")
        pressures.append(-1j*density_kg_m3*frequency_hz*velocity_m_s*integral)
    return np.asarray(pressures, dtype=complex)
