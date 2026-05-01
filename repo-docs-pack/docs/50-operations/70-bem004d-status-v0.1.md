# BEM‑004D Status

- **Baseline:** commit `d73004a` with 339 passing tests (after BEM‑004C merge).
- **Task intent:** compute a deterministic residual report for the regularized prototype
  solve, with explicit tolerance split (residual applied, pressure/analytical not).
- **Implemented files:**
  - `src/ausolveris/geometry/bem.py` (appended BEM‑004D functions)
  - `tests/geometry/test_prototype_residual_report.py`
  - `repo-docs-pack/docs/40-validation/18-prototype-residual-report-v0.1.md`
  - `repo-docs-pack/docs/50-operations/70-bem004d-status-v0.1.md`
- **Validation command:** `PYTHONPATH=src pytest tests/geometry -q`
- **Final test result:** **349 passed** (339 existing + 10 new BEM‑004D tests).
- **Explicit statement:** No analytical pressure evaluation, no scattered‑pressure
  comparison, no observer pressure, no SPL, directivity, impedance, full‑sphere solve,
  enclosure BEM, LEM coupling, or optimizer integration was added.