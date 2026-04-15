# Merge Gate Checklist

This checklist must be satisfied before merging to a protected branch.

## Scope control

- [ ] The work links to an approved task packet.
- [ ] The task packet acceptance criteria are satisfied.
- [ ] No out-of-scope files were changed without approval.

## Code quality

- [ ] Code is readable and structurally coherent.
- [ ] Public interfaces have appropriate docstrings.
- [ ] Assumptions and units are documented where relevant.
- [ ] No obvious dead code or debug leftovers remain.

## Testing

- [ ] Required pytest tests were added or updated.
- [ ] Relevant tests pass.
- [ ] Regression risk was considered.
- [ ] Validation commands are recorded.

## Documentation

- [ ] Documentation impact was reviewed.
- [ ] Required docs were updated.
- [ ] Changes respect append-over-overwrite policy.
- [ ] Any significant decision was captured in ADR if needed.

## Audit

- [ ] Auditor reviewed the task.
- [ ] Auditor recorded pass/fail notes.
- [ ] Open defects are either resolved or explicitly accepted.

## Release safety

- [ ] Branch is in a mergeable state.
- [ ] No unresolved blocker remains.
- [ ] Director or Maintainer approval is present where required.
