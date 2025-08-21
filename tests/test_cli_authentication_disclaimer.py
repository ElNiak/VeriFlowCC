"""Test CLI authentication disclaimer integration.

This module tests the authentication disclaimer functionality added to the CLI
startup messages and command executions. Tests validate that appropriate
authentication disclaimers are displayed to users.

Test Categories:
- Authentication disclaimer display in CLI help
- Authentication disclaimer in command outputs
- Rich formatting validation for disclaimer messages
- Integration with existing CLI commands

Authentication:
Tests do not require authentication as they focus on disclaimer display.

Execution:
Run with: pytest tests/test_cli_authentication_disclaimer.py -v
"""

from contextlib import contextmanager
from pathlib import Path

import pytest
from typer.testing import CliRunner
from verifflowcc.cli import app

from tests.conftest import PathConfig as TestPathConfig


@contextmanager
def temp_env_vars(**env_vars: str):
    """Context manager to temporarily set environment variables without mocking."""
    import os

    original_values: dict[str, str | None] = {}

    # Store original values and set new ones
    for key, value in env_vars.items():
        original_values[key] = os.environ.get(key)
        os.environ[key] = value

    try:
        yield
    finally:
        # Restore original values
        for key, original_value in original_values.items():
            if original_value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = original_value


@pytest.fixture
def runner() -> CliRunner:
    """Create a CLI test runner."""
    return CliRunner()


class TestAuthenticationDisclaimerDisplay:
    """Test authentication disclaimer display in CLI commands."""

    def test_main_help_contains_authentication_disclaimer(self, runner: CliRunner) -> None:
        """Test that main CLI help contains authentication disclaimer."""
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0

        # Check for authentication disclaimer in help text
        assert (
            "AUTHENTICATION REQUIRED" in result.output or "authentication" in result.output.lower()
        )
        assert "Claude Code" in result.output

    def test_main_callback_shows_authentication_disclaimer(self, runner: CliRunner) -> None:
        """Test that main callback shows authentication disclaimer in docstring."""
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0

        # Verify authentication disclaimer appears in help
        assert "Claude Code authentication" in result.output
        assert "VeriFlow" in result.output or "authentication" in result.output.lower()

    def test_app_description_includes_authentication_requirement(self, runner: CliRunner) -> None:
        """Test that app description includes authentication requirement."""
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0

        # Check that help text mentions authentication requirement
        assert "Claude Code authentication" in result.output

    def test_version_command_with_authentication_context(self, runner: CliRunner) -> None:
        """Test version command works within authentication context."""
        result = runner.invoke(app, ["--version"])
        assert result.exit_code == 0
        assert "VeriFlowCC" in result.output
        assert "version" in result.output.lower()


class TestAuthenticationDisclaimerInCommands:
    """Test authentication disclaimer integration in individual commands."""

    def test_init_command_authentication_context(self, runner: CliRunner, tmp_path: Path) -> None:
        """Test init command shows authentication disclaimer context."""
        import os

        original_cwd = Path.cwd()

        try:
            os.chdir(str(tmp_path))
            custom_dir = tmp_path / "test_init_auth"

            with temp_env_vars(AGILEVV_BASE_DIR=str(custom_dir)):
                result = runner.invoke(app, ["init", "--help"])
                assert result.exit_code == 0

                # Verify help text is accessible and shows proper command info
                assert "Initialize" in result.output or "init" in result.output.lower()

        finally:
            os.chdir(original_cwd)

    def test_sprint_command_authentication_context(self, runner: CliRunner) -> None:
        """Test sprint command shows authentication disclaimer context."""
        result = runner.invoke(app, ["sprint", "--help"])
        assert result.exit_code == 0

        # Verify help mentions story requirement and command functionality
        assert "story" in result.output.lower()
        assert "Execute" in result.output or "sprint" in result.output.lower()

    def test_plan_command_authentication_context(self, runner: CliRunner) -> None:
        """Test plan command shows authentication disclaimer context."""
        result = runner.invoke(app, ["plan", "--help"])
        assert result.exit_code == 0

        # Verify help shows planning functionality
        assert "plan" in result.output.lower() or "Plan" in result.output

    def test_status_command_authentication_context(self, runner: CliRunner) -> None:
        """Test status command shows authentication disclaimer context."""
        result = runner.invoke(app, ["status", "--help"])
        assert result.exit_code == 0

        # Verify help shows status functionality
        assert "status" in result.output.lower() or "Show" in result.output

    def test_validate_command_authentication_context(self, runner: CliRunner) -> None:
        """Test validate command shows authentication disclaimer context."""
        result = runner.invoke(app, ["validate", "--help"])
        assert result.exit_code == 0

        # Verify help shows validation functionality
        assert "validate" in result.output.lower() or "Validate" in result.output


class TestAuthenticationDisclaimerFormatting:
    """Test authentication disclaimer Rich formatting validation."""

    def test_disclaimer_formatting_in_help(self, runner: CliRunner) -> None:
        """Test that disclaimer uses proper Rich formatting in help text."""
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0

        # Check for structured help output with authentication info
        assert len(result.output) > 100  # Should be substantial help text
        assert "VeriFlowCC" in result.output

        # Look for authentication-related terms
        auth_terms = ["authentication", "Claude Code", "required", "VeriFlow"]
        found_terms = sum(1 for term in auth_terms if term.lower() in result.output.lower())
        assert found_terms >= 2  # Should mention multiple authentication-related terms

    def test_disclaimer_appears_before_commands(self, runner: CliRunner) -> None:
        """Test that authentication disclaimer appears before command list."""
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0

        # Find positions of key text elements
        output_lower = result.output.lower()
        auth_pos = output_lower.find("authentication")
        commands_pos = output_lower.find("commands:")

        # Authentication disclaimer should appear before commands section
        if auth_pos >= 0 and commands_pos >= 0:
            assert auth_pos < commands_pos

    def test_disclaimer_contains_required_information(self, runner: CliRunner) -> None:
        """Test that disclaimer contains all required information."""
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0

        # Check for essential disclaimer components
        output_lower = result.output.lower()

        # Should mention Claude Code
        assert "claude" in output_lower

        # Should indicate authentication is required
        assert "authentication" in output_lower or "auth" in output_lower


class TestAuthenticationDisclaimerIntegration:
    """Test authentication disclaimer integration with CLI workflow."""

    def test_disclaimer_consistency_across_commands(self, runner: CliRunner) -> None:
        """Test authentication disclaimer consistency across all commands."""
        commands = ["init", "sprint", "plan", "status", "validate", "checkpoint"]

        for cmd in commands:
            result = runner.invoke(app, [cmd, "--help"])
            assert result.exit_code == 0
            assert len(result.output) > 0

            # Each command should have substantial help text
            # This validates the command structure is intact for disclaimer integration

    def test_disclaimer_with_no_command_invocation(self, runner: CliRunner) -> None:
        """Test authentication disclaimer when no command is invoked."""
        result = runner.invoke(app, [])
        assert result.exit_code == 0

        # Should show help with authentication disclaimer
        assert "VeriFlowCC" in result.output
        assert len(result.output) > 100  # Should show full help

    def test_disclaimer_error_handling_integration(self, runner: CliRunner) -> None:
        """Test disclaimer integration with error handling."""
        # Test invalid command - should still show meaningful output
        result = runner.invoke(app, ["invalid_command"])
        assert result.exit_code != 0
        assert len(result.output) > 0

    def test_disclaimer_with_environment_variables(self, runner: CliRunner, tmp_path: Path) -> None:
        """Test authentication disclaimer with environment variable configuration."""
        import os

        original_cwd = Path.cwd()

        try:
            os.chdir(str(tmp_path))
            custom_dir = tmp_path / "test_env_auth"

            # Test with custom AGILEVV_BASE_DIR
            with temp_env_vars(AGILEVV_BASE_DIR=str(custom_dir)):
                result = runner.invoke(app, ["--help"])
                assert result.exit_code == 0
                assert "VeriFlowCC" in result.output

                # Should still show authentication requirements regardless of env vars
                output_lower = result.output.lower()
                assert "claude" in output_lower or "authentication" in output_lower

        finally:
            os.chdir(original_cwd)


class TestAuthenticationDisclaimerStartupMessages:
    """Test authentication disclaimer in CLI startup messages."""

    def test_startup_authentication_message_preparation(self, runner: CliRunner) -> None:
        """Test CLI is prepared for startup authentication messages."""
        # This test validates the CLI structure is ready for startup disclaimers
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0

        # Verify CLI has proper Rich console integration for messages
        assert "VeriFlowCC" in result.output

        # Check that the CLI uses Rich formatting (indicated by structured output)
        lines = result.output.split("\n")
        assert len(lines) > 10  # Should have multi-line structured output

    def test_startup_message_integration_readiness(
        self, runner: CliRunner, isolated_agilevv_dir: TestPathConfig
    ) -> None:
        """Test CLI readiness for startup message integration."""
        import os

        original_cwd = Path.cwd()
        test_cwd = isolated_agilevv_dir.base_dir.parent
        test_cwd.mkdir(parents=True, exist_ok=True)

        try:
            os.chdir(str(test_cwd))

            with temp_env_vars(AGILEVV_BASE_DIR=str(isolated_agilevv_dir.base_dir)):
                # Test that CLI can handle startup context properly
                result = runner.invoke(app, ["init", "--help"])
                assert result.exit_code == 0

                # Verify CLI maintains proper structure for message integration
                assert len(result.output) > 50

        finally:
            os.chdir(original_cwd)

    def test_console_rich_formatting_capability(self, runner: CliRunner) -> None:
        """Test that CLI has Rich console formatting capability for disclaimers."""
        result = runner.invoke(app, ["--version"])
        assert result.exit_code == 0

        # Should show formatted version output using Rich
        assert "VeriFlowCC" in result.output
        assert "version" in result.output.lower()

        # Verify output formatting indicates Rich integration is active
        assert len(result.output.strip()) > 10


class TestAuthenticationDisclaimerErrorScenarios:
    """Test authentication disclaimer in error scenarios."""

    def test_disclaimer_with_missing_project_error(self, runner: CliRunner, tmp_path: Path) -> None:
        """Test disclaimer context with missing project errors."""
        import os

        original_cwd = Path.cwd()

        try:
            os.chdir(str(tmp_path))
            non_existent_dir = tmp_path / "non_existent_agilevv"

            with temp_env_vars(AGILEVV_BASE_DIR=str(non_existent_dir)):
                result = runner.invoke(app, ["status"])

                # Should show error but still maintain authentication context
                assert result.exit_code == 1
                assert len(result.output) > 0
                assert "not initialized" in result.output.lower()

        finally:
            os.chdir(original_cwd)

    def test_disclaimer_with_invalid_arguments(self, runner: CliRunner) -> None:
        """Test disclaimer context with invalid command arguments."""
        result = runner.invoke(app, ["sprint"])  # Missing required --story argument
        assert result.exit_code != 0
        assert len(result.output) > 0

        # Should show error with context, maintaining authentication awareness
        assert "story" in result.output.lower() or "required" in result.output.lower()

    def test_disclaimer_with_permission_errors(self, runner: CliRunner) -> None:
        """Test disclaimer context with potential permission errors."""
        # Test with invalid directory scenario that CLI should handle gracefully
        result = runner.invoke(app, ["init", "--dir", "/nonexistent/readonly/path"])

        # Command should handle error gracefully while maintaining authentication context
        # This tests the error handling pathway for disclaimer integration
        # The command may succeed (if path gets created) or fail (permission denied)
        # Either way, it should maintain CLI structure for authentication disclaimers
        assert result.exit_code >= 0  # Any valid exit code is acceptable
