---
description: Rules to finish off and deliver to user a set of tasks that have been completed using Agent OS / AgileVerifFlowCC
globs:
  - .agilevv/specs/**
  - .agilevv/product/**
  - .agilevv/recaps/**
  - **/*.md
alwaysApply: false
version: 1.2
encoding: UTF-8
---

# Task Completion Rules

## Overview

After **all tasks** in the current spec are completed, follow these steps to:

1. validate with a **full test suite**, 2) resolve **pre-commit** issues, 3) commit/push and open a **PR**, 4) verify **tasks.md** and optionally update **roadmap.md**, 5) create a **recap** and a **completion report** in the spec folder, and 6) present a concise summary.

**Guardrails**

- **Only** `implementer` (code changes) and `file-creator` (docs/status) write to disk.
- **Parallelize analysis, serialize writes** (avoid concurrent edits).
- Append **evidence** to `EVIDENCE.md` at each major step.

<process_flow>

<variables>
  <var name="SPEC_DIR"        source="choose-or-detect:current_spec_dir"         required="true" />
  <var name="SPEC_SLUG"       source="basename:${SPEC_DIR}"                      required="true" />
  <var name="TASKS_FILE"      source="computed:${SPEC_DIR}/tasks.md"             required="true" />
  <var name="EVIDENCE_FILE"   source="computed:${SPEC_DIR}/EVIDENCE.md"          required="true" />
  <var name="SPEC_LITE"       source="computed:${SPEC_DIR}/spec-lite.md"         required="false" />
  <var name="ROADMAP_FILE"    source="path:.agilevv/product/roadmap.md"          required="false" />
  <var name="COMPLETION_FILE" source="computed:${SPEC_DIR}/COMPLETION.md"        required="true" />
  <var name="TODAY"           source="date:YYYY-MM-DD"                           required="true" />
</variables>

<step number="0" subagent="project-manager" name="pre_flight_validation">

### Step 0: Pre-Flight Validation

Ensure the environment is safe and artifacts are present.

<checks>
- `${TASKS_FILE}` exists and is non-empty.
- `EVIDENCE.md` exists; last task entry contains reviewer verdict + test summary.
- We are **not** on `main`; if on main, Step 4 will enforce a feature branch/worktree.
</checks>

<outputs>
- Confirmed `${SPEC_DIR}`, `${TASKS_FILE}`, `${EVIDENCE_FILE}`.
</outputs>
</step>

<step number="1" subagent="test-runner" name="test_suite_verification">

### Step 1: Run All Tests (Full Suite)

Use the `test-runner` to run the **entire** test suite. Fix regressions before proceeding.

<instructions>
  ACTION: Use test-runner
  REQUEST: "Run the full test suite"
  OUTPUT: Commands executed; counts (run/passed/failed/xfail); duration
  LOOP: If failures → engage fixes (implementer/debugger) → re-run until **100% pass**
</instructions>

<test_execution>
<order>1. Run entire suite 2. Fix failures 3. Re-run</order>
<requirement>100% pass rate</requirement>
</test_execution>

<evidence_log>

- Append to `${EVIDENCE_FILE}`: suite command(s), table summary, failure notes (if any), final status.
  </evidence_log>

</step>

<step number="2" subagent="precommit-error-analyzer" name="precommit_error_analysis">

### Step 2: Pre-commit Error Analysis

Analyze any pre-commit issues and group them **per file** (formatting, linting, types, secrets, etc.).

<instructions>
  ACTION: Use precommit-error-analyzer
  REQUEST: "Analyze pre-commit errors and group by file & category"
  OUTPUT: Structured list: file → [formatter, linter, mypy, secrets, …]
</instructions>

<notes>
- Prefer deterministic fixes (formatters) before style/complexity changes.
</notes>

</step>

<step number="3" subagent="lint-type-fixer" name="precommit_fix">

### Step 3: Pre-commit Fix (Safe, Targeted)

Use `lint-type-fixer` **per independent file** to auto-fix issues.  
**Serialize** overlapping edits; parallelize disjoint files if safe.

<instructions>
  ACTION: Use lint-type-fixer
  REQUEST: "Fix pre-commit issues in this file with minimal diffs"
  VERIFY: Re-run pre-commit on changed files; iterate until clean
</instructions>

<guardrails>
- Keep diffs minimal; avoid refactors beyond necessary fixes.
- If a fix might change runtime behavior, request an explicit reviewer check.
</guardrails>

<evidence_log>

- Append: files fixed, categories resolved, re-run results to `${EVIDENCE_FILE}`.
  </evidence_log>

</step>

<step number="4" subagent="git-workflow" name="git_workflow">

### Step 4: Git Workflow (Commit → Push → PR)

Create a commit, push to remote, and open/update the **Pull Request**.

<instructions>
  ACTION: Use git-workflow
  REQUEST: |
    Prepare PR for spec: ${SPEC_SLUG}
    - Ensure we are on a feature branch/worktree (not main)
    - Stage only relevant files
    - Commit with conventional message
    - Push branch to origin
    - Open or update PR targeting default branch
    - Add concise description and link to spec & evidence
  WAIT: Capture PR URL
</instructions>

<commit_process>
<commit>
<message>feat(${SPEC_SLUG}): deliver spec tasks — tests green, pre-commit clean</message>
    <format>Conventional Commits</format>
  </commit>
  <push>
    <target>feature branch</target>
    <remote>origin</remote>
  </push>
  <pull_request>
    <title>[${SPEC_SLUG}] Deliver feature — tests green</title>
<description> - Summary of changes - How to test (commands) - Links: @${SPEC_DIR}/spec.md, @${TASKS_FILE}, @${EVIDENCE_FILE}
</description>
</pull_request>
</commit_process>

<outputs>
- `PR_URL` (persist for later steps).
</outputs>

<evidence_log>

- Append PR URL and commit hash to `${EVIDENCE_FILE}`.
  </evidence_log>

</step>

<step number="5" subagent="project-manager" name="tasks_list_check">

### Step 5: Tasks Completion Verification

Confirm `tasks.md` is accurate: completed items `[x]`, or documented blockers.

<instructions>
  ACTION: Use project-manager
  REQUEST: |
    Verify task completion in ${TASKS_FILE}:
    - Mark completed tasks `[x]` **only** if verified (tests green + reviewed)
    - Ensure any incomplete tasks include a ⚠️ blocker note with reason & link to evidence
</instructions>

<completion_criteria>
<valid_states>- Completed `[x]` · Blocked with ⚠️ reason</valid_states>
<invalid_state>- Unmarked without blocker documentation</invalid_state>
</completion_criteria>

<evidence_log>

- Append a short “task status snapshot” to `${EVIDENCE_FILE}`.
  </evidence_log>

</step>

<step number="6" subagent="project-manager" name="roadmap_progress_check">

### Step 6: Roadmap Progress Update (Conditional)

Update `@.agilevv/product/roadmap.md` **only if** the spec fully completes a roadmap item.

<conditional_execution>
<preliminary_check>
IF tasks clearly do **not** complete a roadmap item → SKIP
ELSE analyze mapping from spec to roadmap
</preliminary_check>
</conditional_execution>

<roadmap_criteria>
<update_when> - Spec implements the roadmap feature end-to-end - All related tasks completed - Full test suite passes
</update_when>
</roadmap_criteria>

<instructions>
  ACTION: If criteria met, mark roadmap entry `[x]` and reference `${PR_URL}`.
</instructions>

</step>

<step number="7" subagent="file-creator" name="document_recap">

### Step 7: Create Recap Document

Create a recap in `.agilevv/recaps/` summarizing what was delivered.

<file_creation>
<location>.agilevv/recaps/</location>
<naming>${SPEC_SLUG}.md</naming>
<format>markdown</format>
</file_creation>

<recap_template>

# [${TODAY}] Recap: ${SPEC_SLUG}

This recaps what was delivered for the spec at @${SPEC_DIR}/spec.md.

## Recap

[1 paragraph + bullets of completed functionality]

## Context

[Paste or paraphrase the summary from spec-lite.md, if present]

## Links

- Spec: @${SPEC_DIR}/spec.md
- Tasks: @${TASKS_FILE}
- Evidence: @${EVIDENCE_FILE}
- PR: ${PR_URL}
  </recap_template>

<evidence_log>

- Append recap path to `${EVIDENCE_FILE}`.
  </evidence_log>

</step>

<step number="8" subagent="file-creator" name="completion_report">

### Step 8: Create Completion Report (in Spec Folder)

Create `${COMPLETION_FILE}` inside the spec folder to serve as the final, immutable report.

<report_template>

# Completion Report — ${SPEC_SLUG}

_Date: ${TODAY}_

## Summary

[2–4 sentences: what changed, why, and user impact.]

## Verification Evidence

- Full test suite: **pass** (include counts & command)
- Pre-commit: **clean** (tools run)
- Reviewer verdicts: [summary with dates]
- Key commits: [hashes/subjects]

## How to Validate

- Commands to run locally
- Any browser steps (if applicable)

## Links

- PR: ${PR_URL}
- Spec: @${SPEC_DIR}/spec.md
- Tasks: @${TASKS_FILE}
- Evidence: @${EVIDENCE_FILE}
- Recap: @.agilevv/recaps/${SPEC_SLUG}.md
  </report_template>

<outputs>
- Wrote `${COMPLETION_FILE}`
</outputs>

<evidence_log>

- Append completion report path to `${EVIDENCE_FILE}`.
  </evidence_log>

</step>

<step number="9" subagent="project-manager" name="completion_summary">

### Step 9: Completion Summary (for the user)

Produce a succinct, emoji-sectioned summary message.

<summary_template>

## ✅ What’s been done

1. **[FEATURE_1]** — [one-sentence]
2. **[FEATURE_2]** — [one-sentence]

## 🧪 Tests

- Full suite passed (run/passed/failed: N/N/0)
- Commands: `pytest -q` …

## ⚠️ Issues encountered

[ONLY_IF_APPLICABLE]

- **[ISSUE]** — [description & status]

## 👀 Ready to test

[ONLY_IF_APPLICABLE]

1. [browser step 1]
2. [browser step 2]

## 📦 Pull Request

{PR_URL}
</summary_template>

<instructions>
  ACTION: Present this summary; also copy into the PR description if useful.
</instructions>

</step>

<step number="10" subagent="project-manager" name="completion_notification">

### Step 10: Completion Notification (Cross-Platform)

Play a completion sound **if available**; otherwise show a visual cue.

<notification_commands>
<macOS>afplay /System/Library/Sounds/Glass.aiff || true</macOS>
<linux>paplay /usr/share/sounds/freedesktop/stereo/complete.oga || aplay /usr/share/sounds/alsa/Front_Center.wav || true</linux>
<windows>powershell -c "[console]::beep(880,250); [console]::beep(660,250)"</windows>
</notification_commands>

<instructions>
  ACTION: Try the platform-appropriate command; ignore failures gracefully.
</instructions>

</step>

</process_flow>
