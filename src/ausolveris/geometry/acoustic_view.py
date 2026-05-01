from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
from .model import GeometryModel

@dataclass
class AcousticPatch:
    boundary_id: str
    owner_id: str
    frame_ref: str
    normal: Tuple[float, float, float]
    source_group: Optional[str] = None

@dataclass
class AcousticInterface:
    interface_id: str
    side_a: str
    side_b: str
    edge_id: Optional[str] = None

@dataclass
class AcousticObserver:
    point_id: str
    frame_ref: Optional[str] = None

@dataclass
class AcousticTopologyView:
    patches: Dict[str, AcousticPatch] = field(default_factory=dict)
    interfaces: Dict[str, AcousticInterface] = field(default_factory=dict)
    observers: Dict[str, AcousticObserver] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)

def derive_acoustic_topology(model: GeometryModel, acoustic_metadata: Dict[str, Any]) -> AcousticTopologyView:
    """
    Derive acoustic view from GeometryModel and explicit acoustic metadata.
    Metadata keys:
        'patches': dict boundary_id -> {owner, frame, normal, source_group?}
        'interfaces': dict interface_id -> {side_a, side_b, edge_id?}
        'observers': dict observer_id -> {point_id, frame_ref?}
    Validation rules per spec.
    """
    view = AcousticTopologyView()
    meta = acoustic_metadata.get('acoustic', {})
    
    # Patches
    for bid, patch_data in meta.get('patches', {}).items():
        if bid not in model.boundaries:
            view.errors.append(f"Patch boundary {bid} not found in model")
            continue
        required = ['owner', 'frame', 'normal']
        if not all(k in patch_data for k in required):
            view.errors.append(f"Patch {bid} missing required metadata {required}")
            continue
        owner = patch_data['owner']
        frame = patch_data['frame']
        normal = tuple(patch_data['normal'])
        if len(normal) != 3:
            view.errors.append(f"Patch {bid} normal must be 3D")
            continue
        if bid in view.patches:
            view.errors.append(f"Duplicate acoustic ownership of patch {bid}")
            continue
        patch = AcousticPatch(boundary_id=bid, owner_id=owner, frame_ref=frame, normal=normal,
                              source_group=patch_data.get('source_group'))
        view.patches[bid] = patch
        
    # Interfaces
    for iid, iface_data in meta.get('interfaces', {}).items():
        if 'side_a' not in iface_data or 'side_b' not in iface_data:
            view.errors.append(f"Interface {iid} missing side_a or side_b")
            continue
        side_a = iface_data['side_a']
        side_b = iface_data['side_b']
        if side_a == side_b:
            view.errors.append(f"Interface {iid} side_a == side_b")
            continue
        # Check that sides refer to existing patches or boundaries
        if side_a not in view.patches and side_a not in model.boundaries:
            view.errors.append(f"Interface {iid} side_a {side_a} not found")
        if side_b not in view.patches and side_b not in model.boundaries:
            view.errors.append(f"Interface {iid} side_b {side_b} not found")
        edge_id = iface_data.get('edge_id')
        view.interfaces[iid] = AcousticInterface(interface_id=iid, side_a=side_a, side_b=side_b, edge_id=edge_id)
        
    # Observers
    for obs_id, obs_data in meta.get('observers', {}).items():
        if 'point_id' not in obs_data:
            view.errors.append(f"Observer {obs_id} missing point_id")
            continue
        point_id = obs_data['point_id']
        if point_id not in model.points:
            view.errors.append(f"Observer {obs_id} point {point_id} not in model")
            continue
        frame_ref = obs_data.get('frame_ref')
        view.observers[obs_id] = AcousticObserver(point_id=point_id, frame_ref=frame_ref)
        
    return view
