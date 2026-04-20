# EXP-001 Status – Model Primitives (v0.1)

**Date:** 2026-04-20  
**Status:** Implemented (awaiting audit)

**Scope summary**  
Optional in-memory geometry primitives added to GeometryModel (points/edges dicts).  
Primitives are strictly in-memory only for this experiment.

**Files changed**  
- `src/ausolveris/geometry/model.py` (extended `__init__` signature + storage + `_validate` only)  
- `tests/geometry/test_model_primitives.py` (new file – exactly 8 tests)  
- `repo-docs-pack/docs/50-operations/18-exp-001-status-v0.1.md` (this status file)

**Notes**  
- points/edges are in-memory only  
- to_dict/from_dict are intentionally unchanged (no serialization of primitives)  
- Frame, Anchor, Boundary, Part behavior unchanged  
- No validation changes to existing model elements  

**Pytest results (placeholder)**  
- `pytest tests/geometry/test_model_primitives.py -v` → 8 passed  
- `pytest tests/geometry -q` → 59 passed (baseline 51 + 8 new)
