# System Map

## Purpose

This document explains how the software is divided into major subsystems, what each subsystem is responsible for, and how they fit together.

## Why this document exists

The project cannot rely on one AI or one human carrying the entire codebase in memory. The system must therefore be understandable as a map of stable areas and responsibilities.

## Top-level subsystem map

### 1. Project specification layer

Owns loading, validating, normalizing, and versioning YAML project definitions.

### 2. Core domain layer

Owns project-wide concepts used by many parts of the software:

- units,
- coordinates,
- geometry references,
- source definitions,
- frequency studies,
- materials,
- result metadata.

### 3. Analytic geometry and flare layer

Owns analytic horn and waveguide descriptions that are reusable across builders and solvers.

Examples:

- flare-law abstractions,
- profile samplers,
- geometric helper functions,
- section-generation logic.

### 4. LEM layer

Owns lumped or reduced acoustic model constructions derived from project geometry and study definitions.

### 5. BEM layer

Owns 3D boundary-element-oriented geometry preparation, boundary definitions, and acoustic radiation or scattering workflows.

### 6. Hybrid coupling layer

Owns bridges between reduced models and boundary models when the project grows into coupled workflows.

### 7. Runtime and job layer

Owns execution plans, job lifecycle, logs, caches, and local or remote worker orchestration.

### 8. Post-processing layer

Owns conversion of raw solver outputs into user-facing results, exports, and visualizable artifacts.

### 9. Interfaces layer

Owns user-facing execution surfaces:

- Python API,
- CLI,
- local service interface,
- later remote or client-server control.

## Design rule

Every new feature proposal must identify which subsystem owns it. If ownership is unclear, the task is not ready for implementation.

## Early sequence of growth

The expected growth path is:

1. Project specification and core domain,
2. analytic geometry and flare layer,
3. first solver path,
4. post-processing,
5. stronger runtime separation,
6. hybrid and advanced workflows.

## Architectural decision trigger

If a proposed change crosses subsystem boundaries or changes which subsystem owns a responsibility, it requires architecture review and possibly an ADR.
