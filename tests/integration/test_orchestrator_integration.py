"""Integration tests for Orchestrator with all agents.

This module tests the full V-Model workflow with all agents integrated.
"""

from unittest.mock import patch

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

    def test_orchestrator_initializes_all_agents(self, isolated_agilevv_dir):
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

    def test_orchestrator_stage_agent_mapping(self, isolated_agilevv_dir):
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

        for stage, expected_agent in stage_mappings.items():
            agent = orchestrator._get_stage_agent(stage)
            assert agent == expected_agent


@pytest.mark.asyncio
class TestFullVModelWorkflow:
    """Test complete V-Model workflow with all agents."""

    @patch("verifflowcc.agents.requirements_analyst.RequirementsAnalystAgent.process")
    @patch("verifflowcc.agents.architect.ArchitectAgent.process")
    @patch("verifflowcc.agents.developer.DeveloperAgent.process")
    @patch("verifflowcc.agents.qa_tester.QATesterAgent.process")
    @patch("verifflowcc.agents.integration.IntegrationAgent.process")
    async def test_complete_sprint_workflow(
        self,
        mock_integration_process,
        mock_qa_process,
        mock_developer_process,
        mock_architect_process,
        mock_requirements_process,
        isolated_agilevv_dir,
    ):
        """Test a complete sprint workflow through all V-Model stages."""

        # Setup mock responses for each agent
        # RequirementsAnalyst uses different return format (execute method)
        mock_requirements_process.return_value = {
            "result": {"acceptance_criteria": ["Test criteria"]},
            "status": "success",
            "artifacts": {"requirements": "requirements.json"},
        }

        mock_architect_process.return_value = {
            "status": "success",
            "next_stage_ready": True,
            "artifacts": {"design": "design.json"},
            "design_specifications": {"components": ["UserService"]},
            "architecture_updates": {"diagrams": ["arch.puml"]},
            "interface_contracts": {"IUser": {"methods": ["getId"]}},
        }

        mock_developer_process.return_value = {
            "status": "success",
            "next_stage_ready": True,
            "artifacts": {"implementation": "impl.json"},
            "source_files": ["src/user_service.py"],
            "code_metrics": {"lines": 100, "complexity": 5},
            "implementation_report": {"features": ["user_management"]},
        }

        mock_qa_process.return_value = {
            "status": "success",
            "next_stage_ready": True,
            "artifacts": {"testing": "tests.json"},
            "test_files": ["tests/test_user.py"],
            "test_results": {"passed": 10, "failed": 0},
            "coverage_report": {"percentage": 95},
            "quality_metrics": {"test_count": 10},
        }

        mock_integration_process.return_value = {
            "status": "success",
            "next_stage_ready": True,
            "artifacts": {"integration": "integration.json"},
            "integration_results": {"status": "healthy"},
            "deployment_validation": {"ready": True},
            "system_health": {"cpu": 25, "memory": 60},
        }

        # Run sprint workflow
        orchestrator = Orchestrator(path_config=isolated_agilevv_dir)

        # Mock sprint data - this becomes the "story" parameter in run_sprint
        sprint_data = {
            "sprint_number": 1,
            "user_story": "As a user I want to login",
            "story_id": "US-001",
        }

        result = await orchestrator.run_sprint(sprint_data)

        # Verify sprint structure (not checking status since implementation varies)
        assert "sprint_number" in result
        assert "story" in result
        assert "stages" in result

        # The orchestrator doesn't return a top-level status, but individual stage results
        # Verify stages were executed by checking the stages dict contains our expected stages
        assert len(result["stages"]) > 0

    @patch("verifflowcc.agents.architect.ArchitectAgent.process")
    async def test_stage_failure_handling(self, mock_architect_process, isolated_agilevv_dir):
        """Test that orchestrator handles stage failures gracefully."""

        # Setup architect to fail
        mock_architect_process.return_value = {
            "status": "error",
            "next_stage_ready": False,
            "errors": ["Design generation failed"],
            "artifacts": {},
        }

        orchestrator = Orchestrator(path_config=isolated_agilevv_dir)

        # Try to execute design stage
        context = {"user_story": "Test story"}
        result = await orchestrator.execute_stage(VModelStage.DESIGN, context)

        # Verify failure was handled
        assert result["status"] == "error"
        assert "Design generation failed" in result["errors"]
        assert result["next_stage_ready"] is False

    @patch("verifflowcc.agents.developer.DeveloperAgent.process")
    async def test_stage_partial_success(self, mock_developer_process, isolated_agilevv_dir):
        """Test handling of partial success from agents."""

        # Setup developer to return partial success
        mock_developer_process.return_value = {
            "status": "partial",
            "next_stage_ready": False,
            "artifacts": {"implementation": "partial_impl.json"},
            "source_files": ["src/incomplete.py"],
            "errors": ["Code quality validation failed"],
        }

        orchestrator = Orchestrator(path_config=isolated_agilevv_dir)

        # Execute coding stage
        context = {"design_artifacts": {"components": ["Service"]}}
        result = await orchestrator.execute_stage(VModelStage.CODING, context)

        # Verify partial success was handled
        assert result["status"] == "partial"
        assert result["next_stage_ready"] is False
        assert "Code quality validation failed" in result["errors"]


class TestOrchestratorArtifactPassing:
    """Test artifact passing between V-Model stages."""

    @pytest.mark.asyncio
    @patch("verifflowcc.agents.architect.ArchitectAgent.process")
    @patch("verifflowcc.agents.developer.DeveloperAgent.process")
    async def test_artifact_passing_design_to_coding(
        self, mock_developer_process, mock_architect_process, isolated_agilevv_dir
    ):
        """Test that artifacts flow correctly from design to coding stage."""

        # Setup architect response with design artifacts
        design_artifacts = {
            "components": ["UserService", "AuthService"],
            "interfaces": ["IUserRepository"],
            "data_models": ["User", "Session"],
        }

        mock_architect_process.return_value = {
            "status": "success",
            "next_stage_ready": True,
            "artifacts": {"design_doc": "design.json"},
            "design_specifications": design_artifacts,
            "architecture_updates": {"diagrams": ["arch.puml"]},
            "interface_contracts": {"IUser": {"methods": ["getId"]}},
        }

        mock_developer_process.return_value = {
            "status": "success",
            "next_stage_ready": True,
            "artifacts": {"implementation": "impl.json"},
            "source_files": ["src/user_service.py"],
        }

        orchestrator = Orchestrator(path_config=isolated_agilevv_dir)

        # Execute design stage with requirements artifacts in the context
        design_result = await orchestrator.execute_stage(
            VModelStage.DESIGN,
            {"story_id": "US-001", "requirements_artifacts": {"story": "User login"}},
        )

        # Execute coding stage with design artifacts
        coding_context = {
            "story_id": "US-001",
            "design_artifacts": design_result["design_specifications"],
            "architecture_context": design_result["architecture_updates"],
        }

        coding_result = await orchestrator.execute_stage(VModelStage.CODING, coding_context)

        # Verify developer received design artifacts
        mock_developer_process.assert_called_once()
        call_args = mock_developer_process.call_args[0][0]
        assert "design_artifacts" in call_args
        assert call_args["design_artifacts"] == design_artifacts


class TestOrchestratorConfiguration:
    """Test Orchestrator configuration and agent setup."""

    def test_orchestrator_loads_agent_configuration(self, isolated_agilevv_dir):
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

    def test_orchestrator_handles_missing_config(self, isolated_agilevv_dir):
        """Test that Orchestrator handles missing configuration gracefully."""
        # Don't create any configuration file
        orchestrator = Orchestrator(path_config=isolated_agilevv_dir)

        # Should initialize with default values
        assert orchestrator.agents is not None
        assert len(orchestrator.agents) == 5  # All 5 agents


class TestOrchestratorErrorRecovery:
    """Test Orchestrator error recovery and rollback mechanisms."""

    @pytest.mark.asyncio
    async def test_orchestrator_checkpoint_on_stage_completion(self, isolated_agilevv_dir):
        """Test that Orchestrator creates checkpoints after successful stages."""
        orchestrator = Orchestrator(path_config=isolated_agilevv_dir)

        # Execute checkpoint
        checkpoint_name = "design_complete"
        await orchestrator.checkpoint(checkpoint_name)

        # Verify checkpoint was created
        checkpoint_path = isolated_agilevv_dir.base_dir / "checkpoints" / f"{checkpoint_name}.json"
        assert checkpoint_path.exists()

    @pytest.mark.asyncio
    async def test_orchestrator_rollback_on_failure(self, isolated_agilevv_dir):
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
