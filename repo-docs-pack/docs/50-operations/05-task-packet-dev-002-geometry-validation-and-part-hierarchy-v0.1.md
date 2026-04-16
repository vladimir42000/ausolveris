# DEV-002 Task Packet — geometry validation and part hierarchy

- Doc ID: OPS-05-DEV-002
- Version: v0.1
- Status: Approved baseline task packet
- Authoring role: Spec Lead
- Decision owner: Director
- Physics review required: No
- Audit required before acceptance: Yes
- Last updated: 2026-04-16

## 1. Task identity

- Task ID: DEV-002-geometry-validation-and-part-hierarchy
- Phase ID: geometry-implementation-p2
- Deliverable: Expand the canonical geometry model with bounded hierarchy validation and minimal part-parent structure support, without solver coupling.

## 2. Objective

Implement the next bounded geometry-model increment after DEV-001.

This task exists to strengthen canonical geometry integrity around part hierarchy and structural validation while preserving the approved geometry-first posture and keeping the model solver-independent.

This task must remain strictly limited to:
- the existing geometry model module,
- bounded validation expansion,
- bounded part hierarchy representation,
- focused test expansion.

## 3. Authority and input documents

This task is governed by:

- `repo-docs-pack/docs/20-architecture/06-geometry-canonical-model-v0.1.md`
- `repo-docs-pack/docs/20-architecture/07-functional-vs-derived-geometry-v0.1.md`
- `repo-docs-pack/docs/20-architecture/08-geometry-open-questions-and-risks-v0.1.md`
- `repo-docs-pack/docs/30-spec/05-part-hierarchy-anchors-frames-and-boundary-semantics-v0.1.md`
- `repo-docs-pack/docs/30-spec/06-solver-consumption-of-geometry-v0.1.md`
- `repo-docs-pack/docs/50-operations/03-task-packet-dev-001-geometry-core-data-model-v0.1.md`
- `repo-docs-pack/docs/50-operations/04-dev-001-status-v0.1.md`

## 4. Files in scope

Implementation scope is restricted to:

- `src/ausolveris/geometry/model.py`
- `tests/geometry/test_model_validation.py`
- `tests/geometry/test_model_yaml_roundtrip.py`
- `repo-docs-pack/docs/50-operations/07-dev-002-status-v0.1.md`

## 5. Files out of scope

The following are explicitly out of scope for DEV-002:

- any solver module
- any meshing module
- any physics or boundary-condition implementation
- any runtime adapter or API layer
- any CLI or application entrypoint
- any UI or visualization code
- any repository restructuring
- any schema-definition file or schema compiler
- any new geometry modules beyond the existing bounded model module
- any expansion of boundary vocabulary beyond structural identity

## 6. Required input contract

The implementation must preserve the approved geometry posture:

- canonical geometry remains solver-independent
- functional geometry remains distinct from derived geometry
- no solver assumptions may be embedded in the canonical model
- no meshing concepts may be introduced
- no physics semantics may be introduced
- unresolved scope must remain explicitly unresolved rather than invented locally

The model may be expanded only far enough to represent and validate:
- explicit top-level part collection
- explicit child-part nesting
- parent/child structural consistency rules
- canonical containment integrity across part hierarchy traversal

## 7. Required output contract

The deliverable must provide:

- bounded expansion of the existing canonical geometry model module
- explicit part hierarchy support adequate to express parent-child containment cleanly
- stronger structural validation for hierarchy integrity
- YAML-safe dictionary serialization/deserialization that preserves hierarchy structure
- tests covering hierarchy validation and roundtrip behavior
- a DEV-002 developer handover/status note

The implementation must not require solver code, mesh code, runtime code, or physics code.

## 8. Required bounded design direction

DEV-002 is not a primitive-set expansion task.

Allowed direction:
- strengthen and clarify how `Part` hierarchy is represented and validated inside the existing model surface
- add bounded structural fields only if needed for parent-child integrity and only inside the existing module

Not allowed:
- inventing new geometry families
- inventing solver-facing fields
- inventing mesh-facing fields
- inventing semantic boundary typing
- introducing materials, ports, regions, observables, or compiled geometry artifacts

If a new field appears necessary, it must be justified as hierarchy-only and remain solver-independent.

## 9. Validation rules required in this task

Validation in DEV-002 remains structural only.

Existing DEV-001 checks must continue to hold.

New required checks:
- child parts must have non-empty ids and names through all hierarchy levels
- duplicate part ids anywhere in the traversed hierarchy must be rejected
- duplicate anchor ids within the same part must be rejected by dictionary identity rules
- duplicate boundary ids within the same part must be rejected by dictionary identity rules
- if parent reference support is introduced, parent-child references must be consistent and acyclic
- hierarchy traversal used for validation must be deterministic and cover all descendants
- YAML load must reject hierarchy structures that violate the above structural rules

Not allowed in DEV-002:
- physical interpretation validation
- solver compatibility validation
- mesh-generation validation
- derived-geometry validation

## 10. Test requirements

The test suite must include:
- hierarchy validation tests for multi-level nested parts
- rejection tests for duplicate part ids across a hierarchy tree
- cycle-rejection tests if parent reference support is introduced
- YAML roundtrip tests preserving nested hierarchy integrity
- regression coverage showing DEV-001 behavior still passes
- a bounded pytest command that continues to pass without external runtime dependencies

The bounded test command is:

```bash
pytest tests/geometry -q
```

## 11. Acceptance criteria

DEV-002 is acceptable only if all of the following are true:

- implementation remains confined to the stated files in scope
- the geometry model remains solver-independent
- hierarchy validation is strengthened in a bounded way
- no out-of-scope concepts are introduced
- YAML roundtrip still passes for nested hierarchy structures
- `pytest tests/geometry -q` passes
- a DEV-002 status/handover note exists and accurately describes the work

## 12. Escalation path

Escalate to Spec Lead instead of inventing behavior if any of the following occurs:

- hierarchy validation appears to require new geometry semantics beyond structural containment
- the task appears to require explicit boundary vocabulary beyond identity
- the task appears to require solver-facing references or compiled artifacts
- the task appears to require additional modules or repository restructuring
- the task appears to require schema-definition work better handled under SCH-001

If blocked, stop and report the minimum blocking question.

## 13. Developer handover expectation

The developer handover for DEV-002 must include:

- files touched
- tests run
- pass/fail result
- any remaining known limitations
- confirmation that no solver, meshing, or physics scope was added
- confirmation that boundary vocabulary remains deferred
