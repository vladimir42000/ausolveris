# Prototype Residual Report (BEM‑004D)

- **Scope:** BEM‑004D computes the algebraic residual of the regularized prototype
  solve (BEM‑004C) and packages it with tolerance markers.
- **Residual formula:** `r = (A + ε·I) x – rhs`
- **Norms reported:** `max_abs_residual` and `relative_l2_residual` (relative to `||rhs||_2`).
- **Tolerance split:**
  - `residual_tolerance_applied = true` (residual norms are computed)
  - `analytical_reference_comparison_performed = false`
  - `pressure_tolerance_applied = false`
  - complex pressure tolerances remain `declared_not_applied` from BEM‑004A.
- **What this is not:**
  - No analytical pressure evaluator.
  - No scattered‑pressure comparison.
  - No observer pressure reconstruction.
  - No SPL, directivity, or impedance.
  - No physical BEM validation.
- **Future step:** BEM‑004E remains the next planned milestone for analytical reference
  pressure evaluation and comparison.