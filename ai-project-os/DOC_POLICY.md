# Documentation Policy

This document defines how project documentation evolves without losing project memory.

## Documentation classes

### Class A — Stable core documents

These are append-only unless an explicit governance action supersedes them:

- `CONSTITUTION.md`
- `ROLE_MODEL.md`
- `PHASE_PLAN.md`
- `PHYSICS_FOUNDATIONS.md`
- `docs/adr/*`

### Class B — Controlled living documents

These may evolve, but changes must preserve historical meaning and explicitly note material changes:

- `ARCHITECTURE.md`
- `API_SPEC.md`
- `YAML_SCHEMA.md`
- `TEST_STRATEGY.md`
- `USER_GUIDE.md`
- `DEVELOPER_GUIDE.md`

### Class C — Dynamic status documents

These are expected to change frequently:

- `STATUS.md`
- `CHANGELOG.md`
- `LATEST_RELEASE.md`
- `TEST_RESULTS.md`
- `BENCHMARK_RESULTS.md`

## Append-over-overwrite rule

If accepted meaning must change, prefer one of these patterns:

1. Add a dated update section.
2. Add a supersession note that points to a newer section or ADR.
3. Add an addendum instead of rewriting historical text.

## Documentation minimums per task

Each non-trivial task must consider whether it impacts:

- user behavior,
- developer workflow,
- architecture,
- numerical assumptions,
- tests,
- benchmark interpretation.

If yes, the relevant document must be updated.

## Code documentation rules

The project requires:

- module-level purpose notes where needed,
- function or class docstrings for public interfaces,
- units and assumptions in docstrings when relevant,
- concise inline comments only where algorithmic intent is not obvious.

## Forbidden practices

- Silent rewriting of accepted architecture rationale.
- Large prose dumps with no link to code or task.
- Keeping critical decisions only in chat threads.
