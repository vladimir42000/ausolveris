"""Tetrahedralize a closed STL of acoustic air using the optional Gmsh API."""
from collections import defaultdict
from contextlib import contextmanager
from pathlib import Path
import struct
from threading import RLock
from uuid import uuid4

import numpy as np


_UNITS = {"m": 1., "cm": .01, "mm": .001, "in": .0254}
_LOCK = RLock()
# Outward local faces for a positive oriented tetrahedron.
_FACES = np.array([[1, 2, 3], [0, 3, 2], [0, 1, 3], [0, 2, 1]])


def _read_stl(path):
    data = Path(path).read_bytes()
    if len(data) >= 84 and len(data) == 84 + 50 * struct.unpack_from("<I", data, 80)[0]:
        # Each record contains a normal, three float32 vertices and two attribute bytes.
        records = np.dtype([("normal", "<f4", 3), ("vertices", "<f4", (3, 3)),
                            ("attribute", "<u2")])
        facets = np.frombuffer(data, dtype=records, offset=84)["vertices"]
    else:
        try:
            lines = iter(filter(None, (line.lower().split()
                                       for line in data.decode("ascii").splitlines())))
            vertices = []
            for words in lines:
                if words[0] in {"solid", "endsolid"}:
                    continue
                if words[:2] != ["facet", "normal"] or next(lines) != ["outer", "loop"]:
                    raise ValueError
                for _ in range(3):
                    vertex = next(lines)
                    if len(vertex) != 4 or vertex[0] != "vertex":
                        raise ValueError
                    vertices.append([float(x) for x in vertex[1:]])
                if next(lines) != ["endloop"] or next(lines) != ["endfacet"]:
                    raise ValueError
            facets = np.asarray(vertices).reshape(-1, 3, 3)
        except (StopIteration, UnicodeError, ValueError) as exc:
            raise ValueError("Invalid binary or ASCII STL") from exc
    if not len(facets) or not np.isfinite(facets).all():
        raise ValueError("STL must contain finite triangles")
    vertices, inverse = np.unique(facets.reshape(-1, 3), axis=0, return_inverse=True)
    return vertices.astype(float), inverse.reshape(-1, 3)


def _shell(points, faces):
    a, b, c = points[faces].transpose(1, 0, 2)
    if np.any(np.linalg.norm(np.cross(b-a, c-a), axis=1) == 0):
        raise ValueError("Degenerate STL triangle")
    edges = defaultdict(list)
    for i, (a, b, c) in enumerate(faces):
        for u, v in ((a, b), (b, c), (c, a)):
            edges[min(u, v), max(u, v)].append((i, u < v))
    neighbors = [[] for _ in faces]
    for incident in edges.values():
        if len(incident) != 2:
            raise ValueError("STL must be closed with exactly two triangles per edge")
        (i, forward), (j, other) = incident
        neighbors[i].append((j, forward == other))
        neighbors[j].append((i, forward == other))
    # Propagate compatible winding irrespective of STL normal records.
    flip = {0: False}
    pending = [0]
    while pending:
        i = pending.pop()
        for j, opposite in neighbors[i]:
            value = flip[i] ^ opposite
            if j not in flip:
                flip[j] = value
                pending.append(j)
            elif flip[j] != value:
                raise ValueError("STL surface is not orientable")
    if len(flip) != len(faces):
        raise ValueError("STL must enclose one connected air volume")
    reverse = np.array([flip[i] for i in range(len(faces))])
    faces[reverse] = faces[reverse, ::-1]
    a, b, c = (points - points[0])[faces].transpose(1, 0, 2)
    volume = np.einsum("ij,ij->", a, np.cross(b-a, c-a)) / 6
    if not np.isfinite(volume) or volume == 0:
        raise ValueError("STL encloses zero volume")
    if volume < 0:
        faces[:] = faces[:, ::-1]
    return abs(volume)


def _port(points, triangles, z, tol, name):
    selected = triangles[np.all(abs(points[triangles, 2] - z) <= tol, axis=1)]
    if not len(selected):
        raise ValueError(f"No planar {name} triangles on requested z plane")
    edges = selected[:, [[0, 1], [1, 2], [2, 0]]].reshape(-1, 2)
    edges, counts = np.unique(np.sort(edges, axis=1), axis=0, return_counts=True)
    rim = defaultdict(list)
    for a, b in edges[counts == 1]:
        rim[a].append(b)
        rim[b].append(a)
    seen = set()
    pending = list(rim)[:1]
    while pending:
        node = pending.pop()
        if node not in seen:
            seen.add(node)
            pending.extend(rim[node])
    if not rim or len(seen) != len(rim) or any(len(v) != 2 for v in rim.values()):
        raise ValueError(f"{name} must have one boundary loop (simply connected air port)")
    return selected


@contextmanager
def _model(gmsh, size):
    with _LOCK:
        owned = not gmsh.isInitialized()
        if owned:
            gmsh.initialize([], readConfigFiles=False, interruptible=False)
        previous = gmsh.model.getCurrent()
        gmsh.model.add("air-" + uuid4().hex)
        settings = {"General.Terminal": 0, "Mesh.MeshSizeMin": size,
                    "Mesh.MeshSizeMax": size, "Mesh.ElementOrder": 1,
                    "Mesh.RecombineAll": 0, "Mesh.Algorithm3D": 1}
        saved = {}
        try:
            for key, value in settings.items():
                saved[key] = gmsh.option.getNumber(key)
                gmsh.option.setNumber(key, value)
            yield
        finally:
            gmsh.model.remove()
            if owned:
                gmsh.finalize()
            else:
                for key, value in saved.items():
                    gmsh.option.setNumber(key, value)
                if previous in gmsh.model.list():
                    gmsh.model.setCurrent(previous)


def _generate(points, faces, size):
    try:
        import gmsh
    except (ImportError, OSError) as exc:
        raise ImportError("mesh_air_stl requires the optional gmsh Python API and shared libraries") from exc
    with _model(gmsh, size):
        geo = gmsh.model.geo
        nodes = [geo.addPoint(*p, size) for p in points]
        lines = {}
        surfaces = []
        for a, b, c in faces:
            loop = []
            for u, v in ((a, b), (b, c), (c, a)):
                edge = min(u, v), max(u, v)
                if edge not in lines:
                    lines[edge] = geo.addLine(nodes[edge[0]], nodes[edge[1]])
                loop.append(lines[edge] if u < v else -lines[edge])
            surfaces.append(geo.addPlaneSurface([geo.addCurveLoop(loop)]))
        volume = geo.addVolume([geo.addSurfaceLoop(surfaces)])
        geo.synchronize()
        mesh = gmsh.model.mesh
        mesh.generate(3)
        tags, coords, _ = mesh.getNodes()
        order = np.argsort(tags)
        points = coords.reshape(-1, 3)[order]
        types, _, connectivity = mesh.getElements(3, volume)
        if list(types) != [4]:
            raise ValueError("Gmsh did not generate first-order tetrahedra")
        tetra = np.searchsorted(tags[order], connectivity[0]).reshape(-1, 4)
    return points, tetra


def mesh_air_stl(path, *, units, cell_size_m, inlet_z_m=None, outlet_z_m=None):
    """Mesh a connected, capped air volume. Units are m, cm, mm or in.

    Cap coordinates and target cell size are in metres. Caps default to the
    lowest and highest z planes respectively. Each port must be a planar disk
    topologically. Return metre coordinates, positive tetrahedra and outward
    inlet/outlet triangles with zero-based indices into the coordinates.
    """
    if units not in _UNITS:
        raise ValueError("units must be one of m, cm, mm, in")
    if not np.isfinite(cell_size_m) or cell_size_m <= 0:
        raise ValueError("cell_size_m must be positive and finite")
    points, faces = _read_stl(path)
    points *= _UNITS[units]
    volume = _shell(points, faces)
    a, b, c = points[faces].transpose(1, 0, 2)
    surface_area2 = np.linalg.norm(np.cross(b-a, c-a), axis=1).sum()
    z = points[:, 2]
    lo = z.min() if inlet_z_m is None else inlet_z_m
    hi = z.max() if outlet_z_m is None else outlet_z_m
    tol = np.ptp(z) * 1e-8
    if not np.isfinite([lo, hi]).all() or hi-lo <= 2*tol:
        raise ValueError("Expected distinct finite cap planes with inlet below outlet")
    ports = [(lo, "inlet"), (hi, "outlet")]
    areas = []
    for plane, name in ports:
        cap = _port(points, faces, plane, tol, name)
        a, b, c = points[cap].transpose(1, 0, 2)
        areas.append(np.abs(np.cross(b-a, c-a)[:, 2]).sum())
    try:
        points, tetra = _generate(points, faces, cell_size_m)
    except (ImportError, ValueError):
        raise
    except Exception as exc:
        raise RuntimeError(f"Gmsh failed to tetrahedralize the STL: {exc}") from exc
    a, b, c, d = points[tetra].transpose(1, 0, 2)
    determinants = np.einsum("ij,ij->i", b-a, np.cross(c-a, d-a))
    if np.any(determinants <= 0) or not np.isclose(determinants.sum()/6, volume,
                                                   rtol=1e-7, atol=0):
        raise ValueError("Invalid tetrahedra or mesh volume differs from STL")
    faces = tetra[:, _FACES].reshape(-1, 3)
    _, first, counts = np.unique(np.sort(faces, axis=1), axis=0, return_index=True,
                                 return_counts=True)
    if np.any(counts > 2):
        raise ValueError("Non-manifold tetrahedral boundary")
    boundary = faces[first[counts == 1]]
    a, b, c = points[boundary].transpose(1, 0, 2)
    area2 = np.linalg.norm(np.cross(b-a, c-a), axis=1).sum()
    if not np.isclose(area2, surface_area2, rtol=1e-7, atol=0):
        raise ValueError("Tetrahedral boundary area differs from STL")
    caps = []
    for (plane, name), area in zip(ports, areas):
        cap = _port(points, boundary, plane, tol, name)
        a, b, c = points[cap].transpose(1, 0, 2)
        oriented = np.cross(b-a, c-a)[:, 2] * (-1 if name == "inlet" else 1)
        if np.any(oriented <= 0) or not np.isclose(oriented.sum(), area, rtol=1e-7, atol=0):
            raise ValueError(f"Invalid {name} boundary area or orientation")
        caps.append(cap)
    return points, tetra, caps[0], caps[1]
