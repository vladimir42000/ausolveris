# Single-Case Acoustic Formulation (v0.1)

## Status
**Defined – PHY-001**

## Purpose
PHY-001 introduces the first physical acoustic sanity hook. It bridges the gap between the structural/non-physical `AcousticOperatorAssemblyPackage` and a minimal baseline calculation.

## Supported Cases
The **only** supported case is `"phy001_free_field_monopole_pressure"`. All unsupported cases (e.g., enclosure solvers, multi-source arrays, general scattering) are strictly rejected rather than approximated.

## Analytical Formula
The physical formulation uses a simple free-field harmonic point-source pressure relationship:

`p(r, f) = j * rho0 * omega * Q / (4 * pi * r) * exp(-j * k * r)`

Assumptions:
- Homogeneous free-field air parameters (`rho0`, `c0`).
- Strict $r > 0$ source-to-observer distance.
- Monopole approximation.

## Hard Scope Exclusions
- This is **not** BEM.
- This is **not** LEM.
- This is **not** an enclosure solver.
- This is **not** a validated loudspeaker simulation framework.
- Future BEM/LEM work must be added through later bounded tasks.
