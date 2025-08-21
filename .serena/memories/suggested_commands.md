# VeriFlowCC Development Commands

## Package Management (UV - Ultra Fast)

```bash
# Install dependencies
uv sync

# Add new dependencies
uv add <package>

# Add development dependencies
uv add --dev <package>

# Install in development mode
uv pip install -e .
```

## Testing Commands

```bash
# Run all tests with coverage
uv run pytest

# Run specific test file
uv run pytest tests/test_file.py

# Run tests by markers
uv run pytest -m unit           # Unit tests only
uv run pytest -m integration    # Integration tests only
uv run pytest -m e2e           # End-to-end tests only

# Run with detailed coverage
uv run pytest --log-cli-level=DEBUG --cov=verifflowcc --cov-report=term-missing

# Run tests in parallel (faster)
uv run pytest -n auto

# Test isolation features
uv run pytest --keep-test-dirs  # Keep test directories for debugging
uv run pytest tests/test_examples.py -v  # See isolation examples
```

## Code Quality Commands

```bash
# Lint and auto-fix code
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

## VeriFlowCC CLI Commands

```bash
# Run the main CLI
uv run verifflowcc

# Alternative short command
uv run vv

# Initialize new project
uv run verifflowcc init

# Plan sprint
uv run verifflowcc plan

# Run sprint
uv run verifflowcc sprint

# Check status
uv run verifflowcc status

# Validate current state
uv run verifflowcc validate

# Checkpoint management
uv run verifflowcc checkpoint
uv run verifflowcc checkpoint list
uv run verifflowcc checkpoint restore
```

## Development Workflow

```bash
# 1. Set up development environment
uv sync

# 2. Run tests to ensure everything works
uv run pytest

# 3. Make code changes
# ... edit files ...

# 4. Run quality checks
uv run ruff check --fix
uv run ruff format
uv run mypy verifflowcc

# 5. Run tests again
uv run pytest

# 6. Commit changes (pre-commit hooks run automatically)
git add .
git commit -m "your message"
```

## macOS Specific Commands

```bash
# System sound for completion notifications
afplay /System/Library/Sounds/Glass.aiff

# Common file operations
ls -la          # List files with details
find . -name    # Find files by name
grep -r         # Search in files (prefer rg - ripgrep)
rg              # Fast text search (preferred over grep)
```

## Git Operations

```bash
# Standard git workflow
git status
git add .
git commit -m "message"
git push

# Branching for features
git checkout -b feature-name
git checkout main

# Viewing history
git log --oneline
git diff
```

## Environment Variables

```bash
# Set AgileVV base directory for testing
export AGILEVV_BASE_DIR=".agilevv-test"

# Python path for development
export PYTHONPATH="."
```
