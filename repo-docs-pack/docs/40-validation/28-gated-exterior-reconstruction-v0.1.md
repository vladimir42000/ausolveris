# 28 — Gated Exterior Reconstruction Prototype (BEM-006B)
Version: v0.1
Milestone: BEM-006B
Stage: bem006b_gated_exterior_reconstruction

---

## Purpose

BEM-006B executes the prototype boundary-to-observer matrix-vector
multiplication `p_scattered = H @ x`, where H is the BEM-006A regular
H-matrix prototype and x is the BEM-004C artificially regularized boundary
solution vector. It produces reconstructed observer-pressure arrays but does
not invoke the BEM-005C matching scaffold or apply any tolerance policy.

---

## What BEM-006B does

- Accepts the BEM-006A `HMatrixPrototype` and the BEM-004C
  `RegularizedSolvePrototype` as inputs.
- Verifies dimension compatibility: `H.panel_count == len(x)`.
- Computes `p_scattered[i] = Σ_j H[i,j] × x[j]` for each observer point.
- Optionally accepts an `incident_pressure` array to form `p_total`.
- Emits a deterministic SHA-256 package ID.
- Returns a `ReconstructedObserverPressure` package.

---

## Incident pressure policy

If `incident_pressure` is supplied (list of complex, length = observer count):

```
p_total = p_incident + p_scattered
```

If `incident_pressure` is `None` (default):

```
p_incident = [0j] * observer_count   # deterministic zero placeholder
p_total    = p_scattered
```

No `ValueError` is raised for absent incident pressure. The `incident_pressure_supplied`
field in the result records which path was taken.

---

## What BEM-006B does not do

| Capability | Status |
|---|---|
| BEM-005C matching scaffold invocation | Not called |
| Analytical reference comparison (BEM-004F) | Not performed |
| Tolerance policy application | Not applied |
| Singular quadrature | Not implemented |
| Near-singular quadrature | Not implemented |
| BEM-005B gate unlock or modification | Gate unchanged |
| Full validated BEM solve | Not performed |
| SPL, directivity, impedance | Not computed |
| Validated BEM claim | Not made |

---

## Why the result remains non_physical=True

The reconstruction is computed from:
- A toy 3–6 panel subset (not the full sphere mesh).
- An artificially regularized algebraic boundary solution (BEM-004C), which
  is not a physically correct Neumann density.
- A single-layer centroid-collocation H-matrix with no quadrature convergence
  guarantee.

No comparison against the BEM-004F analytical reference has been performed.
`benchmark_passed` is therefore not evaluated at this milestone.

---

## Required metadata

```python
{
    "reconstruction_stage": "bem006b_gated_exterior_reconstruction",
    "benchmark_id": "ben004_rigid_sphere_scattering_registered",
    "physical_h_matrix_assembled": True,
    "physical_reconstruction_performed": True,
    "singular_quadrature_implemented": False,
    "analytical_reference_comparison_performed": False,
    "tolerance_policy_applied": False,
    "spl_computed": False,
    "directivity_computed": False,
    "impedance_computed": False,
    "non_physical": True,
}
```

---

## Validation baseline

```
PYTHONPATH=src pytest tests/geometry/test_gated_exterior_reconstruction.py -q
-> 10 passed

PYTHONPATH=src pytest tests/geometry -q
-> 419 passed
```

---

## Lineage

BEM-006A (H-matrix) + BEM-004C (boundary solution) → **BEM-006B**
→ BEM-006C (analytical comparison, pending authorization)
