"""Integration tests for PathConfig refactoring across the codebase.

NOTE: Mock infrastructure has been removed. Integration tests are now skipped
and will be replaced with real SDK integration tests.
"""

import os
from pathlib import Path

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
        pytest.skip("Requires real CLI integration - will be replaced")

    def test_cli_uses_environment_variable(self, tmp_path: Path) -> None:
        """Test that CLI respects AGILEVV_BASE_DIR environment variable."""
        pytest.skip("Requires real CLI integration - will be replaced")


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
        assert orchestrator.path_config == isolated_agilevv_dir

        # Ensure state has checkpoint_history key
        if "checkpoint_history" not in orchestrator.state:
            orchestrator.state["checkpoint_history"] = []

        # Test basic functionality without mocking
        checkpoint_name = "test-checkpoint"
        await orchestrator.checkpoint(checkpoint_name, "Test checkpoint")

        checkpoint_file = isolated_agilevv_dir.checkpoints_dir / f"{checkpoint_name}.json"
        assert checkpoint_file.exists()

    def test_orchestrator_load_state_with_path_config(
        self, isolated_agilevv_dir: PathConfig
    ) -> None:
        """Test that Orchestrator loads state from PathConfig location."""
        import json

        # Create test state
        test_state = {"current_stage": "requirements", "sprint": 1}
        isolated_agilevv_dir.ensure_structure()
        isolated_agilevv_dir.state_path.write_text(json.dumps(test_state, indent=2))

        # Create orchestrator
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

        # Test basic functionality without mocking
        assert analyst.path_config == isolated_agilevv_dir
        assert analyst.path_config.backlog_path.exists()


class TestGitIntegrationPathConfig:
    """Test GitIntegration with PathConfig."""

    def test_git_integration_uses_path_config_basic(
        self, tmp_path: Path, isolated_agilevv_dir: PathConfig
    ) -> None:
        """Test basic GitIntegration with PathConfig."""
        # Test basic functionality without mocking external dependencies
        git = GitIntegration(path_config=isolated_agilevv_dir)
        assert git.path_config == isolated_agilevv_dir

    def test_create_checkpoint_commit_path_config_skipped(
        self, tmp_path: Path, isolated_agilevv_dir: PathConfig
    ) -> None:
        """Test checkpoint creation - skipped due to git dependency."""
        pytest.skip("Requires real git integration - will be replaced")


class PathConfigBackwardCompatibility:
    """Test backward compatibility with existing .agilevv directories."""

    def test_default_uses_dot_agilevv(self, tmp_path: Path) -> None:
        """Test that default PathConfig uses .agilevv directory."""
        # Test without environment variable override
        old_value = os.environ.get("AGILEVV_BASE_DIR")
        try:
            if "AGILEVV_BASE_DIR" in os.environ:
                del os.environ["AGILEVV_BASE_DIR"]

            # Change to tmp_path for this test
            original_cwd = Path.cwd()
            os.chdir(tmp_path)

            try:
                config = PathConfig()
                expected_path = tmp_path / ".agilevv"
                assert config.base_dir == expected_path
            finally:
                os.chdir(original_cwd)
        finally:
            if old_value is not None:
                os.environ["AGILEVV_BASE_DIR"] = old_value

    def test_migration_from_legacy_structure(self, tmp_path: Path) -> None:
        """Test migration from legacy .agilevv structure."""
        # Create legacy structure
        legacy_dir = tmp_path / ".agilevv"
        legacy_dir.mkdir()
        (legacy_dir / "backlog.md").write_text("# Legacy Backlog")
        (legacy_dir / "state.json").write_text('{"legacy": true}')

        # Test that PathConfig can work with existing structure
        config = PathConfig(base_dir=legacy_dir)
        config.ensure_structure()

        # Should preserve existing files
        assert config.backlog_path.exists()
        assert "Legacy Backlog" in config.backlog_path.read_text()

    def test_concurrent_access_different_directories(self, tmp_path: Path) -> None:
        """Test concurrent access to different PathConfig directories."""
        # Create two different configurations
        dir1 = tmp_path / "project1" / ".agilevv"
        dir2 = tmp_path / "project2" / ".agilevv"

        config1 = PathConfig(base_dir=dir1)
        config2 = PathConfig(base_dir=dir2)

        # Both should work independently
        config1.ensure_structure()
        config2.ensure_structure()

        assert config1.base_dir != config2.base_dir
        assert config1.backlog_path != config2.backlog_path
        assert config1.base_dir.exists()
        assert config2.base_dir.exists()


# NOTE: All SDK-dependent integration tests have been removed/skipped
# They will be replaced with proper real SDK integration tests
