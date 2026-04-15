# Task Granularity Rules

## Purpose

This document defines what a development task must look like before it is assigned.

## Core rule

A task must be small enough to be implemented, tested, reviewed, and handed over without requiring full-repository awareness.

## A good task usually has

- one clear objective,
- one owning subsystem,
- limited files in scope,
- explicit acceptance criteria,
- explicit validation commands,
- no hidden architectural decisions.

## A task is too big if

- it spans multiple subsystems without contract definitions,
- it requires redesigning several abstractions at once,
- it cannot be validated by a compact test set,
- the developer must inspect unrelated modules just to guess where code belongs.

## Good task examples

- implement one flare-law class under an existing protocol,
- add one schema validation rule,
- add one post-processing export function,
- refactor one module without changing its public interface,
- add one regression test for a known bug.

## Bad task examples

- add horn support,
- improve the runtime,
- make the API more flexible,
- support arbitrary geometry everywhere.

## Required contents of a developer-ready task

- task ID,
- phase ID,
- objective,
- files in scope,
- files out of scope,
- required outputs,
- interface contract or reference to it,
- tests to add or update,
- validation commands,
- escalation rule if architecture is touched.

## Escalation rule

If the task reveals a missing contract, unclear ownership, or architectural conflict, the developer must stop local expansion and escalate to the Spec Lead.
