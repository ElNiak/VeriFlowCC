# Technical Specification

This is the technical specification for the spec detailed in @.agilevv/specs/2025-08-21-context-subagent-standardization/spec.md

> Created: 2025-08-22
> Version: 1.0.0

## Technical Requirements

### Sequential Workflow Hook Architecture

- Implement SubagentStop hooks to control V-Model stage transitions and validate completion criteria
- Create PreToolUse hooks for validating context format before subagent invocation using Task tool
- Establish PostToolUse hooks for standardizing subagent outputs and enforcing JSON Schema compliance
- Deploy UserPromptSubmit hooks for validating input context before main agent processing begins

### Context Transfer Validation System

- Implement ContextTransfer class with serialize/deserialize methods for CONTEXT1 → CONTEXT2 → CONTEXT3 chains
- Create context validation middleware using PreToolUse hooks to catch format errors before subagent execution
- Establish context versioning system in .agilevv/state.json to track sequential agent progression
- Deploy SessionStart hooks to load V-Model context and initialize proper stage-specific templates

### Claude Code Subagent Integration

- Convert existing Jinja2 templates (.j2 files) to Claude Code subagent format with YAML frontmatter
- Create .claude/agents/ directory structure with single-responsibility subagent definitions
- Implement subagent registry following Claude Code naming conventions (kebab-case format)
- Establish tool permission mapping between VeriFlowCC agents and Claude Code subagent capabilities

### Hook-Based Quality Gates

- Deploy stage-specific validation hooks for each V-Model phase (requirements, architect, developer, qa, integration)
- Implement artifact validation using PostToolUse hooks on Write|Edit|MultiEdit operations
- Create automated quality checks with SubagentStop hooks before allowing stage progression
- Establish error recovery patterns using hooks for failed context transfers or validation failures

### JSON Schema Validation Pipeline

- Define comprehensive schemas for each V-Model stage context using Pydantic models
- Implement constrained decoding validation in PreToolUse hooks before subagent invocation
- Create schema migration system for evolving context formats without breaking existing workflows
- Deploy PostToolUse hooks for automatic output validation and format enforcement

### Hook Configuration Infrastructure

- Create .claude/hooks/ directory with Python validation scripts for each V-Model stage
- Implement .claude/config.json with hook event mappings for sequential workflow coordination
- Establish environment variable handling for $CLAUDE_PROJECT_DIR and context path management
- Create hook chaining patterns for multi-stage validation (requirements → architecture → development)

### V-Model Stage Coordination Hooks

- **Requirements Gate Hook**: Validates INVEST/SMART criteria before proceeding to architecture
- **Architecture Validation Hook**: Ensures design completeness before development phase
- **Code Quality Hook**: Enforces standards before testing phase using PostToolUse on code changes
- **Test Validation Hook**: Verifies test completion before integration using SubagentStop events
- **Integration Gate Hook**: Final validation before deployment approval using comprehensive checks

### Template and Instruction Migration

- Migrate verifflowcc/prompts/_.j2 templates to .claude/agents/_.md format with proper YAML frontmatter
- Update .claude/instructions/ files to leverage hooks for workflow coordination
- Implement template validation using PreToolUse hooks to ensure Claude Code compliance
- Create instruction inheritance patterns supporting hook-based context engineering principles

### Hook Implementation Examples

**SubagentStop Hook for Stage Transition:**

```python
# .claude/hooks/vmodel_stage_transition.py
import json
import sys
import os


def validate_stage_completion():
    project_dir = os.environ.get("CLAUDE_PROJECT_DIR")
    state_file = os.path.join(project_dir, ".agilevv", "state.json")

    # Load current V-Model state
    with open(state_file, "r") as f:
        state = json.load(f)

    current_stage = state.get("current_stage")

    # Validate stage completion criteria
    if not validate_stage_artifacts(current_stage):
        print(
            json.dumps({"decision": "block", "reason": f"V-Model {current_stage} stage incomplete"})
        )
        sys.exit(2)

    # Transfer context to next stage
    transfer_context_to_next_stage(current_stage)
    print(json.dumps({"decision": "allow"}))
```

**PreToolUse Hook for Context Validation:**

```python
# .claude/hooks/context_validation.py
import json
import sys
from jsonschema import validate, ValidationError


def validate_task_context():
    tool_input = json.loads(os.environ.get("CLAUDE_TOOL_INPUT", "{}"))

    if tool_input.get("subagent_type") in ["requirements-analyst", "architect", "developer"]:
        context_schema = load_vmodel_schema(tool_input["subagent_type"])

        try:
            validate(tool_input.get("prompt", {}), context_schema)
        except ValidationError as e:
            print(
                json.dumps(
                    {"decision": "block", "reason": f"Context validation failed: {e.message}"}
                )
            )
            sys.exit(2)

    print(json.dumps({"decision": "allow"}))
```

## Approach

### Phase 1: Hook Infrastructure Setup

1. Create .claude/hooks/ directory structure with Python validation scripts
1. Implement basic hook event handlers for SubagentStop, PreToolUse, PostToolUse
1. Establish .claude/config.json with initial hook mappings
1. Create context validation schemas for each V-Model stage

### Phase 2: V-Model Integration

1. Migrate existing Jinja2 templates to Claude Code agent format
1. Implement context transfer mechanisms between V-Model stages
1. Create stage-specific validation hooks for quality gates
1. Establish error recovery and rollback patterns

### Phase 3: Subagent Standardization

1. Convert VeriFlowCC agents to Claude Code subagent specifications
1. Implement tool permission mapping and security constraints
1. Create agent registry with kebab-case naming conventions
1. Establish subagent communication protocols

### Phase 4: Quality Assurance Integration

1. Deploy comprehensive validation hooks across all V-Model stages
1. Implement automated quality checks and artifact validation
1. Create performance monitoring and metrics collection
1. Establish testing patterns for hook-based workflows

## External Dependencies

Since this implementation focuses on internal standardization using Claude Code hooks and existing infrastructure, no new external dependencies are required:

- **Existing Claude Code Hooks** - Native workflow automation capability
- **Existing Python Environment** - For hook script execution
- **Existing JSON Schema** - Enhanced for context validation in hooks
- **Existing Pydantic** - Extended for V-Model context schema validation

All dependencies leverage VeriFlowCC's current technology stack with hooks providing the coordination layer.
