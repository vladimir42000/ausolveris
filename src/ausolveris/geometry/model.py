"""
Canonical geometry data model.

This module defines the minimal canonical geometry representation
as per the architecture specifications (GEO-01 through GEO-05).
It includes parts, anchors, frames, and boundaries without
solver coupling or physics assumptions.
"""

from typing import Dict, List, Optional, Tuple, Any
import uuid


class Frame:
    """Coordinate frame with explicit origin, orientation, and units."""
    
    def __init__(
        self,
        id: str,
        origin: Tuple[float, float, float] = (0.0, 0.0, 0.0),
        orientation: Tuple[
            Tuple[float, float, float],
            Tuple[float, float, float],
            Tuple[float, float, float]
        ] = ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0)),
        units: str = "meter"
    ):
        if not id or not id.strip():
            raise ValueError('Frame id must be non-empty')
        self.id = id.strip()
        
        if len(origin) != 3:
            raise ValueError('Origin must have exactly three elements')
        self.origin = origin
        
        if len(orientation) != 3:
            raise ValueError('Orientation must have three rows')
        for row in orientation:
            if len(row) != 3:
                raise ValueError('Each orientation row must have three elements')
        self.orientation = orientation
        
        self.units = units
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert frame to YAML-safe dictionary."""
        # Convert tuples to lists for YAML compatibility
        origin_list = list(self.origin)
        orientation_list = [list(row) for row in self.orientation]
        return {
            'id': self.id,
            'origin': origin_list,
            'orientation': orientation_list,
            'units': self.units
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Frame':
        """Create frame from dictionary."""
        # Convert lists back to tuples
        origin = data.get('origin', [0.0, 0.0, 0.0])
        orientation = data.get('orientation', [[1.0,0.0,0.0],[0.0,1.0,0.0],[0.0,0.0,1.0]])
        return cls(
            id=data['id'],
            origin=tuple(float(x) for x in origin),
            orientation=tuple(tuple(float(x) for x in row) for row in orientation),
            units=data.get('units', 'meter')
        )


class Anchor:
    """Named geometric reference point attached to a part."""
    
    def __init__(self, id: str, frame_id: Optional[str] = None):
        if not id or not id.strip():
            raise ValueError('Anchor id must be non-empty')
        self.id = id.strip()
        self.frame_id = frame_id
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert anchor to YAML-safe dictionary."""
        result = {'id': self.id}
        if self.frame_id is not None:
            result['frame_id'] = self.frame_id
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Anchor':
        """Create anchor from dictionary."""
        return cls(
            id=data['id'],
            frame_id=data.get('frame_id')
        )


class Boundary:
    """Named geometric locus or region attached to a part."""
    
    def __init__(self, id: str):
        if not id or not id.strip():
            raise ValueError('Boundary id must be non-empty')
        self.id = id.strip()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert boundary to YAML-safe dictionary."""
        return {
            'id': self.id
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Boundary':
        """Create boundary from dictionary."""
        return cls(
            id=data['id']
        )


class Part:
    """Geometric part with identity, children, and attached references."""
    
    def __init__(
        self,
        id: str,
        name: str,
        children: Optional[List['Part']] = None,
        anchors: Optional[Dict[str, Anchor]] = None,
        boundaries: Optional[Dict[str, Boundary]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        if not id or not id.strip():
            raise ValueError('Part id must be non-empty')
        self.id = id.strip()
        
        if not name or not name.strip():
            raise ValueError('Part name must be non-empty')
        self.name = name.strip()
        
        self.children = children if children is not None else []
        self.anchors = anchors if anchors is not None else {}
        self.boundaries = boundaries if boundaries is not None else {}
        self.metadata = metadata if metadata is not None else {}
        
        # Validate that anchor and boundary keys match their IDs
        self._validate()
    
    def _validate(self):
        """Validate that anchor and boundary keys match their IDs."""
        for key, anchor in self.anchors.items():
            if key != anchor.id:
                raise ValueError(
                    f'Anchor dictionary key "{key}" does not match contained Anchor.id "{anchor.id}"'
                )
        
        for key, boundary in self.boundaries.items():
            if key != boundary.id:
                raise ValueError(
                    f'Boundary dictionary key "{key}" does not match contained Boundary.id "{boundary.id}"'
                )
        
        # Note: children validation is done at the GeometryModel level
        # to avoid infinite recursion and to check hierarchy-wide constraints
        # (duplicate ids, cycles). We do NOT recursively call child._validate() here.
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert part to YAML-safe dictionary."""
        return {
            'id': self.id,
            'name': self.name,
            'children': [child.to_dict() for child in self.children],
            'anchors': {k: v.to_dict() for k, v in self.anchors.items()},
            'boundaries': {k: v.to_dict() for k, v in self.boundaries.items()},
            'metadata': self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Part':
        """Create part from dictionary."""
        # Handle children recursively
        children_data = data.get('children', [])
        anchors_data = data.get('anchors', {})
        boundaries_data = data.get('boundaries', {})
        metadata = data.get('metadata', {})
        
        # Create anchors and boundaries
        anchors = {k: Anchor.from_dict(v) for k, v in anchors_data.items()}
        boundaries = {k: Boundary.from_dict(v) for k, v in boundaries_data.items()}
        
        # Create the part
        part = cls(
            id=data['id'],
            name=data['name'],
            children=[],
            anchors=anchors,
            boundaries=boundaries,
            metadata=metadata
        )
        
        # Add children recursively
        for child_data in children_data:
            part.children.append(cls.from_dict(child_data))
        
        return part


class GeometryModel:
    """Top-level container for canonical geometry."""
    
    def __init__(
        self,
        id: Optional[str] = None,
        name: str = "",
        parts: Optional[Dict[str, Part]] = None,
        frames: Optional[Dict[str, Frame]] = None,
        points: Optional[Dict[str, Tuple[float, float, float]]] = None,
        edges: Optional[Dict[str, Tuple[str, str]]] = None
    ):
        self.id = id if id is not None else str(uuid.uuid4())
        self.name = name.strip()
        self.parts = parts if parts is not None else {}
        self.frames = frames if frames is not None else {}
        self.points = points if points is not None else {}
        self.edges = edges if edges is not None else {}
        
        # Validate references
        self._validate()
    
    def _validate(self):
        """Validate that all references are consistent."""
        # Check that part keys match part IDs
        for key, part in self.parts.items():
            if key != part.id:
                raise ValueError(
                    f'Part dictionary key "{key}" does not match contained Part.id "{part.id}"'
                )
        
        # Check that frame keys match frame IDs
        for key, frame in self.frames.items():
            if key != frame.id:
                raise ValueError(
                    f'Frame dictionary key "{key}" does not match contained Frame.id "{frame.id}"'
                )
        
        # Check for duplicate ids across parts and frames
        all_ids = set()
        for part_id in self.parts.keys():
            if part_id in all_ids:
                raise ValueError(f'Duplicate id across parts/frames: {part_id}')
            all_ids.add(part_id)
        
        for frame_id in self.frames.keys():
            if frame_id in all_ids:
                raise ValueError(f'Duplicate id across parts/frames: {frame_id}')
            all_ids.add(frame_id)
        
        # Validate each part's internal consistency
        for part in self.parts.values():
            part._validate()
        
        # Validate anchor frame references and check hierarchy integrity
        frame_ids = set(self.frames.keys())
        seen_part_ids = set()
        
        def traverse_part_hierarchy(part, current_path_objects):
            """Traverse part hierarchy checking for cycles and duplicate ids."""
            # Check for cycles using object identity in current traversal path
            part_object_id = id(part)
            if part_object_id in current_path_objects:
                raise ValueError(f'Cycle detected in part hierarchy involving part "{part.id}"')
            
            # Check for duplicate part ids across the entire hierarchy
            if part.id in seen_part_ids:
                raise ValueError(f'Duplicate part id "{part.id}" found in hierarchy')
            seen_part_ids.add(part.id)
            
            # Check anchors
            for anchor in part.anchors.values():
                if anchor.frame_id is not None and anchor.frame_id not in frame_ids:
                    raise ValueError(
                        f'Anchor {anchor.id} references non-existent frame {anchor.frame_id}'
                    )
            
            # Recursively traverse children
            new_path_objects = current_path_objects | {part_object_id}
            for child in part.children:
                traverse_part_hierarchy(child, new_path_objects)
        
        # Traverse from all top-level parts
        for part in self.parts.values():
            traverse_part_hierarchy(part, set())

        # === EXP-001 Primitive validation (in-memory only) ===
        # points validation
        for key, coords in self.points.items():
            if not isinstance(key, str) or not key.strip():
                raise ValueError(f'Point key must be non-empty id string: {repr(key)}')
            if not isinstance(coords, (list, tuple)) or len(coords) != 3:
                raise ValueError(f'Point "{key}" must contain exactly 3 numeric coordinates')
            for c in coords:
                if not isinstance(c, (int, float)):
                    raise ValueError(f'Point "{key}" coordinates must be numeric: {c}')
        
        # edges validation
        for key, edge in self.edges.items():
            if not isinstance(key, str) or not key.strip():
                raise ValueError(f'Edge key must be non-empty id string: {repr(key)}')
            if not isinstance(edge, (list, tuple)) or len(edge) != 2:
                raise ValueError(f'Edge "{key}" must contain exactly 2 point-id strings')
            p1, p2 = edge
            if not isinstance(p1, str) or not isinstance(p2, str):
                raise ValueError(f'Edge "{key}" endpoints must be point-id strings')
            if p1 not in self.points:
                raise ValueError(f'Edge "{key}" references missing point "{p1}"')
            if p2 not in self.points:
                raise ValueError(f'Edge "{key}" references missing point "{p2}"')
            if p1 == p2:
                raise ValueError(f'Self-edge not allowed for "{key}": both endpoints "{p1}"')
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert geometry model to YAML-safe dictionary."""
        return {
            'id': self.id,
            'name': self.name,
            'parts': {k: v.to_dict() for k, v in self.parts.items()},
            'frames': {k: v.to_dict() for k, v in self.frames.items()}
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'GeometryModel':
        """Create geometry model from dictionary."""
        parts_data = data.get('parts', {})
        frames_data = data.get('frames', {})
        
        # Create frames
        frames = {k: Frame.from_dict(v) for k, v in frames_data.items()}
        
        # Create parts
        parts = {k: Part.from_dict(v) for k, v in parts_data.items()}
        
        # Create the model
        return cls(
            id=data.get('id'),
            name=data.get('name', ''),
            parts=parts,
            frames=frames
        )
