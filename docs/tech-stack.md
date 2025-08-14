# VeriFlowCC Technology Stack

## Overview

VeriFlowCC leverages modern Python development tools combined with Claude Code SDK for AI-powered V-Model development workflows.

## Core Technologies

### AI & Language Models

- **Claude Code SDK** (`claude-code-sdk>=0.1.0`)

  - Primary interface for Claude AI models
  - Supports streaming responses and session management
  - Integrated across all V-Model agents
  - Mock mode for testing and development

- **Claude Models**

  - **Claude Opus 4.1**: Strategic planning and complex reasoning
  - **Claude Sonnet**: Implementation, testing, and specialized tasks
  - Context management and prompt engineering

### Python Ecosystem

- **Python 3.10+**: Core runtime environment
- **UV Package Manager**: Fast dependency management (10-100x faster than pip)
- **Typer**: CLI framework with rich features
- **Rich**: Enhanced terminal output and progress indicators
- **Pydantic v2**: Data validation and structured responses
- **PyYAML**: Configuration file management
- **Jinja2**: Template engine for AI prompts

### Development Tools

- **pytest**: Testing framework with coverage reporting
- **Ruff**: Lightning-fast linting and formatting
- **mypy**: Static type checking
- **pre-commit**: Git hooks for code quality

### V-Model Agent Architecture

All agents use the Claude Code SDK with specialized configurations:

#### Requirements Analyst Agent

- **Purpose**: INVEST/SMART requirements validation
- **Template**: `requirements.j2`
- **SDK Features**: Session persistence, validation scoring
- **Outputs**: Structured requirements with acceptance criteria

#### Architect Agent

- **Purpose**: System design and PlantUML diagrams
- **Template**: `architect.j2`
- **SDK Features**: Design documentation generation
- **Outputs**: C4 diagrams, interface specifications

#### Developer Agent

- **Purpose**: Source code generation and quality validation
- **Template**: `developer.j2`
- **SDK Features**: File creation, code quality metrics
- **Outputs**: Implemented features with quality scores

#### QA Tester Agent

- **Purpose**: Comprehensive testing strategies
- **Template**: `qa.j2`
- **SDK Features**: Test execution coordination
- **Outputs**: Test plans, execution results, quality assessments

#### Integration Agent

- **Purpose**: End-to-end validation and GO/NO-GO decisions
- **Template**: `integration.j2`
- **SDK Features**: System-wide validation, release recommendations
- **Outputs**: Integration reports, deployment readiness

### Configuration Management

#### SDK Configuration (`SDKConfig`)

```python
class SDKConfig:
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    timeout: int = 30
    max_retries: int = 3
```

#### Path Management (`PathConfig`)

- Configurable `.agilevv/` base directory
- Test isolation with `.agilevv-test/`
- Security boundaries and path traversal protection

#### Agent Factory Pattern

- Centralized agent creation
- Consistent SDK configuration
- Mock mode support for testing

### Quality Gates & Metrics

#### V-Model Quality Thresholds

```yaml
quality_thresholds:
  test_coverage: 80
  code_quality_score: 70
  requirements_validation_score: 80
  overall_readiness_score: 75
```

#### Gating Modes

- **Hard Gating**: Blocks progression until criteria met
- **Soft Gating**: Warnings but allows continuation
- **Off**: No quality enforcement

### File Structure Integration

```
verifflowcc/
├── agents/          # SDK-integrated V-Model agents
├── core/            # Orchestrator and configuration
├── prompts/         # Jinja2 templates for each stage
└── schemas/         # Pydantic models for validation

.agilevv/           # Project artifacts (auto-generated)
├── artifacts/      # Stage outputs and reports
├── checkpoints/    # Git-based state management
└── config.yaml     # V-Model gating configuration
```

## Development Workflow

### Package Management

```bash
# Install dependencies
uv sync

# Add new dependencies
uv add <package>

# Development dependencies
uv add --dev <package>
```

### Code Quality Pipeline

```bash
# Linting with auto-fix
uv run ruff check --fix

# Code formatting
uv run ruff format

# Type checking
uv run mypy verifflowcc

# Run all pre-commit hooks
uv run pre-commit run --all-files
```

### Testing Framework

```bash
# Run all tests with coverage
uv run pytest --cov=verifflowcc --cov-report=term-missing

# Test isolation features
uv run pytest --keep-test-dirs  # Keep test directories for debugging

# Parallel test execution
uv run pytest -n auto
```

## Integration Points

### Git Integration

- Automatic checkpointing at V-Model gates
- Rollback capability on validation failures
- Branch management for sprint workflows

### MCP (Model Context Protocol)

- Standardized tool interface
- GitHub integration capabilities
- Documentation lookup and retrieval

### Session Management

- Persistent agent state across sprints
- Context optimization for token efficiency
- Memory management between V-Model stages

## Performance Characteristics

### Token Optimization

- Stage-specific context isolation
- Jinja2 template reuse
- Session state persistence
- Context window management

### Execution Speed

- UV package manager for fast dependency resolution
- Parallel test execution support
- Streaming responses from Claude Code SDK
- Efficient artifact caching

## Security Considerations

### Path Security

- Configurable base directories
- Path traversal prevention
- Test environment isolation

### API Security

- Secure credential management
- Configurable timeout and retry limits
- Mock mode for development

### Code Generation Safety

- Quality validation before acceptance
- Rollback mechanisms on failures
- Human oversight at quality gates

## Future Extensibility

### Agent Expansion

- Factory pattern supports new agent types
- Template-based prompt engineering
- Consistent SDK integration patterns

### Tool Integration

- MCP server support for new tools
- Configurable external integrations
- Plugin architecture potential

### Scaling Considerations

- Multi-project workspace support
- Team collaboration features
- Enterprise deployment patterns

## Version History

- **v0.1.0**: Initial mock implementation
- **v0.2.0**: Claude Code SDK integration
  - All agents migrated to real AI interaction
  - Comprehensive prompt templates
  - Quality gates and validation
  - Session management and persistence

## Dependencies Summary

```toml
[dependencies]
typer = {extras = ["all"], version = ">=0.12.0"}
rich = ">=13.0.0"
pydantic = ">=2.0.0"
pyyaml = ">=6.0.0"
jinja2 = ">=3.1.0"
claude-code-sdk = ">=0.1.0"

[dev-dependencies]
pytest = ">=7.0.0"
pytest-cov = ">=4.0.0"
pytest-xdist = ">=3.0.0"
ruff = ">=0.1.0"
mypy = ">=1.0.0"
pre-commit = ">=3.0.0"
```

This technology stack provides a robust foundation for AI-powered V-Model development workflows while maintaining flexibility for future enhancements and integrations.
