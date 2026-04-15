# Architecture Decision Space

## Status

Draft for review.

## Purpose

This document records the current major design options and their likely consequences before a hard commitment is made.

## Current core question

What should be the first stable capability of the platform?

## Candidate directions

### Option 1: Geometry-first foundation

Description:
Build a reusable geometry and flare-law layer first, plus the supporting domain and project-definition skeleton needed to make it stable and testable.

Advantages:
- strong architectural cleanliness,
- reusable by multiple future branches,
- lower numerical risk than jumping directly into solver implementation,
- easier to benchmark locally.

Risks:
- user value may feel indirect if outputs are too abstract,
- danger of overdesigning abstractions before enough concrete consumers exist.

### Option 2: First reduced-model path immediately

Description:
Implement a narrow first modeling path and derive abstractions from that experience.

Advantages:
- early end-to-end user value,
- concrete benchmark path,
- less risk of abstract design detached from use.

Risks:
- shared geometry/domain concepts may be embedded in solver-specific code,
- future branches may need refactoring to extract reusable concepts.

### Option 3: Dual-path early architecture

Description:
Build both reusable geometry and a first modeling path in parallel from the start.

Advantages:
- immediate pressure-testing of abstractions,
- stronger confidence that the geometry branch is not too isolated.

Risks:
- more complexity,
- weaker focus,
- higher planning and validation burden.

## Current recommendation

Option 1 remains the safest architectural starting point, but only if it is constrained by two rules:

1. the geometry branch must be defined against likely future consumers,
2. the project must revisit the decision after a whole-tree review rather than treat it as final dogma.

## Decision filters

A v1 direction should be preferred if it:
- reduces future coupling,
- does not block later modeling branches,
- creates reusable contracts,
- can be validated meaningfully,
- does not force premature optimization.

## Provisional conclusion

Geometry-first is a strong candidate but should remain a provisional architecture choice until reviewed against the full-tree dependency picture.
