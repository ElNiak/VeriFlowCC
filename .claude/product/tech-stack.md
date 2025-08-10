# VeriFlowCC Technology Stack

## Core Technologies

### Language & Runtime

- **Python 3.10+** - Primary language for implementation
  - Modern async/await support
  - Type hints for clarity
  - Strong ecosystem for CLI tools

### Package Management

- **UV** - Ultra-fast Python package manager (10-100x faster than pip)
  - Lock file support for reproducibility
  - Integrated virtual environment management
  - Native workspace support

## Dependencies

### Core Framework

- **anthropic** (>=0.25.0) - Claude API SDK
  - Direct integration with Claude models
  - Native agent support
  - Tool use capabilities

### CLI & Interface

- **typer** (>=0.12.0) - Modern CLI framework

  - Type-safe command definitions
  - Automatic help generation
  - Rich formatting support

- **rich** (>=13.7.0) - Terminal formatting

  - Progress bars for long operations
  - Formatted tables for status display
  - Syntax highlighting for code output

### Data & Validation

- **pydantic** (>=2.7.0) - Data validation
  - Structured agent communication
  - Schema enforcement for LLM outputs
  - Type-safe configuration

### Templates & Prompts

- **jinja2** (>=3.1.3) - Template engine
  - Agent prompt generation
  - Context injection
  - Dynamic documentation

### Version Control

- **gitpython** (>=3.1.40) - Git integration
  - Checkpoint creation
  - Rollback capabilities
  - Commit automation

### Configuration

- **pyyaml** (>=6.0.1) - YAML parsing
  - Configuration files
  - Agent definitions
  - Workflow specifications

## Development Tools

### Testing

- **pytest** (>=8.2.0) - Testing framework
  - Comprehensive test suite
  - Coverage reporting
  - Parallel execution
- **pytest-asyncio** - Async test support
- **pytest-cov** - Coverage integration

### Code Quality

- **ruff** (>=0.5.0) - Fast Python linter
  - Auto-formatting
  - Import sorting
  - Security checks
- **mypy** (>=1.10.0) - Static type checker
- **pre-commit** (>=3.7.0) - Git hooks

## Architecture Decisions

### Why Python?

- Native Claude-Code SDK support
- Excellent async capabilities for AI operations
- Rich ecosystem for CLI and automation
- Type hints for maintainability

### Why UV over pip/poetry?

- 10-100x faster installation
- Built-in workspace support
- Simpler dependency resolution
- Native lock file support

### Why Typer over Click/argparse?

- Type-safe by default
- Modern Python 3.10+ features
- Automatic documentation
- Better developer experience

### Why File-based Memory?

- Simplicity for single developers
- Git-friendly versioning
- Human-readable artifacts
- No database dependencies

### Why Pydantic?

- LLM output validation
- Structured agent communication
- Automatic schema generation
- Type safety throughout

## Integration Points

### Claude-Code Integration

- Uses native Claude-Code agent spawning
- Leverages built-in tool capabilities
- Context injection via templates
- Memory persistence via CLAUDE.md

### Git Integration

- Automatic checkpointing at gates
- Rollback on validation failures
- Commit message generation
- Branch management for sprints

### MCP Potential

- Ready for Model Context Protocol
- Extensible tool interface
- Future third-party integrations
- Standardized agent communication

## Performance Considerations

### Token Optimization

- Smart context pruning
- Selective file imports
- Compressed summaries
- Cached responses

### Execution Speed

- Async agent operations
- Parallel test execution
- UV for fast dependencies
- Minimal overhead design

## Security & Safety

### Input Validation

- Pydantic schemas for all inputs
- Sanitized file operations
- Controlled shell execution
- API key management

### Error Handling

- Structured error types
- Automatic rollback on failures
- Comprehensive logging
- Graceful degradation

## Future Considerations

### Potential Additions

- **FastAPI** - Web dashboard (Phase 4)
- **SQLite** - Optional persistent storage
- **Redis** - Caching layer
- **Docker** - Containerized agents

### Upgrade Path

- Designed for extensibility
- Plugin architecture planned
- API versioning considered
- Backward compatibility focus
