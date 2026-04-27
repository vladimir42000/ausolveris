# Acoustic Benchmark and Readiness Plan (v0.1)

**Status:** Defined – BEN-002  
**Date:** 2026-04-27  

## Purpose
Define a bounded benchmark/readiness harness for future numerical acoustic validation. This is a **readiness‑only** milestone – no numerical benchmark results are produced.

## Principles
- `GeometryModel` remains canonical.
- `AcousticTopologyView` is the sole input to benchmark readiness.
- The consumption contract (`consume_acoustic_topology`) must have succeeded.
- No raw geometry access or acoustic inference from names.
- No BEM, LEM, FEM, driver, SPL, impedance, pressure, velocity, or radiation.

## Supported readiness checks
- Patch/interface/observer counts
- Source group declaration
- Orientation, frame, interface side metadata
- Rejection of enclosure‑specific solver categories

## Future Work
Later numerical modules will use this readiness harness to validate preconditions before running BEM/LEM/FEM simulations. This task is a pure validation‑readiness layer.
