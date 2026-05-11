# 30 — Phase 4 Plan 002: Transition to Physical Boundary Accuracy
Version: v0.1
Milestone: BEM-PHASE4-PLAN-002
Type: documentation-only control-plane milestone
Executable code changes: none

---

## 1. Scope

BEM-PHASE4-PLAN-002 drafts the transition path from the current
"live-failure" prototype state to a future physical boundary solve with
singular quadrature and full-sphere mesh coverage.

No code is changed. No quadrature is implemented. No solver behaviour is
altered. No validated BEM capability is claimed.

---

## 2. Current plateau summary

The project has reached the following state as of BEM-006C:

| Component | Status |
|---|---|
| Analytical rigid-sphere reference (BEM-004F) | Implemented, `n_max=6`, deterministic |
| Boundary RHS (BEM-004B) | Implemented on 3–6 panel controlled subset |
| Regularized algebraic boundary solve (BEM-004C) | Prototype only, no physical Neumann density |
| Regular exterior H-matrix assembly (BEM-006A) | Single-layer centroid collocation, regular interactions only |
| Observer reconstruction (BEM-006B) | `p_scattered = H @ x`, prototype panel subset |
| Analytical matching / tolerance reporting (BEM-005C / BEM-006C) | Wired end-to-end |
| `benchmark_passed` | `False` — expected and honest |

The full data path from boundary unknowns to observer reconstruction to
analytical matching is wired and deterministic. The benchmark failure is not
a pipeline defect. It is a consequence of two mathematical deficits:

1. **Boundary unknown accuracy.** The BEM-004C solution is an artificially
   regularized algebraic prototype. It does not represent a physically correct
   Neumann density on the sphere surface.

2. **Operator completeness.** The BEM-003/006A operator uses only the
   single-layer centroid-collocation approximation on 3–6 panels. No singular
   self-panel diagonal correction, no near-singular treatment, and no
   convergence with panel refinement have been established.

Addressing these two deficits is the purpose of the transition path defined
here.

---

## 3. Singular quadrature selection

### Candidate methods

**Duffy transformation**
Maps a triangle integral with an integrand singular at a corner into a
product of regular integrals by a change of variables that cancels the
Jacobian singularity. Widely used in acoustic and electromagnetic BEM.
Disadvantage: the transformation introduces a Jacobian that concentrates
quadrature points near the singularity; convergence can be slow for kernels
with strong singularities; implementation complexity is moderate to high.

**Semi-analytical singular extraction**
Decomposes the kernel into a known singular part (evaluated analytically)
and a smooth remainder (integrated numerically). Particularly effective for
the scalar Helmholtz kernel `G(r,k) = exp(ikr)/(4πr)` because the leading
singular term `1/(4πr)` has a closed-form triangle-panel integral.
Advantage: the numerical quadrature operates only on a smooth residual, so
standard Gaussian rules converge quickly. Disadvantage: requires the
closed-form singular integral to be derived and verified for each kernel type.

**Singularity subtraction**
Identical in spirit to semi-analytical extraction but sometimes applied at
the integrand level rather than decomposing the analytic formula. Slightly
more general; shares the same convergence advantage for the smooth remainder.

**High-order Gaussian quadrature for regular and near-regular interactions**
For observer-to-panel interactions where the observer is strictly exterior
and well-separated, high-order Gaussian rules on the triangle converge
exponentially. The current centroid-collocation rule is order 1; moving to
7- or 13-point Gauss rules over triangles is a bounded, low-risk improvement.
This does not address self-panel singularities but improves off-diagonal
accuracy significantly.

**Adaptive panel refinement**
Recursively subdivide panels near the singularity until the integrand is
smooth on each sub-panel. A robust fall-back for validation but not efficient
for production; convergence rate is problem-dependent. Should be treated as
an auxiliary verification tool, not the primary strategy.

### Preferred first implementation strategy

**Semi-analytical singular extraction for self-panel diagonal entries,
combined with higher-order Gaussian quadrature for all off-diagonal
(regular) entries.**

Rationale:
- The scalar Helmholtz kernel's singular part `1/(4πr)` has a well-known
  closed-form triangle-panel integral. This makes semi-analytical extraction
  tractable with modest derivation effort.
- For the rigid-sphere benchmark the dominant accuracy gap is in the
  self-panel diagonal (boundary-to-boundary operator), not in the
  boundary-to-observer rows (which are already regular).
- Upgrading off-diagonal regular quadrature from centroid-collocation to a
  higher-order Gauss rule is independent of the singular strategy and can
  proceed first as BEM-007B.
- Duffy transformation is not preferred because it adds implementation
  complexity without a clear accuracy advantage over semi-analytical
  extraction for the Helmholtz kernel.
- Adaptive refinement is reserved for verification only.

---

## 4. Required Auditor Technical Critique Before Phase 5

The following items must be verified by the Auditor before any quadrature
implementation milestone is authorized. No BEM-007A or later coding patch
may proceed until this critique is complete and recorded.

**4.1 Kernel singularity form**
Confirm the exact singular expansion of the Helmholtz Green function
`G(r,k) = exp(ikr)/(4πr)` and its normal derivative `∂G/∂n` at `r → 0`.
Confirm whether the boundary operator in use is single-layer, double-layer,
or combined, and that the singular part matches the chosen quadrature formula.

**4.2 Panel geometry assumptions**
Confirm that all benchmark panels are flat triangles. Confirm that the
closed-form singular integral formula used in semi-analytical extraction
is derived for flat triangles, not curved elements.

**4.3 Normal derivative convention**
Confirm the sign convention for outward normals on the sphere surface.
Confirm that the normal-derivative kernel `∂G/∂n(x,y)` uses the outward
normal at the source point `y` (not the observer). Verify against BEM-004B
RHS convention and BEM-006A H-row convention.

**4.4 Diagonal / self-panel treatment**
Confirm the intended self-panel formula: closed-form solid-angle term or
semi-analytical extraction result. Confirm that `k=0` and `k>0` cases are
handled separately if the singular extraction result depends on `k`.

**4.5 Phase convention consistency**
Confirm that the time-harmonic convention `e^{-iωt}` is used consistently
in the Green function, the analytical reference (BEM-004F), the incident
field (BEM-004A), and the boundary RHS (BEM-004B). A sign error here
produces a result that looks plausible but fails comparison by a complex
conjugate.

**4.6 Deterministic reproducibility**
Confirm that all quadrature point sets (Gauss rule tables, singular
extraction constants) are hard-coded deterministic constants, not drawn
from library calls whose output could change between versions.

**4.7 Validation target and error thresholds**
Confirm the expected convergence rate for the chosen quadrature scheme on
the rigid-sphere benchmark. Define the panel count and `n_max` values at
which the project would claim the benchmark has passed, and what error
thresholds would be accepted as validated. Document these targets before
coding begins so the acceptance criteria are set independently of the
numerical result.

---

## 5. Full-sphere mapping plan

The current implementation is restricted to a 3–6 panel controlled subset
of the rigid-sphere benchmark mesh. The transition to a full-sphere solve
must be incremental.

**Step 1 — Controlled subset remains as smoke-test fixture**
The 3–6 panel subset and its associated package IDs must be preserved
throughout Phase 5. Any regression in the controlled subset must block
further development.

**Step 2 — Small full-sphere meshes**
Introduce full-sphere meshes at low subdivision levels (e.g. subdivision
level 1: 20 panels, level 2: 80 panels). Assemble H and solve on the full
mesh. Compare to BEM-004F. Document the expected failure at low resolution.

**Step 3 — Incremental panel count**
Increase panel count in bounded steps (20 → 80 → 320 → 1280). At each
step: record `relative_l2_error`, check deterministic package ID, confirm
no regression on the controlled subset.

**Step 4 — Preserve deterministic mesh and package IDs**
Every mesh and every result package must carry a SHA-256 ID that is stable
across runs and changes when any input changes. No mesh may be generated
with a non-deterministic seed.

---

## 6. Convergence path

### Panel count

| Step | Panels | Expected outcome |
|---|---|---|
| Current prototype | 3–6 | `benchmark_passed=False`, large error, expected |
| Level 1 full sphere | ~20 | `benchmark_passed=False`, large error, expected |
| Level 2 full sphere | ~80 | Error should decrease; still expected to fail |
| Level 3 full sphere | ~320 | With singular quadrature: error may approach tolerance |
| Level 4 full sphere | ~1280 | Potential `benchmark_passed=True` claim, if Auditor approves |

### Analytical `n_max`

The BEM-004F reference is currently computed at `n_max=6`. As panel count
and wavenumber `k` increase, `n_max` should be raised to keep the analytical
reference more accurate than the numerical result. Each change to `n_max`
must be a separate documented patch.

### Claim policy

`benchmark_passed=True` must not be reported until:
- the Auditor has reviewed the convergence evidence at two consecutive
  refinement levels,
- the `relative_l2_error` falls below the declared tolerance at both levels,
- the Director has authorized the claim.

No premature claim is acceptable regardless of what the numbers show.

---

## 7. Proposed milestone sequence

```
BEM-PHASE4-PLAN-002 (this document)
│
├── BEM-007A: Singular-kernel taxonomy and self-panel formula freeze
│   - Document exact singular expansion for the Helmholtz kernel.
│   - Derive and record the closed-form self-panel integral formula.
│   - Documentation-only; no code.
│
├── BEM-007B: Higher-order Gaussian quadrature for regular off-diagonal entries
│   - Replace centroid collocation with Gaussian triangle rules (7+ points).
│   - Preserve controlled subset smoke tests.
│   - Re-run BEM-006C pipeline; document error change.
│
├── BEM-007C: Boundary operator diagonal replacement for controlled subset
│   - Replace zeroed/approximate diagonal with semi-analytical extraction.
│   - Smoke test on controlled 3–6 panel subset only.
│   - No full-sphere claim.
│
├── BEM-008A: First full-sphere mesh boundary solve smoke
│   - Introduce level-1 full-sphere mesh (~20 panels).
│   - Assemble and solve on full mesh with BEM-007B/007C quadrature.
│   - Document error; expect failure.
│
└── BEM-008B: Convergence ladder against analytical reference
    - Level 1 → 2 → 3 mesh refinement.
    - Record error at each level.
    - Determine whether benchmark_passed=True is justifiable.
    - Auditor review required before claim.
```

Names (007A, 007B, etc.) may be revised by Director and Auditor before
each milestone is authorized.

---

## 8. Risk register

| Risk | Description | Mitigation |
|---|---|---|
| False validation claim | Reporting `benchmark_passed=True` before genuine convergence is demonstrated | Require two consecutive refinement levels below tolerance; Auditor sign-off required |
| Singular diagonal error | Incorrect closed-form self-panel formula silently corrupts the diagonal | Verify formula against published BEM references; cross-check with Duffy implementation on a single panel |
| Normal orientation / sign convention | Outward normal sign error flips scattered pressure sign | Assert positive outward-normal dot product against radial direction at fixture build time; test at BEM-007C |
| Phase convention mismatch | `e^{+iωt}` vs `e^{-iωt}` inconsistency between analytical reference and numerical solver | Explicitly document convention in BEM-004F and verify that BEM-004B and BEM-006A use the same sign |
| Ill-conditioning / regularization leakage | BEM-004C regularization epsilon leaks into physical result | Never feed BEM-004C solution directly into a validated solve claim; require a physical Neumann solve as a separate milestone |
| Convergence masking | Error decreases with refinement for the wrong reason (numerical cancellation) | Track individual observer errors, not just norms; inspect complex phases |
| Deterministic ID drift | A code change silently alters the SHA-256 package ID of an existing fixture | Run the controlled-subset smoke test as a regression check on every patch; any ID change must be deliberate and documented |

---

## 9. Hard exclusions

- No executable code changed by this document.
- No quadrature implementation.
- No solver behaviour change.
- No SPL, directivity, or impedance computation.
- No enclosure BEM.
- No LEM coupling.
- No optimizer integration.
- No validated BEM capability claimed.

---

## 10. Acceptance criteria

- This plan document exists and covers all ten required sections.
- Status file `82-phase4-plan-002-status-v0.1.md` exists.
- Exactly two documentation files are staged and committed.
- Test suite passes at exactly 429 tests (delta: 0).
- Auditor technical critique (Section 4) is required and must be recorded
  before any Phase 5 or quadrature implementation milestone is authorized.

---

## Lineage

BEM-006C → **BEM-PHASE4-PLAN-002** → BEM-007A (pending authorization)
