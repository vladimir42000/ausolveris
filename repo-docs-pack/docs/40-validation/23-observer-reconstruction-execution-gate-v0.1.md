# 23 — Observer Reconstruction Execution Gate (BEM-005B)
Version: v0.1
Milestone: BEM-005B
Stage: bem005b_reconstruction_execution_gate

---

## Purpose

BEM-005B implements a structural validation gate that sits between the existing
boundary-solution prototype (BEM-004C) and any future physical reconstruction.
It verifies that required inputs exist and are structurally consistent, then
explicitly blocks physical execution and returns a deterministic non-physical
result package.

---

## What this gate does

- Accepts three already-constructed packages:
  - `RegularizedSolvePrototype` (BEM-004C)
  - `ExteriorObserverScaffold` (BEM-004E)
  - `ObserverReconstructionScaffold` (BEM-005A)
- Validates types and benchmark IDs with controlled `ValueError` (no accidental `AttributeError`).
- Validates that `observer_scaffold.observer_positions` matches
  `reconstruction_scaffold.observer_points` exactly.
- Sets `request_validated=True` only after all checks pass.
- Returns zeroed, explicitly non-physical pressure placeholder arrays.
- Emits a deterministic SHA-256 package ID that changes when any input package changes.

---

## What this gate does not do

| Capability | Status |
|---|---|
| Physical H-matrix assembly | Not performed |
| Physical boundary-to-observer reconstruction | Not performed |
| Analytical reference comparison (BEM-004F) | Not performed |
| Tolerance policy application | Not applied |
| Singular quadrature | Not implemented |
| SPL computation | Not computed |
| Directivity computation | Not computed |
| Impedance computation | Not computed |

---

## Public API

### `build_reconstruction_gate_request`

```python
build_reconstruction_gate_request(
    boundary_solution: RegularizedSolvePrototype,
    observer_scaffold: ExteriorObserverScaffold,
    reconstruction_scaffold: ObserverReconstructionScaffold,
) -> ReconstructionGateRequest
```

Raises `ValueError` on any structural inconsistency.
Returns a `ReconstructionGateRequest` with `request_validated=True`.

### `execute_reconstruction_gate`

```python
execute_reconstruction_gate(
    request: ReconstructionGateRequest,
) -> ReconstructionGateResult
```

Accepts only a validated request. Returns `ReconstructionGateResult` with
all capability flags set to `False` and all pressure arrays zeroed.

---

## Required metadata in result

```python
{
    "reconstruction_stage": "bem005b_reconstruction_execution_gate",
    "benchmark_id": "ben004_rigid_sphere_scattering_registered",
    "request_validated": True,
    "execution_gated": True,
    "physical_h_matrix_assembled": False,
    "physical_reconstruction_performed": False,
    "analytical_reference_comparison_performed": False,
    "tolerance_policy_applied": False,
    "singular_quadrature_implemented": False,
    "spl_computed": False,
    "directivity_computed": False,
    "impedance_computed": False,
    "non_physical": True,
}
```

---

## Validation baseline

```
PYTHONPATH=src pytest tests/geometry/test_observer_reconstruction_gate.py -q
-> 10 passed

PYTHONPATH=src pytest tests/geometry -q
-> 389 passed
```

---

## Lineage

BEM-004C → BEM-004E → BEM-005A → **BEM-005B** → (future: BEM-005C singular quadrature)

No physical solver capability is claimed at this stage.
