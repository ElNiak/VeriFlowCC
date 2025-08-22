---
description: Rules to finish off and deliver a completed task or set of tasks using AgileVerifFlowCC
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
After the current task(s) under the active spec have been completed, follow these steps to:  
1) validate with a **full test suite**, 2) fix **pre-commit** issues, 3) push & open a **PR**, 4) verify **tasks.md** & roadmap, 5) create a **recap** doc, and 6) deliver a **completion summary**.

<process_flow>

<variables>
  <var name="SPEC_DIR"      source="choose-or-detect:current_spec_dir" required="true" />
  <var name="SPEC_SLUG"     source="basename:${SPEC_DIR}"               required="true" />
  <var name="EVIDENCE_FILE" source="computed:${SPEC_DIR}/EVIDENCE.md"   required="true" />
  <var name="TASKS_FILE"    source="computed:${SPEC_DIR}/tasks.md"      required="true" />
  <var name="SPEC_LITE"     source="computed:${SPEC_DIR}/spec-lite.md"  required="false"/>
  <var name="TODAY"         source="date:YYYY-MM-DD"                    required="true" />
</variables>

<step number="0" subagent="project-manager" name="pre_flight_validation">

### Step 0: Pre-Flight Validation

Ensure we can complete safely and deterministically.

<checks>
- `${TASKS_FILE}` exists and is non-empty.
- **Focused tests** for recent tasks are green (from execute-task phase).
- `EVIDENCE.md` contains the last task’s reviewer verdict and test summary.
- We are **not** on `main`; if on `main`, Step 4 will enforce a feature branch.
</checks>

<outputs>
- Confirmed `${SPEC_DIR}`, `${TASKS_FILE}`, and `${EVIDENCE_FILE}`.
</outputs>
</step>

<step number="1" subagent="test-runner" name="test_suite_verification">

### Step 1: Run All Tests (Full Suite)

Use the `test-runner` to execute the **entire** test suite. Fix regressions before proceeding.

<instructions>
  ACTION: Use test-runner
  REQUEST: "Run the full test suite"
  OUTPUT: Commands executed, counts (run/passed/failed/xfail), and duration
  LOOP: If failures → engage debugger/fixes → re-run suite until **100% pass**
</instructions>

<test_execution>
  <order>1) Run entire suite  2) Fix failures  3) Re-run</order>
  <requirement>100% pass rate</requirement>
</test_execution>

<evidence_log>
- Append to `${EVIDENCE_FILE}`: suite command(s), summary table, failure notes (if any), and final status.
</evidence_log>

</step>

<step number="2" subagent="precommit-error-analyzer" name="precommit_error_analysis">

### Step 2: Pre-Commit Error Analysis

Analyze any pre-commit issues (formatting, linting, types, secrets, etc.) and group them **per file**.

<instructions>
  ACTION: Use precommit-error-analyzer
  REQUEST: "Analyze pre-commit errors and group by file and category"
  OUTPUT: Structured list: file → [formatter, linter, mypy, etc.]
</instructions>

<notes>
- Prefer **deterministic** tools (formatters) before style/complexity fixes.
</notes>

</step>

<step number="3" subagent="lint-type-fixer" name="precommit_fix">

### Step 3: Pre-Commit Fix (Safe Auto-Fix)

Use one `lint-type-fixer` per **independent file** to auto-fix issues.  
**Serialize** overlapping edits; you may run **in parallel** for disjoint files.

<instructions>
  ACTION: Use lint-type-fixer
  REQUEST: "Fix pre-commit issues in the provided file with minimal diffs"
  VERIFY: Re-run pre-commit on changed files; iterate until clean
</instructions>

<guardrails>
- Keep diffs minimal; no refactors beyond necessary fixes.
- If a fix changes runtime behavior, request a **reviewer** check.
</guardrails>

<evidence_log>
- Append: files fixed, categories resolved, re-run results.
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
    <message>feat(${SPEC_SLUG}): deliver task(s) — tests green, pre-commit clean</message>
    <format>Conventional Commits</format>
  </commit>
  <push>
    <target>feature branch</target>
    <remote>origin</remote>
  </push>
  <pull_request>
    <title>[${SPEC_SLUG}] Deliver feature — tests green</title>
    <description>
      - Summary of changes
      - How to test (commands)
      - Links: spec.md, EVIDENCE.md, tasks.md
    </description>
  </pull_request>
</commit_process>

<evidence_log>
- Append PR URL and commit hash to `${EVIDENCE_FILE}`.
</evidence_log>

</step>

<step number="5" subagent="project-manager" name="tasks_list_check">

### Step 5: Tasks Completion Verification

Confirm `tasks.md` is accurate: completed tasks `[x]`, or documented blockers.

<instructions>
  ACTION: Use project-manager
  REQUEST: |
    Verify task completion in ${TASKS_FILE}:
    - Mark completed tasks `[x]` **only** if verified (tests green + reviewed)
    - Ensure any incomplete tasks include a ⚠️ blocker note with a brief reason & link to evidence
</instructions>

<completion_criteria>
  <valid_states>- Completed `[x]`  ·  Blocked with ⚠️ reason</valid_states>
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
  <update_when>
    - Spec implements the roadmap feature end-to-end
    - All related tasks completed
    - Full test suite passes
  </update_when>
</roadmap_criteria>

<instructions>
  ACTION: If criteria met, mark the roadmap entry `[x]` and reference the PR.
</instructions>

</step>

<step number="7" subagent="file-creator" name="document_recap">

### Step 7: Create Recap Document

Create a recap file in `.agilevv/recaps/` summarizing what was delivered.

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
- PR: [PR_URL]
</recap_template>

<evidence_log>
- Append recap path to `${EVIDENCE_FILE}`.
</evidence_log>

</step>

<step number="8" subagent="project-manager" name="completion_summary">

### Step 8: Completion Summary (for the user)

Produce a succinct, emoji-sectioned summary.

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
1) [browser step 1]  
2) [browser step 2]

## 📦 Pull Request
[PR_URL]
</summary_template>

<instructions>
  ACTION: Create and present the summary message; copy to PR description if useful.
</instructions>

</step>

<step number="9" subagent="project-manager" name="completion_notification">

### Step 9: Completion Notification (Cross-Platform)

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