---
description: Rules to initiate execution of a set of tasks using AgileVerifFlowCC
globs:
  - .agilevv/specs/**
  - .agilevv/product/**
  - **/*.md
alwaysApply: false
version: 1.2
encoding: UTF-8
---

# Task Execution Rules

## Overview
Initiate execution of one or more tasks for a given spec.  
**Guardrails**
- **Parallelize analysis, serialize writes.** Only `Implementer` (inside execute-task flow) or `file-creator` writes to disk.
- Work on a **feature branch/worktree**, never on `main`.
- After each parent task, **log evidence** and **commit**; keep the process resumable.

<process_flow>

<variables>
  <var name="SPEC_DIR" source="choose-or-detect:current_or_latest_spec_dir" required="true" />
  <var name="TASKS_FILE" source="computed:${SPEC_DIR}/tasks.md" required="true" />
  <var name="SPEC_LITE" source="computed:${SPEC_DIR}/spec-lite.md" required="false" />
  <var name="TECH_SPEC" source="computed:${SPEC_DIR}/sub-specs/technical-spec.md" required="false" />
  <var name="MISSION" source="path:.agilevv/product/mission-lite.md" required="false" />
  <var name="EVIDENCE" source="computed:${SPEC_DIR}/EVIDENCE.md" required="true" />
</variables>

<step number="0" subagent="context-fetcher" name="pre_flight_validation">

### Step 0: Pre-Flight Validation

Verify we’re ready to execute.

<checks>
- `tasks.md` exists and is non-empty.
- Optional but recommended: `spec-lite.md`, `sub-specs/technical-spec.md` present.
- Ensure we are **not** on `main`. If on `main`, Step 4 will create/switch to feature branch.
</checks>

<outputs>
- Detected `SPEC_DIR` and `TASKS_FILE`.
- Short summary: number of parent tasks, first uncompleted parent task number.
</outputs>
</step>

<step number="1" name="task_assignment">

### Step 1: Task Assignment

Identify which tasks to execute from `.agilevv/specs`, using an explicit selection or defaulting to the **next uncompleted parent task**.

<task_selection>
<explicit>user provides exact parent task numbers (e.g., 2, 5)</explicit>
<implicit>read `${TASKS_FILE}` and pick the first unchecked parent task</implicit>
</task_selection>

<instructions>
ACTION: List candidate parent tasks and **confirm** with user.  
DEFAULT: Select next uncompleted parent task (branch/worktree name may be used as a hint).  
CONFIRM: Echo chosen task numbers and titles before proceeding.
</instructions>

<outputs>
- Confirmed list: `[parent_task_numbers]` with titles.
</outputs>
</step>

<step number="2" subagent="context-fetcher" name="context_analysis">

### Step 2: Context Analysis

Gather **minimal** context for execution.

<instructions>
ACTION: Use `context-fetcher` to:
  - LOAD: `${TASKS_FILE}` (always)
  - IF not already in context:
      - LOAD: `${MISSION}` (product pitch)
      - LOAD: `${SPEC_LITE}` (spec summary)
      - LOAD: `${TECH_SPEC}` (technical approach)
PROCESS: Summarize the above into ≤8 bullets (dependencies, risky areas, commands to run tests).
</instructions>

<outputs>
- Context bullets (≤8) with references to file paths.
</outputs>
</step>

<step number="3" subagent="systems-checker" name="development_server_check">

### Step 3: Check for Development Server

Detect a running dev server (common ports/process names). Ask permission to stop if found.

<server_check_flow>
<if_running>
ASK: “A development server is running. Shut it down before proceeding? (yes/no)”
WAIT for response; IF yes, stop it safely; IF no, warn about potential conflicts and proceed.
</if_running>
<if_not_running>
PROCEED immediately.
</if_not_running>
</server_check_flow>

<instructions>
ACTION: Check for local dev server; ask permission **only** if running.
</instructions>
</step>

<step number="4" subagent="git-workflow" name="git_branch_management">

### Step 4: Git Branch/Worktree Management

Use `git-workflow` to ensure isolation on a feature branch/worktree.

<instructions>
REQUEST:
  """
  Prepare branch/worktree for spec: ${SPEC_DIR}
  - Branch name = spec folder name without date prefix (e.g., 2025-03-15-password-reset → password-reset)
  - Create worktree if configured; otherwise checkout branch
  - Stash or commit uncommitted changes as WIP (never lose work)
  - Ensure we’re **not** on main
  """
WAIT: for completion and report current branch/worktree path.
</instructions>

<outputs>
- Active branch/worktree and clean status (or WIP commit hash).
</outputs>
</step>

<step number="5" name="task_execution_loop">

### Step 5: Task Execution Loop

Execute the assigned **parent tasks** and their subtasks using `@.claude/instructions/core/execute-task.md`.

<execution_flow>
LOAD once: @.claude/instructions/core/execute-task.md

FOR each `parent_task_number` in confirmed list:
  EXECUTE `execute-task.md` with:
    - parent_task_number
    - include all of its subtasks
  WAIT for completion (execute-task handles Implementer/Reviewer/Test-Runner gates)
  UPDATE status in `${TASKS_FILE}` via `file-creator` (check off the completed parent task and subtasks)
  APPEND evidence to `${EVIDENCE}`:
    - Completed task number/title
    - Commit hash(es) produced
    - Test command(s) run and summary (pass/fail count)
  COMMIT changes:
    - Message: "feat(${parent_task_number}): complete [title] — evidence logged"
END FOR
</execution_flow>

<loop_logic>
<continue_conditions>
- More assigned parent tasks remain
- User has not requested stop
</continue_conditions>
<exit_conditions>
- All assigned parent tasks completed
- User requests early termination
- Blocking issue prevents continuation (record in EVIDENCE and stop)
</exit_conditions>
</loop_logic>

<task_status_check>
AFTER each parent task:
- Re-scan `${TASKS_FILE}` for remaining unchecked parent tasks.
- If assigned set is complete, proceed to Step 6.
</task_status_check>

<instructions>
ACTION: Load `execute-task.md` once; reuse for each parent task.
SERIALIZE: Execute tasks one at a time to avoid merge conflicts.
AUDIT: Log evidence + commit after each parent task.
</instructions>
</step>

<step number="6" name="complete_tasks">

### Step 6: Run Task-Completion Steps

When assigned tasks are done, run the standard completion flow.

<instructions>
LOAD once: @.claude/instructions/core/complete-tasks.md  
ACTION: Execute all steps in `complete-tasks.md` process_flow.
APPEND to `${EVIDENCE}` a final summary:
  - Completed parent tasks
  - Remaining open items (if any)
  - Final commit hash and branch
</instructions>

<outputs>
- Completion artifacts as defined by `complete-tasks.md`.
- Final evidence summary appended.
</outputs>
</step>

</process_flow>