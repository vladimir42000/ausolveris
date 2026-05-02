"""
BEM-005A: Observer reconstruction scaffold tests.
Exactly 10 tests as required.
"""

import pytest
import hashlib
import json
from ausolveris.geometry.bem import ObserverReconstructionScaffold


# ----------------------------------------------------------------------------
# Fixtures and helpers
# ----------------------------------------------------------------------------

class MockObserverScaffold:
    """Simulates BEM-004E exterior observer scaffold."""
    def __init__(self, points):
        self.points = points


@pytest.fixture
def valid_observer_scaffold():
    return MockObserverScaffold([(2.0, 0.0, 0.0), (0.0, 2.0, 0.0), (0.0, 0.0, 2.0)])


@pytest.fixture
def valid_boundary_stub():
    return {"boundary_data_present": True, "mesh": "sphere", "solution": "stub"}


@pytest.fixture
def scaffold(valid_observer_scaffold, valid_boundary_stub):
    return ObserverReconstructionScaffold(valid_observer_scaffold, valid_boundary_stub)


# ----------------------------------------------------------------------------
# Tests 1–10
# ----------------------------------------------------------------------------

def test_1_accepts_valid_observer_scaffold(valid_observer_scaffold, valid_boundary_stub):
    """1. Valid BEM-004E exterior observer scaffold is accepted."""
    scaffold = ObserverReconstructionScaffold(valid_observer_scaffold, valid_boundary_stub)
    assert scaffold.observer_points == valid_observer_scaffold.points


def test_2_accepts_stub_boundary_package(valid_observer_scaffold, valid_boundary_stub):
    """2. Stub boundary-solution package is accepted when structurally valid."""
    scaffold = ObserverReconstructionScaffold(valid_observer_scaffold, valid_boundary_stub)
    assert scaffold.boundary_stub == valid_boundary_stub


def test_3_exposes_three_pressure_fields(scaffold):
    """3. Package exposes reconstructed_incident/scattered/total_pressure."""
    result = scaffold.reconstruct()
    assert "reconstructed_incident_pressure" in result
    assert "reconstructed_scattered_pressure" in result
    assert "reconstructed_total_pressure" in result


def test_4_pressure_arrays_match_observer_length(scaffold, valid_observer_scaffold):
    """4. Reconstructed pressure arrays have lengths matching the observer scaffold."""
    result = scaffold.reconstruct()
    n_obs = len(valid_observer_scaffold.points)
    assert len(result["reconstructed_incident_pressure"]) == n_obs
    assert len(result["reconstructed_scattered_pressure"]) == n_obs
    assert len(result["reconstructed_total_pressure"]) == n_obs


def test_5_H_descriptor_exists_not_assembled(scaffold):
    """5. H descriptor/scaffold exists but boundary_to_observer_operator_assembled is false."""
    result = scaffold.reconstruct()
    assert "H_descriptor" in result
    assert result["metadata"]["boundary_to_observer_operator_assembled"] is False
    assert result["H_descriptor"]["assembled"] is False


def test_6_reconstruction_not_performed_non_physical(scaffold):
    """6. Reconstruction is not performed and output is marked non-physical."""
    result = scaffold.reconstruct()
    assert result["metadata"]["reconstruction_performed"] is False
    assert result["metadata"]["non_physical"] is True


def test_7_no_analytical_comparison_no_tolerance(scaffold):
    """7. Analytical reference comparison is not performed and tolerance policy is not applied."""
    result = scaffold.reconstruct()
    assert result["metadata"]["analytical_reference_comparison_performed"] is False
    assert result["metadata"]["tolerance_policy_applied"] is False


def test_8_no_singular_SPL_directivity_impedance(scaffold):
    """8. Singular quadrature, SPL, directivity, and impedance flags are all false."""
    result = scaffold.reconstruct()
    meta = result["metadata"]
    assert meta["singular_quadrature_implemented"] is False
    assert meta["spl_computed"] is False
    assert meta["directivity_computed"] is False
    assert meta["impedance_computed"] is False


def test_9_deterministic_package_id(scaffold):
    """9. Deterministic package ID is SHA-256-like, stable, not built-in hash."""
    result1 = scaffold.reconstruct()
    result2 = scaffold.reconstruct()
    pid = result1["package_id"]
    # SHA-256 produces 64 hex chars
    assert isinstance(pid, str)
    assert len(pid) == 64
    assert all(c in "0123456789abcdef" for c in pid)
    # Stable for identical inputs
    assert pid == result2["package_id"]
    # Changing inputs changes ID
    different_obs = MockObserverScaffold([(5.0, 0.0, 0.0)])
    scaffold2 = ObserverReconstructionScaffold(different_obs, {"stub": "diff"})
    result3 = scaffold2.reconstruct()
    assert result3["package_id"] != pid


def test_10_rejects_invalid_inputs(valid_boundary_stub):
    """10. Invalid observer scaffold or invalid boundary-solution package is rejected."""
    # Invalid observer scaffold (no points)
    class BadScaffold:
        pass
    with pytest.raises(ValueError):
        ObserverReconstructionScaffold(BadScaffold(), valid_boundary_stub)
    # Invalid boundary stub (not dict)
    with pytest.raises(ValueError):
        ObserverReconstructionScaffold(MockObserverScaffold([(1,0,0)]), "not a dict")
    # Invalid point format
    with pytest.raises(ValueError):
        ObserverReconstructionScaffold(MockObserverScaffold([(1,0)]), valid_boundary_stub)
