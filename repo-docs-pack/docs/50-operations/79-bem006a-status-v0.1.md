# 79 — BEM-006A Status (v0.1)
Milestone: BEM-006A — Regular Exterior Observer H-Row Assembly Prototype
Status: implemented — pending Auditor push authorization

---

## Base commit

30d7ce1 — BEM-PHASE4-PLAN-001: Freeze H-matrix physics strategy

---

## Scope

Regular exterior observer H-matrix prototype only.
No reconstruction performed. No validated BEM claim.

---

## What was added

- `HMatrixPrototype` dataclass in `src/ausolveris/geometry/bem.py`
- `assemble_regular_h_matrix_prototype()` factory function in `src/ausolveris/geometry/bem.py`
- 10 acceptance tests in `tests/geometry/test_regular_h_matrix_prototype.py`
- Validation doc: `repo-docs-pack/docs/40-validation/27-regular-h-matrix-prototype-v0.1.md`

---

## Kernel convention

Single-layer Green-function kernel, identical to BEM-003:
`H[i, j] = G(|x_obs_i − centroid_j|, k) × area_j`

Normal-derivative kernel not assembled in this milestone.

---

## BEM-005B gate status

**Locked.** BEM-006A assembles H rows only. No reconstruction gate is unlocked.
No H @ boundary_unknowns multiplication is performed.

---

## Negative capability boundary (unchanged)

- No singular quadrature
- No near-singular quadrature
- No observer pressure reconstruction
- No full BEM solve
- No analytical reference comparison
- No tolerance policy application
- No SPL, directivity, or impedance
- No enclosure BEM, LEM coupling, or optimizer integration
- No validated BEM claim
- No new dependency

---

## Validation

```
PYTHONPATH=src pytest tests/geometry/test_regular_h_matrix_prototype.py -q
-> 10 passed

PYTHONPATH=src pytest tests/geometry -q
-> 409 passed   (delta: +10)
```

---

## Commit message

`BEM-006A: Add regular H-matrix prototype`

Do not push until Auditor authorizes push.
