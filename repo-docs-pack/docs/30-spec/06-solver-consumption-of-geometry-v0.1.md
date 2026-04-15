# Solver Consumption of Geometry

- Doc ID: GEO-04
- Version: v0.1
- Status: Draft
- Authoring role: Spec Lead
- Decision owner: Director
- Physics review required: Yes
- Audit required before acceptance: Yes
- Last updated: 2026-04-15

## Purpose

State how solver-facing modules should relate to canonical geometry under the current provisional architecture, without freezing a more specific solver-consumption contract than the repository currently supports.

## Baseline constraints

The current repository baseline supports these constraints:

- solvers may consume shared domain abstractions,
- solvers should not silently redefine shared geometry concepts,
- solver options must be separated from physical model definition,
- geometry should remain reusable across multiple future consumers,
- geometry must not embed solver assumptions too early.

## Consumption principle

Solver modules should treat canonical geometry as an upstream shared input, not as an internal implementation detail they are free to reinterpret without contract.

This means a solver-facing module should:

1. consume explicit geometry references rather than hidden positional assumptions,
2. declare which geometry-side inputs it requires,
3. make any additional derivation or compilation step visible,
4. preserve units, coordinate meaning, and identifiers,
5. avoid mutating canonical geometry in place.

## Safe current statement

What can safely be said today is this:

- canonical geometry exists before solver-specific preparation,
- solver modules may require derived geometry artifacts,
- those artifacts should be produced through explicit, owned transformations,
- the canonical model should remain readable independently of any one solver path.

## What is not yet frozen

The current documentation does **not** yet justify freezing:

- whether solvers consume canonical geometry directly,
- whether solvers consume a normalized intermediate graph,
- whether solvers consume only compiled solver-specific representations,
- the exact public interface between geometry and any one solver family.

Those are still open design decisions.

## Provisional recommendation

A reasonable provisional direction is:

> geometry consumers should receive canonical geometry through an explicit geometry-to-consumer preparation boundary, rather than by reading raw project YAML ad hoc and reconstructing their own geometry meaning.

### Why this recommendation helps

It reduces drift between consumers, preserves ownership, and makes future validation easier.

### Trade-off

It adds one architectural seam and may feel slower than allowing each solver path to parse geometry for itself. But that seam is valuable because the project explicitly wants reusable geometry contracts and wants to avoid solver-shaped architectural drift.

## Consumer categories

Without freezing exact contracts, it is still useful to distinguish likely consumer categories:

### Geometry-side consumers

These remain inside the geometry branch and may consume canonical geometry for:

- validation,
- sampling,
- export,
- geometry-side visualization,
- derivation of named geometric artifacts.

### Modeling consumers

These belong to future modeling branches and may consume canonical geometry or derived artifacts for:

- reduced-model preparation,
- boundary-oriented preparation,
- later hybrid coupling preparation.

### Post-processing and interface consumers

These should normally consume result metadata and reviewed artifacts rather than reconstruct geometry semantics independently.

## Contract guidance for future work

When a specific solver path is eventually proposed, its geometry-consumption contract should state at least:

- owning subsystem,
- upstream geometry inputs,
- accepted derived artifact types,
- units and coordinate expectations,
- invariants,
- error behavior,
- what the solver is not allowed to infer implicitly.

## Non-goal guardrail

This document does not authorize direct implementation of a solver-specific geometry API beyond bounded local experimentation already approved elsewhere. Acceptance of any concrete consumption contract requires later review.
