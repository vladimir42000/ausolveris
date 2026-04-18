"""Lightweight structural validator for GeometryModel dicts.

Validates the exact shape produced by GeometryModel.to_dict().
Raises ValueError with descriptive messages.
"""

from typing import Any, Dict, Set


def validate_geometry_dict(data: Dict[str, Any]) -> None:
    """
    Validate a dictionary representing a GeometryModel.

    Expected structure (from GeometryModel.to_dict()):
    {
        "id": <optional str>,
        "name": <str>,               # may be empty string
        "parts": {                   # may be empty dict
            "<part_id>": {
                "id": <str>,
                "name": <str>,       # must be non-empty (per existing model)
                "children": [<part_dict>, ...],
                "anchors": {
                    "<anchor_id>": {"id": <str>, "frame_id": <optional str>},
                    ...
                },
                "boundaries": {
                    "<boundary_id>": {"id": <str>},
                    ...
                },
                "metadata": {...}
            },
            ...
        },
        "frames": {                  # may be empty dict
            "<frame_id>": {
                "id": <str>,
                "origin": [x, y, z],
                "orientation": [[r11,r12,r13],[r21,r22,r23],[r31,r32,r33]],
                "units": <str>
            },
            ...
        }
    }

    Raises ValueError on any violation.
    """
    if not isinstance(data, dict):
        raise ValueError("Geometry data must be a dictionary")

    # Required top-level keys
    required_top = {"name", "parts", "frames"}
    if not required_top.issubset(data.keys()):
        missing = required_top - set(data.keys())
        raise ValueError(f"Missing required top-level keys: {missing}")

    # Disallow unknown top-level keys (strict mode)
    allowed_top = {"id", "name", "parts", "frames"}
    unknown_top = set(data.keys()) - allowed_top
    if unknown_top:
        raise ValueError(f"Unknown top-level keys: {unknown_top}")

    # Validate name (empty string allowed)
    if not isinstance(data["name"], str):
        raise ValueError("'name' must be a string")
    # No non-empty requirement

    # Optional id
    if "id" in data:
        if not isinstance(data["id"], str):
            raise ValueError("'id' must be a string")
        if data["id"] == "":
            raise ValueError("'id' must not be empty")

    # Validate parts (may be empty)
    parts = data["parts"]
    if not isinstance(parts, dict):
        raise ValueError("'parts' must be a dictionary")

    # Validate frames (may be empty)
    frames = data["frames"]
    if not isinstance(frames, dict):
        raise ValueError("'frames' must be a dictionary")

    # Track all part IDs across hierarchy for duplicate detection
    all_part_ids: Set[str] = set()
    all_frame_ids: Set[str] = set()

    # Validate frames first (so anchor references can be checked)
    for frame_id, frame_dict in frames.items():
        _validate_frame(frame_id, frame_dict)
        if frame_id in all_frame_ids:
            raise ValueError(f"Duplicate frame id '{frame_id}'")
        all_frame_ids.add(frame_id)

    # Validate parts recursively
    for part_id, part_dict in parts.items():
        _validate_part(part_id, part_dict, all_part_ids, all_frame_ids, visited_parts=set())


def _validate_frame(frame_id: str, frame_dict: Any) -> None:
    """Validate a single frame dictionary."""
    if not isinstance(frame_dict, dict):
        raise ValueError(f"Frame '{frame_id}' must be a dictionary")

    required = {"id", "origin", "orientation", "units"}
    if not required.issubset(frame_dict.keys()):
        missing = required - set(frame_dict.keys())
        raise ValueError(f"Frame '{frame_id}' missing keys: {missing}")

    # id must match the dict key
    if frame_dict["id"] != frame_id:
        raise ValueError(f"Frame dict key '{frame_id}' does not match 'id' field '{frame_dict['id']}'")

    # origin: list of 3 floats
    origin = frame_dict["origin"]
    if not isinstance(origin, list) or len(origin) != 3:
        raise ValueError(f"Frame '{frame_id}'.origin must be a list of 3 numbers")
    for i, val in enumerate(origin):
        if not isinstance(val, (int, float)):
            raise ValueError(f"Frame '{frame_id}'.origin[{i}] must be a number")

    # orientation: 3x3 list of floats
    orient = frame_dict["orientation"]
    if not isinstance(orient, list) or len(orient) != 3:
        raise ValueError(f"Frame '{frame_id}'.orientation must be a 3x3 matrix")
    for i, row in enumerate(orient):
        if not isinstance(row, list) or len(row) != 3:
            raise ValueError(f"Frame '{frame_id}'.orientation row {i} must be a list of 3 numbers")
        for j, val in enumerate(row):
            if not isinstance(val, (int, float)):
                raise ValueError(f"Frame '{frame_id}'.orientation[{i}][{j}] must be a number")

    # units: string
    if not isinstance(frame_dict["units"], str):
        raise ValueError(f"Frame '{frame_id}'.units must be a string")

    # No unknown keys
    allowed = {"id", "origin", "orientation", "units"}
    unknown = set(frame_dict.keys()) - allowed
    if unknown:
        raise ValueError(f"Frame '{frame_id}' has unknown keys: {unknown}")


def _validate_part(
    part_id: str,
    part_dict: Any,
    all_part_ids: Set[str],
    all_frame_ids: Set[str],
    visited_parts: Set[str],
) -> None:
    """
    Validate a part dictionary recursively.
    visited_parts tracks the path for cycle detection.
    """
    if not isinstance(part_dict, dict):
        raise ValueError(f"Part '{part_id}' must be a dictionary")

    required = {"id", "name", "children", "anchors", "boundaries", "metadata"}
    if not required.issubset(part_dict.keys()):
        missing = required - set(part_dict.keys())
        raise ValueError(f"Part '{part_id}' missing keys: {missing}")

    # id must match the dict key
    if part_dict["id"] != part_id:
        raise ValueError(f"Part dict key '{part_id}' does not match 'id' field '{part_dict['id']}'")

    # Check duplicate part id across hierarchy
    if part_id in all_part_ids:
        raise ValueError(f"Duplicate part id '{part_id}'")
    all_part_ids.add(part_id)

    # Check for cycles
    if part_id in visited_parts:
        raise ValueError(f"Cyclic part hierarchy detected involving part '{part_id}'")
    visited_parts.add(part_id)

    # name (must be a string, non-empty per existing model)
    if not isinstance(part_dict["name"], str):
        raise ValueError(f"Part '{part_id}'.name must be a string")
    if part_dict["name"] == "":
        raise ValueError(f"Part '{part_id}'.name must not be empty")

    # metadata can be any dict, but must be a dict
    metadata = part_dict["metadata"]
    if not isinstance(metadata, dict):
        raise ValueError(f"Part '{part_id}'.metadata must be a dictionary")

    # Validate anchors
    anchors = part_dict["anchors"]
    if not isinstance(anchors, dict):
        raise ValueError(f"Part '{part_id}'.anchors must be a dictionary")
    for anchor_id, anchor_dict in anchors.items():
        _validate_anchor(anchor_id, anchor_dict, all_frame_ids)

    # Validate boundaries
    boundaries = part_dict["boundaries"]
    if not isinstance(boundaries, dict):
        raise ValueError(f"Part '{part_id}'.boundaries must be a dictionary")
    for boundary_id, boundary_dict in boundaries.items():
        _validate_boundary(boundary_id, boundary_dict)

    # Validate children recursively
    children = part_dict["children"]
    if not isinstance(children, list):
        raise ValueError(f"Part '{part_id}'.children must be a list")
    for i, child_dict in enumerate(children):
        if not isinstance(child_dict, dict):
            raise ValueError(f"Part '{part_id}'.children[{i}] must be a dictionary")
        child_id = child_dict.get("id")
        if not isinstance(child_id, str):
            raise ValueError(f"Part '{part_id}'.children[{i}] missing or invalid 'id'")
        _validate_part(child_id, child_dict, all_part_ids, all_frame_ids, visited_parts.copy())

    # No unknown keys in part dict
    allowed = {"id", "name", "children", "anchors", "boundaries", "metadata"}
    unknown = set(part_dict.keys()) - allowed
    if unknown:
        raise ValueError(f"Part '{part_id}' has unknown keys: {unknown}")


def _validate_anchor(anchor_id: str, anchor_dict: Any, all_frame_ids: Set[str]) -> None:
    """Validate a single anchor dictionary."""
    if not isinstance(anchor_dict, dict):
        raise ValueError(f"Anchor '{anchor_id}' must be a dictionary")

    if "id" not in anchor_dict:
        raise ValueError(f"Anchor '{anchor_id}' missing 'id' key")
    if anchor_dict["id"] != anchor_id:
        raise ValueError(f"Anchor dict key '{anchor_id}' does not match 'id' field '{anchor_dict['id']}'")

    # Only allowed keys: id, frame_id (optional)
    allowed = {"id", "frame_id"}
    unknown = set(anchor_dict.keys()) - allowed
    if unknown:
        raise ValueError(f"Anchor '{anchor_id}' has unknown keys: {unknown}")

    # frame_id if present must be a string and reference existing frame
    if "frame_id" in anchor_dict:
        frame_id = anchor_dict["frame_id"]
        if not isinstance(frame_id, str):
            raise ValueError(f"Anchor '{anchor_id}'.frame_id must be a string")
        if frame_id not in all_frame_ids:
            raise ValueError(f"Anchor '{anchor_id}' references unknown frame '{frame_id}'")


def _validate_boundary(boundary_id: str, boundary_dict: Any) -> None:
    """Validate a single boundary dictionary."""
    if not isinstance(boundary_dict, dict):
        raise ValueError(f"Boundary '{boundary_id}' must be a dictionary")

    if "id" not in boundary_dict:
        raise ValueError(f"Boundary '{boundary_id}' missing 'id' key")
    if boundary_dict["id"] != boundary_id:
        raise ValueError(f"Boundary dict key '{boundary_id}' does not match 'id' field '{boundary_dict['id']}'")

    # Only allowed key: id
    allowed = {"id"}
    unknown = set(boundary_dict.keys()) - allowed
    if unknown:
        raise ValueError(f"Boundary '{boundary_id}' has unknown keys: {unknown}")
