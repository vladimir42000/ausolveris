# Handover Protocol

This protocol defines how work is transferred between threads, models, or roles.

## Principle

A handover must be sufficient for a new role or thread to continue work without searching old chat history.

## Mandatory triggers

Create a handover when:

- a thread is saturating,
- a role changes,
- a model changes,
- work pauses for later continuation,
- a task is blocked and escalated,
- an audit begins after implementation.

## Handover structure

Every handover must include:

- Task ID.
- Phase ID.
- Branch name.
- Goal.
- Why this task matters.
- Files in scope.
- Files out of scope.
- Decisions already taken.
- Work completed.
- Work remaining.
- Validation commands.
- Risks and blockers.
- Open questions.
- Recommended next action.

## Size rule

A handover must be concise enough for a new agent to absorb quickly. Prefer bullets, file paths, IDs, commands, and references over narrative prose.

## Repository linkage rule

A handover must point to authoritative repository artifacts:

- task packet,
- ADRs,
- status snapshot,
- relevant docs,
- benchmark files,
- test commands.

## Exit rule

No agent may end a substantial work block without either:

- completing the task and updating task status, or
- issuing a handover.
