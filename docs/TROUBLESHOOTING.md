# Test Isolation Troubleshooting Guide

This guide helps diagnose and fix common issues with the VeriFlowCC test isolation framework.

## Table of Contents

1. [Common Issues](#common-issues)
1. [Debugging Techniques](#debugging-techniques)
1. [Error Messages](#error-messages)
1. [Performance Issues](#performance-issues)
1. [CI/CD Issues](#cicd-issues)

## Common Issues

### Tests Pass Individually but Fail When Run Together

**Symptoms:**

- `pytest tests/test_module.py::test_one` passes
- `pytest tests/test_module.py` fails
- Random test failures in CI but not locally

**Cause:** Tests are sharing state unintentionally.

**Solutions:**

1. **Use isolated fixtures instead of shared ones:**

```python
# Problem: Shared state
def test_one(shared_agilevv_dir): ...
def test_two(shared_agilevv_dir): ...  # May see test_one's data


# Solution: Isolated directories
def test_one(isolated_agilevv_dir): ...
def test_two(isolated_agilevv_dir): ...  # Fresh directory
```

2. **Check for module-level variables:**

```python
# Problem: Module-level state
_cache = {}


def test_one():
    _cache["key"] = "value"  # Affects other tests


# Solution: Use fixtures for state
def test_one(isolated_agilevv_dir):
    cache_file = isolated_agilevv_dir.base_dir / "cache.json"
    cache_file.write_text('{"key": "value"}')
```

3. **Verify cleanup in fixtures:**

```python
# Ensure proper cleanup
@pytest.fixture
def my_fixture(isolated_agilevv_dir):
    # Setup
    resource = create_resource()
    yield resource
    # Cleanup - happens even if test fails
    resource.cleanup()
```

### Test Directories Not Being Cleaned Up

**Symptoms:**

- `/tmp` filling up with `.agilevv-test-*` directories
- Old test data persisting between runs
- Disk space issues

**Cause:** Tests crashing before cleanup or `--keep-test-dirs` flag.

**Solutions:**

1. **Check for the keep flag:**

```bash
# Check your pytest command
pytest --keep-test-dirs  # This prevents cleanup!

# Remove the flag for normal operation
pytest  # Cleanup happens automatically
```

2. **Manual cleanup of old directories:**

```bash
# Find old test directories
find /tmp -name ".agilevv-test-*" -type d -mtime +1

# Remove old test directories (older than 1 day)
find /tmp -name ".agilevv-test-*" -type d -mtime +1 -exec rm -rf {} +
```

3. **Add cleanup to test teardown:**

```python
def test_with_explicit_cleanup(isolated_agilevv_dir):
    try:
        # Test logic
        pass
    finally:
        # Explicit cleanup if needed
        if isolated_agilevv_dir.base_dir.exists():
            isolated_agilevv_dir.cleanup()
```

### FileNotFoundError: Cannot Find Test Files

**Symptoms:**

- `FileNotFoundError: [Errno 2] No such file or directory`
- Tests fail with "path does not exist"
- Inconsistent file access errors

**Cause:** Directory structure not created or incorrect path resolution.

**Solutions:**

1. **Ensure directories exist before use:**

```python
def test_create_structure(isolated_agilevv_dir):
    # Problem: Directory might not exist
    # (isolated_agilevv_dir.requirements_dir / "req.md").write_text("...")

    # Solution: Create directory first
    isolated_agilevv_dir.requirements_dir.mkdir(parents=True, exist_ok=True)
    (isolated_agilevv_dir.requirements_dir / "req.md").write_text("...")
```

2. **Use ensure_structure for complete setup:**

```python
def test_with_structure(isolated_agilevv_dir):
    # Create all standard directories
    isolated_agilevv_dir.ensure_structure(create_defaults=True)

    # Now all paths exist
    assert isolated_agilevv_dir.requirements_dir.exists()
    assert isolated_agilevv_dir.checkpoints_dir.exists()
```

3. **Check path resolution:**

```python
def test_path_resolution(isolated_agilevv_dir):
    # Debug path issues
    print(f"Base dir: {isolated_agilevv_dir.base_dir}")
    print(f"Exists: {isolated_agilevv_dir.base_dir.exists()}")
    print(f"Absolute: {isolated_agilevv_dir.base_dir.absolute()}")
```

### PermissionError: Cannot Write to Directory

**Symptoms:**

- `PermissionError: [Errno 13] Permission denied`
- Cannot create files in test directory
- Cleanup fails with permission errors

**Cause:** Incorrect permissions or trying to modify production directories.

**Solutions:**

1. **Verify test environment:**

```python
def test_check_environment(isolated_agilevv_dir):
    # Ensure we're in test environment
    assert isolated_agilevv_dir.is_test_environment()

    # Check directory is writable
    test_file = isolated_agilevv_dir.base_dir / "test.txt"
    test_file.write_text("test")  # Should work in test env
```

2. **Fix directory permissions:**

```bash
# Check permissions
ls -la /tmp/.agilevv-test-*

# Fix permissions if needed
chmod -R u+rwx /tmp/.agilevv-test-*
```

3. **Use temp directories correctly:**

```python
def test_temp_dir_usage(tmp_path):
    # tmp_path is guaranteed writable
    test_dir = tmp_path / ".agilevv-test"
    config = PathConfig(base_dir=test_dir)
    config.ensure_base_exists()
```

### ValueError: Path Outside Base Directory

**Symptoms:**

- `ValueError: Path /etc/passwd is outside base directory`
- `ValueError: Path contains parent directory references`
- Security validation errors

**Cause:** Attempting to access files outside the test directory.

**Solutions:**

1. **Use relative paths only:**

```python
def test_relative_paths(isolated_agilevv_dir):
    # Problem: Absolute path
    # path = isolated_agilevv_dir.get_artifact_path("/tmp/file.txt")

    # Solution: Relative path
    path = isolated_agilevv_dir.get_artifact_path("outputs/file.txt")
```

2. **Avoid path traversal:**

```python
def test_no_traversal(isolated_agilevv_dir):
    # Problem: Path traversal
    # path = isolated_agilevv_dir.get_artifact_path("../../etc/passwd")

    # Solution: Stay within base directory
    path = isolated_agilevv_dir.get_artifact_path("data/passwd")
```

## Debugging Techniques

### Enable Verbose Output

```bash
# Show test output
pytest -v -s tests/test_module.py

# -v: verbose test names
# -s: show print statements
```

### Inspect Test Directories

```python
def test_debug_directory(isolated_agilevv_dir):
    """Debug test to inspect directory structure."""
    print(f"\nTest Directory: {isolated_agilevv_dir.base_dir}")
    print("Contents:")
    for path in isolated_agilevv_dir.base_dir.rglob("*"):
        print(f"  {path.relative_to(isolated_agilevv_dir.base_dir)}")
```

### Keep Directories for Inspection

```bash
# Keep test directories after failure
pytest --keep-test-dirs tests/failing_test.py

# Inspect the preserved directory
ls -la /tmp/.agilevv-test-*/
```

### Use Interactive Debugging

```python
def test_with_debugger(isolated_agilevv_dir):
    """Drop into debugger for inspection."""
    import pdb

    pdb.set_trace()

    # Inspect in debugger:
    # p isolated_agilevv_dir.base_dir
    # p list(isolated_agilevv_dir.base_dir.iterdir())
```

### Check Environment Variables

```python
def test_check_environment():
    """Debug environment variables."""
    import os

    print(f"AGILEVV_BASE_DIR: {os.environ.get('AGILEVV_BASE_DIR', 'Not set')}")
    print(f"TMPDIR: {os.environ.get('TMPDIR', 'Not set')}")
    print(f"PWD: {os.getcwd()}")
```

## Error Messages

### "PathConfig object has no attribute 'X'"

**Meaning:** Trying to access a property that doesn't exist.

**Common mistakes:**

```python
# Wrong property names
config.backlog_dir  # Wrong - no such property
config.backlog_path  # Correct

config.config_dir  # Wrong
config.config_path  # Correct

config.requirements_path  # Wrong
config.requirements_dir  # Correct
```

### "Cannot cleanup non-test directory"

**Meaning:** Trying to cleanup a production directory.

**Fix:**

```python
# Only test directories can be cleaned up
config = PathConfig(base_dir=".agilevv-test")  # OK
config.cleanup()

config = PathConfig(base_dir=".agilevv")  # Production
# config.cleanup()  # Would raise PermissionError
```

### "Path must be relative"

**Meaning:** Absolute paths are not allowed for security.

**Fix:**

```python
# Use relative paths
config.get_artifact_path("relative/path.txt")  # OK
# config.get_artifact_path("/absolute/path.txt")  # Error
```

## Performance Issues

### Slow Test Startup

**Symptoms:**

- Tests take long to start
- Directory creation is slow
- Fixture setup timeout

**Solutions:**

1. **Use appropriate fixture scope:**

```python
# Expensive setup? Use session scope
@pytest.fixture(scope="session")
def expensive_setup(session_agilevv_dir):
    # This runs once for all tests
    perform_expensive_setup()
    return data
```

2. **Parallelize test execution:**

```bash
# Run tests in parallel
pytest -n auto  # Uses all CPU cores
pytest -n 4     # Uses 4 workers
```

3. **Cache expensive operations:**

```python
@pytest.fixture(scope="session")
def cached_data(session_agilevv_dir):
    cache_file = session_agilevv_dir.base_dir / "cache.pkl"
    if cache_file.exists():
        return pickle.load(cache_file.open("rb"))

    data = expensive_computation()
    pickle.dump(data, cache_file.open("wb"))
    return data
```

### High Memory Usage

**Symptoms:**

- Tests consume excessive memory
- OOM errors in CI
- Memory not released between tests

**Solutions:**

1. **Explicitly clean up large objects:**

```python
def test_large_data(isolated_agilevv_dir):
    large_data = create_large_dataset()
    try:
        # Use data
        pass
    finally:
        del large_data  # Explicit cleanup
        import gc

        gc.collect()  # Force garbage collection
```

2. **Use generators for large datasets:**

```python
def test_with_generator(isolated_agilevv_dir):
    # Don't load all data at once
    for chunk in read_large_file_in_chunks():
        process_chunk(chunk)
```

## CI/CD Issues

### Tests Pass Locally but Fail in CI

**Common causes:**

1. Different Python versions
1. Missing dependencies
1. Different filesystem (case sensitivity)
1. Environment variables

**Debug steps:**

1. **Match CI environment locally:**

```bash
# Use same Python version
python --version  # Check local
# Match with CI version

# Use clean environment
python -m venv test_env
source test_env/bin/activate
pip install -e .
pytest
```

2. **Check CI logs for environment:**

```yaml
# In GitHub Actions, add debugging
- name: Debug environment
  run: |
    python --version
    pip list
    env | sort
    pwd
    ls -la
```

3. **Handle platform differences:**

```python
import platform


def test_platform_specific(isolated_agilevv_dir):
    if platform.system() == "Windows":
        # Windows-specific handling
        pass
    else:
        # Unix-like systems
        pass
```

### Cleanup Fails in CI

**Symptoms:**

- "Permission denied" errors
- "Directory not empty" errors
- Hanging cleanup processes

**Solutions:**

1. **Add retry logic:**

```python
import time
import shutil


def robust_cleanup(path, retries=3):
    for i in range(retries):
        try:
            shutil.rmtree(path)
            return
        except Exception as e:
            if i == retries - 1:
                raise
            time.sleep(1)
```

2. **Handle Windows file locking:**

```python
def test_windows_compatible(isolated_agilevv_dir):
    file_path = isolated_agilevv_dir.base_dir / "test.txt"

    # Ensure file is closed
    with file_path.open("w") as f:
        f.write("test")
    # File automatically closed here

    # Now safe to cleanup
```

## Getting Help

If you encounter issues not covered here:

1. **Check test output carefully:**

```bash
pytest -vvs --tb=long tests/problematic_test.py
```

2. **Search existing issues:**

- GitHub Issues: [VeriFlowCC Issues](https://github.com/yourusername/VeriFlowCC/issues)

3. **Create minimal reproduction:**

```python
# minimal_test.py
def test_minimal_reproduction(isolated_agilevv_dir):
    # Minimal code that reproduces the issue
    pass
```

4. **Provide environment details:**

```bash
python --version
pip list | grep -E "pytest|verifflowcc"
uname -a  # or platform info
```

## See Also

- [Test Data Management Guide](./TEST_DATA_MANAGEMENT.md)
- [API Documentation](./API_DOCUMENTATION.md)
- [Test Examples](../tests/test_examples.py)
