# Role Model

This document defines the exact operating roles for the project, their authority, outputs, and boundaries.

## Director

### Purpose

Protect long-term direction, decide priorities, and approve phase transitions.

### Owns

- Vision and priority.
- Phase approval.
- Scope arbitration.
- Final decision on disputed trade-offs.

### Produces

- Phase approval notes.
- Priority decisions.
- Acceptance or rejection of milestone direction.

### Must not

- Perform routine coding.
- Carry detailed implementation context continuously.
- Act as sole auditor of its own approved direction.

## Product Physicist

### Purpose

Protect physical meaning, domain realism, benchmark relevance, and use-case validity.

### Owns

- Problem realism.
- Modeling assumptions.
- Benchmark scenario relevance.
- Units, conventions, and physical interpretation.

### Produces

- Modeling assumption notes.
- Benchmark selection input.
- Validity concerns on solver behavior.

### Must not

- Approve code quality alone.
- Merge code without audit gate.

## Spec Lead

### Purpose

Translate direction into technical tasks that developers can execute safely and efficiently.

### Owns

- Task packets.
- Interfaces and contracts.
- ADR drafting.
- Architecture coherence.
- Handover pack quality.

### Produces

- Technical specs.
- Task packets.
- ADR drafts.
- Review comments for implementation conformance.

### Must not

- Change project scope alone.
- Approve its own work as final quality gate.

## Developer

### Purpose

Implement code, tests, and implementation-level documentation.

### Owns

- Feature branch code.
- Pytest tests.
- Docstrings.
- Local developer notes.
- Validation command execution.

### Produces

- Code.
- Tests.
- Small technical notes.
- Handover after implementation.

### Must not

- Merge directly to protected branch.
- Redefine architecture ad hoc.
- Skip documentation impact review.

## Auditor

### Purpose

Act as independent quality and regression control.

### Owns

- Merge-gate verification.
- Reproducibility review.
- Regression review.
- Conformance check against task packet.

### Produces

- Audit notes.
- Defect lists.
- Pass/fail gate recommendation.

### Must not

- Quietly redesign scope.
- Share the same operative thread as Developer for the same task.

## Documentation Steward

### Purpose

Preserve project memory and keep repository knowledge coherent, append-only where required, and easy to hand over.

### Owns

- Stable document hygiene.
- Status snapshots.
- Changelog discipline.
- Glossary and cross-links.
- Preservation of historical meaning.

### Produces

- Documentation updates.
- Status snapshots.
- Indexes and references.
- Handover normalization.

### Must not

- Rewrite accepted decisions without an explicit supersession record.
- Invent technical intent not documented elsewhere.

## Optional Maintainer

If the team later grows, a Maintainer role may be separated from Director.

### Purpose

Own protected branch merge operations and release tagging.

### Owns

- Protected branch settings.
- Release tags.
- Merge execution after approvals.

### Must not

- Bypass merge gate.
