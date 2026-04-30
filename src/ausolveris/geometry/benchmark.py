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

# ---------------------------------------------------------------------------
# BEM-002: rigid-sphere benchmark mesh fixture (geometry only)
# Appended to the existing `benchmark.py`. Do not alter any prior content.
# ---------------------------------------------------------------------------

import math
import hashlib
from dataclasses import dataclass
from typing import List, Tuple

# ---------------------------------------------------------------------------
# Panel and fixture data structures
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class RigidSpherePanel:
    """A single triangular panel of the rigid‑sphere mesh."""
    vertex_indices: Tuple[int, int, int]      # indices into the vertex list
    centroid: Tuple[float, float, float]      # Cartesian centroid
    outward_normal: Tuple[float, float, float]  # unit normal pointing outward
    area: float

@dataclass
class RigidSphereMeshFixture:
    """Deterministic triangulated sphere fixture for BEN‑004."""
    benchmark_id: str
    sphere_radius: float
    sphere_center: Tuple[float, float, float]
    canonical_frame_metadata: dict
    vertices: List[Tuple[float, float, float]]
    panels: List[RigidSpherePanel]
    fixture_hash: str
    execution_status: str
    scattering_solve_performed: bool
    bem_operator_assembled: bool
    normal_convention: str

# ---------------------------------------------------------------------------
# Icosahedron primitive – deterministic, closed, purely triangular
# ---------------------------------------------------------------------------

def _icosahedron_vertices() -> List[Tuple[float, float, float]]:
    """Return the 12 vertices of a regular icosahedron centred at origin."""
    phi = (1.0 + math.sqrt(5.0)) / 2.0   # golden ratio
    return [
        (-1,  phi, 0), (1,  phi, 0), (-1, -phi, 0), (1, -phi, 0),
        (0, -1,  phi), (0,  1,  phi), (0, -1, -phi), (0,  1, -phi),
        ( phi, 0, -1), ( phi, 0,  1), (-phi, 0, -1), (-phi, 0,  1),
    ]

def _icosahedron_faces() -> List[Tuple[int, int, int]]:
    """Return the 20 triangular faces (zero‑based indices) of an icosahedron."""
    return [
        (0, 11, 5), (0, 5, 1), (0, 1, 7), (0, 7, 10), (0, 10, 11),
        (1, 5, 9), (5, 11, 4), (11, 10, 2), (10, 7, 6), (7, 1, 8),
        (3, 9, 4), (3, 4, 2), (3, 2, 6), (3, 6, 8), (3, 8, 9),
        (4, 9, 5), (2, 4, 11), (6, 2, 10), (8, 6, 7), (9, 8, 1),
    ]

def _subdivide_faces(
    vertices: List[Tuple[float, float, float]],
    faces: List[Tuple[int, int, int]],
    level: int
) -> Tuple[List[Tuple[float, float, float]], List[Tuple[int, int, int]]]:
    """Subdivide each triangle into 4 by splitting edges, repeated `level` times."""
    verts = list(vertices)
    tris = list(faces)
    edge_map = {}

    def midpoint(i: int, j: int) -> int:
        key = (i, j) if i < j else (j, i)
        if key in edge_map:
            return edge_map[key]
        x = tuple((verts[i][k] + verts[j][k]) / 2.0 for k in range(3))
        idx = len(verts)
        verts.append(x)
        edge_map[key] = idx
        return idx

    for _ in range(level):
        new_tris = []
        for i0, i1, i2 in tris:
            a = midpoint(i0, i1)
            b = midpoint(i1, i2)
            c = midpoint(i2, i0)
            new_tris.extend([
                (i0, a, c), (i1, b, a), (i2, c, b), (a, b, c)
            ])
        tris = new_tris
    return verts, tris

def _normalise(v: Tuple[float, float, float]) -> Tuple[float, float, float]:
    """Return a unit vector in the same direction."""
    norm = math.sqrt(v[0]*v[0] + v[1]*v[1] + v[2]*v[2])
    if norm == 0.0:
        return (0.0, 0.0, 0.0)
    return (v[0]/norm, v[1]/norm, v[2]/norm)

def _cross(a: Tuple[float, float, float], b: Tuple[float, float, float]) -> Tuple[float, float, float]:
    return (
        a[1]*b[2] - a[2]*b[1],
        a[2]*b[0] - a[0]*b[2],
        a[0]*b[1] - a[1]*b[0],
    )

def _subtract(a: Tuple[float, float, float], b: Tuple[float, float, float]) -> Tuple[float, float, float]:
    return (a[0]-b[0], a[1]-b[1], a[2]-b[2])

def _add(a: Tuple[float, float, float], b: Tuple[float, float, float]) -> Tuple[float, float, float]:
    return (a[0]+b[0], a[1]+b[1], a[2]+b[2])

def _scale(v: Tuple[float, float, float], s: float) -> Tuple[float, float, float]:
    return (v[0]*s, v[1]*s, v[2]*s)

def _area_of_triangle(v0, v1, v2) -> float:
    """Area = 0.5 * |(v1-v0) x (v2-v0)|."""
    e1 = _subtract(v1, v0)
    e2 = _subtract(v2, v0)
    cr = _cross(e1, e2)
    return 0.5 * math.sqrt(cr[0]*cr[0] + cr[1]*cr[1] + cr[2]*cr[2])

# ---------------------------------------------------------------------------
# Fixture builder
# ---------------------------------------------------------------------------

def build_rigid_sphere_benchmark_fixture(
    benchmark_id: str,
    radius: float = 1.0,
    center: Tuple[float, float, float] = (0.0, 0.0, 0.0),
    subdivision_level: int = 1
) -> RigidSphereMeshFixture:
    """
    Create a deterministic triangular mesh fixture for the rigid‑sphere benchmark.

    Only the benchmark id ``ben004_rigid_sphere_scattering_registered`` is supported.
    The sphere is approximated by a subdivided icosahedron, scaled to the given radius
    and translated to the given center.  All normals point outward to the exterior
    acoustic domain.
    """
    if benchmark_id != "ben004_rigid_sphere_scattering_registered":
        raise ValueError(
            f"Unsupported benchmark_id: {benchmark_id}. "
            f"Only 'ben004_rigid_sphere_scattering_registered' is allowed."
        )

    # ---- raw icosahedron, refined deterministically ----
    verts, faces = _icosahedron_vertices(), _icosahedron_faces()
    verts, faces = _subdivide_faces(verts, faces, subdivision_level)

    # ---- scale and translate vertices ----
    scaled_verts = [
        _add(_scale(v, radius), center) for v in verts
    ]

    # ---- build panels ----
    panels: List[RigidSpherePanel] = []
    for i0, i1, i2 in faces:
        v0, v1, v2 = scaled_verts[i0], scaled_verts[i1], scaled_verts[i2]
        # centroid
        c = _scale(_add(_add(v0, v1), v2), 1.0/3.0)
        # outward normal = normalised vector from sphere centre to centroid
        to_centroid = _subtract(c, center)
        n = _normalise(to_centroid)
        area = _area_of_triangle(v0, v1, v2)
        panels.append(RigidSpherePanel(
            vertex_indices=(i0, i1, i2),
            centroid=c,
            outward_normal=n,
            area=area
        ))

    # ---- deterministic fixture hash (SHA-256 of vertex coords + face indices) ----
    hash_input = []
    # sort vertices not necessary because order is already deterministic
    for v in scaled_verts:
        hash_input.append(f"{v[0]:.15e},{v[1]:.15e},{v[2]:.15e}")
    for f in faces:
        hash_input.append(f"{f[0]},{f[1]},{f[2]}")
    hash_str = hashlib.sha256("\n".join(hash_input).encode("utf-8")).hexdigest()

    return RigidSphereMeshFixture(
        benchmark_id=benchmark_id,
        sphere_radius=radius,
        sphere_center=center,
        canonical_frame_metadata={
            "frame": "Cartesian",
            "units": "metres",
            "right": (1.0, 0.0, 0.0),
            "up": (0.0, 0.0, 1.0),
            "forward": (0.0, 1.0, 0.0),
        },
        vertices=scaled_verts,
        panels=panels,
        fixture_hash=hash_str,
        execution_status="registered_not_executed",
        scattering_solve_performed=False,
        bem_operator_assembled=False,
        normal_convention="outward_to_exterior_acoustic_domain",
    )

# ---------------------------------------------------------------------------
# Mesh validation (does not compute BEM quantities)
# ---------------------------------------------------------------------------

def validate_rigid_sphere_mesh_fixture(
    fixture: RigidSphereMeshFixture,
) -> List[str]:
    """
    Validate the structural integrity of a rigid‑sphere mesh fixture.

    Returns a list of error messages (empty if valid).
    Does not perform any BEM computation, Green‑function evaluation,
    or scattering analysis.
    """
    errors = []
    if fixture.benchmark_id != "ben004_rigid_sphere_scattering_registered":
        errors.append(f"Unexpected benchmark_id: {fixture.benchmark_id}")
    if fixture.sphere_radius <= 0.0:
        errors.append(f"sphere_radius must be > 0, got {fixture.sphere_radius}")
    if len(fixture.sphere_center) != 3:
        errors.append("sphere_center must have length 3")
    if any(not math.isfinite(c) for c in fixture.sphere_center):
        errors.append("sphere_center values must be finite")
    if fixture.execution_status != "registered_not_executed":
        errors.append("execution_status must be 'registered_not_executed'")
    if fixture.scattering_solve_performed:
        errors.append("scattering_solve_performed must be False")
    if fixture.bem_operator_assembled:
        errors.append("bem_operator_assembled must be False")
    if fixture.normal_convention != "outward_to_exterior_acoustic_domain":
        errors.append("normal_convention must be 'outward_to_exterior_acoustic_domain'")

    if not fixture.vertices:
        errors.append("Vertex list is empty")
    if not fixture.panels:
        errors.append("Panel list is empty")

    # --- panel checks ---
    seen_face_set = set()
    for p in fixture.panels:
        i0, i1, i2 = p.vertex_indices
        if i0 == i1 or i1 == i2 or i2 == i0:
            errors.append(f"Degenerate triangle (duplicate indices): {p.vertex_indices}")
        if any(idx < 0 or idx >= len(fixture.vertices) for idx in p.vertex_indices):
            errors.append(f"Vertex index out of range: {p.vertex_indices}")
        # area check
        if p.area <= 0.0:
            errors.append(f"Non‑positive panel area: {p.area}")
        # normal is unit
        n = p.outward_normal
        norm_n = math.sqrt(n[0]*n[0] + n[1]*n[1] + n[2]*n[2])
        if not math.isclose(norm_n, 1.0, rel_tol=1e-12):
            errors.append(f"Normal not unit length: {n} (norm={norm_n})")
        # outward normal check: (centroid - center) dot normal should be > 0
        to_cent = _subtract(p.centroid, fixture.sphere_center)
        dot = to_cent[0]*n[0] + to_cent[1]*n[1] + to_cent[2]*n[2]
        if dot <= 0.0:
            errors.append(f"Normal points inward for panel {p.vertex_indices}")
        seen_face_set.add(p.vertex_indices)

    if len(seen_face_set) != len(fixture.panels):
        errors.append("Duplicate faces detected")

    # --- closure check: every edge appears exactly twice ---
    edge_count = {}
    for p in fixture.panels:
        i0, i1, i2 = p.vertex_indices
        for e in [(i0, i1), (i1, i2), (i2, i0)]:
            key = tuple(sorted(e))
            edge_count[key] = edge_count.get(key, 0) + 1
    non_manifold = [e for e, cnt in edge_count.items() if cnt != 2]
    if non_manifold:
        errors.append(f"Mesh is not closed (non‑manifold edges: {len(non_manifold)})")

    return errors