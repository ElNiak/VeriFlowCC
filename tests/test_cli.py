"""Tests for the VeriFlowCC CLI application."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner
from verifflowcc.cli import app


@pytest.fixture
def runner() -> CliRunner:
    """Create a CLI test runner."""
    return CliRunner()


@pytest.fixture
def mock_project_dir(tmp_path: Path) -> Path:
    """Create a temporary project directory for testing."""
    return tmp_path


class TestCLIStructure:
    """Test CLI application structure and command registration."""

    def test_app_exists(self) -> None:
        """Test that the Typer app is properly initialized."""
        assert app is not None
        assert hasattr(app, "command")

    def test_all_commands_registered(self, runner: CliRunner) -> None:
        """Test that all required commands are registered."""
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0

        # Check for all required commands in help output
        required_commands = ["init", "plan", "sprint", "status", "validate", "checkpoint"]
        for command in required_commands:
            assert command in result.stdout

    def test_rich_console_initialized(self) -> None:
        """Test that Rich console is properly initialized."""
        from verifflowcc.cli import console

        assert console is not None
        assert hasattr(console, "print")
        assert hasattr(console, "status")


class TestInitCommand:
    """Test the init command."""

    def test_init_command_exists(self, runner: CliRunner) -> None:
        """Test that init command is registered."""
        result = runner.invoke(app, ["init", "--help"])
        assert result.exit_code == 0
        assert "Initialize a new VeriFlowCC project" in result.stdout

    def test_init_creates_directory_structure(
        self, runner: CliRunner, mock_project_dir: Path
    ) -> None:
        """Test that init creates the required directory structure."""
        with patch("verifflowcc.cli.Path.cwd", return_value=mock_project_dir):
            result = runner.invoke(app, ["init"])
            assert result.exit_code == 0

            # Check that .agilevv directory was created
            agilevv_dir = mock_project_dir / ".agilevv"
            assert agilevv_dir.exists()
            assert (agilevv_dir / "config.yaml").exists()
            assert (agilevv_dir / "state.json").exists()

    def test_init_force_flag(self, runner: CliRunner, mock_project_dir: Path) -> None:
        """Test init with --force flag for reinitializing."""
        with patch("verifflowcc.cli.Path.cwd", return_value=mock_project_dir):
            # First initialization
            result = runner.invoke(app, ["init"])
            assert result.exit_code == 0

            # Try to reinitialize without force (should fail)
            result = runner.invoke(app, ["init"])
            assert result.exit_code == 1
            assert "already initialized" in result.stdout.lower()

            # Reinitialize with force (should succeed)
            result = runner.invoke(app, ["init", "--force"])
            assert result.exit_code == 0


class TestPlanCommand:
    """Test the plan command."""

    def test_plan_command_exists(self, runner: CliRunner) -> None:
        """Test that plan command is registered."""
        result = runner.invoke(app, ["plan", "--help"])
        assert result.exit_code == 0
        assert "Plan a new sprint" in result.stdout

    @patch("verifflowcc.cli.load_backlog")
    def test_plan_reads_backlog(
        self, mock_load_backlog: MagicMock, runner: CliRunner, mock_project_dir: Path
    ) -> None:
        """Test that plan command reads from backlog."""
        mock_load_backlog.return_value = ["Story 1", "Story 2"]

        with patch("verifflowcc.cli.Path.cwd", return_value=mock_project_dir):
            # Create .agilevv directory first
            (mock_project_dir / ".agilevv").mkdir()
            (mock_project_dir / ".agilevv" / "backlog.md").write_text("# Backlog")

            result = runner.invoke(app, ["plan", "--story-id", "1"])
            assert result.exit_code == 0
            mock_load_backlog.assert_called_once()


class TestSprintCommand:
    """Test the sprint command."""

    def test_sprint_command_exists(self, runner: CliRunner) -> None:
        """Test that sprint command is registered."""
        result = runner.invoke(app, ["sprint", "--help"])
        assert result.exit_code == 0
        assert "Execute a sprint" in result.stdout

    def test_sprint_requires_story(self, runner: CliRunner) -> None:
        """Test that sprint command requires --story parameter."""
        result = runner.invoke(app, ["sprint"])
        assert result.exit_code == 2  # Missing required option
        assert "--story" in result.stdout

    @patch("verifflowcc.cli.Orchestrator")
    def test_sprint_with_story(
        self, mock_orchestrator: MagicMock, runner: CliRunner, mock_project_dir: Path
    ) -> None:
        """Test sprint command with story parameter."""
        with patch("verifflowcc.cli.Path.cwd", return_value=mock_project_dir):
            # Setup mock project
            (mock_project_dir / ".agilevv").mkdir()
            (mock_project_dir / ".agilevv" / "state.json").write_text("{}")

            result = runner.invoke(app, ["sprint", "--story", "Test story"])
            assert result.exit_code == 0
            mock_orchestrator.assert_called_once()


class TestStatusCommand:
    """Test the status command."""

    def test_status_command_exists(self, runner: CliRunner) -> None:
        """Test that status command is registered."""
        result = runner.invoke(app, ["status", "--help"])
        assert result.exit_code == 0
        assert "Show project status" in result.stdout

    def test_status_displays_state(self, runner: CliRunner, mock_project_dir: Path) -> None:
        """Test that status command displays current state."""
        with patch("verifflowcc.cli.Path.cwd", return_value=mock_project_dir):
            # Setup mock state
            (mock_project_dir / ".agilevv").mkdir()
            state_data = {
                "current_sprint": "Sprint 1",
                "current_stage": "Requirements",
                "active_story": "Test Story",
            }
            import json

            (mock_project_dir / ".agilevv" / "state.json").write_text(json.dumps(state_data))

            result = runner.invoke(app, ["status"])
            assert result.exit_code == 0
            assert "Sprint 1" in result.stdout
            assert "Requirements" in result.stdout

    def test_status_json_output(self, runner: CliRunner, mock_project_dir: Path) -> None:
        """Test status command with --json flag."""
        with patch("verifflowcc.cli.Path.cwd", return_value=mock_project_dir):
            (mock_project_dir / ".agilevv").mkdir()
            (mock_project_dir / ".agilevv" / "state.json").write_text("{}")

            result = runner.invoke(app, ["status", "--json"])
            assert result.exit_code == 0
            # Output should be valid JSON
            import json

            json.loads(result.stdout)


class TestValidateCommand:
    """Test the validate command."""

    def test_validate_command_exists(self, runner: CliRunner) -> None:
        """Test that validate command is registered."""
        result = runner.invoke(app, ["validate", "--help"])
        assert result.exit_code == 0
        assert "Validate the current sprint" in result.stdout

    @patch("verifflowcc.cli.run_validation")
    def test_validate_runs_checks(
        self, mock_validation: MagicMock, runner: CliRunner, mock_project_dir: Path
    ) -> None:
        """Test that validate command runs validation checks."""
        mock_validation.return_value = {"passed": True, "tests": 10, "failures": 0}

        with patch("verifflowcc.cli.Path.cwd", return_value=mock_project_dir):
            (mock_project_dir / ".agilevv").mkdir()
            (mock_project_dir / ".agilevv" / "state.json").write_text("{}")

            result = runner.invoke(app, ["validate"])
            assert result.exit_code == 0
            mock_validation.assert_called_once()


class TestCheckpointCommand:
    """Test the checkpoint command."""

    def test_checkpoint_command_exists(self, runner: CliRunner) -> None:
        """Test that checkpoint command is registered."""
        result = runner.invoke(app, ["checkpoint", "--help"])
        assert result.exit_code == 0
        assert "Create or manage checkpoints" in result.stdout

    @patch("verifflowcc.cli.git.Repo")
    def test_checkpoint_create(
        self, mock_repo: MagicMock, runner: CliRunner, mock_project_dir: Path
    ) -> None:
        """Test creating a checkpoint."""
        with patch("verifflowcc.cli.Path.cwd", return_value=mock_project_dir):
            (mock_project_dir / ".agilevv").mkdir()

            result = runner.invoke(app, ["checkpoint", "--name", "test-checkpoint"])
            assert result.exit_code == 0
            assert "Checkpoint created" in result.stdout

    def test_checkpoint_list_subcommand(self, runner: CliRunner) -> None:
        """Test checkpoint list subcommand."""
        result = runner.invoke(app, ["checkpoint", "list", "--help"])
        assert result.exit_code == 0
        assert "List available checkpoints" in result.stdout

    def test_checkpoint_restore_subcommand(self, runner: CliRunner) -> None:
        """Test checkpoint restore subcommand."""
        result = runner.invoke(app, ["checkpoint", "restore", "--help"])
        assert result.exit_code == 0
        assert "Restore to a checkpoint" in result.stdout


class TestErrorHandling:
    """Test error handling and exit codes."""

    def test_proper_exit_codes(self, runner: CliRunner) -> None:
        """Test that commands return proper exit codes."""
        # Success case
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0

        # Invalid command
        result = runner.invoke(app, ["invalid-command"])
        assert result.exit_code == 2

        # Missing required option
        result = runner.invoke(app, ["sprint"])
        assert result.exit_code == 2

    def test_keyboard_interrupt_handling(self, runner: CliRunner, mock_project_dir: Path) -> None:
        """Test graceful handling of keyboard interrupts."""
        with patch("verifflowcc.cli.Path.cwd", return_value=mock_project_dir):
            with patch("verifflowcc.cli.Orchestrator") as mock_orch:
                mock_orch.side_effect = KeyboardInterrupt()

                result = runner.invoke(app, ["sprint", "--story", "Test"])
                assert result.exit_code == 130  # Standard exit code for SIGINT
                assert "Interrupted" in result.stdout or "Cancelled" in result.stdout


class TestHelpDocumentation:
    """Test help documentation for all commands."""

    def test_main_help(self, runner: CliRunner) -> None:
        """Test main application help."""
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "VeriFlowCC" in result.stdout
        assert "Agile V-Model" in result.stdout

    def test_all_commands_have_help(self, runner: CliRunner) -> None:
        """Test that all commands have help documentation."""
        commands = ["init", "plan", "sprint", "status", "validate", "checkpoint"]

        for command in commands:
            result = runner.invoke(app, [command, "--help"])
            assert result.exit_code == 0
            assert command in result.stdout.lower()
            # Each command should have a description
            assert len(result.stdout.strip()) > 50
