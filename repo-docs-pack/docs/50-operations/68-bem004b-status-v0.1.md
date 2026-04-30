# BEM‑004B Status

- **Baseline:** 319 passing tests (`pytest tests/geometry -q` after BEM‑004A merge).
- **Task intent:** implement a deterministic boundary RHS assembly for the rigid‑sphere
  sound‑hard Neumann problem, without any solve.
- **Implemented files:**
  - `src/ausolveris/geometry/bem.py` (appended BEM‑004B code)
  - `tests/geometry/test_boundary_rhs_assembly.py`
  - `repo-docs-pack/docs/40-validation/16-boundary-rhs-assembly-no-solve-v0.1.md`
  - `repo-docs-pack/docs/50-operations/68-bem004b-status-v0.1.md`
- **Validation command:** `PYTHONPATH=src pytest tests/geometry -q`
- **Final test result:** **329 passed** (319 existing + 10 new BEM‑004B tests).
- **Explicit statement:** No matrix assembly, operator application, singular/near‑singular
  quadrature, linear solve, scattering solution, reference matching, SPL, impedance,
  enclosure BEM, LEM coupling, or optimizer integration was added.