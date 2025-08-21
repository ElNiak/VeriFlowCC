# Real Testing Guide for VeriFlowCC

## Overview

VeriFlowCC follows a **100% real integration testing approach** with **zero mock dependencies**. This guide provides patterns and best practices for writing tests that use real Claude Code SDK integration without any `unittest.mock` usage.

## Core Principles

### 1. No Mock Dependencies

- **NEVER** use `unittest.mock`, `@patch`, `MagicMock`, or `AsyncMock`
- All tests must use real Claude Code SDK integration
- Environment variables are managed with real context managers

### 2. Real API Authentication

- Tests require `ANTHROPIC_API_KEY` environment variable for full integration
- Tests are automatically skipped if authentication is not available
- Use test-friendly API keys for structure validation when needed

### 3. Test Isolation

- Use `.agilevv-test/` directories instead of production `.agilevv/`
- Each test gets isolated environment to prevent interference
- Automatic cleanup ensures tests don't affect each other

## Essential Patterns

### Environment Variable Management

**❌ Wrong (Mock-based approach):**

```python
from unittest.mock import patch


@patch.dict(os.environ, {"API_KEY": "test-key"})
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
import os
import pytest
from verifflowcc.core.sdk_config import SDKConfig


def _can_authenticate_with_sdk() -> bool:
    """Check if Claude Code SDK authentication is possible."""
    try:
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if api_key:
            sdk_config = SDKConfig(api_key=api_key, timeout=10)
            return sdk_config.api_key is not None
        return False
    except Exception:
        return False


# Skip tests if no authentication
skip_if_no_auth = pytest.mark.skipif(
    not _can_authenticate_with_sdk(), reason="No Claude Code SDK authentication available"
)


@skip_if_no_auth
def test_real_sdk_functionality():
    # Test will only run with real API key
    pass
```

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
@skip_if_no_auth
async def test_real_requirements_analysis():
    """Test requirements analyst with real SDK."""
    # Setup real SDK config
    api_key = os.getenv("ANTHROPIC_API_KEY")
    sdk_config = SDKConfig(api_key=api_key, timeout=60)

    # Create real agent instance
    agent = RequirementsAnalyst(sdk_config=sdk_config)

    # Test with real input
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


@skip_if_no_auth
def test_real_cli_command(isolated_agilevv_dir: TestPathConfig):
    """Test CLI commands with real orchestrator integration."""
    runner = CliRunner()

    # Set real environment
    with temp_env_vars(AGILEVV_BASE_DIR=str(isolated_agilevv_dir.base_dir)):
        result = runner.invoke(app, ["init"])

    # Verify real command execution
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

- Always check for real API key availability
- Skip tests gracefully when authentication is not available
- Use test-specific API keys when possible
- Never hardcode API keys in test files

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
@skip_if_no_auth
async def test_error_handling():
    """Test real error scenarios."""
    try:
        # Trigger real error condition
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

```python
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
# Using mocks
from unittest.mock import patch, MagicMock

# Patching environment
@patch.dict(os.environ, {"KEY": "value"})

# Mocking SDK responses
mock_sdk = MagicMock()
mock_sdk.generate.return_value = "fake response"
```

### ✅ Do This Instead

```python
# Real environment management
with temp_env_vars(KEY="value"):
    # test code

# Real SDK integration
api_key = os.getenv("ANTHROPIC_API_KEY")
if api_key:
    sdk_config = SDKConfig(api_key=api_key)
    # real test with actual SDK
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

- Verify `ANTHROPIC_API_KEY` is set
- Check API key permissions and quotas
- Test authentication separately

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
