import math

import numpy as np
import pytest

from ausolveris.geometry.bem import AnalyticalRigidSphereReferenceEvaluator
from ausolveris.geometry.benchmark import build_rigid_sphere_benchmark_fixture
from ausolveris.geometry.sphere_scattering import _panel_integrals, rigid_sphere_scattered_pressure


def test_refinement_preserves_requested_radius_and_planar_normals():
    center = (1, 2, 3)
    fixture = build_rigid_sphere_benchmark_fixture(
        "ben004_rigid_sphere_scattering_registered", 0.3, center, 2)
    np.testing.assert_allclose(np.linalg.norm(np.array(fixture.vertices) - center, axis=1), 0.3)
    for panel in fixture.panels:
        triangle = np.array(fixture.vertices)[list(panel.vertex_indices)]
        np.testing.assert_allclose(np.diff(triangle, axis=0) @ panel.outward_normal, 0, atol=1e-14)


@pytest.mark.parametrize("z", [0.1, 0.01])
def test_close_target_over_square_against_exact_solid_angle(z):
    square = np.array([[[-1,-1,0], [1,-1,0], [1,1,0]],
                       [[-1,-1,0], [1,1,0], [-1,1,0]]], dtype=float)
    actual = _panel_integrals(square, np.array([0,0,z]), np.array([0,0,1]), 0).sum()
    expected = -math.atan(1 / (z * math.sqrt(z*z + 2))) / math.pi
    assert actual == pytest.approx(expected, rel=1e-6)


def test_scattered_pressure_improves_with_mesh_refinement():
    points = [(2, 0, 0), (0, 2, 0), (-2, 0, 0)]
    exact = np.array(AnalyticalRigidSphereReferenceEvaluator(1, 1, 1, (1, 0, 0))
                     .evaluate(points)["scattered_pressure"])
    errors = [np.linalg.norm(rigid_sphere_scattered_pressure(1, level, points) - exact)
              / np.linalg.norm(exact) for level in (0, 1)]
    assert errors[1] < 0.07
    assert errors[1] < errors[0] / 2
