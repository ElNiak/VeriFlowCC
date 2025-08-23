---
description: Product Planning Rules for AgileVerifFlowCC
globs:
alwaysApply: false
version: 4.1
encoding: UTF-8
---

# Product Planning Rules

## Overview

Generate product docs for new projects: mission, tech-stack and roadmap files for AI agent consumption. This flow is **idempotent**, writes only via `file-creator`, and blocks until required inputs are present.

<process_flow>

<step number="0" subagent="project-manager" name="resolve_project_root">

### Step 0: Resolve Project Root (Read-Only)

Confirm we are inside the intended project folder and detect write readiness.

<checks>
- Current directory appears to be a repo root (best-effort `git rev-parse --show-toplevel`)
- `.agilevv/` does not conflict with existing non-doc assets
- Workspace is writable
</checks>

<if_not_ready>
ASK the user:

1. What is the project root path to use? (absolute or relative)
2. Has the new application been initialized and are we inside the project folder? (yes/no)
3. Proceed to create `.agilevv/` structure under this root? (yes/no)
   </if_not_ready>

<outputs>
- resolved_root: absolute path (string)
- ready: boolean
</outputs>

</step>

<step number="1" subagent="context-fetcher" name="gather_user_input">

### Step 1: Gather User Input

Use the context-fetcher subagent to collect all required inputs from the user, with **blocking validation** before proceeding. If items are missing, emit the error template and pause.

<input_schema>

- main_idea: string (required)
- key_features: array[string] (min: 3, required)
- target_users: array[string] (min: 1, required)
- tech_stack_preferences: map[string,string] (optional)
- initialized_project: boolean (required)
  </input_schema>

<data_sources>
<primary>user_direct_input</primary>
<fallback_sequence> 1. @.agilevv/standards/tech-stack.md 2. @.claude/CLAUDE.md 3. Cursor User Rules
</fallback_sequence>
</data_sources>

<error_template>
Please provide the following missing information:

1. Main idea for the product
2. List of key features (minimum 3)
3. Target users and use cases (minimum 1)
4. Tech stack preferences
5. Has the new application been initialized and are we inside the project folder? (yes/no)
   </error_template>

<outputs>
- collected_input.json (in-memory structure for later steps)
</outputs>

</step>

<step number="2" subagent="file-creator" name="create_documentation_structure">

### Step 2: Create Documentation Structure

Use the file-creator subagent to create the following file structure **idempotently** with write-permission validation and protection against overwriting existing files:

<file_structure>
.agilevv/
└── product/
├── mission.md # Product vision and purpose
├── mission-lite.md # Condensed mission for AI context
├── tech-stack.md # Technical architecture
└── roadmap.md # Development phases
</file_structure>

<sentinels>
- Use sentinel blocks for future updates where sections may be re-generated.
- All writes must be atomic (temp + rename). Preserve existing content outside sentinel ranges.
</sentinels>

</step>

<step number="3" subagent="file-creator" name="create_mission_md">

### Step 3: Create mission.md

Use the file-creator subagent to create the file: `.agilevv/product/mission.md` using the template and constraints below. Populate placeholders with `collected_input`.

<file_template>

  <header>
    # Product Mission
  </header>
  <required_sections>
    - Pitch
    - Users
    - The Problem
    - Differentiators
    - Key Features
  </required_sections>
</file_template>

<section name="pitch">
  <template>
    ## Pitch

    [PRODUCT_NAME] is a [PRODUCT_TYPE] that helps [TARGET_USERS] [SOLVE_PROBLEM] by providing [KEY_VALUE_PROPOSITION].

  </template>
  <constraints>
    - length: 1–2 sentences
    - style: elevator pitch
  </constraints>
</section>

<section name="users">
  <template>
    ## Users

    ### Primary Customers

    - [CUSTOMER_SEGMENT_1]: [DESCRIPTION]
    - [CUSTOMER_SEGMENT_2]: [DESCRIPTION]

    ### User Personas

    **[USER_TYPE]** ([AGE_RANGE])
    - **Role:** [JOB_TITLE]
    - **Context:** [BUSINESS_CONTEXT]
    - **Pain Points:** [PAIN_POINT_1], [PAIN_POINT_2]
    - **Goals:** [GOAL_1], [GOAL_2]

  </template>
  <schema>
    - name: string
    - age_range: "XX–XX years old"
    - role: string
    - context: string
    - pain_points: array[string]
    - goals: array[string]
  </schema>
  <constraints>
    - personas: 1–3
    - each persona must include at least 2 pain points and 2 goals
  </constraints>
</section>

<section name="problem">
  <template>
    ## The Problem

    ### [PROBLEM_TITLE]

    [PROBLEM_DESCRIPTION]. [QUANTIFIABLE_IMPACT].

    **Our Solution:** [SOLUTION_DESCRIPTION]

  </template>
  <constraints>
    - problems: 2–4
    - description: 1–3 sentences
    - impact: include a metric (e.g., "%", "hours/week", "€ cost")
    - solution: 1 sentence
  </constraints>
</section>

<section name="differentiators">
  <template>
    ## Differentiators

    ### [DIFFERENTIATOR_TITLE]

    Unlike [COMPETITOR_OR_ALTERNATIVE], we provide [SPECIFIC_ADVANTAGE]. This results in [MEASURABLE_BENEFIT].

  </template>
  <constraints>
    - count: 2–3
    - focus: competitive advantages tied to user-value
    - evidence: 1 short justification per differentiator
  </constraints>
</section>

<section name="features">
  <template>
    ## Key Features

    ### Core Features

    - **[FEATURE_NAME]:** [USER_BENEFIT_DESCRIPTION]

    ### Collaboration Features

    - **[FEATURE_NAME]:** [USER_BENEFIT_DESCRIPTION]

  </template>
  <constraints>
    - total: 8–10 features
    - grouping: by category
    - description: user-benefit focused (avoid implementation detail)
  </constraints>
</section>

<validation>
- Ensure at least 8 features total across categories
- Ensure personas include role, context, pain points, and goals
</validation>

</step>

<step number="4" subagent="file-creator" name="create_tech_stack_md">

### Step 4: Create tech-stack.md

Use the file-creator subagent to create `.agilevv/product/tech-stack.md`, filling from `collected_input` with the following template and resolution logic.

<file_template>

  <header>
    # Technical Stack
  </header>
</file_template>

<required_items>

- application_framework: string + version
- database_system: string
- javascript_framework: string
- import_strategy: ["importmaps", "node"]
- css_framework: string + version
- ui_component_library: string
- fonts_provider: string
- icon_library: string
- application_hosting: string
- database_hosting: string
- asset_hosting: string
- deployment_solution: string
- code_repository_url: string
  </required_items>

<data_resolution>
IF context-fetcher available:
FOR each missing tech stack item:
USE @agent:context-fetcher with REQUEST:
"Find `[ITEM_NAME]` defaults from any existing tech-stack.md or standards"
IF found:
APPLY default
ELSE:
PROCEED to manual resolution

<manual_resolution>
FOR each missing item:
CHECK, in order: 1. @.agilevv/standards/tech-stack.md 2. @.claude/CLAUDE.md 3. Cursor User Rules
IF still missing:
ADD to missing_list
</manual_resolution>
</data_resolution>

<missing_items_template>
Please provide the following technical stack details:
[NUMBERED_LIST_OF_MISSING_ITEMS]

You can respond with the technology choice or "n/a" for each item.
</missing_items_template>

</step>

<step number="5" subagent="file-creator" name="create_mission_lite_md">

### Step 5: Create mission-lite.md

Use the file-creator subagent to create `.agilevv/product/mission-lite.md` for **condensed context**.

<file_template>

  <header>
    # Product Mission (Lite)
  </header>
</file_template>

<content_structure>
<elevator_pitch> - source: Step 3 mission.md pitch section - format: single sentence (≤ 35 words)
</elevator_pitch>
<value_summary> - length: 1–3 sentences - includes: value proposition, primary users, primary differentiator - excludes: secondary users/differentiators
</value_summary>
</content_structure>

<content_template>
[ELEVATOR_PITCH_FROM_MISSION_MD]

[1–3_SENTENCES_SUMMARIZING_VALUE_TARGET_USERS_AND_PRIMARY_DIFFERENTIATOR]
</content_template>

<example>
TaskFlow is a project management tool that helps remote teams coordinate work efficiently by providing real-time collaboration and automated workflow tracking.

TaskFlow serves distributed software teams who need seamless task coordination across time zones. Unlike traditional project management tools, TaskFlow automatically syncs with development workflows and provides intelligent task prioritization based on team capacity and dependencies.
</example>

</step>

<step number="6" subagent="file-creator" name="create_roadmap_md">

### Step 6: Create roadmap.md

Use the file-creator subagent to create `.agilevv/product/roadmap.md` using this structure. Ensure **phase constraints** and **effort scale** are respected.

<file_template>

  <header>
    # Product Roadmap
  </header>
</file_template>

<phase_structure>
<phase_count>1–5</phase_count>
<features_per_phase>3–7</features_per_phase>
<phase_template> ## Phase [NUMBER]: [NAME]

    **Goal:** [PHASE_GOAL]
    **Success Criteria:** [MEASURABLE_CRITERIA]

    ### Features

    - [ ] [FEATURE] - [DESCRIPTION] `[EFFORT]`

    ### Dependencies

    - [DEPENDENCY]

    ### Risks (Optional)
    - [RISK] — [MITIGATION]

</phase_template>
</phase_structure>

<phase_guidelines>

- Phase 1: Core MVP functionality
- Phase 2: Key differentiators
- Phase 3: Scale and polish
- Phase 4: Advanced features
- Phase 5: Enterprise features
  </phase_guidelines>

<effort_scale>

- XS: 1 day
- S: 2–3 days
- M: 1 week
- L: 2 weeks
- XL: 3+ weeks
  </effort_scale>

<validation>
- Ensure each phase lists 3–7 features
- Each feature must include an effort tag
</validation>

</step>

<step number="7" subagent="project-manager" name="review_and_summary">

### Step 7: Review & Summary (Read-Only)

Present a concise summary and request approval or edits before closing.

<summary_template>
Created product docs:

- Mission: `.agilevv/product/mission.md`
- Mission (Lite): `.agilevv/product/mission-lite.md`
- Tech Stack: `.agilevv/product/tech-stack.md`
- Roadmap: `.agilevv/product/roadmap.md`

Would you like to review or request changes to any section?  
Reply with:

1. "approve" to finalize
2. A list of edits (file + section + change)
   </summary_template>

</step>

</process_flow>
