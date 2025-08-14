# API Specification

This is the API specification for the spec detailed in @.agilevv/specs/2025-08-14-story-map-integration/spec.md

> Created: 2025-08-14
> Version: 1.0.0

## CLI Commands

### story-map init

**Purpose:** Initialize story mapping during Sprint 0 with user persona and epic creation
**Usage:** `verifflowcc story-map init [--template TEMPLATE] [--interactive]`
**Parameters:**

- `--template`: Optional template file for story map initialization
- `--interactive`: Enable interactive story map creation wizard
  **Response:** Creates `.agilevv/story_map.json` and `story_map.md` files
  **Errors:** ValidationError if story map already exists, FileNotFoundError for template

### story-map add-epic

**Purpose:** Add new epic to existing story map with feature breakdown
**Usage:** `verifflowcc story-map add-epic EPIC_NAME [--description DESC] [--priority PRIORITY]`
**Parameters:**

- `EPIC_NAME`: Required epic name
- `--description`: Epic description text
- `--priority`: Priority level (must, should, could, won't)
  **Response:** Updates story map with new epic and confirms creation
  **Errors:** ValidationError if epic name conflicts, FileNotFoundError if story map not initialized

### story-map add-story

**Purpose:** Add user story to existing epic with acceptance criteria
**Usage:** `verifflowcc story-map add-story EPIC_ID STORY_TITLE [--as USER_TYPE] [--want ACTION] [--so BENEFIT]`
**Parameters:**

- `EPIC_ID`: Target epic identifier
- `STORY_TITLE`: User story title
- `--as`, `--want`, `--so`: User story template components
  **Response:** Creates user story with INVEST validation results
  **Errors:** ValidationError if INVEST criteria not met, NotFoundError if epic doesn't exist

### story-map validate-dod

**Purpose:** Validate Definition of Done criteria for specified story or epic
**Usage:** `verifflowcc story-map validate-dod [STORY_ID | EPIC_ID] [--level LEVEL]`
**Parameters:**

- `STORY_ID/EPIC_ID`: Optional target identifier (validates all if omitted)
- `--level`: DoD level to validate (story, feature, epic)
  **Response:** DoD validation report with pass/fail status and evidence
  **Errors:** ValidationError if DoD criteria not met, NotFoundError for invalid IDs

### story-map status

**Purpose:** Display current story map status and progress summary
**Usage:** `verifflowcc story-map status [--format FORMAT] [--filter FILTER]`
**Parameters:**

- `--format`: Output format (text, json, markdown)
- `--filter`: Filter by status (completed, in_progress, planned)
  **Response:** Story map progress report with completion metrics
  **Errors:** FileNotFoundError if story map not initialized

## Integration Commands

### Enhanced Orchestrator Commands

**Modified:** `verifflowcc init-sprint0`

- Now includes story map initialization as part of Sprint 0 setup
- Integrates story mapping with vision collection and architecture alignment

**Modified:** `verifflowcc plan`

- Consults story map for next highest-priority story selection
- Updates story selection based on previous sprint learnings

**Modified:** `verifflowcc run-sprint`

- Includes story map context in all V-Model stage agent inputs
- Validates DoD criteria at each quality gate before stage progression
