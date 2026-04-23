# solver.py
from copy import deepcopy
from typing import Dict, Any, List, Tuple
from .model import GeometryModel
from .physics import flare_law_acoustic_objective
from .optimizer import newton_step, apply_step

# --- BASELINE FUNCTIONS (Refactored for recursive tree-walking) ---

def run_geometry_solver_stub(model: GeometryModel) -> Dict[str, Any]:
    """
    Baseline stub for compatibility with existing tests.
    Calculates observables by recursively walking the Part tree to support nested hierarchies.
    """
    if not isinstance(model, GeometryModel):
        raise TypeError("Input must be a GeometryModel instance")

    parts_dict = getattr(model, 'parts', {}) or {}
    frames = getattr(model, 'frames', {}) or {}
    
    def walk_tree(parts_list: List[Any]) -> Tuple[int, int, int, int]:
        """
        Recursively compute metrics for a list of parts.
        Returns: (total_count, max_depth, total_anchors, total_boundaries)
        """
        total_count = 0
        max_d = 0
        total_anchors = 0
        total_boundaries = 0
        
        for p in parts_list:
            total_count += 1
            # Sum anchors and boundaries for this specific part
            total_anchors += len(getattr(p, 'anchors', {}) or {})
            total_boundaries += len(getattr(p, 'boundaries', {}) or {})
            
            # Recurse into children if they exist
            children = getattr(p, 'children', []) or []
            if children:
                c_count, c_depth, c_anchors, c_bounds = walk_tree(children)
                total_count += c_count
                max_d = max(max_d, c_depth)
                total_anchors += c_anchors
                total_boundaries += c_bounds
                
        return total_count, (max_d + 1) if total_count > 0 else 0, total_anchors, total_boundaries

    # Process root-level parts
    root_parts = list(parts_dict.values())
    total_parts, depth, anchors, boundaries = walk_tree(root_parts)

    return {
        "model_id": getattr(model, "id", "test-id"),
        "model_name": getattr(model, "name", "Test Model"),
        "root_part_count": len(root_parts),
        "total_part_count": total_parts,
        "frame_count": len(frames),
        "anchor_count": anchors,
        "boundary_count": boundaries,
        "max_hierarchy_depth": depth,
    }

# --- NEW SOLVER LOGIC (SOL-002) ---

def optimize(model: GeometryModel, max_steps: int = 10) -> GeometryModel:
    """
    Run a fixed-step optimization loop using the flare-law acoustic objective.
    
    Args:
        model: Input geometry (not mutated)
        max_steps: Number of iterations to run
    
    Returns:
        New GeometryModel after applying all steps.
    """
    if max_steps < 0:
        raise ValueError("max_steps must be non-negative")
    
    current = deepcopy(model)
    for _ in range(max_steps):
        # Compute step based on current model using the acoustic physics objective
        step = newton_step(current, objective_func=flare_law_acoustic_objective)
        # Apply step to generate a new model instance
        current = apply_step(current, step)
    return current
