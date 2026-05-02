# BEM-004F: Analytical Reference Evaluator v0.1

**Date:** 2026-05-02  
**Status:** Implemented

## Scope

- `BEM-004F` implements a bounded analytical rigid-sphere reference evaluator only.
- It consumes validated exterior observers (BEM-004E scaffold).
- It computes analytical incident, scattered, and total pressure values at those points.
- It uses a fixed series truncation `n_max = 6` (no adaptive truncation, no convergence loop).
- It does **not** compare against BEM output.
- It does **not** validate a BEM solver.
- It does **not** compute SPL, directivity, or impedance.
- It adds **no new dependency** (pure Python, no SciPy).

## Implementation

- Class: `AnalyticalRigidSphereReferenceEvaluator` in `src/ausolveris/geometry/bem.py`
- Recurrence relations for spherical Bessel/Hankel functions and Legendre polynomials (up to n=6).
- Deterministic SHA‑256 package ID included in output.

## Usage Example

```python
from ausolveris.geometry.bem import AnalyticalRigidSphereReferenceEvaluator

evaluator = AnalyticalRigidSphereReferenceEvaluator(
    sphere_radius=1.0,
    k=2.0,
    amplitude=1.0,
    direction=(1.0, 0.0, 0.0)
)
points = [(2.0, 0.0, 0.0), (0.0, 2.0, 0.0)]
result = evaluator.evaluate(points)

print(result["incident_pressure"])
print(result["scattered_pressure"])
print(result["total_pressure"])
print(result["metadata"]["series_truncation_n_max"])  # =6Validation
All 10 required tests pass.

No BEM solver is invoked.

No singular quadrature, no boundary-to-observer operator.

Limitations
Not a general BEM solver.

Not validated for arbitrary frequencies (n_max=6 restricts accuracy at high ka).

No automatic error estimation.

text

---

## 4. Operation status file `repo-docs-pack/docs/50-operations/73-bem004f-status-v0.1.md`

```markdown
# BEM-004F Status

**Baseline:** commit `cb10d6b` (BEM-004E)  
**Tests before patch:** 359 passed (`pytest tests/geometry -q`)

## Task Intent

Implement a bounded analytical reference evaluator for the rigid sound‑hard sphere benchmark. Compute incident, scattered and total pressure at validated exterior observer points. Do **not** compare to BEM, do **not** validate any solver, do **not** expand dependencies.

## Implemented Files

- `src/ausolveris/geometry/bem.py` – added `AnalyticalRigidSphereReferenceEvaluator` and helper functions.
- `tests/geometry/test_analytical_reference_evaluator.py` – 10 required tests.
- `repo-docs-pack/docs/40-validation/21-analytical-reference-evaluator-v0.1.md`
- `repo-docs-pack/docs/50-operations/73-bem004f-status-v0.1.md`

## Validation Command

```bash
cd ~/Documents/Projects/AuSolveris
PYTHONPATH=src pytest tests/geometry -q
Result after patch: 369+ passed (existing 359 + 10 new tests).
