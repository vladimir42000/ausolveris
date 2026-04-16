# DEV-001 Task Packet — geometry core data model

- Doc ID: OPS-03-DEV-001
- Version: v0.1
- Status: Approved baseline task packet
- Authoring role: Spec Lead
- Decision owner: Director
- Physics review required: No
- Audit required before acceptance: Yes
- Last updated: 2026-04-16

## 1. Task identity

- Task ID: DEV-001-geometry-core-data-model
- Phase ID: geometry-implementation-p1
- Deliverable: Implement canonical geometry data model from approved geometry docs

## 2. Objective

Implement the first bounded canonical geometry data model as a small, solver-independent code unit.

This task exists to establish a minimal in-repo geometry representation aligned with the approved geometry concept package.

This task must remain strictly limited to:
- one folder,
- one primary module,
- basic structural validation,
- YAML-safe roundtrip support.

## 3. Authority and input documents

This task is governed by:

- `repo-docs-pack/docs/20-architecture/06-geometry-canonical-model-v0.1.md`
- `repo-docs-pack/docs/20-architecture/07-functional-vs-derived-geometry-v0.1.md`
- `repo-docs-pack/docs/20-architecture/08-geometry-open-questions-and-risks-v0.1.md`
- `repo-docs-pack/docs/30-spec/05-part-hierarchy-anchors-frames-and-boundary-semantics-v0.1.md`
- `repo-docs-pack/docs/30-spec/06-solver-consumption-of-geometry-v0.1.md`

## 4. Files in scope

Implementation scope is restricted to:

- `src/ausolveris/geometry/model.py`
- `tests/geometry/test_model_validation.py`
- `tests/geometry/test_model_yaml_roundtrip.py`

## 5. Files out of scope

The following are explicitly out of scope for DEV-001:

- any solver module
- any meshing module
- any physics or boundary-condition implementation
- any CLI or application entrypoint
- any repository restructuring
- any YAML schema formalization beyond this local roundtrip need
- any additional geometry modules beyond the bounded model module
- any documentation edits other than this task packet if missing

## 6. Required input contract

The implementation must reflect the approved geometry posture:

- canonical geometry is solver-independent
- functional geometry is distinct from derived geometry
- no solver assumptions may be embedded in the canonical model
- no meshing concepts may be introduced
- no physics semantics may be introduced
- unresolved scope must remain unresolved rather than invented locally

The model may include only the minimum structures needed to represent:
- geometry model container
- part hierarchy
- anchors
- frames
- boundaries

## 7. Required output contract

The deliverable must provide:

- a canonical geometry model module in Python
- a minimal serializable object model for:
  - geometry model
  - part
  - anchor
  - frame
  - boundary
- conversion to YAML-safe dictionary structures
- reconstruction from YAML-safe dictionary structures
- basic structural validation

The implementation must not require solver code, mesh code, or physics code.

## 8. Validation rules required in this task

Validation in DEV-001 is structural only.

Required checks:
- non-empty required ids
- non-empty required part names
- valid frame origin dimensionality
- valid frame orientation dimensionality
- part/frame mapping keys must match contained object ids
- anchor/boundary mapping keys inside parts must match contained object ids
- anchor frame references must resolve to existing frames when specified
- duplicate ids across top-level part/frame namespaces must be rejected

Not allowed in DEV-001:
- physical interpretation validation
- solver compatibility validation
- mesh-generation validation
- derived-geometry validation

## 9. Test requirements

The test suite must include:
- basic object validation tests
- nested part hierarchy test coverage
- key/id mismatch validation tests
- missing referenced frame validation tests
- YAML roundtrip tests using in-memory serialization
- YAML roundtrip tests using file serialization
- validation-on-load tests for invalid dictionaries

The bounded test command is:

```bash
pytest tests/geometry -q
```

## 10. Acceptance criteria

DEV-001 is acceptable only if all of the following are true:

- implementation remains confined to the stated files in scope
- no out-of-scope concepts are introduced
- the model remains solver-independent
- structural validation is present
- YAML roundtrip passes
- `pytest tests/geometry -q` passes
- the resulting code is suitable for Auditor review as the first bounded code deliverable

## 11. Escalation path

Escalate to Spec Lead instead of inventing behavior if any of the following occurs:

- the task appears to require new primitives beyond the approved bounded set
- the task appears to require solver-specific fields
- the task appears to require meshing or derived geometry structures
- the task appears to require physical boundary semantics beyond structural labeling
- the task appears to require additional modules or repository restructuring

If blocked, stop and report the minimum blocking question.

## 12. Developer handover expectation

The developer handover for DEV-001 must include:

- files touched
- tests run
- pass/fail result
- any remaining known limitations
- confirmation that no solver, meshing, or physics scope was added
