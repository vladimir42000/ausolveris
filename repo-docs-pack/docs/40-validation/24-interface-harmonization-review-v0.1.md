# 24 — Observer Interface Harmonization Review
Version: v0.1
Milestone: BEM-PHASE3-PLAN-002
Type: documentation-only control-plane milestone
Executable code changes: none

---

## 1. Scope

This document records the canonical decision for the observer point-cloud
attribute name used across the BEM Phase 3 scaffold chain, and provides a
blueprint for a future bounded code patch to apply that decision consistently.

No code is changed by this document.
No harmonization is implemented by this document.
No numerical execution is authorized by this document.

---

## 2. Current mismatch

Three milestones interact with the same conceptual object — a list of exterior
Cartesian observer coordinates — but use different attribute names:

| Milestone | Class | Attribute exposed |
|---|---|---|
| BEM-004E | `ExteriorObserverScaffold` | `.observer_positions` |
| BEM-005A | `ObserverReconstructionScaffold` | consumes `.points` on input; stores as `.observer_points` |
| BEM-005B | `ReconstructionGateRequest` | stores `.observer_positions` (from BEM-004E) |

### How the mismatch manifested in BEM-005B

`ObserverReconstructionScaffold.__init__` (BEM-005A) requires the caller to
pass an object with a `.points` attribute. `ExteriorObserverScaffold` (BEM-004E)
exposes `.observer_positions`, not `.points`. These two classes therefore cannot
be composed directly.

The BEM-005B gate worked around this by:
1. Accepting both objects as separate arguments.
2. Comparing `observer_scaffold.observer_positions` to
   `reconstruction_scaffold.observer_points` explicitly.
3. Requiring tests to supply a lightweight `_Pts` wrapper to satisfy
   `ObserverReconstructionScaffold.__init__`.

This workaround is bounded and functional, but it creates a growing gap between
the public interface of BEM-004E and BEM-005A that will widen with each
subsequent milestone unless resolved.

---

## 3. Canonical contract decision

**Canonical attribute name: `observer_positions`**

All scaffold and gate classes in the BEM Phase 3 chain shall expose and consume
Cartesian exterior observer coordinates under the single name `observer_positions`.

---

## 4. Rationale

**Deterministic Cartesian observer coordinates.**
`observer_positions` names the quantity unambiguously: ordered Cartesian
coordinates of exterior acoustic observer points. `points` and `observer_points`
are generic and do not carry domain meaning.

**Alignment with BEM-PHASE3-PLAN-001.**
Phase 3 is frozen to Option A: build validation targets and reconstruction
contracts before singular quadrature. Using a single consistent attribute name
across all contracts reduces the surface area of future integration work.

**Clearer domain meaning.**
`observer_positions` communicates both the role (acoustic observer) and the
content (spatial positions). This is directly traceable to the physics of
exterior Helmholtz problems, where the observer location is a named input.

**Avoids adapter and workaround proliferation.**
Each future milestone that composes BEM-004E output with BEM-005A input would
otherwise need its own bridge — either an adapter class, an explicit comparison
workaround, or a wrapper fixture. Harmonizing the name at the source eliminates
all of these.

---

## 5. Future refactor blueprint

The following files require changes in the future harmonization patch. No
changes are made to any of these files by this document.

### `src/ausolveris/geometry/bem.py`

- `ObserverReconstructionScaffold.__init__`:
  - Change the guard from `hasattr(observer_scaffold, 'points')` to
    `hasattr(observer_scaffold, 'observer_positions')`.
  - Store the input as `self.observer_positions` (replacing `self.observer_points`).
  - Update `_compute_package_id` to reference `self.observer_positions`.
- `ObserverReconstructionScaffold.reconstruct`:
  - Replace all internal references to `self.observer_points` with
    `self.observer_positions`.
- `build_reconstruction_gate_request`:
  - Replace the comparison
    `observer_scaffold.observer_positions == reconstruction_scaffold.observer_points`
    with
    `observer_scaffold.observer_positions == reconstruction_scaffold.observer_positions`.
  - Update the gate request dataclass field from `observer_positions` (already
    correct) and any internal reference to `observer_points`.

### `tests/geometry/test_observer_reconstruction_scaffold.py`

- Replace all `MockObserverScaffold` (which supplies `.points`) with a wrapper
  or direct object that supplies `.observer_positions`.
- Update all assertions that reference `scaffold.observer_points` to reference
  `scaffold.observer_positions`.
- All 10 existing tests must pass or be replaced with equivalent harmonized
  assertions covering the same behaviours.

### `tests/geometry/test_observer_reconstruction_gate.py`

- Replace the `_Pts` wrapper class (which supplies `.points`) with a wrapper
  that supplies `.observer_positions`, or remove the wrapper entirely if the
  real `ExteriorObserverScaffold` can now be passed directly to
  `ObserverReconstructionScaffold.__init__`.
- Update internal comparisons and assertions to reference `observer_positions`
  consistently.
- All 10 existing tests must pass or be replaced with equivalent harmonized
  assertions.

### Documentation

- Any doc that refers to `.points` or `.observer_points` as a canonical
  attribute name should be updated to `.observer_positions`.

---

## 6. Future patch constraints

The harmonization code patch, when authorized, must satisfy all of the
following:

- Preserve all 389 existing tests, or update only the tests directly affected
  by the rename to equivalent harmonized assertions. Net test count must not
  decrease.
- Must not perform physical reconstruction.
- Must not assemble a physical H matrix.
- Must not implement singular quadrature.
- Must not consume or compare against the BEM-004F analytical reference.
- Must not compute SPL, directivity, or impedance.
- Must not claim validated BEM capability.
- Must not introduce new dependencies.
- Must not use Python built-in `hash()` for any deterministic package ID.
- Must follow the one-bounded-patch-at-a-time development culture: the rename
  patch covers the rename only, nothing else.

---

## 7. Explicit non-claims

- This document does not validate AuSolveris as a BEM solver.
- This document does not implement the interface harmonization.
- This document does not authorize any numerical execution.
- This document does not change any source code or test.
- AuSolveris remains without a validated rigid-sphere scattering comparison.
- AuSolveris remains without physical observer reconstruction.
- AuSolveris remains without singular quadrature.
- AuSolveris remains without SPL, directivity, or impedance output.

---

## 8. Recommended next milestone name

**BEM-005-PATCH** (preferred) or **BEM-005C**, at Director's discretion.

BEM-005-PATCH communicates that this is a bounded rename within the existing
005 scaffold family rather than a new capability layer. BEM-005C is acceptable
if the Director wishes to keep a strictly linear milestone numbering scheme.

Either name must be authorized by Director and Auditor before coding begins.

---

## Lineage

BEM-004E → BEM-005A → BEM-005B → **BEM-PHASE3-PLAN-002** → BEM-005-PATCH (pending)
