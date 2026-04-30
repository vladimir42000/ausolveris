# BEM‑001 Status

- **Baseline:** 278 passing tests (`pytest tests/geometry -q` on commit `9c404fd`).
- **Task intent:** implement scalar Helmholtz Green‑function utility and validation hooks.
- **Implemented files:**
  - `src/ausolveris/geometry/bem.py`
  - `tests/geometry/test_helmholtz_green_function.py`
  - `repo-docs-pack/docs/40-validation/12-helmholtz-green-function-utility-v0.1.md`
  - `repo-docs-pack/docs/50-operations/60-bem001-status-v0.1.md`
- **Validation command:** `PYTHONPATH=src pytest tests/geometry -q`
- **Final test result:** **288 passed** (all 10 new tests pass).
- **Explicit statement:** No matrix assembly, operator application, scattering solve, mesh generation, SPL/impedance output, enclosure BEM, LEM coupling, or optimizer integration was added.
