---
description: Spec Review & Refresh Rules for AgileVerifFlowCC (evidence-first audit of existing specs)
globs:
  - .agilevv/product/**
  - .agilevv/specs/**
  - .agilevv/product/**
  - .agilevv/specs/**
  - **/*.md
  - **/*.py
  - **/*.ts
alwaysApply: false
version: 1.0
encoding: UTF-8
---

# Spec Review & Refresh Rules

## Overview

Audit and refresh an **existing** feature specification (possibly stale) to realign with the current mission, roadmap, and codebase.  
**Guardrails:**

- **Parallelize analysis, serialize writes.** Only the **file-creator** subagent writes to disk.
- Read-only agents (context-fetcher, reviewer, security-auditor) **must not modify files**.
- Any write step must **list file paths** it produced/updated and append to **EVIDENCE.md**.

<pre_flight_check>
MUST_RUN: @agent:system-checker (block if any Critical fails)
</pre_flight_check>

<process_flow>

<variables>
  <var name="TARGET_SPEC_DIR" source="step:1.output.spec_dir" required="true" />
  <var name="REVIEW_DATE" source="step:2.output.date" required="true" />
  <var name="REVIEW_DIR" source="computed:${TARGET_SPEC_DIR}/reviews/${REVIEW_DATE}" required="true" />
</variables>

<artifacts_emitted>

- ${REVIEW_DIR}/REVIEW.md
- ${REVIEW_DIR}/CHECKLIST.md
- ${REVIEW_DIR}/DIFF.md
- ${REVIEW_DIR}/PATCHES/\*.patch (conditional)
- Append updates to: ${TARGET_SPEC_DIR}/EVIDENCE.md
  </artifacts_emitted>

<step number="1" subagent="context-fetcher" name="identify_target_spec">

### Step 1: Identify Target Spec

Determine which existing spec to review.

<selection_logic>

- If user provided an explicit path → use it (validate it exists).
- Else auto-select the **most recently modified** folder under `.agilevv/specs/*` (or `.agilevv/specs/*`), preferring those that contain `spec.md`.
- Extract **SPEC_SLUG** (folder suffix without date) and **SPEC_DATE** (leading YYYY-MM-DD) from folder name if present.
  </selection_logic>

<required_files>

- spec.md (mandatory)
- spec-lite.md (recommended)
- sub-specs/technical-spec.md (recommended)
- (conditional) sub-specs/database-schema.md
- (conditional) sub-specs/api-spec.md
- ACCEPTANCE.md (recommended)
- TRACEABILITY.csv (recommended)
- EVIDENCE.md (recommended; create if missing during write step)
  </required_files>

<outputs>
- spec_dir: absolute/relative path to target spec
- discovered_files: map of present/missing required files
</outputs>
</step>

<step number="2" subagent="date-checker" name="get_review_date">

### Step 2: Get Review Date

Return **today’s date** as `YYYY-MM-DD` for the review folder.

<subagent_output>

- date: YYYY-MM-DD
  </subagent_output>

</step>

<step number="3" subagent="context-fetcher" name="load_minimum_context">

### Step 3: Load Minimum Context

Load only the docs needed for alignment checks if not already in context.

<documents>
- @.agilevv/product/mission-lite.md (or .agilevv/product/mission-lite.md)
- @.agilevv/product/tech-stack.md (or .agilevv/product/tech-stack.md)
- @.agilevv/product/roadmap.md (or .agilevv/product/roadmap.md)
- ${TARGET_SPEC_DIR}/spec.md (+ spec-lite.md if present)
- ${TARGET_SPEC_DIR}/sub-specs/technical-spec.md (if present)
- ${TARGET_SPEC_DIR}/ACCEPTANCE.md (if present)
- ${TARGET_SPEC_DIR}/TRACEABILITY.csv (if present)
- ${TARGET_SPEC_DIR}/EVIDENCE.md (if present)
</documents>

<outputs>
- A compact, token-bounded synopsis (≤ 8 bullets) of constraints/opportunities and the spec’s stated goals.
</outputs>
</step>

<step number="4" subagent="context-fetcher" name="staleness_and_consistency_assessment">

### Step 4: Staleness & Consistency Assessment

Assess how stale the spec is and how well it aligns with product docs.

<checks>
- **Age**: days since last git change to each file (`git log -1 --format=%cs -- <file>`), categorize: Fresh (≤14d), Warming (15–60d), Stale (61–180d), **Outdated** (>180d)
- **Mission Fit**: spec goals vs. mission-lite (conflicts/mismatches)
- **Tech Consistency**: libraries/frameworks named vs. tech-stack; flag defunct/renamed deps
- **Roadmap Link**: referenced item exists and current state (unchecked, in-progress, complete)
- **Section Completeness**: required fields present (Overview, User Stories, Scope, OOS, Success Metrics, Assumptions/Deps)
- **Evidence Presence**: ACCEPTANCE + TRACEABILITY exist and map at least one requirement
</checks>

<outputs>
- A **Spec Health Score** (0–100) with components (Age, Mission, Tech, Roadmap, Completeness, Evidence).
- A short **risk table**: [{area, severity(C/M/m), finding, proof(reference)}].
</outputs>
</step>

<step number="5" subagent="context-fetcher" name="traceability_review">

### Step 5: Traceability Review

Verify Req↔AC↔Test links and identify gaps.

<checks>
- Parse User Stories from `spec.md` (or list requirements if present).
- Cross-reference `ACCEPTANCE.md` IDs (e.g., AC-001 ↔ US-001) — flag orphans/missing.
- Check `TRACEABILITY.csv` structure: headers present, at least one row, consistent IDs.
- Probe tests directory (if present) to see if related test files/functions exist **by pattern** (no code execution).
</checks>

<outputs>
- Table of {requirement_id, has_AC, has_Test, notes}.
- List of missing ACs/tests with suggested IDs and filenames.
</outputs>
</step>

<step number="6" subagent="reviewer" name="content_quality_review">

### Step 6: Content Quality Review

Perform a structured editorial review for clarity, testability, and ambiguity.

<criteria>
- Overview: outcome-oriented, unambiguous, ≤2 sentences.
- User Stories: INVEST, include minimal workflow.
- Scope/OOS: crisp boundaries.
- Success Metrics: at least one **leading** and one **lagging** metric, measurable.
- Assumptions/Deps: explicit and actionable.
- Tech Spec: architecture, data model, interfaces, security, observability.
</criteria>

<outputs>
- Line-level notes with suggestions; group by severity (Critical/Major/Minor).
- A verdict: **approve** / **revise** / **block** with reasons.
</outputs>
</step>

<step number="7" subagent="security-auditor" name="security_and_privacy_review">

### Step 7: Security & Privacy Review (Conditional)

Run if the feature touches auth, secrets, network/protocols, PII, or data export/import.

<deliverables>
- Threat model (STRIDE-like) with mitigations
- Security requirements to add to spec (if missing)
- Notes on supply-chain risks (deps, MCP tools, SDKs)
</deliverables>

<outputs>
- A security note block to append to EVIDENCE.md
</outputs>
</step>

<step number="8" subagent="file-creator" name="emit_review_artifacts">

### Step 8: Emit Review Artifacts (No Mutation of Core Spec Files)

Create a **review folder** and write artifacts; do **not** rewrite spec files yet.

<create>
- mkdir -p ${REVIEW_DIR}/PATCHES
- write ${REVIEW_DIR}/REVIEW.md (health score, risks, decisions, summary)
- write ${REVIEW_DIR}/CHECKLIST.md (pass/fail for each check; missing items list)
- write ${REVIEW_DIR}/DIFF.md (proposed redlines summary; no content mutation yet)
</create>

<append_evidence>

- Append an entry to ${TARGET_SPEC_DIR}/EVIDENCE.md:
  - Review date, reviewer agent(s), verdict
  - Paths to artifacts under ${REVIEW_DIR}
  - (If any) security notes
    </append_evidence>

<outputs>
- List of files created/updated.
</outputs>
</step>

<step number="9" subagent="file-creator" name="prepare_patches">

### Step 9: Prepare Patches (Conditional)

If the verdict in Step 6 is **revise** or **block**, generate **unified diffs** as patch files only.

<rules>
- Create one patch per target file (e.g., spec.md, technical-spec.md).
- Include only **minimal** changes needed to resolve findings.
- Name patches as: `${REVIEW_DIR}/PATCHES/<filename>.patch`.
</rules>

<outputs>
- Paths to generated patch files (if any).
</outputs>
</step>

<step number="10" name="user_review_and_approval_gate">

### Step 10: User Review & Approval Gate

Present a concise summary and seek approval to apply patches.

<summary_template>
**Spec Review Summary — ${SPEC_SLUG}** (Health: <score>/100)

- Risks: [top 3 short bullets]
- Missing/weak items: [N]
- Patches prepared: [Y/N] → see `${REVIEW_DIR}/PATCHES/`

Reply **apply** to apply patches, **skip** to keep artifacts only, or describe edits to regenerate patches.
</summary_template>

<approval_flow>
IF user replies "apply":
PROCEED to Step 11
ELSE:
END with artifacts preserved
</approval_flow>

</step>

<step number="11" subagent="file-creator" name="apply_patches">

### Step 11: Apply Patches (Conditional)

Apply the approved patches atomically; update evidence and create a changelog note.

<apply_policy>

- Atomic write (temp + rename) per file
- Preserve non-target sections; only modify lines covered by patch
  </apply_policy>

<evidence_update>

- Append to ${TARGET_SPEC_DIR}/EVIDENCE.md:
  - Applied patch list with checksums
  - Reviewer/approver name + date
    </evidence_update>

<outputs>
- List of modified files with line ranges.
</outputs>
</step>

<step number="12" name="validation_and_exit">

### Step 12: Validation & Exit Criteria

Re-run completeness checks on the **updated** spec set.

<validate_presence>

- Required: spec.md; recommend: spec-lite.md, technical-spec.md, ACCEPTANCE.md, TRACEABILITY.csv, EVIDENCE.md
- Traceability: each requirement has ≥1 AC; CSV has ≥1 row; no dangling IDs
- Security (if applicable): threat model attached in EVIDENCE.md
  </validate_presence>

<exit_report>

- Final health score and residual risks
- Final list of changed files
  </exit_report>

</step>

</process_flow>
