# 83 — BEM-007A Status (v0.1)
Milestone: BEM-007A — Boundary Integral Formulation and Singular Kernel Taxonomy Freeze
Status: implemented — pending Auditor push authorization
Type: documentation-only

---

## Base commit

77affbc — BEM-PHASE4-PLAN-002: Freeze physical boundary accuracy transition plan

---

## Scope

Formulation and singular kernel taxonomy freeze only.
No Python source files changed.
No tests added, modified, or removed.
No singular quadrature implemented.
No Duffy transformation implemented.
No semi-analytical extraction implemented.
No H-matrix code changes.
No BEM-004F analytical evaluator changes.
No tolerance threshold changes.
`n_max` remains frozen at 6.
No validated BEM claim.

---

## Files staged

```
repo-docs-pack/docs/40-validation/31-boundary-integral-formulation-taxonomy-v0.1.md
repo-docs-pack/docs/50-operations/83-bem007a-status-v0.1.md
```

No other files staged or touched.

---

## Key decisions frozen in this milestone

| Item | Decision |
|---|---|
| BEM formulation | Indirect single-layer (ISL) |
| Boundary unknown x | Single-layer source density σ |
| Boundary operator A | Single-layer S + jump term + D' (prototype currently lacks jump and D') |
| Observer operator H | Single-layer evaluation at exterior points; same kernel as S |
| Discretization | Centroid collocation |
| Panel geometry | Flat triangles only |
| Outward normal convention | Radially outward; derivative at source point y |
| Time / phase convention | e^{−iωt} suppressed; spatial e^{+ikr} outgoing |
| Self-panel treatment | Semi-analytical extraction (Laplace singular term) — to be implemented in BEM-007C |
| Regular off-diagonal quadrature | 7-point Dunavant Gauss rule, degree 5 — to be implemented in BEM-007B |

---

## What must be corrected in future milestones

- BEM-004C: add physical `(1/2)σ` jump term and `D'σ` adjoint double-layer term.
- BEM-006A off-diagonal: upgrade from centroid (order 1) to 7-point Gauss (BEM-007B).
- BEM-006A self-panel: add semi-analytical extraction correction (BEM-007C).

---

## Validation

```
PYTHONPATH=src pytest tests/geometry -q
-> 429 passed   (unchanged, delta: 0)
```

---

## Negative capability boundary (unchanged)

- No singular quadrature
- No Duffy transformation
- No semi-analytical extraction
- No full BEM solve
- No analytical evaluator modification
- No SPL, directivity, or impedance
- No enclosure BEM, LEM coupling, or optimizer integration
- No validated BEM claim
- No new dependency

---

## Commit message

`BEM-007A: Freeze boundary formulation taxonomy`

Do not push until Auditor authorizes push.
