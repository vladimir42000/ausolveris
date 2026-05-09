# 80 — BEM-006B Status (v0.1)
Milestone: BEM-006B — Gated Exterior Reconstruction Prototype
Status: implemented — pending Auditor push authorization

---

## Base commit

bd410e4 — BEM-006A: Add regular H-matrix prototype

---

## Scope

Prototype H @ x matrix-vector multiplication only.
No analytical comparison. No tolerance policy. No validated BEM claim.

---

## What was added

- `ReconstructedObserverPressure` dataclass in `src/ausolveris/geometry/bem.py`
- `reconstruct_exterior_observer_pressure()` factory function in `src/ausolveris/geometry/bem.py`
- 10 acceptance tests in `tests/geometry/test_gated_exterior_reconstruction.py`
- Validation doc: `repo-docs-pack/docs/40-validation/28-gated-exterior-reconstruction-v0.1.md`

---

## Incident pressure policy

If `incident_pressure=None` (default): zero placeholder array, `total = scattered`.
If supplied: `total = incident + scattered`. Documented in both source and doc.

---

## Negative capability boundary (unchanged)

- No analytical reference comparison
- No BEM-005C matching scaffold invocation
- No tolerance policy application
- No singular quadrature
- No near-singular quadrature
- No BEM-005B gate modification
- No full validated BEM solve
- No SPL, directivity, or impedance
- No enclosure BEM, LEM coupling, or optimizer integration
- No validated BEM claim
- No new dependency

---

## Validation

```
PYTHONPATH=src pytest tests/geometry/test_gated_exterior_reconstruction.py -q
-> 10 passed

PYTHONPATH=src pytest tests/geometry -q
-> 419 passed   (delta: +10)
```

---

## Commit message

`BEM-006B: Add gated exterior reconstruction prototype`

Do not push until Auditor authorizes push.
