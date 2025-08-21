# Real Testing Guide for VeriFlowCC

## Overview

VeriFlowCC follows a **100% real integration testing approach** with **zero mock dependencies**. This guide provides patterns and best practices for writing tests that use real Claude Code SDK integration without any `unittest.mock` usage.

## Core Principles

### 1. No Mock Dependencies

- **NEVER** use `unittest.mock`, `@patch`, `MagicMock`, or `AsyncMock`
- All tests must use real Claude Code SDK integration
- Environment variables are managed with real context managers

### 2. Real API Authentication

- Tests use configured Claude Code authentication (subscription or API key)
- Authentication is assumed to be pre-configured and available
- Tests fail fast if authentication is not available (no graceful skipping)
- Authentication flexibility allows various setup approaches

### 3. Test Isolation

- Use `.agilevv-test/` directories instead of production `.agilevv/`
- Each test gets isolated environment to prevent interference
- Automatic cleanup ensures tests don't affect each other

## Essential Patterns

### Environment Variable Management

**❌ Wrong (Mock-based approach):**

```python
from unittest.mock import patch


@patch.dict(os.environ, {"AUTH_TOKEN": "test-token"})
def test_something():
    # Test code here
    pass
```

**✅ Correct (Real approach):**

```python
from contextlib import contextmanager
import os


@contextmanager
def temp_env_vars(**env_vars: str):
    """Context manager to temporarily set environment variables."""
    original_values = {}

    for key, value in env_vars.items():
        original_values[key] = os.environ.get(key)
        os.environ[key] = value

    try:
        yield
    finally:
        for key, original_value in original_values.items():
            if original_value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = original_value


def test_with_env_vars():
    with temp_env_vars(AGILEVV_BASE_DIR=str(test_dir)):
        # Test code here
        pass
```

### Authentication Handling

**Pattern for real SDK authentication:**

```python
import pytest
from verifflowcc.core.sdk_config import SDKConfig


def test_real_sdk_functionality():
    """Test with real SDK - authentication is assumed to be pre-configured."""
    # Authentication is assumed to be available
    # Tests fail fast if authentication is not configured
    sdk_config = SDKConfig(timeout=10)

    # Test will proceed assuming authentication is configured
    # If authentication fails, test fails immediately (no skipping)
    pass
```

**Note**: Tests now assume authentication is pre-configured and fail fast if unavailable, rather than being skipped gracefully.

### Test Isolation with Real Directories

**Use the isolation fixtures:**

```python
from tests.conftest import PathConfig as TestPathConfig


def test_isolated_operation(isolated_agilevv_dir: TestPathConfig):
    """Each test gets its own .agilevv-test directory."""
    assert isolated_agilevv_dir.base_dir.exists()

    # Test operations in isolated directory
    config_file = isolated_agilevv_dir.config_path
    assert config_file.parent == isolated_agilevv_dir.base_dir
```

### Agent Testing Patterns

**Real SDK agent testing:**

```python
import pytest
from verifflowcc.agents.requirements_analyst import RequirementsAnalyst
from verifflowcc.core.sdk_config import SDKConfig


@pytest.mark.real_sdk
async def test_real_requirements_analysis():
    """Test requirements analyst with real SDK - authentication assumed."""
    # Setup real SDK config - authentication is assumed to be configured
    sdk_config = SDKConfig(timeout=60)

    # Create real agent instance
    agent = RequirementsAnalyst(sdk_config=sdk_config)

    # Test with real input - fails fast if authentication unavailable
    story = "As a user, I want to login to the system"
    result = await agent.analyze_requirements(story)

    # Validate real response structure
    assert result.status in ["success", "partial", "error"]
    assert isinstance(result.artifacts, dict)
    assert result.artifacts  # Should not be empty
```

### CLI Testing Patterns

**Real CLI integration testing:**

```python
from typer.testing import CliRunner
from verifflowcc.cli import app


def test_real_cli_command(isolated_agilevv_dir: TestPathConfig):
    """Test CLI commands with real orchestrator integration - authentication assumed."""
    runner = CliRunner()

    # Set real environment - authentication assumed to be pre-configured
    with temp_env_vars(AGILEVV_BASE_DIR=str(isolated_agilevv_dir.base_dir)):
        result = runner.invoke(app, ["init"])

    # Verify real command execution - fails fast if authentication unavailable
    assert result.exit_code == 0
    assert isolated_agilevv_dir.config_path.exists()
```

## Test Organization

### Test Markers

Use these pytest markers to organize tests:

```python
pytestmark = [
    pytest.mark.integration,  # Integration test
    pytest.mark.real_sdk,  # Uses real Claude SDK
    pytest.mark.e2e,  # End-to-end test
    pytest.mark.sequential,  # Must run sequentially
    pytest.mark.slow,  # Takes significant time
]
```

### Directory Structure

```
tests/
├── agents/              # Agent-specific tests
│   ├── test_real_*_sdk.py  # Real SDK integration tests
│   └── test_*.py           # Unit tests
├── core/                # Core functionality tests
│   ├── test_real_*.py      # Real integration tests
│   └── test_*.py           # Unit tests
├── integration/         # Integration tests
│   ├── test_e2e_*.py       # End-to-end tests
│   └── test_*_integration.py
├── schemas/             # Schema validation tests
├── validation/          # Mock removal validation
└── conftest.py          # Shared test fixtures
```

## Running Tests

### Basic Commands

```bash
# Run all tests (excluding slow ones)
uv run pytest -m "not slow"

# Run real SDK integration tests only
uv run pytest -m real_sdk

# Run with coverage
uv run pytest --cov=verifflowcc --cov-report=term-missing

# Keep test directories for debugging
uv run pytest --keep-test-dirs tests/failing_test.py
```

### Sequential Execution

```bash
# Run tests sequentially (important for agent handoff tests)
uv run pytest -x tests/integration/test_e2e_vmodel_workflow_handoffs.py
```

## Best Practices

### 1. Authentication Strategy

- Authentication is assumed to be pre-configured and available
- Tests fail fast when authentication is not available (no graceful skipping)
- Use flexible authentication approaches (subscription or API key)
- Never hardcode authentication credentials in test files

### 2. Resource Management

- Use context managers for temporary resources
- Clean up test directories automatically
- Implement proper timeout handling for real API calls
- Handle network failures gracefully

### 3. Test Data

- Use realistic test data that works with real APIs
- Create reusable test fixtures for common scenarios
- Validate both successful and error response patterns
- Test edge cases with real API responses

### 4. Error Handling

```python
async def test_error_handling():
    """Test real error scenarios - authentication assumed."""
    try:
        # Trigger real error condition (authentication assumed available)
        result = await agent.process_invalid_input()
    except SomeExpectedError as e:
        assert "expected error pattern" in str(e)
    else:
        assert False, "Expected exception not raised"
```

### 5. Performance Considerations

- Use appropriate timeouts for real API calls
- Implement retry logic for network issues
- Mock only external services, never internal components
- Use `@pytest.mark.slow` for time-intensive tests

## Validation Testing

### Mock Removal Validation

The project includes comprehensive validation to ensure no mock dependencies remain:

```bash
# Run mock removal validation
uv run pytest tests/validation/test_mock_removal_validation.py
```

This validates:

- No `unittest.mock` imports
- No `@patch` decorators
- No `MagicMock`/`AsyncMock` instances
- No mock SDK classes
- No mock mode parameters

### Artifact Validation

All agent outputs are validated using Pydantic schemas:

```python
from verifflowcc.schemas.agent_schemas import DesignOutput


def test_artifact_validation():
    """Validate agent artifacts match expected schema."""
    # Real agent output
    result = await agent.generate_design()

    # Validate against schema
    validated = DesignOutput(**result.model_dump())
    assert validated.design_specifications
    assert validated.architecture_updates
```

## Common Pitfalls

### ❌ Don't Do This

```python
# Using mocks - DON'T DO THIS
from unittest.mock import patch, MagicMock


# Patching environment
@patch.dict(os.environ, {"KEY": "value"})
def test_with_mock_env():
    # test with mocked environment
    pass


# Mocking SDK responses
mock_sdk = MagicMock()
mock_sdk.generate.return_value = "fake response"
```

### ✅ Do This Instead

```python
# Real environment management
with temp_env_vars(KEY="value"):
    # test code here - proper indentation
    result = some_test_function()
    assert result is not None

# Real SDK integration with flexible authentication
sdk_config = SDKConfig()  # Uses configured authentication automatically
if sdk_config.is_authenticated():
    # real test with actual SDK
    response = sdk_config.get_client().generate("test prompt")
    assert response is not None
```

## Debugging Tips

### 1. Preserve Test Directories

```bash
uv run pytest --keep-test-dirs tests/failing_test.py
```

### 2. Verbose Logging

```bash
uv run pytest --log-cli-level=DEBUG -s tests/specific_test.py
```

### 3. Test Isolation Issues

- Check if tests are using shared resources
- Verify environment variable cleanup
- Ensure proper fixture scoping

### 4. Authentication Problems

- Verify Claude Code authentication is configured properly before running tests
- Check authentication method (subscription or API key setup)
- Tests assume authentication is available and will fail fast if not configured
- Test authentication separately with SDK configuration if tests are failing

## Migration from Mock-Based Tests

When converting existing mock-based tests:

1. **Remove all mock imports and decorators**
1. **Replace `@patch.dict` with `temp_env_vars()`**
1. **Add real authentication handling**
1. **Use test isolation fixtures**
1. **Add appropriate test markers**
1. **Validate real response structures**

## Summary

The VeriFlowCC real testing approach ensures:

- **Reliability**: Tests use actual production code paths
- **Confidence**: Real API integration catches integration issues
- **Maintenance**: No mock maintenance overhead
- **Quality**: Higher test quality through real scenarios

By following these patterns, you'll create robust tests that provide genuine confidence in the system's functionality while maintaining the integrity of the no-mock approach.
