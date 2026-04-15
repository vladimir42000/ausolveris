# Architecture

## Status

This document is an initial architecture scaffold. It records the intended structure of the project before the v1 technical scope is frozen.

## Architectural intent

The target system is an open-source, YAML-driven loudspeaker modeling platform with a server-client operating model and staged numerical backends.

The architecture should support:

- human-readable project definitions,
- task-oriented solver execution,
- reproducible results,
- strong traceability from physics assumptions to code,
- modular solver backends,
- later support for local and remote execution.

## Early component model

### Project specification layer

Responsible for reading, validating, and normalizing YAML project definitions.

### Core domain layer

Responsible for shared concepts such as geometry references, materials, sources, units, coordinate systems, and frequency sweep definitions.

### Mesh and geometry layer

Responsible for importing, tagging, and exposing geometry and mesh data to solver modules.

### Solver layer

Responsible for numerical execution. Intended to remain modular so different formulations can coexist.

Potential future subdomains:

- reduced or lumped enclosure models,
- 3D boundary element radiation models,
- hybrid couplings.

### Runtime layer

Responsible for job execution, logging, caching, and resource management.

### Post-processing layer

Responsible for derived outputs such as SPL, directivity, transfer functions, pressure maps, and export formats.

### Interface layer

Responsible for CLI, API, and later server-client orchestration.

## Immediate architecture constraints

- No monolithic all-in-one solver design at the start.
- No irreversible commitment to a single numerical backend before benchmarks justify it.
- No undocumented physics shortcuts.
- All major architectural changes require ADR coverage.

## Open architecture questions

- What exact v1 problem family will define the first stable solver pathway?
- What YAML top-level entities are mandatory in v1?
- Which parts run in-process first, and which are postponed to later server-client separation?
