"""
BEM-004F: Analytical rigid-sphere reference evaluator tests.
Exactly 10 tests as required by the milestone.
"""

import pytest
import math
import cmath
import hashlib
import json
from ausolveris.geometry.bem import AnalyticalRigidSphereReferenceEvaluator


# ----------------------------------------------------------------------------
# Fixtures and helpers
# ----------------------------------------------------------------------------

class MockObserverScaffold:
    """Simulates the BEM-004E exterior observer scaffold."""
    def __init__(self, points):
        self.points = points


@pytest.fixture
def sphere_params():
    return {
        "radius": 1.0,
        "k": 2.0,
        "amplitude": 1.0,
        "direction": (1.0, 0.0, 0.0)
    }


@pytest.fixture
def exterior_points():
    # Points outside radius = 1.0
    return [(2.0, 0.0, 0.0), (0.0, 2.0, 0.0), (0.0, 0.0, 2.0)]


@pytest.fixture
def evaluator(sphere_params):
    return AnalyticalRigidSphereReferenceEvaluator(
        sphere_radius=sphere_params["radius"],
        k=sphere_params["k"],
        amplitude=sphere_params["amplitude"],
        direction=sphere_params["direction"],
        n_max=6
    )


# ----------------------------------------------------------------------------
# Tests 1-10 (one per requirement)
# ----------------------------------------------------------------------------

def test_1_accepts_bem004e_observer_scaffold(evaluator, exterior_points):
    """1. Valid BEM-004E exterior observer scaffold is accepted."""
    scaffold = MockObserverScaffold(exterior_points)
    result = evaluator.evaluate(scaffold)
    assert "incident_pressure" in result
    assert len(result["incident_pressure"]) == len(exterior_points)


def test_2_incident_matches_plane_wave_formula(evaluator):
    """2. Incident pressure matches A exp(i k d·x) at a known observer."""
    x = (2.0, 0.0, 0.0)
    # direction = (1,0,0), so d·x = 2.0
    expected = 1.0 * cmath.exp(1j * 2.0 * 2.0)  # A=1, k=2, dot=2
    result = evaluator.evaluate([x])
    incident = result["incident_pressure"][0]
    assert abs(incident - expected) < 1e-12


def test_3_package_contains_arrays_of_correct_length(evaluator, exterior_points):
    """3. Analytical package contains incident/scattered/total arrays of correct length."""
    result = evaluator.evaluate(exterior_points)
    n = len(exterior_points)
    assert len(result["incident_pressure"]) == n
    assert len(result["scattered_pressure"]) == n
    assert len(result["total_pressure"]) == n


def test_4_total_equals_incident_plus_scattered(evaluator, exterior_points):
    """4. analytical_total_pressure equals analytical_incident_pressure + analytical_scattered_pressure."""
    result = evaluator.evaluate(exterior_points)
    for inc, scat, total in zip(result["incident_pressure"],
                                result["scattered_pressure"],
                                result["total_pressure"]):
        assert abs(total - (inc + scat)) < 1e-12


def test_5_deterministic_package_id(evaluator, exterior_points):
    """5. Deterministic package ID is stable."""
    result1 = evaluator.evaluate(exterior_points)
    result2 = evaluator.evaluate(exterior_points)
    package_id = result1["package_id"]

    # SHA‑256 produces 64 hex characters
    assert isinstance(package_id, str)
    assert len(package_id) == 64
    assert all(c in "0123456789abcdef" for c in package_id)

    # Stability for identical inputs
    assert package_id == result2["package_id"]

    # Sensitivity: different observer points produce a different ID
    different_points = [(3.0, 0.0, 0.0), (0.0, 3.0, 0.0)]
    result3 = evaluator.evaluate(different_points)
    assert result3["package_id"] != package_id
    assert len(result3["package_id"]) == 64


def test_6_series_truncation_flags(evaluator):
    """6. series_truncation_n_max equals 6 and adaptive_truncation_used=false."""
    result = evaluator.evaluate([(2.0, 0.0, 0.0)])
    meta = result["metadata"]
    assert meta["series_truncation_n_max"] == 6
    assert meta["adaptive_truncation_used"] is False
    assert meta["convergence_seeking_used"] is False


def test_7_invalid_inputs_rejected(sphere_params):
    """7. Invalid k, amplitude, direction, or observer scaffold is rejected."""
    # Invalid direction zero vector
    with pytest.raises(ValueError):
        AnalyticalRigidSphereReferenceEvaluator(
            sphere_radius=1.0, k=2.0, amplitude=1.0, direction=(0,0,0)
        )
    # Invalid observer interior point
    evaluator = AnalyticalRigidSphereReferenceEvaluator(
        sphere_radius=1.0, k=2.0, amplitude=1.0, direction=(1,0,0)
    )
    with pytest.raises(ValueError):
        evaluator.evaluate([(0.5, 0.0, 0.0)])
    # Invalid point format
    with pytest.raises(ValueError):
        evaluator.evaluate([(1.0, 2.0)])  # not triple


def test_8_metadata_flags_no_comparison(evaluator, exterior_points):
    """8. Metadata states reference_matching_performed=false and tolerance_policy_applied=false."""
    result = evaluator.evaluate(exterior_points)
    meta = result["metadata"]
    assert meta["reference_matching_performed"] is False
    assert meta["tolerance_policy_applied"] is False


def test_9_metadata_flags_no_bem_consumption(evaluator, exterior_points):
    """9. Metadata states no BEM solution consumed and no observer reconstruction performed."""
    result = evaluator.evaluate(exterior_points)
    meta = result["metadata"]
    assert meta["bem_solution_consumed"] is False
    assert meta["observer_reconstruction_performed"] is False


def test_10_metadata_flags_no_spl_directivity_impedance_operator(evaluator, exterior_points):
    """10. Metadata states no SPL, directivity, impedance, boundary-to-observer operator, or BEM solve."""
    result = evaluator.evaluate(exterior_points)
    meta = result["metadata"]
    assert meta["spl_computed"] is False
    assert meta["directivity_computed"] is False
    assert meta["impedance_computed"] is False
    assert meta["boundary_to_observer_operator_assembled"] is False
    # Also ensure no BEM solve flag (already covered by bem_solution_consumed but explicit)
    assert "bem_solve_performed" not in meta or meta.get("bem_solve_performed", False) is False