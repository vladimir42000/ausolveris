# SOL-002: Acoustic Operator Assembly Contract (v0.1)

## Status
**Non-physical, architecture-only milestone**

## Scope
SOL-002 defines a **placeholder** operator assembly stub. It does **not** implement any acoustic physics.

- No BEM kernels, LEM equations, Green functions, matrix coefficients, or solver mathematics.
- No pressure, velocity, impedance, SPL, transfer functions, or radiation loads.
- No FEM coupling, enclosure-specific solvers, or acoustic correctness claims.

## Contract
- Input: `AcousticTopologyView` that is **benchmark-ready** (validated by `benchmark.py`).
- Output: `AcousticOperatorAssemblyPackage` with:
  - `non_physical = true`
  - `physical_kernel = "none"`
  - `numerical_values_present = false`
  - `solver_stage = "operator_assembly_stub"`
  - Deterministic structural entries (patches, interfaces, sources, observers).

## Validation
- Invalid metadata (side_a==side_b, missing groups, unsupported labels) causes rejection.
- All outputs are explicitly marked non-physical.

## Future Extension
Physical BEM/LEM operators **must** replace the placeholder assembly through later scoped tasks.
The existing chain `GeometryModel -> AcousticTopologyView -> benchmark-readiness` remains canonical.
