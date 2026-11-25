"""Symmetric, linearly flared rectangular horn with a baffled Rayleigh outlet."""
from itertools import product

import numpy as np
from scipy.linalg import solve
from scipy.sparse import bmat, coo_matrix, csr_matrix
from scipy.sparse.linalg import spsolve

from .rectangular_duct import RectangularDuct, _patch_offsets


def _quarter_load(nx, ny, dx, dy, k):
    """Fold four source quadrants onto one set of receiving patches."""
    offsets = _patch_offsets(2*nx, 2*ny, dx, dy, k)
    y, x = np.indices((ny, nx)).reshape(2, -1)
    direct_x, direct_y = np.abs(x[:, None]-x), np.abs(y[:, None]-y)
    image_x, image_y = x[:, None]+x+1, y[:, None]+y+1
    load = offsets[direct_y, direct_x]
    load += offsets[direct_y, image_x]
    load += offsets[image_y, direct_x]
    load += offsets[image_y, image_x]
    return load


def _brick_rule(axial_order):
    # Nodes follow the element connectivity in (z, y, x) order.
    corners = np.array(list(product((-1, 1), repeat=2)))
    z_nodes, z_weights = np.polynomial.legendre.leggauss(axial_order + 1)
    for z, weight in zip(z_nodes, z_weights):
        if axial_order == 1:
            axial = np.array([1-z, 1+z])/2
            dz = np.array([-.5, .5])
        else:
            axial = np.array([z*(z-1)/2, 1-z*z, z*(z+1)/2])
            dz = np.array([z-.5, -2*z, z+.5])
        for point in corners/np.sqrt(3):
            factors = (1 + corners*point)/2
            plane = factors.prod(axis=1)
            deriv = np.column_stack((np.kron(dz, plane),
                                     np.kron(axial, corners[:, 0]*factors[:, 1]/2),
                                     np.kron(axial, corners[:, 1]*factors[:, 0]/2)))
            yield np.kron(axial, plane), deriv, weight


def _interior(coordinates, elements, k, axial_order):
    vertices = coordinates[elements]
    count, nodes = elements.shape
    local = np.zeros((count, nodes, nodes))
    for basis, deriv, weight in _brick_rule(axial_order):
        jac = vertices.transpose(0, 2, 1) @ deriv
        gradient = deriv @ np.linalg.inv(jac)
        local += weight*np.abs(np.linalg.det(jac))[:, None, None]*(
            gradient @ gradient.transpose(0, 2, 1) - k**2*np.outer(basis, basis))
    rows, cols = np.broadcast_arrays(elements[:, :, None], elements[:, None, :])
    return coo_matrix((local.ravel(), (rows.ravel(), cols.ravel())),
                      shape=(len(coordinates), len(coordinates))).tocsr()


def _layered_ports(interior, weights, average, load, k, area, throat_area, plane, order):
    """Eliminate real interior blocks, retaining inlet mean and outlet velocity."""
    drive = -1j*k*throat_area/4
    source = weights[:plane].copy()
    correction = np.zeros((plane, plane))
    inlet_offset = 0.
    last = interior.shape[0]-plane
    for start in range(0, last, order*plane):
        end = start+order*plane
        block = interior[start:end, start:end].toarray()
        block[:plane, :plane] -= correction
        coupling = interior[start:end, end:end+plane].toarray()
        rhs = np.column_stack((coupling, np.zeros(end-start)))
        rhs[:plane, -1] = source
        eliminated = solve(block, rhs, assume_a="sym")
        correction = coupling.T @ eliminated[:, :-1]
        inlet_offset += source @ eliminated[:plane, -1]
        source = -coupling.T @ eliminated[:, -1]

    end_block = interior[last:, last:].toarray() - correction
    face = average[:, last:].toarray()
    system = np.block([[end_block, -1j*k*area*face.T], [face, -load]])
    result = np.linalg.solve(system, np.r_[drive*source, np.zeros(len(load))])
    inlet_mean = drive*inlet_offset + source @ result[:plane]
    return inlet_mean, result[plane:]


def solve_rectangular_horn(throat_m, mouth_m, length_m, frequency_hz, *,
                           cells=(4, 2, 32), axial_order=1, layered=False, density=1.21, sound_speed=343.):
    """Uniform 1 m/s inlet, modelled on one transverse symmetry quadrant.

    cells counts elements. Axial order 2 adds one nodal plane per axial
    element. In both orders, each transverse face uses four corner nodes.
    layered=True uses successive Schur complements to reduce solve memory.
    The full solve can be used near a singular interior elimination block.
    """
    throat, mouth = np.asarray(throat_m, float), np.asarray(mouth_m, float)
    if throat.shape != (2,) or mouth.shape != (2,):
        raise ValueError("Expected width and height at both ends")
    dimensions = np.r_[throat, mouth, length_m, frequency_hz, density, sound_speed]
    if not np.isfinite(dimensions).all() or np.any(dimensions <= 0):
        raise ValueError("Expected positive finite dimensions, frequency and air properties")
    if len(cells) != 3 or any(not isinstance(n, (int, np.integer)) or n < 1 for n in cells):
        raise ValueError("Expected three positive integer cell counts")
    if axial_order not in (1, 2) or not isinstance(axial_order, (int, np.integer)):
        raise ValueError("Expected axial polynomial order 1 or 2")
    nx, ny, nz = cells
    layers = nz*axial_order
    z, y, x = np.indices((layers+1, ny+1, nx+1))
    widths, heights = throat[:, None] + (mouth-throat)[:, None]*np.arange(layers+1)/layers
    coordinates = np.column_stack(((x*widths[:, None, None]/(2*nx)).ravel(),
                                   (y*heights[:, None, None]/(2*ny)).ravel(),
                                   (z*length_m/layers).ravel()))
    ids = np.arange(x.size).reshape(x.shape)
    elements = np.stack([ids[c:c+layers:axial_order, b:b+ny, a:a+nx]
                         for c, b, a in product(range(axial_order+1), range(2), range(2))],
                        axis=-1).reshape(-1, 4*(axial_order+1))
    k = 2*np.pi*frequency_hz/sound_speed
    interior = _interior(coordinates, elements, k, axial_order)
    # Each rectangular face has four equal integrated basis weights.
    patch_count = nx*ny
    faces = elements[-patch_count:, -4:]
    average = coo_matrix((np.full(faces.size, .25),
                          (np.repeat(np.arange(patch_count), 4), faces.ravel())),
                         shape=(patch_count, ids.size)).tocsr()
    area = mouth.prod()/(4*patch_count)
    load = _quarter_load(nx, ny, mouth[0]/(2*nx), mouth[1]/(2*ny), k)
    inlet = elements[:patch_count, :4].ravel()
    weights = np.bincount(inlet, minlength=ids.size)/(4*patch_count)
    if layered:
        inlet_mean, velocity = _layered_ports(interior, weights, average, load, k, area,
                                              throat.prod(), (nx+1)*(ny+1), axial_order)
    else:
        system = bmat([[interior, -1j*k*area*average.T],
                       [average, -csr_matrix(load)]], format="csc")
        rhs = np.r_[-1j*k*throat.prod()/4*weights, np.zeros(patch_count)]
        solution = spsolve(system, rhs)
        inlet_mean = weights @ solution[:ids.size]
        velocity = solution[-patch_count:]
    rc = density*sound_speed
    def reflect(values):
        quadrant = values.reshape(ny, nx)
        half = np.concatenate((quadrant[:, ::-1], quadrant), axis=1)
        return np.concatenate((half[::-1], half))
    impedance = rc*inlet_mean/throat.prod()
    return RectangularDuct(impedance, reflect(velocity), reflect(rc*(load @ velocity)),
                           *mouth, frequency_hz, density, sound_speed)
