# Interface Contracts

## Purpose

This document defines how public interfaces should be specified before or during implementation.

## Why contracts matter

A Developer cannot fit code correctly into a larger system if the public contract is vague. Contracts let local work stay compatible with the rest of the repository.

## Contract template

Each public class, protocol, or function should eventually define:

- name,
- purpose,
- owning module,
- inputs,
- outputs,
- units,
- invariants,
- error behavior,
- side effects,
- dependencies,
- examples of use.

## Design principles

- Prefer small, explicit public contracts.
- Separate physical meaning from execution plumbing.
- Keep pure geometry or math separate from orchestration when practical.
- Avoid hidden unit conversions.
- Make invalid states hard to represent.

## Example contract sketch

### `ExponentialFlareLaw`

Purpose:
Represent an exponential flare law for reusable geometry-side calculations.

Possible inputs:
- throat area,
- flare parameter or mouth constraint,
- path length,
- unit convention.

Possible outputs:
- area at position,
- radius at position,
- sampled profile over a path.

Not responsible for:
- mesh generation,
- solver execution,
- file I/O,
- plotting.

## Contract maturity levels

### Level 0

Idea only.

### Level 1

Named concept with purpose and ownership.

### Level 2

I/O and units defined.

### Level 3

Validation rules, error behavior, and examples defined.

### Level 4

Stable enough for implementation and testing.

## Rule for coding

The Developer should not implement or change a public contract beyond minor local details unless the contract has reached a stable enough level for the task.
