# 25 — Analytical Matching Scaffold (BEM-005C)
Version: v0.1
Milestone: BEM-005C
Stage: bem005c_analytical_matching_scaffold

---

## Purpose

BEM-005C implements a matching and tolerance scaffold that compares the
BEM-004F analytical total pressure against the BEM-005B gated reconstructed
total pressure. It applies explicit tolerance thresholds and reports whether
the benchmark passes or fails.

---

## What BEM-005C does

- Accepts the BEM-004F analytical reference package (dict from
  `AnalyticalRigidSphereReferenceEvaluator.evaluate()`) and the BEM-005B
  gated reconstruction result (`ReconstructionGateResult`).
- Validates benchmark IDs and pressure array lengths.
- Extracts analytical and reconstructed total pressure arrays.
- Computes `relative_l2_error = ||p_anal - p_rec||_2 / ||p_anal||_2`.
- Computes `max_abs_error = max(|p_anal[i] - p_rec[i]|)`.
- Applies tolerance thresholds:
  - relative pressure tolerance: 1.0e-2
  - absolute pressure tolerance: 1.0e-6
- Sets `benchmark_passed = (relative_l2_error <= 1e-2) AND (max_abs_error <= 1e-6)`.
- Sets `reference_matching_performed = True` and `tolerance_policy_applied = True`.
- Emits a deterministic SHA-256 package ID.

---

## Current expected benchmark outcome

**`benchmark_passed = False`**

This failure is **expected and required** at this phase. BEM-005B returns
zeroed non-physical placeholder pressure arrays. Comparing zero reconstruction
against a nonzero analytical field produces `relative_l2_error = 1.0`,
which exceeds the 1.0e-2 relative tolerance. This deterministic failure
is the correct behavior of the scaffold until a physical reconstruction
replaces the BEM-005B gate.

---

## What BEM-005C does not do

| Capability | Status |
|---|---|
| Physical H-matrix assembly | Not performed |
| Physical boundary-to-observer reconstruction | Not performed |
| Singular quadrature | Not implemented |
| Full BEM solve | Not performed |
| SPL computation | Not computed |
| Directivity computation | Not computed |
| Impedance computation | Not computed |
| Validated BEM capability claim | Not made |

BEM-005C does not modify BEM-004F analytical evaluator math.
BEM-005C does not spoof analytical or reconstructed data to force `benchmark_passed=True`.

---

## Required metadata in result

```python
{
    "validation_stage": "bem005c_analytical_matching_scaffold",
    "benchmark_id": "ben004_rigid_sphere_scattering_registered",
    "reference_matching_performed": True,
    "tolerance_policy_applied": True,
    "benchmark_passed": False,          # expected under gated-zero reconstruction
    "physical_h_matrix_assembled": False,
    "singular_quadrature_implemented": False,
    "spl_computed": False,
    "directivity_computed": False,
    "impedance_computed": False,
    "non_physical": True,
}
```

---

## Public API

### `build_analytical_matching_report`

```python
build_analytical_matching_report(
    analytical_package: dict,
    reconstruction_result: ReconstructionGateResult,
) -> ReferenceMatchingReport
```

Raises `ValueError` on: wrong type, benchmark_id mismatch, length mismatch,
or zero analytical norm.

---

## Validation baseline

```
PYTHONPATH=src pytest tests/geometry/test_analytical_matching_scaffold.py -q
-> 10 passed

PYTHONPATH=src pytest tests/geometry -q
-> 399 passed
```

---

## Lineage

BEM-004F → BEM-005B → **BEM-005C** → (future: physical reconstruction replacing BEM-005B gate)
