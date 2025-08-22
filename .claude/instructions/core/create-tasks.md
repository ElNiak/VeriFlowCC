---
description: Create an Agent OS tasks list from an approved feature spec
globs:
  - .agilevv/specs/**
  - **/*.md
alwaysApply: false
version: 1.2
encoding: UTF-8
---

# Create Tasks from Approved Spec

## Overview
With the user's approval, produce an **atomic, test-first** tasks list from the current feature spec.  
**Guardrails**
- **Only** `file-creator` writes. All other subagents read/plan/review.
- **Parallelize analysis, serialize writes** (no competing writers).
- Every major task must map to ≥1 **acceptance criterion**; record mapping in `TRACEABILITY.csv`.

<process_flow>

<variables>
  <var name="SPEC_DIR" source="choose-or-detect:last_approved_spec_dir" required="true" />
  <var name="SPEC_SLUG" source="basename:${SPEC_DIR}" required="true" />
  <var name="TODAY" source="date:YYYY-MM-DD" required="true" />
  <var name="TASKS_FILE" source="computed:${SPEC_DIR}/tasks.md" required="true" />
  <var name="TRACE_FILE" source="computed:${SPEC_DIR}/TRACEABILITY.csv" required="true" />
</variables>

<step number="0" subagent="context-fetcher" name="locate_and_read_spec">

### Step 0: Locate & Read Approved Spec

<actions>
1. If user provided a spec path, use it; otherwise **detect latest approved** spec directory under `.agilevv/specs/` (heuristic: newest folder or user confirmation).
2. READ:
   - `${SPEC_DIR}/spec.md`
   - `${SPEC_DIR}/ACCEPTANCE.md`
   - `${SPEC_DIR}/spec-lite.md` (context)
   - `${SPEC_DIR}/sub-specs/technical-spec.md` (context)
   - (if present) `${SPEC_DIR}/TRACEABILITY.csv`
3. Extract:
   - Spec Scope feature list
   - Acceptance criteria IDs (AC-xxx) and linked Requirement IDs (US-xxx)
</actions>

<outputs>
- Confirmed `SPEC_DIR` and a bullet summary of scope features & acceptance criteria.
</outputs>
</step>

<step number="1" subagent="context-fetcher" name="derive_task_skeletons">

### Step 1: Derive Task Skeletons

Create a preliminary list of **major tasks** (1–5) from Spec Scope & Acceptance, ensuring coverage.

<derivation_rules>
- Each **major task** targets a coherent feature/component or acceptance cluster.
- **First subtask** per major task: *Write tests* for that component/criterion.
- **Last subtask** per major task: *Verify tests & acceptance pass* (include command to run).
- Prefer tasks that can be completed in ≤1 day (atomicity).
- Note dependencies between tasks (data model, API, sequencing).
</derivation_rules>

<outputs>
- Proposed major tasks with titles and the acceptance criteria each covers.
</outputs>
</step>

<step number="2" subagent="file-creator" name="create_tasks_md">

### Step 2: Create tasks.md

Write `${TASKS_FILE}` with the following template and content filled from Step 1.

<file_template>
<header>
# Spec Tasks — ${SPEC_SLUG}
> Date: ${TODAY}
> Source: @${SPEC_DIR}/spec.md
</header>

<task_structure>
<major_tasks>
- count: 1–5
- format: numbered checklist
- grouping: by feature or component
</major_tasks>
<subtasks>
- count: up to 8 per major task
- format: decimal notation (1.1, 1.2)
- first_subtask: write tests
- last_subtask: verify tests & acceptance pass
</subtasks>
</task_structure>

<task_template>
## Tasks

- [ ] 1. [MAJOR_TASK_TITLE] (covers: AC-###, AC-###)
  - **Objective:** [one-sentence purpose]
  - **Definition of Done:** [what proves completion; link to acceptance/test names]
  - **Depends on:** [TSK-### or none]
  - **Estimate:** [S/M/L]
  - **Risk:** [low/med/high]
  - [ ] 1.1 Write tests for [COMPONENT/CRITERIA] (target: AC-###)
  - [ ] 1.2 [IMPLEMENTATION_STEP]
  - [ ] 1.3 [IMPLEMENTATION_STEP]
  - [ ] 1.4 Verify tests & acceptance pass (`pytest -k "<pattern>"` or equivalent)

- [ ] 2. [MAJOR_TASK_TITLE] (covers: AC-###)
  - **Objective:** …
  - **Definition of Done:** …
  - **Depends on:** …
  - **Estimate:** …
  - **Risk:** …
  - [ ] 2.1 Write tests for […]
  - [ ] 2.2 […]
  - [ ] 2.3 Verify tests & acceptance pass
</task_template>
</file_template>

<ordering_principles>
- Respect technical dependencies.
- Follow TDD: tests precede implementation steps.
- Build incrementally; prefer independent vertical slices.
</ordering_principles>

<outputs>
- Wrote `${TASKS_FILE}`
</outputs>
</step>

<step number="3" subagent="file-creator" name="update_traceability">

### Step 3: Update TRACEABILITY.csv (placeholders)

Append (or create if missing) `${TRACE_FILE}` lines mapping **Req↔Task↔Test** based on tasks you just wrote.

<file_templates>
<traceability_csv_if_missing>
requirement_id,task_id,test_id,notes
</traceability_csv_if_missing>
<traceability_rows_example>
US-001,TSK-001,test_<area>::test_<case>,"happy path"
US-001,TSK-001,test_<area>::test_<edge>,"edge case"
</traceability_rows_example>
</file_templates>

<rules>
- For every AC-xxx linked to US-xxx in `ACCEPTANCE.md`, ensure at least one row with a provisional `test_id` placeholder.
- Task IDs use **TSK-00N** aligned with the major task numbers (1 → TSK-001).
</rules>

<outputs>
- Updated `${TRACE_FILE}` with provisional mappings (idempotent append).
</outputs>
</step>

<step number="4" subagent="reviewer" name="review_tasks">

### Step 4: Reviewer Gate (Atomicity & Coverage)

Have the **reviewer** evaluate `tasks.md` for:
- Atomicity (≤1 day each), clarity, and DoD quality
- Correct TDD ordering, realistic dependencies
- Coverage: every acceptance criterion is covered by ≥1 major task

<actions>
- If issues found → summarize and **return to Step 2** to revise.
- If acceptable → proceed to Execution Readiness.
</actions>

<outputs>
- Reviewer verdict appended below (and stored in EVIDENCE).
</outputs>
</step>

<step number="5" subagent="file-creator" name="log_evidence">

### Step 5: Evidence Log

Append to `${SPEC_DIR}/EVIDENCE.md`:
- Paths produced/updated: `${TASKS_FILE}`, `${TRACE_FILE}`
- Reviewer verdict/date for tasks
- Any assumptions or open risks discovered while tasking

<outputs>
- Updated `EVIDENCE.md`
</outputs>
</step>

<step number="6" name="execution_readiness">

### Step 6: Execution Readiness Check

Present the first task summary and request confirmation to proceed.

<readiness_summary>
<present_to_user>
- Spec: ${SPEC_SLUG}
- **Task 1:** title + Objective + Depends on
- Subtasks overview (1.1 … last)
- Command to run tests for Task 1 (e.g., `pytest -k "<pattern>"`)
</present_to_user>
</readiness_summary>

<execution_prompt>
PROMPT:
"The planning is complete. The first task is:

**Task 1:** [FIRST_TASK_TITLE]
[BRIEF_DESCRIPTION_OF_TASK_1_AND_SUBTASKS]

Proceed with implementing **Task 1** now? I will focus **only** on Task 1 and its subtasks unless you specify otherwise.

Type 'yes' to proceed with Task 1, or tell me what to adjust first."
</execution_prompt>

<execution_flow>
IF user_confirms_yes:
  TRY Execute: @.claude/commands/execute-task.md   <!-- single-task flow preferred -->
  ELSE Fallback Execute: @.claude/commands/execute-tasks.md
</execution_flow>

</step>

</process_flow>