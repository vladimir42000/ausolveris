# INT-001 Task Packet — YAML → solver pipeline

- Doc ID: OPS-11-INT-001
- Version: v0.1
- Status: Proposed execution authority
- Authoring role: Spec Lead
- Decision owner: Director
- Physics review required: No
- Audit required before acceptance: Yes
- Last updated: 2026-04-18

## 1. Task identity

- Task ID: INT-001-yaml-solver-pipeline
- Phase ID: runtime-integration-p1
- Branch: `int-001-yaml-solver-pipeline`
- Deliverable: bounded end-to-end pipeline from YAML text/file to solver-stub observables and YAML-safe observable output

## 2. Purpose

Implement the first integration path that composes already-merged components:

- YAML deserialization,
- canonical geometry reconstruction,
- solver-stub execution,
- benchmark-observable export.

This task is intentionally limited to orchestration of existing surfaces plus one bounded test file and one status/handover note.

This task does **not** implement:
- new geometry semantics,
- new schema rules,
- new solver math,
- UI,
- optimization,
- external integrations.

## 3. Authority and input documents

This task is governed by:

- `repo-docs-pack/docs/20-architecture/06-geometry-canonical-model-v0.1.md`
- `repo-docs-pack/docs/20-architecture/07-functional-vs-derived-geometry-v0.1.md`
- `repo-docs-pack/docs/20-architecture/08-geometry-open-questions-and-risks-v0.1.md`
- `repo-docs-pack/docs/30-spec/04-yaml-schema-concept-v0.1.md`
- `repo-docs-pack/docs/30-spec/05-part-hierarchy-anchors-frames-and-boundary-semantics-v0.1.md`
- `repo-docs-pack/docs/30-spec/06-solver-consumption-of-geometry-v0.1.md`
- `repo-docs-pack/docs/40-validation/04-geometry-benchmark-plan-v1.0.md`
- `repo-docs-pack/docs/50-operations/09-task-packet-sol-001-geometry-solver-stub-v0.1.md`

Merged implementation baseline to read but not modify unless explicitly authorized later:
- `src/ausolveris/geometry/model.py`
- `src/ausolveris/geometry/schema.py`
- `src/ausolveris/geometry/serializer.py`
- `src/ausolveris/geometry/solver.py`
- `src/ausolveris/geometry/benchmark.py`
- `tests/geometry/test_model_validation.py`
- `tests/geometry/test_model_yaml_roundtrip.py`
- `tests/geometry/test_geometry_schema.py`
- `tests/geometry/test_solver_stub.py`

## 4. Files in scope

Implementation scope is restricted to exactly these files:

- `src/ausolveris/geometry/pipeline.py`
- `tests/geometry/test_pipeline.py`
- `repo-docs-pack/docs/50-operations/12-int-001-status-v0.1.md`

## 5. Files out of scope

The following are explicitly out of scope for INT-001:

- any modification of `model.py`
- any modification of `schema.py`
- any modification of `serializer.py`
- any modification of `solver.py`
- any modification of `benchmark.py`
- any modification of existing tests
- any UI or visualizer work
- any optimization or search logic
- any acoustics, numerical solving, meshing, or physics implementation
- any external dependency addition
- any benchmark framework expansion beyond bounded pipeline composition

## 6. Required pipeline surface

Provide one bounded integration module:

### `src/ausolveris/geometry/pipeline.py`

Required public functions:

- `run_solver_pipeline_from_yaml_string(yaml_text: str) -> dict`
- `run_solver_pipeline_from_yaml_file(path: str | Path) -> dict`
- `solver_pipeline_observables_to_yaml_string(yaml_text: str) -> str`
- `solver_pipeline_observables_to_yaml_file(yaml_text: str, path: str | Path) -> None`

Required composition rules:

1. deserialize geometry YAML using the existing serializer layer
2. run the existing solver stub on the resulting `GeometryModel`
3. return the solver observables unchanged
4. for YAML-output helpers, export the observables using the existing benchmark helper

These functions must be orchestration only. They must not duplicate schema, serializer, solver, or benchmark logic.

## 7. Exact pipeline steps

For `run_solver_pipeline_from_yaml_string(yaml_text)`:

1. call existing YAML-string-to-model deserializer
2. obtain a `GeometryModel`
3. call existing solver stub
4. return the observables dict

For `run_solver_pipeline_from_yaml_file(path)`:

1. call existing YAML-file-to-model deserializer
2. obtain a `GeometryModel`
3. call existing solver stub
4. return the observables dict

For `solver_pipeline_observables_to_yaml_string(yaml_text)`:

1. run YAML-string pipeline
2. export resulting observables with existing benchmark YAML string helper
3. return YAML text

For `solver_pipeline_observables_to_yaml_file(yaml_text, path)`:

1. run YAML-string pipeline
2. export resulting observables with existing benchmark YAML file helper

## 8. Required observables contract

INT-001 must not invent a new observable contract.

It must preserve exactly the observable keys already produced by SOL-001:

- `model_id`
- `model_name`
- `root_part_count`
- `total_part_count`
- `frame_count`
- `anchor_count`
- `boundary_count`
- `max_hierarchy_depth`

## 9. Required behavior and constraints

The pipeline must:

- be deterministic for the same YAML input
- preserve current validation behavior from the serializer/schema layer
- preserve current stub behavior from the solver layer
- raise underlying validation or YAML parse errors rather than silently masking them
- avoid mutation of the input YAML text or resulting model
- avoid any hidden normalization or geometry rewriting
- return YAML-safe primitive observable values only

## 10. Test requirements

Create one bounded test file:

- `tests/geometry/test_pipeline.py`

Target:
- **8 to 10 tests**

The test file must cover at least:

1. valid minimal YAML string → observables dict
2. valid nested hierarchy YAML string → correct observable counts
3. YAML file → observables dict
4. pipeline YAML-string export produces valid YAML with expected keys
5. pipeline YAML-file export writes valid YAML
6. malformed YAML string is rejected
7. valid YAML with invalid root shape is rejected
8. schema-invalid YAML is rejected through the pipeline
9. end-to-end result matches direct serializer + solver composition for the same model

Use the bounded test command:

    pytest tests/geometry -q

Existing geometry tests must continue to pass.

## 11. Acceptance criteria

INT-001 is acceptable only if all of the following are true:

- implementation remains confined to the exact files in scope
- no edits are made to existing model/schema/serializer/solver/benchmark modules
- the pipeline uses composition of existing merged surfaces only
- the observable set remains exactly the SOL-001 observable keys
- YAML output uses safe dumping through the benchmark helper
- the new test file contains 8 to 10 tests
- `pytest tests/geometry -q` passes
- the status/handover note is present and complete

## 12. Escalation path

Escalate instead of inventing behavior if any of the following occurs:

- implementation appears to require modifying existing merged runtime modules
- additional observables seem necessary
- pipeline behavior appears to require new schema or validation rules
- any external dependency appears necessary
- UI, optimization, or physics scope starts to appear necessary

If blocked, stop and report the minimum blocking question.

## 13. Developer handover expectation

The developer handover for INT-001 must include:

- files touched
- tests run
- pass/fail result
- exact pipeline functions implemented
- confirmation that observable keys were preserved unchanged
- known limitations
- explicit confirmation that no UI, optimization, meshing, or physics scope was added
