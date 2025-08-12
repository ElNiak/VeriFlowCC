"""Path configuration for the .agilevv directory structure.

This module provides a centralized configuration for all paths related to
the .agilevv directory, supporting both production and test environments
with configurable base directories.
"""

import json
import os
import shutil
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

import yaml


class PathConfig:
    """Manages paths for the .agilevv directory structure.

    This class provides a configurable base directory for the .agilevv folder,
    allowing tests to use isolated directories while maintaining backward
    compatibility with production code.

    Attributes:
        base_dir: The base directory for all .agilevv-related paths.
    """

    def __init__(self, base_dir: str | Path | None = None) -> None:
        """Initialize PathConfig with configurable base directory.

        Args:
            base_dir: Base directory for .agilevv structure. If None, checks
                     AGILEVV_BASE_DIR environment variable, then defaults to
                     .agilevv in current working directory.
        """
        if base_dir is not None:
            # Explicit base_dir takes precedence
            self.base_dir = Path(base_dir)
        elif env_dir := os.environ.get("AGILEVV_BASE_DIR"):
            # Environment variable is second priority
            self.base_dir = Path(env_dir).expanduser()
        else:
            # Default to .agilevv in current working directory
            self.base_dir = Path.cwd() / ".agilevv"

        # Ensure base_dir is absolute
        if not self.base_dir.is_absolute():
            self.base_dir = Path.cwd() / self.base_dir

    # Core configuration paths
    @property
    def config_path(self) -> Path:
        """Path to config.yaml file."""
        return self.base_dir / "config.yaml"

    @property
    def state_path(self) -> Path:
        """Path to state.json file."""
        return self.base_dir / "state.json"

    @property
    def backlog_path(self) -> Path:
        """Path to backlog.md file."""
        return self.base_dir / "backlog.md"

    @property
    def architecture_path(self) -> Path:
        """Path to architecture.md file."""
        return self.base_dir / "architecture.md"

    # Directory paths
    @property
    def requirements_dir(self) -> Path:
        """Path to requirements directory."""
        return self.base_dir / "requirements"

    @property
    def c4_diagrams_dir(self) -> Path:
        """Path to C4 diagrams directory."""
        return self.base_dir / "c4" / "diagrams"

    @property
    def checkpoints_dir(self) -> Path:
        """Path to checkpoints directory."""
        return self.base_dir / "checkpoints"

    @property
    def logs_dir(self) -> Path:
        """Path to logs directory."""
        return self.base_dir / "logs"

    def get_artifact_path(self, artifact_name: str) -> Path:
        """Get path for a specific artifact within base directory.

        Args:
            artifact_name: Name or relative path of the artifact.

        Returns:
            Full path to the artifact.

        Raises:
            ValueError: If artifact_name is an absolute path or contains
                       parent directory references.
        """
        artifact_path = Path(artifact_name)

        # Security: Prevent absolute paths
        if artifact_path.is_absolute():
            raise ValueError("Artifact path cannot be absolute")

        # Security: Prevent directory traversal
        if ".." in artifact_path.parts:
            raise ValueError("Artifact path cannot contain parent directory references")

        return self.base_dir / artifact_path

    def ensure_base_exists(self) -> None:
        """Create base directory if it doesn't exist."""
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def ensure_structure(self, create_defaults: bool = False) -> None:
        """Create the complete .agilevv directory structure.

        Args:
            create_defaults: If True, create default config files if they
                           don't already exist.
        """
        # Create base directory
        self.ensure_base_exists()

        # Create all subdirectories
        self.requirements_dir.mkdir(parents=True, exist_ok=True)
        self.c4_diagrams_dir.mkdir(parents=True, exist_ok=True)
        self.checkpoints_dir.mkdir(parents=True, exist_ok=True)
        self.logs_dir.mkdir(parents=True, exist_ok=True)

        # Create default config files if requested
        if create_defaults:
            if not self.config_path.exists():
                default_config = {
                    "version": "1.0.0",
                    "project": "VeriFlowCC",
                    "gating": {"hard": True, "soft_warnings": True},
                }
                with self.config_path.open("w") as f:
                    yaml.safe_dump(default_config, f)

            if not self.state_path.exists():
                default_state = {
                    "current_sprint": 0,
                    "current_stage": "planning",
                    "checkpoints": [],
                }
                with self.state_path.open("w") as f:
                    json.dump(default_state, f, indent=2)

    def validate_path(self, path: Path, must_be_inside: bool = False) -> bool:
        """Validate that a path exists and optionally is within base directory.

        Args:
            path: Path to validate.
            must_be_inside: If True, ensure path is within base directory.

        Returns:
            True if path exists (and is inside base_dir if required).

        Raises:
            ValueError: If must_be_inside is True and path is outside base_dir.
        """
        if must_be_inside:
            try:
                path.resolve().relative_to(self.base_dir.resolve())
            except ValueError as e:
                raise ValueError(f"Path {path} is outside base directory {self.base_dir}") from e

        return path.exists()

    def is_test_environment(self) -> bool:
        """Check if running in a test environment.

        Returns:
            True if running under pytest or in test mode.
        """
        # Check for pytest
        if "pytest" in os.environ.get("PYTEST_CURRENT_TEST", ""):
            return True

        # Check if base_dir indicates test environment
        if "test" in str(self.base_dir).lower():
            return True

        # Check for common test runners
        import sys

        if any("pytest" in arg for arg in sys.argv):
            return True

        return False

    def cleanup(self) -> None:
        """Remove the base directory and all contents.

        WARNING: This is destructive! Only use for test cleanup.

        Raises:
            ValueError: If attempting to cleanup a non-test directory.
        """
        # Safety check: Only allow cleanup of test directories
        base_name = self.base_dir.name.lower()
        if not ("test" in base_name or base_name.startswith(".agilevv-test")):
            raise ValueError(
                f"Cannot cleanup non-test directory: {self.base_dir}. "
                "This operation is only allowed for test directories."
            )

        if self.base_dir.exists():
            shutil.rmtree(self.base_dir)

    @classmethod
    def create_test_instance(cls, test_dir: Path | None = None) -> "PathConfig":
        """Create a PathConfig instance for testing.

        Args:
            test_dir: Optional test directory. If None, creates a temp directory.

        Returns:
            PathConfig instance configured for testing.
        """
        if test_dir is None:
            import tempfile

            test_dir = Path(tempfile.mkdtemp(prefix="agilevv-test-"))

        return cls(base_dir=test_dir)

    @classmethod
    @contextmanager
    def test_isolation(cls, test_dir: Path | None = None) -> Iterator["PathConfig"]:
        """Context manager for temporary test isolation.

        Args:
            test_dir: Optional test directory. If None, creates a temp directory.

        Yields:
            PathConfig instance configured for testing.
        """
        config = cls.create_test_instance(test_dir)
        config.ensure_base_exists()

        try:
            yield config
        finally:
            # Cleanup is optional - tests can choose to keep directories
            # for debugging by not calling cleanup()
            pass

    def __eq__(self, other: object) -> bool:
        """Check equality based on base_dir."""
        if not isinstance(other, PathConfig):
            return NotImplemented
        return self.base_dir == other.base_dir

    def __hash__(self) -> int:
        """Hash based on base_dir for use in sets/dicts."""
        return hash(self.base_dir)

    def __str__(self) -> str:
        """Human-readable string representation."""
        return f"PathConfig(base_dir={self.base_dir})"

    def __repr__(self) -> str:
        """Developer-friendly string representation."""
        return f"PathConfig(base_dir={self.base_dir!r})"
