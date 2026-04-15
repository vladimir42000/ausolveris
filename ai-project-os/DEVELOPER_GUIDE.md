# Developer Guide

## Purpose

This document explains how contributors and AI-assisted development roles should work inside the repository.

## Core rules

- Work from an approved task packet.
- Keep changes small and scoped.
- Add or update tests when behavior changes.
- Respect append-over-overwrite documentation policy.
- Record major decisions as ADRs.

## Expected working pattern

1. Read the task packet.
2. Confirm files in scope.
3. Create or switch to the assigned branch.
4. Implement the minimal coherent change.
5. Run validation commands.
6. Update relevant documentation.
7. Produce a concise handover or completion note.

## Documentation expectations

Developers should provide:

- docstrings for public interfaces,
- units and assumptions where relevant,
- concise inline comments where algorithmic intent is not obvious,
- no unnecessary verbose commentary.

## Review expectations

Developer output is not merge-ready until:

- tests pass,
- docs impact is reviewed,
- merge gate is checked,
- auditor feedback is resolved or accepted.
