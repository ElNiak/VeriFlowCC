"""Example usage scenarios for the test isolation framework.

This module demonstrates various use cases for the VeriFlowCC test isolation
framework, showing how to use different fixture scopes and the factory pattern.
"""

from typing import TYPE_CHECKING

import pytest
from verifflowcc.core.path_config import PathConfig

if TYPE_CHECKING:
    from tests.conftest import AgileVVDirFactory


class TestBasicIsolationExamples:
    """Basic examples of using test isolation fixtures."""

    def test_example_isolated_test_directory(self, isolated_agilevv_dir: PathConfig) -> None:
        """Example: Each test gets its own isolated directory.

        This example shows how to use the function-scoped fixture for
        complete test isolation. Each test gets a fresh directory.
        """
        # The fixture provides a configured PathConfig instance
        assert isinstance(isolated_agilevv_dir, PathConfig)
        assert isolated_agilevv_dir.is_test_environment()

        # Create test data in the isolated environment
        test_file = isolated_agilevv_dir.backlog_path
        test_file.write_text("# Test Backlog\n\nTest user story")

        # Verify the file exists in the test environment
        assert test_file.exists()
        assert "Test user story" in test_file.read_text()

        # Directory will be automatically cleaned up after this test

    def test_example_environment_isolation(self, isolated_agilevv_dir: PathConfig) -> None:
        """Example: Environment variables are isolated per test.

        Shows that each test has its own AGILEVV_BASE_DIR environment
        variable that doesn't affect other tests or production.
        """
        import os

        # The environment variable is set for this test
        env_value = os.environ.get("AGILEVV_BASE_DIR")
        assert env_value is not None
        assert str(isolated_agilevv_dir.base_dir) == env_value

        # This won't affect other tests or production code


class TestSharedDirectoryExamples:
    """Examples of sharing directories between tests."""

    def test_example_shared_setup_part1(self, shared_agilevv_dir: PathConfig) -> None:
        """Example: Multiple tests share the same directory (Part 1).

        This test creates data that will be available to other tests
        in the same module using the module-scoped fixture.
        """
        # Create shared test data
        shared_file = shared_agilevv_dir.requirements_dir / "shared_requirements.md"
        shared_file.parent.mkdir(parents=True, exist_ok=True)
        shared_file.write_text("# Shared Requirements\n\nRequirement 1")

        assert shared_file.exists()

    def test_example_shared_setup_part2(self, shared_agilevv_dir: PathConfig) -> None:
        """Example: Multiple tests share the same directory (Part 2).

        This test can access data created by Part 1 because they share
        the same module-scoped fixture.
        """
        # Access data created by previous test
        shared_file = shared_agilevv_dir.requirements_dir / "shared_requirements.md"

        # File still exists from Part 1
        assert shared_file.exists()
        assert "Requirement 1" in shared_file.read_text()

        # Add more data
        content = shared_file.read_text()
        shared_file.write_text(content + "\nRequirement 2")


class TestFactoryPatternExamples:
    """Examples of using the AgileVVDirFactory for complex setups."""

    def test_example_factory_with_backlog(self, agilevv_factory: "AgileVVDirFactory") -> None:
        """Example: Create test directory with pre-populated backlog.

        Shows how to use the factory to quickly set up test data
        for testing backlog-related functionality.
        """
        # Create a test environment with sample backlog
        config = agilevv_factory.create_with_backlog(
            name="backlog-test",
            stories=[
                "As a developer, I want test isolation",
                "As a tester, I want parallel execution",
                "As a user, I want fast tests",
            ],
        )

        # The backlog is pre-populated
        assert config.backlog_path.exists()
        backlog_content = config.backlog_path.read_text()
        assert "As a developer, I want test isolation" in backlog_content
        assert "As a tester, I want parallel execution" in backlog_content

    def test_example_factory_with_sprint(self, agilevv_factory: "AgileVVDirFactory") -> None:
        """Example: Create test directory with sprint structure.

        Demonstrates setting up a sprint environment for testing
        sprint-related functionality.
        """
        # Create test environment with sprint data
        config = agilevv_factory.create_with_sprint(name="sprint-test", sprint_num=1)

        # Sprint structure is created
        sprint_dir = config.requirements_dir / "sprint-01"
        assert sprint_dir.exists()
        assert (sprint_dir / "requirements.md").exists()
        assert (sprint_dir / "tasks.md").exists()

    def test_example_factory_full_structure(self, agilevv_factory: "AgileVVDirFactory") -> None:
        """Example: Create complete test structure.

        Shows how to set up a full VeriFlowCC directory structure
        for integration testing.
        """
        # Create complete structure
        config = agilevv_factory.create_full_structure(name="integration-test")

        # All components are present
        assert config.backlog_path.exists()
        assert config.requirements_dir.exists()
        assert config.architecture_path.exists()
        assert config.config_path.exists()

        # Config file has content
        assert "version" in config.config_path.read_text()


class TestParallelExecutionExamples:
    """Examples showing parallel test execution safety."""

    @pytest.mark.parametrize("test_id", [1, 2, 3, 4, 5])
    def test_example_parallel_isolation(
        self, test_id: int, isolated_agilevv_dir: PathConfig
    ) -> None:
        """Example: Parallel tests don't interfere with each other.

        This parametrized test runs multiple times in parallel,
        each with its own isolated directory.
        """
        # Each parallel instance gets unique directory
        test_file = isolated_agilevv_dir.base_dir / f"test_{test_id}.txt"
        test_file.write_text(f"Test {test_id} data")

        # Verify this test's data
        assert test_file.exists()
        assert f"Test {test_id} data" in test_file.read_text()

        # No other test's data is visible
        for other_id in range(1, 6):
            if other_id != test_id:
                other_file = isolated_agilevv_dir.base_dir / f"test_{other_id}.txt"
                assert not other_file.exists()


class TestCleanupExamples:
    """Examples of cleanup strategies."""

    def test_example_automatic_cleanup(self, isolated_agilevv_dir: PathConfig) -> None:
        """Example: Automatic cleanup after test.

        Shows that test directories are automatically cleaned up
        unless --keep-test-dirs flag is used.
        """
        # Create test data
        test_dir = isolated_agilevv_dir.base_dir
        test_file = test_dir / "temporary.txt"
        test_file.write_text("This will be cleaned up")

        assert test_file.exists()
        # After this test, the directory will be removed automatically

    def test_example_cleanup_with_keep_flag(
        self, isolated_agilevv_dir: PathConfig, request: pytest.FixtureRequest
    ) -> None:
        """Example: Keep test directories for debugging.

        When running with pytest --keep-test-dirs, directories are
        preserved for post-test debugging.
        """
        # Check if keep flag is set
        keep_dirs = request.config.getoption("--keep-test-dirs", False)

        # Create debug data
        debug_file = isolated_agilevv_dir.base_dir / "debug_info.txt"
        debug_file.write_text("Debug information for investigation")

        if keep_dirs:
            # Directory will be kept after test
            print(f"Test directory kept at: {isolated_agilevv_dir.base_dir}")
        else:
            # Directory will be cleaned up
            pass


class TestRealWorldScenarios:
    """Real-world usage scenarios."""

    def test_example_testing_vmodel_workflow(self, agilevv_factory: "AgileVVDirFactory") -> None:
        """Example: Testing V-Model workflow with isolation.

        Shows how to test the V-Model workflow stages using
        isolated test environments.
        """
        # Set up V-Model test environment
        config = agilevv_factory.create_basic(name="vmodel-test")

        # Simulate requirements stage
        requirements = config.requirements_dir / "requirements.md"
        requirements.parent.mkdir(parents=True, exist_ok=True)
        requirements.write_text("# Requirements\n\n- REQ-001: Test isolation")

        # Simulate design stage
        architecture = config.architecture_path
        architecture.write_text("# Architecture\n\nComponent: TestIsolation")

        # Simulate checkpoint
        checkpoint = config.checkpoints_dir / "checkpoint-001.json"
        checkpoint.parent.mkdir(parents=True, exist_ok=True)
        checkpoint.write_text('{"stage": "design", "status": "complete"}')

        # Verify workflow progression
        assert requirements.exists()
        assert architecture.exists()
        assert checkpoint.exists()

    def test_example_testing_agent_artifacts(self, isolated_agilevv_dir: PathConfig) -> None:
        """Example: Testing agent artifact generation.

        Demonstrates how agents can safely generate artifacts
        in isolated test environments.
        """
        # Simulate agent creating artifacts
        agent_output = isolated_agilevv_dir.get_artifact_path("agent_output.md")
        agent_output.parent.mkdir(parents=True, exist_ok=True)
        agent_output.write_text("# Agent Output\n\nGenerated content")

        # Verify artifact creation
        assert agent_output.exists()
        assert agent_output.is_relative_to(isolated_agilevv_dir.base_dir)

        # Test security - can't write outside base directory
        with pytest.raises(ValueError):
            isolated_agilevv_dir.get_artifact_path("/etc/passwd")

        with pytest.raises(ValueError):
            isolated_agilevv_dir.get_artifact_path("../../../etc/passwd")


class TestDebuggingExamples:
    """Examples for debugging test issues."""

    def test_example_debugging_test_state(self, isolated_agilevv_dir: PathConfig) -> None:
        """Example: Debugging test state and environment.

        Shows how to inspect the test environment for debugging
        purposes.
        """
        import os

        # Print test environment information
        print(f"\nTest Directory: {isolated_agilevv_dir.base_dir}")
        print(f"Is Test Environment: {isolated_agilevv_dir.is_test_environment()}")
        print(f"Environment Variable: {os.environ.get('AGILEVV_BASE_DIR')}")

        # List all created directories
        for path in isolated_agilevv_dir.base_dir.rglob("*"):
            if path.is_dir():
                print(f"  Directory: {path.relative_to(isolated_agilevv_dir.base_dir)}")

        # Create some test data for inspection
        test_data = isolated_agilevv_dir.base_dir / "test_data.json"
        test_data.write_text('{"test": "data", "debug": true}')

        assert test_data.exists()
