# Architecture Exploration

## Status

Draft for review.

## Purpose

This document gives the whole-tree view of the project at a controlled level of detail. It is intended to keep the architecture visible while discovery is still in progress.

## Why this document exists

The project must not drift into deep design of one branch before the main tree is visible. This document therefore describes the top-level architecture and the first layer of meaningful sub-branches.

## System intent

The target system is an open-source, YAML-driven loudspeaker modeling platform designed for reproducible engineering studies. It should eventually support staged growth from reusable geometry and domain abstractions toward modeling workflows, validation, and broader execution paths.

## Top-level tree

### A. Product specification and project-definition branch

Purpose:
Own how a study is described, validated, normalized, and versioned.

Level-2 branches:
- YAML schema and versioning,
- project validation,
- project normalization,
- user-facing project examples.

Architectural importance:
Foundational. Nearly every other branch depends on it indirectly.

### B. Core domain branch

Purpose:
Own shared project concepts that should not be redefined independently in multiple branches.

Level-2 branches:
- units and conventions,
- identifiers and references,
- study definitions,
- metadata and result descriptors,
- public protocols and shared datatypes.

Architectural importance:
Highly foundational. This branch prevents structural drift and duplication.

### C. Geometry branch

Purpose:
Own reusable geometric descriptions and transformations that can be consumed by later modeling branches.

Level-2 branches:
- flare-law abstractions,
- profile and path representations,
- geometry sampling,
- geometry validation,
- geometry export.

Architectural importance:
Candidate first implementation branch. Strong v1 potential if kept solver-independent.

### D. Modeling branch

Purpose:
Own solver-oriented transformations and numerical pathways.

Level-2 branches:
- reduced-model pathway,
- boundary-model pathway,
- later hybrid pathway,
- study-specific discretization and assembly.

Architectural importance:
Important, but not necessarily first. This branch should consume stable domain and geometry abstractions rather than define them prematurely.

### E. Post-processing and observer branch

Purpose:
Own output interpretation, derived quantities, export transforms, and later observation or response representations.

Level-2 branches:
- raw result transforms,
- observer definitions,
- export structures,
- reporting-friendly artifacts.

Architectural importance:
Important but downstream. It should depend on stable outputs from other branches.

### F. Runtime and orchestration branch

Purpose:
Own execution flow, job metadata, caching, and later server-client or worker execution.

Level-2 branches:
- local execution,
- job lifecycle,
- logging,
- artifact management,
- future distributed execution.

Architectural importance:
Foundational for mature operation, but can remain lightweight in v1.

### G. Validation and benchmark branch

Purpose:
Own benchmark case definitions, reference artifacts, acceptance criteria, and trust-building workflow.

Level-2 branches:
- benchmark registry,
- reference data and tolerances,
- validation workflows,
- regression comparison.

Architectural importance:
Cross-cutting and critical. Without this branch, the project may run but still not be trustworthy.

### H. Interfaces branch

Purpose:
Own how users and tools interact with the system.

Level-2 branches:
- Python API,
- CLI,
- future service interface,
- example workflows.

Architectural importance:
Necessary, but should wrap the system rather than define its internals.

## First architectural reading

The tree is not balanced in the sense of equal size. It is intentionally dependency-shaped.

Foundational branches are B, A, G, and parts of C.

Downstream branches are D, E, and richer parts of F and H.

## Candidate v1 reading

A realistic v1 path is currently:
- A minimal A branch,
- a strong B branch,
- a narrow but reusable C branch,
- lightweight G support,
- lightweight H support,
- only minimal F.

This means the first useful capability may be geometry-centric rather than solver-centric.

## Key architecture concern

The geometry branch must not be shaped in a way that prevents later reduced-model, boundary-model, or observer branches from consuming it cleanly.

## Open questions

- Which geometry abstractions remain solver-independent enough to deserve first-class status?
- Which outputs should geometry provide so that later modeling branches can reuse them without hidden assumptions?
- How much of study definition belongs to the core domain versus geometry branch?
