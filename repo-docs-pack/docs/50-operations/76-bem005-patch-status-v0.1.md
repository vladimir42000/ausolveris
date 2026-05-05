# 76 — BEM-005-PATCH Status (v0.1)
Milestone: BEM-005-PATCH — Observer Interface Harmonization Execution
Status: COMPLETE — pending Auditor push authorization

---

## Base commit

8c6de8c — BEM-PHASE3-PLAN-002: Freeze observer interface harmonization plan

---

## Scope

Observer interface harmonization only.
Canonical attribute unified to `observer_positions` across the BEM-005 scaffold chain.
No numerical capability added.
No validated BEM claim.

---

## Canonical attribute

`observer_positions` is the single, authoritative attribute name for the
Cartesian exterior observer point-cloud at every scaffold and gate surface.

`points` and `observer_points` are no longer canonical production contracts.

---

## Changes applied

### `src/ausolveris/geometry/bem.py`

- `ObserverReconstructionScaffold.__init__`:
  - Guard changed from `hasattr(observer_scaffold, 'points')` to
    `hasattr(observer_scaffold, 'observer_positions')`.
  - Input read from `.observer_positions` (was `.points`).
  - Stored attribute renamed from `self.observer_points` to `self.observer_positions`.
- `ObserverReconstructionScaffold.reconstruct`:
  - Internal length reference updated from `self.observer_points` to
    `self.observer_positions`.
- `ObserverReconstructionScaffold._compute_package_id`:
  - JSON key renamed from `"observer_points"` to `"observer_positions"`.
- `build_reconstruction_gate_request`:
  - Temporary bridge comment removed.
  - Comparison updated from `reconstruction_scaffold.observer_points` to
    `reconstruction_scaffold.observer_positions`.
  - Error message updated to name `observer_positions` consistently.

### `tests/geometry/test_observer_reconstruction_scaffold.py`

- `MockObserverScaffold`: attribute renamed from `.points` to `.observer_positions`.
- `test_1`: assertion updated from `.observer_points` / `.points` to
  `.observer_positions` / `.observer_positions`.
- `test_4`: length reference updated from `.points` to `.observer_positions`.
- `test_10`: rejection comment updated from "no points" to "no observer_positions".

### `tests/geometry/test_observer_reconstruction_gate.py`

- `_Pts` wrapper: attribute renamed from `.points` to `.observer_positions`.
  Class docstring and surrounding comment updated.
- Fixture `reconstruction_scaffold`: comment updated.
- No test logic changed — all 10 tests continue to exercise the same behaviors.

---

## Files not changed

- `tests/geometry/test_exterior_observer_scaffold.py` — BEM-004E already used
  `observer_positions`; no change required.
- All other source and test files — not in scope.
- `repo-docs-pack/docs/40-validation/24-interface-harmonization-review-v0.1.md` —
  updated separately to mark the blueprint as implemented.

---

## Test result

```
PYTHONPATH=src pytest tests/geometry/test_exterior_observer_scaffold.py -q  → 10 passed
PYTHONPATH=src pytest tests/geometry/test_observer_reconstruction_scaffold.py -q  → 10 passed
PYTHONPATH=src pytest tests/geometry/test_observer_reconstruction_gate.py -q  → 10 passed
PYTHONPATH=src pytest tests/geometry -q  → 389 passed
```

Test delta: 0 (no tests added or removed).

---

## Hard exclusions (unchanged)

- No singular quadrature
- No full BEM solve
- No physical H-matrix assembly
- No physical observer-pressure reconstruction
- No analytical reference comparison
- No tolerance-policy application
- No SPL, directivity, or impedance
- No enclosure BEM, LEM coupling, or optimizer integration
- No validated BEM claim
- No new dependency

---

## Commit message

`BEM-005-PATCH: Harmonize observer interface naming`

Do not push until Auditor authorizes push.
