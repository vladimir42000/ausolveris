# Module Ownership

## Purpose

This document defines which code area owns which responsibility so that developers do not place behavior arbitrarily.

## Ownership rules

- A module should have one clear reason to change.
- Shared concepts should live in shared domain or protocol layers, not in random consumer modules.
- Solvers may consume domain abstractions but should not silently redefine them.
- Builders should assemble objects, not hide physical formulas that belong elsewhere.

## Example ownership model

### `project_spec`

Owns YAML loading, schema version handling, validation, normalization, and project-level defaults.

### `domain`

Owns shared datatypes, units, study descriptors, identifiers, enums, and public protocols.

### `geometry` or `flare`

Owns analytic shape definitions, flare-law interfaces, curve or profile sampling, and geometry-side validation.

### `lem`

Owns reduced-model objects, discretization for reduced models, and LEM-specific assembly.

### `bem`

Owns BEM-side geometry preparation, boundary descriptors, and BEM-specific assembly.

### `runtime`

Owns execution control, job state, caching, logging, artifact locations, and reproducibility metadata.

### `post`

Owns result derivation, export transforms, and presentation-oriented calculations.

### `interfaces`

Owns CLI commands, Python convenience entry points, and external-facing API wrappers.

## Modification rules

When a new feature arrives, choose the implementation location using this order:

1. Does an existing module already own this responsibility?
2. Would adding it there preserve coherence and single responsibility?
3. Is the feature shared by multiple consumers and therefore better placed in a lower shared layer?
4. Does adding it here create a new public contract or architectural dependency?

If question 4 is yes, escalate to architecture review.

## Developer rule

The Developer may propose a placement, but authoritative ownership belongs to the Spec Lead under the architecture rules.
