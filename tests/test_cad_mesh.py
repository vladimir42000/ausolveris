"""Generated STL fixtures use millimetres and do not require a CAD application."""
import struct
import sys

import numpy as np
import pytest

from ausolveris.geometry.cad_mesh import mesh_air_stl


def _stl(path, facets, binary=False):
    if binary:
        data = bytearray(80) + struct.pack("<I", len(facets))
        for facet in facets:
            data += struct.pack("<12fH", 0, 0, 0, *np.ravel(facet), 0)
        path.write_bytes(data)
    else:
        with path.open("w") as stream:
            stream.write("solid duct\n")
            for facet in facets:
                stream.write("facet normal 0 0 0\nouter loop\n")
                for x, y, z in facet:
                    stream.write(f"vertex {x} {y} {z}\n")
                stream.write("endloop\nendfacet\n")
            stream.write("endsolid duct\n")
    return path


def _square(radius, z):
    return np.array([[-radius, -radius, z], [radius, -radius, z],
                     [radius, radius, z], [-radius, radius, z]])


def _strip(first, second):
    faces = []
    for i in range(4):
        j = (i + 1) % 4
        faces.extend([[first[i], first[j], second[j]], [first[i], second[j], second[i]]])
    return faces


def _disk(ring):
    return [ring[[0, 1, 2]], ring[[0, 2, 3]]]


def _box():
    low, high = _square(10, 0), _square(10, 40)
    return _disk(low) + _strip(low, high) + _disk(high)


@pytest.mark.parametrize("binary", [False, True])
def test_generated_duct(tmp_path, binary):
    pytest.importorskip("gmsh")
    path = _stl(tmp_path / "duct.stl", _box(), binary)
    points, tets, inlet, outlet = mesh_air_stl(path, units="mm", cell_size_m=.007)
    np.testing.assert_allclose(np.ptp(points, axis=0), [.02, .02, .04])
    assert len(tets) > 6 and tets.shape[1] == 4
    assert tets.min() >= 0 and tets.max() < len(points)
    a, b, c, d = points[tets].transpose(1, 0, 2)
    volumes = np.linalg.det(np.stack([b-a, c-a, d-a], axis=1)) / 6
    assert np.all(volumes > 0)
    assert volumes.sum() == pytest.approx(.02**2 * .04)
    faces = tets[:, [[0, 1, 2], [0, 1, 3], [0, 2, 3], [1, 2, 3]]].reshape(-1, 3)
    unique, counts = np.unique(np.sort(faces, axis=1), axis=0, return_counts=True)
    boundary = unique[counts == 1]
    for cap, z, sign in [(inlet, 0., -1), (outlet, .04, 1)]:
        expected = boundary[np.isclose(points[boundary, 2], z).all(axis=1)]
        assert set(map(tuple, np.sort(cap, axis=1))) == set(map(tuple, expected))
        a, b, c = points[cap].transpose(1, 0, 2)
        areas = sign * np.cross(b-a, c-a)[:, 2] / 2
        assert np.all(areas > 0)
        assert areas.sum() == pytest.approx(.02**2)


def test_explicit_recessed_inlet(tmp_path):
    pytest.importorskip("gmsh")
    outer, inner = _square(10, 0), _square(6, 0)
    recessed, top = _square(6, 5), _square(10, 40)
    facets = (_strip(outer, top) + _strip(outer, inner) + _strip(inner, recessed)
              + _disk(recessed) + _disk(top))
    path = _stl(tmp_path / "recess.stl", facets)
    points, _, inlet, outlet = mesh_air_stl(path, units="mm", cell_size_m=.008,
                                            inlet_z_m=.005, outlet_z_m=.04)
    np.testing.assert_allclose(points[inlet, 2], .005)
    np.testing.assert_allclose(points[outlet, 2], .04)


def test_reject_annular_printable_wall(tmp_path):
    outer, top = _square(10, 0), _square(10, 40)
    inner, inner_top = _square(8, 0), _square(8, 40)
    wall = _strip(outer, top) + _strip(inner, inner_top)
    wall += _strip(outer, inner) + _strip(top, inner_top)
    path = _stl(tmp_path / "wall.stl", wall, binary=True)
    with pytest.raises(ValueError, match="inlet must have one boundary loop"):
        mesh_air_stl(path, units="mm", cell_size_m=.005)


def test_reject_open_surface(tmp_path):
    path = _stl(tmp_path / "open.stl", _box()[1:])
    with pytest.raises(ValueError, match="closed"):
        mesh_air_stl(path, units="mm", cell_size_m=.005)


def test_require_units_and_valid_size(tmp_path):
    path = tmp_path / "unused.stl"
    with pytest.raises(TypeError, match="units"):
        mesh_air_stl(path, cell_size_m=.005)
    with pytest.raises(ValueError, match="units"):
        mesh_air_stl(path, units="auto", cell_size_m=.005)
    with pytest.raises(ValueError, match="cell_size_m"):
        mesh_air_stl(path, units="mm", cell_size_m=np.nan)


def test_missing_cap_and_optional_dependency(tmp_path, monkeypatch):
    path = _stl(tmp_path / "duct.stl", _box())
    monkeypatch.setitem(sys.modules, "gmsh", None)
    with pytest.raises(ValueError, match="No planar inlet"):
        mesh_air_stl(path, units="mm", cell_size_m=.005, inlet_z_m=.002)
    with pytest.raises(ImportError, match="optional gmsh"):
        mesh_air_stl(path, units="mm", cell_size_m=.005)
