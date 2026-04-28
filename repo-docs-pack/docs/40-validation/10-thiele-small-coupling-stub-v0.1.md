# Thiele-Small Driver Coupling Stub (v0.1)

## Status
**Defined – LEM-001**

## Purpose
LEM-001 introduces a deterministic Thiele-Small-style driver coupling sanity stub. It produces scalar sanity hooks validating the interplay between the existing `PHY-002` cavity compliance and `PHY-003` port inertance results.

## Supported Modes
1. `lem001_closed_box_resonance_sanity`: Computes $f_c = f_s \cdot \sqrt{1 + V_{as}/V_b}$
2. `lem001_port_cavity_resonance_sanity`: Computes $f = rac{1}{2\pi\sqrt{M_a C_a}}$

## Constraints and Exclusions
- `Qts` is validated but explicitly unused to prevent damping/frequency-response derivations.
- **No full LEM solver** is implemented. 
- No impedance curve is computed.
- No SPL response is computed.
- No frequency sweep is permitted.
- No bass-reflex or closed-box solver is fully instantiated.
- Output is rigorously flagged with `scalar_sanity_only = True`.
