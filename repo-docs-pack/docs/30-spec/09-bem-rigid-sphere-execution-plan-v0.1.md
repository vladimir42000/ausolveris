# BEM-PLAN-001: Rigid-Sphere BEM Execution Plan & Interface Freeze (v0.1)

## Benchmark Identity
The first BEM execution target is locked to:
`ben004_rigid_sphere_scattering_registered`
**Status:** Currently registration-only. Not executed. No solver logic exists in the repository.

## First Formulation Choice
The planned formulation is strictly frozen to:
- Exterior acoustic Helmholtz scattering.
- Sound-hard / rigid sphere boundary.
- Incident plane wave excitation.
- Neumann boundary condition on the sphere surface (zero total normal velocity).
- Observer comparison against an analytical rigid-sphere scattering reference.

## Geometry and Discretization Input Requirements
Future BEM mesh fixtures must provide:
- Exact sphere radius.
- A surface mesh/panel representation (e.g., planar triangles or quadrilaterals).
- Panel center coordinates and area.
- Deterministic panel ordering.
- A deterministic observer point list.
- A deterministic frequency or wavenumber list.
*Note: BEM-PLAN-001 does not generate or discretize a mesh.*

## Boundary-Condition and Sign Conventions
- The exterior normal points *out* of the sphere into the exterior acoustic domain.
- Sound-hard boundary explicitly means zero total normal velocity on the surface.
- The incident and scattered field formulation must use a consistent time convention (e.g., $e^{+j\omega t}$ or $e^{-j\omega t}$), which must be uniformly enforced across analytical references and Green functions.

## Incident-Field and Source Convention
Future solvers will use an incident plane wave defined by a direction vector and a pressure amplitude, referenced to a global coordinate origin (the sphere center).

## Observer/Reference Comparison Strategy
Comparisons will evaluate complex pressure at defined observer locations against a published analytical rigid-sphere scattering reference. The comparison will evaluate either total pressure or scattered pressure (to be locked in BEM-004), utilizing deterministic ordering and bounded numerical tolerances.

## Tolerance Policy
Tolerances will be strictly staged. No pass/fail acoustic tolerance is applied in BEM-PLAN-001.
- **BEM-001:** Green-function unit test tolerances.
- **BEM-002:** Geometry/mesh generation precision tolerances.
- **BEM-003:** Operator matrix shape/assembly checks (non-singular only).
- **BEM-004:** Final scattering/reference numerical comparison tolerances against the analytical solution.

## Staged Implementation Sequence
The execution of the BEM architecture is locked to the following sequence:

1. **BEM-001:** Scalar Helmholtz Green-function utility and validation only. No panels, no matrix assembly, no scattering solve.
2. **BEM-002:** Rigid-sphere benchmark mesh/geometry fixture only. Deterministic sphere surface fixture, normals, panel metadata. No matrix and no solve.
3. **BEM-003:** Non-singular operator assembly for controlled panels only. Matrix/operator shape validation only. No singular treatment. No scattering solve.
4. **BEM-004:** First rigid-sphere scattering solve against the analytical reference. This is the first task allowed to execute the `ben004` benchmark numerically.

## Existing Contract Preservation
- `PHY-001/002/003` remain scalar sanity hooks.
- `LEM-001` remains scalar sanity coupling.
- `OPT-002/003` remain non-physical descriptors.
- `VIS-001` remains a non-physical visualization descriptor.
- `INT-002` remains orchestration only.
- `BEN-004` remains registration-only until BEM-004.
