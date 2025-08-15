# Technical Specification

This is the technical specification for the spec detailed in @.agilevv/specs/2025-08-12-test-isolation-agilevv/spec.md

## Technical Requirements

### Core Architecture Changes

- **Base Directory Abstraction**: Create a `PathConfig` class that manages all .agilevv/ path resolution
- **Dependency Injection**: Pass `PathConfig` instance through constructors instead of hard-coding paths
- **Environment Variable Support**: Implement `AGILEVV_BASE_DIR` environment variable with fallback to `.agilevv/`
- **Path Resolution Strategy**: Use `Path.resolve()` for absolute paths and maintain relative path compatibility

### Test Framework Architecture

- **Pytest Fixtures Hierarchy**:

  - `isolated_agilevv_dir`: Creates unique temporary directory per test
  - `shared_agilevv_dir`: Creates shared directory per test module
  - `session_agilevv_dir`: Creates single directory per test session
  - `agilevv_path_config`: Provides configured PathConfig instance

- **Fixture Scopes**:

  - Function scope: Complete isolation, automatic cleanup
  - Module scope: Shared within test file, cleanup after module
  - Session scope: Shared across all tests, cleanup at session end
  - Class scope: Shared within test class, cleanup after class

### Data Management Strategy

- **Test Data Categories**:

  - Static fixtures: Pre-defined JSON/YAML files in `tests/fixtures/agilevv/`
  - Dynamic fixtures: Generated at runtime based on test requirements
  - Snapshot fixtures: Captured from real .agilevv/ states for regression testing

- **Cleanup Strategies**:

  - Automatic: Default for function-scoped fixtures
  - Deferred: For shared fixtures, cleanup after last consumer
  - Manual: For debugging, controlled by `--keep-test-dirs` pytest flag
  - Selective: Keep only failed test directories for debugging

### Implementation Patterns

- **Factory Pattern**: `AgileVVDirFactory` for creating test directory structures
- **Builder Pattern**: `TestDataBuilder` for constructing complex test configurations
- **Context Manager**: `with_agilevv_dir()` for explicit resource management
- **Decorator Pattern**: `@with_test_isolation` for method-level isolation

### File Refactoring Requirements

**Files requiring PathConfig integration:**

1. `verifflowcc/cli.py` - 31 hard-coded references
1. `verifflowcc/core/orchestrator.py` - Core path management
1. `verifflowcc/core/git_integration.py` - Git operations
1. `verifflowcc/agents/base.py` - Agent artifact management
1. `verifflowcc/agents/requirements_analyst.py` - Requirements storage
1. All test files in `tests/` directory

### Performance Considerations

- **Lazy Directory Creation**: Only create .agilevv/ structure when first accessed
- **Copy-on-Write**: Share read-only test data, copy only when modified
- **Parallel Test Support**: Use process-safe locking for shared resources
- **Memory Management**: Stream large artifacts instead of loading entirely

### Error Handling

- **Path Resolution Errors**: Clear messages indicating missing configuration
- **Permission Errors**: Fallback to user temp directory if project directory not writable
- **Cleanup Failures**: Log warnings but don't fail tests
- **Race Conditions**: Retry logic with exponential backoff for file operations

### Migration Path

- **Backward Compatibility**: Detect existing .agilevv/ and use as default
- **Progressive Migration**: Support both old and new path systems during transition
- **Configuration Detection**: Auto-detect test environment and apply isolation
- **Developer Override**: Allow explicit path configuration via settings

## External Dependencies

**pytest-datadir** - Provides reusable test data directory management

- **Justification:** Handles complex test data scenarios with built-in cleanup and isolation

**pytest-env** - Environment variable management for tests

- **Justification:** Simplifies AGILEVV_BASE_DIR testing across different configurations

**filelock** - Cross-platform file locking for parallel test execution

- **Justification:** Prevents race conditions when multiple tests access shared resources
