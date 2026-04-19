# INT-001 Status Note — YAML solver pipeline

- Doc ID: OPS-12-INT-001
- Version: v0.1
- Status: Developer handover for audit
- Authoring role: Developer
- Decision owner: Director
- Physics review required: No
- Audit required before acceptance: Yes
- Last updated: 2026-04-18

## 1. Task identity

- Task ID: INT-001-yaml-solver-pipeline
- Phase ID: runtime-integration-p1

## 2. Files touched

- `src/ausolveris/geometry/pipeline.py`
- `tests/geometry/test_pipeline.py`
- `repo-docs-pack/docs/50-operations/12-int-001-status-v0.1.md`

## 3. Tests run

- `pytest tests/geometry/test_pipeline.py -q`
- `pytest tests/geometry -q`

## 4. Result

- Pass: yes
- Summary: bounded end-to-end composition from YAML input to solver-stub observables and YAML output added without modifying existing runtime modules

## 5. Exact pipeline functions implemented

- `run_solver_pipeline_from_yaml_string`
- `run_solver_pipeline_from_yaml_file`
- `solver_pipeline_observables_to_yaml_string`
- `solver_pipeline_observables_to_yaml_file`

## 6. Observable contract confirmation

INT-001 preserves the existing SOL-001 observable keys unchanged:

- `model_id`
- `model_name`
- `root_part_count`
- `total_part_count`
- `frame_count`
- `anchor_count`
- `boundary_count`
- `max_hierarchy_depth`

## 7. Known limitations

- Composition/orchestration only
- No new schema rules
- No new solver math
- No UI
- No optimization
- No meshing
- No physics semantics
- No mutation or normalization of input geometry

## 8. Scope confirmation

This INT-001 implementation remains within the approved bounded scope:
- composition of existing serializer, solver, and benchmark surfaces only
- one new pipeline test file only

No UI, optimization, meshing, or physics scope was added.

## 9. Related documents

This INT-001 handover should be read together with:

- `repo-docs-pack/docs/20-architecture/06-geometry-canonical-model-v0.1.md`
- `repo-docs-pack/docs/20-architecture/07-functional-vs-derived-geometry-v0.1.md`
- `repo-docs-pack/docs/20-architecture/08-geometry-open-questions-and-risks-v0.1.md`
- `repo-docs-pack/docs/30-spec/04-yaml-schema-concept-v0.1.md`
- `repo-docs-pack/docs/30-spec/05-part-hierarchy-anchors-frames-and-boundary-semantics-v0.1.md`
- `repo-docs-pack/docs/30-spec/06-solver-consumption-of-geometry-v0.1.md`
- `repo-docs-pack/docs/40-validation/04-geometry-benchmark-plan-v1.0.md`
- `repo-docs-pack/docs/50-operations/11-task-packet-int-001-yaml-solver-pipeline-v0.1.md`
