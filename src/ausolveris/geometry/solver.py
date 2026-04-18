from .model import GeometryModel


def run_geometry_solver_stub(model: GeometryModel) -> dict:
    if not isinstance(model, GeometryModel):
        raise TypeError("run_geometry_solver_stub expects a GeometryModel")

    visited = set()
    total_parts = 0
    total_anchors = 0
    total_boundaries = 0
    max_depth = 0

    def walk(part, depth):
        nonlocal total_parts, total_anchors, total_boundaries, max_depth
        obj_id = id(part)
        if obj_id in visited:
            return
        visited.add(obj_id)

        total_parts += 1
        total_anchors += len(part.anchors)
        total_boundaries += len(part.boundaries)
        if depth > max_depth:
            max_depth = depth

        for child in part.children:
            walk(child, depth + 1)

    for root_part in model.parts.values():
        walk(root_part, 1)

    return {
        "model_id": model.id,
        "model_name": model.name,
        "root_part_count": len(model.parts),
        "total_part_count": total_parts,
        "frame_count": len(model.frames),
        "anchor_count": total_anchors,
        "boundary_count": total_boundaries,
        "max_hierarchy_depth": max_depth,
    }
