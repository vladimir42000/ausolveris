# Benchmark Catalog

## Status

Draft scaffold.

## Purpose

This document will define the benchmark cases used to support verification and validation.

## Benchmark principles

Each benchmark entry should eventually specify:

- purpose and scope,
- physics being tested,
- exact configuration,
- reference source,
- expected outputs,
- uncertainty or tolerance,
- acceptance rule.

## Early benchmark classes

### Analytical benchmarks

Used where closed-form or strongly trusted reference behavior exists.

### Trusted numerical comparisons

Used where comparison against accepted external tools or established numerical methods is appropriate.

### Experimental or measured references

Used where the purpose is validation against physical behavior rather than only verification against mathematics.

## Placeholder entries

### BM-001

Simple geometry or flare reference behavior.

### BM-002

First solver-path canonical case.

### BM-003

Regression benchmark for first reusable output artifact.

## Rule

No solver result should be treated as trustworthy simply because it runs. Trust increases only when benchmark purpose, configuration, and acceptance conditions are explicit.
