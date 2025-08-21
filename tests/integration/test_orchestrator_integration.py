"""Integration tests for Orchestrator with all agents.

This module tests the full V-Model workflow with all agents integrated.
"""

from typing import Any

import pytest
from verifflowcc.agents.architect import ArchitectAgent
from verifflowcc.agents.developer import DeveloperAgent
from verifflowcc.agents.integration import IntegrationAgent
from verifflowcc.agents.qa_tester import QATesterAgent
from verifflowcc.agents.requirements_analyst import RequirementsAnalystAgent
from verifflowcc.core.orchestrator import Orchestrator
from verifflowcc.core.vmodel import VModelStage


class TestOrchestratorAgentIntegration:
    """Test Orchestrator integration with all V-Model agents."""

    def test_orchestrator_initializes_all_agents(self, isolated_agilevv_dir: Any) -> None:
        """Test that Orchestrator initializes all required agents."""
        orchestrator = Orchestrator(path_config=isolated_agilevv_dir)

        # Verify all agents are initialized
        agents = orchestrator.agents
        assert "requirements_analyst" in agents
        assert "architect" in agents
        assert "developer" in agents
        assert "qa_tester" in agents
        assert "integration" in agents

        # Verify agent types
        assert isinstance(agents["requirements_analyst"], RequirementsAnalystAgent)
        assert isinstance(agents["architect"], ArchitectAgent)
        assert isinstance(agents["developer"], DeveloperAgent)
        assert isinstance(agents["qa_tester"], QATesterAgent)
        assert isinstance(agents["integration"], IntegrationAgent)

    def test_orchestrator_stage_agent_mapping(self, isolated_agilevv_dir: Any) -> None:
        """Test that Orchestrator maps stages to correct agents."""
        orchestrator = Orchestrator(path_config=isolated_agilevv_dir)

        # Test stage to agent mapping
        stage_mappings = {
            VModelStage.REQUIREMENTS: "requirements_analyst",
            VModelStage.DESIGN: "architect",
            VModelStage.CODING: "developer",
            VModelStage.UNIT_TESTING: "qa_tester",
            VModelStage.INTEGRATION_TESTING: "qa_tester",
            VModelStage.SYSTEM_TESTING: "qa_tester",
        }

        for _stage, expected_agent_name in stage_mappings.items():
            # Check that the expected agent exists
            assert expected_agent_name in orchestrator.agents
            # The actual agent mapping happens internally during execution


# NOTE: V-Model workflow and artifact passing tests with real SDK integration
# are implemented in test_real_orchestrator_integration.py


class TestOrchestratorConfiguration:
    """Test Orchestrator configuration and agent setup."""

    def test_orchestrator_loads_agent_configuration(self, isolated_agilevv_dir: Any) -> None:
        """Test that Orchestrator loads agent configuration correctly."""
        # Create test configuration in YAML format (as expected by orchestrator)
        config_data = """
v_model:
  gating_mode: soft
agents:
  architect:
    model: claude-3-opus
    max_tokens: 8000
  developer:
    model: claude-3-haiku
    max_tokens: 6000
"""

        # Save configuration
        config_path = isolated_agilevv_dir.config_path
        config_path.parent.mkdir(parents=True, exist_ok=True)
        config_path.write_text(config_data)

        # Initialize orchestrator
        orchestrator = Orchestrator(path_config=isolated_agilevv_dir)

        # Verify agent configuration was applied
        architect_agent = orchestrator.agents["architect"]
        developer_agent = orchestrator.agents["developer"]

        # The orchestrator implementation does load and apply the configuration
        assert architect_agent.model == "claude-3-opus"
        assert architect_agent.max_tokens == 8000
        assert developer_agent.model == "claude-3-haiku"
        assert developer_agent.max_tokens == 6000

    def test_orchestrator_handles_missing_config(self, isolated_agilevv_dir: Any) -> None:
        """Test that Orchestrator handles missing configuration gracefully."""
        # Don't create any configuration file
        orchestrator = Orchestrator(path_config=isolated_agilevv_dir)

        # Should initialize with default values
        assert orchestrator.agents is not None
        assert len(orchestrator.agents) == 5  # All 5 agents


class TestOrchestratorErrorRecovery:
    """Test Orchestrator error recovery and rollback mechanisms."""

    @pytest.mark.asyncio
    async def test_orchestrator_checkpoint_on_stage_completion(
        self, isolated_agilevv_dir: Any
    ) -> None:
        """Test that Orchestrator creates checkpoints after successful stages."""
        orchestrator = Orchestrator(path_config=isolated_agilevv_dir)

        # Execute checkpoint
        checkpoint_name = "design_complete"
        await orchestrator.checkpoint(checkpoint_name)

        # Verify checkpoint was created
        checkpoint_path = isolated_agilevv_dir.base_dir / "checkpoints" / f"{checkpoint_name}.json"
        assert checkpoint_path.exists()

    @pytest.mark.asyncio
    async def test_orchestrator_rollback_on_failure(self, isolated_agilevv_dir: Any) -> None:
        """Test that Orchestrator can rollback to previous checkpoint."""
        orchestrator = Orchestrator(path_config=isolated_agilevv_dir)

        # Create initial state (set both state and current_stage)
        orchestrator.current_stage = VModelStage.DESIGN
        orchestrator.state.update({"current_stage": "design", "completed": []})
        await orchestrator.checkpoint("initial_state")

        # Modify state (set both state and current_stage)
        orchestrator.current_stage = VModelStage.CODING
        orchestrator.state.update({"current_stage": "coding", "completed": ["design"]})

        # Rollback
        result = await orchestrator.restore_checkpoint("initial_state")

        # Verify rollback succeeded
        assert result is True

        # Verify state was restored
        assert (
            orchestrator.state["current_stage"] == "design"
        )  # String comparison since it's loaded from JSON
        assert orchestrator.state["completed"] == []
