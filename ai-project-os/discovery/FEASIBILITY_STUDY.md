# Feasibility Study

## Status

Draft for review and decision support.

## Purpose

This document evaluates the feasibility of the proposed project before v1 scope is frozen.

## Problem statement

The project ambition is to build an open-source, YAML-driven loudspeaker modeling platform with a staged path toward LEM, BEM, and possibly hybrid workflows. The key feasibility question is not whether all ambitions are theoretically interesting, but which subset is realistic for a first release with controlled cost and complexity.

## Feasibility dimensions

### Operational feasibility

The project is operationally feasible if it primarily targets advanced users who accept YAML-driven workflows, explicit configuration, and early-stage engineering tooling.

Operational feasibility is lower for casual users expecting a polished GUI from the beginning.

### Technical feasibility

A Python-led backbone with modular solver pathways is technically feasible.

A narrow v1 focused on one clear problem family is feasible.

A full broad-spectrum open-source replacement for every AkAbak-like capability in an initial phase is not considered realistic.

### Numerical feasibility

Analytic geometry handling, flare-law infrastructure, YAML specification, validation, execution orchestration, and benchmark infrastructure are feasible in an early phase.

A narrow initial solver path, especially one with strong geometric structure and limited physics assumptions, is feasible.

Fully general hybrid workflows, unrestricted geometry, advanced performance optimization, and broad end-user coverage should be treated as later-phase work or research topics.

### Economic feasibility

The project is feasible if development is phased, architecture decisions are explicit, and expensive exploration is constrained by benchmark-driven scope discipline.

The project becomes economically weak if large-scale generic abstractions or multiple solver families are implemented before the first useful benchmarked use case exists.

## Candidate strategic options

### Option A

Narrow v1 around horn and waveguide-related geometry plus a first reduced-model or geometry-evaluation path.

Assessment: high feasibility, good learning value, strong architectural payoff.

### Option B

Narrow v1 around one reusable geometry layer plus one benchmarked first solver path.

Assessment: very strong feasibility, best balance of architecture and practical progress.

### Option C

Simultaneous LEM, BEM, and hybrid coupling in the first release.

Assessment: low feasibility for a disciplined first release.

## Early feasibility conclusion

The project is realistic if and only if the first release is tightly bounded.

The most realistic direction is to build:

1. a robust project specification and execution backbone,
2. a reusable analytic geometry layer,
3. a first benchmark-backed solver path,
4. a validation-first post-processing layer.

## Questions requiring owner review

- Which exact problem family should define v1?
- Is the first user flow geometry-centric, solver-centric, or benchmark-centric?
- What minimum outputs make the first release useful?
- What published or trusted references will act as initial benchmark anchors?

## Provisional recommendation

Proceed to v1 definition only after selecting one narrow initial problem family and one first solver path. Delay broader hybrid ambitions until benchmark-backed experience exists.
