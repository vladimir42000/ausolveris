# Planning and Execution Model

## Purpose

This document explains who defines what, in what order the project is prepared, and how the work transitions from planning into coding.

## Core sequence

The project should progress in this order:

1. Governance setup.
2. Product mission definition.
3. v1 functional analysis.
4. Technical analysis.
5. System map and ownership model.
6. Interface contract definition for early subsystems.
7. Phase planning.
8. Initial benchmark plan.
9. Development task decomposition.
10. Coding.
11. Audit and integration.

## Who defines what

### Director

Defines:
- mission,
- priority,
- release direction,
- trade-off acceptance.

### Product Physicist

Defines:
- target physical problems,
- acceptable assumptions,
- benchmark relevance,
- modeling realism.

### Spec Lead

Defines:
- architecture shape,
- subsystem boundaries,
- interface contracts,
- task granularity,
- detailed developer handouts.

### Developer

Defines:
- local internal implementation details inside a task boundary,
- refactoring details that do not violate architecture.

### Auditor

Defines:
- whether the change is acceptable against the task, tests, and merge gate.

## Preparation before coding

### Minimal preparation package

Coding should begin only after these are available:

- accepted governance documents,
- initial ADR set,
- product mission,
- v1 use cases,
- v1 non-goals,
- first benchmark list,
- system map,
- module ownership rules,
- task granularity rules,
- first stable interface contracts for the subsystem being coded.

### Recommended preparation effort

For a project of this complexity, a realistic lean preparation period is around 5 to 10 focused working days before serious coding begins.

A practical split is:

- 1 to 2 days for governance finalization,
- 1 to 3 days for mission, v1 scope, and benchmark planning,
- 1 to 3 days for architecture and ownership model,
- 1 to 2 days for first contracts and first phase task decomposition.

This is not wasted time. Strong upfront preparation reduces later rework, especially in scientific software where incorrect structure can silently damage results.

## Suggested near-term execution plan

### Preparation block A

Freeze mission and product direction.

### Preparation block B

Freeze v1 scope, benchmark philosophy, and non-goals.

### Preparation block C

Freeze subsystem map, ownership, and first contract set.

### Preparation block D

Define Phase P1 and first task packets.

### Coding block P1

Begin only with developer-ready tasks that fit the architecture.

## Validation before coding

Before the first coding task, confirm:

- architecture questions needed for that task are resolved,
- contract maturity is high enough,
- benchmark reference exists or is planned,
- task packet is clear enough to hand to a Developer without discussion drift.

## Long-term rule

The project should never move directly from idea to implementation. It should move from idea to ownership, ownership to contract, contract to task, and task to code.
