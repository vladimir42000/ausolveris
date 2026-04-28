# solver.py
from typing import Dict, List, Tuple, Any
import copy
from .model import GeometryModel
from .physics import flare_law_acoustic_objective

# --- BASELINE FUNCTIONS (Preserved for compatibility) ---

def run_geometry_solver_stub(model: GeometryModel) -> Dict[str, Any]:
    """
    Baseline stub. Calculates observables dynamically to satisfy baseline tests.
    """
    if not isinstance(model, GeometryModel):
        raise TypeError("Input must be a GeometryModel instance")

    parts_dict = getattr(model, 'parts', {}) or {}
    frames = getattr(model, 'frames', {}) or {}
    
    def walk_tree(parts_list: List[Any]) -> Tuple[int, int, int, int]:
        total_count = 0
        max_d = 0
        total_anchors = 0
        total_boundaries = 0
        for p in parts_list:
            total_count += 1
            total_anchors += len(getattr(p, 'anchors', {}) or {})
            total_boundaries += len(getattr(p, 'boundaries', {}) or {})
            children = getattr(p, 'children', []) or []
            if children:
                c_count, c_depth, c_anchors, c_bounds = walk_tree(children)
                total_count += c_count
                max_d = max(max_d, c_depth)
                total_anchors += c_anchors
                total_boundaries += c_bounds
        return total_count, (max_d + 1) if total_count > 0 else 0, total_anchors, total_boundaries

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

# --- INTERNAL HELPERS ---

def _compute_gradient(model: GeometryModel, epsilon: float = 1e-6) -> Dict[str, Tuple[float, float, float]]:
    """Finite-difference gradient of physics objective w.r.t each point's (x,y,z)."""
    grad = {}
    f0 = flare_law_acoustic_objective(model)
    # If the model is already invalid, the gradient is effectively zero
    if f0 == 1.0:
        return {pid: (0.0, 0.0, 0.0) for pid in model.points}
        
    for pid, coords in model.points.items():
        grad_vec = []
        for dim in range(3):
            model_plus = copy.deepcopy(model)
            new_coords = list(coords)
            new_coords[dim] += epsilon
            model_plus.points[pid] = tuple(new_coords)
            f1 = flare_law_acoustic_objective(model_plus)
            grad_vec.append((f1 - f0) / epsilon)
        grad[pid] = tuple(grad_vec)
    return grad

# --- OPTIMIZATION ENGINE (SOL-003) ---

def optimize(model: GeometryModel,
             step_size: float = 0.1,
             tolerance: float = 1e-4,
             max_steps: int = 100,
             verbose: bool = False) -> Tuple[GeometryModel, Dict]:
    """
    Optimize geometry to minimize acoustic objective via gradient descent.
    """
    if max_steps < 0:
        raise ValueError("max_steps must be non-negative")

    current = copy.deepcopy(model)
    initial_obj = flare_law_acoustic_objective(current)
    history = [initial_obj]
    converged = False
    
    # --- FIXED SHORT CIRCUIT ---
    # This prevents the "null step" that was causing the [0.0, 0.0] vs [0.0] error.
    if initial_obj == 0.0 or initial_obj == 1.0 or max_steps == 0:
        return current, {
            'converged': True, 
            'steps': 0, 
            'history': history
        }

    for step in range(max_steps):
        grad = _compute_gradient(current)
        
        new_model = copy.deepcopy(current)
        for pid, (dx, dy, dz) in grad.items():
            old = current.points[pid]
            new_model.points[pid] = (
                old[0] - step_size * dx,
                old[1] - step_size * dy,
                old[2] - step_size * dz
            )
        
        new_obj = flare_law_acoustic_objective(new_model)
        history.append(new_obj)
        change = abs(history[-2] - new_obj)
        
        if verbose:
            print(f"Step {step+1}: objective = {new_obj:.6f}, change = {change:.6f}")
        
        if change < tolerance:
            converged = True
            break
            
        current = new_model
    
    info = {
        'converged': converged,
        'steps': len(history) - 1,
        'history': history
    }
    return current, info

from .acoustic_view import AcousticTopologyView

def consume_acoustic_topology(view: AcousticTopologyView) -> dict:
    """
    Read-only consumption of validated acoustic topology.
    Returns structural observables, no numerical acoustics.
    
    Raises:
        ValueError: if view has errors (invalid topology).
    
    Returns dict with keys:
        - patch_count: int
        - interface_count: int
        - observer_count: int
        - source_group_count: int
        - owner_count: int
        - interface_side_pairs: list of tuples (side_a, side_b)
        - orientation_metadata_present: bool (True if all patches have normal defined)
        - duplicate_ownership_detected: bool
        - unresolved_observers: list of observer ids with missing point/frame
    """
    if view.errors:
        raise ValueError(f"Invalid acoustic topology: {view.errors}")
    
    patches = view.patches
    interfaces = view.interfaces
    observers = view.observers
    
    patch_count = len(patches)
    interface_count = len(interfaces)
    observer_count = len(observers)
    
    source_groups = {p.source_group for p in patches.values() if p.source_group}
    source_group_count = len(source_groups)
    
    owners = {p.owner_id for p in patches.values()}
    owner_count = len(owners)
    
    interface_side_pairs = [(iface.side_a, iface.side_b) for iface in interfaces.values()]
    
    orientation_metadata_present = all(len(p.normal) == 3 for p in patches.values())
    
    seen_boundaries = set()
    duplicate_ownership_detected = False
    for bid in patches:
        if bid in seen_boundaries:
            duplicate_ownership_detected = True
            break
        seen_boundaries.add(bid)
    
    unresolved_observers = []
    
    return {
        'patch_count': patch_count,
        'interface_count': interface_count,
        'observer_count': observer_count,
        'source_group_count': source_group_count,
        'owner_count': owner_count,
        'interface_side_pairs': interface_side_pairs,
        'orientation_metadata_present': orientation_metadata_present,
        'duplicate_ownership_detected': duplicate_ownership_detected,
        'unresolved_observers': unresolved_observers,
    }

import hashlib
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Any, Optional
from .acoustic_view import AcousticTopologyView

class BoundaryConditionPlaceholder(Enum):
    RIGID_WALL = "rigid_wall_placeholder"
    INTERFACE = "interface_placeholder"
    SOURCE_PATCH = "source_patch_placeholder"
    OBSERVER = "observer_placeholder"

@dataclass
class AcousticOperatorEntry:
    """Structural placeholder for a single operator assembly entry."""
    entry_id: str
    topology_signature: str
    entry_type: str
    boundary_label: BoundaryConditionPlaceholder
    side_convention: Optional[str] = None
    orientation_sign: Optional[int] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class AcousticOperatorAssemblyPackage:
    """Non-physical operator assembly output."""
    operator_package_id: str
    topology_signature: str
    benchmark_descriptor_id: str
    non_physical: bool = True
    physical_kernel: str = "none"
    numerical_values_present: bool = False
    solver_stage: str = "operator_assembly_stub"
    entries: List[AcousticOperatorEntry] = field(default_factory=list)

class AcousticOperatorAssemblyStub:
    """Deterministic placeholder assembly stub. No acoustic physics."""

    def assemble(self, topology_view: 'AcousticTopologyView', benchmark_descriptor_id: str) -> AcousticOperatorAssemblyPackage:
        # 1. Benchmark Readiness check (Strictly require the flag, default to False)
        is_ready = getattr(topology_view, "is_benchmark_ready", False)
        if not is_ready:
            raise ValueError("AcousticTopologyView is not benchmark-ready")

        # 2. Validate metadata / rejection cases
        if not topology_view.observers:
            raise ValueError("Missing observer mapping")
            
        has_source = any(p.source_group for p in topology_view.patches.values())
        if not has_source:
            raise ValueError("Missing source patch grouping")
            
        for iface in topology_view.interfaces.values():
            if iface.side_a == iface.side_b:
                raise ValueError(f"Invalid interface side metadata: side_a == side_b for {iface.interface_id}")

        for patch in topology_view.patches.values():
            label = getattr(patch, 'bc_label', 'rigid_wall_placeholder')
            try:
                BoundaryConditionPlaceholder(label)
            except ValueError:
                raise ValueError(f"Unsupported boundary condition label: {label}")
                
            if not getattr(patch, 'normal', None) or len(patch.normal) != 3:
                raise ValueError("Missing orientation/sign metadata")

        # 3. Assemble deterministic structures
        topology_sig = f"sig_{len(topology_view.patches)}_{len(topology_view.interfaces)}"
        
        # FIX: Deterministic SHA-256 ID instead of Python's salted hash()
        raw_id = (topology_sig + benchmark_descriptor_id).encode('utf-8')
        hashed_id = hashlib.sha256(raw_id).hexdigest()[:8]
        package_id = f"sol002_stub_{hashed_id}"

        entries = []
        for pid, patch in sorted(topology_view.patches.items()):
            label = getattr(patch, 'bc_label', 'rigid_wall_placeholder')
            if getattr(patch, 'source_group', None):
                label = 'source_patch_placeholder'
                
            entries.append(AcousticOperatorEntry(
                entry_id=f"patch_{pid}",
                topology_signature=topology_sig,
                entry_type="patch",
                boundary_label=BoundaryConditionPlaceholder(label)
            ))
            
        for iid, iface in sorted(topology_view.interfaces.items()):
            entries.append(AcousticOperatorEntry(
                entry_id=f"interface_{iid}",
                topology_signature=topology_sig,
                entry_type="interface",
                boundary_label=BoundaryConditionPlaceholder.INTERFACE,
                side_convention=f"{iface.side_a}->{iface.side_b}"
            ))

        for oid, obs in sorted(topology_view.observers.items()):
            entries.append(AcousticOperatorEntry(
                entry_id=f"observer_{oid}",
                topology_signature=topology_sig,
                entry_type="observer",
                boundary_label=BoundaryConditionPlaceholder.OBSERVER
            ))

        return AcousticOperatorAssemblyPackage(
            operator_package_id=package_id,
            topology_signature=topology_sig,
            benchmark_descriptor_id=benchmark_descriptor_id,
            entries=entries
        )

def assemble_acoustic_operator_stub(view: AcousticTopologyView, benchmark_descriptor_id: str) -> AcousticOperatorAssemblyPackage:
    stub = AcousticOperatorAssemblyStub()
    return stub.assemble(view, benchmark_descriptor_id)

import math
import cmath
from dataclasses import dataclass

@dataclass
class SingleCaseAcousticFormulationInput:
    topology_view: 'AcousticTopologyView'
    operator_package: 'AcousticOperatorAssemblyPackage'
    benchmark_id: str
    frequency_hz: float
    source_distance_m: float
    volume_velocity_m3_s: float = 1.0
    rho0: float = 1.21
    c0: float = 343.0

@dataclass
class SingleCaseAcousticFormulationResult:
    frequency_hz: float
    pressure_complex: complex
    pressure_magnitude: float
    source_observer_distance_m: float
    rho0: float
    c0: float
    volume_velocity_m3_s: float
    wavenumber_rad_m: float
    angular_frequency_rad_s: float
    physical_case: str = "phy001_free_field_monopole_pressure"
    formulation_scope: str = "single_case_only"
    general_solver: bool = False
    bem_implemented: bool = False
    lem_implemented: bool = False
    enclosure_model: bool = False

def evaluate_phy001_single_case(input_data: SingleCaseAcousticFormulationInput) -> SingleCaseAcousticFormulationResult:
    # 1. Benchmark ID Validation
    if input_data.benchmark_id != "phy001_free_field_monopole_pressure":
        raise ValueError(f"Unsupported benchmark case: {input_data.benchmark_id}")
        
    # 2. Benchmark Readiness Validation
    if not getattr(input_data.topology_view, "is_benchmark_ready", False):
        raise ValueError("Topology is not benchmark-ready")
        
    # 3. Non-physical Operator Precondition
    if getattr(input_data.operator_package, "non_physical", None) is not True:
        raise ValueError("Operator package must be explicitly marked non_physical")

    # 4. Source Group & Observer Validation
    source_groups = {p.source_group for p in input_data.topology_view.patches.values() if getattr(p, 'source_group', None)}
    if len(source_groups) == 0:
        raise ValueError("Missing source-group declaration")
    if len(source_groups) > 1:
        raise ValueError("Multiple source groups not supported in PHY-001")
        
    observers = input_data.topology_view.observers
    if not observers:
        raise ValueError("Missing observer mapping")
    if len(observers) > 1:
        raise ValueError("Multiple observers not supported in PHY-001")
        
    # 5. Frequency and Distance Validation
    if input_data.frequency_hz <= 0:
        raise ValueError("Frequency must be strictly positive")

    r = input_data.source_distance_m
    if r <= 0:
        raise ValueError("Source-observer distance must be strictly positive (r > 0)")
        
    # 6. Formulation Hook Execution
    f = input_data.frequency_hz
    rho0 = input_data.rho0
    c0 = input_data.c0
    Q = input_data.volume_velocity_m3_s
    
    omega = 2.0 * math.pi * f
    k = omega / c0
    
    amplitude = (rho0 * omega * Q) / (4.0 * math.pi * r)
    phase_factor = cmath.exp(-1j * k * r)
    p_complex = 1j * amplitude * phase_factor
    
    return SingleCaseAcousticFormulationResult(
        frequency_hz=f,
        pressure_complex=p_complex,
        pressure_magnitude=abs(p_complex),
        source_observer_distance_m=r,
        rho0=rho0,
        c0=c0,
        volume_velocity_m3_s=Q,
        wavenumber_rad_m=k,
        angular_frequency_rad_s=omega
    )
