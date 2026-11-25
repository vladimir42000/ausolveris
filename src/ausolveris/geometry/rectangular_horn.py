"""Symmetric, linearly flared rectangular horn with a baffled Rayleigh outlet."""
from itertools import product

import numpy as np
from scipy.sparse import bmat, coo_matrix, csr_matrix
from scipy.sparse.linalg import spsolve

from .rectangular_duct import RectangularDuct, _patch_load


def _interior(coordinates, elements, k):
    # Trilinear bricks; numerical integration in the physical tapered section.
    signs = np.array(list(product((-1, 1), repeat=3)))
    vertices = coordinates[elements]
    local = np.zeros((len(elements), 8, 8))
    for point in signs / np.sqrt(3):
        factors = (1 + signs*point)/2
        basis = factors.prod(axis=1)
        deriv = np.column_stack([signs[:, i]*factors[:, (i+1)%3]*factors[:, (i+2)%3]/2
                                 for i in range(3)])
        jac = vertices.transpose(0, 2, 1) @ deriv
        gradient = deriv @ np.linalg.inv(jac)
        local += np.abs(np.linalg.det(jac))[:, None, None]*(
            gradient @ gradient.transpose(0, 2, 1) - k**2*np.outer(basis, basis))
    rows, cols = np.broadcast_arrays(elements[:, :, None], elements[:, None, :])
    return coo_matrix((local.ravel(), (rows.ravel(), cols.ravel())),
                      shape=(len(coordinates), len(coordinates))).tocsr()


def solve_rectangular_horn(throat_m, mouth_m, length_m, frequency_hz, *,
                           cells=(4, 2, 32), density=1.21, sound_speed=343.):
    """Uniform 1 m/s inlet. Transverse cell counts apply to one symmetry quadrant."""
    throat, mouth = np.asarray(throat_m, float), np.asarray(mouth_m, float)
    if throat.shape != (2,) or mouth.shape != (2,):
        raise ValueError("Expected width and height at both ends")
    dimensions = np.r_[throat, mouth, length_m, frequency_hz, density, sound_speed]
    if not np.isfinite(dimensions).all() or np.any(dimensions <= 0):
        raise ValueError("Expected positive finite dimensions, frequency and air properties")
    if len(cells) != 3 or any(not isinstance(n, (int, np.integer)) or n < 1 for n in cells):
        raise ValueError("Expected three positive integer cell counts")
    nx, ny, nz = cells
    z, y, x = np.indices((nz+1, ny+1, nx+1))
    widths, heights = throat[:, None] + (mouth-throat)[:, None]*np.arange(nz+1)/nz
    coordinates = np.column_stack(((x*widths[:, None, None]/(2*nx)).ravel(),
                                   (y*heights[:, None, None]/(2*ny)).ravel(),
                                   (z*length_m/nz).ravel()))
    ids = np.arange(x.size).reshape(x.shape)
    elements = np.stack([ids[c:c+nz, b:b+ny, a:a+nx]
                         for c, b, a in product(range(2), repeat=3)], axis=-1).reshape(-1, 8)
    k = 2*np.pi*frequency_hz/sound_speed
    interior = _interior(coordinates, elements, k)
    # Each rectangular face has four equal integrated basis weights.
    patch_count = nx*ny
    faces = elements[-patch_count:, 4:]
    average = coo_matrix((np.full(faces.size, .25),
                          (np.repeat(np.arange(patch_count), 4), faces.ravel())),
                         shape=(patch_count, ids.size)).tocsr()
    area = mouth.prod()/(4*patch_count)
    full_load = _patch_load(2*nx, 2*ny, mouth[0]/(2*nx), mouth[1]/(2*ny), k)
    mirrors = full_load.reshape(2*ny, 2*nx, 2*ny, 2*nx)[ny:, nx:]
    load = (mirrors[:, :, ny:, nx:] + mirrors[:, :, ny:, nx-1::-1]
            + mirrors[:, :, ny-1::-1, nx:] + mirrors[:, :, ny-1::-1, nx-1::-1])
    load = load.reshape(patch_count, patch_count)
    system = bmat([[interior, -1j*k*area*average.T],
                   [average, -csr_matrix(load)]], format="csc")
    inlet = elements[:patch_count, :4].ravel()
    weights = np.bincount(inlet, minlength=ids.size)/(4*patch_count)
    rhs = np.r_[-1j*k*throat.prod()/4*weights, np.zeros(patch_count)]
    solution = spsolve(system, rhs)
    rc = density*sound_speed
    velocity = solution[-patch_count:]
    def reflect(values):
        quadrant = values.reshape(ny, nx)
        half = np.concatenate((quadrant[:, ::-1], quadrant), axis=1)
        return np.concatenate((half[::-1], half))
    impedance = rc*(weights @ solution[:ids.size])/throat.prod()
    return RectangularDuct(impedance, reflect(velocity), reflect(rc*(load @ velocity)),
                           *mouth, frequency_hz, density, sound_speed)
