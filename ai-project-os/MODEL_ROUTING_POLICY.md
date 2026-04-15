# Model Routing Policy

This document defines which model class should be used for which role to optimize cost, quality, and stability.

## Core principle

Use the cheapest model that can reliably perform the task.

## Routing philosophy

- High-volume implementation uses cheap models.
- High-consequence review uses stronger models.
- Planning and broad discussion can use subscription chats.
- Long-lived memory belongs in repository files, not model context.

## Recommended routing

### Director

Use human-led reasoning with subscription chat support.

### Product Physicist

Use a careful reasoning model, but with low traffic and short structured prompts.

### Spec Lead

Use a stronger model than Developer when architecture, contracts, and task decomposition matter.

### Developer

Use a low-cost coding-capable model in Aider for most implementation loops.

Recommended starting point:
- DeepSeek-class coding model via API.

### Auditor

Use a stronger model for milestone and merge-gate review; cheap model can assist with routine checklist checking.

### Documentation Steward

Use a cheap model or human editing for structured documentation tasks.

## Cost rules

- Avoid sending large unchanged context repeatedly.
- Reuse fixed templates.
- Keep responses compact by policy.
- Use branch-local and task-local context only.
- Require files lists and validation commands rather than broad narrative.

## Escalation rules

Escalate from cheap model to stronger model when:

- architecture is changing,
- numerical correctness is uncertain,
- audit detects repeated failure,
- ambiguous trade-offs cannot be resolved with confidence,
- benchmark mismatch persists.
