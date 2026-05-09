# 29 — Pipeline Integration Report (BEM-006C)
Version: v0.1
Milestone: BEM-006C
Stage: bem006c_pipeline_integration_report

---

## Purpose

BEM-006C connects the BEM-006B reconstructed numerical pressure output to the
BEM-005C-style analytical matching pipeline and generates an expected-failure
report. It proves the full pipeline can consume real complex numerical arrays,
compute error norms, and report a deterministic benchmark outcome.

---

## What BEM-006C does

- Accepts the BEM-004F analytical reference package and the BEM-006B
  `ReconstructedObserverPressure` package.
- Validates benchmark IDs and pressure array lengths.
- Asserts that the reconstruction contains real numerical data (not gated zeros).
- Computes `relative_l2_error = ||p_anal_total - p_rec_total||_2 / ||p_anal_total||_2`.
- Computes `max_abs_error = max(|p_anal_total[i] - p_rec_total[i]|)`.
- Applies tolerance thresholds (relative: 1.0e-2, absolute: 1.0e-6).
- Sets `benchmark_passed = False` (expected and required).
- Sets `numerical_data_consumed = True`.
- Emits a deterministic SHA-256 package ID.

---

## Expected benchmark outcome

**`benchmark_passed = False`**

This failure is **expected and required**. It is not a software defect.

The reconstructed pressure is produced by a regular exterior prototype using:
- A toy 3–6 panel centroid-collocation H-matrix.
- An artificially regularized boundary solution (BEM-004C), not a physically
  correct Neumann density.
- No singular quadrature, no convergence guarantee.

The prototype computes a genuine (non-zero) H @ x product, but the result
is numerically far from the BEM-004F analytical total pressure. This gap
records where the project stands and what physical improvements are needed.

---

## What BEM-006C does not do

| Capability | Status |
|---|---|
| Singular quadrature | Not implemented |
| Near-singular quadrature | Not implemented |
| Full validated BEM boundary solve | Not performed |
| SPL, directivity, impedance | Not computed |
| Validated BEM capability | Not claimed |
| `benchmark_passed = True` | Not set — result spoofing is forbidden |

BEM-006C does not modify the BEM-004F analytical evaluator.
BEM-006C does not spoof or adjust reconstructed data to force a passing result.

---

## Required metadata

```python
{
    "validation_stage": "bem006c_pipeline_integration_report",
    "benchmark_id": "ben004_rigid_sphere_scattering_registered",
    "numerical_data_consumed": True,
    "analytical_reference_matched": True,
    "tolerance_policy_applied": True,
    "benchmark_passed": False,           # expected under prototype reconstruction
    "error_norms_computed": True,
    "physical_h_matrix_assembled": True,
    "singular_quadrature_implemented": False,
    "non_physical_prototype_warning": True,
    "spl_computed": False,
    "directivity_computed": False,
    "impedance_computed": False,
}
```

---

## Validation baseline

```
PYTHONPATH=src pytest tests/geometry/test_pipeline_integration.py -q
-> 10 passed

PYTHONPATH=src pytest tests/geometry -q
-> 429 passed
```

---

## Lineage

BEM-004F + BEM-006B → **BEM-006C**
→ BEM-007A or later: near-singular/singular quadrature strategy
  (pending Director and Auditor authorization)
