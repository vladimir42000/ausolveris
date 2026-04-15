# Project Constitution

This constitution is the highest operational document for the project. It defines the non-changing rules that govern direction, development, review, documentation, and handover.

## Mission rule

The project exists to create a useful, testable, open-source loudspeaker-oriented simulation platform. Development decisions must favor practical modeling value, traceability, and scientific honesty over feature count.

## Authority rule

The Director owns direction and phase priority. No other role may change project direction unilaterally.

## Physics rule

Physical meaning outranks coding elegance. If a proposed implementation is numerically attractive but physically misleading, it must not be accepted without explicit Director and Product Physicist approval.

## Scope rule

No coding begins without a linked phase and task packet. No task packet may exist without acceptance criteria.

## Decision rule

No significant architectural, numerical, interface, storage, meshing, or workflow decision is valid unless recorded in the repository.

## ADR rule

Every significant technical decision must be written as an ADR. Existing ADRs are append-only historical records. If a decision changes, a new ADR supersedes the older one.

## Documentation rule

Stable documentation must not be silently overwritten. Evolution is recorded by dated additions, explicit supersession notes, or new sections.

## Traceability rule

Physics assumptions, approximations, units, conventions, and solver limitations must be traceable from documentation to code and tests.

## Testing rule

No feature is complete without tests, unless a written exception is accepted in the task packet. Pytest is the default validation framework.

## Merge rule

No merge to a protected branch is allowed without task completion evidence, passing required tests, documentation impact review, and audit approval.

## Handover rule

If a thread, model, or role changes, a formal handover packet is mandatory. Unstructured chat memory is not a valid handover mechanism.

## Minimal-context rule

Agents receive only the context necessary for the current task. Repository documents are the authoritative memory. Chat history is temporary working state only.

## Reproducibility rule

Commands used to validate or benchmark a task must be recorded in the task packet, report, or relevant documentation.

## Human veto rule

The human sponsor may stop, redirect, pause, or reject any work at any time.
