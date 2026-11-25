"""Linear tetrahedral acoustics with a single baffled-piston radiation mode."""
from dataclasses import dataclass
from itertools import combinations
import warnings

import numpy as np
from scipy.sparse import bmat, coo_matrix, csr_matrix
from scipy.sparse.csgraph import connected_components
from scipy.sparse.linalg import MatrixRankWarning, spsolve
from scipy.special import j1, struve

from .baffled_piston import baffled_piston_pressure


@dataclass(frozen=True)
class CadHornResult:
    """Peak phasors for 1 m/s uniform inward throat velocity, exp(-i omega t)."""

    throat_impedance: complex  # area-mean inlet pressure / inlet volume flow, Pa s/m³
    density: float
    sound_speed: float
    frequency_hz: float
    inlet_area_m2: float
    outlet_area_m2: float
    outlet_velocity_m_s: complex  # uniform, positive outward

    def exterior_pressure(self, observers_m):
        """Return complex Pa at N by 3 outlet-centred coordinates (z > 0).

        The Rayleigh field uses the solved velocity on an equal-area circular
        disk in an infinite rigid baffle. It neglects the actual aperture shape,
        higher radiation modes and cabinet diffraction. Supports ka <= 33.
        """
        return baffled_piston_pressure(
            np.sqrt(self.outlet_area_m2 / np.pi), self.frequency_hz,
            self.outlet_velocity_m_s, observers_m, density_kg_m3=self.density,
            sound_speed_m_s=self.sound_speed)


def _indices(values, width, size):
    cells = np.asarray(values)
    if (cells.ndim != 2 or cells.shape[1] != width or not cells.size
            or cells.dtype.kind not in 'iu' or cells.min() < 0 or cells.max() >= size):
        raise ValueError(f"Expected nonempty zero-based integer connectivity with {width} columns")
    return cells.astype(np.intp, copy=False)


def _port_weights(points, triangles):
    vertices = points[triangles]
    areas = .5 * np.linalg.norm(np.cross(vertices[:, 1] - vertices[:, 0],
                                         vertices[:, 2] - vertices[:, 0]), axis=1)
    return np.bincount(triangles.ravel(), weights=np.repeat(areas / 3, 3), minlength=len(points))


def _boundary_faces(cells):
    """Validate the face-connected volume and return its exterior faces."""
    if len(np.unique(np.sort(cells, axis=1), axis=0)) != len(cells):
        raise ValueError("Duplicate tetrahedra")

    # Four consecutive faces per tetrahedron. Group by sorted vertex triple
    # so adjacent equal entries identify both owners of an interior face.
    local_faces = list(combinations(range(4), 3))
    faces = np.sort(cells[:, local_faces].reshape(-1, 3), axis=1)
    order = np.lexsort(faces.T)
    faces = faces[order]
    same = np.all(faces[:-1] == faces[1:], axis=1)
    if np.any(same[:-1] & same[1:]):
        raise ValueError("Nonmanifold volume face belongs to more than two tetrahedra")
    owners = order // 4
    graph = csr_matrix((np.ones(same.sum(), dtype=bool),
                        (owners[:-1][same], owners[1:][same])), shape=(len(cells), len(cells)))
    if connected_components(graph, directed=False, return_labels=False) != 1:
        raise ValueError("Disconnected fluid domain: tetrahedra must connect across faces")
    exterior = ~(np.r_[False, same] | np.r_[same, False])
    return set(map(tuple, faces[exterior]))


@dataclass(frozen=True)
class PreparedCadHorn:
    """Assembled mesh operators and port integrals for repeated solves."""

    stiffness: csr_matrix
    mass: csr_matrix
    inlet_weights: np.ndarray
    outlet_weights: csr_matrix  # column of integrated basis functions
    outlet_mean: csr_matrix  # row mapping nodal pressure to its port average
    inlet_area_m2: float
    outlet_area_m2: float

    def solve(self, hz, *, density=1.21, sound_speed=343.):
        """Solve for 1 m/s inward throat velocity at the given frequency in Hz."""
        if any(not np.isfinite(x) or x <= 0 for x in (hz, density, sound_speed)):
            raise ValueError("Expected positive finite frequency, density and sound speed")
        k = 2 * np.pi * hz / sound_speed
        ka = k * np.sqrt(self.outlet_area_m2 / np.pi)
        # Series avoids cancellation in 1 - J1(2ka)/ka.
        resistance = ka**2 * (.5 - ka**2 / 12) if ka < .001 else 1 - j1(2 * ka) / ka
        load = density * sound_speed * (resistance - 1j * struve(1, 2 * ka) / ka)
        iw_rho = 1j * k * sound_speed * density
        # Last unknown is uniform outlet velocity. Last row sets mean(p) = load * v.
        system = bmat([[self.stiffness - k**2 * self.mass, -iw_rho * self.outlet_weights],
                       [self.outlet_mean, csr_matrix([[-load]])]], format='csc')
        with warnings.catch_warnings():
            warnings.simplefilter('error', MatrixRankWarning)
            solution = spsolve(system, np.r_[-iw_rho * self.inlet_weights, 0])
        impedance = self.inlet_weights @ solution[:-1] / self.inlet_area_m2**2
        return CadHornResult(impedance, density, sound_speed, hz, self.inlet_area_m2,
                             self.outlet_area_m2, solution[-1])


def prepare_cad_horn(points, tetra, inlet, outlet):
    """Assemble P1 operators for a single face-connected tetrahedral air volume.

    Coordinates are in metres. Connectivity uses zero-based point indices.
    Each port comprises distinct exterior faces in either winding. Remaining
    faces are rigid. Mesh geometry and topology are only needed during preparation.
    """
    points = np.asarray(points, dtype=float)
    if points.ndim != 2 or points.shape[1] != 3 or not np.isfinite(points).all():
        raise ValueError("Expected finite N by 3 point coordinates")
    cells = _indices(tetra, 4, len(points))
    inlet = _indices(inlet, 3, len(points))
    outlet = _indices(outlet, 3, len(points))
    boundary = _boundary_faces(cells)
    for tri in np.sort(np.vstack((inlet, outlet)), axis=1):
        if tuple(tri) not in boundary:
            raise ValueError("Ports must contain distinct exterior tetrahedral faces")
        boundary.remove(tuple(tri))

    edges = points[cells[:, 1:]] - points[cells[:, :1]]
    volume = abs(np.linalg.det(edges)) / 6
    if np.any(volume == 0):
        raise ValueError("Degenerate tetrahedron")
    # With edge vectors as rows, inverse columns are gradients of N1..N3.
    grad = np.linalg.inv(edges)
    grad = np.concatenate((-grad.sum(axis=2, keepdims=True), grad), axis=2)
    stiffness = volume[:, None, None] * (grad.transpose(0, 2, 1) @ grad)
    mass = volume[:, None, None] * (1 + np.eye(4)) / 20
    active, indices = np.unique(cells, return_inverse=True)
    indices = indices.reshape(cells.shape)
    rows = np.broadcast_to(indices[:, :, None], stiffness.shape).ravel()
    cols = np.broadcast_to(indices[:, None, :], stiffness.shape).ravel()

    def assemble(elements):
        return coo_matrix((elements.ravel(), (rows, cols)),
                          shape=(len(active), len(active))).tocsr()

    wi = _port_weights(points, inlet)[active]
    wo = _port_weights(points, outlet)[active]
    ao = wo.sum()
    return PreparedCadHorn(assemble(stiffness), assemble(mass), wi, csr_matrix(wo[:, None]),
                           csr_matrix(wo / ao), wi.sum(), ao)


def solve_cad_horn(points_m, tetra, inlet_triangles, outlet_triangles, frequency_hz, *,
                   density=1.21, sound_speed=343.):
    """Prepare an imported air mesh and solve once. Use prepare_cad_horn for sweeps."""
    horn = prepare_cad_horn(points_m, tetra, inlet_triangles, outlet_triangles)
    return horn.solve(frequency_hz, density=density, sound_speed=sound_speed)
