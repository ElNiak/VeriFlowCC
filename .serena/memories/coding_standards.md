# VeriFlowCC Coding Standards and Conventions

## Code Style

- **Line length**: 100 characters maximum
- **Python version**: 3.10+ required
- **Quote style**: Double quotes preferred
- **Indentation**: 4 spaces (no tabs)
- **Type hints**: Required for all functions and classes
- **Docstrings**: Follow Google style for classes and public methods

## Naming Conventions

- **Functions/methods**: snake_case
- **Classes**: PascalCase
- **Constants**: UPPER_SNAKE_CASE
- **Private methods**: Leading underscore (\_method_name)
- **Modules**: lowercase with underscores

## Code Organization

- **File structure**: Follow the established directory layout
- **Imports**: Organized with isort, grouped by standard/third-party/local
- **Error handling**: Never use bare `except:`, specify exception types
- **Async/await**: Use for AI agent calls and I/O operations

## Security Standards

- **No secrets in code**: Use environment variables or secure storage
- **Input validation**: Use Pydantic for all data validation
- **Safe subprocess calls**: Use appropriate security measures
- **Path traversal prevention**: Enforce directory boundaries in PathConfig

## Testing Standards

- **Test organization**: Use pytest markers for categorization
- **Coverage**: Minimum 80% code coverage required
- **Test naming**: test_feature_scenario format
- **AAA pattern**: Arrange, Act, Assert structure
- **Isolation**: Use PathConfig fixtures for test isolation

## Ruff Configuration

Selected linters:

- E/W: pycodestyle errors and warnings
- F: pyflakes
- I: isort import sorting
- B: flake8-bugbear
- C4: flake8-comprehensions
- UP: pyupgrade
- S: bandit security
- N: pep8-naming
- TID: flake8-tidy-imports
- PTH: flake8-use-pathlib
- TCH: flake8-type-checking
- RUF: Ruff-specific rules

## MyPy Configuration

- **Strict typing**: disallow_untyped_defs = true
- **No implicit optional**: Explicit Optional[] required
- **Warn unused**: Flag unused configs and imports
- **Check untyped**: Analyze even untyped function definitions

## Git Conventions

- **Commit messages**: Use conventional commits format when applicable
- **Branch naming**: Feature branches use descriptive names
- **Checkpointing**: Automatic commits at V-Model gates
- **Pre-commit hooks**: All code must pass quality checks before commit

## Agent Communication

- **Structured data**: Use Pydantic models for agent communication
- **Context management**: Minimize token usage through targeted context
- **Memory management**: Use CLAUDE.md for persistent project knowledge
- **Error propagation**: Clear error messages with context
