# Geometry Benchmark Plan

- Doc ID: VAL-04
- Version: v1.0
- Status: Proposed
- Authoring role: Product Physicist
- Decision owner: Director
- Physics review required: Yes
- Audit required before acceptance: Yes
- Last updated: 2026-04-16

## Purpose

Define the first geometry-only benchmark plan for AuSolveris.

This document does **not** validate solver physics, numerical accuracy, or benchmark agreement with measured data. Its purpose is narrower:

- validate that canonical geometry preserves physically meaningful intent,
- validate that geometry semantics are stable and reviewable,
- validate that equivalent geometry stays equivalent under harmless rewrites,
- validate that ambiguous or contradictory geometry is rejected early,
- establish the minimum acceptance bar for geometry to be treated as trustworthy enough for later downstream contract work.

## Scope boundary

This benchmark plan covers **geometry validation only**.

It is in scope to test:

- part identity,
- hierarchy meaning,
- anchor semantics,
- frame and transform meaning,
- unit handling,
- boundary/reference stability,
- functional-versus-derived geometry separation,
- derivation traceability,
- rejection of invalid or ambiguous geometry.

It is out of scope to test:

- acoustic correctness,
- boundary-condition physics,
- mesh convergence,
- radiation behavior,
- resonances,
- material-law realism,
- solver performance,
- benchmark agreement with experiment,
- final solver-consumption APIs.

## Validation principle

Canonical geometry should become trusted only when its physical meaning is explicit enough that later consumers do not need to guess.

For this phase, the relevant question is not:

> does the solver produce the right physical answer?

The relevant question is:

> does the canonical geometry express the intended object, references, and relationships clearly enough that later solver work can consume it without hidden reinterpretation?

## Benchmark families

The first benchmark set should cover five families.

### 1. Reference semantics benchmarks

These benchmarks verify that canonical geometry can represent physically meaningful structure without ambiguity.

#### VAL-04-B01 Single-part reference body

A minimal single-part geometry with:

- explicit units,
- explicit frame,
- stable identity,
- named anchors or boundaries where applicable.

Purpose:

- prove the model can express one physically interpretable object cleanly.

#### VAL-04-B02 Parent-child assembly

A multi-part geometry with stable part decomposition.

Purpose:

- prove hierarchy expresses ownership and decomposition,
- prove containment does not silently imply physics,
- prove child references remain resolvable.

#### VAL-04-B03 Boundary-bearing part

A geometry with multiple named geometric loci.

Purpose:

- prove named boundaries or regions can be attached to geometry without naming drift,
- prove later attachment points exist without freezing physics meaning too early.

#### VAL-04-B04 Anchor-bearing assembly

A multi-part case with several anchors attached to different geometric contexts.

Purpose:

- prove anchors are stable geometry-side references,
- prove anchors are not treated as solver nodes or hidden physics sources.

### 2. Frame, transform, and unit benchmarks

These benchmarks verify that coordinate meaning is physically stable.

#### VAL-04-B05 Global-versus-local frame equivalence

The same geometry authored once in a global frame and once through local part frames and transforms.

Purpose:

- prove equivalent authorings preserve the same physical meaning after normalization.

#### VAL-04-B06 Rigid-transform invariance

The same geometry translated or rotated without changing its intrinsic form.

Purpose:

- prove pose is not confused with identity,
- prove reference semantics survive rigid transforms.

#### VAL-04-B07 Unit equivalence

The same geometry expressed in different declared units.

Purpose:

- prove normalized physical dimensions remain equivalent,
- prove silent unit drift is not tolerated.

#### VAL-04-B08 Orientation and handedness sensitivity

A deliberate orientation or handedness mismatch case.

Purpose:

- prove the system does not silently accept ambiguous frame meaning.

### 3. Relationship and topology benchmarks

These benchmarks verify that physically relevant geometric relationships are not collapsed into vague hierarchy.

#### VAL-04-B09 Two-part interface case

Two parts that meet at a named interface-like locus.

Purpose:

- prove shared geometric reference can exist before physics vocabulary is frozen,
- prove geometric contact/adjacency can be represented without hidden boundary conditions.

#### VAL-04-B10 Contained-versus-adjacent distinction

One case based on containment and one case based on adjacency or attachment.

Purpose:

- prove containment, adjacency, and coupling are not treated as the same thing.

#### VAL-04-B11 Reference stability under benign refactor

A geometry that is reorganized structurally without changing intended physical meaning.

Purpose:

- prove named references survive non-semantic edits.

### 4. Functional-versus-derived geometry benchmarks

These benchmarks verify that canonical geometry remains primary.

#### VAL-04-B12 Derived artifact provenance

A simple functional geometry that produces one derived geometry artifact.

Purpose:

- prove derivation ownership, units, and provenance remain explicit,
- prove the derived artifact remains secondary to the canonical source.

#### VAL-04-B13 Derived artifact regeneration

A derived artifact is removed and recreated from the same canonical source.

Purpose:

- prove regeneration is traceable and reproducible at the geometry-semantics level.

#### VAL-04-B14 Canonical immutability under derivation

A derivation process must not mutate the canonical source description in place.

Purpose:

- enforce the source-of-truth rule from the geometry architecture package.

### 5. Negative and rejection benchmarks

These benchmarks verify that unsafe geometry is rejected rather than guessed.

#### VAL-04-B15 Invalid geometry corpus

The rejection set should include, at minimum:

- duplicate identifiers,
- dangling references,
- missing or conflicting units,
- contradictory frame definitions,
- invalid extents where forbidden,
- ambiguous boundary ownership,
- cyclic hierarchy,
- references to non-existent geometry,
- silent unit mixing,
- derived artifacts presented as canonical without explicit approval.

Purpose:

- ensure underdefined or contradictory geometry fails early and clearly.

## Recommended first benchmark batch

The first implementation batch should stay small and reviewable.

Recommended initial cases:

1. single-part box with explicit global frame,
2. same box in alternative units,
3. same box authored through local frame composition,
4. two-part chamber-and-neck style assembly,
5. boundary-bearing panel with named opening,
6. anchor stability under benign structural refactor,
7. one derived-artifact provenance case,
8. one negative corpus pack.

This batch is sufficient to test the current geometry core claims without opening solver physics.

## Reference geometry and test data requirements

This phase does not require measured physical data.

It does require controlled geometry reference assets.

### Required benchmark assets

#### A. Gold canonical geometry fixtures

Each positive benchmark should have a small, hand-authored canonical geometry fixture with:

- explicit units,
- explicit frame meaning,
- stable identifiers,
- named parts,
- named anchors or boundaries where relevant,
- expected ownership and hierarchy.

These fixtures should stay human-readable and reviewable in the repository.

#### B. Expected normalized outcomes

Each positive benchmark should define the expected normalized result, including:

- resolved units,
- resolved frame relationships,
- stable identifier mapping,
- reference resolution,
- preserved hierarchy meaning,
- preserved functional-versus-derived separation.

These expected outcomes are the main oracle for geometry correctness in this phase.

#### C. Equivalence pairs

The benchmark pack should include explicit geometry pairs that are expected to be physically equivalent, including:

- unit-converted variants,
- local-frame versus global-frame authorings,
- rigidly transformed variants,
- benignly refactored variants.

#### D. Rejection corpus

The benchmark pack should include deliberately invalid geometry inputs that must fail deterministically.

This rejection corpus is a core validation asset, not an optional extra.

#### E. Derivation provenance fixtures

Where derived geometry is present, the benchmark data should record:

- source geometry identity,
- derivation ownership,
- units and conventions used,
- derivation settings,
- artifact class,
- whether the artifact is ephemeral, cached, or persistent.

#### F. Human review sketches

Each benchmark geometry should have a small review sketch or diagram in documentation or companion review material.

The goal is simple: a human reviewer should be able to see quickly what object the benchmark is intended to represent.

## Acceptance criteria for trustworthy geometry

For geometry to be treated as trustworthy enough at this phase, all of the following criteria should hold.

### 1. Semantic unambiguity

Accepted benchmark cases must show that:

- part identity is deterministic,
- hierarchy meaning is explicit,
- frame meaning is explicit,
- anchor and boundary references resolve deterministically,
- containment does not silently imply physics.

### 2. Stable physical meaning under harmless rewrites

Equivalent benchmark cases must preserve the same physical meaning across:

- unit conversion,
- local/global frame reformulation,
- rigid transform changes,
- benign hierarchy refactors.

### 3. Strict early rejection of invalid geometry

Known-bad geometry must fail before any downstream consumer is allowed to treat it as trustworthy input.

A geometry system is not trustworthy if it partially accepts ambiguous input and silently guesses the missing meaning.

### 4. Functional geometry remains primary

Whenever derived geometry exists:

- provenance must remain explicit,
- ownership must remain explicit,
- canonical geometry must remain the source of truth,
- derivation must not silently overwrite canonical meaning.

### 5. Human reviewability

A reviewer should be able to inspect each benchmark and answer:

- what geometry is intended,
- what the named references mean,
- what normalization or derivation occurred,
- why the accepted result is correct,
- why the rejected result is invalid.

### 6. Minimum coverage before downstream contract work

Before opening the first bounded solver-consumption contract, the benchmark suite should cover at least:

- one single-part reference case,
- one multi-part assembly case,
- one interface/adjacency case,
- one local-frame equivalence case,
- one unit-equivalence case,
- one derived-artifact traceability case,
- one realistic enclosure or passage-like geometry,
- one invalid-geometry rejection suite.

## Trust threshold statement

For the current project phase, geometry is trustworthy enough when it demonstrates three things:

1. physical meaning is explicit,
2. equivalent geometry stays equivalent,
3. ambiguous geometry is rejected rather than guessed.

That threshold is sufficient for later bounded contract work.

It is **not** sufficient for claiming full physical validation, solver validation, or benchmark-grade scientific closure.

## Deferred items

The following remain intentionally deferred beyond this document:

- finalized physical boundary taxonomy,
- solver-specific geometry consumption rules,
- mesh-specific acceptance criteria,
- numerical convergence acceptance bars,
- measured-data benchmark closure,
- implementation-specific schema details.

These should be reviewed later through bounded follow-on validation work.

## Proposed next use

If this document is accepted, it should be used to guide:

- creation of the first geometry benchmark fixtures,
- creation of the first rejection corpus,
- review of normalization and derivation behavior,
- preparation for the first bounded downstream geometry-consumption review.

It should **not** be used to justify early solver-physics claims.

## Related documents

This benchmark plan should be read together with:

- [`repo-docs-pack/docs/20-architecture/06-geometry-canonical-model-v0.1.md`](../20-architecture/06-geometry-canonical-model-v0.1.md)
- [`repo-docs-pack/docs/20-architecture/07-functional-vs-derived-geometry-v0.1.md`](../20-architecture/07-functional-vs-derived-geometry-v0.1.md)
- [`repo-docs-pack/docs/20-architecture/08-geometry-open-questions-and-risks-v0.1.md`](../20-architecture/08-geometry-open-questions-and-risks-v0.1.md)
- [`repo-docs-pack/docs/30-spec/05-part-hierarchy-anchors-frames-and-boundary-semantics-v0.1.md`](../30-spec/05-part-hierarchy-anchors-frames-and-boundary-semantics-v0.1.md)
- [`repo-docs-pack/docs/30-spec/06-solver-consumption-of-geometry-v0.1.md`](../30-spec/06-solver-consumption-of-geometry-v0.1.md)
- [`repo-docs-pack/docs/50-operations/06-task-packet-sch-001-geometry-yaml-schema-v1-v0.1.md`](../50-operations/06-task-packet-sch-001-geometry-yaml-schema-v1-v0.1.md)

These documents define the canonical geometry posture, functional-versus-derived separation, current part/anchor/frame/boundary semantics, downstream solver-facing constraints, and the YAML-schema context this benchmark plan is intended to protect before solver-physics validation begins.

