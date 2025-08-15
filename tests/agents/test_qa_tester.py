"""Tests for QATesterAgent (Testing stage agent).

This module tests the QATesterAgent functionality including test generation,
test execution, and quality validation.
"""

import json
from typing import Any
from unittest.mock import patch

import pytest
from verifflowcc.agents.qa_tester import QATesterAgent
from verifflowcc.core.orchestrator import VModelStage
from verifflowcc.core.path_config import PathConfig
from verifflowcc.schemas.agent_schemas import TestingInput, TestingOutput


class TestQATesterAgentInitialization:
    """Test QATesterAgent initialization and configuration."""

    def test_qa_tester_agent_initialization(self, isolated_agilevv_dir: PathConfig) -> None:
        """Test QATesterAgent initializes correctly."""
        agent = QATesterAgent(name="qa_tester", path_config=isolated_agilevv_dir)

        assert agent.name == "qa_tester"
        assert agent.path_config == isolated_agilevv_dir
        assert agent.agent_type == "qa"


class TestQATesterAgentInputValidation:
    """Test QATesterAgent input validation and processing."""

    def test_testing_input_validation(self, isolated_agilevv_dir: PathConfig) -> None:
        """Test that QATesterAgent validates TestingInput correctly."""
        # Instantiate agent to verify it can be created with valid config
        QATesterAgent(path_config=isolated_agilevv_dir)

        # Valid input
        valid_input = TestingInput(
            story_id="US-001",
            stage=VModelStage.UNIT_TESTING,
            context={"implementation_complete": True},
            test_scope=["unit", "integration"],
            acceptance_criteria=["User can login", "User can logout"],
        )

        # Should not raise any validation errors
        assert valid_input.story_id == "US-001"
        assert valid_input.stage == VModelStage.UNIT_TESTING
        assert valid_input.test_scope == ["unit", "integration"]


@pytest.mark.asyncio
class TestQATesterAgentProcessing:
    """Test QATesterAgent main processing functionality."""

    @patch("verifflowcc.agents.qa_tester.QATesterAgent._call_claude_sdk")
    async def test_process_test_generation(
        self, mock_claude_api: Any, isolated_agilevv_dir: PathConfig
    ) -> None:
        """Test the main process method for test generation."""
        # Setup mock response
        mock_response = {
            "test_files": ["tests/test_user_service.py", "tests/test_auth_service.py"],
            "test_results": {"passed": 10, "failed": 0, "total": 10},
            "coverage_report": {"percentage": 95.5, "missing_lines": []},
            "quality_metrics": {"test_count": 10, "assertions": 25},
        }
        mock_claude_api.return_value = json.dumps(mock_response)

        agent = QATesterAgent(path_config=isolated_agilevv_dir)

        # Create input
        testing_input = TestingInput(
            story_id="US-001",
            stage=VModelStage.UNIT_TESTING,
            context={"implementation_complete": True},
            test_scope=["unit", "integration"],
            acceptance_criteria=["User can login", "User can logout"],
        )

        # Process
        result = await agent.process(testing_input.model_dump())

        # Validate result structure
        assert isinstance(result, dict)
        assert result["status"] == "success"
        assert result["next_stage_ready"] is True
        assert "test_files" in result
        assert "test_results" in result

        # Validate that artifacts were saved
        test_artifact_path = isolated_agilevv_dir.base_dir / "testing" / "US-001.json"
        assert test_artifact_path.exists()

    @patch("verifflowcc.agents.qa_tester.QATesterAgent._call_claude_sdk")
    async def test_process_with_api_failure(
        self, mock_claude_api: Any, isolated_agilevv_dir: PathConfig
    ) -> None:
        """Test process method handles API failures gracefully."""
        # Setup mock to raise an exception
        mock_claude_api.side_effect = Exception("API Error: Test generation failed")

        agent = QATesterAgent(path_config=isolated_agilevv_dir)

        testing_input = TestingInput(
            story_id="US-002",
            stage=VModelStage.UNIT_TESTING,
            context={},
            test_scope=["unit"],
            acceptance_criteria=["Basic functionality works"],
        )

        # Process should handle the error
        result = await agent.process(testing_input.model_dump())

        assert result["status"] == "error"
        assert result["next_stage_ready"] is False
        assert "error" in result


class TestQATesterAgentIntegration:
    """Integration tests for QATesterAgent with V-Model workflow."""

    def test_testing_output_validation(self, isolated_agilevv_dir: PathConfig) -> None:
        """Test TestingOutput validation for next stage."""
        # Create valid testing output
        testing_output_data: dict[str, Any] = {
            "status": "success",
            "artifacts": {"test_report": "path/to/tests.json"},
            "test_files": ["tests/test_user.py", "tests/test_auth.py"],
            "test_results": {"passed": 15, "failed": 0, "total": 15},
            "coverage_report": {"percentage": 95.0, "missing_lines": []},
            "quality_metrics": {"test_count": 15, "assertions": 40},
            "next_stage_ready": True,
        }

        # Should validate successfully
        testing_output = TestingOutput(**testing_output_data)
        assert testing_output.status == "success"
        assert testing_output.next_stage_ready is True
        assert len(testing_output.test_files) == 2
