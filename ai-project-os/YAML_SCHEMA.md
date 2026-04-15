# YAML Schema

## Status

This document captures the conceptual structure of the future YAML project format. It is not yet final.

## Design goals

The YAML schema should be:

- human-readable,
- diff-friendly in git,
- explicit about units and assumptions,
- stable enough for versioned projects,
- modular enough to support future solver growth.

## Candidate top-level sections

- `project`
- `units`
- `geometry`
- `materials`
- `sources`
- `boundaries`
- `mesh`
- `study`
- `solver`
- `outputs`
- `postprocess`

## Candidate design rules

- Each project file must declare schema version.
- Units must never be left implicit where ambiguity is possible.
- Geometry references must be stable and reusable.
- Solver options must be separated from physical model definition.
- Output requests must be explicit rather than inferred.

## Candidate example skeleton

```yaml
project:
  name: example
  schema_version: 0.1

units:
  length: mm
  frequency: Hz

geometry:
  meshes: []

materials: {}

sources: {}

boundaries: {}

mesh: {}

study:
  frequencies: []

solver:
  kind: undefined

outputs:
  - kind: spl

postprocess: {}
```

## Open questions

- How much geometry can be described directly in YAML versus imported from mesh/CAD sources?
- How should hybrid LEM/BEM coupling be expressed without making v1 schema too heavy?
- Which fields are mandatory in the smallest valid project?
