"""OPT-001: Structural observable scoring stub.

Provides deterministic scoring of geometry model complexity based on
solver observables. No search, no mutation, no physics meaning.
"""

from pathlib import Path
from typing import Union, Dict, Any

from .pipeline import (
    run_solver_pipeline_from_yaml_string,
    run_solver_pipeline_from_yaml_file,
)


# Required observable keys (from existing solver stub)
REQUIRED_OBSERVABLE_KEYS = {
    "model_id",
    "model_name",
    "root_part_count",
    "total_part_count",
    "frame_count",
    "anchor_count",
    "boundary_count",
    "max_hierarchy_depth",
}

COUNT_FIELDS = [
    "root_part_count",
    "total_part_count",
    "frame_count",
    "anchor_count",
    "boundary_count",
    "max_hierarchy_depth",
]


def _validate_and_extract_counts(observables: Dict[str, Any]) -> Dict[str, int]:
    """Validate observables and extract count fields."""
    missing = REQUIRED_OBSERVABLE_KEYS - set(observables.keys())
    if missing:
        raise ValueError(f"Missing required observable keys: {missing}")

    counts = {}
    for field in COUNT_FIELDS:
        value = observables[field]
        if not isinstance(value, (int, float)):
            raise TypeError(f"Field '{field}' must be numeric, got {type(value).__name__}")
        counts[field] = int(value)
    return counts


def score_solver_observables(observables: Dict[str, Any]) -> Dict[str, Any]:
    """
    Score solver observables according to structure_complexity_v1.

    Args:
        observables: Dict from run_geometry_solver_stub or pipeline.

    Returns:
        Dict with keys: model_id, model_name, score_name, score_value, components.
    """
    counts = _validate_and_extract_counts(observables)
    complexity_penalty = sum(counts.values())
    score_value = -complexity_penalty

    return {
        "model_id": observables["model_id"],
        "model_name": observables["model_name"],
        "score_name": "structure_complexity_v1",
        "score_value": score_value,
        "components": counts,
    }


def score_geometry_yaml_string(yaml_text: str) -> Dict[str, Any]:
    """
    Load geometry from YAML string, run pipeline, and score.

    Args:
        yaml_text: YAML string representing a GeometryModel.

    Returns:
        Score dict (same as score_solver_observables).
    """
    observables = run_solver_pipeline_from_yaml_string(yaml_text)
    return score_solver_observables(observables)


def score_geometry_yaml_file(path: Union[str, Path]) -> Dict[str, Any]:
    """
    Load geometry from YAML file, run pipeline, and score.

    Args:
        path: Path to YAML file.

    Returns:
        Score dict (same as score_solver_observables).
    """
    observables = run_solver_pipeline_from_yaml_file(path)
    return score_solver_observables(observables)
