# Test Data Management Guide

This guide explains how to effectively manage test data in VeriFlowCC using the test isolation framework.

## Table of Contents

1. [Overview](#overview)
1. [Test Isolation Architecture](#test-isolation-architecture)
1. [Using Test Fixtures](#using-test-fixtures)
1. [Test Data Patterns](#test-data-patterns)
1. [Best Practices](#best-practices)
1. [Troubleshooting](#troubleshooting)

## Overview

VeriFlowCC's test isolation framework ensures that tests:

- Never interfere with production data
- Don't affect each other when run in parallel
- Can be debugged easily with preserved test artifacts
- Maintain consistent, reproducible environments

## Test Isolation Architecture

### Directory Structure

Tests create isolated directory structures that mirror production:

```
.agilevv-test-{test_name}/
├── backlog.md           # Test backlog data
├── architecture.md      # Test architecture docs
├── config.yaml          # Test configuration
├── state.json           # Test state tracking
├── requirements/        # Test requirements
├── c4_diagrams/        # Test C4 diagrams
├── checkpoints/        # Test checkpoints
└── logs/               # Test logs
```

### Environment Isolation

Each test automatically:

1. Creates a unique base directory
1. Sets `AGILEVV_BASE_DIR` environment variable
1. Configures PathConfig to use the test directory
1. Cleans up after completion (unless debugging)

## Using Test Fixtures

### Function-Scoped Isolation

For complete test isolation, use `isolated_agilevv_dir`:

```python
def test_feature(isolated_agilevv_dir: PathConfig):
    """Each test gets its own directory."""
    # Write test data
    isolated_agilevv_dir.backlog_path.write_text("Test backlog")

    # Directory is automatically cleaned up after test
```

### Module-Scoped Sharing

For tests that need to share state, use `shared_agilevv_dir`:

```python
class TestIntegration:
    def test_setup(self, shared_agilevv_dir: PathConfig):
        """Set up shared test data."""
        shared_agilevv_dir.config_path.write_text("shared: true")

    def test_use_shared(self, shared_agilevv_dir: PathConfig):
        """Use data from test_setup."""
        assert "shared" in shared_agilevv_dir.config_path.read_text()
```

### Session-Scoped Persistence

For expensive setup that should happen once, use `session_agilevv_dir`:

```python
def test_with_expensive_setup(session_agilevv_dir: PathConfig):
    """Uses directory that persists for entire test session."""
    # Setup happens once for all tests in session
    if not session_agilevv_dir.architecture_path.exists():
        # Expensive setup here
        session_agilevv_dir.architecture_path.write_text("...")
```

## Test Data Patterns

### Using the Factory Pattern

The `AgileVVDirFactory` provides convenient methods for common test scenarios:

```python
def test_with_factory(agilevv_factory):
    """Use factory for complex test setups."""

    # Create with pre-populated backlog
    config = agilevv_factory.create_with_backlog(name="test1", stories=["Story 1", "Story 2"])

    # Create with sprint structure
    config = agilevv_factory.create_with_sprint(name="test2", sprint_num=1)

    # Create complete V-Model structure
    config = agilevv_factory.create_full_structure(name="test3")

    # All directories are cleaned up automatically
```

### Test Data Builders

Use helper functions to create consistent test data:

```python
from tests.conftest import build_sample_user_story, build_sample_sprint_data


def test_with_builders():
    story = build_sample_user_story(
        story_id="US-001", title="Test Isolation", description="As a developer..."
    )

    sprint = build_sample_sprint_data(sprint_num=1, stories=["US-001", "US-002"])
```

### Parametrized Tests

Test multiple scenarios with consistent isolation:

```python
@pytest.mark.parametrize(
    "sprint_num,expected_velocity",
    [
        (1, 13),
        (2, 21),
        (3, 34),
    ],
)
def test_sprint_velocity(isolated_agilevv_dir: PathConfig, sprint_num: int, expected_velocity: int):
    """Each parameter combination gets its own directory."""
    # Test logic here
```

## Best Practices

### 1. Choose the Right Scope

- **Function scope**: Default choice for unit tests
- **Module scope**: Integration tests that share expensive setup
- **Session scope**: End-to-end tests with very expensive setup

### 2. Use Descriptive Names

```python
# Good: Descriptive test data
config = agilevv_factory.create_with_backlog(
    name="authentication-test", stories=["Login feature", "Password reset"]
)

# Bad: Generic names
config = agilevv_factory.create_basic(name="test")
```

### 3. Clean Test Data

Always use clean, minimal test data:

```python
def test_minimal_data(isolated_agilevv_dir: PathConfig):
    """Use only the data needed for the test."""
    # Good: Minimal, focused test data
    test_req = "REQ-001: Authentication required"
    isolated_agilevv_dir.requirements_dir.mkdir(parents=True)
    (isolated_agilevv_dir.requirements_dir / "auth.md").write_text(test_req)

    # Bad: Creating unnecessary data
    # Don't create full structure if you only need requirements
```

### 4. Parallel Execution Safety

Tests are automatically safe for parallel execution:

```bash
# Run tests in parallel
# Each test gets its own isolated directory
pytest -n auto tests/
```

### 5. Debugging Failed Tests

Use `--keep-test-dirs` to preserve test directories:

```bash
# Keep directories for debugging
pytest --keep-test-dirs tests/failing_test.py

# Directories will be preserved at:
# /tmp/.agilevv-test-{test_name}/
```

### 6. Security Considerations

PathConfig enforces security boundaries:

```python
def test_security(isolated_agilevv_dir: PathConfig):
    # This will raise ValueError - can't escape base directory
    with pytest.raises(ValueError):
        isolated_agilevv_dir.get_artifact_path("../../../etc/passwd")

    # This will also raise ValueError - no absolute paths
    with pytest.raises(ValueError):
        isolated_agilevv_dir.get_artifact_path("/etc/passwd")
```

## Troubleshooting

### Issue: Tests Pass Individually but Fail Together

**Cause**: Tests may be sharing state unintentionally.

**Solution**: Use `isolated_agilevv_dir` instead of `shared_agilevv_dir`:

```python
# Change from:
def test_one(shared_agilevv_dir: PathConfig): ...
def test_two(shared_agilevv_dir: PathConfig): ...


# To:
def test_one(isolated_agilevv_dir: PathConfig): ...
def test_two(isolated_agilevv_dir: PathConfig): ...
```

### Issue: Test Directories Not Being Cleaned Up

**Cause**: Test may be crashing before cleanup or `--keep-test-dirs` is set.

**Solution**: Check for exceptions and ensure cleanup:

```python
def test_with_cleanup(isolated_agilevv_dir: PathConfig):
    try:
        # Test logic
        pass
    finally:
        # Cleanup happens automatically
        # But you can add custom cleanup here if needed
        pass
```

### Issue: Cannot Find Test Data Files

**Cause**: Incorrect path resolution or directory not created.

**Solution**: Ensure directories exist before writing:

```python
def test_create_structure(isolated_agilevv_dir: PathConfig):
    # Ensure directory exists
    isolated_agilevv_dir.requirements_dir.mkdir(parents=True, exist_ok=True)

    # Now safe to write file
    req_file = isolated_agilevv_dir.requirements_dir / "req.md"
    req_file.write_text("Requirements")
```

### Issue: Environment Variable Conflicts

**Cause**: Multiple tests setting `AGILEVV_BASE_DIR` differently.

**Solution**: Let fixtures handle environment variables:

```python
# Don't do this:
def test_bad():
    os.environ["AGILEVV_BASE_DIR"] = "/custom/path"
    # This affects other tests!
    pass


# Do this instead:
def test_good(isolated_agilevv_dir: PathConfig):
    # Fixture handles environment variable
    # Automatically restored after test
    pass
```

## Advanced Usage

### Custom Cleanup Strategies

Implement selective cleanup for debugging:

```python
def test_with_selective_cleanup(agilevv_factory):
    config = agilevv_factory.create_full_structure()

    # Keep only logs for debugging
    agilevv_factory.cleanup_selective(patterns=["*.md", "*.yaml", "*.json"])
    # Logs directory remains for inspection
```

### Testing Production Behavior

Simulate production paths while maintaining isolation:

```python
def test_production_simulation(tmp_path):
    # Create a production-like path
    prod_like_dir = tmp_path / ".agilevv"  # Note: not .agilevv-test
    config = PathConfig(base_dir=prod_like_dir)

    # Will behave like production but still isolated in tmp_path
    assert not config.is_test_environment()  # Returns False
```

### Cross-Test Communication

When tests need to communicate (rare), use session fixtures:

```python
@pytest.fixture(scope="session")
def shared_test_results():
    """Share results between tests."""
    return {}


def test_producer(shared_test_results, isolated_agilevv_dir):
    # Produce data
    result = perform_expensive_operation()
    shared_test_results["expensive_result"] = result


def test_consumer(shared_test_results, isolated_agilevv_dir):
    # Consume data from producer
    result = shared_test_results.get("expensive_result")
    # Use result in test
```

## See Also

- [PathConfig API Documentation](./API_DOCUMENTATION.md)
- [Test Examples](../tests/test_examples.py)
- [Troubleshooting Guide](./TROUBLESHOOTING.md)
