# SOL-001 Task Packet — geometry solver stub

- Doc ID: OPS-09-SOL-001
- Version: v0.1
- Status: Proposed execution authority
- Authoring role: Spec Lead
- Decision owner: Director
- Physics review required: No
- Audit required before acceptance: Yes
- Last updated: 2026-04-18

## 1. Task identity

- Task ID: SOL-001-geometry-solver-stub
- Phase ID: runtime-implementation-p1
- Branch: `sol-001-geometry-solver-stub`
- Deliverable: first bounded runtime path from canonical geometry model to solver-stub observables and benchmark-observable YAML output

## 2. Purpose

Implement the first runtime execution path for geometry without opening full acoustics, optimization, or UI scope.

This task is intentionally limited to:
- loading an already-validated `GeometryModel`,
- computing a deterministic, structural solver-stub observable set,
- exporting those observables in a benchmark-friendly YAML form,
- adding one bounded test file,
- adding one status/handover note.

This task does **not** implement acoustics, numerical solving, optimization, or mesh/physics behavior.

## 3. Authority and input documents

This task is governed by:

- `repo-docs-pack/docs/20-architecture/06-geometry-canonical-model-v0.1.md`
- `repo-docs-pack/docs/20-architecture/07-functional-vs-derived-geometry-v0.1.md`
- `repo-docs-pack/docs/20-architecture/08-geometry-open-questions-and-risks-v0.1.md`
- `repo-docs-pack/docs/30-spec/04-yaml-schema-concept-v0.1.md`
- `repo-docs-pack/docs/30-spec/05-part-hierarchy-anchors-frames-and-boundary-semantics-v0.1.md`
- `repo-docs-pack/docs/30-spec/06-solver-consumption-of-geometry-v0.1.md`
- `repo-docs-pack/docs/40-validation/04-geometry-benchmark-plan-v1.0.md`

Current implementation baseline to read but not modify unless explicitly allowed later:
- `src/ausolveris/geometry/model.py`
- `src/ausolveris/geometry/schema.py`
- `src/ausolveris/geometry/serializer.py`
- `tests/geometry/test_model_validation.py`
- `tests/geometry/test_model_yaml_roundtrip.py`
- `tests/geometry/test_geometry_schema.py`

## 4. Files in scope

Implementation scope is restricted to exactly these files:

- `src/ausolveris/geometry/solver.py`
- `src/ausolveris/geometry/benchmark.py`
- `tests/geometry/test_solver_stub.py`
- `repo-docs-pack/docs/50-operations/10-sol-001-status-v0.1.md`

## 5. Files out of scope

The following are explicitly out of scope for SOL-001:

- any UI or visualizer work
- any optimizer or search logic
- any full acoustic or numerical solver implementation
- any mesh or derived-geometry execution path
- any modification of canonical geometry model semantics
- any modification of `model.py`, `schema.py`, or `serializer.py`
- any benchmark execution framework beyond bounded observable export
- any new dependency unless explicitly approved later

## 6. Required runtime surface

SOL-001 must provide a minimal runtime surface for the current geometry model only.

### 6.1 `src/ausolveris/geometry/solver.py`

Provide a bounded solver-stub function and helpers that operate on `GeometryModel`.

Required public function:

- `run_geometry_solver_stub(model: GeometryModel) -> dict`

The returned dictionary must be YAML-safe and deterministic.

### 6.2 `src/ausolveris/geometry/benchmark.py`

Provide bounded benchmark-observable export helpers.

Required public functions:

- `solver_observables_to_yaml_string(observables: dict) -> str`
- `solver_observables_to_yaml_file(observables: dict, path: str | Path) -> None`

## 7. Required observables list

The solver stub must compute exactly these observables:

- `model_id`
- `model_name`
- `root_part_count`
- `total_part_count`
- `frame_count`
- `anchor_count`
- `boundary_count`
- `max_hierarchy_depth`

Definitions:

- `model_id`: `GeometryModel.id`
- `model_name`: `GeometryModel.name`
- `root_part_count`: number of top-level parts in `GeometryModel.parts`
- `total_part_count`: total number of parts reachable by traversing all descendants from top-level parts
- `frame_count`: number of frames in `GeometryModel.frames`
- `anchor_count`: total number of anchors across all traversed parts
- `boundary_count`: total number of boundaries across all traversed parts
- `max_hierarchy_depth`: maximum nesting depth of the traversed part hierarchy, with a top-level part counted as depth `1`

No other observables are required in SOL-001.

## 8. Required stub math

SOL-001 must remain structural and arithmetic only.

Required computation rules:

- `root_part_count = len(model.parts)`
- `frame_count = len(model.frames)`
- `total_part_count = count of unique traversed parts`
- `anchor_count = sum(len(part.anchors) for each traversed part)`
- `boundary_count = sum(len(part.boundaries) for each traversed part)`
- `max_hierarchy_depth = max depth reached during traversal, with root depth = 1; if there are no parts, depth = 0`

Traversal must preserve the current merged structural validation posture:
- operate on the existing valid model surface,
- do not reinterpret geometry semantics,
- do not infer physics,
- do not open solver-node or mesh concepts.

## 9. Required behavior and constraints

The stub must:

- accept only `GeometryModel` input
- be deterministic for the same model input
- return YAML-safe primitive values only
- avoid any solver-physics vocabulary beyond the bounded word “solver stub”
- avoid mutation of the input model
- avoid any hidden normalization or geometry rewriting

The benchmark export helpers must:

- use `yaml.safe_dump`
- preserve observable keys and values
- write UTF-8 text files when exporting to disk

## 10. Test requirements

Create one bounded test file:

- `tests/geometry/test_solver_stub.py`

Target:
- **6 to 8 tests**

The test file must cover at least:

1. empty geometry model produces zero-count observables and depth `0`
2. single-part model produces correct counts and depth `1`
3. nested hierarchy produces correct `total_part_count` and `max_hierarchy_depth`
4. anchor and boundary counts are correct across multiple parts
5. solver stub output is YAML-safe and serializable through the benchmark helper
6. file-based benchmark YAML export works
7. non-`GeometryModel` input is rejected cleanly

Use the bounded test command:

```bash
pytest tests/geometry -q
```

Existing geometry tests must continue to pass.

## 11. Acceptance criteria

SOL-001 is acceptable only if all of the following are true:

- implementation remains confined to the exact files in scope
- no changes are made to the canonical geometry model surface
- no acoustics, optimization, UI, meshing, or physics scope is added
- the observable set matches the required list exactly
- the stub math matches the definitions in this packet
- benchmark export uses safe YAML dumping
- the new test file contains 6 to 8 tests
- `pytest tests/geometry -q` passes
- the status/handover note is present and complete

## 12. Escalation path

Escalate instead of inventing behavior if any of the following occurs:

- implementation appears to require editing `model.py`, `schema.py`, or `serializer.py`
- additional observables seem necessary beyond the required list
- physics or numerical-solver semantics appear necessary
- benchmark output appears to require a formal schema beyond bounded YAML-safe export
- a new dependency appears necessary

If blocked, stop and report the minimum blocking question.

## 13. Developer handover expectation

The developer handover for SOL-001 must include:

- files touched
- tests run
- pass/fail result
- exact observable keys implemented
- known limitations
- explicit confirmation that no UI, optimization, meshing, or physics scope was added
