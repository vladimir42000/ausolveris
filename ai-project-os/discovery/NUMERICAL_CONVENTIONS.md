# Numerical Conventions

## Status

Draft for review.

## Purpose

This document captures project-wide numerical and physical convention rules.

## Early principles

- units must be explicit,
- sign conventions must be documented,
- coordinate meaning must be stated,
- normalization rules must be visible,
- public APIs should avoid silent unit conversion where practical.

## Provisional internal preference

Use SI-style internal conventions unless a clear project reason requires otherwise.

## Topics to freeze

- length units,
- frequency units,
- pressure reference conventions,
- phase and sign conventions,
- coordinate systems,
- indexing and ordering rules for sampled geometry or outputs.

## Rule for evolution

Any change to a project-wide numerical convention requires explicit documentation update and likely ADR coverage if it affects public behavior.
