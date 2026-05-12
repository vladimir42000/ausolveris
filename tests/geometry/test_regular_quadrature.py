"""Tests for BEM-007B regular off-diagonal triangle quadrature."""

import re

import pytest

from ausolveris.geometry.bem import (
    BEM007B_REGULAR_QUADRATURE_METADATA,
    bem007b_regular_triangle_quadrature_rule,
    evaluate_regular_off_diagonal_triangle_quadrature,
)


SOURCE_TRIANGLE = ((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0))
TARGET_TRIANGLE = ((0.0, 0.0, 2.0), (1.0, 0.0, 2.0), (0.0, 1.0, 2.0))


def test_separated_flat_triangular_source_target_interaction_is_accepted():
    result = evaluate_regular_off_diagonal_triangle_quadrature(SOURCE_TRIANGLE, TARGET_TRIANGLE, 2.5)

    assert result["metadata"]["quadrature_stage"] == "bem007b_regular_off_diagonal_prototype"
    assert result["minimum_collocation_distance"] > 0.0
    assert result["source_area"] == pytest.approx(0.5)


def test_self_coincident_or_touching_panel_interaction_is_rejected():
    with pytest.raises(ValueError, match="distinct"):
        evaluate_regular_off_diagonal_triangle_quadrature(SOURCE_TRIANGLE, SOURCE_TRIANGLE, 2.5)

    touching_target = ((0.0, 0.0, 0.0), (1.0, 0.0, 2.0), (0.0, 1.0, 2.0))
    with pytest.raises(ValueError, match="touching|coincident"):
        evaluate_regular_off_diagonal_triangle_quadrature(SOURCE_TRIANGLE, touching_target, 2.5)


def test_degenerate_non_triangular_or_invalid_triangle_input_is_rejected():
    degenerate = ((0.0, 0.0, 0.0), (1.0, 1.0, 1.0), (2.0, 2.0, 2.0))
    with pytest.raises(ValueError, match="degenerate"):
        evaluate_regular_off_diagonal_triangle_quadrature(degenerate, TARGET_TRIANGLE, 2.5)

    non_triangular = ((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0))
    with pytest.raises(ValueError, match="3 vertices"):
        evaluate_regular_off_diagonal_triangle_quadrature(non_triangular, TARGET_TRIANGLE, 2.5)


def test_quadrature_rule_weights_are_deterministic_and_sum_to_reference_area():
    first = bem007b_regular_triangle_quadrature_rule()
    second = bem007b_regular_triangle_quadrature_rule()

    assert first == second
    assert len(first) == 7
    assert sum(weight for _, weight in first) == pytest.approx(0.5)


def test_regular_integral_returns_deterministic_complex_value():
    result = evaluate_regular_off_diagonal_triangle_quadrature(SOURCE_TRIANGLE, TARGET_TRIANGLE, 1.25)

    assert isinstance(result["value"], complex)
    assert result["value"].real == pytest.approx(-0.01610681798068177)
    assert result["value"].imag == pytest.approx(0.011201346044412213)


def test_repeated_identical_evaluation_gives_identical_result_and_package_id():
    first = evaluate_regular_off_diagonal_triangle_quadrature(SOURCE_TRIANGLE, TARGET_TRIANGLE, 1.25)
    second = evaluate_regular_off_diagonal_triangle_quadrature(SOURCE_TRIANGLE, TARGET_TRIANGLE, 1.25)

    assert first["value"] == second["value"]
    assert first["package_id"] == second["package_id"]


def test_package_id_is_sha256_like_and_stable_for_identical_inputs():
    result = evaluate_regular_off_diagonal_triangle_quadrature(SOURCE_TRIANGLE, TARGET_TRIANGLE, 1.25)

    assert re.fullmatch(r"[0-9a-f]{64}", result["package_id"])
    assert result["package_id"] == evaluate_regular_off_diagonal_triangle_quadrature(
        SOURCE_TRIANGLE, TARGET_TRIANGLE, 1.25
    )["package_id"]


def test_package_id_changes_when_deterministic_inputs_change():
    baseline = evaluate_regular_off_diagonal_triangle_quadrature(SOURCE_TRIANGLE, TARGET_TRIANGLE, 1.25)
    changed_k = evaluate_regular_off_diagonal_triangle_quadrature(SOURCE_TRIANGLE, TARGET_TRIANGLE, 1.50)
    moved_target = evaluate_regular_off_diagonal_triangle_quadrature(
        SOURCE_TRIANGLE,
        ((0.0, 0.0, 2.2), (1.0, 0.0, 2.2), (0.0, 1.0, 2.2)),
        1.25,
    )

    assert baseline["package_id"] != changed_k["package_id"]
    assert baseline["package_id"] != moved_target["package_id"]


def test_metadata_records_regular_not_singular_and_not_adaptive():
    result = evaluate_regular_off_diagonal_triangle_quadrature(SOURCE_TRIANGLE, TARGET_TRIANGLE, 1.25)
    metadata = result["metadata"]

    assert metadata["regular_quadrature_implemented"] is True
    assert metadata["singular_quadrature_implemented"] is False
    assert metadata["adaptive_integration_used"] is False
    assert metadata == BEM007B_REGULAR_QUADRATURE_METADATA


def test_metadata_records_no_matrix_no_benchmark_and_no_system_physics_claims():
    result = evaluate_regular_off_diagonal_triangle_quadrature(SOURCE_TRIANGLE, TARGET_TRIANGLE, 1.25)
    metadata = result["metadata"]

    assert metadata["physical_a_matrix_assembled"] is False
    assert metadata["benchmark_passed"] is False
    assert metadata["non_physical"] is True
    assert "spl" not in metadata
    assert "impedance" not in metadata
