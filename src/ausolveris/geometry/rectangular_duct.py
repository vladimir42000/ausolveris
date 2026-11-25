"""Rigid rectangular duct coupled to a flush aperture in an infinite baffle."""
from dataclasses import dataclass

import numpy as np
from scipy.sparse import bmat, csr_matrix, diags, eye, kron
from scipy.sparse.linalg import spsolve

from .baffled_piston import _unit_rule
from .rectangular_piston import rectangular_piston_pressure


def _patch_load(nx, ny, dx, dy, k):
    """Area-averaged Rayleigh impedance / (rho*c) for equal rectangular patches."""
    nodes, weights = _unit_rule(max(16, int(np.ceil(k*max(dx, dy))) + 8))
    u, v = nodes[:, None], nodes[None, :]
    jacobian = dx*dy*u*weights[:, None]*weights[None, :]
    offsets = np.empty((ny, nx), complex)
    for j, i in np.ndindex(ny, nx):
        integral = 0j
        # Convolving two rectangles gives separable triangular overlap weights.
        # Split into quadrants and two triangles; the self singularity cancels
        # with the radial Jacobian of the Duffy map.
        for sx in (-1, 1):
            for sy in (-1, 1):
                for a, b in ((u, u*v), (u*v, u)):
                    r = np.hypot(dx*(i + sx*a), dy*(j + sy*b))
                    integral += np.sum(jacobian*(1-a)*(1-b)*np.exp(1j*k*r)/r)
        offsets[j, i] = -1j*k*integral/(2*np.pi)
    y, x = np.indices((ny, nx)).reshape(2, -1)
    return offsets[np.abs(y[:, None]-y), np.abs(x[:, None]-x)]


def _laplacian(n, spacing):
    if n == 1:
        return csr_matrix((1, 1))
    difference = diags([-np.ones(n-1), np.ones(n-1)], [0, 1], shape=(n-1, n))
    return (difference.T @ difference)/spacing**2


@dataclass
class RectangularDuct:
    throat_impedance: complex
    mouth_velocity_m_s: np.ndarray
    mouth_pressure_pa: np.ndarray
    width_m: float
    height_m: float
    frequency_hz: float
    density: float
    sound_speed: float

    def exterior_pressure(self, observers_m):
        points = np.asarray(observers_m, dtype=float)
        ny, nx = self.mouth_velocity_m_s.shape
        dx, dy = self.width_m/nx, self.height_m/ny
        total = np.zeros(len(points), dtype=complex)
        for j, i in np.ndindex(ny, nx):
            center = [(i+.5)*dx-self.width_m/2, (j+.5)*dy-self.height_m/2, 0.]
            total += rectangular_piston_pressure(dx, dy, self.frequency_hz,
                self.mouth_velocity_m_s[j, i], points-center,
                density_kg_m3=self.density, sound_speed_m_s=self.sound_speed)
        return total


def solve_rectangular_duct(width_m, height_m, length_m, frequency_hz, *,
                           cells=(8, 4, 32), density=1.21, sound_speed=343.):
    """Unit uniform inlet velocity. Cell counts follow width, height, length."""
    for value in (width_m, height_m, length_m, frequency_hz, density, sound_speed):
        if not np.isfinite(value) or value <= 0:
            raise ValueError("Expected positive finite dimensions, frequency and air properties")
    if len(cells) != 3 or any(not isinstance(n, (int, np.integer)) or n < 1 for n in cells):
        raise ValueError("Expected three positive integer cell counts")
    nx, ny, nz = cells
    dx, dy, dz = width_m/nx, height_m/ny, length_m/nz
    k = 2*np.pi*frequency_hz/sound_speed
    face = nx*ny
    transverse = kron(eye(ny), _laplacian(nx, dx)) + kron(_laplacian(ny, dy), eye(nx))
    interior = kron(eye(nz), transverse) + kron(_laplacian(nz, dz), eye(face))
    interior -= k**2*eye(face*nz)
    load = _patch_load(nx, ny, dx, dy, k)
    outlet = eye(face, face*nz, k=(nz-1)*face, format="csr")
    # Face pressure follows from the cell-centre pressure plus the half-cell
    # momentum increment. Unknown pressures are normalized by rho*c.
    matrix = bmat([[dz**2*interior, -1j*k*dz*outlet.T],
                   [outlet, .5j*k*dz*eye(face)-csr_matrix(load)]], format="csc")
    rhs = np.zeros(face*(nz+1), complex)
    rhs[:face] = -1j*k*dz
    solution = spsolve(matrix, rhs)
    velocity = solution[-face:]
    zin = density*sound_speed*(solution[:face].mean()-.5j*k*dz)/(width_m*height_m)
    pressure = density*sound_speed*(load @ velocity)
    return RectangularDuct(zin, velocity.reshape(ny, nx), pressure.reshape(ny, nx),
                           width_m, height_m, frequency_hz, density, sound_speed)
