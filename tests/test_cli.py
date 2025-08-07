"""Tests for VeriFlowCC CLI."""

from pathlib import Path
from unittest.mock import patch

from typer.testing import CliRunner
from verifflowcc import __version__
from verifflowcc.cli import app

runner = CliRunner()


def test_version_command():
    """Test version command shows correct version."""
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert __version__ in result.stdout
    assert "AI-driven V-Model development pipeline" in result.stdout
    assert "Claude Opus 4.1 and Sonnet 4" in result.stdout


def test_init_command_default():
    """Test init command with default options."""
    with patch("verifflowcc.cli.Progress") as mock_progress:
        result = runner.invoke(app, ["init"])
        assert result.exit_code == 0
        assert "Initializing VeriFlowCC Project" in result.stdout
        assert f"Version: {__version__}" in result.stdout
        assert "Project initialized successfully!" in result.stdout
        assert str(Path.cwd()) in result.stdout


def test_init_command_with_options():
    """Test init command with custom options."""
    test_dir = Path("/tmp/test_project")
    test_config = Path("/tmp/config.yaml")

    with patch("verifflowcc.cli.Progress") as mock_progress:
        result = runner.invoke(
            app, ["init", "--dir", str(test_dir), "--config", str(test_config), "--force"]
        )
        assert result.exit_code == 0
        assert str(test_dir) in result.stdout
        assert str(test_config) in result.stdout


def test_plan_command():
    """Test plan command."""
    with patch("verifflowcc.cli.Progress") as mock_progress:
        with patch("verifflowcc.cli.typer.confirm", return_value=False):
            result = runner.invoke(app, ["plan", "User authentication feature", "--no-interactive"])
            assert result.exit_code == 0
            assert "Planning Feature" in result.stdout
            assert "User authentication feature" in result.stdout
            assert "Plan created successfully!" in result.stdout


def test_plan_command_with_output():
    """Test plan command with output file."""
    output_file = Path("/tmp/plan.yaml")

    with patch("verifflowcc.cli.Progress") as mock_progress:
        result = runner.invoke(
            app, ["plan", "API endpoints", "--output", str(output_file), "--no-interactive"]
        )
        assert result.exit_code == 0
        assert str(output_file) in result.stdout


def test_execute_command_file_not_found():
    """Test execute command with non-existent plan file."""
    result = runner.invoke(app, ["execute", "/tmp/nonexistent.yaml"])
    assert result.exit_code == 1
    assert "Error:" in result.stdout
    assert "Plan file not found" in result.stdout


def test_execute_command_with_plan():
    """Test execute command with existing plan file."""
    plan_file = Path("/tmp/test_plan.yaml")

    with patch("pathlib.Path.exists", return_value=True):
        with patch("verifflowcc.cli.Progress") as mock_progress:
            result = runner.invoke(app, ["execute", str(plan_file), "--dry-run"])
            assert result.exit_code == 0
            assert "Executing Plan" in result.stdout
            assert "test_plan.yaml" in result.stdout
            assert "Execution completed successfully!" in result.stdout


def test_execute_command_specific_stage():
    """Test execute command with specific stage."""
    plan_file = Path("/tmp/test_plan.yaml")

    with patch("pathlib.Path.exists", return_value=True):
        with patch("verifflowcc.cli.Progress") as mock_progress:
            result = runner.invoke(
                app, ["execute", str(plan_file), "--stage", "testing", "--dry-run"]
            )
            assert result.exit_code == 0
            assert "Would execute: testing" in result.stdout


def test_status_command():
    """Test status command."""
    result = runner.invoke(app, ["status"])
    assert result.exit_code == 0
    assert "VeriFlowCC Status" in result.stdout
    assert "Active Plans" in result.stdout
    # Check for table headers
    assert "Plan ID" in result.stdout
    assert "Feature" in result.stdout
    assert "Stage" in result.stdout
    assert "Status" in result.stdout


def test_status_command_verbose():
    """Test status command with verbose flag."""
    result = runner.invoke(app, ["status", "--verbose"])
    assert result.exit_code == 0
    assert "Recent Activities:" in result.stdout
    assert "Plan created:" in result.stdout
    assert "Last checkpoint:" in result.stdout


def test_rollback_command_cancelled():
    """Test rollback command when user cancels."""
    with patch("verifflowcc.cli.typer.confirm", return_value=False):
        result = runner.invoke(app, ["rollback", "2"])
        assert result.exit_code == 0
        assert "Rollback cancelled" in result.stdout


def test_rollback_command_confirmed():
    """Test rollback command when user confirms."""
    with patch("verifflowcc.cli.typer.confirm", return_value=True):
        result = runner.invoke(app, ["rollback", "1"])
        assert result.exit_code == 0
        assert "Rolling Back 1 Checkpoint(s)" in result.stdout
        assert "Rolled back 1 checkpoint(s)" in result.stdout


def test_rollback_command_force():
    """Test rollback command with force flag."""
    result = runner.invoke(app, ["rollback", "3", "--force"])
    assert result.exit_code == 0
    assert "Rolling Back 3 Checkpoint(s)" in result.stdout
    assert "Rolled back 3 checkpoint(s)" in result.stdout
    # Should not ask for confirmation
    assert "Are you sure" not in result.stdout


def test_validate_command():
    """Test validate command."""
    with patch("verifflowcc.cli.Progress") as mock_progress:
        result = runner.invoke(app, ["validate", "User API"])
        assert result.exit_code == 0
        assert "Running Validation" in result.stdout
        assert "Validation passed!" in result.stdout
        assert "All acceptance criteria met" in result.stdout
        assert "Test coverage:" in result.stdout
        assert "Code quality:" in result.stdout


def test_validate_command_with_plan():
    """Test validate command with plan file."""
    plan_file = Path("/tmp/plan.yaml")

    with patch("verifflowcc.cli.Progress") as mock_progress:
        result = runner.invoke(app, ["validate", "--plan", str(plan_file)])
        assert result.exit_code == 0
        assert "Running Validation" in result.stdout


def test_main_keyboard_interrupt():
    """Test main function handles keyboard interrupt."""
    with patch("verifflowcc.cli.app", side_effect=KeyboardInterrupt):
        from verifflowcc.cli import main

        exit_code = main()
        assert exit_code == 130


def test_main_general_exception():
    """Test main function handles general exceptions."""
    with patch("verifflowcc.cli.app", side_effect=Exception("Test error")):
        with patch.dict("os.environ", {"DEBUG": "false"}):
            from verifflowcc.cli import main

            exit_code = main()
            assert exit_code == 1


def test_main_success():
    """Test main function successful execution."""
    with patch("verifflowcc.cli.app"):
        from verifflowcc.cli import main

        exit_code = main()
        assert exit_code == 0
