# OPT-003: Single-Objective Fitness Descriptor Stub (v0.1)

## Status
**Defined – OPT-003**

## Purpose
OPT-003 defines a deterministic fitness descriptor stub. It establishes the downstream optimization structure by consuming previously validated packages (`OPT-002` scores or `VIS-001` visualizations) and producing explicit fitness scaffolding.

## Hard Exclusions
To maintain hygiene and prevent scope creep, this stub:
- Does **not** execute a real optimization loop.
- Does **not** rank candidates or recommend acoustic designs.
- Strictly blocks acoustic merit claims (e.g., `spl_fitness`, `design_quality`).
- Sets `placeholder_value_non_physical = True` and `acoustic_interpretation = False` for all generated fitness scalars.
