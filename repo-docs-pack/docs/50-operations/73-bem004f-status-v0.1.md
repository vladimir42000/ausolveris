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

Compliance with Constraints
Constraint	Status
No SciPy / no new dependency	✅ pure Python
No BEM comparison	✅
No BEM reconstruction	✅
No singular quadrature	✅
No tolerance‑policy application	✅
No SPL/directivity/impedance	✅
Fixed n_max = 6	✅
No adaptive truncation	✅
No convergence loop	✅
Deterministic package ID (SHA‑256)	✅
