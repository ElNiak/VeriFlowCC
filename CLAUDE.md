# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**VeriFlowCC** is a Verification Flow Command Center that integrates Anthropic's Claude models (Opus 4.1 and Sonnet 4) to create a structured, agent-driven software development pipeline following the Agile V-Model methodology.

Key Concepts:
- **Agile V-Model**: Rigorous verification and validation at each development stage
- **Multi-Agent Architecture**: Planner agent (Opus 4.1) for strategy, Worker agents (Sonnet 4) for execution
- **Gated Stages**: Sequential phases that must be completed before progression
- **Hook-Gated Pipeline**: Each stage has exit criteria that must be met before progression

## Architecture & Core Components

### Development Pipeline Stages
1. **Planning** → Requirements analysis and task decomposition (Opus 4.1)
2. **Design** → Architecture and solution specification (Sonnet 4)
3. **Coding** → Implementation with file operations (Sonnet 4)
4. **Testing** → Test execution and analysis (Sonnet 4)
5. **Validation** → Final verification against acceptance criteria (Opus 4.1)

### Current Project Structure
```
VeriFlowCC/
├── verifflowcc/
│   ├── cli.py                # Main CLI entry point (Typer-based)
│   ├── agents/               # Agent implementations (currently empty)
│   ├── core/                 # Core business logic (currently empty)
│   ├── prompts/              # Jinja2 prompt templates
│   │   ├── planner.jinja2
│   │   ├── design.jinja2
│   │   ├── coding.jinja2
│   │   ├── testing.jinja2
│   │   └── validation.jinja2
│   └── schemas/              # Pydantic models
│       ├── plan.py
│       ├── task.py
│       ├── test_report.py
│       └── validation.py
├── tests/                    # Test suite
│   ├── test_cli.py
│   └── test_schemas/
├── .claude/                  # Claude agent definitions
│   └── agents/              # Agent role specifications
└── docs/                    # Documentation
    ├── roadmap/             # Sprint planning docs
    └── AgileVV/             # Methodology documentation
```

## Development Commands

### Setup & Installation
```bash
# Using UV package manager (recommended - 10-100x faster than pip)
uv sync                      # Install dependencies
uv run verifflowcc --help   # Run CLI

# Alternative with pip
pip install -e .            # Install in editable mode
verifflowcc --help         # Run CLI
```

### Testing
```bash
# Run all tests with coverage
uv run pytest

# Run specific test categories
uv run pytest tests/test_schemas/
uv run pytest tests/test_cli.py

# Run with async support
uv run pytest --asyncio-mode=auto

# Run with verbose output
uv run pytest -v --cov=verifflowcc --cov-report=term-missing
```

### Linting & Code Quality
```bash
# Run all pre-commit hooks
pre-commit run --all-files

# Individual tools
uv run ruff check .          # Lint code
uv run ruff check --fix .    # Auto-fix issues
uv run ruff format .         # Format code
uv run mypy verifflowcc      # Type checking
```

## Development Workflow

### Sprint Structure
Following the 12-week roadmap:
- **Sprint 0** (Weeks 1-2): Planning & Design - PRD, C4 diagrams, CLI scaffold
- **Sprint 1** (Weeks 3-4): Planner MVE - Opus 4.1 integration
- **Sprint 2** (Weeks 5-6): Coding Agent MVE - Sonnet 4 code generation
- **Sprint 3** (Weeks 8-9): Testing Agent + Fix Loop
- **Validation Gate** (Week 10): Acceptance criteria verification

### Gate Criteria
Each stage must satisfy exit criteria before progression:
```python
def gate_passed(stage: Stage, artifact: Path) -> bool:
    return artifact.exists() and validate_schema(artifact)
```

### Checkpointing
- Git commits at stage boundaries
- Rollback capability on test failures
- Persistent memory updates in CLAUDE.md

## MCP Integration

### Configured MCP Servers
1. **sequential-thinking**: Multi-step reasoning and planning
2. **perplexity-ask**: External knowledge queries
3. **context7**: Documentation retrieval
4. **serena**: Code analysis and semantic operations
5. **consult7**: Code consultation with Google AI

### Agent-MCP Interaction
- Planner uses sequential-thinking for decomposition
- Coding agent uses serena for code analysis
- Testing agent uses shell tools via MCP
- All agents can query documentation via context7

## Key Implementation Priorities

### Current Sprint (Sprint 0 - Planning & Design)
1. Finalize PRD and architecture documentation
2. Create Jinja2 prompt templates for each agent role
3. Define Pydantic schemas (Plan, Task, TestReport)
4. Implement CLI scaffold with Typer
5. Set up CI/CD with pre-commit hooks

### Technical Decisions
- **Python 3.10+** for modern type hints and async support
- **Poetry** for dependency management
- **Typer** for CLI interface (user-friendly, type-safe)
- **Pydantic** for schema validation and structured outputs
- **Jinja2** for prompt templating
- **Claude SDK** for API integration
- **Git** for version control and checkpointing

### Context Management Strategy
- Isolated contexts per agent (no monolithic context)
- Structured data transfer between stages (JSON/YAML)
- Token efficiency through context chunking
- Persistent memory in CLAUDE.md for cross-session continuity

## Important Files & References

### Documentation
- `/README.md` - Complete PRD and architecture overview
- `/docs/roadmap/ROADMAP.md` - 12-week development plan
- `/docs/roadmap/Sprint-*.md` - Sprint-specific deliverables
- `/docs/AgileVV/AgileVV.md` - Agile V-Model methodology

### Configuration
- `/.mcp.example.json` - MCP server configuration example
- `/pyproject.toml` - Python project dependencies
- `/.pre-commit-config.yaml` - Code quality hooks
- `/PYTHON_GUIDELINES.md` - Python coding standards for this project

## Development Guidelines

1. **V-Model Compliance**: Never skip stages; always verify outputs
2. **Token Efficiency**: Use context isolation and structured prompts
3. **Observability**: Log all agent actions and decisions
4. **Safety**: Require user approval for file writes and dangerous operations
5. **Modularity**: Keep agent modules independent and testable
6. **Python Style**: Follow PYTHON_GUIDELINES.md - use UV, type hints, Pydantic validation
7. **Testing**: Maintain minimum 80% code coverage with pytest

## Key Implementation Patterns

### Agent Communication
```python
# Use Pydantic models for structured data transfer
from pydantic import BaseModel
from typing import List

class PlannerOutput(BaseModel):
    requirements: List[str]
    tasks: List[Task]
    acceptance_criteria: List[str]
```

### Error Handling
- Always use specific exception types
- Implement retry logic with exponential backoff for API calls
- Validate all LLM outputs with Pydantic schemas
- Log errors with structured context

### File Operations
- Use pathlib.Path for all file operations
- Validate paths before operations
- Use context managers for file handling

## Agent-OS Integration (Sprint 0.5 - Active)

### State Management Architecture
**Decision:** Hybrid approach (ADR-001)
- `.vv/state.json` for workflow state persistence (finite state machine)
- Pydantic models for data validation
- Git-based checkpointing at gate boundaries
- State transitions follow V-Model rules with enforcement

### Hook Integration Strategy
**Decision:** Merged architecture with precedence (ADR-002)
```
~/.claude/hooks/
├── before_*.d/
│   ├── 00-49: UX hooks (Agent-OS banners)
│   ├── 50-99: Gate enforcement (VeriFlowCC)
│   └── 100+: Cleanup/utility hooks
```
- UX hooks provide feedback, gate hooks enforce stage rules
- Performance target: <100ms overhead per operation

### Helper Agent Pattern
**Decision:** Delegation pattern (ADR-003)
- Helper agents in `.claude/agents/helpers/` (markdown format)
- **context-fetcher**: Gathers relevant code context
- **git-workflow**: Manages git operations and CHANGELOG
- **test-runner**: Executes and analyzes tests
- Token reduction target: 30-50% through focused context

### Memory Hierarchy
**Decision:** 4-layer system (ADR-004)
1. **Project Layer**: CLAUDE.md, conventions (persistent)
2. **Sprint Layer**: Goals, progress, context (sprint-scoped)
3. **Stage Layer**: Artifacts, feedback (stage-scoped)
4. **Agent Layer**: Runtime prompt and tools
- Token allocation varies by agent role
- Selective loading based on relevance

## Sprint Status

### Current Sprint: 0.5 - Foundation Completion
- Completing agent context definitions
- Establishing state management
- Defining V-Model gate criteria
- Creating test framework

### Upcoming Sprints
- **Sprint 1**: Workflow Enforcement (pause-resume, hooks, CLI)
- **Sprint 2**: Helper Agents & Tooling
- **Sprint 3**: UX & Automation (CHANGELOG, demos)

## Claude Agent Definitions

The project includes pre-configured agent roles in `.claude/agents/`:

### Primary Agents (Stage-bound)
- **planner**: Strategic planning and decomposition (Opus 4.1)
- **verification/** agents: Requirements, architecture, implementation
- **validation/** agents: Testing, integration, acceptance
- **generic/** agents: Code review, debugging, documentation

### Helper Agents (Stateless)
- **helpers/context-fetcher.md**: Efficient context retrieval
- **helpers/git-workflow.md**: Version control operations
- **helpers/test-runner.md**: Test execution and analysis

## V-Model Gate Criteria

Each stage transition requires gate validation:
- **Planning → Requirements**: Requirements documented, acceptance criteria defined
- **Requirements → Design**: INVEST/SMART criteria met, requirements verified
- **Design → Coding**: Architecture documented, interfaces defined
- **Coding → Testing**: Code complete, compiles, static analysis passed
- **Testing → Validation**: All tests passed, coverage ≥80%
- **Validation → Complete**: Acceptance criteria validated, CHANGELOG updated

## CLI Commands (VV Subcommands)

```bash
vv sprint-init <ID>    # Initialize new sprint
vv resume             # Resume from current state
vv status            # Show workflow status
vv rollback          # Rollback to previous gate
vv checkpoint        # Manual checkpoint creation
```

## Testing Requirements

- Minimum 80% code coverage
- All unit tests must pass for gate progression
- Integration tests validate stage transitions
- Use `uv run pytest` for test execution
- Test reports stored in `sprints/<ID>/artifacts/testing/`

## Notes for Future Claude Instances

- This project implements the Agile V-Model with AI agents
- The Planner (Opus 4.1) is strategic; Workers (Sonnet 4) are tactical
- Always maintain gate criteria between stages
- Git checkpoints are mandatory at stage boundaries
- Context isolation is critical for token efficiency
- User approval is required for impactful actions
- Project uses UV package manager for speed (not Poetry)
- Schemas are already defined in `verifflowcc/schemas/`
- Prompt templates exist in `verifflowcc/prompts/`
- State persists in `.vv/state.json` across sessions
- Helper agents reduce token usage through delegation
- Hooks enforce stage-appropriate tool usage
- CHANGELOG auto-updates on validation success
