# INT-002: End-to-End Pipeline Integration Stub (v0.1)

## Status
**Defined – INT-002**

## Purpose
INT-002 integrates the existing, isolated contract layers into a single, deterministic end-to-end pipeline stub. It orchestrates the flow from YAML geometry configuration through topology generation, benchmark validation, physical formulation hooks, optional coupling, and observable score tracking.

## Supported Cases
This pipeline strictly limits execution to the established sanity hooks:
- `phy001_free_field_monopole_pressure`
- `phy002_rigid_cavity_compliance`
- `phy003_simple_port_inertance`
- Coupling: `lem001_closed_box_resonance_sanity`, `lem001_port_cavity_resonance_sanity`

## Constraints
- This is an **orchestration contract**, not a new solver feature.
- **No new physics** or parameter-space searches are introduced.
- **No visualization, plotting, sweeps, or batch processing**.
- If a layer (e.g., topology or formulation) encounters an error or unsupported request, the pipeline safely raises a `PipelineStageError` specifying the exact stage of failure.
