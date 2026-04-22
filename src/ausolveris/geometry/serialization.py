# serialization.py
from typing import Dict, Any
from .model import GeometryModel

def export_geometry_summary(model: GeometryModel) -> Dict[str, Any]:
    """
    Export a stable, bounded summary of a GeometryModel for downstream consumers.
    
    Returns a dict with the following keys:
        - "parts": dict (model.parts if present and non-empty, else {})
        - "frames": dict (model.frames if present and non-empty, else {})
        - "primitives": dict with keys "points" and "edges" if model has them and 
          they are non-empty, otherwise the key is omitted entirely.
    
    The exported primitives are shallow copies (references to same dicts).
    This function does not mutate the model or change to_dict/from_dict behavior.
    """
    result: Dict[str, Any] = {}
    
    # Parts
    if hasattr(model, 'parts') and model.parts:
        result["parts"] = dict(model.parts)  # shallow copy
    else:
        result["parts"] = {}
    
    # Frames
    if hasattr(model, 'frames') and model.frames:
        result["frames"] = dict(model.frames)
    else:
        result["frames"] = {}
    
    # Primitives (optional) – only include if they exist and are non-empty
    primitives_dict = {}
    has_primitives = False
    
    # Check truthiness to ensure empty dicts {} are treated as "absent"
    if hasattr(model, 'points') and model.points:
        primitives_dict["points"] = dict(model.points)
        has_primitives = True
        
    if hasattr(model, 'edges') and model.edges:
        primitives_dict["edges"] = dict(model.edges)
        has_primitives = True
    
    if has_primitives:
        result["primitives"] = primitives_dict
    
    return result
