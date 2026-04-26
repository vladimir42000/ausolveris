# Acoustic Topology Consumption Contract (v0.1)

**Status:** Draft → Implemented  
**Date:** 2026-04-27  

## Purpose
Define a read-only contract for future numerical acoustics modules to consume a validated `AcousticTopologyView`. This contract ensures that topology validation is completed before any BEM/LEM/FEM calculation.

## Principles
- `GeometryModel` remains canonical.
- `AcousticTopologyView` is derived from `GeometryModel` + explicit acoustic metadata.
- Consumption is allowed only after `view.errors` is empty.
- No numerical acoustics (pressure, velocity, impedance, radiation, etc.) are computed at this stage.
- The current solver stub only returns structural observables (counts, summaries).

## API
```python
def consume_acoustic_topology(view: AcousticTopologyView) -> dict
```
Raises `ValueError` if invalid. Returns dictionary with structural keys.

## Future Work
- BEM/LEM modules must consume this contract instead of reading raw geometry.
- This task does not implement any acoustic solver physics.
