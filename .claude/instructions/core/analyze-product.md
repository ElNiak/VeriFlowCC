---
description: Analyze Current Product & Install AgileVerifFlowCC (for existing repositories)
globs:
alwaysApply: false
version: 1.2
encoding: UTF-8
---

# Analyze Current Product & Install AgileVerifFlowCC

## Overview

Install AgileVerifFlowCC into an **existing** codebase and generate accurate product docs that reflect the _actual_ implementation.  
This flow is **deterministic**, **idempotent**, and writes **only** via `file-creator`.

<pre_flight_check>
EXECUTE: @.claude/instructions/meta/pre-flight.md
REQUIRE_MARKER: PRE_FLIGHT_MARKER: AgileVerifFlowCC
MUST_RUN: @agent:system-checker <!-- Block if any Critical fails -->
</pre_flight_check>

<artifacts>
- `.agilevv/product/` — canonical product docs (mission, mission-lite, tech-stack, roadmap)
- `.agilevv/analysis/` — codebase analysis outputs
- `.agilevv/decisions/` — architecture/decision logs
- `.agilevv/install/` — install logs & readiness snapshots
</artifacts>

<inputs_template>

```xml
<install-existing-request>
  <repo_root>.</repo_root>
  <branch_name optional="true">install-agileverifflowcc</branch_name>
  <product_type optional="true">auto</product_type>
  <prior_docs optional="true">
    <path>.agilevv/product/mission.md</path>
  </prior_docs>
</install-existing-request>
```

<outputs_template>

```md
# 🧭 Install Report

Repo: <repo_root> Branch: <branch_name> Product: <observed_product_type>

## Summary

- System readiness: <Ready yes/no> (Critical passed: <n>/<m>)
- Product docs created/updated: mission, mission-lite, tech-stack, roadmap
- Analysis artifacts: inventory.md, stack.md, endpoints.md, decisions.md

## Next Actions

1. Review `.agilevv/product/` documents
2. Confirm roadmap Phase 0 items
3. Approve branch & open PR
```

</outputs_template>

<process_flow>

<step number="0" subagent="project-manager" name="initialize_and_guard">

### Step 0: Initialize & Guard (Read-Only)

Resolve repository root and enforce safe write conditions.

<checks>
- Resolve repo root (`git rev-parse --show-toplevel`, fallback to `.`)
- Verify workspace writable
- Ensure dedicated branch/worktree exists for installation tasks
</checks>

<instructions>
  ACTION: If `branch_name` not provided, derive from date: `install-agileverif-YYYYMMDD`
  DELEGATE: @agent:git-workflow to create/switch branch (exclude default `main/master`)
  RECORD: planned writes under `.agilevv/`
</instructions>

</step>

<step number="1" subagent="system-checker" name="environment_readiness">

### Step 1: Environment Readiness Gate

Run `system-checker` and **block** if any Critical checks fail.

<gate>
- Critical must all pass
- If blocked: print top 3 remediations and STOP
</gate>

<artifacts>
- Write JSON and MD snapshot to `.agilevv/install/system-check-<DATE>.{json,md}`
</artifacts>

</step>

<step number="2" subagent="context-fetcher" name="deep_codebase_analysis">

### Step 2: Deep Codebase Analysis

Use `context-fetcher` to read the codebase and extract concrete signals.

<analysis_areas>
<project_structure>

- Directory organization
- File naming patterns
- Module structure
- Build configuration
  </project_structure>
  <technology_stack>
- Frameworks (pyproject.toml, requirements.txt, package.json, Gemfile)
- Databases and ORMs
- Infra & deploy configs (Dockerfile, Compose, CI)
  </technology_stack>
  <implementation_progress>
- Completed features
- Work in progress
- Authentication/authorization state
- API endpoints
- Database schema/migrations
  </implementation_progress>
  <code_patterns>
- Coding style and conventions
- Tests layout (unit/integration/validation)
- Reusable utilities and middleware/hooks
  </code_patterns>
  </analysis_areas>

<outputs>
- `analysis/inventory.md` — file tree & modules
- `analysis/stack.md` — frameworks, libs, versions (observed)
- `analysis/endpoints.md` — API surface (routes, methods, auth)
- `analysis/db.md` — schema summary & migrations
- `analysis/tests.md` — test structure & coverage hints
</outputs>

</step>

<step number="3" subagent="context-fetcher" name="gather_product_context">

### Step 3: Gather Product Context

Ask the user concise, numbered questions; merge answers with code facts.

<context_questions>
Based on the repository, you appear to be building **[OBSERVED_PRODUCT_TYPE]**.

To set up AgileVerifFlowCC correctly:

1. **Product Vision** — problem solved & primary users?
2. **Hidden Features** — anything not obvious from code?
3. **Roadmap** — what’s next? any refactors planned?
4. **Decisions** — key product/tech decisions to record?
5. **Team Preferences** — coding standards/practices we should codify?
   </context_questions>

<instructions>
  ACTION: Present questions; WAIT for answers
  MERGE: user context with Step 2 analysis into a single data model
  STORE: in-memory for Step 4
</instructions>

</step>

<step number="4" subagent="file-creator" name="persist_analysis_artifacts">

### Step 4: Persist Analysis Artifacts

Create/update `.agilevv/analysis/*.md` using **idempotent** sentinel blocks.

<files>
- `.agilevv/analysis/inventory.md`
- `.agilevv/analysis/stack.md`
- `.agilevv/analysis/endpoints.md`
- `.agilevv/analysis/db.md`
- `.agilevv/analysis/tests.md`
</files>

<write_policy>

- Atomic writes (temp + rename)
- Preserve manual notes outside sentinel blocks
  </write_policy>

</step>

<step number="5" subagent="project-manager" name="prepare_plan_product_input">

### Step 5: Prepare plan-product Input

Assemble structured input from analysis + user responses.

<execution_parameters>
<main_idea>[DERIVED_FROM_ANALYSIS_AND_USER_INPUT]</main_idea>
<key_features>
<implemented>[FROM_STEP_2]</implemented>
<planned>[FROM_STEP_3]</planned>
</key_features>
<target_users>[FROM_STEP_3]</target_users>
<tech_stack>[FROM_STEP_2_STACK]</tech_stack>
</execution_parameters>

<outputs>
- `install/plan-product-input.json` (for reproducibility)
</outputs>

</step>

<step number="6" subagent="project-manager" name="execute_plan_product">

### Step 6: Execute plan-product

Invoke `@.claude/instructions/core/plan-product.md` with the prepared context; allow it to create `.agilevv/product/`.

<execution_prompt>
@.claude/instructions/core/plan-product.md

Installing AgileVerifFlowCC into an existing product.

**Main Idea:** [SUMMARY_FROM_ANALYSIS_AND_CONTEXT]

**Key Features**

- Implemented: [LIST_FROM_ANALYSIS]
- Planned: [LIST_FROM_USER]

**Target Users:** [FROM_USER_RESPONSE]

**Tech Stack:** [DETECTED_STACK_WITH_VERSIONS]
</execution_prompt>

<guardrails>
- Only `file-creator` writes
- Paths limited to `.agilevv/product/`
</guardrails>

</step>

<step number="7" subagent="file-creator" name="customize_generated_files">

### Step 7: Customize Generated Documentation

Refine roadmap/tech-stack/decisions to reflect _actual_ implementation.

<customization_tasks>
<roadmap_adjustment>

- Add **Phase 0: Already Completed** with detected features
- Move implemented items under Phase 0 with `[x]`
- Ensure Phase 1 reflects current in-progress work
  </roadmap_adjustment>
  <tech_stack_verification>
- Verify versions
- Add infra details (CI/CD, container, hosting)
- Note environment constraints
  </tech_stack_verification>
  <decisions_documentation>
- Record historical decisions (why chosen, when)
- Capture pivots/changes and rationale
  </decisions_documentation>
  </customization_tasks>

<roadmap_template>

## Phase 0: Already Completed

- [x] [FEATURE_1] — [DESCRIPTION_FROM_CODE]
- [x] [FEATURE_2] — [DESCRIPTION_FROM_CODE]
- [x] [FEATURE_3] — [DESCRIPTION_FROM_CODE]

## Phase 1: Current Development

- [ ] [IN_PROGRESS_FEATURE] — [DESCRIPTION]

[CONTINUE_WITH_STANDARD_PHASES]
</roadmap_template>

</step>

<step number="8" subagent="git-workflow" name="commit_and_pr">

### Step 8: Commit & PR

Create a commit and open a PR for the installation changes.

<commit_message>
chore(agent-os): install AgileVerifFlowCC — analysis, product docs, roadmap phase 0
</commit_message>

<pr_template>
Title: Install AgileVerifFlowCC — analysis + product docs  
Body:

- Adds `.agilevv/analysis/*` artifacts
- Adds/updates `.agilevv/product/*` (mission, mission-lite, tech-stack, roadmap)
- Documents decisions & environment snapshot
  </pr_template>

</step>

<step number="9" subagent="project-manager" name="final_verification_and_summary">

### Step 9: Final Verification & Summary

Verify completeness and present next steps.

<verification_checklist>

- [ ] `.agilevv/product/` exists and is populated
- [ ] Roadmap includes **Phase 0** completed features
- [ ] Tech stack aligns with detected dependencies
- [ ] PR created and linked
      </verification_checklist>

<summary_template>

## ✅ AgileVerifFlowCC Installed for Existing Product

**Tech Stack:** [SUMMARY_OF_DETECTED_STACK]  
**Completed Features:** [COUNT]  
**Code Style:** [DETECTED_PATTERNS]  
**Current Phase:** [IDENTIFIED_STAGE]

**Created/Updated**

- `.agilevv/product/` — mission, mission-lite, tech-stack, roadmap
- `.agilevv/analysis/` — inventory, stack, endpoints, db, tests
- `.agilevv/decisions/` — decision logs
- `.agilevv/install/` — system-check snapshot, plan-product input

**Next Steps**

1. Review `.agilevv/product/` docs
2. Confirm roadmap **Phase 0** and upcoming phases
3. Approve PR and merge
4. Start your next feature with: `@.claude/instructions/core/create-spec.md`
   </summary_template>

</step>

</process_flow>

<post_flight_check>
EXECUTE: @.claude/instructions/meta/post-flight.md
REQUIRE_MARKER: POST_FLIGHT_MARKER: AgileVerifFlowCC v1.0
</post_flight_check>

## Error Handling

<error_scenarios>
<scenario name="no_clear_structure">
<condition>Project type/structure cannot be determined</condition>
<action>Ask user for project type and primary entry points</action>
</scenario>
<scenario name="conflicting_patterns">
<condition>Multiple coding styles detected</condition>
<action>Ask user which standard to document as canonical</action>
</scenario>
<scenario name="missing_dependencies">
<condition>Tech stack incomplete or ambiguous</condition>
<action>List detected technologies and ask for missing/ambiguous items</action>
</scenario>
<scenario name="blocked_by_readiness">
<condition>system-checker Critical failures</condition>
<action>Report top 3 remediations and stop until resolved</action>
</scenario>
</error_scenarios>

## Execution Summary

<final_checklist>
<verify>

- [ ] Repo resolved and branch protected
- [ ] System readiness verified (Critical all pass)
- [ ] Codebase analyzed and artifacts persisted
- [ ] plan-product executed with structured context
- [ ] Documentation customized for existing product
- [ ] PR created for adoption
      </verify>
      </final_checklist>
