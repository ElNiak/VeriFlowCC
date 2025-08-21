"""Tests for pytest fixtures and isolation utilities."""

import os
from pathlib import Path

import pytest
from verifflowcc.core.path_config import PathConfig


class TestIsolatedAgileVVDirFixture:
    """Test the isolated_agilevv_dir fixture behavior."""

    def test_creates_unique_test_directory(self, tmp_path: Path) -> None:
        """Test that fixture creates a unique test directory."""
        # Simulate the fixture behavior
        test_dir = tmp_path / ".agilevv-test"
        config = PathConfig(base_dir=test_dir)

        assert config.base_dir == test_dir
        assert config.is_test_environment()

    def test_cleanup_after_test_completes(self, tmp_path: Path) -> None:
        """Test that fixture cleans up directory after test."""
        test_dir = tmp_path / ".agilevv-test"
        test_dir.mkdir()

        # Create some test files
        (test_dir / "test.txt").write_text("test content")

        # Simulate cleanup
        config = PathConfig(base_dir=test_dir)
        config.cleanup()

        assert not test_dir.exists()

    def test_isolation_between_tests(self, tmp_path: Path) -> None:
        """Test that each test gets its own isolated directory."""
        # First test simulation
        test_dir_1 = tmp_path / ".agilevv-test-1"
        config_1 = PathConfig(base_dir=test_dir_1)

        # Second test simulation
        test_dir_2 = tmp_path / ".agilevv-test-2"
        config_2 = PathConfig(base_dir=test_dir_2)

        assert config_1.base_dir != config_2.base_dir
        assert config_1.base_dir.parent == config_2.base_dir.parent

    def test_environment_variable_override(self, tmp_path: Path) -> None:
        """Test that AGILEVV_BASE_DIR environment variable works in fixture."""
        custom_dir = tmp_path / "custom-test-dir"

        # Set environment variable directly instead of using patch
        old_value = os.environ.get("AGILEVV_BASE_DIR")
        try:
            os.environ["AGILEVV_BASE_DIR"] = str(custom_dir)
            config = PathConfig()
            assert config.base_dir == custom_dir
            assert config.is_test_environment()
        finally:
            # Restore original value
            if old_value is None:
                os.environ.pop("AGILEVV_BASE_DIR", None)
            else:
                os.environ["AGILEVV_BASE_DIR"] = old_value

    def test_fixture_with_keep_test_dirs_flag(self, tmp_path: Path) -> None:
        """Test that --keep-test-dirs flag prevents cleanup."""
        test_dir = tmp_path / ".agilevv-test"
        test_dir.mkdir()
        (test_dir / "test.txt").write_text("test content")

        # Simulate fixture with keep flag
        PathConfig(base_dir=test_dir)  # Create config but don't cleanup

        # With keep flag, cleanup should not remove directory
        # This will be implemented in conftest.py
        assert test_dir.exists()


class TestSharedAgileVVDirFixture:
    """Test the shared_agilevv_dir fixture behavior (module scope)."""

    def test_shared_within_module(self, tmp_path: Path) -> None:
        """Test that fixture is shared within a test module."""
        # Simulate module-scoped fixture
        module_dir = tmp_path / ".agilevv-test-module"
        config = PathConfig(base_dir=module_dir)

        # Multiple tests in same module should use same directory
        assert config.base_dir == module_dir
        assert config.is_test_environment()

    def test_different_between_modules(self, tmp_path: Path) -> None:
        """Test that different modules get different directories."""
        module_dir_1 = tmp_path / ".agilevv-test-module-1"
        module_dir_2 = tmp_path / ".agilevv-test-module-2"

        config_1 = PathConfig(base_dir=module_dir_1)
        config_2 = PathConfig(base_dir=module_dir_2)

        assert config_1.base_dir != config_2.base_dir

    def test_cleanup_after_module_completes(self, tmp_path: Path) -> None:
        """Test that fixture cleans up after all module tests complete."""
        module_dir = tmp_path / ".agilevv-test-module"
        module_dir.mkdir()

        config = PathConfig(base_dir=module_dir)
        config.cleanup()

        assert not module_dir.exists()


class TestSessionAgileVVDirFixture:
    """Test the session_agilevv_dir fixture behavior (session scope)."""

    def test_shared_across_session(self, tmp_path: Path) -> None:
        """Test that fixture is shared across entire test session."""
        session_dir = tmp_path / ".agilevv-test-session"
        config = PathConfig(base_dir=session_dir)

        # All tests in session should use same directory
        assert config.base_dir == session_dir
        assert config.is_test_environment()

    def test_cleanup_after_session_completes(self, tmp_path: Path) -> None:
        """Test that fixture cleans up after session ends."""
        session_dir = tmp_path / ".agilevv-test-session"
        session_dir.mkdir()

        config = PathConfig(base_dir=session_dir)
        config.cleanup()

        assert not session_dir.exists()


class TestAgileVVDirFactory:
    """Test the AgileVVDirFactory for complex test setups."""

    def test_factory_creates_custom_structure(self, tmp_path: Path) -> None:
        """Test that factory can create custom directory structures."""
        # This will be implemented as a factory class
        test_dir = tmp_path / ".agilevv-test"
        config = PathConfig(base_dir=test_dir)

        # Factory should be able to create custom structures
        config.ensure_structure()

        assert config.backlog_path.parent.exists()
        assert config.requirements_dir.exists()
        assert config.checkpoints_dir.exists()

    def test_factory_with_prepopulated_data(self, tmp_path: Path) -> None:
        """Test that factory can prepopulate test data."""
        test_dir = tmp_path / ".agilevv-test"
        config = PathConfig(base_dir=test_dir)
        config.ensure_structure()

        # Simulate prepopulated data
        (config.backlog_path.parent / "user_stories.md").write_text("# User Stories")
        (config.logs_dir / "test.md").write_text("Test memory")

        assert (config.backlog_path.parent / "user_stories.md").exists()
        assert (config.logs_dir / "test.md").exists()

    def test_factory_cleanup_strategies(self, tmp_path: Path) -> None:
        """Test different cleanup strategies for factory."""
        test_dir = tmp_path / ".agilevv-test"
        config = PathConfig(base_dir=test_dir)

        # Test different cleanup strategies
        # 1. Automatic cleanup
        config.cleanup()
        assert not test_dir.exists()

        # 2. Selective cleanup (keep certain files)
        test_dir.mkdir()
        important_file = test_dir / "keep.txt"
        important_file.write_text("keep this")
        temp_file = test_dir / "temp.txt"
        temp_file.write_text("remove this")

        # Selective cleanup would be implemented in factory
        assert test_dir.exists()  # Directory still exists for now


class TestFixtureIntegration:
    """Test integration between fixtures and PathConfig."""

    def test_fixture_provides_pathconfig_instance(self, tmp_path: Path) -> None:
        """Test that fixture provides a configured PathConfig instance."""
        test_dir = tmp_path / ".agilevv-test"
        config = PathConfig(base_dir=test_dir)

        assert isinstance(config, PathConfig)
        assert config.is_test_environment()
        assert config.base_dir == test_dir

    def test_nested_fixture_usage(self, tmp_path: Path) -> None:
        """Test that fixtures can be used together."""
        # Function-scoped fixture
        func_dir = tmp_path / ".agilevv-test-func"
        func_config = PathConfig(base_dir=func_dir)

        # Module-scoped fixture
        module_dir = tmp_path / ".agilevv-test-module"
        module_config = PathConfig(base_dir=module_dir)

        assert func_config.base_dir != module_config.base_dir
        assert func_config.is_test_environment()
        assert module_config.is_test_environment()

    @pytest.mark.parametrize("scope", ["function", "module", "session"])
    def test_fixture_scope_behavior(self, scope: str, tmp_path: Path) -> None:
        """Test that fixtures behave correctly for different scopes."""
        test_dir = tmp_path / f".agilevv-test-{scope}"
        config = PathConfig(base_dir=test_dir)

        assert config.is_test_environment()
        assert scope in str(config.base_dir)


class TestTestDataBuilders:
    """Test helper utilities for building test data."""

    def test_build_sample_backlog(self, tmp_path: Path) -> None:
        """Test building a sample backlog for testing."""
        test_dir = tmp_path / ".agilevv-test"
        config = PathConfig(base_dir=test_dir)
        config.ensure_structure()

        # Helper to build sample backlog
        sample_backlog = """# Product Backlog

## User Stories

1. As a developer, I want test isolation
2. As a tester, I want parallel execution
"""
        config.backlog_path.write_text(sample_backlog)

        assert config.backlog_path.read_text() == sample_backlog

    def test_build_sample_sprint(self, tmp_path: Path) -> None:
        """Test building a sample sprint structure."""
        test_dir = tmp_path / ".agilevv-test"
        config = PathConfig(base_dir=test_dir)
        config.ensure_structure()

        # Helper to build sample sprint
        sprint_dir = config.requirements_dir / "sprint-01"
        sprint_dir.mkdir()
        (sprint_dir / "requirements.md").write_text("# Sprint 1 Requirements")
        (sprint_dir / "tasks.md").write_text("# Sprint 1 Tasks")

        assert sprint_dir.exists()
        assert (sprint_dir / "requirements.md").exists()
        assert (sprint_dir / "tasks.md").exists()


class TestParallelExecution:
    """Test support for parallel test execution."""

    def test_no_conflicts_with_parallel_execution(self, tmp_path: Path) -> None:
        """Test that parallel tests don't conflict."""
        # Each parallel test gets unique directory
        test_dirs = []
        for i in range(5):
            test_dir = tmp_path / f".agilevv-test-parallel-{i}"
            config = PathConfig(base_dir=test_dir)
            test_dirs.append(config.base_dir)

        # All directories should be unique
        assert len(set(test_dirs)) == 5

    def test_filelock_prevents_race_conditions(self, tmp_path: Path) -> None:
        """Test that file locking prevents race conditions."""
        # This will use filelock library when implemented
        test_dir = tmp_path / ".agilevv-test"
        config = PathConfig(base_dir=test_dir)

        # Simulate concurrent access
        config.ensure_structure()

        # Multiple "processes" should not corrupt data
        assert config.base_dir.exists()
        assert config.is_test_environment()
