# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**VeriFlowCC** (Verification Flow Command Center) is an AI-driven development pipeline that integrates Anthropic's Claude-Code with the Agile V-Model methodology. It enforces rigorous verification and validation (V&V) at each stage of feature development through a structured, agent-driven approach.

## Development Commands

### Package Management

```bash
# Install dependencies (using UV - 10-100x faster than pip)
uv sync

# Add new dependencies
uv add <package>

# Add dev dependencies
uv add --dev <package>
```

### Testing

```bash
# Run all tests with coverage
uv run pytest

# Run specific test file
uv run pytest tests/test_file.py

# Run tests with specific markers
uv run pytest -m unit  # unit tests only
uv run pytest -m integration  # integration tests only
uv run pytest -m e2e  # end-to-end tests only

# Run tests with coverage report
uv run pytest --cov=verifflowcc --cov-report=term-missing

# Run tests in parallel (faster)
uv run pytest -n auto
```

### Code Quality

```bash
# Run linter (auto-fix enabled)
uv run ruff check --fix

# Format code
uv run ruff format

# Type checking
uv run mypy verifflowcc

# Run all pre-commit hooks
uv run pre-commit run --all-files

# Run specific pre-commit hook
uv run pre-commit run ruff --all-files
```

### Development Workflow

```bash
# Run the CLI
uv run verifflowcc

# Install in development mode
uv pip install -e .
```

## Architecture

### V-Model Implementation

The project implements the Agile V-Model through a structured pipeline:

1. **Requirements** → Design → Code → Test → **Validation**
1. Each sprint is a complete V-cycle with verification gates
1. Subagents handle specific phases (Requirements, Design, Development, QA)

### Directory Structure

```
verifflowcc/          # Main package (currently empty - to be implemented)
├── agents/           # Agent implementations for each V-Model phase
├── core/             # Orchestrator and core business logic
├── prompts/          # Jinja2 templates for agent prompts
├── schemas/          # Pydantic models for structured data
└── cli.py            # CLI entry point

.agilevv/             # Project artifacts (auto-generated)
├── backlog.md        # User stories and requirements
├── architecture.md   # System design documentation
└── config.yaml       # V-Model gating configuration

tests/                # Test suite
├── agents/           # Agent-specific tests
├── integration/      # Integration tests
└── e2e/              # End-to-end workflow tests
```

### Key Components

#### Orchestrator

- Controls V-Model workflow execution
- Manages stage transitions and gating
- Coordinates subagent invocations
- Handles checkpointing and rollback

#### Subagents (AI Personas)

- **Requirements Analyst**: Elaborates user stories, defines acceptance criteria
- **Architect/Designer**: Creates system design, updates architecture
- **Developer**: Implements features following design specs
- **QA/Tester**: Writes and executes tests, validates acceptance criteria
- **Integration Engineer**: Handles system integration and deployment

#### Memory Management

- **CLAUDE.md**: Project-wide persistent memory
- **backlog.md**: Living requirements document
- **architecture.md**: Evolving design documentation
- Git checkpointing for rollback capability

## Coding Standards

### Python Guidelines

- Follow PEP 8 with 100-character line limit
- Use type hints for all functions and classes
- Implement async/await for AI agent calls
- Use Pydantic for data validation
- Never use bare `except:` - specify exception types
- Structure agent communication with Pydantic models

### Testing Requirements

- Minimum 80% code coverage (enforced by pytest)
- Write tests for all new features
- Use markers to categorize tests (unit, integration, e2e)
- Follow AAA pattern (Arrange, Act, Assert)

### Error Handling

- Log errors with structured logging
- Implement retry logic with exponential backoff for API calls
- Validate all LLM outputs with Pydantic before processing
- Use proper exception hierarchy

## V-Model Workflow

### Sprint 0 (Foundation)

1. Collect vision and initial requirements
1. Create story map/backlog
1. Draft component architecture
1. Setup project memory and repository

### Sprint N (Feature Development)

1. **Plan**: Select story, refine requirements
1. **Design**: Update architecture for feature
1. **Code**: Implement following design
1. **Verify**: Write and run tests
1. **Validate**: Confirm acceptance criteria
1. **Integrate**: Run regression tests
1. **Document**: Update artifacts and memory

### Gating Controls

- **Hard gating**: No proceeding until phase criteria met
- **Soft gating**: Warnings but can continue
- Configured via `.agilevv/config.yaml`

## Tool Integration

### MCP (Model Context Protocol)

- Standardized interface for external tool calls
- GitHub integration for PR creation
- Documentation lookup capabilities

### Hooks

- **PreToolUse**: Enforce workflow rules before actions
- **PostToolUse**: Trigger automatic follow-ups (linting, formatting)
- **SubagentStop**: Chain between V-Model phases

## Important Notes

- The `verifflowcc/` package directory is currently empty - implementation pending
- Project follows "plan-then-act" workflow pattern
- All artifacts are version-controlled for traceability
- Context engineering minimizes token usage
- Checkpointing enables safe rollback on failures

## Testing Philosophy

Tests are organized by V-Model stage and type:

- **Stage markers**: planning, requirements, design, coding, testing, integration, validation
- **Type markers**: unit, integration, e2e, smoke, regression
- **Priority markers**: critical, high, medium, low

Run targeted test suites based on current development phase.
