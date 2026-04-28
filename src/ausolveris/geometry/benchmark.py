from pathlib import Path
import yaml


def solver_observables_to_yaml_string(observables: dict) -> str:
    return yaml.safe_dump(observables, sort_keys=False, default_flow_style=False)


def solver_observables_to_yaml_file(observables: dict, path) -> None:
    path = Path(path)
    yaml_text = solver_observables_to_yaml_string(observables)
    path.write_text(yaml_text, encoding="utf-8")
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Any
from .acoustic_view import AcousticTopologyView

@dataclass
class AcousticBenchmarkDescriptor:
    """Structural description of a benchmark case for future numerical validation."""
    benchmark_id: str
    label: str
    category: str           # e.g., "rigid_wall", "interface", "observer", "source_group"
    required_patch_kinds: List[str] = field(default_factory=list)   # e.g., ["rigid_wall"]
    required_interface_count: Optional[int] = None
    required_observer_count: Optional[int] = None
    require_source_group: bool = False
    require_orientation_metadata: bool = True
    require_frame_metadata: bool = True
    require_interface_side_metadata: bool = True
    notes: Optional[str] = None

@dataclass
class AcousticBenchmarkReadinessResult:
    """Readiness verdict with structural details – no numerical values."""
    descriptor_id: str
    is_ready: bool
    reasons: List[str] = field(default_factory=list)
    patch_count: Optional[int] = None
    interface_count: Optional[int] = None
    observer_count: Optional[int] = None
    has_source_group: bool = False
    has_orientation_metadata: bool = False
    has_frame_metadata: bool = False
    has_interface_side_metadata: bool = False

def validate_acoustic_benchmark_descriptor(descriptor: AcousticBenchmarkDescriptor) -> List[str]:
    """Validate descriptor internal consistency. Return list of errors."""
    errors = []
    if not descriptor.benchmark_id:
        errors.append("benchmark_id required")
    if not descriptor.label:
        errors.append("label required")
    # Reject enclosure‑specific solver labels
    forbidden_keywords = [
        "sealed_box_solver", "bass_reflex_solver", "blh_solver",
        "flh_solver", "tapped_horn_solver"
    ]
    if any(keyword in descriptor.category.lower() for keyword in forbidden_keywords):
        errors.append(f"Unsupported enclosure‑specific category: {descriptor.category}")
    if descriptor.required_interface_count is not None and descriptor.required_interface_count < 0:
        errors.append("required_interface_count cannot be negative")
    if descriptor.required_observer_count is not None and descriptor.required_observer_count < 0:
        errors.append("required_observer_count cannot be negative")
    return errors

def evaluate_acoustic_benchmark_readiness(
    view: AcousticTopologyView,
    descriptor: AcousticBenchmarkDescriptor
) -> AcousticBenchmarkReadinessResult:
    """
    Determine if a given AcousticTopologyView satisfies the benchmark descriptor.
    Uses only derived contract – no raw geometry access.
    Returns readiness result with structural reasons.
    """
    reasons = []
    # Check descriptor validity first
    desc_errors = validate_acoustic_benchmark_descriptor(descriptor)
    if desc_errors:
        return AcousticBenchmarkReadinessResult(
            descriptor_id=descriptor.benchmark_id,
            is_ready=False,
            reasons=desc_errors
        )
    
    # Check view errors
    if view.errors:
        reasons.append(f"View has errors: {view.errors}")
        return AcousticBenchmarkReadinessResult(
            descriptor_id=descriptor.benchmark_id,
            is_ready=False,
            reasons=reasons
        )
    
    patch_count = len(view.patches)
    if descriptor.required_interface_count is not None:
        if len(view.interfaces) < descriptor.required_interface_count:
            reasons.append(f"Interface count {len(view.interfaces)} < required {descriptor.required_interface_count}")
    if descriptor.required_observer_count is not None:
        if len(view.observers) < descriptor.required_observer_count:
            reasons.append(f"Observer count {len(view.observers)} < required {descriptor.required_observer_count}")
    
    # Source group readiness
    has_source_group = any(p.source_group is not None for p in view.patches.values())
    if descriptor.require_source_group and not has_source_group:
        reasons.append("Requires source group but none found")
    
    # Orientation metadata: all patches have normal (by construction, normal always present)
    has_orientation = all(len(p.normal) == 3 for p in view.patches.values())
    if descriptor.require_orientation_metadata and not has_orientation:
        reasons.append("Missing orientation metadata on some patch")
    
    # Frame metadata: all patches have frame_ref (they do by construction)
    has_frame = all(p.frame_ref is not None for p in view.patches.values())
    if descriptor.require_frame_metadata and not has_frame:
        reasons.append("Missing frame metadata on some patch")
    
    # Interface side metadata: all interfaces have distinct side_a/side_b
    has_interface_side = all(iface.side_a != iface.side_b for iface in view.interfaces.values())
    if descriptor.require_interface_side_metadata and not has_interface_side:
        reasons.append("Interface side metadata invalid (side_a == side_b)")
    
    is_ready = len(reasons) == 0
    return AcousticBenchmarkReadinessResult(
        descriptor_id=descriptor.benchmark_id,
        is_ready=is_ready,
        reasons=reasons,
        patch_count=patch_count,
        interface_count=len(view.interfaces),
        observer_count=len(view.observers),
        has_source_group=has_source_group,
        has_orientation_metadata=has_orientation,
        has_frame_metadata=has_frame,
        has_interface_side_metadata=has_interface_side,
    )

@dataclass
class AnalyticalBEMBenchmarkDescriptor(AcousticBenchmarkDescriptor):
    source_citation: str = ""
    reference_data_fields: List[str] = field(default_factory=list)
    execution_status: str = "registered_not_executed"
    physical_result_computed: bool = False
    bem_implemented: bool = False
    reference_matching_performed: bool = False

def validate_analytical_bem_benchmark(descriptor: AnalyticalBEMBenchmarkDescriptor) -> List[str]:
    errors = validate_acoustic_benchmark_descriptor(descriptor)
    if not getattr(descriptor, 'source_citation', None):
        errors.append("source_citation required for analytical benchmarks")
    if not getattr(descriptor, 'reference_data_fields', None):
        errors.append("expected reference fields must be declared")
    if getattr(descriptor, 'execution_status', None) != "registered_not_executed":
        errors.append("Execution explicitly rejected: must be 'registered_not_executed'")
    if getattr(descriptor, 'physical_result_computed', True):
        errors.append("Execution explicitly rejected: physical result/BEM must be false")
    if getattr(descriptor, 'bem_implemented', True):
        errors.append("Execution explicitly rejected: bem_implemented must be false")
    if getattr(descriptor, 'reference_matching_performed', True):
        errors.append("Execution explicitly rejected: reference_matching_performed must be false")
    return errors
