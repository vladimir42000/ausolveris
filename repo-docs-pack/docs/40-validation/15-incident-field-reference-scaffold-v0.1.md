# Incident‑Field Reference Scaffold (BEM‑004A)

- **Scope:** BEM‑004A provides the incident‑field evaluation and analytical‑reference
  metadata scaffold for the rigid‑sphere benchmark. No BEM system is solved.
- **Physical convention:** rigid (sound‑hard) sphere; Neumann boundary condition
  ∂p_total/∂n = 0. The future scattered‑field boundary data is
  ∂p_scat/∂n = -∂p_inc/∂n, computed here as a scaffold.
- **Implemented:**
  - Incident plane‑wave pressure: p_inc = A exp(i k d·x)
  - Incident normal derivative: ∂p_inc/∂n = i k (d·n) p_inc
  - Scaffold Neumann RHS: -∂p_inc/∂n
- **Tolerance policy:** declared with specific tolerances and comparison norms,
  but not applied (status = `declared_not_applied`).
- **What this is not:**
  - No BEM linear system solve.
  - No full physical operator assembly.
  - No analytical reference pressure evaluator (e.g., series solution).
  - No reference matching or error computation.
  - No SPL, impedance, or directivity.
- **Next step:** BEM‑004B – controlled boundary‑condition RHS assembly (no solve).