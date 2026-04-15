# Test Strategy

## Purpose

This document defines the intended validation strategy for the project.

## Core principles

- Every non-trivial feature should be testable.
- Numerical code requires both functional tests and regression tests.
- Benchmarks must be separable from fast unit tests.
- Validation commands must be easy to run locally.

## Planned test layers

### Unit tests

Fast tests for pure functions, validators, parsers, transformations, and small numerical helpers.

### Integration tests

Tests that verify multi-component behavior such as YAML loading, mesh import, or job execution flow.

### Regression tests

Tests that compare outputs against accepted reference values, files, or response curves.

### Benchmark tests

Larger tests used to compare behavior against known analytical, published, or trusted reference cases.

## Expected tooling

- `pytest` for test execution.
- markers to separate slow and fast tests.
- reproducible reference artifacts stored in a controlled form.

## Early rules

- New code should come with tests unless explicitly exempted.
- Bug fixes should include a regression test whenever practical.
- Solver outputs should not be considered stable unless benchmarked.

## Open questions

- What first benchmark problems are most appropriate for v1?
- Which tolerances are acceptable for early numerical regression?
- How should large reference data be stored and versioned?
