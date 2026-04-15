# Functional Geometry and Derived Geometry

- Doc ID: GEO-02
- Version: v0.1
- Status: Draft
- Authoring role: Spec Lead
- Decision owner: Director
- Physics review required: Yes
- Audit required before acceptance: Yes
- Last updated: 2026-04-15

## Purpose

Separate the geometry that expresses study intent from the geometry or mesh artifacts generated, imported, or transformed for downstream use.

## Core distinction

### Functional geometry

Functional geometry is the source-of-truth representation of the study shape, structure, references, and geometric relationships as defined by the project.

It answers questions such as:

- what object or sub-object exists,
- how it is identified,
- how it is positioned or referenced,
- which parts are related,
- which named regions or boundaries exist,
- what geometric meaning is intended.

### Derived geometry

Derived geometry is any downstream artifact produced from, attached to, or interpreted from functional geometry for a narrower purpose.

Examples include:

- sampled profiles,
- tessellated surfaces,
- imported or generated meshes,
- reduced-model discretization support geometry,
- solver-preparation geometry,
- export-oriented intermediate forms.

## Ownership rule

Functional geometry belongs to the geometry/core-domain side of the architecture.

Derived geometry belongs to whichever downstream subsystem generates or owns it:

- geometry branch for geometry-side sampling or export,
- BEM-oriented branch for boundary-ready mesh preparation,
- reduced-model branch for reduced-model discretization support,
- runtime or artifact subsystems only for storage and traceability, not for meaning.

## Source-of-truth rule

The functional geometry representation is primary.

Derived geometry is secondary unless the project later approves a specific imported-geometry workflow in which an external artifact is accepted as the canonical source. That workflow is not yet frozen by the current documentation set and therefore remains an open question.

## Traceability rule

When derived geometry exists, the project should be able to answer:

- from which functional geometry it came,
- under which conventions and units it was produced,
- which transformation or sampling settings were used,
- which subsystem owns the artifact,
- whether the artifact is reusable or solver-local.

## Persistence rule

Functional geometry should be stable and diff-friendly in project definitions.

Derived geometry may be:

- ephemeral,
- cached,
- exported,
- regenerated,
- or stored as an explicit artifact,

but it should not silently replace the source-of-truth functional description.

## Validation split

### Functional geometry validation

Functional geometry validation should focus on:

- structural completeness,
- identifier consistency,
- explicit units and coordinate meaning,
- internal geometric consistency,
- required references being resolvable,
- invalid states being rejected before solver preparation.

### Derived geometry validation

Derived geometry validation should focus on:

- derivation correctness,
- artifact integrity,
- downstream fitness for the intended consumer,
- reproducibility of the derivation process.

## Mesh-specific position

The current baseline does not justify treating mesh as the same thing as geometry.

Mesh should therefore be treated as a derived representation unless and until an explicit import-first or mesh-first decision is approved.

This is especially important because the architecture material distinguishes reusable geometry from solver-specific and BEM-specific preparation.

## Provisional recommendation

A practical provisional rule is:

> prefer functional geometry as the canonical layer, and treat mesh as a named derived artifact class rather than as the canonical model itself.

### Trade-off

This avoids early solver coupling and keeps project intent readable, but it may require an additional derivation step before some solver workflows can execute. Under the current repository posture, that extra step is preferable to prematurely collapsing geometry and solver preparation into one layer.

## Non-goals

This document does not decide:

- whether v1 will support analytic-only geometry,
- whether v1 will support imported CAD or imported mesh as inputs,
- the exact persistence format for derived mesh artifacts,
- the exact metadata schema for geometry derivations.

Those remain explicit follow-on decisions.
