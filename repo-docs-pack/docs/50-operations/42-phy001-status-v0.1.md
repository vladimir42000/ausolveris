# PHY-001 Status – Single-case acoustic formulation stub

## Baseline
- 182 passing geometry tests after SOL-002.

## Intent
Implement PHY-001: a tightly scoped single-case physical acoustic formulation hook for exactly one canonical benchmark case (`phy001_free_field_monopole_pressure`).

## Implemented Files
- `src/ausolveris/geometry/solver.py` (Appended `SingleCaseAcousticFormulationInput`, `SingleCaseAcousticFormulationResult`, and `evaluate_phy001_single_case`)
- `tests/geometry/test_single_case_acoustic_formulation.py` (10 tests)
- `repo-docs-pack/docs/40-validation/06-single-case-acoustic-formulation-v0.1.md`
- `repo-docs-pack/docs/50-operations/42-phy001-status-v0.1.md`

## Validation Command
```bash
PYTHONPATH=src pytest tests/geometry -q
```

## Test Results
- All existing geometry tests pass.
- New 10 PHY-001 tests pass (192 total).

## Explicit Scope Statement
✅ No BEM/LEM/FEM/enclosure/driver framework was added.  
✅ The only physical result generated is the single analytic free-field pressure sanity case. All other descriptor inputs fail explicitly.
