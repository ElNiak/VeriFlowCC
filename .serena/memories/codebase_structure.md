# VeriFlowCC Codebase Structure

## Root Directory

```
VeriFlowCC/
├── verifflowcc/           # Main Python package
├── tests/                 # Test suite
├── docs/                  # Documentation
├── .claude/              # Claude-specific configurations
├── CLAUDE.md             # Project memory and instructions
├── README.md             # Project overview and documentation
├── pyproject.toml        # Project configuration and dependencies
├── ruff.toml             # Ruff linter/formatter configuration
├── .pre-commit-config.yaml # Pre-commit hooks configuration
├── pytest.ini           # Pytest configuration
└── .gitignore            # Git ignore patterns
```

## Main Package Structure (`verifflowcc/`)

```
verifflowcc/
├── __init__.py           # Package initialization
├── cli.py                # Main CLI entry point with Typer
├── core/                 # Core business logic
│   ├── __init__.py
│   ├── orchestrator.py   # V-Model workflow orchestration
│   ├── vmodel.py         # V-Model stage definitions
│   ├── path_config.py    # Test isolation and path management
│   └── git_integration.py # Git operations and checkpointing
├── agents/               # Agent implementations
│   ├── __init__.py
│   ├── base.py           # Base agent class
│   ├── requirements_analyst.py # Requirements analysis
│   ├── architect.py      # System design and architecture
│   ├── developer.py      # Code implementation
│   ├── qa_tester.py      # Testing and verification
│   └── integration.py    # Integration and deployment
└── schemas/              # Pydantic data models
    ├── __init__.py
    └── agent_schemas.py  # Agent communication schemas
```

## Test Structure (`tests/`)

```
tests/
├── __init__.py
├── conftest.py           # Pytest configuration and fixtures
├── test_cli.py           # CLI interface tests
├── test_integration.py   # Main integration tests
├── test_examples.py      # Test isolation examples
├── core/                 # Core module tests
│   └── test_path_config.py
├── agents/               # Agent-specific tests
│   ├── __init__.py
│   ├── test_architect.py
│   ├── test_developer.py
│   ├── test_integration.py
│   └── test_qa_tester.py
├── schemas/              # Schema validation tests
│   ├── __init__.py
│   └── test_agent_schemas.py
└── integration/          # Integration test suite
    ├── test_path_config_integration.py
    └── test_orchestrator_integration.py
```

## Key Files and Their Purposes

### CLI Interface (`cli.py`)

- Main entry point using Typer framework
- Commands: init, plan, sprint, status, validate, checkpoint
- Handles keyboard interrupts gracefully
- Manages PathConfig for test isolation

### Core Components

- **`orchestrator.py`**: Central V-Model workflow controller
- **`vmodel.py`**: V-Model stage definitions and transitions
- **`path_config.py`**: Test isolation system with directory management
- **`git_integration.py`**: Git operations and automated checkpointing

### Agent System

- **`base.py`**: Common agent interface and functionality
- **Specialized agents**: Each handles specific V-Model phases
- **Communication**: Uses Pydantic schemas for structured data exchange

### Configuration Files

- **`pyproject.toml`**: Modern Python project configuration
- **`ruff.toml`**: Linting and formatting rules
- **`.pre-commit-config.yaml`**: Automated code quality checks
- **`pytest.ini`**: Test configuration with markers and coverage

## Test Organization

Tests are organized by:

- **Module**: Core, agents, schemas, integration
- **Type**: Unit, integration, e2e (using pytest markers)
- **Stage**: Planning, requirements, design, coding, testing, validation
- **Priority**: Critical, high, medium, low

## Directory Conventions

- **Source code**: `verifflowcc/` package directory
- **Tests**: Mirror source structure in `tests/`
- **Documentation**: `docs/` for detailed documentation
- **Claude config**: `.claude/` for AI-specific configurations
- **Artifacts**: `.agilevv/` for project artifacts (auto-generated)

## Import Structure

- **Absolute imports**: Always use from package root
- **Type checking**: Import typing modules in TYPE_CHECKING blocks
- **Dependencies**: Clearly separated into core vs dev dependencies

## File Naming Patterns

- **Python modules**: snake_case
- **Test files**: `test_*.py` prefix
- **Configuration**: Standard names (pyproject.toml, ruff.toml, etc.)
- **Documentation**: kebab-case for markdown files
