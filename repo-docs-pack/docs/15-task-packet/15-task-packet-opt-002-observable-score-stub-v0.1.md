# OPT-002: Observable Score Stub (v0.1)

## Status
**Defined – OPT-002**

## Purpose
OPT-002 defines a strictly bounded placeholder observable-score contract. It bridges the gap between the three physical formulation hooks (PHY-001, PHY-002, PHY-003) and future numerical optimization loops. 

## Supported Inputs
The stub strictly accepts only the outputs from the three validated physical sanity cases:
- `phy001_free_field_monopole_pressure`
- `phy002_rigid_cavity_compliance`
- `phy003_simple_port_inertance`

## Exclusions & Non-Physical Constraints
- This does **not** implement a real optimization loop.
- It does **not** perform gradient descent or parameter space search.
- It does **not** rank loudspeaker designs.
- It does **not** calculate SPL fitness, impedance fitness, group delay, or acoustic merit.
- The generated `ObservableScorePackage` explicitly sets `non_physical_score=True` and `optimization_performed=False`.
- Future optimization work and parameter-space traversal will build upon this deterministic placeholder.
