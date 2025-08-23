---
description: Rules to execute a task and its sub-tasks using AgileVerifFlowCC
globs:
  - .agilevv/specs/**
  - .agilevv/standards/**
  - **/*.md
alwaysApply: false
version: 1.2
encoding: UTF-8
---

# Task Execution Rules

## Overview

Execute a specific parent task and its subtasks using a **TDD** workflow.  
**Guardrails**

- **Only** `implementer` (code changes) and `file-creator` (docs/status) write to disk.
- **Parallelize analysis, serialize writes.** Run on a feature branch/worktree.
- Log **evidence** (diffs, commands, test results, commit hashes) as you go.

<process_flow>

<variables>
  <var name="SPEC_DIR" source="choose-or-detect:current_spec_dir" required="true" />
  <var name="TASKS_FILE" source="computed:${SPEC_DIR}/tasks.md" required="true" />
  <var name="EVIDENCE_FILE" source="computed:${SPEC_DIR}/EVIDENCE.md" required="true" />
  <var name="TRACE_FILE" source="computed:${SPEC_DIR}/TRACEABILITY.csv" required="true" />
  <var name="PARENT_TASK_NUMBER" source="input:param(parent_task_number)" required="true" />
</variables>

<step number="0" subagent="context-fetcher" name="pre_flight_validation">

### Step 0: Pre-Flight Validation

Validate inputs and environment before writing anything.

<checks>
- `${TASKS_FILE}` exists and is non-empty
- `${PARENT_TASK_NUMBER}` exists in `${TASKS_FILE}`
- Optional but recommended present: `${SPEC_DIR}/spec-lite.md`, `${SPEC_DIR}/sub-specs/technical-spec.md`
</checks>

<git_policy>

- If on `main`, request branch switch (or invoke `git-workflow` to prepare feature branch).
  </git_policy>

<outputs>
- Confirmed `${SPEC_DIR}`, `${TASKS_FILE}`, and `${PARENT_TASK_NUMBER}`
- Count of subtasks under the parent task
</outputs>
</step>

<step number="1" name="task_understanding">

### Step 1: Task Understanding

Read and analyze the **parent task** `${PARENT_TASK_NUMBER}` and all its subtasks from `tasks.md`.

<task_analysis>
<read_from_tasks_md>

- Parent task title & objective
- All subtask descriptions (1.x … n.x)
- Dependencies & Definition of Done
- Acceptance criteria covered (AC-###)
  </read_from_tasks_md>
  </task_analysis>

<instructions>
  ACTION: Summarize scope, DoD, dependencies, AC coverage in ≤8 bullets.
  OUTPUT: A one-paragraph execution plan (tests → impl → verify).
</instructions>

</step>

<step number="2" subagent="context-fetcher" name="technical_spec_review">

### Step 2: Technical Specification Review

Use `context-fetcher` to extract only the sections of `technical-spec.md` that support this task.

<selective_reading>
<search_technical_spec>
FIND sections related to:

- This feature’s functionality & data boundaries
- Implementation approach and interfaces
- Integration points
- Performance criteria/SLOs
  </search_technical_spec>
  </selective_reading>

<instructions>
  ACTION: Extract **only** details needed for the current task; ignore unrelated areas.
  OUTPUT: ≤6 bullets mapping spec details → impacted files/symbols.
</instructions>

</step>

<step number="3" subagent="context-fetcher" name="best_practices_review">

### Step 3: Best Practices Review

Pull relevant guidance from `.agilevv/standards/best-practices.md`.

<selective_reading>
<search_best_practices>
FIND sections relevant to:

- Current tech stack & feature type
- Testing approach (unit/integration/property/fuzz)
- Code organization & error handling
- Security & performance gotchas (if applicable)
  </search_best_practices>
  </selective_reading>

<if>
IF none found:
launch standard-analyser agent to infer best practices from repo context.
</if>

<outputs>
- Checklist of applicable practices to follow for this task.
</outputs>

</step>

<step number="4" subagent="context-fetcher" name="code_style_review">

### Step 4: Code Style Review

Load style rules from `.agilevv/standards/code-style.md` for languages/files touched.

<selective_reading>
<search_code_style>
FIND style rules for:

- Languages/file types in scope
- Component patterns involved
- Test style guidelines
  </search_code_style>
  </selective_reading>

<outputs>
- Short list of style constraints (naming, structure, docstrings, linting).
</outputs>

</step>

<step number="5" subagent="implementer" name="task_execution">

### Step 5: Task & Subtask Execution (TDD, Implementer-only writes)

The `implementer` performs code edits; all others read/plan/review.  
Follow the **test-first** ordering, then implementation, then verification.

<typical_task_structure>
<first_subtask>Write tests for the feature (unit/integration/edge cases)</first_subtask>
<middle_subtasks>Implement functionality in small steps; keep tests green; refactor</middle_subtasks>
<final_subtask>Verify all tests pass; prepare for review</final_subtask>
</typical_task_structure>

<execution_order>
<subtask_1_tests>

- Create tests for the parent feature (target AC-###)
- Run tests to confirm expected failures
  </subtask_1_tests>

  <middle_subtasks_implementation>

- Implement per subtask (2.x … n-1.x)
- After each edit: run the **relevant** tests
- Keep diffs small; update docs if needed
  </middle_subtasks_implementation>

  <final_subtask_verification>

- Ensure all task-specific tests pass locally
- Prepare notes for reviewer (files/symbols changed)
  </final_subtask_verification>
  </execution_order>

<instructions>
  ACTION: Execute subtasks in order; mark each subtask draft-complete locally (do not tick in `tasks.md` yet).
  OUTPUT: Provide a concise changelog (files touched, symbols changed).
</instructions>

</step>

<step number="6" subagent="test-runner" name="task_test_verification">

### Step 6: Focused Test Verification (Test-Runner)

Run **only** tests relevant to this parent task.

<focused_test_execution>
<run_only>

- New/updated tests for this feature
- Directly related existing tests
  </run_only>
  <skip>
- Full suite (run later in multi-task flow)
  </skip>

</focused_test_execution>

<final_verification>
IF failures:

- Engage **debugger** to isolate and fix minimal changes
- Re-run focused tests until green
  ELSE:
- Confirm task-specific tests pass
  </final_verification>

<instructions>
  ACTION: Request test-runner to execute the narrowed set; report command(s) used and results.
  OUTPUT: Table of tests run with pass/fail counts.
</instructions>

</step>

<step number="7" subagent="reviewer" name="review_gate">

### Step 7: Reviewer Gate (Quality/Security/Perf)

Run **reviewer** on the diffs produced by Step 5.

<review_checklist>

- DRY, clarity, error handling, input validation
- Test adequacy (happy paths + edge cases)
- Security: secrets, injections, path traversal (if relevant)
- Performance considerations and obvious hotspots
  </review_checklist>

<gate>
IF reviewer **blocks**:
  - Summarize actionable issues
  - Return to Step 5 (implementer) → Step 6 (tests) → re-review
IF reviewer **approves**:
  - Proceed to completion
</gate>

<outputs>
- Reviewer verdict and line-level notes.
</outputs>

</step>

<step number="8" subagent="file-creator" name="traceability_and_evidence">

### Step 8: Traceability & Evidence Logging

Update **TRACEABILITY.csv** and append to **EVIDENCE.md**.

<traceability_update>

- For each acceptance criterion (AC-###) covered by this task:
  - Add or update mapping rows: `US-xxx,TSK-${PARENT_TASK_NUMBER:03d},test_<area>::test_<case>,"notes"`
- Keep idempotent (avoid duplicate rows).
  </traceability_update>

<evidence_append>
Add a section to `${EVIDENCE_FILE}`:

- Parent task number/title
- Files changed (paths)
- Commands run (tests, linters)
- Test summary (how many run/passed/failed)
- Reviewer verdict (approve/block + date)
- Commit hash(es) or WIP
  </evidence_append>

<outputs>
- Updated `${TRACE_FILE}` and `${EVIDENCE_FILE}`
</outputs>

</step>

<step number="9" subagent="file-creator" name="task_status_updates">

### Step 9: Task Status Updates (tasks.md)

Update `${TASKS_FILE}` **only after** Reviewer approval and focused tests pass.

<update_format>
<completed>

- [x] <parent task line> (append short note: “tests green; reviewed”)
  - [x] 1.1 … (tests)
  - [x] 1.2 …
  - [x] 1.3 …
        </completed>

<incomplete>
- [ ] <subtask line>  (if anything remains)
</incomplete>
<blocked>
- [ ] <subtask line>
  ⚠️ Blocking issue: <description> (link to EVIDENCE section)
</blocked>
</update_format>

<blocking_criteria>

- Max 3 serious attempts before marking ⚠️ blocked
- Record reproduction steps and logs in EVIDENCE
  </blocking_criteria>

<outputs>
- `${TASKS_FILE}` updated with accurate status checkboxes.
</outputs>

</step>

<step number="10" name="finalize_and_handoff">

### Step 10: Finalize & Handoff

Optionally commit now (if not already done by hooks) and hand off to the task completion routine.

<commit_policy>

- Commit message: `feat(task ${PARENT_TASK_NUMBER}): complete <title> — tests green, reviewed`
- Ensure no unrelated files are staged.
  </commit_policy>

<instructions>
LOAD once: @.claude/instructions/core/complete-task.md  
ACTION: Execute all steps in `complete-task.md` process_flow.
</instructions>

<outputs>
- Completion artifacts as defined by `complete-task.md`
</outputs>

</step>

</process_flow>
