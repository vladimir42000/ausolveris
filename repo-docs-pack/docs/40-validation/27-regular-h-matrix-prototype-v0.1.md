# 27 — Regular H-Matrix Prototype (BEM-006A)
Version: v0.1
Milestone: BEM-006A
Stage: bem006a_regular_h_matrix_prototype

---

## Purpose

BEM-006A assembles a standalone physical boundary-to-observer H-matrix
prototype for strictly exterior observer points using regular numerical
integration only. It does not execute reconstruction and does not compare
against the BEM-004F analytical reference.

---

## Kernel convention

The boundary-to-observer H-matrix uses the same single-layer Green-function
kernel established in BEM-003:

```
H[i, j] = G(|x_obs_i − centroid_j|, k) × area_j
```

where:
- `x_obs_i` is the i-th exterior observer position (from `observer_positions`)
- `centroid_j` is the j-th selected panel centroid
- `area_j` is the j-th selected panel area (quadrature weight)
- `G(r, k) = exp(ikr) / (4πr)` is the scalar Helmholtz Green function (BEM-001)

This is the value-kernel (single-layer) discretization. The normal-derivative
(double-layer) kernel is not assembled in this milestone.

---

## Why interactions are regular

Observer points are supplied via `ExteriorObserverScaffold`, which enforces
strict exterior domain validation: every observer position lies strictly
outside the sphere (distance from origin > sphere radius). Boundary panel
centroids lie on the sphere surface. The observer-to-panel distance is
therefore strictly positive for all (i, j) pairs, making the Green function
kernel regular (non-singular) for all assembled entries.

No near-singular or singular quadrature strategy is required or implemented
for this exterior observer problem.

---

## What BEM-006A does

- Accepts `RigidSphereMeshFixture`, a 3–6 panel subset, an
  `ExteriorObserverScaffold`, and a wavenumber.
- Validates all inputs with controlled `ValueError`.
- Assembles `H[i, j] = G(r_ij, k) × area_j` for all observer × panel pairs.
- Returns an `HMatrixPrototype` package with full metadata and a
  deterministic SHA-256 package ID.

---

## What BEM-006A does not do

| Capability | Status |
|---|---|
| Singular quadrature | Not implemented |
| Near-singular quadrature | Not implemented |
| Observer pressure reconstruction (H @ unknowns) | Not performed |
| BEM-005B gate unlock | Gate remains locked |
| Analytical reference comparison (BEM-004F) | Not performed |
| Tolerance policy application (BEM-005C) | Not applied |
| SPL, directivity, impedance | Not computed |
| Full BEM solve | Not performed |
| Validated BEM capability | Not claimed |

---

## Required metadata

```python
{
    "matrix_stage": "bem006a_regular_h_matrix_prototype",
    "benchmark_id": "ben004_rigid_sphere_scattering_registered",
    "physical_h_matrix_assembled": True,
    "singular_quadrature_implemented": False,
    "reconstruction_performed": False,
    "analytical_reference_comparison_performed": False,
    "tolerance_policy_applied": False,
    "spl_computed": False,
    "directivity_computed": False,
    "impedance_computed": False,
    "non_physical": True,
}
```

Although `physical_h_matrix_assembled=True`, the package is `non_physical=True`
as a solver result because no `H @ boundary_unknowns` multiplication has been
executed and no reconstruction has been performed.

---

## Validation baseline

```
PYTHONPATH=src pytest tests/geometry/test_regular_h_matrix_prototype.py -q
-> 10 passed

PYTHONPATH=src pytest tests/geometry -q
-> 409 passed
```

---

## Lineage

BEM-003 (single-layer kernel) + BEM-004E (observer scaffold) → **BEM-006A**
→ BEM-006B (gated reconstruction using regular H, pending authorization)
