# Discovery Review

## Status

Draft review summary.

## Current picture

The project has moved from pure governance setup into a first architecture exploration stage. The most important correction made during discovery is that the work should not go deeper into one branch without rechecking the whole tree.

## Current recommendation

Proceed with a whole-tree-aware architecture path in which:

- the top-level tree remains visible,
- foundational branches are stabilized first,
- geometry-first remains a candidate but not an unquestioned dogma,
- solver branches are deferred until the shared domain and geometry contracts are clear enough.

## What is considered likely

- core domain is foundational,
- project specification is required early,
- validation cannot be postponed too far,
- geometry is a strong candidate for first useful capability,
- runtime can remain lightweight initially.

## What remains unresolved

- exact first stable geometry contracts,
- exact scope of geometry exports,
- exact minimum benchmark set,
- exact criteria for promoting geometry-first from provisional to frozen.

## Decision checkpoint proposed

Before any deeper branch design is accepted, the project should review:

1. architecture exploration,
2. discovery package,
3. candidate v1 direction,
4. first dependency and complexity concerns.

After that checkpoint, the project may either:
- confirm geometry-first,
- modify it,
- or choose a different first path.

## Recommended next deliverable

Create one decision note or ADR-level record that states whether geometry-first remains provisional or becomes the approved first architectural direction.
