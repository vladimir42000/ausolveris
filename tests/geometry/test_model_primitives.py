import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

import pytest
from src.ausolveris.geometry.model import GeometryModel


def test_valid_model_accepts_empty_primitives():
    model = GeometryModel(points={}, edges={})
    assert model.points == {}
    assert model.edges == {}


def test_valid_model_accepts_one_point():
    model = GeometryModel(points={'p1': (0.0, 0.0, 0.0)}, edges={})
    assert model.points == {'p1': (0.0, 0.0, 0.0)}
    assert model.edges == {}


def test_valid_model_accepts_two_points_and_one_edge():
    model = GeometryModel(
        points={'p1': (0.0, 0.0, 0.0), 'p2': (1.0, 0.0, 0.0)},
        edges={'e1': ('p1', 'p2')}
    )
    assert model.points == {'p1': (0.0, 0.0, 0.0), 'p2': (1.0, 0.0, 0.0)}
    assert model.edges == {'e1': ('p1', 'p2')}


def test_invalid_point_id_rejected():
    with pytest.raises(ValueError, match='Point key must be non-empty id string'):
        GeometryModel(points={'': (0.0, 0.0, 0.0)}, edges={})


def test_invalid_point_coordinates_length_rejected():
    with pytest.raises(ValueError, match='must contain exactly 3 numeric coordinates'):
        GeometryModel(points={'p1': (0.0, 0.0)}, edges={})


def test_invalid_edge_id_rejected():
    with pytest.raises(ValueError, match='Edge key must be non-empty id string'):
        GeometryModel(
            points={'p1': (0.0, 0.0, 0.0), 'p2': (1.0, 0.0, 0.0)},
            edges={'': ('p1', 'p2')}
        )


def test_edge_referencing_missing_point_rejected():
    with pytest.raises(ValueError, match='references missing point'):
        GeometryModel(
            points={'p1': (0.0, 0.0, 0.0)},
            edges={'e1': ('p1', 'p3')}
        )


def test_self_edge_rejected():
    with pytest.raises(ValueError, match='Self-edge not allowed'):
        GeometryModel(
            points={'p1': (0.0, 0.0, 0.0)},
            edges={'e1': ('p1', 'p1')}
        )
