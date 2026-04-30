# Helmholtz Green‑Function Utility (BEM‑001)

- **Scope:** BEM‑001 implements only the scalar free‑space Helmholtz Green‑function evaluation.
- **Convention:** `G(r, k) = exp(i*k*r) / (4*pi*r)`
- **Input validation:**
  - `r_m` must be finite and strictly positive; `r_m <= 0` raises `ValueError`.
  - `k_rad_m` must be finite and non‑negative; `k_rad_m < 0` raises `ValueError`.
  - Non‑finite values for either argument raise `ValueError`.
- **Singularity policy:** `r <= 0` is rejected; no regularisation or singular integration is performed.
- **What this is not:**
  - Not BEM matrix assembly.
  - Not a boundary integral operator.
  - Not a scattering solver.
  - Does not execute BEN‑004.
- **Future use:** BEM‑002, BEM‑003, BEM‑004 may reuse this utility.
