# OPT-001 Task Packet — observable score stub

* **Packet file**: `repo-docs-pack/docs/50-operations/15-task-packet-opt-001-observable-score-stub-v0.1.md`
* **Doc ID**: OPS-15-OPT-001
* **Version**: v0.1
* **Status**: Proposed execution authority
* **Authoring role**: Spec Lead
* **Decision owner**: Director
* **Physics review required**: No
* **Audit required before acceptance**: Yes
* **Last updated**: 2026-04-18

## 1. Task identity

* **Task ID**: OPT-001-observable-score-stub
* **Phase ID**: optimization-foundation-p1
* **Branch**: `opt-001-observable-score-stub`

## 2. Critical scope correction

The current merged geometry stack supports:

* canonical geometry model
* YAML serialization/deserialization
* structural solver stub
* YAML → solver pipeline
* deterministic solver observables

It does **not** yet support:

* approved parameter-edit contracts
* bounded candidate mutation semantics
* search-space definitions
* optimization algorithms
* benchmark-driven search loops

Therefore **OPT-001 must be a scoring foundation only**, not a search/optimization engine.

This task is intentionally limited to:

* scoring the existing SOL-001/INT-001 observable contract with a deterministic scalar score
* composing current YAML → pipeline → score flow
* adding one bounded test file
* adding one status/handover note

It does **not** perform search, tuning, mutation, or optimization loops.

## 3. Purpose

Provide the first optimization-facing foundation for the current runtime stack without opening search, physics, or UI scope.

The goal is to make current solver observables consumable by a bounded deterministic scoring layer.

## 4. Authority and input documents

This task is governed by:

* `repo-docs-pack/docs/20-architecture/06-geometry-canonical-model-v0.1.md`
* `repo-docs-pack/docs/20-architecture/07-functional-vs-derived-geometry-v0.1.md`
* `repo-docs-pack/docs/20-architecture/08-geometry-open-questions-and-risks-v0.1.md`
* `repo-docs-pack/docs/30-spec/04-yaml-schema-concept-v0.1.md`
* `repo-docs-pack/docs/30-spec/05-part-hierarchy-anchors-frames-and-boundary-semantics-v0.1.md`
* `repo-docs-pack/docs/30-spec/06-solver-consumption-of-geometry-v0.1.md`
* `repo-docs-pack/docs/40-validation/04-geometry-benchmark-plan-v1.0.md`
* `repo-docs-pack/docs/50-operations/09-task-packet-sol-001-geometry-solver-stub-v0.1.md`
* `repo-docs-pack/docs/50-operations/11-task-packet-int-001-yaml-solver-pipeline-v0.1.md`

Merged implementation baseline to read but not modify unless explicitly authorized later:

* `src/ausolveris/geometry/model.py`
* `src/ausolveris/geometry/schema.py`
* `src/ausolveris/geometry/serializer.py`
* `src/ausolveris/geometry/solver.py`
* `src/ausolveris/geometry/benchmark.py`
* `src/ausolveris/geometry/pipeline.py`
* current geometry test suite

## 5. Files in scope

Implementation scope is restricted to exactly these files:

* `src/ausolveris/geometry/optimizer.py`
* `tests/geometry/test_optimizer.py`
* `repo-docs-pack/docs/50-operations/16-opt-001-status-v0.1.md`

## 6. Files out of scope

The following are explicitly out of scope for OPT-001:

* any modification of `model.py`
* any modification of `schema.py`
* any modification of `serializer.py`
* any modification of `solver.py`
* any modification of `benchmark.py`
* any modification of `pipeline.py`
* any modification of existing tests
* any candidate mutation logic
* any search loop
* any optimization algorithm beyond deterministic scoring
* any UI or visualization work
* any acoustics, numerical solving, meshing, or physics implementation
* any external dependency addition

## 7. Required scoring surface

Provide one bounded scoring module:

### `src/ausolveris/geometry/optimizer.py`

Required public functions:

* `score_solver_observables(observables: dict) -> dict`
* `score_geometry_yaml_string(yaml_text: str) -> dict`
* `score_geometry_yaml_file(path: str | Path) -> dict`

These functions must be composition only. They must not duplicate serializer, solver, or pipeline logic.

## 8. Required observable contract

OPT-001 must consume exactly the existing SOL-001/INT-001 observable keys:

* `model_id`
* `model_name`
* `root_part_count`
* `total_part_count`
* `frame_count`
* `anchor_count`
* `boundary_count`
* `max_hierarchy_depth`

No additional observables are required or allowed in OPT-001.

## 9. Exact score contract

`score_solver_observables(observables)` must return a YAML-safe dict with exactly these keys:

* `model_id`
* `model_name`
* `score_name`
* `score_value`
* `components`

Where:

* `score_name` is fixed to: `structure_complexity_v1`
* `components` is a dict containing exactly:

  * `root_part_count`
  * `total_part_count`
  * `frame_count`
  * `anchor_count`
  * `boundary_count`
  * `max_hierarchy_depth`

### Exact score math

Define:

* `complexity_penalty = root_part_count + total_part_count + frame_count + anchor_count + boundary_count + max_hierarchy_depth`

Then:

* `score_value = -complexity_penalty`

This score is intentionally simple and structural only.

It must not be interpreted as a physical quality metric.

## 10. Exact pipeline composition

For `score_geometry_yaml_string(yaml_text)`:

1. call the existing YAML → solver pipeline
2. obtain the solver observables dict
3. call `score_solver_observables`
4. return the score dict

For `score_geometry_yaml_file(path)`:

1. call the existing YAML-file pipeline surface or equivalent existing composed surfaces
2. obtain the solver observables dict
3. call `score_solver_observables`
4. return the score dict

## 11. Required behavior and constraints

The scoring layer must:

* be deterministic for the same input
* preserve current serializer/schema validation behavior
* preserve current pipeline/solver behavior
* reject missing required observable keys cleanly
* reject non-numeric count values cleanly
* return YAML-safe primitive values only
* avoid mutation of the input observable dict or geometry model
* avoid any hidden normalization or geometry rewriting
* avoid any claim that the score is acoustically meaningful

## 12. Test requirements

Create one bounded test file:

* `tests/geometry/test_optimizer.py`

Target:

* **6 to 8 tests**

The test file must cover at least:

1. empty-model observables score to `0`
2. known non-empty observable set scores to the expected negative sum
3. missing required observable key is rejected
4. non-numeric observable count value is rejected
5. YAML string → pipeline → score works end-to-end
6. YAML file → pipeline → score works end-to-end
7. end-to-end score matches direct pipeline result plus direct scoring for the same model

Use the bounded test command:

`pytest tests/geometry -q`

Existing geometry tests must continue to pass.

## 13. Acceptance criteria

OPT-001 is acceptable only if all of the following are true:

* implementation remains confined to the exact files in scope
* no edits are made to existing core/runtime modules
* scoring remains deterministic and structural-only
* the observable contract remains exactly the current SOL-001/INT-001 contract
* the score math matches this packet exactly
* the new test file contains 6 to 8 tests
* `pytest tests/geometry -q` passes
* the status/handover note is present and complete

## 14. Escalation path

Escalate instead of inventing behavior if any of the following occurs:

* implementation appears to require candidate mutation/search logic
* additional observables seem necessary
* score semantics appear to require physics meaning
* any external dependency appears necessary
* any existing runtime module appears to need modification

If blocked, stop and report the minimum blocking question.

## 15. Developer handover expectation

The developer handover for OPT-001 must include:

* files touched
* tests run
* pass/fail result
* exact scoring functions implemented
* exact score contract and score name
* explicit confirmation that no search loop or mutation logic was added
* known limitations
* explicit confirmation that the score remains structural-only and not physics-meaningful

---

Spec Lead disposition:

* **OPT-001 is the next active execution authority**
* **UI-001 remains parked**
* no UI work should be activated unless Director explicitly un-parks it
