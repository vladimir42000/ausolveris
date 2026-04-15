# AI Project Operating System — Human Operator HOWTO

This package is a deployable governance backbone for an AI-assisted Python project, especially a scientific or engineering codebase with multiple AI roles, frequent thread handovers, and strict quality control.

It is designed so a human operator can launch work with minimal improvisation and keep direction, documentation, and code quality under control.

## Purpose

This operating system is meant to solve five recurring problems in AI-assisted development:

1. Chat threads saturate and context gets lost.
2. One agent starts doing too many roles and project direction drifts.
3. Code gets produced faster than it gets validated.
4. Documentation gets overwritten instead of preserved.
5. Token costs grow because too much history is passed around.

## What is included

- `CONSTITUTION.md` — non-changing project rules.
- `ROLE_MODEL.md` — exact team composition and boundaries.
- `MODEL_ROUTING_POLICY.md` — which model to use for which role.
- `DOC_POLICY.md` — append-only and history-preserving documentation rules.
- `HANDOVER_PROTOCOL.md` — mandatory thread-to-thread transfer discipline.
- `MERGE_GATE_CHECKLIST.md` — release and merge approval gate.
- `PHASE_PLAN_TEMPLATE.md` — structure for major phases.
- `REPORT_TEMPLATE.md` — periodic management report to Director.
- `templates/TASK_PACKET_TEMPLATE.md` — exact task handout to development agents.
- `templates/ADR_TEMPLATE.md` — architecture decision record template.
- `templates/STATUS_SNAPSHOT_TEMPLATE.md` — compact periodic project state snapshot.
- `templates/AGENT_PROMPT_PACK.md` — compact prompt blocks for each role.
- `docs/adr/README.md` — ADR folder usage notes.

## Recommended initial team

The operating model assumes six roles:

1. Director.
2. Product Physicist.
3. Spec Lead.
4. Developer.
5. Auditor.
6. Documentation Steward.

If the project is very small, Director and Product Physicist can be the same human. If the team is under heavy budget pressure, Documentation Steward can be partially merged into Spec Lead, but only if append-only discipline is still respected.

## Recommended tool allocation

### Lowest-cost effective setup

- Director: human using subscription chats.
- Product Physicist: human plus one conservative AI thread.
- Spec Lead: stronger reasoning model, used only for phase specs and reviews.
- Developer: DeepSeek-class model in Aider.
- Auditor: stronger model for milestone review, cheap model for routine checks.
- Documentation Steward: cheap model or human.

## Folder deployment in your real repository

Copy the following files into the root of the real project repository:

- `CONSTITUTION.md`
- `ROLE_MODEL.md`
- `MODEL_ROUTING_POLICY.md`
- `DOC_POLICY.md`
- `HANDOVER_PROTOCOL.md`
- `MERGE_GATE_CHECKLIST.md`
- `PHASE_PLAN_TEMPLATE.md`
- `REPORT_TEMPLATE.md`
- `templates/`
- `docs/adr/`

Recommended final repository structure:

```text
repo/
├── CONSTITUTION.md
├── ROLE_MODEL.md
├── MODEL_ROUTING_POLICY.md
├── DOC_POLICY.md
├── HANDOVER_PROTOCOL.md
├── MERGE_GATE_CHECKLIST.md
├── PHASE_PLAN.md
├── REPORT_TEMPLATE.md
├── STATUS.md
├── CHANGELOG.md
├── ARCHITECTURE.md
├── API_SPEC.md
├── YAML_SCHEMA.md
├── TEST_STRATEGY.md
├── USER_GUIDE.md
├── DEVELOPER_GUIDE.md
├── PHYSICS_FOUNDATIONS.md
├── docs/
│   └── adr/
├── templates/
├── src/
├── tests/
└── benchmarks/
```

## Human operator deployment steps

### Step 1 — Create the repository skeleton

Create the repository and copy this governance pack into it.

### Step 2 — Freeze the core rules

Before any coding starts, read and accept:

- `CONSTITUTION.md`
- `ROLE_MODEL.md`
- `DOC_POLICY.md`
- `HANDOVER_PROTOCOL.md`

Do not begin implementation before these are accepted.

### Step 3 — Name the first phase

Create `PHASE_PLAN.md` from `PHASE_PLAN_TEMPLATE.md` and define:

- project mission,
- v1 scope,
- non-goals,
- first benchmark problems,
- acceptance criteria.

### Step 4 — Start the ADR log

Create the first ADRs:

- ADR-001: repository governance model,
- ADR-002: language/runtime/toolchain choice,
- ADR-003: initial solver scope,
- ADR-004: documentation and append-only policy.

### Step 5 — Configure the AI roles

Create one prompt/session per role using `templates/AGENT_PROMPT_PACK.md`.

Recommended isolation:

- One persistent thread for Spec Lead.
- One Aider coding session bound to the active branch.
- One separate Auditor thread.
- One documentation-maintenance thread if not human-managed.

Never let the Developer and Auditor share the same working thread.

### Step 6 — Install Aider workflow

Typical coding loop:

1. Human or Spec Lead prepares a task packet.
2. Developer receives only the task packet and necessary files.
3. Developer edits code in Aider on a feature branch.
4. Developer runs tests and updates docs required by the task.
5. Auditor checks the task against the merge gate.
6. Director approves next step.

### Step 7 — Use branch discipline

Recommended branches:

- `main` — protected, releasable only.
- `feature/<phase>-<topic>` — implementation.
- `docs/<topic>` — documentation-heavy work if needed.
- `audit/<topic>` — optional audit investigations.

No direct push to `main`.

### Step 8 — Enforce handover discipline

When a thread becomes saturated or a role changes hands:

- create a handover packet,
- update status snapshot,
- record any decisions as ADRs,
- ensure the next agent receives only the minimal relevant context.

## Token economy rules for the human operator

These are the main money-saving rules:

- Keep each task narrow.
- Never attach the whole repository if only two files matter.
- Use templates instead of free-form narrative.
- Force short answers unless explanation is needed.
- Treat the repo as memory; do not rely on chat history.
- Prefer diffs, checklists, commands, and file paths over prose.
- Reset or clear context between unrelated tasks.

## Operating rhythm

Recommended cadence:

- Daily or per work block: task packet + code + tests + handover.
- Every few tasks: auditor review.
- Weekly or per milestone: management report to Director.
- Every architecture change: ADR entry.
- Every release candidate: status snapshot + benchmark review.

## Minimal start procedure

If you want to start immediately:

1. Read `CONSTITUTION.md`.
2. Read `ROLE_MODEL.md`.
3. Fill `PHASE_PLAN_TEMPLATE.md` into `PHASE_PLAN.md`.
4. Create ADR-001 to ADR-004.
5. Start one Spec Lead thread and one Developer Aider session.
6. Issue the first task packet.
7. Require pytest and doc updates on first merge.

## Suggested first real tasks after governance setup

- Define v1 user problems.
- Define v1 solver non-goals.
- Freeze repository structure.
- Freeze YAML top-level schema concept.
- Define benchmark set for horns and waveguides.
- Define testing strategy for numerical regression.

## Final operator rule

If something important exists only in chat, it does not exist.
