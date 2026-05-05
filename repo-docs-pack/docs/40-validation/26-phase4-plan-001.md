# 26 — Phase 4 Plan 001: H-Matrix Physics & Singular Quadrature Strategy
Version: v0.1
Milestone: BEM-PHASE4-PLAN-001
Type: documentation-only control-plane milestone
Executable code changes: none

---

## 1. Scope

This document defines the strategy and roadmap for Phase 4 of AuSolveris
development: physical boundary-to-observer H-matrix assembly and
singular/near-singular quadrature. No code is implemented here. No physical
H-matrix is assembled. No validated BEM capability is claimed.

---

## 2. Phase 3 completion summary

Phase 3 established the following scaffold chain, all of which are now in place:

| Milestone | What exists |
|---|---|
| BEM-004F | Analytical rigid-sphere reference evaluator — computes exact incident, scattered, and total pressure at exterior observer points |
| BEM-005B | Reconstruction execution gate — structurally validates input packages and blocks physical execution; returns zeroed non-physical pressure placeholders |
| BEM-005C | Analytical reference matching and tolerance scaffold — compares BEM-004F analytical total pressure against BEM-005B gated reconstruction; applies tolerance thresholds and reports metrics |

**Current benchmark outcome: `benchmark_passed = False`**

This failure is expected and correct. BEM-005B returns zeroed non-physical
pressure arrays. Comparing zero reconstruction against a nonzero analytical
field yields `relative_l2_error = 1.0`, which exceeds the 1.0e-2 relative
tolerance. The scaffold chain is structurally sound; the benchmark failure
is a consequence of the still-gated physical execution, not a defect.

---

## 3. Phase 4 objective

Phase 4 must define, prototype, and progressively unlock the physical
boundary-to-observer operator before any reconstruction execution is authorized.
The objective is to replace the gated-zero BEM-005B placeholders with a
physically meaningful but still bounded exterior observer scattered pressure,
assembled from the existing boundary solution (BEM-004C) using a regular
exterior H-matrix row prototype.

Physical execution must be unlocked incrementally, milestone by milestone,
with each step remaining bounded by the negative capability constraints.

---

## 4. H-matrix interface

### Semantic contract

The boundary-to-observer operator H maps boundary surface unknowns (normal
velocity or pressure density, from BEM-004C or a later boundary solve) to
exterior observer scattered pressure values at the positions defined by
`observer_positions` (BEM-004E canonical attribute, harmonized in BEM-005-PATCH).

The operator must explicitly distinguish three pressure pathways:

| Pathway | Source |
|---|---|
| Incident pressure | Evaluated analytically at observer (BEM-004F or equivalent) |
| Scattered pressure | H × boundary unknowns — the physical product of H-matrix assembly |
| Total pressure | Incident + scattered, assembled after both pathways are available |

### Input compatibility

The H-matrix assembly must consume boundary solution packages conforming to the
`RegularizedSolvePrototype` interface (BEM-004C) or any compatible successor.
The `benchmark_id` field must match `"ben004_rigid_sphere_scattering_registered"`
for the validation benchmark.

### Observer positions

All observer coordinate inputs and outputs must use the canonical
`observer_positions` attribute established by BEM-005-PATCH. The attribute
name `points` or `observer_points` must not reappear as a canonical contract.

### Package ID

Every H-matrix assembly result must carry a deterministic SHA-256 package ID
computed from the boundary solution package ID, the observer positions, the
wavenumber, and the quadrature parameters. Python built-in `hash()` must not
be used.

---

## 5. Quadrature strategy

### Regular interactions (observer strictly exterior)

For observer points that are strictly exterior to the sphere (distance from
surface > some documented threshold), the Green function kernel is smooth and
non-singular. A bounded deterministic Gaussian quadrature over each panel
centroid or Gaussian point set is sufficient for a prototype.

Preferred approach: **panel-centroid collocation** for the initial prototype
(BEM-006A/006B), with a documented plan to upgrade to higher-order Gaussian
quadrature in a subsequent milestone.

Quadrature order must be recorded in the result package and fixed
deterministically (not drawn from random or adaptive logic) at each milestone.

### Near-singular interactions

Near-singular interactions arise when an observer point is close to but not on
the boundary surface. These must remain **explicitly gated** until a dedicated
near-singular strategy milestone is authorized. The gate must be a controlled
`ValueError` or equivalent structural block, not a silent numerical degradation.

Threshold for "near-singular": observer distance from nearest panel centroid
less than one panel diameter. This threshold must be documented and enforced
in the prototype.

### Singular / self-panel interactions

For the exterior observer reconstruction problem (observer strictly outside the
sphere), singular self-panel interactions do not arise at the observer level —
the kernel is evaluated between a surface panel and an exterior point, not
between two coincident surface points. Singular terms are therefore **not
required** for BEM-006A/006B exterior observer reconstruction.

Boundary-to-boundary singular interactions (relevant to a future boundary
solve upgrade) remain a later problem and must not be addressed in Phase 4.

### Preferred singular quadrature strategy for future boundary work

For the eventual boundary-boundary singular integrals the preferred strategy
is **singularity subtraction** (also called semi-analytical extraction):
analytically subtract the singular part of the kernel, integrate the smooth
remainder numerically, and add back the analytically computed singular
contribution. This approach is preferred over Duffy transformation (higher
implementation complexity, Jacobian singularity risk) and panel refinement
(convergence rate lower for strongly singular kernels). This preference is
recorded here for Director and Auditor reference but is not implemented in
Phase 4.

---

## 6. Gate-unlock roadmap

Each milestone below must:
- preserve all 399 existing tests or update only directly affected tests,
- preserve all negative capability flags from BEM-005C,
- not claim validated BEM capability,
- not introduce new dependencies,
- be authorized by Director and Auditor before coding begins.

```
Phase 3 (complete)
└── BEM-005C: Analytical matching scaffold — benchmark_passed=False (expected)

Phase 4 (this plan)
├── BEM-006A: Regular exterior observer H-row assembly prototype only
│   - assemble one row of H per observer point using panel-centroid collocation
│   - no near-singular gating needed if observers are strictly exterior
│   - no boundary solve upgrade
│   - result package: H_row_prototype, non-physical flag retained
│
├── BEM-006B: Gated exterior reconstruction using regular-only H on controlled panels
│   - feed BEM-006A H rows into a reconstruction execution (replacing BEM-005B gate)
│   - bounded to 3–6 panels as in BEM-003 lineage
│   - compare reconstruction to BEM-004F reference via BEM-005C scaffold
│   - benchmark_passed still expected False (under-resolved, no singular quadrature)
│
├── BEM-006C: Physical reconstruction prototype comparison to analytical reference
│   - full-panel H assembly on rigid-sphere benchmark mesh
│   - compare to BEM-004F; document convergence status
│   - benchmark_passed may still be False; not yet validated
│
└── BEM-007A or later: Near-singular / singular quadrature contract
    - define near-singular threshold enforcement
    - prototype singularity subtraction for boundary-boundary integrals
    - re-run BEM-005C matching scaffold; document whether benchmark passes
```

---

## 7. Risk register

| Risk | Description | Mitigation |
|---|---|---|
| Phase convention | Time-harmonic convention `e^{-iωt}` vs `e^{+iωt}` must match BEM-004F | Verify sign convention against BEM-004F at BEM-006A before any comparison |
| Panel normal orientation | Outward vs inward normal sign error silently flips scattered pressure | Assert positive outward normal dot product against radial direction for rigid sphere at fixture build time |
| Quadrature order / convergence | Panel-centroid collocation has low convergence order; may not pass BEM-005C tolerance | Document expected error level per panel count; do not claim passing tolerance until higher-order quadrature is implemented |
| Singular / near-singular kernel | Accidental near-singular observer point causes silent numerical blow-up | Enforce near-singular gate with controlled ValueError; never suppress NaN/Inf silently |
| Boundary unknown semantics | BEM-004C boundary solution is a regularized algebraic prototype, not a physical Neumann density | Never feed BEM-004C solution directly into a physical H-matrix without documenting the approximation |
| False validation claim | Passing BEM-005C metrics on under-resolved prototype is mistaken for validated BEM | Do not set `benchmark_passed=True` milestone until Director and Auditor have reviewed convergence evidence |

---

## 8. Hard exclusions

- No executable code changed by this document.
- No H-matrix assembly implemented.
- No singular quadrature implemented.
- No analytical evaluator (BEM-004F) changes.
- No tolerance scaffold (BEM-005C) changes.
- No SPL, directivity, or impedance computation.
- No enclosure BEM, LEM coupling, or optimizer integration.
- No validated BEM capability claimed.

---

## 9. Acceptance criteria

- This document identifies strategy, interface contract, quadrature approach,
  risk register, and milestone roadmap.
- Status file `78-phase4-plan-status-v0.1.md` exists.
- Test suite passes with exactly 399 tests.
- Only two documentation files are staged and committed.

---

## Lineage

BEM-005C → **BEM-PHASE4-PLAN-001** → BEM-006A (pending authorization)
