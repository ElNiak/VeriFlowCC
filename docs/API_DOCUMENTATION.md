# PathConfig API Documentation

Complete API reference for the VeriFlowCC PathConfig system and test isolation framework.

## Table of Contents

1. [PathConfig Class](#pathconfig-class)
2. [Test Fixtures](#test-fixtures)
3. [AgileVVDirFactory](#agilevvdirfactory)
4. [Helper Functions](#helper-functions)

## PathConfig Class

The central class for managing VeriFlowCC directory paths and structure.

### Constructor

```python
PathConfig(base_dir: Optional[Union[str, Path]] = None)
```

Creates a new PathConfig instance.

**Parameters:**
- `base_dir` (Optional[Union[str, Path]]): Base directory for the .agilevv structure. If None, uses `AGILEVV_BASE_DIR` environment variable or defaults to `.agilevv`

**Example:**
```python
# Use default
config = PathConfig()

# Use custom directory
config = PathConfig(base_dir="/custom/path/.agilevv")

# Use Path object
config = PathConfig(base_dir=Path.home() / ".agilevv-test")
```

### Properties

#### base_dir
```python
@property
def base_dir(self) -> Path
```
Returns the base directory path.

#### config_path
```python
@property
def config_path(self) -> Path
```
Returns path to config.yaml file.

#### state_path
```python
@property
def state_path(self) -> Path
```
Returns path to state.json file.

#### backlog_path
```python
@property
def backlog_path(self) -> Path
```
Returns path to backlog.md file.

#### architecture_path
```python
@property
def architecture_path(self) -> Path
```
Returns path to architecture.md file.

#### requirements_dir
```python
@property
def requirements_dir(self) -> Path
```
Returns path to requirements directory.

#### c4_diagrams_dir
```python
@property
def c4_diagrams_dir(self) -> Path
```
Returns path to C4 diagrams directory.

#### checkpoints_dir
```python
@property
def checkpoints_dir(self) -> Path
```
Returns path to checkpoints directory.

#### logs_dir
```python
@property
def logs_dir(self) -> Path
```
Returns path to logs directory.

### Methods

#### get_artifact_path
```python
def get_artifact_path(self, relative_path: str) -> Path
```

Get a safe artifact path within the base directory.

**Parameters:**
- `relative_path` (str): Relative path to the artifact

**Returns:**
- Path: Resolved artifact path

**Raises:**
- ValueError: If path is absolute or tries to escape base directory

**Example:**
```python
config = PathConfig()
artifact = config.get_artifact_path("outputs/report.md")
# Returns: base_dir/outputs/report.md

# Security check - these raise ValueError:
config.get_artifact_path("/etc/passwd")  # Absolute path
config.get_artifact_path("../../../etc/passwd")  # Path traversal
```

#### ensure_base_exists
```python
def ensure_base_exists(self) -> None
```

Create the base directory if it doesn't exist.

**Example:**
```python
config = PathConfig(base_dir="/tmp/.agilevv-test")
config.ensure_base_exists()
# Creates /tmp/.agilevv-test if it doesn't exist
```

#### ensure_structure
```python
def ensure_structure(self, create_defaults: bool = False) -> None
```

Create the complete .agilevv directory structure.

**Parameters:**
- `create_defaults` (bool): If True, create default config files

**Example:**
```python
config = PathConfig()
config.ensure_structure(create_defaults=True)
# Creates all directories and default config/state files
```

#### validate_path
```python
def validate_path(self, path: Path, must_exist: bool = True) -> bool
```

Validate that a path is within base directory and optionally exists.

**Parameters:**
- `path` (Path): Path to validate
- `must_exist` (bool): If True, check that path exists

**Returns:**
- bool: True if valid

**Raises:**
- ValueError: If path is outside base directory
- FileNotFoundError: If must_exist=True and path doesn't exist

**Example:**
```python
config = PathConfig()
config.validate_path(config.backlog_path, must_exist=False)  # True
config.validate_path(Path("/etc/passwd"))  # Raises ValueError
```

#### is_test_environment
```python
def is_test_environment(self) -> bool
```

Check if this is a test environment.

**Returns:**
- bool: True if base directory indicates test environment

**Example:**
```python
config = PathConfig(base_dir=".agilevv-test")
config.is_test_environment()  # Returns True

config = PathConfig(base_dir=".agilevv")
config.is_test_environment()  # Returns False
```

#### cleanup
```python
def cleanup(self) -> None
```

Clean up the directory structure (only in test environments).

**Raises:**
- PermissionError: If attempting to cleanup non-test directory

**Example:**
```python
config = PathConfig(base_dir="/tmp/.agilevv-test")
config.cleanup()  # Removes entire directory tree
```

#### create_test_instance
```python
@classmethod
def create_test_instance(cls, test_name: str = "test") -> "PathConfig"
```

Create a PathConfig instance for testing.

**Parameters:**
- `test_name` (str): Name suffix for test directory

**Returns:**
- PathConfig: Configured instance for testing

**Example:**
```python
config = PathConfig.create_test_instance("my_test")
# Creates PathConfig with base_dir like /tmp/.agilevv-test-my_test-{timestamp}
```

#### test_isolation
```python
@contextmanager
def test_isolation(cls, test_name: str = "test")
```

Context manager for test isolation.

**Parameters:**
- `test_name` (str): Name suffix for test directory

**Yields:**
- PathConfig: Configured instance that's cleaned up on exit

**Example:**
```python
with PathConfig.test_isolation("my_test") as config:
    config.backlog_path.write_text("Test data")
    # Use config for testing
# Directory automatically cleaned up after context
```

## Test Fixtures

Pytest fixtures for test isolation, defined in `tests/conftest.py`.

### isolated_agilevv_dir

```python
@pytest.fixture(scope="function")
def isolated_agilevv_dir(
    request: pytest.FixtureRequest,
    tmp_path: Path
) -> Generator[PathConfig, None, None]
```

Function-scoped fixture providing isolated test directory.

**Scope:** Function (each test gets unique directory)

**Yields:** PathConfig instance

**Cleanup:** Automatic unless `--keep-test-dirs` flag is used

**Example:**
```python
def test_example(isolated_agilevv_dir: PathConfig):
    isolated_agilevv_dir.backlog_path.write_text("Test")
    assert isolated_agilevv_dir.is_test_environment()
```

### shared_agilevv_dir

```python
@pytest.fixture(scope="module")
def shared_agilevv_dir(
    request: pytest.FixtureRequest,
    tmp_path_factory: pytest.TempPathFactory
) -> Generator[PathConfig, None, None]
```

Module-scoped fixture providing shared test directory.

**Scope:** Module (all tests in module share directory)

**Yields:** PathConfig instance

**Cleanup:** After all module tests complete

**Example:**
```python
class TestSuite:
    def test_setup(self, shared_agilevv_dir: PathConfig):
        shared_agilevv_dir.config_path.write_text("shared: true")

    def test_use(self, shared_agilevv_dir: PathConfig):
        assert "shared" in shared_agilevv_dir.config_path.read_text()
```

### session_agilevv_dir

```python
@pytest.fixture(scope="session")
def session_agilevv_dir(
    request: pytest.FixtureRequest,
    tmp_path_factory: pytest.TempPathFactory
) -> Generator[PathConfig, None, None]
```

Session-scoped fixture providing persistent test directory.

**Scope:** Session (entire test run shares directory)

**Yields:** PathConfig instance

**Cleanup:** After all tests complete

**Example:**
```python
def test_expensive_setup(session_agilevv_dir: PathConfig):
    # Setup happens once for entire session
    if not session_agilevv_dir.architecture_path.exists():
        perform_expensive_setup(session_agilevv_dir)
```

### agilevv_factory

```python
@pytest.fixture
def agilevv_factory(tmp_path: Path) -> Generator[AgileVVDirFactory, None, None]
```

Factory fixture for creating complex test structures.

**Scope:** Function

**Yields:** AgileVVDirFactory instance

**Cleanup:** Automatic for all created directories

**Example:**
```python
def test_with_factory(agilevv_factory):
    config = agilevv_factory.create_with_backlog(stories=["Story 1"])
    assert config.backlog_path.exists()
```

## AgileVVDirFactory

Factory class for creating test directory structures.

### Constructor

```python
AgileVVDirFactory(base_path: Path)
```

**Parameters:**
- `base_path` (Path): Base path for creating test directories

### Methods

#### create_basic

```python
def create_basic(self, name: str = "test") -> PathConfig
```

Create a basic test directory structure.

**Parameters:**
- `name` (str): Name suffix for test directory

**Returns:**
- PathConfig: Configured instance

**Example:**
```python
factory = AgileVVDirFactory(tmp_path)
config = factory.create_basic("my-test")
```

#### create_with_backlog

```python
def create_with_backlog(
    self,
    name: str = "test",
    stories: Optional[List[str]] = None
) -> PathConfig
```

Create test directory with pre-populated backlog.

**Parameters:**
- `name` (str): Name suffix for test directory
- `stories` (Optional[List[str]]): User stories for backlog

**Returns:**
- PathConfig: Configured instance with backlog

**Example:**
```python
config = factory.create_with_backlog(
    name="backlog-test",
    stories=["As a user, I want...", "As a developer, I need..."]
)
```

#### create_with_sprint

```python
def create_with_sprint(
    self,
    name: str = "test",
    sprint_num: int = 1
) -> PathConfig
```

Create test directory with sprint structure.

**Parameters:**
- `name` (str): Name suffix for test directory
- `sprint_num` (int): Sprint number to create

**Returns:**
- PathConfig: Configured instance with sprint

**Example:**
```python
config = factory.create_with_sprint(name="sprint-test", sprint_num=1)
# Creates sprint-01 directory with requirements.md, tasks.md, etc.
```

#### create_with_memory

```python
def create_with_memory(
    self,
    name: str = "test",
    memories: Optional[Dict[str, str]] = None
) -> PathConfig
```

Create test directory with memory files.

**Parameters:**
- `name` (str): Name suffix for test directory
- `memories` (Optional[Dict[str, str]]): Memory file names and contents

**Returns:**
- PathConfig: Configured instance with memories

**Example:**
```python
config = factory.create_with_memory(
    name="memory-test",
    memories={
        "context.md": "# Project Context",
        "decisions.md": "# Technical Decisions"
    }
)
```

#### create_full_structure

```python
def create_full_structure(self, name: str = "test") -> PathConfig
```

Create complete test directory structure.

**Parameters:**
- `name` (str): Name suffix for test directory

**Returns:**
- PathConfig: Configured instance with full structure

**Example:**
```python
config = factory.create_full_structure("integration-test")
# Creates complete .agilevv structure with all components
```

#### cleanup_all

```python
def cleanup_all(self, keep_dirs: bool = False) -> None
```

Clean up all created test directories.

**Parameters:**
- `keep_dirs` (bool): If True, keep directories for debugging

**Example:**
```python
factory.cleanup_all()  # Remove all test directories
factory.cleanup_all(keep_dirs=True)  # Keep for debugging
```

#### cleanup_selective

```python
def cleanup_selective(self, patterns: List[str]) -> None
```

Clean up only files matching specific patterns.

**Parameters:**
- `patterns` (List[str]): Glob patterns to match for cleanup

**Example:**
```python
factory.cleanup_selective(["*.log", "*.tmp", "**/__pycache__"])
# Removes only log files, temp files, and Python cache
```

## Helper Functions

Utility functions for test data creation.

### build_sample_user_story

```python
def build_sample_user_story(
    story_id: str,
    title: str,
    description: str
) -> Dict[str, str]
```

Build a sample user story for testing.

**Parameters:**
- `story_id` (str): Unique story identifier
- `title` (str): Story title
- `description` (str): Story description

**Returns:**
- Dict[str, str]: Story data with acceptance criteria

**Example:**
```python
story = build_sample_user_story(
    story_id="US-001",
    title="User Authentication",
    description="As a user, I want to log in securely"
)
```

### build_sample_sprint_data

```python
def build_sample_sprint_data(
    sprint_num: int,
    stories: List[str]
) -> Dict[str, Any]
```

Build sample sprint data for testing.

**Parameters:**
- `sprint_num` (int): Sprint number
- `stories` (List[str]): Story IDs for the sprint

**Returns:**
- Dict[str, Any]: Sprint data with dates and velocity

**Example:**
```python
sprint = build_sample_sprint_data(
    sprint_num=1,
    stories=["US-001", "US-002", "US-003"]
)
```

## Usage Examples

### Basic Test Isolation

```python
def test_isolated(isolated_agilevv_dir: PathConfig):
    """Simple isolated test."""
    isolated_agilevv_dir.backlog_path.write_text("Test backlog")
    assert isolated_agilevv_dir.backlog_path.exists()
```

### Integration Test with Shared State

```python
class TestIntegration:
    def test_setup_data(self, shared_agilevv_dir: PathConfig):
        """Set up shared test data."""
        shared_agilevv_dir.ensure_structure(create_defaults=True)

    def test_use_data(self, shared_agilevv_dir: PathConfig):
        """Use the shared data."""
        assert shared_agilevv_dir.config_path.exists()
```

### Complex Test Setup with Factory

```python
def test_complex_scenario(agilevv_factory):
    """Test with complex pre-populated structure."""
    config = agilevv_factory.create_full_structure("complex")

    # All components are ready
    assert config.backlog_path.exists()
    assert config.requirements_dir.exists()
    assert config.architecture_path.exists()

    # Automatic cleanup after test
```

### Security Testing

```python
def test_security_boundaries(isolated_agilevv_dir: PathConfig):
    """Test path security features."""
    # These should raise ValueError
    with pytest.raises(ValueError):
        isolated_agilevv_dir.get_artifact_path("/etc/passwd")

    with pytest.raises(ValueError):
        isolated_agilevv_dir.get_artifact_path("../../etc/passwd")

    # This should work
    safe_path = isolated_agilevv_dir.get_artifact_path("safe/path.txt")
    assert safe_path.is_relative_to(isolated_agilevv_dir.base_dir)
```

## See Also

- [Test Data Management Guide](./TEST_DATA_MANAGEMENT.md)
- [Test Examples](../tests/test_examples.py)
- [Troubleshooting Guide](./TROUBLESHOOTING.md)
