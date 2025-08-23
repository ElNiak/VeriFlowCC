---
description: Common Pre-Flight Steps for AgileVerifFlowCC Instructions
globs:
  - .agilevv/**
  - **/*.md
alwaysApply: false
version: 1.2
encoding: UTF-8
---

# Pre-Flight Rules

- **Subagent fidelity.** For any step that specifies a subagent via `subagent="<name>"`, you **MUST** use that exact subagent to execute the step. Do **not** emulate or merge roles. If the subagent is unavailable or under-privileged, **stop** and ask the user numbered questions to resolve it.

- **Deterministic execution.** Process `<process_flow>` blocks **sequentially**. Execute **every numbered step** exactly as written before proceeding. Respect all `<conditional>` / `<decision_tree>` branches. Do not merge or skip steps.

- **Least-privilege & serialized writes.** Only **implementer** (code edits) and **file-creator** (docs/status) are allowed to write. All other subagents are **read/plan/review** only. **Serialize** write operations; never perform concurrent edits.

- **Context discipline.** Load the **minimum** content needed (e.g., `spec-lite.md`, `technical-spec.md`, `tasks.md`) and reference file paths instead of pasting large blobs. Prefer tool-backed navigation over raw dumps.

- **Environment sanity.** Before any writes:
  - Ensure you’re on a **feature branch/worktree** (not `main`); otherwise ask to switch or invoke the project’s git workflow step.
  - If a local dev server may conflict with tests/ports, check and ask permission to stop it.
  - Confirm required inputs exist for the instruction (e.g., `spec.md`, `tasks.md`, etc.).

- **Variables & time.** Capture common variables at start (e.g., `SPEC_DIR`, `SPEC_SLUG`, `TODAY`) and reuse consistently. Use the project’s timezone for dates (default **Europe/Brussels**).

- **Templates = contracts.** When a step provides a template, **use it verbatim**: preserve section order, headings, and placeholders. Fill all placeholders; do not remove required sections or add unrequested ones.

- **Subagent inputs/outputs.** For steps with `<inputs_template>` or `<outputs_template>`, **strictly adhere** to the specified XML structure. Do not add/remove fields or change formats. If a required input is unavailable, **stop** and ask numbered questions.

- **Idempotency & duplication guards.** Reruns must not create duplicate lines/sections. When appending, prefer sentinels such as:
  - `<!-- AUTO:BEGIN <section-name> -->` … `<!-- AUTO:END <section-name> -->`
    and replace within those bounds on subsequent runs.

- **Evidence-first logging.** After critical actions (tests, reviews, commits, file creation), append a brief entry to `EVIDENCE.md` with **paths, commands run, diffs/summary, and outcomes**. Redact secrets/tokens.

- **Safety constraints.** Never run destructive shell commands or network fetches unless explicitly requested by the instruction. Obey project hooks (format/lint/test gates) if present.

- **Clarification protocol.** If anything blocks correct execution, **stop and ask numbered questions**, then continue once clarified. If partial progress is possible without risk, clearly state what will be done and what remains blocked.

<!-- PRE_FLIGHT_MARKER: AgileVerifFlowCC v1.2 -->
