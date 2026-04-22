# physics.py
import math
from typing import Set
from .model import GeometryModel

def flare_law_acoustic_objective(model: GeometryModel) -> float:
    """
    Compute acoustic objective based on flare geometry.
    Assumes points define a central axis (sorted by x) and edges form a single connected chain.
    Computes variance of cross-sectional areas (circular, area = π * r^2, r = sqrt(y^2+z^2)).
    Returns:
        - 0.0 if model has no points.
        - float('inf') if geometry is invalid (disconnected, single point, missing edges, inconsistent).
        - Positive variance for non‑uniform flares.
    """
    if not model.points:
        return 0.0
    if len(model.points) < 2:
        return float('inf')
    if not model.edges:
        return float('inf')
    
    # Build adjacency and check connectivity
    adj: dict[str, set[str]] = {}
    for start_id, end_id in model.edges.values():
        adj.setdefault(start_id, set()).add(end_id)
        adj.setdefault(end_id, set()).add(start_id)
    
    first = next(iter(model.points.keys()))
    visited: set[str] = set()
    stack = [first]
    while stack:
        node = stack.pop()
        if node in visited:
            continue
        visited.add(node)
        for nb in adj.get(node, []):
            if nb not in visited:
                stack.append(nb)
    
    if visited != set(model.points.keys()):
        return float('inf')
    
    # Extract (x, r) sorted by x
    points_data = []
    for pid, (x, y, z) in model.points.items():
        r = math.hypot(y, z)
        points_data.append((x, r))
    points_data.sort(key=lambda p: p[0])
    
    areas = [math.pi * (r**2) for _, r in points_data]
    mean = sum(areas) / len(areas)
    variance = sum((a - mean)**2 for a in areas) / len(areas)
    return variance
