"""Tests for IntegrationAgent (Integration stage agent).

This module tests the IntegrationAgent functionality including system validation,
deployment verification, and integration reporting.
"""

from typing import Any
from unittest.mock import patch

import pytest
from verifflowcc.agents.integration import IntegrationAgent
from verifflowcc.core.orchestrator import VModelStage
from verifflowcc.core.path_config import PathConfig
from verifflowcc.schemas.agent_schemas import IntegrationInput, IntegrationOutput


class TestIntegrationAgentInitialization:
    """Test IntegrationAgent initialization and configuration."""

    def test_integration_agent_initialization(self, isolated_agilevv_dir: PathConfig) -> None:
        """Test IntegrationAgent initializes correctly."""
        agent = IntegrationAgent(name="integration", path_config=isolated_agilevv_dir)

        assert agent.name == "integration"
        assert agent.path_config == isolated_agilevv_dir
        assert agent.agent_type == "integration"


class TestIntegrationAgentInputValidation:
    """Test IntegrationAgent input validation and processing."""

    def test_integration_input_validation(self, isolated_agilevv_dir: PathConfig) -> None:
        """Test that IntegrationAgent validates IntegrationInput correctly."""
        # Instantiate agent to verify it can be created with valid config
        IntegrationAgent(path_config=isolated_agilevv_dir)

        # Valid input
        valid_input = IntegrationInput(
            story_id="US-001",
            stage=VModelStage.INTEGRATION_TESTING,
            context={"all_tests_passed": True},
            system_artifacts={"deployment": "config", "tests": "results"},
            integration_scope=["database", "api", "frontend"],
        )

        # Should not raise any validation errors
        assert valid_input.story_id == "US-001"
        assert valid_input.stage == VModelStage.INTEGRATION_TESTING
        assert valid_input.integration_scope == ["database", "api", "frontend"]


@pytest.mark.asyncio
class TestIntegrationAgentProcessing:
    """Test IntegrationAgent main processing functionality."""

    @patch("verifflowcc.agents.integration.IntegrationAgent._call_claude_api")
    async def test_process_integration_validation(
        self, mock_claude_api: Any, isolated_agilevv_dir: PathConfig
    ) -> None:
        """Test the main process method for integration validation."""
        # Setup mock response
        mock_response = {
            "integration_results": {"status": "healthy", "services": 3},
            "deployment_validation": {"environment": "staging", "health_checks": True},
            "system_health": {"cpu": 25, "memory": 60, "uptime": "99.9%"},
        }
        mock_claude_api.return_value = mock_response

        agent = IntegrationAgent(path_config=isolated_agilevv_dir)

        # Create input
        integration_input = IntegrationInput(
            story_id="US-001",
            stage=VModelStage.INTEGRATION_TESTING,
            context={"all_tests_passed": True},
            system_artifacts={"deployment": "config"},
            integration_scope=["database", "api", "frontend"],
        )

        # Process
        result = await agent.process(integration_input.model_dump())

        # Validate result structure
        assert isinstance(result, dict)
        assert result["status"] == "success"
        assert result["next_stage_ready"] is True
        assert "integration_results" in result

        # Validate that artifacts were saved
        integration_artifact_path = isolated_agilevv_dir.base_dir / "integration" / "US-001.json"
        assert integration_artifact_path.exists()


class TestIntegrationAgentIntegration:
    """Integration tests for IntegrationAgent with V-Model workflow."""

    def test_integration_output_validation(self, isolated_agilevv_dir: PathConfig) -> None:
        """Test IntegrationOutput validation for next stage."""
        # Create valid integration output
        integration_output_data: dict[str, Any] = {
            "status": "success",
            "artifacts": {"integration_report": "path/to/integration.json"},
            "integration_results": {"status": "healthy", "services": 3},
            "deployment_validation": {"environment": "production", "health_checks": True},
            "system_health": {"cpu": 30, "memory": 50, "uptime": "99.95%"},
            "next_stage_ready": True,
        }

        # Should validate successfully
        integration_output = IntegrationOutput(**integration_output_data)
        assert integration_output.status == "success"
        assert integration_output.next_stage_ready is True
        assert integration_output.integration_results["status"] == "healthy"
