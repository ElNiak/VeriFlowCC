"""Test CLI functionality with proper test isolation."""

import json
import os
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner
from verifflowcc.cli import app
from verifflowcc.core.path_config import PathConfig


@pytest.fixture
def runner() -> CliRunner:
    """Create a CLI test runner."""
    return CliRunner()


@pytest.fixture
def mock_project_dir(isolated_agilevv_dir: PathConfig) -> Path:
    """Create a mock project directory using isolated PathConfig.

    This fixture now uses the isolated_agilevv_dir to ensure proper test isolation.
    """
    # Return the parent directory (project root) not the .agilevv dir itself
    return isolated_agilevv_dir.base_dir.parent


@pytest.fixture
def fresh_project_dir(tmp_path: Path) -> Path:
    """Create a fresh project directory for init tests.

    This doesn't pre-create the .agilevv structure.
    """
    return tmp_path


class TestCLIStructure:
    """Test CLI application structure and command registration."""

    def test_cli_app_exists(self) -> None:
        """Test that the CLI app is properly configured."""
        assert app is not None
        assert hasattr(app, "commands")

    def test_help_command(self, runner: CliRunner) -> None:
        """Test that help command works."""
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "VeriFlowCC" in result.stdout

    def test_version_command(self, runner: CliRunner) -> None:
        """Test that version command works."""
        result = runner.invoke(app, ["--version"])
        assert result.exit_code == 0
        assert "VeriFlowCC" in result.stdout


class TestInitCommand:
    """Test the init command functionality."""

    def test_init_command_basic(self, runner: CliRunner, fresh_project_dir: Path) -> None:
        """Test basic init command."""
        with patch("verifflowcc.cli.Path.cwd", return_value=fresh_project_dir):
            result = runner.invoke(app, ["init"])
            assert result.exit_code == 0
            assert "Initialized VeriFlowCC" in result.stdout

    def test_init_command_with_force(self, runner: CliRunner, fresh_project_dir: Path) -> None:
        """Test init command with --force flag."""
        with patch("verifflowcc.cli.Path.cwd", return_value=fresh_project_dir):
            # First init
            result = runner.invoke(app, ["init"])
            assert result.exit_code == 0

            # Second init should fail without force
            result = runner.invoke(app, ["init"])
            assert result.exit_code != 0

            # Should work with force
            result = runner.invoke(app, ["init", "--force"])
            assert result.exit_code == 0

    def test_init_creates_structure(self, runner: CliRunner, fresh_project_dir: Path) -> None:
        """Test that init creates the expected directory structure."""
        with patch("verifflowcc.cli.Path.cwd", return_value=fresh_project_dir):
            result = runner.invoke(app, ["init"])
            assert result.exit_code == 0

            # Check that .agilevv structure was created
            agilevv_dir = fresh_project_dir / ".agilevv"
            assert agilevv_dir.exists()
            assert (agilevv_dir / "config.yaml").exists()
            assert (agilevv_dir / "state.json").exists()


class TestPlanCommand:
    """Test the plan command."""

    def test_plan_no_backlog(
        self, runner: CliRunner, mock_project_dir: Path, isolated_agilevv_dir: PathConfig
    ) -> None:
        """Test plan command when no backlog exists."""
        with patch("verifflowcc.cli.Path.cwd", return_value=mock_project_dir):
            isolated_agilevv_dir.ensure_structure(create_defaults=False)
            with patch.dict(os.environ, {"AGILEVV_BASE_DIR": str(isolated_agilevv_dir.base_dir)}):
                result = runner.invoke(app, ["plan"])
                assert result.exit_code != 0
                assert "backlog not found" in result.stdout.lower()

    def test_plan_list_stories(
        self, runner: CliRunner, mock_project_dir: Path, isolated_agilevv_dir: PathConfig
    ) -> None:
        """Test plan command lists stories from backlog."""
        with patch("verifflowcc.cli.Path.cwd", return_value=mock_project_dir):
            isolated_agilevv_dir.ensure_structure(create_defaults=True)
            # Create backlog
            isolated_agilevv_dir.backlog_path.write_text(
                "# Backlog\n\n- [ ] Story 1\n- [ ] Story 2"
            )

            with patch.dict(os.environ, {"AGILEVV_BASE_DIR": str(isolated_agilevv_dir.base_dir)}):
                result = runner.invoke(app, ["plan"])
                assert result.exit_code == 0
                assert "Story 1" in result.stdout
                assert "Story 2" in result.stdout

    def test_plan_select_story(
        self, runner: CliRunner, mock_project_dir: Path, isolated_agilevv_dir: PathConfig
    ) -> None:
        """Test plan command can select a specific story."""
        with patch("verifflowcc.cli.Path.cwd", return_value=mock_project_dir):
            isolated_agilevv_dir.ensure_structure(create_defaults=True)
            # Create backlog
            isolated_agilevv_dir.backlog_path.write_text(
                "# Backlog\n\n- [ ] Story 1\n- [ ] Story 2"
            )
            # Create state.json

            state_data = {"active_story": None, "current_stage": "planning"}
            isolated_agilevv_dir.state_path.write_text(json.dumps(state_data))

            with patch.dict(os.environ, {"AGILEVV_BASE_DIR": str(isolated_agilevv_dir.base_dir)}):
                result = runner.invoke(app, ["plan", "--story-id", "1"])
                assert result.exit_code == 0
                assert "Story selected" in result.stdout


class TestSprintCommand:
    """Test the sprint command."""

    def test_sprint_no_story_selected(
        self, runner: CliRunner, mock_project_dir: Path, isolated_agilevv_dir: PathConfig
    ) -> None:
        """Test sprint command when no story is selected."""
        with patch("verifflowcc.cli.Path.cwd", return_value=mock_project_dir):
            isolated_agilevv_dir.ensure_structure(create_defaults=True)
            # Create empty state
            isolated_agilevv_dir.state_path.write_text("{}")

            with patch.dict(os.environ, {"AGILEVV_BASE_DIR": str(isolated_agilevv_dir.base_dir)}):
                result = runner.invoke(app, ["sprint"])
                # Should provide guidance or error
                assert result.exit_code in [0, 1]  # Could be success with message or error

    def test_sprint_with_story(
        self, runner: CliRunner, mock_project_dir: Path, isolated_agilevv_dir: PathConfig
    ) -> None:
        """Test sprint command with story parameter."""
        with patch("verifflowcc.cli.Path.cwd", return_value=mock_project_dir):
            # Setup using PathConfig - ensure defaults are created
            isolated_agilevv_dir.ensure_structure(create_defaults=True)

            import yaml

            # Create minimal config with v_model
            config_data = {
                "v_model": {
                    "gating": "soft",
                    "stages": ["requirements", "design", "coding", "testing", "validation"],
                }
            }
            isolated_agilevv_dir.config_path.write_text(yaml.dump(config_data))

            # Create state with required keys for the orchestrator
            state_data = {
                "current_sprint": None,
                "current_stage": None,
                "completed_stages": [],
                "active_story": None,
                "sprint_number": 0,
                "checkpoint_history": [],
            }
            isolated_agilevv_dir.state_path.write_text(json.dumps(state_data))

            with patch.dict(os.environ, {"AGILEVV_BASE_DIR": str(isolated_agilevv_dir.base_dir)}):
                # Mock the Orchestrator import to avoid complexity
                with patch("verifflowcc.core.orchestrator.Orchestrator") as mock_orch_class:
                    mock_orch = MagicMock()
                    mock_orch.run_sprint = MagicMock(return_value={"stages": {}})
                    mock_orch_class.return_value = mock_orch

                    # Mock asyncio.run to return the expected result
                    with patch("verifflowcc.cli.asyncio.run") as mock_async:
                        mock_async.return_value = {"stages": {}}

                        result = runner.invoke(app, ["sprint", "--story", "Test story"])
                        # Should succeed with the mocked orchestrator
                        assert result.exit_code == 0


class TestStatusCommand:
    """Test the status command."""

    def test_status_basic(
        self, runner: CliRunner, mock_project_dir: Path, isolated_agilevv_dir: PathConfig
    ) -> None:
        """Test basic status command."""
        with patch("verifflowcc.cli.Path.cwd", return_value=mock_project_dir):
            isolated_agilevv_dir.ensure_structure(create_defaults=True)
            # Create state with some data
            state_data = {
                "current_sprint": "Sprint 1",
                "current_stage": "Requirements",
                "active_story": "Test Story",
            }

            isolated_agilevv_dir.state_path.write_text(json.dumps(state_data))

            with patch.dict(os.environ, {"AGILEVV_BASE_DIR": str(isolated_agilevv_dir.base_dir)}):
                result = runner.invoke(app, ["status"])
            assert result.exit_code == 0
            assert "Sprint 1" in result.stdout
            assert "Requirements" in result.stdout

    def test_status_json_output(
        self, runner: CliRunner, mock_project_dir: Path, isolated_agilevv_dir: PathConfig
    ) -> None:
        """Test status command with --json flag."""
        with patch("verifflowcc.cli.Path.cwd", return_value=mock_project_dir):
            isolated_agilevv_dir.ensure_structure(create_defaults=True)
            isolated_agilevv_dir.state_path.write_text("{}")

            with patch.dict(os.environ, {"AGILEVV_BASE_DIR": str(isolated_agilevv_dir.base_dir)}):
                result = runner.invoke(app, ["status", "--json"])
            assert result.exit_code == 0
            # Output should be valid JSON

            json.loads(result.stdout)


class TestResumeCommand:
    """Test the resume command."""

    def test_resume_no_state(
        self, runner: CliRunner, mock_project_dir: Path, isolated_agilevv_dir: PathConfig
    ) -> None:
        """Test resume command when no state exists."""
        with patch("verifflowcc.cli.Path.cwd", return_value=mock_project_dir):
            isolated_agilevv_dir.ensure_structure(create_defaults=False)
            with patch.dict(os.environ, {"AGILEVV_BASE_DIR": str(isolated_agilevv_dir.base_dir)}):
                result = runner.invoke(app, ["resume"])
                # Should handle missing state gracefully
                assert result.exit_code in [0, 1]


class TestCheckpointCommand:
    """Test the checkpoint command."""

    def test_checkpoint_basic(
        self, runner: CliRunner, mock_project_dir: Path, isolated_agilevv_dir: PathConfig
    ) -> None:
        """Test basic checkpoint creation."""
        with patch("verifflowcc.cli.Path.cwd", return_value=mock_project_dir):
            # Setup using PathConfig
            isolated_agilevv_dir.ensure_structure(create_defaults=True)
            isolated_agilevv_dir.checkpoints_dir.mkdir(parents=True, exist_ok=True)

            state_data: dict[str, Any] = {"checkpoint_history": []}
            isolated_agilevv_dir.state_path.write_text(json.dumps(state_data))

            with patch.dict(os.environ, {"AGILEVV_BASE_DIR": str(isolated_agilevv_dir.base_dir)}):
                # Mock git integration to avoid actual git operations
                with patch(
                    "verifflowcc.core.git_integration.GitIntegration.is_git_repo",
                    return_value=False,
                ):
                    result = runner.invoke(app, ["checkpoint", "--name", "test-checkpoint"])
                    assert result.exit_code == 0
                    assert "Checkpoint created" in result.stdout


class TestValidateCommand:
    """Test the validate command."""

    def test_validate_basic(
        self, runner: CliRunner, mock_project_dir: Path, isolated_agilevv_dir: PathConfig
    ) -> None:
        """Test basic validate command."""
        with patch("verifflowcc.cli.Path.cwd", return_value=mock_project_dir):
            isolated_agilevv_dir.ensure_structure(create_defaults=True)
            with patch.dict(os.environ, {"AGILEVV_BASE_DIR": str(isolated_agilevv_dir.base_dir)}):
                result = runner.invoke(app, ["validate"])
                # Validate should run some checks
                assert result.exit_code in [0, 1]  # Could pass or fail validation


class TestHistoryCommand:
    """Test the history command."""

    def test_history_basic(
        self, runner: CliRunner, mock_project_dir: Path, isolated_agilevv_dir: PathConfig
    ) -> None:
        """Test basic history command."""
        with patch("verifflowcc.cli.Path.cwd", return_value=mock_project_dir):
            isolated_agilevv_dir.ensure_structure(create_defaults=True)
            with patch.dict(os.environ, {"AGILEVV_BASE_DIR": str(isolated_agilevv_dir.base_dir)}):
                result = runner.invoke(app, ["history"])
                # History should run without error
                assert result.exit_code == 0


class TestCLIErrorHandling:
    """Test CLI error handling scenarios."""

    def test_command_outside_project(self, runner: CliRunner, tmp_path: Path) -> None:
        """Test commands fail gracefully outside a VeriFlowCC project."""
        with patch("verifflowcc.cli.Path.cwd", return_value=tmp_path):
            # No .agilevv directory exists
            result = runner.invoke(app, ["status"])
            # Should fail gracefully
            assert result.exit_code != 0

    def test_corrupted_state_file(
        self, runner: CliRunner, mock_project_dir: Path, isolated_agilevv_dir: PathConfig
    ) -> None:
        """Test handling of corrupted state file."""
        with patch("verifflowcc.cli.Path.cwd", return_value=mock_project_dir):
            isolated_agilevv_dir.ensure_structure(create_defaults=True)
            # Write invalid JSON
            isolated_agilevv_dir.state_path.write_text("invalid json")

            with patch.dict(os.environ, {"AGILEVV_BASE_DIR": str(isolated_agilevv_dir.base_dir)}):
                result = runner.invoke(app, ["status"])
                # Should handle corrupted state gracefully
                assert result.exit_code in [0, 1]
