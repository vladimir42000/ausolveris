# BEM‑004A Status

- **Baseline:** 309 passing tests (`pytest tests/geometry -q` after BEM‑003 merge).
- **Task intent:** implement incident‑field and analytical‑reference scaffold for the
  rigid‑sphere benchmark, with tolerance policy metadata, but no BEM solve.
- **Implemented files:**
  - `src/ausolveris/geometry/bem.py` (appended BEM‑004A code)
  - `tests/geometry/test_incident_field_reference_scaffold.py`
  - `repo-docs-pack/docs/40-validation/15-incident-field-reference-scaffold-v0.1.md`
  - `repo-docs-pack/docs/50-operations/66-bem004a-status-v0.1.md`
- **Validation command:** `PYTHONPATH=src pytest tests/geometry -q`
- **Final test result:** **319 passed** (309 existing + 10 new BEM‑004A tests).
- **Explicit statement:** No linear solve, full operator generation, singular quadrature,
  scattered pressure, analytical evaluator, reference matching, SPL, impedance,
  enclosure BEM, LEM coupling, or optimizer integration was added.