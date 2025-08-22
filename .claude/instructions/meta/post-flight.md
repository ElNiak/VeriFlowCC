---
description: Common Post-Flight Steps for AgileVerifFlowCC Instructions
globs:
  - .agilevv/**
  - **/*.md
alwaysApply: false
version: 1.2
encoding: UTF-8
---

# Post-Flight Rules

After completing all steps in a `process_flow`, perform this verification and report any discrepancies:

## A. Step & Subagent Verification
- ✅ Confirm **every numbered step** was executed exactly as instructed (including conditionals).
- ✅ Confirm each step that specified `subagent="<name>"` actually delegated to that subagent.
- ⚠️ If any step wasn’t executed as written, **explain precisely** what diverged (misread, skipped, or tool constraint) and why.
- ⚠️ If a required subagent could not be used, **explain** the limitation and the mitigation taken (or ask for permission to retry).

## B. Least-Privilege & Write Discipline
- ✅ Verify only **implementer** and/or **file-creator** performed writes; all others were read/plan/review only.
- ✅ Confirm writes were **serialized** (no overlapping concurrent edits).
- ⚠️ If any other agent wrote or if concurrency occurred, document the scope and remediate.

## C. Artifacts & Evidence Ledger
- ✅ Ensure required artifacts for the instruction exist and are **non-empty** (e.g., `spec.md`, `spec-lite.md`, `technical-spec.md`, `tasks.md`, `ACCEPTANCE.md`, `TRACEABILITY.csv`, `EVIDENCE.md`, recap/completion reports where applicable).
- ✅ Confirm `EVIDENCE.md` includes the latest:
  - File paths created/updated
  - Commands run (tests, linters, commit/push)
  - Test results summary (focused/full)
  - Reviewer verdict(s) (if applicable)
  - Commit hash(es) and PR URL (when opened)
- ⚠️ If anything is missing, add it now (via **file-creator**) or report what’s missing and why.

## D. Traceability & Consistency
- ✅ If the flow touched requirements/tasks/tests, verify `TRACEABILITY.csv` rows are present and consistent (no dangling `US-*` or `AC-*` without mapped `TSK-*`/tests).
- ✅ Confirm `tasks.md` status matches reality: `[x]` only when tests are green and (if required) reviewed; blockers marked with `⚠️` and linked to evidence.
- ✅ If roadmap changes were part of the flow, ensure `product/roadmap.md` status matches the delivered scope and test state.

## E. Branch/PR Hygiene
- ✅ Not on `main` during edits; commits use clear messages (prefer Conventional Commits).
- ✅ PR created/updated with concise description, test commands, and links (spec, tasks, evidence).
- ⚠️ If PR/branch steps weren’t performed (by design or environment), state why and provide next actions.

## F. Idempotency Check
- ✅ Re-running the instruction should **not** duplicate sections/rows. Where sentinels were used, confirm content is inside the correct bounds.
- ⚠️ If duplication occurred, de-duplicate and adjust sentinel usage.

## G. Final User Report
- Provide a short **Post-Flight Report** summarizing:
  - What was executed
  - Any deviations and fixes
  - Where evidence and artifacts live (paths/links)
  - Any explicit asks from the user to proceed/revise

<!-- POST_FLIGHT_MARKER: AgileVerifFlowCC v1.2 -->