# Geometry Open Questions and Risks

- Doc ID: GEO-05
- Version: v0.1
- Status: Draft
- Authoring role: Spec Lead
- Decision owner: Director
- Physics review required: Yes
- Audit required before acceptance: Yes
- Last updated: 2026-04-15

## Purpose

Record the unresolved decisions and main risk areas surrounding the geometry core concept package so they remain explicit rather than being settled accidentally through implementation.

## Open questions

### 1. Exact v1 geometry scope

The current baseline supports geometry-first as a provisional direction, but it does not yet freeze whether v1 geometry is:

- purely analytic,
- partly imported,
- mesh-assisted,
- or multi-representation from the start.

### 2. Exact primitive set

The current documents justify reusable geometry contracts, but they do not yet justify a frozen list of primitives. The project still needs to decide which entities deserve first-class status in v1.

### 3. Exact scope of geometry exports

Architecture exploration material explicitly leaves unresolved the scope of geometry exports. This must be settled before downstream consumers begin depending on outputs that were never formally owned.

### 4. Boundary vocabulary

Boundary existence is clearly relevant, but the exact physical boundary vocabulary remains unfrozen and should not be implied by naming alone.

### 5. Imported artifact posture

It is still unresolved whether imported mesh or external geometry can ever be canonical in v1, or whether they must remain derived artifacts attached to a canonical project definition.

### 6. Solver-consumption boundary

It remains unresolved whether the long-term stable boundary is:

- direct consumption of canonical geometry,
- consumption through a shared compiled intermediate,
- or per-solver preparation contracts.

### 7. YAML expression level

The baseline YAML material leaves open how much geometry should be expressed directly in YAML versus referenced through imported artifacts.

## Risks

### Risk A: geometry overdesign

A geometry-first posture can drift into abstraction for its own sake. This risk is explicitly present in the architecture decision-space material.

#### Failure mode

The project freezes a large primitive system without enough real consumers.

#### Mitigation

Keep contracts narrow, review consumer needs explicitly, and defer anything not required by a bounded v1 path.

### Risk B: solver leakage into canonical geometry

This is already called out by the repository baseline.

#### Failure mode

Canonical geometry starts carrying solver-local assumptions, indexing, or boundary semantics that should belong to downstream consumers.

#### Mitigation

Require explicit ownership, explicit contracts, and review of any new field that appears solver-shaped.

### Risk C: ambiguous coordinate and unit meaning

The numerical conventions material already identifies this as foundational.

#### Failure mode

Geometry is structurally present but cannot be interpreted consistently across consumers.

#### Mitigation

Refuse implicit coordinate meaning, require explicit units, and make frame semantics part of contract review.

### Risk D: mesh and geometry collapse into one concept too early

This risks coupling geometry to a narrow backend path and undermining reusability.

#### Mitigation

Keep functional geometry and derived mesh geometry separate unless a reviewed decision says otherwise.

### Risk E: unclear ownership between geometry, modeling, and interfaces

If subsystem ownership is unclear, the task is not implementation-ready.

#### Mitigation

Require every geometry-related task to identify owning subsystem and whether it changes a public contract.

## Provisional sequencing recommendation

The safest next bounded sequence appears to be:

1. freeze the semantic role of canonical geometry,
2. freeze the functional-versus-derived split,
3. define the minimum reference semantics for parts, anchors, frames, and boundaries,
4. only then define one concrete consumer contract for one bounded downstream path.

### Trade-off

This delays deep solver integration, but it reduces the chance of architecture drift and protects the geometry-first posture from becoming a disguised solver-first implementation.

## Review triggers

A new review checkpoint should be triggered if any proposal attempts to:

- freeze the primitive set,
- define a physical boundary vocabulary,
- make mesh canonical by default,
- add solver-specific fields to canonical geometry,
- or define a stable solver-consumption API.
