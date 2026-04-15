# Geometry Canonical Model

- Doc ID: GEO-01
- Version: v0.1
- Status: Draft
- Authoring role: Spec Lead
- Decision owner: Director
- Physics review required: Yes
- Audit required before acceptance: Yes
- Last updated: 2026-04-15

## Purpose

Define what the canonical geometry model is responsible for, what it is not responsible for, and why it is treated as a first-class architectural concern in the current provisional geometry-first posture.

## Source-of-truth posture

The current repository baseline supports the following posture:

- geometry-first is a strong candidate for early stabilization,
- reusable geometry contracts belong in the foundational set,
- geometry must remain reusable across later modeling branches,
- geometry must not embed solver assumptions too early,
- solver options must remain separated from physical model definition,
- units, coordinate meaning, and conventions must stay explicit.

This document therefore treats the canonical geometry model as a shared project representation of geometric intent, not as a solver-specific data structure.

## Definition

The canonical geometry model is the stable, reviewable description of the study geometry that later consumers may interpret, validate, sample, transform, or compile.

Its job is to preserve geometric meaning across the project lifecycle:

- YAML/project definition,
- validation and normalization,
- geometry-side checks,
- downstream solver preparation,
- result traceability,
- later benchmark interpretation.

## What the canonical model must do

At the current maturity level, the canonical geometry model should support these responsibilities:

1. carry stable geometric identity so project elements can be named and referenced without ambiguity,
2. preserve explicit units and coordinate meaning,
3. represent reusable geometry intent independently from any one solver backend,
4. support geometry-side validation before numerical execution begins,
5. expose enough structure for later consumers to derive their own solver-side forms,
6. remain diff-friendly and reviewable in repository-managed project descriptions.

## What the canonical model must not do

The current baseline does **not** support treating the canonical model as any of the following:

- a BEM-specific boundary description,
- a reduced-model discretization,
- a meshing recipe locked to one numerical backend,
- an execution graph,
- a result container,
- a hidden transport for undocumented physics shortcuts.

## Canonical model content classes

The baseline documentation is not yet strong enough to freeze a complete primitive set. The canonical model is therefore defined here by **content classes** rather than by a closed list of primitives.

The content classes that are clearly justified already are:

- reusable geometry descriptions,
- stable references and identifiers,
- coordinate and unit meaning,
- geometry-side validation metadata,
- named relationships needed by downstream consumers,
- derivation links to downstream artifacts when those artifacts exist.

The exact v1 primitive set remains an open decision and must not be invented implicitly through implementation.

## Architectural position

The canonical geometry model sits between project specification/core domain and later geometry consumers.

It should be treated as:

- closer to project meaning than to solver assembly,
- more stable than derived numerical artifacts,
- broad enough to support multiple future consumers,
- narrow enough to avoid speculative all-purpose CAD ambitions.

## Non-goal guardrails

To preserve the bounded v1 posture, the canonical geometry model should **not** be expanded yet into a general-purpose CAD system, unrestricted free-form modeling system, or broad hybrid-workflow container.

Those directions may matter later, but they are not justified as accepted scope in the current repository baseline.

## Provisional recommendation

A useful working recommendation is:

> treat the canonical geometry model as the durable "functional study geometry" layer that downstream modules may consume only through explicit contracts.

### Trade-off

This keeps the architecture clean and reusable, but it also means early user-visible outputs may initially be geometry-side artifacts rather than full solver results. That trade-off is acceptable under the current geometry-first posture, provided it remains explicit and provisional.

## Acceptance implications

This document is ready to support follow-on specification work only at this level:

- define geometry-side responsibilities,
- constrain later contract design,
- block solver-shaped leakage into canonical geometry,
- support review of future geometry interfaces.

It does **not** yet authorize implementation of a full primitive library or a solver-consumption contract without further review.
