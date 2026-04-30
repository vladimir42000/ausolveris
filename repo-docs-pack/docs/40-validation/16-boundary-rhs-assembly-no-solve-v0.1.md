# Boundary RHS Assembly (BEM‑004B)

- **Scope:** BEM‑004B assembles the deterministic sound‑hard Neumann boundary RHS vector
  from the incident‑field scaffold. No BEM solve is performed.
- **RHS formula:** `rhs_j = -∂p_inc/∂n` at panel centroid `j`.
- **Uses:** BEM‑004A scaffold (incident field and normal derivative) and BEM‑002 fixture
  panel normals.
- **What this is not:**
  - No BEM matrix assembly.
  - No boundary integral operator application.
  - No linear system solve.
  - No scattered‑field reconstruction.
  - No analytical reference comparison.
  - No SPL, impedance, or directivity.
- **Next step:** BEM‑004C – controlled matrix‑free operator application (no solve).