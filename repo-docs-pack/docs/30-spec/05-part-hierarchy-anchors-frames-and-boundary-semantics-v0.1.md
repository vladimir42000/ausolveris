# Part Hierarchy, Anchors, Frames, and Boundary Semantics

- Doc ID: GEO-03
- Version: v0.1
- Status: Draft
- Authoring role: Spec Lead
- Decision owner: Director
- Physics review required: Yes
- Audit required before acceptance: Yes
- Last updated: 2026-04-15

## Purpose

Define the minimum specification posture for how canonical geometry should express decomposition, reference points, local coordinate meaning, and boundary attachment points without prematurely freezing a full primitive system or a physics vocabulary.

## Part hierarchy

The canonical model should be able to express geometry as a hierarchy of named parts or subparts.

At minimum, the hierarchy exists to support:

- stable ownership of geometric meaning,
- readable decomposition of complex studies,
- reusable references across project files and later consumers,
- bounded downstream selection of regions, interfaces, or boundaries,
- traceability from outputs back to named geometric intent.

### Required semantics

The hierarchy should support these semantics even before the exact data model is frozen:

1. a part has a stable identity,
2. a part may have children or contained sub-elements,
3. a part may expose named references used elsewhere,
4. a part may carry geometry-side metadata,
5. containment must not silently imply physical boundary conditions.

## Anchors

Anchors are stable named geometric references attached to the canonical model.

Their purpose is to let project definitions and downstream consumers refer to meaningful locations or attachment references without depending on unstable solver-local indexing.

### Anchor semantics

At this stage, anchors should be understood as:

- named,
- explicitly scoped,
- geometrically meaningful,
- stable under non-breaking local refactoring of downstream artifacts,
- usable by validation and downstream derivation steps.

### What anchors are not

Anchors are not yet defined as:

- solver nodes,
- mesh vertex indices,
- physics sources by themselves,
- automatic constraints.

Those interpretations belong to later consumer contracts.

## Frames

Frames express coordinate meaning locally or globally so that geometry references remain interpretable.

The repository baseline already requires that coordinate meaning be stated explicitly. Frames are therefore required conceptually even though the exact frame algebra is not yet frozen.

### Minimum frame semantics

Any accepted frame concept should eventually make these questions answerable:

- relative to what origin or reference is this quantity stated,
- what orientation convention applies,
- which units are active,
- whether a quantity is global or part-local,
- how downstream consumers interpret handedness, direction, and sign.

### Guardrail

The geometry specification should define frame meaning clearly enough for reuse, but it should not bake in solver-specific coordinate conventions unless those conventions are explicitly approved as project-wide conventions.

## Boundary semantics

Boundary semantics are needed because later modules must attach conditions, interfaces, observations, or derived preparations to named geometric loci.

However, the current documentation baseline does **not** justify freezing a complete physical boundary vocabulary yet.

### Minimum boundary posture

The canonical geometry model should be able to express that a named geometric boundary exists and can be referenced.

At this stage, a named boundary should carry only the semantics that are safe to assert now:

- it is a geometrically identifiable locus or region,
- it belongs to some part or relationship context,
- it may be targeted by later validation or downstream preparation,
- its geometric identity is stable independently of any one solver backend.

### Explicit deferral

The following remain deferred decisions requiring later review, including Product Physicist review where relevant:

- exact boundary vocabulary,
- exact physical meaning of each boundary kind,
- default boundary assumptions,
- observer attachment semantics,
- coupling semantics between boundaries and solver modules.

## Provisional recommendation

A workable provisional contract direction is:

> define parts, anchors, frames, and boundaries first as geometry-side reference semantics, and allow physics meaning to be attached only by later reviewed contracts.

### Trade-off

This keeps the canonical model clean and reusable, but it delays some end-to-end convenience until downstream contracts are defined. That is the safer choice at the current project stage because it prevents accidental physics commitments from being smuggled in through geometry naming.

## Specification maturity note

This document establishes required **semantic slots** but intentionally does not freeze the exact v1 primitive set. That freeze should happen only after the project decides how much geometry richness v1 actually needs.
