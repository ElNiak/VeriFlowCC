---
description: Spec Creation Rules for AgileVerifFlowCC
globs:
  - .agilevv/product/**
  - .agilevv/specs/**
  - **/*.md
  - **/*.py
  - **/*.ts
alwaysApply: false
version: 1.2
encoding: UTF-8
---

# Spec Creation Rules

## Overview

Generate detailed, **evidence-first** feature specifications aligned with the product mission and roadmap.  
**Guardrails:**

- **Parallelize analysis, serialize writes.** Only the **file-creator** subagent writes to disk.
- Use least-privilege tools; other subagents **read/ask/plan** only.
- Every step that creates or approves artifacts must **list file paths** it produced/validated.

<process_flow>

<variables>
  <var name="SPEC_DATE" source="step:4.output.date" required="true" />
  <var name="SPEC_SLUG" source="computed:kebab-case short descriptive name (≤5 words)" required="true" />
  <var name="SPEC_DIR" source="computed:.agilevv/specs/${SPEC_DATE}-${SPEC_SLUG}" required="true" />
</variables>

<artifacts_required>

- ${SPEC_DIR}/spec.md
- ${SPEC_DIR}/spec-lite.md
- ${SPEC_DIR}/sub-specs/technical-spec.md
- (conditional) ${SPEC_DIR}/sub-specs/database-schema.md
- (conditional) ${SPEC_DIR}/sub-specs/api-spec.md
- ${SPEC_DIR}/ACCEPTANCE.md
- ${SPEC_DIR}/TRACEABILITY.csv
- ${SPEC_DIR}/EVIDENCE.md
  </artifacts_required>

<step number="1" subagent="context-fetcher" name="spec_initiation">

### Step 1: Spec Initiation

Identify how this spec starts: either **pull next roadmap item** or **accept user-proposed idea**.

<option_a_flow>
<trigger_phrases>

- "what's next?"
- "next item"
  </trigger_phrases>
  <actions>

1. READ @.agilevv/product/roadmap.md
2. FIND the next uncompleted item (first unchecked/unscoped entry)
3. SUMMARIZE the item (1–2 sentences) and PROPOSE it to user
4. WAIT for user approval (yes/no or revise)
   </actions>
   </option_a_flow>

<option_b_flow>
<trigger>user shares a specific spec idea</trigger>
<accept>any format, length, or detail level</accept>
<proceed>to context gathering (Step 2)</proceed>
</option_b_flow>

<outputs>
- Chosen spec intent: {roadmap-item | user-idea} with a one-line title proposal.
</outputs>
</step>

<step number="2" subagent="context-fetcher" name="context_gathering">

### Step 2: Context Gathering (Conditional)

Load **only** the minimum context not already present.

<conditional_logic>
IF `mission-lite.md` AND `tech-stack.md` are already in current context:
SKIP this step and PROCEED to Step 3
ELSE:
READ whichever are missing:

- @.agilevv/product/mission-lite.md
- @.agilevv/product/tech-stack.md
  </conditional_logic>

<context_analysis>

- mission-lite → core product purpose and value
- tech-stack → technical constraints, supported languages/frameworks, performance/security baselines
  </context_analysis>

<outputs>
- Bullet list of constraints/opportunities derived from product docs (≤8 bullets).
</outputs>
</step>

<step number="3" subagent="context-fetcher" name="requirements_clarification">

### Step 3: Requirements Clarification

Ask **numbered questions** to pin down scope & constraints before writing files.

<clarification_areas>
<scope>

- in_scope: what must be included
- out_of_scope: what is explicitly excluded
  </scope>
  <technical>
- functionality specifics & data boundaries
- UI/UX requirements or target flows
- integration points (APIs, services, protocols)
- performance/SLO targets; security/privacy constraints
  </technical>
  </clarification_areas>

<decision_tree>
IF clarification_needed:
ASK numbered_questions
WAIT for_user_response
ELSE:
PROCEED to Step 4 (Date Determination)
</decision_tree>

<outputs>
- A finalized 1-line **spec title** proposal and a short synopsis (≤2 sentences).
</outputs>
</step>

<step number="4" subagent="date-checker" name="date_determination">

### Step 4: Date Determination

Return **today’s date** in `YYYY-MM-DD` for folder naming.

<subagent_output>

- `date: YYYY-MM-DD` ← store as **SPEC_DATE**
  </subagent_output>

<outputs>
- SPEC_DATE captured.
</outputs>
</step>

<step number="5" subagent="file-creator" name="spec_folder_creation">

### Step 5: Spec Folder Creation

Create the spec folder and scaffolding with **kebab-case** slug (≤5 words).

<folder_naming>
<format>${SPEC_DATE}-${SPEC_SLUG}</format>
<date>use SPEC_DATE from Step 4</date>
<name_constraints>

- max_words: 5
- style: kebab-case
- descriptive: true
  </name_constraints>
  </folder_naming>

<create>
- mkdir -p ${SPEC_DIR}/sub-specs
- touch ${SPEC_DIR}/{spec.md,spec-lite.md,ACCEPTANCE.md,TRACEABILITY.csv,EVIDENCE.md}
- touch ${SPEC_DIR}/sub-specs/technical-spec.md
</create>

<example_names>

- 2025-03-15-password-reset-flow
- 2025-03-16-user-profile-dashboard
- 2025-03-17-api-rate-limiting
  </example_names>

<outputs>
- List of created paths under ${SPEC_DIR}
</outputs>
</step>

<step number="6" subagent="file-creator" name="create_spec_md">

### Step 6: Create spec.md

Write `${SPEC_DIR}/spec.md` using this **evidence-first** SRD template.

<file_template>

<header>
# Spec Requirements Document
> Spec: ${SPEC_SLUG}
> Created: ${SPEC_DATE}
</header>

<required_sections>

- Overview (1–2 sentences goal & objective)
- User Stories (1–3 stories, INVEST style + brief workflow)
- Spec Scope (1–5 numbered features, one sentence each)
- Out of Scope (explicit exclusions)
- Success Metrics (leading & lagging indicators)
- Assumptions & Dependencies
  </required_sections>
  </file_template>

<section name="overview">
<template>
## Overview
[1–2 sentences stating goal and objective.]
</template>
</section>

<section name="user_stories">
<template>
## User Stories
### [STORY_TITLE]
As a [USER_TYPE], I want to [ACTION], so that [BENEFIT].
- Workflow: [short path incl. edge case]
</template>
<constraints>
- count: 1–3
- include: workflow and problem solved
</constraints>
</section>

<section name="spec_scope">
<template>
## Spec Scope
1. **[FEATURE_NAME]** — [One sentence description]
2. **[FEATURE_NAME]** — [One sentence description]
</template>
</section>

<section name="out_of_scope">
<template>
## Out of Scope
- [EXCLUDED_FUNCTIONALITY_1]
- [EXCLUDED_FUNCTIONALITY_2]
</template>
</section>

<section name="success_metrics">
<template>
## Success Metrics
- Leading: [e.g., task completion rate, P50 latency]
- Lagging: [e.g., support tickets ↓, retention ↑]
</template>
</section>

<section name="assumptions_deps">
<template>
## Assumptions & Dependencies
- [Assumption or dependency]
</template>
</section>

<outputs>
- Wrote ${SPEC_DIR}/spec.md
</outputs>
</step>

<step number="7" subagent="file-creator" name="create_spec_lite_md">

### Step 7: Create spec-lite.md

Write `${SPEC_DIR}/spec-lite.md` as **compact AI context**.

<file_template>

<header>
# Spec Summary (Lite)
</header>
<body>
[1–3 sentences summarizing core goal & objective from spec.md Overview.]
</body>
</file_template>

<outputs>
- Wrote ${SPEC_DIR}/spec-lite.md
</outputs>
</step>

<step number="8" subagent="file-creator" name="create_technical_spec">

### Step 8: Create Technical Specification

Write `${SPEC_DIR}/sub-specs/technical-spec.md` with structured sections.

<file_template>

<header>
# Technical Specification
> Source: @${SPEC_DIR}/spec.md
</header>
</file_template>

<spec_sections>

- Architecture & Components (diagram optional)
- Data Model & Schemas (high-level)
- Interfaces/APIs (stubs or references)
- Performance Budgets & Load Profile
- Security & Threats (authz, secrets, SSRF/RCE, supply chain)
- Observability (logs/metrics/traces, SLOs/alerts)
- Alternatives Considered (with rationale)
  </spec_sections>

<external_dependencies_conditional>

- Only include if **new** dependencies needed:
  - library/package, purpose, version requirement
  - justification for inclusion
    </external_dependencies_conditional>

<outputs>
- Wrote ${SPEC_DIR}/sub-specs/technical-spec.md
</outputs>
</step>

<step number="9" subagent="file-creator" name="create_database_schema">

### Step 9: Create Database Schema (Conditional)

Only if **database changes** are required.

<decision_tree>
IF spec_requires_database_changes:
CREATE ${SPEC_DIR}/sub-specs/database-schema.md
ELSE:
SKIP
</decision_tree>

<file_template>

<header>
# Database Schema
> Source: @${SPEC_DIR}/spec.md
</header>
<body>
## Changes
- New tables/columns
- Modifications & migrations

## Specifications

- Exact SQL or migration syntax
- Indexes & constraints
- Foreign keys

## Rationale

- Performance considerations
- Data integrity rules
</body>
</file_template>

<outputs>
- (conditional) Wrote ${SPEC_DIR}/sub-specs/database-schema.md
</outputs>
</step>

<step number="10" subagent="file-creator" name="create_api_spec">

### Step 10: Create API Specification (Conditional)

Only if **API changes** are required.

<decision_tree>
IF spec_requires_api_changes:
CREATE ${SPEC_DIR}/sub-specs/api-spec.md
ELSE:
SKIP
</decision_tree>

<file_template>

<header>
# API Specification
> Source: @${SPEC_DIR}/spec.md
</header>
<body>
## Endpoints
### [HTTP_METHOD] [ENDPOINT_PATH]
**Purpose:** [description]  
**Parameters:** [list]  
**Response:** [format]  
**Errors:** [enumerate common error cases]
</body>
</file_template>

<outputs>
- (conditional) Wrote ${SPEC_DIR}/sub-specs/api-spec.md
</outputs>
</step>

<step number="11" subagent="file-creator" name="create_acceptance_and_traceability">

### Step 11: Acceptance Criteria & Traceability

Create **testable** acceptance criteria and a Req↔Task↔Test map.

<files>
- ${SPEC_DIR}/ACCEPTANCE.md
- ${SPEC_DIR}/TRACEABILITY.csv
</files>

<file_templates>
<acceptance_md>

# Acceptance Criteria — ${SPEC_SLUG}

- AC-001 (Req: US-001)
  - Given …
  - When …
  - Then …
  - Evidence: tests `tests/<area>/test_<case>.py::<fn>`, expected logs/metrics signal(s)
    </acceptance*md>
    <traceability_csv>
    requirement_id,task_id,test_id,notes
    US-001,TSK-001,test*<area>::test*<case>,"happy path"
    US-001,TSK-002,test*<area>::test\_<edge>,"edge case"
    </traceability_csv>
    </file_templates>

<outputs>
- Wrote ${SPEC_DIR}/ACCEPTANCE.md
- Wrote ${SPEC_DIR}/TRACEABILITY.csv
</outputs>
</step>

<step number="12" subagent="reviewer" name="spec_review_and_security_gate">

### Step 12: Review & Security Gate

Run reviews before green-lighting task creation.

<actions>
1. **Reviewer** reads spec.md + sub-specs; produces **line-level notes** and a **verdict** (approve/block) with reasons.  
2. If feature is security-sensitive or touches auth/secrets/network/protocols, run **security-auditor** for a threat model & mitigations.  
3. Append reviewer/security outputs to **EVIDENCE.md**.
</actions>

<file-creator_actions>

- Create or append ${SPEC_DIR}/EVIDENCE.md with:
  - Links/paths to reviewed files
  - Reviewer verdict and date
  - (If run) Security audit notes & required mitigations
    </file-creator_actions>

<gate>
- If **block**, update TodoList to Step 6–10 to revise.  
- If **approve**, proceed to Step 13.
</gate>

<outputs>
- Updated ${SPEC_DIR}/EVIDENCE.md
</outputs>
</step>

<step number="13" name="user_review">

### Step 13: User Review & Handoff

Present all created files, request confirmation to proceed to task creation.

<review_request>
I've created the spec set:

- Spec Requirements: @${SPEC_DIR}/spec.md
- Spec Summary: @${SPEC_DIR}/spec-lite.md
- Technical Spec: @${SPEC_DIR}/sub-specs/technical-spec.md
- (Conditional) DB Schema: @${SPEC_DIR}/sub-specs/database-schema.md
- (Conditional) API Spec: @${SPEC_DIR}/sub-specs/api-spec.md
- Acceptance: @${SPEC_DIR}/ACCEPTANCE.md
- Traceability: @${SPEC_DIR}/TRACEABILITY.csv
- Evidence: @${SPEC_DIR}/EVIDENCE.md

Please review. Reply with “approve” to proceed, or describe changes to revise.
When approved, run **/create-tasks** to build the task checklist from this spec.
</review_request>

</step>

<step number="14" name="validation_and_exit">

### Step 14: Validation & Exit Criteria

Validate that all mandatory artifacts exist and are non-empty.

<validate_presence>

- MUST exist: spec.md, spec-lite.md, sub-specs/technical-spec.md, ACCEPTANCE.md, TRACEABILITY.csv, EVIDENCE.md
- Conditional: database-schema.md (if DB changes), api-spec.md (if API changes)
  </validate_presence>

<exit_criteria>

- Reviewer approved; security audit completed if applicable.
- Every requirement in spec maps to ≥1 acceptance criterion in ACCEPTANCE.md.
- TRACEABILITY.csv has at least one row and no dangling requirement IDs.
  </exit_criteria>

<outputs>
- Validation report (pass/fail with missing paths if any).
</outputs>
</step>

</process_flow>
