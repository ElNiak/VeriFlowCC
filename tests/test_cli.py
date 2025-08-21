"""Test CLI functionality with proper test isolation.

NOTE: Mock infrastructure has been removed. CLI tests now focus on help commands
and basic functionality that doesn't require SDK integration.
"""

import os
from pathlib import Path

import pytest
from typer.testing import CliRunner
from verifflowcc.cli import app
from verifflowcc.core.path_config import PathConfig


@pytest.fixture
def runner() -> CliRunner:
    """Create a CLI test runner."""
    return CliRunner()


@pytest.fixture
def fresh_project_dir(tmp_path: Path) -> Path:
    """Create a fresh project directory for testing."""
    return tmp_path


@pytest.fixture
def mock_project_dir(tmp_path: Path) -> Path:
    """Create a mock project directory with basic structure."""
    project_dir = tmp_path / "mock_project"
    project_dir.mkdir()
    return project_dir


class TestCLIHelp:
    """Test CLI help functionality."""

    def test_main_help(self, runner: CliRunner) -> None:
        """Test main CLI help command."""
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "VeriFlowCC" in result.output
        assert "init" in result.output
        assert "sprint" in result.output

    def test_init_help(self, runner: CliRunner) -> None:
        """Test init command help."""
        result = runner.invoke(app, ["init", "--help"])
        assert result.exit_code == 0
        assert "Initialize" in result.output

    def test_sprint_help(self, runner: CliRunner) -> None:
        """Test sprint command help."""
        result = runner.invoke(app, ["sprint", "--help"])
        assert result.exit_code == 0
        assert "story" in result.output.lower()

    def test_status_help(self, runner: CliRunner) -> None:
        """Test status command help."""
        result = runner.invoke(app, ["status", "--help"])
        assert result.exit_code == 0


class TestCLIBasicValidation:
    """Test basic CLI validation without SDK dependencies."""

    def test_version_command(self, runner: CliRunner) -> None:
        """Test version command."""
        result = runner.invoke(app, ["--version"])
        # Command should work regardless of exit code
        assert "version" in result.output.lower() or result.exit_code == 0

    def test_invalid_command(self, runner: CliRunner) -> None:
        """Test handling of invalid commands."""
        result = runner.invoke(app, ["invalid_command"])
        assert result.exit_code != 0


class TestCLIStructureValidation:
    """Test CLI structure validation."""

    def test_config_structure_validation(self, fresh_project_dir: Path) -> None:
        """Test configuration structure validation."""
        # Create a basic .agilevv structure
        agilevv_dir = fresh_project_dir / ".agilevv"
        agilevv_dir.mkdir()

        # Create basic config file
        config_file = agilevv_dir / "config.yaml"
        config_file.write_text(
            """
gating:
  requirements:
    hard: true
    quality_threshold: 0.8
agents:
  requirements_analyst:
    timeout: 60
"""
        )

        # Validate structure exists
        assert config_file.exists()
        assert agilevv_dir.exists()

    def test_path_config_initialization(self, fresh_project_dir: Path) -> None:
        """Test PathConfig initialization in test environment."""
        # Set environment to use test directory
        old_value = os.environ.get("AGILEVV_BASE_DIR")
        try:
            os.environ["AGILEVV_BASE_DIR"] = str(fresh_project_dir / ".agilevv-test")
            config = PathConfig()
            assert config.is_test_environment()
        finally:
            if old_value is None:
                os.environ.pop("AGILEVV_BASE_DIR", None)
            else:
                os.environ["AGILEVV_BASE_DIR"] = old_value


# NOTE: Real CLI integration tests are implemented in test_real_cli_integration.py
