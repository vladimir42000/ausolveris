# SCH-001 Task Packet — geometry YAML schema v1

- Doc ID: OPS-06-SCH-001
- Version: v0.1
- Status: Superseding code-track execution authority
- Authoring role: Spec Lead
- Decision owner: Director
- Physics review required: No
- Audit required before acceptance: Yes
- Last updated: 2026-04-16

## 1. Task identity

- Task ID: SCH-001-geometry-yaml-schema-v1
- Phase ID: schema-implementation-p1
- Branch: `sch-001-yaml-schema`
- Deliverable: bounded YAML schema + serializer/deserializer implementation for the current canonical geometry model

## 2. Purpose

Implement the first bounded runtime schema layer for geometry YAML so the current canonical geometry model can be serialized, deserialized, and structurally rejected in a disciplined way.

This task is a code track.

It is intentionally limited to:
- schema structure for the existing geometry model surface,
- serializer/deserializer helpers,
- bounded geometry YAML tests,
- one status/handover note.

It must not broaden into solver, UI, meshing, or physics work.

## 3. Authority and input documents

This task is governed by:

- `repo-docs-pack/docs/20-architecture/06-geometry-canonical-model-v0.1.md`
- `repo-docs-pack/docs/20-architecture/07-functional-vs-derived-geometry-v0.1.md`
- `repo-docs-pack/docs/20-architecture/08-geometry-open-questions-and-risks-v0.1.md`
- `repo-docs-pack/docs/30-spec/04-yaml-schema-concept-v0.1.md`
- `repo-docs-pack/docs/30-spec/05-part-hierarchy-anchors-frames-and-boundary-semantics-v0.1.md`
- `repo-docs-pack/docs/30-spec/06-solver-consumption-of-geometry-v0.1.md`

Current implementation baseline to read but not modify in this task:

- `src/ausolveris/geometry/model.py`
- `tests/geometry/test_model_validation.py`
- `tests/geometry/test_model_yaml_roundtrip.py`

## 4. Files in scope

Implementation scope is restricted to exactly these files:

- `src/ausolveris/geometry/schema.py`
- `src/ausolveris/geometry/serializer.py`
- `tests/geometry/test_geometry_schema.py`
- `repo-docs-pack/docs/50-operations/08-sch-001-status-v0.1.md`

## 5. Files out of scope

The following are explicitly out of scope for SCH-001:

- any solver module
- any meshing or derived-geometry implementation
- any physics or boundary-condition implementation
- any UI/runtime application layer outside the bounded geometry serializer helpers
- any repository restructuring
- modification of `src/ausolveris/geometry/model.py`
- modification of existing DEV-001 / DEV-002 tests except by explicit later follow-up
- benchmark planning documents
- schema-engine integration beyond the bounded local implementation in this task
- any new dependency unless explicitly approved later

## 6. Required implementation scope

SCH-001 must provide a bounded implementation for the current geometry model only.

The implementation must cover:

1. A schema helper layer in `src/ausolveris/geometry/schema.py`
   - validates YAML-safe dictionaries for the current geometry model shape
   - checks required top-level structure
   - checks required and optional keys for current entities
   - checks mapping/object-id consistency where relevant
   - remains structural only

2. A serializer/deserializer layer in `src/ausolveris/geometry/serializer.py`
   - uses `yaml.safe_dump`
   - uses `yaml.safe_load`
   - serializes `GeometryModel` to YAML text
   - deserializes YAML text to `GeometryModel`
   - supports file read/write helpers
   - routes loaded dictionaries through schema validation before constructing model objects

3. A bounded SCH-001 test file
   - `tests/geometry/test_geometry_schema.py`

4. A SCH-001 status/handover note
   - `repo-docs-pack/docs/50-operations/08-sch-001-status-v0.1.md`

## 7. Required schema posture

The schema must align with the currently merged geometry surface and must not invent new runtime semantics.

The schema may represent only the currently merged model concepts:

- geometry model
- part
- anchor
- frame
- boundary
- metadata
- child-part hierarchy

The schema must not introduce:
- solver vocabulary
- physics vocabulary
- derived-geometry vocabulary
- meshing vocabulary
- boundary-condition semantics
- new primitive families beyond the current model

The current merged `Boundary` shape is structural identity only. SCH-001 must preserve that posture.

## 8. Required serializer behavior

The serializer/deserializer must support at least:

- geometry model to YAML string
- YAML string to geometry model
- geometry model to YAML file
- YAML file to geometry model

The implementation must remain compatible with the existing `GeometryModel.to_dict()` / `GeometryModel.from_dict()` model surface and with the current DEV-001 / DEV-002 structural validation posture.

## 9. Validation rules required in this task

Validation in SCH-001 is structural only.

Required checks include, at minimum:

- YAML root must be a mapping/object
- top-level keys must match the expected geometry document structure
- required entity keys must be present where required
- mapping/object-id consistency for:
  - parts
  - frames
  - anchors
  - boundaries
- current hierarchy structures must pass through the existing merged geometry validation rules
- invalid structure must be rejected before a model object is returned

Not allowed in SCH-001:

- solver compatibility validation
- meshing validation
- physics validation
- benchmark interpretation
- UI/runtime orchestration beyond bounded serializer helpers

## 10. Test requirements

Create one bounded test file:

- `tests/geometry/test_geometry_schema.py`

Target:
- 8 to 12 tests

The test file must cover at least:

1. valid minimal YAML to model
2. valid nested hierarchy YAML to model
3. model to YAML to model roundtrip
4. file-based roundtrip
5. rejection of invalid root shape
6. rejection of missing required keys
7. rejection of mapping/object-id mismatch
8. rejection of invalid hierarchy input through schema/load path

Use the bounded test command:

```bash
pytest tests/geometry -q
```

Existing geometry tests must continue to pass.

## 11. Acceptance criteria

SCH-001 is acceptable only if all of the following are true:

- implementation remains confined to the exact files in scope
- no solver, UI, meshing, or physics scope is added
- serializer/deserializer uses safe YAML load/dump functions
- schema validation is structural and bounded
- current geometry model can be round-tripped through YAML
- invalid YAML structure is rejected cleanly
- `pytest tests/geometry -q` passes
- new test file contains 8 to 12 tests
- status/handover note is present and complete

## 12. Escalation path

Escalate instead of inventing behavior if any of the following occurs:

- the task appears to require modification of `model.py`
- the task appears to require new model primitives
- the task appears to require solver-specific schema fields
- the task appears to require boundary semantics beyond the current structural identity posture
- the task appears to require new dependencies
- the task appears to require benchmark/physics interpretation

If blocked, stop and report the minimum blocking question.

## 13. Developer handover expectation

The developer handover for SCH-001 must include:

- files touched
- tests run
- pass/fail result
- count of new schema tests added
- known limitations
- explicit confirmation that no solver, meshing, UI, or physics scope was added
