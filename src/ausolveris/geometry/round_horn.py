"""Axisymmetric pressure FEM with a rigid, infinitely baffled annular Rayleigh outlet."""
from dataclasses import dataclass

import numpy as np
from scipy.sparse import bmat, coo_matrix, csr_matrix
from scipy.sparse.linalg import spsolve

from .baffled_piston import _angular_mean, _unit_rule, baffled_piston_pressure


def _port_weights(edges):
    """Integral of each endpoint basis function over its annular face."""
    lo, hi = edges[:-1], edges[1:]
    return np.pi * (hi - lo)[:, None] / 3 * np.column_stack((2*lo + hi, lo + 2*hi))


def _mouth_load(edges, k):
    # Mean pressure on each receiver ring for unit velocity on each source
    # ring, normalized by rho*c. Differences of nested disks give annuli.
    nodes, weights = _unit_rule(8)
    load = np.empty((len(edges)-1, len(edges)-1), dtype=complex)
    for row, (lo, hi) in enumerate(zip(edges[:-1], edges[1:])):
        r = lo + (hi-lo)*nodes
        disk_means = [0j]
        for radius in edges[1:]:
            response = [_angular_mean(radius, s, 0., k, 128) for s in r]
            disk_means.append(np.dot(weights * 2*r/(hi+lo), response))
        load[row] = np.diff(disk_means)
    return load


def _interior_matrix(z, radii, nr, k):
    rr = radii[:, None] * np.linspace(0, 1, nr+1)
    coords = np.column_stack((np.broadcast_to(z[:, None], rr.shape).ravel(), rr.ravel()))
    ids = np.arange(rr.size).reshape(rr.shape)
    a, b = ids[:-1, :-1].ravel(), ids[1:, :-1].ravel()
    tri = np.vstack((np.column_stack((a, b, b+1)), np.column_stack((a, b+1, a+1))))
    vertices = coords[tri]
    dz, dr = (np.roll(vertices, -1, axis=1) - np.roll(vertices, -2, axis=1)).transpose(2, 0, 1)
    area2 = dz[:, 0]*dr[:, 1] - dz[:, 1]*dr[:, 0]
    r = vertices[:, :, 1]
    # Shape-function gradients are constant. Integrate the r-weighted cubic
    # mass integrand exactly using triangle barycentric moments.
    stiff = (dr[:, :, None]*dr[:, None, :] + dz[:, :, None]*dz[:, None, :])
    stiff *= (np.pi*r.mean(axis=1)/area2)[:, None, None]
    mass = r.sum(axis=1)[:, None, None] + r[:, :, None] + r[:, None, :]
    mass *= (1 + np.eye(3)) * (np.pi*area2/60)[:, None, None]
    entries = stiff - k*k*mass
    rows, cols = np.broadcast_arrays(tri[:, :, None], tri[:, None, :])
    return coo_matrix((entries.ravel(), (rows.ravel(), cols.ravel())),
                      shape=(rr.size, rr.size)).tocsr()


@dataclass
class RoundHornResult:
    throat_impedance: complex  # mean throat pressure / inlet volume velocity, Pa s/m³
    wall_pressure_pa: np.ndarray
    axial_positions_m: np.ndarray
    mouth_edges_m: np.ndarray
    mouth_velocity_m_s: np.ndarray
    mouth_pressure_pa: np.ndarray  # mean pressure per annulus
    frequency_hz: float
    density: float
    sound_speed: float

    def exterior_pressure(self, observers_m):
        """Complex peak pressure, with microphones measured from the mouth plane."""
        # Superposition of nested disks represents a nonuniform ring velocity.
        jumps = -np.diff(self.mouth_velocity_m_s, append=0j)
        return sum(baffled_piston_pressure(radius, self.frequency_hz, jump, observers_m,
                                           density_kg_m3=self.density, sound_speed_m_s=self.sound_speed)
                   for radius, jump in zip(self.mouth_edges_m[1:], jumps))


def solve_round_horn(profile, frequency_hz, throat_velocity=1., *, axial_cells=48,
                     radial_cells=8, density=1.21, sound_speed=343.):
    """Solve a piecewise-linear (axial position, radius) profile in metres.

    Velocity points from throat to mouth. Peak phasors use exp(-i omega t).
    The mouth is flush with an infinite baffle. The caller must check mesh
    convergence. The outlet pressure evaluator supports mouth ka <= 10.
    """
    profile = np.asarray(profile, dtype=float)
    if (profile.ndim != 2 or profile.shape[1] != 2 or len(profile) < 2
            or not np.isfinite(profile).all() or np.any(profile[:, 1] <= 0)
            or np.any(np.diff(profile[:, 0]) <= 0)):
        raise ValueError("Expected increasing axial positions and positive finite radii")
    if any(not isinstance(n, (int, np.integer)) or n < 1 for n in (radial_cells, axial_cells)):
        raise ValueError("Cell counts must be positive integers")
    if any(not np.isfinite(x) or x <= 0 for x in (density, sound_speed, frequency_hz)):
        raise ValueError("Expected positive finite air properties and frequency")
    if not np.isfinite(throat_velocity) or throat_velocity == 0:
        raise ValueError("Expected a finite nonzero throat velocity")
    k = 2*np.pi*frequency_hz/sound_speed
    if k*profile[-1, 1] > 10:
        raise ValueError("Mouth load supports ka up to 10")
    knots = profile[:, 0]
    lengths = np.diff(knots)
    counts = np.ceil(axial_cells*lengths/lengths.sum()).astype(int)
    z = np.r_[np.concatenate([np.linspace(l, h, n, endpoint=False)
                               for l, h, n in zip(knots, knots[1:], counts)]), knots[-1]]
    radii = np.interp(z, knots, profile[:, 1])
    interior = _interior_matrix(z, radii, radial_cells, k)
    nodes = interior.shape[0]
    fraction = np.linspace(0, 1, radial_cells+1)
    edges = fraction*radii[-1]
    w_out = _port_weights(edges)
    idx = np.arange(radial_cells)
    port = coo_matrix((w_out.ravel(), ((nodes-radial_cells-1 + idx[:, None] + [0,1]).ravel(),
                                      np.repeat(idx, 2))), shape=(nodes, radial_cells)).tocsr()
    load = _mouth_load(edges, k)
    system = bmat([[interior, -1j*k*port],
                   [port.T, -csr_matrix(w_out.sum(axis=1)[:, None]*load)]], format="csc")
    w_in = _port_weights(fraction*radii[0])
    inlet = np.r_[w_in[:, 0], 0] + np.r_[0, w_in[:, 1]]
    rhs = np.zeros(nodes+radial_cells, dtype=complex)
    rhs[:len(inlet)] = -1j*k*inlet*throat_velocity
    solution = spsolve(system, rhs)
    pressure = solution[:nodes]*density*sound_speed
    velocity = solution[nodes:]
    impedance = (inlet @ pressure[:len(inlet)]) / (throat_velocity*inlet.sum()**2)
    return RoundHornResult(impedance, pressure[radial_cells::radial_cells+1], z, edges,
                           velocity, density*sound_speed*(load @ velocity),
                           frequency_hz, density, sound_speed)
