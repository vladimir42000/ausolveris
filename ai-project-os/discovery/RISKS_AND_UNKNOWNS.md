# Risks and Unknowns

## Status

Draft for review.

## Major project risks

### Scope inflation

The ambition may drift from a realistic first release into a broad, loosely bounded “open AkAbak replacement” before benchmarked value is established.

### Architecture drift

Without strong ownership and contract discipline, new code may be inserted in convenient but incorrect locations, causing long-term structural decay.

### Numerical uncertainty

The project may adopt formulations or approximations whose practical accuracy is not yet known relative to intended loudspeaker use cases.

### Benchmark weakness

The project may produce outputs without enough trusted references to tell whether those outputs are acceptably correct.

### Performance mismatch

A Python-first implementation may be acceptable for orchestration and moderate workloads but insufficient for some future solver kernels without targeted optimization.

### Documentation lag

If technical reasoning is not written when decisions are made, later corrections and handovers will become expensive.

## Unknowns that require clarification

- canonical v1 use case,
- expected mesh or model scale,
- acceptable error versus reference,
- critical output set,
- initial comparison targets,
- first solver family.

## Risk mitigation strategy

- freeze v1 scope early,
- use benchmark-linked planning,
- isolate architectural decisions in ADRs,
- run bounded research spikes for unknowns,
- keep early abstractions minimal and evidence-driven.
