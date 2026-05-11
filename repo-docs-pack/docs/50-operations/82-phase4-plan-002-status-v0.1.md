# 82 — BEM-PHASE4-PLAN-002 Status (v0.1)
Milestone: BEM-PHASE4-PLAN-002 — Transition to Physical Boundary Accuracy
Status: implemented — pending Auditor push authorization
Type: documentation-only

---

## Base commit

067c114 — BEM-006C: Add pipeline integration report

---

## Scope

Phase 4 transition plan only.
No Python source files changed.
No tests added, modified, or removed.
No singular quadrature implemented.
No solver behaviour altered.
No validated BEM claim.

---

## Files staged

```
repo-docs-pack/docs/40-validation/30-phase4-plan-002.md
repo-docs-pack/docs/50-operations/82-phase4-plan-002-status-v0.1.md
```

No other files staged or touched.

---

## Key content of the plan

- Current "live-failure" plateau described (benchmark_passed=False, expected).
- Singular quadrature candidates evaluated; semi-analytical extraction
  preferred for self-panel diagonal; higher-order Gauss rules for regular
  off-diagonal entries.
- Auditor Technical Critique section (§4) lists seven mandatory checks
  before any quadrature milestone is authorized.
- Full-sphere mapping plan: controlled subset → level-1 → level-2 → level-3.
- Convergence path with panel count ladder and n_max progression.
- Proposed milestone sequence: BEM-007A through BEM-008B.
- Risk register: 7 risks documented with mitigations.

---

## Auditor Technical Critique Required Before Phase 5

Section 4 of `30-phase4-plan-002.md` lists seven items that the Auditor
must verify and record before any BEM-007A or later coding patch is
authorized:

1. Kernel singularity form
2. Panel geometry assumptions
3. Normal derivative convention
4. Diagonal / self-panel treatment
5. Phase convention consistency
6. Deterministic reproducibility
7. Validation target and error thresholds

No Phase 5 or quadrature implementation may proceed without this critique.

---

## Validation

```
PYTHONPATH=src pytest tests/geometry -q
-> 429 passed   (unchanged, delta: 0)
```

---

## Negative capability boundary (unchanged)

- No singular quadrature
- No solver behaviour change
- No full BEM solve
- No SPL, directivity, or impedance
- No enclosure BEM, LEM coupling, or optimizer integration
- No validated BEM claim
- No new dependency

---

## Commit message

`BEM-PHASE4-PLAN-002: Freeze physical boundary accuracy transition plan`

Do not push until Auditor authorizes push.
