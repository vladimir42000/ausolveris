# physics.py
import math
from .model import GeometryModel

def _is_single_connected_component(model: GeometryModel) -> bool:
    """Check if all points are connected in a single component via edges (DFS)."""
    if not model.points or not model.edges:
        return False
    # Build adjacency list
    adj = {pid: set() for pid in model.points}
    for start_id, end_id in model.edges.values():
        if start_id in adj and end_id in adj:
            adj[start_id].add(end_id)
            adj[end_id].add(start_id)
    # Start DFS from any point
    start = next(iter(model.points))
    visited = set()
    stack = [start]
    while stack:
        node = stack.pop()
        if node in visited:
            continue
        visited.add(node)
        for neigh in adj.get(node, []):
            if neigh not in visited:
                stack.append(neigh)
    return len(visited) == len(model.points)

def flare_law_acoustic_objective(model: GeometryModel) -> float:
    """
    Normalized acoustic objective in [0,1]:
    - 0.0 : empty model or perfect uniformity
    - 1.0 : invalid/degenerate geometry (disconnected, single point, missing edges, etc.)
    - else: normalized variance capped at 1.0
    """
    # Empty model → neutral (0.0)
    if not model.points:
        return 0.0

    # Need at least 2 points
    if len(model.points) < 2:
        return 1.0

    # Must have edges and form a single connected component
    if not model.edges or not _is_single_connected_component(model):
        return 1.0

    # Extract points sorted by x
    point_list = []
    for (x, y, z) in model.points.values():
        r = math.hypot(y, z)
        if math.isnan(r):
            return 1.0
        point_list.append((x, r))
    point_list.sort(key=lambda p: p[0])

    # Compute areas
    areas = [math.pi * (r**2) for (_, r) in point_list]
    mean = sum(areas) / len(areas)
    variance = sum((a - mean)**2 for a in areas) / len(areas)

    # Normalize to [0,1] with cap
    MAX_VARIANCE = 1000.0  # heuristic upper bound
    normalized = min(variance / MAX_VARIANCE, 1.0)
    return normalized
