"""Integration tests for PathConfig refactoring across the codebase."""

import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from verifflowcc.agents.base import BaseAgent
from verifflowcc.agents.requirements_analyst import RequirementsAnalystAgent
from verifflowcc.core.git_integration import GitIntegration
from verifflowcc.core.orchestrator import Orchestrator
from verifflowcc.core.path_config import PathConfig


class TestCLIPathConfigIntegration:
    """Test CLI integration with PathConfig."""

    def test_cli_init_uses_path_config(self, isolated_agilevv_dir: PathConfig) -> None:
        """Test that CLI init command uses PathConfig."""

        # Mock the PathConfig to use our isolated directory
        with patch("verifflowcc.cli.PathConfig") as mock_path_config:
            mock_path_config.return_value = isolated_agilevv_dir

            # Call init - using typer context
            from typer.testing import CliRunner
            from verifflowcc.cli import app

            runner = CliRunner()
            runner.invoke(app, ["init", "--force"])

            # Verify structure was created
            assert isolated_agilevv_dir.base_dir.exists()
            assert isolated_agilevv_dir.config_path.exists()
            assert isolated_agilevv_dir.state_path.exists()

    def test_cli_respects_env_variable(self, tmp_path: Path) -> None:
        """Test that CLI respects AGILEVV_BASE_DIR environment variable."""
        custom_dir = tmp_path / "custom-agilevv"

        with patch.dict(os.environ, {"AGILEVV_BASE_DIR": str(custom_dir)}):
            from verifflowcc.cli import get_path_config

            config = get_path_config()
            assert config.base_dir == custom_dir


class TestOrchestratorPathConfigIntegration:
    """Test Orchestrator integration with PathConfig."""

    @pytest.mark.asyncio
    async def test_orchestrator_uses_path_config(self, isolated_agilevv_dir: PathConfig) -> None:
        """Test that Orchestrator uses PathConfig for all paths."""
        # Create necessary files
        isolated_agilevv_dir.ensure_structure(create_defaults=True)

        # Create orchestrator with PathConfig
        orchestrator = Orchestrator(path_config=isolated_agilevv_dir)

        # Verify it uses the correct paths
        assert orchestrator.config_path == isolated_agilevv_dir.config_path
        assert orchestrator.state_path == isolated_agilevv_dir.state_path

        # Ensure state has checkpoint_history key
        if "checkpoint_history" not in orchestrator.state:
            orchestrator.state["checkpoint_history"] = []

        # Test checkpoint creation
        checkpoint_name = "test-checkpoint"
        await orchestrator.checkpoint(checkpoint_name, "Test checkpoint")

        checkpoint_file = isolated_agilevv_dir.checkpoints_dir / f"{checkpoint_name}.json"
        assert checkpoint_file.exists()

    def test_orchestrator_load_state_with_path_config(
        self, isolated_agilevv_dir: PathConfig
    ) -> None:
        """Test that Orchestrator loads state from PathConfig location."""
        import json

        # Create state file
        isolated_agilevv_dir.ensure_base_exists()
        test_state = {"current_stage": "testing", "sprint": 1}
        isolated_agilevv_dir.state_path.write_text(json.dumps(test_state))

        # Create orchestrator - state is loaded in __init__
        orchestrator = Orchestrator(path_config=isolated_agilevv_dir)

        # The state is loaded automatically in the constructor
        assert orchestrator.state["current_stage"] == test_state["current_stage"]
        assert orchestrator.state["sprint"] == test_state["sprint"]


class TestAgentsPathConfigIntegration:
    """Test agent integration with PathConfig."""

    def test_base_agent_uses_path_config(self, isolated_agilevv_dir: PathConfig) -> None:
        """Test that BaseAgent uses PathConfig."""
        isolated_agilevv_dir.ensure_structure(create_defaults=True)

        # Create a concrete implementation of BaseAgent since it's abstract
        class TestAgent(BaseAgent):
            async def process(self, input_data: dict) -> dict:
                return {"result": "test"}

        agent = TestAgent(name="test-agent", agent_type="test", path_config=isolated_agilevv_dir)

        # Test artifact saving
        artifact_name = "test-artifact.json"
        artifact_data = {"test": "data"}
        agent.save_artifact(artifact_name, artifact_data)

        artifact_path = isolated_agilevv_dir.base_dir / artifact_name
        assert artifact_path.exists()

        # Test artifact loading
        loaded_data = agent.load_artifact(artifact_name)
        assert loaded_data == artifact_data

    def test_requirements_analyst_uses_path_config(self, isolated_agilevv_dir: PathConfig) -> None:
        """Test that RequirementsAnalyst uses PathConfig."""
        # Create backlog
        isolated_agilevv_dir.ensure_base_exists()
        isolated_agilevv_dir.backlog_path.write_text("# Test Backlog\n\n- Story 1")

        analyst = RequirementsAnalystAgent(path_config=isolated_agilevv_dir)

        # Mock the internal analyze method since we don't have Claude API
        import asyncio

        async def mock_analyze_func(story: dict) -> dict:
            return {
                "id": "STORY-001",
                "title": "Test Story",
                "requirements": "Analyzed requirements",
            }

        with patch.object(analyst, "_analyze_requirements", new=mock_analyze_func):
            # Also mock _update_backlog since we don't need to actually write files
            async def mock_update_backlog(path: Path, requirements: dict) -> None:
                pass

            with patch.object(analyst, "_update_backlog", new=mock_update_backlog):
                # Process requirements
                result = asyncio.run(analyst.process({"story": {"id": "STORY-001"}}))

            # Verify it processes correctly
            assert "requirements" in result


class TestGitIntegrationPathConfig:
    """Test GitIntegration with PathConfig."""

    def test_git_integration_uses_path_config(
        self, isolated_agilevv_dir: PathConfig, tmp_path: Path
    ) -> None:
        """Test that GitIntegration uses PathConfig for staging."""
        # Initialize a git repo
        import subprocess

        repo_path = tmp_path / "test-repo"
        repo_path.mkdir()
        subprocess.run(["git", "init"], cwd=repo_path, check=True)

        # Create GitIntegration with custom path
        git = GitIntegration(repo_path=repo_path)

        # Create .agilevv structure in the repo
        agilevv_dir = repo_path / isolated_agilevv_dir.base_dir.name
        agilevv_dir.mkdir(parents=True)
        (agilevv_dir / "test.txt").write_text("test")

        # Test that create_checkpoint stages the correct directory
        with patch("verifflowcc.core.git_integration.PathConfig") as mock_path_config:
            mock_config = MagicMock()
            mock_config.base_dir = agilevv_dir
            mock_path_config.return_value = mock_config

            # Create checkpoint commit
            git.create_checkpoint_commit("test-checkpoint", "Test message")

            # Verify the directory was staged
            result = subprocess.run(
                ["git", "status", "--porcelain"], cwd=repo_path, capture_output=True, text=True
            )
            assert agilevv_dir.name in result.stdout


class PathConfigBackwardCompatibility:
    """Test backward compatibility with existing .agilevv directories."""

    def test_default_uses_dot_agilevv(self, tmp_path: Path) -> None:
        """Test that PathConfig defaults to .agilevv for compatibility."""
        # Change to temp directory
        original_cwd = Path.cwd()
        os.chdir(tmp_path)

        try:
            config = PathConfig()
            assert config.base_dir == tmp_path / ".agilevv"
        finally:
            os.chdir(original_cwd)

    def test_existing_agilevv_directory_works(self, tmp_path: Path) -> None:
        """Test that existing .agilevv directories continue to work."""
        # Create existing .agilevv structure
        agilevv_dir = tmp_path / ".agilevv"
        agilevv_dir.mkdir()
        (agilevv_dir / "config.yaml").write_text("version: 1.0.0")
        (agilevv_dir / "state.json").write_text('{"stage": "planning"}')

        # Change to temp directory
        original_cwd = Path.cwd()
        os.chdir(tmp_path)

        try:
            config = PathConfig()

            # Verify it finds the existing files
            assert config.config_path.exists()
            assert config.state_path.exists()
            assert "version" in config.config_path.read_text()
        finally:
            os.chdir(original_cwd)
