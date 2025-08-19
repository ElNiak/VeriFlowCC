"""Integration tests for VeriFlowCC end-to-end workflows."""

import json
import logging
import os
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml
from typer.testing import CliRunner
from verifflowcc.cli import app

# Configure logging for tests
logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@pytest.fixture
def runner() -> CliRunner:
    """Create a CLI test runner."""
    logger.debug("Creating CLI test runner")
    return CliRunner()


@pytest.fixture
def temp_project_dir(tmp_path: Path) -> Path:
    """Create a temporary project directory for testing."""
    logger.debug(f"Creating temporary project directory at: {tmp_path}")
    return tmp_path


@pytest.fixture
def initialized_project(temp_project_dir: Path, runner: CliRunner) -> Path:
    """Create and initialize a project for testing."""
    logger.info(f"Initializing project in: {temp_project_dir}")

    # Set up mock environment for SDK
    mock_env = {"ANTHROPIC_API_KEY": "sk-test-mock-key-12345"}

    with (
        patch.dict(os.environ, mock_env),
        patch("verifflowcc.core.orchestrator.Orchestrator"),
        patch("verifflowcc.cli.Path.cwd", return_value=temp_project_dir),
    ):
        logger.debug("Invoking 'init' command")
        result = runner.invoke(app, ["init"])
        logger.debug(
            f"Init command result: exit_code={result.exit_code}, stdout={result.stdout[:100]}..."
        )
        assert result.exit_code == 0
    logger.info("Project initialized successfully")
    return temp_project_dir


class TestEndToEndWorkflow:
    """Test complete VeriFlowCC workflow from init to validate."""

    def test_complete_workflow(self, runner: CliRunner, temp_project_dir: Path) -> None:
        """Test the complete workflow: init -> plan -> sprint -> status -> validate."""
        logger.info("Starting complete workflow test")

        # Set up mock environment for SDK
        mock_env = {"ANTHROPIC_API_KEY": "sk-test-mock-key-12345"}

        with (
            patch.dict(os.environ, mock_env),
            patch("verifflowcc.core.orchestrator.Orchestrator"),
            patch("verifflowcc.cli.Path.cwd", return_value=temp_project_dir),
        ):
            # Step 1: Initialize project
            logger.info("Step 1: Initializing project")
            result = runner.invoke(app, ["init"])
            logger.debug(f"Init result: exit_code={result.exit_code}, stdout={result.stdout}")
            assert result.exit_code == 0
            assert "Project initialized successfully" in result.stdout

            # Verify project structure
            logger.info("Verifying project structure")
            agilevv_dir = temp_project_dir / ".agilevv"
            logger.debug(f"Checking existence of .agilevv directory: {agilevv_dir}")
            assert agilevv_dir.exists()

            files_to_check = [
                "config.yaml",
                "state.json",
                "backlog.md",
                "architecture.md",
            ]
            for file_name in files_to_check:
                file_path = agilevv_dir / file_name
                logger.debug(f"Checking existence of {file_name}: {file_path.exists()}")
                assert file_path.exists()

            # Step 2: Plan sprint with story selection
            logger.info("Step 2: Planning sprint")
            result = runner.invoke(app, ["plan", "--story-id", "1"])
            logger.debug(f"Plan result: exit_code={result.exit_code}, stdout={result.stdout}")
            assert result.exit_code == 0
            assert "Story selected" in result.stdout or "Sprint Planning Complete" in result.stdout

            # Step 3: Execute sprint
            logger.info("Step 3: Executing sprint")
            with patch("verifflowcc.cli.asyncio.run"):
                result = runner.invoke(app, ["sprint", "--story", "Test story"])
                logger.debug(f"Sprint result: exit_code={result.exit_code}, stdout={result.stdout}")
                assert result.exit_code == 0
                assert "Sprint" in result.stdout

            # Step 4: Check status
            logger.info("Step 4: Checking status")
            result = runner.invoke(app, ["status"])
            logger.debug(f"Status result: exit_code={result.exit_code}, stdout={result.stdout}")
            assert result.exit_code == 0
            assert "Current Stage:" in result.stdout or "Status:" in result.stdout

        logger.info("Complete workflow test completed successfully")

    def test_init_creates_proper_structure(self, runner: CliRunner, temp_project_dir: Path) -> None:
        """Test that init creates proper directory structure."""
        logger.info("Testing init project structure creation")

        # Set up mock environment for SDK
        mock_env = {"ANTHROPIC_API_KEY": "sk-test-mock-key-12345"}

        with (
            patch.dict(os.environ, mock_env),
            patch("verifflowcc.core.orchestrator.Orchestrator"),
            patch("verifflowcc.cli.Path.cwd", return_value=temp_project_dir),
        ):
            result = runner.invoke(app, ["init"])
            logger.debug(f"Init result: exit_code={result.exit_code}, stdout={result.stdout}")
            assert result.exit_code == 0
            assert "Project initialized successfully" in result.stdout

            # Verify directory structure
            agilevv_dir = temp_project_dir / ".agilevv"
            assert agilevv_dir.exists()

            # Check required files
            required_files = [
                agilevv_dir / "config.yaml",
                agilevv_dir / "state.json",
                agilevv_dir / "backlog.md",
                agilevv_dir / "architecture.md",
            ]

            for file_path in required_files:
                assert file_path.exists(), f"Required file {file_path} was not created"
                assert file_path.stat().st_size > 0, f"Required file {file_path} is empty"

            # Check config.yaml structure
            config_path = agilevv_dir / "config.yaml"
            with config_path.open() as f:
                config_data = yaml.safe_load(f)

            assert "v_model" in config_data, "config.yaml should contain v_model section"
            assert "stages" in config_data["v_model"], "v_model should contain stages"

            # Check state.json structure
            state_path = agilevv_dir / "state.json"
            with state_path.open() as f:
                state_data = json.load(f)

            assert "current_stage" in state_data, "state.json should contain current_stage"
            assert "completed_stages" in state_data, "state.json should contain completed_stages"

        logger.info("Init structure test completed")

    def test_config_yaml_has_proper_structure(self, initialized_project: Path) -> None:
        """Test that config.yaml has proper V-Model configuration."""
        logger.info("Testing config.yaml structure")

        config_path = initialized_project / ".agilevv" / "config.yaml"
        assert config_path.exists(), "config.yaml should exist"

        with config_path.open() as f:
            config_data = yaml.safe_load(f)

        # Verify main sections
        assert "v_model" in config_data, "config.yaml should have v_model section"

        v_model = config_data["v_model"]
        assert "stages" in v_model, "v_model should have stages section"
        assert "quality_thresholds" in v_model, "v_model should have quality_thresholds section"

        # Check required stages
        required_stages = [
            "requirements",
            "design",
            "coding",
            "unit_testing",
            "integration_testing",
            "system_testing",
            "validation",
        ]

        stages = v_model["stages"]
        for stage in required_stages:
            assert stage in stages, f"Stage {stage} should be configured"
            stage_config = stages[stage]
            assert "gating" in stage_config, f"Stage {stage} should have gating configuration"
            assert stage_config["gating"] in [
                "hard",
                "soft",
            ], f"Stage {stage} gating should be 'hard' or 'soft'"

        logger.info("Config.yaml structure test completed")

    def test_backlog_has_initial_content(self, initialized_project: Path) -> None:
        """Test that backlog.md is created with initial content."""
        logger.info("Testing backlog.md initial content")

        backlog_path = initialized_project / ".agilevv" / "backlog.md"
        assert backlog_path.exists(), "backlog.md should exist"

        with backlog_path.open() as f:
            content = f.read()

        assert len(content) > 0, "backlog.md should not be empty"
        assert (
            "# Product Backlog" in content or "Backlog" in content
        ), "backlog.md should have backlog header"

        logger.info("Backlog content test completed")

    def test_init_on_existing_project(self, initialized_project: Path, runner: CliRunner) -> None:
        """Test behavior when running init on already initialized project."""
        logger.info("Testing init on existing project")

        # Set up mock environment for SDK
        mock_env = {"ANTHROPIC_API_KEY": "sk-test-mock-key-12345"}

        with (
            patch.dict(os.environ, mock_env),
            patch("verifflowcc.core.orchestrator.Orchestrator"),
            patch("verifflowcc.cli.Path.cwd", return_value=initialized_project),
        ):
            # Should handle existing project gracefully
            result = runner.invoke(app, ["init"])
            logger.debug(
                f"Init on existing result: exit_code={result.exit_code}, stdout={result.stdout}"
            )

            # Should either succeed (reinitialize) or warn about existing project
            assert result.exit_code in [
                0,
                1,
            ], "Init on existing project should succeed or warn gracefully"

            if result.exit_code == 0:
                assert "initialized" in result.stdout.lower(), "Should indicate initialization"
            else:
                assert (
                    "already" in result.stdout.lower() or "existing" in result.stdout.lower()
                ), "Should warn about existing project"

        logger.info("Init on existing project test completed")

    def test_commands_without_init(self, runner: CliRunner, temp_project_dir: Path) -> None:
        """Test that commands fail gracefully when project is not initialized."""
        logger.info("Starting commands without init test")

        # Set up mock environment for SDK
        mock_env = {"ANTHROPIC_API_KEY": "sk-test-mock-key-12345"}

        with (
            patch.dict(os.environ, mock_env),
            patch("verifflowcc.core.orchestrator.Orchestrator"),
            patch("verifflowcc.cli.Path.cwd", return_value=temp_project_dir),
        ):
            # Plan should fail
            logger.info("Testing plan command without init")
            result = runner.invoke(app, ["plan"])
            logger.debug(f"Plan result: exit_code={result.exit_code}, stdout={result.stdout}")
            assert result.exit_code == 1
            assert "not initialized" in result.stdout.lower()

            # Status should fail
            logger.info("Testing status command without init")
            result = runner.invoke(app, ["status"])
            logger.debug(f"Status result: exit_code={result.exit_code}, stdout={result.stdout}")
            assert result.exit_code == 1
            assert "not initialized" in result.stdout.lower()

            # Sprint should fail
            logger.info("Testing sprint command without init")
            result = runner.invoke(app, ["sprint", "--story", "Test story"])
            logger.debug(f"Sprint result: exit_code={result.exit_code}, stdout={result.stdout}")
            assert result.exit_code == 1
            assert "not initialized" in result.stdout.lower()

        logger.info("Commands without init test completed")

    def test_yaml_config_validation(self, initialized_project: Path) -> None:
        """Test that generated YAML config is valid."""
        logger.info("Testing YAML config validation")

        config_path = initialized_project / ".agilevv" / "config.yaml"

        try:
            with config_path.open() as f:
                config_data = yaml.safe_load(f)
        except yaml.YAMLError as e:
            pytest.fail(f"config.yaml is not valid YAML: {e}")

        # Validate structure
        assert isinstance(config_data, dict), "Config should be a dictionary"
        assert "v_model" in config_data, "Should have v_model section"

        v_model = config_data["v_model"]
        assert isinstance(v_model, dict), "v_model should be a dictionary"

        logger.info("YAML config validation completed")

    def test_json_state_validation(self, initialized_project: Path) -> None:
        """Test that generated JSON state is valid."""
        logger.info("Testing JSON state validation")

        state_path = initialized_project / ".agilevv" / "state.json"

        try:
            with state_path.open() as f:
                state_data = json.load(f)
        except json.JSONDecodeError as e:
            pytest.fail(f"state.json is not valid JSON: {e}")

        # Validate structure
        assert isinstance(state_data, dict), "State should be a dictionary"
        assert "current_stage" in state_data, "Should have current_stage"
        assert "completed_stages" in state_data, "Should have completed_stages"
        assert isinstance(state_data["completed_stages"], list), "completed_stages should be a list"

        logger.info("JSON state validation completed")


class TestCLIErrorHandling:
    """Test CLI error handling and edge cases."""

    def test_invalid_commands(self, runner: CliRunner, temp_project_dir: Path) -> None:
        """Test handling of invalid commands."""
        logger.info("Testing invalid command handling")

        # Set up mock environment for SDK
        mock_env = {"ANTHROPIC_API_KEY": "sk-test-mock-key-12345"}

        with (
            patch.dict(os.environ, mock_env),
            patch("verifflowcc.core.orchestrator.Orchestrator"),
            patch("verifflowcc.cli.Path.cwd", return_value=temp_project_dir),
        ):
            # Test invalid command
            result = runner.invoke(app, ["invalid-command"])
            logger.debug(f"Invalid command result: exit_code={result.exit_code}")
            assert result.exit_code != 0, "Invalid command should fail"

        logger.info("Invalid command test completed")

    def test_missing_required_arguments(self, runner: CliRunner, initialized_project: Path) -> None:
        """Test handling of missing required arguments."""
        logger.info("Testing missing arguments handling")

        # Set up mock environment for SDK
        mock_env = {"ANTHROPIC_API_KEY": "sk-test-mock-key-12345"}

        with (
            patch.dict(os.environ, mock_env),
            patch("verifflowcc.core.orchestrator.Orchestrator"),
            patch("verifflowcc.cli.Path.cwd", return_value=initialized_project),
        ):
            # Test sprint command without required story argument
            result = runner.invoke(app, ["sprint"])
            logger.debug(f"Sprint without args result: exit_code={result.exit_code}")
            # Should either fail or provide helpful error message
            assert (
                result.exit_code != 0 or "story" in result.stdout.lower()
            ), "Sprint without arguments should fail or show usage"

        logger.info("Missing arguments test completed")

    def test_help_commands(self, runner: CliRunner) -> None:
        """Test help command functionality."""
        logger.info("Testing help commands")

        # Test main help
        result = runner.invoke(app, ["--help"])
        logger.debug(f"Main help result: exit_code={result.exit_code}")
        assert result.exit_code == 0, "Help command should succeed"
        assert (
            "VeriFlowCC" in result.stdout or "Usage:" in result.stdout
        ), "Help should show usage information"

        # Test command-specific help
        commands = ["init", "plan", "sprint", "status"]
        for command in commands:
            result = runner.invoke(app, [command, "--help"])
            logger.debug(f"{command} help result: exit_code={result.exit_code}")
            assert result.exit_code == 0, f"Help for {command} should succeed"
            assert (
                "Usage:" in result.stdout or command in result.stdout
            ), f"Help should show {command} usage"

        logger.info("Help commands test completed")


@pytest.mark.integration
class TestIntegrationWorkflowScenarios:
    """Comprehensive integration tests marked for CI/CD."""

    def test_complete_v_model_simulation(self, runner: CliRunner, temp_project_dir: Path) -> None:
        """Test complete V-Model cycle simulation."""
        logger.info("Starting complete V-Model simulation test")

        # Set up mock environment for SDK
        mock_env = {"ANTHROPIC_API_KEY": "sk-test-mock-key-12345"}

        with (
            patch.dict(os.environ, mock_env),
            patch("verifflowcc.core.orchestrator.Orchestrator") as mock_orchestrator_class,
            patch("verifflowcc.cli.Path.cwd", return_value=temp_project_dir),
        ):
            # Initialize
            logger.info("Step 1: Initializing project")
            result = runner.invoke(app, ["init"])
            logger.debug(f"Init result: exit_code={result.exit_code}")
            assert result.exit_code == 0

            # Mock orchestrator behavior
            mock_orchestrator_instance = mock_orchestrator_class.return_value
            mock_orchestrator_instance.run_sprint.return_value = {
                "sprint_number": 1,
                "story": {"id": "TEST-001", "title": "Test Story"},
                "stages": {
                    "requirements": {"status": "success"},
                    "design": {"status": "success"},
                    "coding": {"status": "success"},
                    "testing": {"status": "success"},
                    "validation": {"status": "success"},
                },
                "final_decision": "GO",
                "readiness_score": 95,
                "success_rate": 1.0,
            }

            # Plan sprint
            logger.info("Step 2: Planning sprint")
            result = runner.invoke(app, ["plan", "--story-id", "1"])
            logger.debug(f"Plan result: exit_code={result.exit_code}")
            assert result.exit_code == 0

            # Execute sprint
            logger.info("Step 3: Executing sprint")
            with patch("verifflowcc.cli.asyncio.run") as mock_async_run:
                mock_async_run.return_value = mock_orchestrator_instance.run_sprint.return_value
                result = runner.invoke(app, ["sprint", "--story", "Test Integration Story"])
                logger.debug(f"Sprint result: exit_code={result.exit_code}")
                assert result.exit_code == 0

            # Check final status
            logger.info("Step 4: Checking final status")
            result = runner.invoke(app, ["status"])
            logger.debug(f"Status result: exit_code={result.exit_code}")
            assert result.exit_code == 0

        logger.info("Complete V-Model simulation test completed")

    def test_multi_sprint_workflow(self, runner: CliRunner, temp_project_dir: Path) -> None:
        """Test multiple sprint execution workflow."""
        logger.info("Testing multi-sprint workflow")

        # Set up mock environment for SDK
        mock_env = {"ANTHROPIC_API_KEY": "sk-test-mock-key-12345"}

        with (
            patch.dict(os.environ, mock_env),
            patch("verifflowcc.core.orchestrator.Orchestrator") as mock_orchestrator_class,
            patch("verifflowcc.cli.Path.cwd", return_value=temp_project_dir),
        ):
            # Initialize project
            result = runner.invoke(app, ["init"])
            assert result.exit_code == 0

            # Mock successful sprints
            mock_orchestrator_instance = mock_orchestrator_class.return_value

            # Execute multiple sprints
            for sprint_num in range(1, 4):  # 3 sprints
                logger.info(f"Executing sprint {sprint_num}")

                mock_orchestrator_instance.run_sprint.return_value = {
                    "sprint_number": sprint_num,
                    "story": {
                        "id": f"TEST-{sprint_num:03d}",
                        "title": f"Test Story {sprint_num}",
                    },
                    "stages": {
                        "requirements": {"status": "success"},
                        "design": {"status": "success"},
                        "coding": {"status": "success"},
                        "testing": {"status": "success"},
                        "validation": {"status": "success"},
                    },
                    "final_decision": "GO",
                    "readiness_score": 90 + sprint_num,
                    "success_rate": 1.0,
                }

                # Plan and execute sprint
                result = runner.invoke(app, ["plan", "--story-id", str(sprint_num)])
                assert result.exit_code == 0

                with patch("verifflowcc.cli.asyncio.run") as mock_async_run:
                    mock_async_run.return_value = mock_orchestrator_instance.run_sprint.return_value
                    result = runner.invoke(app, ["sprint", "--story", f"Story {sprint_num}"])
                    assert result.exit_code == 0

        logger.info("Multi-sprint workflow test completed")

    def test_error_recovery_scenarios(self, runner: CliRunner, temp_project_dir: Path) -> None:
        """Test error recovery and resilience scenarios."""
        logger.info("Testing error recovery scenarios")

        # Set up mock environment for SDK
        mock_env = {"ANTHROPIC_API_KEY": "sk-test-mock-key-12345"}

        with (
            patch.dict(os.environ, mock_env),
            patch("verifflowcc.core.orchestrator.Orchestrator") as mock_orchestrator_class,
            patch("verifflowcc.cli.Path.cwd", return_value=temp_project_dir),
        ):
            # Initialize
            result = runner.invoke(app, ["init"])
            assert result.exit_code == 0

            # Mock failure scenario
            mock_orchestrator_instance = mock_orchestrator_class.return_value
            mock_orchestrator_instance.run_sprint.return_value = {
                "sprint_number": 1,
                "story": {"id": "FAIL-001", "title": "Failing Story"},
                "stages": {
                    "requirements": {"status": "success"},
                    "design": {"status": "error", "error": "Design validation failed"},
                    "coding": {"status": "skipped"},
                    "testing": {"status": "skipped"},
                    "validation": {"status": "skipped"},
                },
                "final_decision": "NO-GO",
                "readiness_score": 40,
                "success_rate": 0.2,
            }

            # Execute failing sprint
            with patch("verifflowcc.cli.asyncio.run") as mock_async_run:
                mock_async_run.return_value = mock_orchestrator_instance.run_sprint.return_value
                result = runner.invoke(app, ["sprint", "--story", "Failing Story"])
                # Should handle failure gracefully
                assert result.exit_code in [
                    0,
                    1,
                ], "Should handle sprint failure gracefully"

        logger.info("Error recovery scenarios test completed")
