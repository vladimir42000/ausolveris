# Foundations and Dependencies

## Status

Draft for review.

## Purpose

This document explains which branches are foundational, which branches depend on them, and where early stabilization effort should be spent.

## Dependency logic

### Product specification depends on core domain

Project files cannot be normalized coherently if units, identifiers, references, and common public data concepts are undefined.

### Geometry depends on core domain

Reusable geometry needs stable units, coordinate meaning, and shared datatypes.

### Modeling depends on core domain and geometry

Future solver paths should consume domain and geometry components instead of re-implementing them.

### Post-processing depends on modeling and domain

Derived outputs need stable metadata and output descriptors.

### Runtime depends on project specification and interfaces

Execution needs normalized inputs and predictable artifact types.

### Validation depends on almost everything
n
Validation is cross-cutting. It needs benchmark definitions, reference artifacts, stable inputs, and inspectable outputs.

## Foundational set

The minimum foundational set appears to be:

- core domain,
- product specification,
- numerical conventions,
- benchmark scaffolding,
- reusable geometry contracts.

## Branches that should stay light early

- distributed runtime,
- full service API,
- advanced post-processing,
- multi-path solver architecture,
- hybrid coupling.

## Architectural warning points

- if geometry starts embedding solver assumptions, later reuse will weaken,
- if the core domain becomes too abstract too early, development speed will drop,
- if validation is delayed, the project may accumulate elegant but untrusted code.

## Current dependency judgment

A geometry-first v1 is acceptable only if the geometry branch is treated as a dependent of the core domain and a future provider to modeling and post-processing, not as an isolated mini-project.
