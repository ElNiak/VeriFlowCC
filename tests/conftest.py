"""Pytest configuration and fixtures for test isolation."""

import os
import shutil
from collections.abc import Generator
from pathlib import Path

import pytest
from verifflowcc.core.path_config import PathConfig


def pytest_addoption(parser: pytest.Parser) -> None:
    """Add custom command-line options for test execution."""
    parser.addoption(
        "--keep-test-dirs",
        action="store_true",
        default=False,
        help="Keep test directories after test completion for debugging",
    )


@pytest.fixture(scope="function")
def isolated_agilevv_dir(
    request: pytest.FixtureRequest, tmp_path: Path
) -> Generator[PathConfig, None, None]:
    """Provide an isolated .agilevv-test directory for each test function.

    This fixture creates a unique test directory for each test function,
    ensuring complete isolation between tests. The directory is automatically
    cleaned up after the test completes unless --keep-test-dirs is specified.

    Args:
        request: Pytest fixture request object
        tmp_path: Pytest's tmp_path fixture for temporary directories

    Yields:
        PathConfig: Configured PathConfig instance for the test directory
    """
    # Create unique test directory
    test_name = request.node.name.replace("[", "_").replace("]", "_").replace(" ", "_")
    test_dir = tmp_path / f".agilevv-test-{test_name}"

    # Set environment variable for this test
    original_env = os.environ.get("AGILEVV_BASE_DIR")
    os.environ["AGILEVV_BASE_DIR"] = str(test_dir)

    # Create PathConfig instance
    config = PathConfig(base_dir=test_dir)
    config.ensure_structure()

    try:
        yield config
    finally:
        # Restore original environment
        if original_env is not None:
            os.environ["AGILEVV_BASE_DIR"] = original_env
        elif "AGILEVV_BASE_DIR" in os.environ:
            del os.environ["AGILEVV_BASE_DIR"]

        # Clean up unless --keep-test-dirs is specified
        if not request.config.getoption("--keep-test-dirs"):
            if test_dir.exists():
                config.cleanup()


@pytest.fixture(scope="module")
def shared_agilevv_dir(
    request: pytest.FixtureRequest, tmp_path_factory: pytest.TempPathFactory
) -> Generator[PathConfig, None, None]:
    """Provide a shared .agilevv-test directory for all tests in a module.

    This fixture creates a single test directory that is shared by all tests
    within a module. This is useful for integration tests that need to share
    state or when test setup is expensive.

    Args:
        request: Pytest fixture request object
        tmp_path_factory: Pytest's tmp_path_factory for module-scoped temp dirs

    Yields:
        PathConfig: Configured PathConfig instance for the shared directory
    """
    # Create module-scoped test directory
    module_name = request.module.__name__.replace(".", "_")
    test_dir = tmp_path_factory.mktemp("agilevv") / f".agilevv-test-module-{module_name}"

    # Set environment variable for this module
    original_env = os.environ.get("AGILEVV_BASE_DIR")
    os.environ["AGILEVV_BASE_DIR"] = str(test_dir)

    # Create PathConfig instance
    config = PathConfig(base_dir=test_dir)
    config.ensure_structure()

    try:
        yield config
    finally:
        # Restore original environment
        if original_env is not None:
            os.environ["AGILEVV_BASE_DIR"] = original_env
        elif "AGILEVV_BASE_DIR" in os.environ:
            del os.environ["AGILEVV_BASE_DIR"]

        # Clean up unless --keep-test-dirs is specified
        if not request.config.getoption("--keep-test-dirs"):
            if test_dir.exists():
                config.cleanup()


@pytest.fixture(scope="session")
def session_agilevv_dir(
    request: pytest.FixtureRequest, tmp_path_factory: pytest.TempPathFactory
) -> Generator[PathConfig, None, None]:
    """Provide a session-wide .agilevv-test directory for all tests.

    This fixture creates a single test directory that is shared across the
    entire test session. This is useful for expensive setup that should only
    be done once, or for tests that need to maintain state across modules.

    Args:
        request: Pytest fixture request object
        tmp_path_factory: Pytest's tmp_path_factory for session-scoped temp dirs

    Yields:
        PathConfig: Configured PathConfig instance for the session directory
    """
    # Create session-scoped test directory
    test_dir = tmp_path_factory.mktemp("agilevv") / ".agilevv-test-session"

    # Set environment variable for this session
    original_env = os.environ.get("AGILEVV_BASE_DIR")
    os.environ["AGILEVV_BASE_DIR"] = str(test_dir)

    # Create PathConfig instance
    config = PathConfig(base_dir=test_dir)
    config.ensure_structure()

    try:
        yield config
    finally:
        # Restore original environment
        if original_env is not None:
            os.environ["AGILEVV_BASE_DIR"] = original_env
        elif "AGILEVV_BASE_DIR" in os.environ:
            del os.environ["AGILEVV_BASE_DIR"]

        # Clean up unless --keep-test-dirs is specified
        if not request.config.getoption("--keep-test-dirs"):
            if test_dir.exists():
                config.cleanup()


class AgileVVDirFactory:
    """Factory for creating complex test directory structures.

    This factory provides methods for creating customized .agilevv directory
    structures with prepopulated data, specific configurations, and various
    cleanup strategies.
    """

    def __init__(self, base_path: Path):
        """Initialize the factory with a base path.

        Args:
            base_path: Base path for creating test directories
        """
        self.base_path = base_path
        self._configs: list[PathConfig] = []

    def create_basic(self, name: str = "test") -> PathConfig:
        """Create a basic test directory structure.

        Args:
            name: Name suffix for the test directory

        Returns:
            PathConfig: Configured instance for the test directory
        """
        test_dir = self.base_path / f".agilevv-test-{name}"
        config = PathConfig(base_dir=test_dir)
        config.ensure_structure()
        self._configs.append(config)
        return config

    def create_with_backlog(
        self, name: str = "test", stories: list[str] | None = None
    ) -> PathConfig:
        """Create test directory with prepopulated backlog.

        Args:
            name: Name suffix for the test directory
            stories: List of user stories to add to backlog

        Returns:
            PathConfig: Configured instance with backlog data
        """
        config = self.create_basic(name)

        # Create default stories if none provided
        if stories is None:
            stories = [
                "As a developer, I want test isolation",
                "As a tester, I want parallel execution",
                "As a user, I want reliable tests",
            ]

        # Write backlog
        backlog_content = "# Product Backlog\n\n## User Stories\n\n"
        for i, story in enumerate(stories, 1):
            backlog_content += f"{i}. {story}\n"

        config.backlog_path.write_text(backlog_content)
        return config

    def create_with_sprint(self, name: str = "test", sprint_num: int = 1) -> PathConfig:
        """Create test directory with sprint structure.

        Args:
            name: Name suffix for the test directory
            sprint_num: Sprint number to create

        Returns:
            PathConfig: Configured instance with sprint data
        """
        config = self.create_basic(name)

        # Create sprint directory
        sprint_dir = config.requirements_dir / f"sprint-{sprint_num:02d}"
        sprint_dir.mkdir(parents=True)

        # Create sprint files
        (sprint_dir / "requirements.md").write_text(f"# Sprint {sprint_num} Requirements")
        (sprint_dir / "tasks.md").write_text(f"# Sprint {sprint_num} Tasks")
        (sprint_dir / "retrospective.md").write_text(f"# Sprint {sprint_num} Retrospective")

        return config

    def create_with_memory(
        self, name: str = "test", memories: dict[str, str] | None = None
    ) -> PathConfig:
        """Create test directory with memory files.

        Args:
            name: Name suffix for the test directory
            memories: Dictionary of memory file names and contents

        Returns:
            PathConfig: Configured instance with memory data
        """
        config = self.create_basic(name)

        # Create default memories if none provided
        if memories is None:
            memories = {
                "context.md": "# Project Context\n\nTest project context.",
                "decisions.md": "# Technical Decisions\n\nTest decisions.",
            }

        # Write memory files
        for filename, content in memories.items():
            (config.logs_dir / filename).write_text(content)

        return config

    def create_full_structure(self, name: str = "test") -> PathConfig:
        """Create a complete test directory structure with all components.

        Args:
            name: Name suffix for the test directory

        Returns:
            PathConfig: Configured instance with full structure
        """
        config = self.create_with_backlog(name)

        # Add sprint
        sprint_dir = config.requirements_dir / "sprint-01"
        sprint_dir.mkdir(parents=True)
        (sprint_dir / "requirements.md").write_text("# Sprint 1 Requirements")

        # Add memory
        (config.logs_dir / "context.md").write_text("# Context")

        # Add architecture
        config.architecture_path.write_text("# System Architecture")

        # Add config
        config.config_path.write_text("version: 1.0\ngating: soft")

        return config

    def cleanup_all(self, keep_dirs: bool = False) -> None:
        """Clean up all created test directories.

        Args:
            keep_dirs: If True, keep directories for debugging
        """
        if not keep_dirs:
            for config in self._configs:
                if config.base_dir.exists():
                    config.cleanup()
        self._configs.clear()

    def cleanup_selective(self, patterns: list[str]) -> None:
        """Clean up only files matching specific patterns.

        Args:
            patterns: List of glob patterns to match for cleanup
        """
        for config in self._configs:
            if config.base_dir.exists():
                for pattern in patterns:
                    for path in config.base_dir.glob(pattern):
                        if path.is_file():
                            path.unlink()
                        elif path.is_dir():
                            shutil.rmtree(path)


@pytest.fixture
def agilevv_factory(tmp_path: Path) -> Generator[AgileVVDirFactory, None, None]:
    """Provide an AgileVVDirFactory for creating test structures.

    Args:
        tmp_path: Pytest's tmp_path fixture

    Yields:
        AgileVVDirFactory: Factory instance for creating test directories
    """
    factory = AgileVVDirFactory(tmp_path)
    try:
        yield factory
    finally:
        # Cleanup all created directories
        factory.cleanup_all()


# Test data builders
def build_sample_user_story(story_id: str, title: str, description: str) -> dict[str, str]:
    """Build a sample user story for testing.

    Args:
        story_id: Unique story identifier
        title: Story title
        description: Story description

    Returns:
        Dictionary with story data
    """
    return {
        "id": story_id,
        "title": title,
        "description": description,
        "acceptance_criteria": [
            "Given initial state",
            "When action occurs",
            "Then expected outcome",
        ],
        "status": "pending",
    }


def build_sample_sprint_data(sprint_num: int, stories: list[str]) -> dict[str, any]:
    """Build sample sprint data for testing.

    Args:
        sprint_num: Sprint number
        stories: List of story IDs for the sprint

    Returns:
        Dictionary with sprint data
    """
    return {
        "sprint_number": sprint_num,
        "stories": stories,
        "start_date": "2024-01-01",
        "end_date": "2024-01-14",
        "velocity": len(stories) * 3,
        "status": "planning",
    }
