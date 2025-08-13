# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**VeriFlowCC** (Verification Flow Command Center) is an AI-driven development pipeline that integrates Claude Code SDK with the Agile V-Model methodology. It enforces rigorous verification and validation (V&V) at each stage of feature development through a structured, agent-driven approach powered by real Claude AI agents.

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
uv run pytest --log-cli-level=DEBUG --cov=verifflowcc --cov-report=term-missing

# Run tests in parallel (faster)
uv run pytest -n auto

# Test Isolation Features (NEW)
# Run tests with isolated directories
uv run pytest --keep-test-dirs  # Keep test directories for debugging

# Run example tests
uv run pytest tests/test_examples.py -v  # See isolation examples in action

# Debug test environments
uv run pytest tests/test_examples.py::TestDebuggingExamples -v -s
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

## Claude Code SDK Setup

VeriFlowCC uses the Claude Code SDK for real AI-powered V-Model execution. All agents are now integrated with the SDK for production-ready functionality.

### API Key Configuration

Set your Anthropic API key for SDK access:

```bash
# Option 1: Environment variable (recommended)
export ANTHROPIC_API_KEY="your-api-key-here"

# Option 2: Claude CLI configuration (if using Claude CLI)
claude auth login
```

### SDK Configuration

The SDK is configured through the `SDKConfig` class in `verifflowcc/core/sdk_config.py`:

```python
class SDKConfig:
    api_key: Optional[str] = None          # Auto-detected from environment
    base_url: Optional[str] = None         # Uses Claude Code SDK default
    timeout: int = 30                      # Request timeout in seconds
    max_retries: int = 3                   # Retry attempts on failure
```

### Agent Configuration

Each V-Model agent has SDK-specific settings:

```yaml
agents:
  requirements_analyst:
    timeout: 60                    # Longer timeout for requirements analysis
  architect:
    timeout: 90                    # Extended time for design work
  developer:
    timeout: 120                   # Most time for implementation
  qa_tester:
    timeout: 90                    # Testing and validation
  integration:
    timeout: 150                   # Comprehensive integration assessment
```

### Mock Mode for Development

For testing without API costs:

```bash
# Run in mock mode (no real SDK calls)
uv run verifflowcc --mock-mode

# Or set environment variable
export VERIFFLOWCC_MOCK_MODE=true
uv run verifflowcc
```

### SDK Features Used

- **Streaming Responses**: Real-time feedback during agent execution
- **Session Management**: Context preservation across V-Model stages
- **Specialized Prompts**: Jinja2 templates optimized for each agent type
- **Quality Validation**: Structured output parsing with Pydantic
- **Error Handling**: Robust retry mechanisms and fallback strategies

## Architecture

### V-Model Implementation

The project implements the Agile V-Model through a structured pipeline:

1. **Requirements** → Design → Code → Test → **Validation**
1. Each sprint is a complete V-cycle with verification gates
1. Subagents handle specific phases (Requirements, Design, Development, QA)

### Directory Structure

```
verifflowcc/          # Main package - Claude Code SDK integrated
├── agents/           # SDK-powered V-Model agents (complete implementation)
│   ├── base.py       # BaseAgent with Claude Code SDK integration
│   ├── factory.py    # AgentFactory for centralized agent creation
│   ├── requirements_analyst.py  # INVEST/SMART requirements validation
│   ├── architect.py  # System design and PlantUML generation
│   ├── developer.py  # Source code generation and quality metrics
│   ├── qa_tester.py  # Comprehensive testing strategies
│   └── integration.py # GO/NO-GO release decision making
├── core/             # Orchestrator and core business logic
│   ├── orchestrator.py # V-Model workflow with SDK coordination
│   ├── sdk_config.py   # Claude Code SDK configuration management
│   ├── path_config.py  # Project path management
│   └── vmodel.py       # V-Model stage definitions
├── prompts/          # Jinja2 templates for agent prompts
│   ├── requirements.j2 # Requirements analysis template
│   ├── architect.j2    # Architecture design template
│   ├── developer.j2    # Development implementation template
│   ├── qa.j2          # Quality assurance template
│   └── integration.j2  # Integration validation template
├── schemas/          # Pydantic models for structured data
└── cli.py            # CLI entry point

.agilevv/             # Project artifacts (auto-generated)
├── artifacts/        # Stage outputs and reports
├── checkpoints/      # Git-based state management
├── backlog.md        # User stories and requirements
├── architecture.md   # System design documentation
├── config.yaml       # V-Model gating configuration
└── state.json        # Orchestrator state with session data

tests/                # Test suite with isolation framework
├── agents/           # Agent-specific tests
├── integration/      # Integration tests
├── e2e/              # End-to-end workflow tests
└── fixtures/         # Test isolation and factory patterns
```

### Key Components

#### Orchestrator

- Controls V-Model workflow execution
- Manages stage transitions and gating
- Coordinates subagent invocations
- Handles checkpointing and rollback

#### SDK-Powered Agents (AI Personas)

- **Requirements Analyst**: Real AI validation of INVEST/SMART criteria with quality scoring
- **Architect/Designer**: AI-powered system design with PlantUML diagram generation
- **Developer**: Actual source code generation with quality metrics and file creation
- **QA/Tester**: Comprehensive test strategy development and execution coordination
- **Integration Agent**: End-to-end validation with GO/NO-GO release decision making

All agents now use the Claude Code SDK for real AI-powered execution with:
- Specialized Jinja2 prompt templates for each V-Model stage
- Session state persistence across the workflow
- Streaming responses for real-time feedback
- Quality validation and metrics collection

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

### Test Isolation Framework

VeriFlowCC provides a comprehensive test isolation framework to ensure tests don't interfere with production or each other:

#### PathConfig System

- **Configurable base directory**: Tests use `.agilevv-test/` instead of `.agilevv/`
- **Environment variable support**: `AGILEVV_BASE_DIR` controls the base directory
- **Security features**: Prevents path traversal and enforces directory boundaries
- **Test detection**: Automatically detects test environments based on directory naming

#### Pytest Fixtures

Three fixture scopes for different testing needs:

1. **`isolated_agilevv_dir`** (function scope)

   - Each test gets a unique directory
   - Complete isolation between tests
   - Automatic cleanup after each test

1. **`shared_agilevv_dir`** (module scope)

   - Shared directory for all tests in a module
   - Useful for integration tests with shared state
   - Cleaned up after module completes

1. **`session_agilevv_dir`** (session scope)

   - Single directory for entire test session
   - For expensive setup that should only happen once
   - Cleaned up after all tests complete

#### AgileVVDirFactory

Factory pattern for complex test setups:

```python
# Create test environment with pre-populated data
config = agilevv_factory.create_with_backlog(stories=[...])
config = agilevv_factory.create_with_sprint(sprint_num=1)
config = agilevv_factory.create_full_structure()
```

#### Debugging Support

- Use `--keep-test-dirs` flag to preserve test directories after tests
- Helpful for debugging failed tests and inspecting test artifacts
- Example: `uv run pytest --keep-test-dirs tests/failing_test.py`

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

- **SDK Integration Complete**: Full Claude Code SDK implementation with real AI agents
- **Production Ready**: All V-Model stages now have functional AI-powered agents
- **Quality Gates**: Comprehensive validation with configurable thresholds
- **Session Persistence**: Context maintained across all V-Model stages
- **Mock Mode**: Available for testing and development without API costs
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
