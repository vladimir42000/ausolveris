# Phase Plan

## Phase identity

- Phase ID: P0
- Phase name: Governance and Foundation Freeze
- Status: accepted
- Owner: Director
- Start date: 2026-04-15
- Target review date: 2026-04-22

## Purpose

This phase establishes the non-changing operational backbone of the project before solver implementation begins. The aim is to prevent direction drift, context loss across AI threads, undocumented decisions, and uncontrolled code growth.

## User value

If this phase succeeds, the project gains a reliable operating framework that allows multiple AI roles and a human operator to collaborate on the solver without losing decisions, breaking discipline, or overwriting project memory.

## In scope

- Freeze governance documents and role definitions.
- Start the ADR record.
- Define the initial project mission and first development assumptions.
- Create the initial active documentation set.
- Define the first technical planning horizon for v1.

## Out of scope

- Implementing solver kernels.
- Finalizing numerical formulations in full detail.
- Building production APIs.
- Benchmark execution beyond initial planning.
- Performance optimization.

## Deliverables

- Accepted governance backbone in repository.
- ADR-001 through ADR-004.
- Initial `PHASE_PLAN.md`.
- Initial active docs created from templates.
- Agreed first planning questions for v1 solver scope.

## Acceptance criteria

- Core governance files are present and accepted.
- ADR system is active with first four records written.
- Repository document structure is created.
- Human operator can start separate AI role threads using the prompt pack.
- The next phase can begin with scope definition rather than governance debate.

## Benchmark or validation targets

- Governance completeness check against the package checklist.
- Ability to issue a first formal task packet.
- Ability to perform a clean handover between two threads using the protocol.

## Key technical risks

- Role overlap causing uncontrolled decisions.
- Stable docs being silently rewritten.
- Coding starting before v1 scope is frozen.
- Excessive token spending due to oversized context transfer.

## Dependencies

- Repository initialized.
- Governance pack unpacked.
- Human operator available to approve the initial operating model.

## Expected documentation outputs

- `PHASE_PLAN.md`
- `STATUS.md`
- `CHANGELOG.md`
- ADR-001 to ADR-004
- Initial stubs for architecture, test strategy, YAML schema, physics foundations, user guide, and developer guide

## Exit condition

This phase is complete when the governance system is accepted, the first ADR set exists, the active planning documents exist, and the project is ready to define v1 technical scope in a controlled way.
