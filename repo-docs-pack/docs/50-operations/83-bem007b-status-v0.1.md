# BEM-007B status v0.1

- Milestone: BEM-007B
- Base commit: 31bf39a
- Status: implemented / pending audit
- Expected validation: `PYTHONPATH=src pytest tests/geometry -q`
- Expected result: 439 passed

## Implemented surface

BEM-007B adds a deterministic, pure-Python, fixed-rule regular off-diagonal
triangle quadrature prototype for separated flat triangular panels. The utility
is pairwise only and evaluates the regular indirect single-layer source-panel
integral at a separated target collocation point.

## Guardrails

- No singular quadrature
- No near-singular quadrature
- No adaptive quadrature
- No Duffy transformation
- No full matrix assembly
- No BEM solve
- No observer reconstruction
- No analytical benchmark matching
- No tolerance policy
- No validated BEM claim
- No benchmark_passed=True
- No SPL/directivity/impedance/enclosure BEM/LEM/optimizer claim

## Audit expectation

Before commit, collect:

```bash
git status --short
git diff --cached --name-only
PYTHONPATH=src pytest tests/geometry/test_regular_quadrature.py -q
PYTHONPATH=src pytest tests/geometry -q
```

Expected staged files after audit authorization:

```text
repo-docs-pack/docs/40-validation/32-regular-off-diagonal-quadrature-v0.1.md
repo-docs-pack/docs/50-operations/83-bem007b-status-v0.1.md
src/ausolveris/geometry/bem.py
tests/geometry/test_regular_quadrature.py
```

Commit message after audit authorization:

```text
BEM-007B: Add regular off-diagonal quadrature prototype
```
