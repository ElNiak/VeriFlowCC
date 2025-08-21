# VeriFlowCC Technology Stack

## Core Technologies

- **Python 3.10+**: Main programming language
- **Typer**: CLI framework with rich terminal UI support
- **Rich**: Terminal formatting and UI enhancements
- **Pydantic v2**: Data validation and settings management
- **PyYAML**: YAML configuration handling
- **Jinja2**: Template engine for prompt generation

## Development Dependencies

- **pytest**: Testing framework with async support
- **pytest-cov**: Code coverage reporting
- **pytest-asyncio**: Async test support
- **pytest-xdist**: Parallel test execution
- **mypy**: Static type checking
- **ruff**: Fast Python linter and formatter
- **pre-commit**: Git hook framework

## Build System

- **Hatchling**: Modern Python build backend
- **UV**: Ultra-fast Python package manager (10-100x faster than pip)

## AI Integration

- **Claude-Code SDK**: Interface with Anthropic's Claude models
- **Opus 4.1**: Planner agent for strategic decisions
- **Sonnet 4**: Worker agents for specialized tasks

## Version Control & CI/CD

- **Git**: Version control with automated checkpointing
- **Pre-commit hooks**: Automated code quality checks
- **GitHub Actions**: Continuous integration (planned)

## Architecture Components

- **MCP (Model Context Protocol)**: Standardized tool interface
- **Subagents**: Specialized AI personas with isolated contexts
- **Orchestrator**: Central workflow controller
- **PathConfig**: Test isolation system

## Key Libraries Used

- **subprocess**: Safe command execution
- **pathlib**: Modern path handling
- **asyncio**: Asynchronous programming support
- **logging**: Structured logging and observability

## Testing Architecture

- **Test Isolation**: PathConfig system prevents test interference
- **Pytest fixtures**: Function, module, and session scopes
- **AgileVVDirFactory**: Factory pattern for complex test setups
- **Coverage requirements**: Minimum 80% code coverage enforced
