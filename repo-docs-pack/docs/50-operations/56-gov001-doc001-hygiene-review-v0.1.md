# GOV-001/DOC-001: Hygiene Review (v0.1)

## Baseline
GitHub main, 262 passing tests.

## Purpose
Conduct a bounded repository hygiene and phase-boundary review. This task classifies known untracked local files, prevents public capability overclaiming, and aligns documentation with repository truth.

## Untracked Files Classification

| File | Classification | Recommended Next Action |
|---|---|---|
| `.gitignore` | local-only | Add to repository root if applicable |
| `repo-docs-pack/docs/50-operations/32-anl001-status-v0.1.md` | catch-up candidate | Commit under separate authorization |
| `repo-docs-pack/docs/50-operations/36-act001-status-v0.1.md` | catch-up candidate | Commit under separate authorization |
| `src/ausolveris/geometry/acoustic_view.py` | catch-up candidate | Commit under separate authorization |
| `src/ausolveris/geometry/analysis.py` | catch-up candidate | Commit under separate authorization |
| `tests/geometry/test_acoustic_view.py` | catch-up candidate | Commit under separate authorization |
| `tests/geometry/test_analysis.py` | catch-up candidate | Commit under separate authorization |

*Explicit Statement:* No untracked files were committed by this task, unless the Director separately authorized it.

## Current Capability Boundary
The repository is strictly in the readiness/scaffolding phase with bounded scalar sanity hooks.

## Current Non-Capabilities
The repository is not a validated BEM solver, does not compute SPL, does not compute impedance, and does not synthesize frequency responses.

## Final Validation Command
`PYTHONPATH=src pytest tests/geometry -q` (Expected: 264 passed)
