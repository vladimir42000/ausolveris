# Physics Foundations

## Status

This is the initial physics foundation scaffold.

## Purpose

This document will record the physical assumptions, conventions, approximations, and limitations used throughout the project.

## Why it exists

A loudspeaker simulation platform can become misleading if numerical implementation details are not tied back to physical meaning. This document exists to preserve that connection.

## Expected future contents

- acoustic medium assumptions,
- time-harmonic versus transient scope,
- source model definitions,
- boundary condition conventions,
- enclosure and radiation approximations,
- coordinate system conventions,
- units and normalization choices,
- solver applicability limits.

## Early rules

- No implicit units where confusion is possible.
- No undocumented approximation should enter the code.
- If a physical shortcut is introduced, it must be documented.
- Benchmark interpretation must reference the assumptions in this file.

## Open questions

- What exact v1 physical problem family will be treated as canonical?
- Which simplifying assumptions are acceptable in v1?
- Which user expectations from AkAbak-like workflows must be matched first?
