# Non‑Singular Operator Prototype (BEM‑003)

- **Scope:** BEM‑003 implements a controlled, non‑singular Green‑function interaction
  prototype only. It uses the BEM‑001 Helmholtz Green function and BEM‑002 panel
  centroids/areas for a small subset (3–6 panels) of the rigid‑sphere fixture.
- **Formula:** For i ≠ j, `A_ij = G(|x_i – x_j|, k) * area_j`. Diagonal entries are zero
  placeholders; self‑interaction is never evaluated.
- **Non‑singular policy:** Panel pairs closer than a declared `min_distance` threshold are
  rejected. No singular or near‑singular integrals are performed.
- **What this is not:**
  - Full‑sphere operator assembly.
  - Boundary integral equation solve.
  - Scattering solution.
  - SPL or impedance computation.
  - Analytical reference comparison.
- **Future use:** BEM‑004 remains the first planned scattering‑solve milestone.