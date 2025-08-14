"""Tests for Requirements Analyst agent.

This module tests the RequirementsAnalystAgent including requirements parsing,
INVEST/SMART validation, story quality scoring, and SDK integration.
"""

import json
from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
from verifflowcc.agents.requirements_analyst import RequirementsAnalystAgent
from verifflowcc.core.sdk_config import SDKConfig

from tests.conftest import PathConfig as TestPathConfig


class TestRequirementsAnalystInitialization:
    """Test RequirementsAnalyst agent initialization."""

    def test_requirements_analyst_initialization_defaults(
        self, isolated_agilevv_dir: TestPathConfig
    ) -> None:
        """Test RequirementsAnalyst initialization with defaults."""
        sdk_config = SDKConfig(api_key="test-key")
        agent = RequirementsAnalystAgent(path_config=isolated_agilevv_dir, sdk_config=sdk_config)

        assert agent.name == "requirements_analyst"
        assert agent.agent_type == "requirements"
        assert agent.path_config == isolated_agilevv_dir
        assert agent.mock_mode is False

    def test_requirements_analyst_initialization_custom(
        self, isolated_agilevv_dir: TestPathConfig
    ) -> None:
        """Test RequirementsAnalyst initialization with custom parameters."""
        sdk_config = SDKConfig(api_key="test-key")

        agent = RequirementsAnalystAgent(
            name="custom_analyst",
            agent_type="requirements",
            path_config=isolated_agilevv_dir,
            sdk_config=sdk_config,
            mock_mode=True,
        )

        assert agent.name == "custom_analyst"
        assert agent.agent_type == "requirements"
        assert agent.path_config == isolated_agilevv_dir
        assert agent.sdk_config == sdk_config
        assert agent.mock_mode is True

    def test_requirements_analyst_initialization_mock_mode(
        self, isolated_agilevv_dir: TestPathConfig
    ) -> None:
        """Test RequirementsAnalyst initialization in mock mode."""
        sdk_config = SDKConfig(api_key="test-key")
        agent = RequirementsAnalystAgent(
            path_config=isolated_agilevv_dir, sdk_config=sdk_config, mock_mode=True
        )

        assert agent.mock_mode is True
        assert agent.agent_type == "requirements"


@pytest.mark.asyncio
class TestRequirementsProcessing:
    """Test requirements processing functionality."""

    async def test_process_basic_user_story(self, isolated_agilevv_dir: TestPathConfig) -> None:
        """Test processing a basic user story."""
        sdk_config = SDKConfig(api_key="test-key")
        agent = RequirementsAnalystAgent(
            path_config=isolated_agilevv_dir, sdk_config=sdk_config, mock_mode=True
        )

        # Mock the SDK call
        mock_response = json.dumps(
            {
                "functional_requirements": [
                    {"id": "FR-001", "description": "User can log in with credentials"}
                ],
                "non_functional_requirements": [
                    {"id": "NFR-001", "description": "Login response time < 2 seconds"}
                ],
                "acceptance_criteria": [
                    {"id": "AC-001", "scenario": "User enters valid credentials and gains access"}
                ],
            }
        )

        with patch.object(agent, "_call_claude_sdk", new_callable=AsyncMock) as mock_claude:
            mock_claude.return_value = mock_response

            input_data = {
                "story": {
                    "id": "US-001",
                    "title": "User Login",
                    "description": "As a user, I want to log in so I can access my account",
                }
            }

            result = await agent.process(input_data)

            # Verify structure
            assert "id" in result
            assert "functional_requirements" in result
            assert "non_functional_requirements" in result
            assert "acceptance_criteria" in result
            assert "elaborated_at" in result
            assert result["agent"] == "requirements_analyst"

    async def test_process_with_context(self, isolated_agilevv_dir: TestPathConfig) -> None:
        """Test processing with project context."""
        sdk_config = SDKConfig(api_key="test-key")
        agent = RequirementsAnalystAgent(
            path_config=isolated_agilevv_dir, sdk_config=sdk_config, mock_mode=True
        )

        mock_response = '{"functional_requirements": [{"id": "FR-001", "description": "Feature implementation"}]}'

        with patch.object(agent, "_call_claude_sdk", new_callable=AsyncMock) as mock_claude:
            mock_claude.return_value = mock_response

            input_data = {
                "story": {
                    "id": "US-002",
                    "title": "Payment Processing",
                    "description": "As a user, I want to make payments",
                },
                "context": {
                    "project_name": "E-commerce Platform",
                    "sprint_number": 3,
                    "team_size": 5,
                },
            }

            result = await agent.process(input_data)

            assert result["id"] == "US-002"
            assert "original_story" in result
            assert result["original_story"]["title"] == "Payment Processing"

    async def test_process_invalid_json_response(
        self, isolated_agilevv_dir: TestPathConfig
    ) -> None:
        """Test handling of invalid JSON response from Claude."""
        sdk_config = SDKConfig(api_key="test-key")
        agent = RequirementsAnalystAgent(
            path_config=isolated_agilevv_dir, sdk_config=sdk_config, mock_mode=True
        )

        # Non-JSON response
        mock_response = "This is a text response without JSON structure."

        with patch.object(agent, "_call_claude_sdk", new_callable=AsyncMock) as mock_claude:
            mock_claude.return_value = mock_response

            input_data = {
                "story": {
                    "id": "US-003",
                    "title": "Invalid Response Test",
                    "description": "Test story",
                }
            }

            result = await agent.process(input_data)

            # Should still return structured data
            assert "id" in result
            assert "response_text" in result
            assert result["response_text"] == mock_response
            assert "functional_requirements" in result
            assert isinstance(result["functional_requirements"], list)

    async def test_process_sdk_error_handling(self, isolated_agilevv_dir: TestPathConfig) -> None:
        """Test handling of SDK errors during processing."""
        sdk_config = SDKConfig(api_key="test-key")
        agent = RequirementsAnalystAgent(
            path_config=isolated_agilevv_dir, sdk_config=sdk_config, mock_mode=True
        )

        with patch.object(agent, "_call_claude_sdk", new_callable=AsyncMock) as mock_claude:
            mock_claude.side_effect = Exception("SDK connection failed")

            input_data = {
                "story": {"id": "US-004", "title": "Error Test", "description": "Test story"}
            }

            with pytest.raises(Exception, match="SDK connection failed"):
                await agent.process(input_data)

    async def test_process_with_task_description(
        self, isolated_agilevv_dir: TestPathConfig
    ) -> None:
        """Test processing with task description instead of story."""
        sdk_config = SDKConfig(api_key="test-key")
        agent = RequirementsAnalystAgent(
            path_config=isolated_agilevv_dir, sdk_config=sdk_config, mock_mode=True
        )

        mock_response = (
            '{"functional_requirements": [{"id": "FR-001", "description": "Task requirement"}]}'
        )

        with patch.object(agent, "_call_claude_sdk", new_callable=AsyncMock) as mock_claude:
            mock_claude.return_value = mock_response

            input_data = {"task_description": "Implement user authentication system", "story": {}}

            result = await agent.process(input_data)

            assert "functional_requirements" in result
            assert "elaborated_at" in result


@pytest.mark.asyncio
class TestRequirementsValidation:
    """Test INVEST/SMART criteria validation."""

    async def test_validate_requirements_all_criteria_pass(
        self, isolated_agilevv_dir: TestPathConfig
    ) -> None:
        """Test validation when all criteria pass."""
        sdk_config = SDKConfig(api_key="test-key")
        agent = RequirementsAnalystAgent(path_config=isolated_agilevv_dir, sdk_config=sdk_config)

        requirements = {
            "id": "REQ-001",
            "original_story": {
                "title": "User Registration",
                "description": "User registration feature",
                "business_value": "Increase user engagement",
            },
            "functional_requirements": [
                {"id": "FR-001", "description": "User can register with email"},
                {"id": "FR-002", "description": "User receives confirmation email"},
            ],
            "non_functional_requirements": [
                {"id": "NFR-001", "description": "Registration completes in < 3 seconds"},
                {"id": "NFR-002", "description": "Support 1000 concurrent users"},
            ],
            "acceptance_criteria": [
                {"id": "AC-001", "scenario": "User enters valid email and password"},
                {"id": "AC-002", "scenario": "User receives confirmation within 5 minutes"},
            ],
            "dependencies": ["Email service"],
        }

        validation = await agent.validate_requirements(requirements)

        assert validation["is_valid"] is True
        assert validation["overall_score"] > 0.8
        assert "invest_criteria" in validation
        assert "smart_criteria" in validation

    async def test_validate_requirements_missing_acceptance_criteria(
        self, isolated_agilevv_dir: TestPathConfig
    ) -> None:
        """Test validation when acceptance criteria are missing."""
        sdk_config = SDKConfig(api_key="test-key")
        agent = RequirementsAnalystAgent(path_config=isolated_agilevv_dir, sdk_config=sdk_config)

        requirements = {
            "id": "REQ-002",
            "original_story": {"title": "Feature", "description": "Test feature"},
            "functional_requirements": [{"id": "FR-001", "description": "Some requirement"}],
            "acceptance_criteria": [],  # Missing
        }

        validation = await agent.validate_requirements(requirements)

        assert validation["is_valid"] is False
        assert validation["invest_criteria"]["testable"]["score"] == 0.0
        assert "Missing acceptance criteria" in validation["invest_criteria"]["testable"]["issues"]

    async def test_validate_requirements_too_many_dependencies(
        self, isolated_agilevv_dir: TestPathConfig
    ) -> None:
        """Test validation when there are too many dependencies."""
        sdk_config = SDKConfig(api_key="test-key")
        agent = RequirementsAnalystAgent(path_config=isolated_agilevv_dir, sdk_config=sdk_config)

        requirements = {
            "id": "REQ-003",
            "original_story": {"title": "Complex Feature"},
            "functional_requirements": [{"id": "FR-001", "description": "Requirement"}],
            "acceptance_criteria": [{"id": "AC-001", "scenario": "Test scenario"}],
            "dependencies": [
                "Service A",
                "Service B",
                "Service C",
                "Service D",
                "Service E",
            ],  # Too many
        }

        validation = await agent.validate_requirements(requirements)

        assert validation["invest_criteria"]["independent"]["score"] == 0.5
        assert "Too many dependencies" in validation["invest_criteria"]["independent"]["issues"][0]

    async def test_validate_requirements_story_too_large(
        self, isolated_agilevv_dir: TestPathConfig
    ) -> None:
        """Test validation when story is too large."""
        sdk_config = SDKConfig(api_key="test-key")
        agent = RequirementsAnalystAgent(path_config=isolated_agilevv_dir, sdk_config=sdk_config)

        # Create many requirements to simulate large story
        functional_reqs = [
            {"id": f"FR-{i:03d}", "description": f"Requirement {i}"} for i in range(8)
        ]
        nf_reqs = [{"id": f"NFR-{i:03d}", "description": f"NFR {i}"} for i in range(5)]

        requirements = {
            "id": "REQ-004",
            "original_story": {"title": "Large Feature"},
            "functional_requirements": functional_reqs,
            "non_functional_requirements": nf_reqs,
            "acceptance_criteria": [{"id": "AC-001", "scenario": "Test"}],
        }

        validation = await agent.validate_requirements(requirements)

        assert validation["invest_criteria"]["small"]["score"] == 0.4
        assert "too large" in validation["invest_criteria"]["small"]["issues"][0]

    async def test_validate_requirements_insufficient_detail(
        self, isolated_agilevv_dir: TestPathConfig
    ) -> None:
        """Test validation when requirements lack sufficient detail."""
        sdk_config = SDKConfig(api_key="test-key")
        agent = RequirementsAnalystAgent(path_config=isolated_agilevv_dir, sdk_config=sdk_config)

        requirements = {
            "id": "REQ-005",
            "original_story": {"title": "Minimal Feature"},
            "functional_requirements": [],  # No functional requirements
            "acceptance_criteria": [{"id": "AC-001", "scenario": "Test"}],
        }

        validation = await agent.validate_requirements(requirements)

        assert validation["invest_criteria"]["estimable"]["score"] == 0.2
        assert validation["smart_criteria"]["specific"]["score"] == 0.2

    async def test_validate_requirements_error_handling(
        self, isolated_agilevv_dir: TestPathConfig
    ) -> None:
        """Test validation error handling."""
        sdk_config = SDKConfig(api_key="test-key")
        agent = RequirementsAnalystAgent(path_config=isolated_agilevv_dir, sdk_config=sdk_config)

        # Invalid requirements (missing required fields)
        requirements = None

        validation = await agent.validate_requirements(requirements)

        assert validation["is_valid"] is False
        assert "error" in validation
        assert validation["overall_score"] == 0.0


@pytest.mark.asyncio
class TestBacklogIntegration:
    """Test backlog integration functionality."""

    async def test_update_backlog_new_story(self, isolated_agilevv_dir: TestPathConfig) -> None:
        """Test updating backlog with new story."""
        sdk_config = SDKConfig(api_key="test-key")
        agent = RequirementsAnalystAgent(path_config=isolated_agilevv_dir, sdk_config=sdk_config)

        requirements = {
            "id": "REQ-001",
            "original_story": {
                "id": "US-001",
                "title": "New Feature",
                "description": "A new feature for testing",
                "priority": "High",
            },
            "functional_requirements": [{"id": "FR-001", "description": "User can do something"}],
            "acceptance_criteria": [
                {"id": "AC-001", "scenario": "User performs action successfully"}
            ],
            "elaborated_at": datetime.now().isoformat(),
        }

        await agent._update_backlog(requirements)

        # Check that backlog was created and updated
        backlog_path = isolated_agilevv_dir.backlog_path
        assert backlog_path.exists()

        content = backlog_path.read_text()
        assert "REQ-001: New Feature" in content
        assert "A new feature for testing" in content
        assert "User can do something" in content

    async def test_update_backlog_existing_story(
        self, isolated_agilevv_dir: TestPathConfig
    ) -> None:
        """Test updating backlog with existing story (no duplicate)."""
        sdk_config = SDKConfig(api_key="test-key")
        agent = RequirementsAnalystAgent(path_config=isolated_agilevv_dir, sdk_config=sdk_config)

        # Create initial backlog content
        backlog_path = isolated_agilevv_dir.backlog_path
        backlog_path.parent.mkdir(parents=True, exist_ok=True)
        backlog_path.write_text(
            "# Product Backlog\n\n## REQ-001: Existing Feature\n\nSome content\n"
        )

        requirements = {
            "id": "REQ-001",
            "original_story": {"title": "Existing Feature", "description": "Already in backlog"},
        }

        await agent._update_backlog(requirements)

        content = backlog_path.read_text()
        # Should not duplicate - only one occurrence
        assert content.count("REQ-001: Existing Feature") == 1

    async def test_update_backlog_complex_requirements(
        self, isolated_agilevv_dir: TestPathConfig
    ) -> None:
        """Test updating backlog with complex requirements structure."""
        sdk_config = SDKConfig(api_key="test-key")
        agent = RequirementsAnalystAgent(path_config=isolated_agilevv_dir, sdk_config=sdk_config)

        requirements = {
            "id": "REQ-002",
            "original_story": {
                "title": "Complex Feature",
                "description": "Complex feature with multiple aspects",
                "priority": "Medium",
            },
            "functional_requirements": [
                {"id": "FR-001", "description": "First functional requirement"},
                {"id": "FR-002", "description": "Second functional requirement"},
            ],
            "non_functional_requirements": [
                {"id": "NFR-001", "description": "Performance requirement"}
            ],
            "acceptance_criteria": [
                {"id": "AC-001", "scenario": "First scenario"},
                {"id": "AC-002", "scenario": "Second scenario"},
            ],
            "dependencies": [
                {"type": "service", "description": "External API service"},
                {"type": "data", "description": "User database"},
            ],
        }

        await agent._update_backlog(requirements)

        content = isolated_agilevv_dir.backlog_path.read_text()
        assert "Complex Feature" in content
        assert "First functional requirement" in content
        assert "Performance requirement" in content
        assert "First scenario" in content
        assert "External API service" in content

    async def test_update_backlog_error_handling(
        self, isolated_agilevv_dir: TestPathConfig
    ) -> None:
        """Test backlog update error handling."""
        sdk_config = SDKConfig(api_key="test-key")
        agent = RequirementsAnalystAgent(path_config=isolated_agilevv_dir, sdk_config=sdk_config)

        # Test with read-only directory
        with patch.object(Path, "write_text", side_effect=PermissionError("Read-only")):
            requirements = {"id": "REQ-003", "original_story": {"title": "Test"}}

            # Should not raise exception, just log error
            await agent._update_backlog(requirements)


@pytest.mark.asyncio
class TestRequirementsParsingAndStoryScoring:
    """Test requirements parsing and story quality scoring."""

    async def test_parse_requirements_response_valid_json(
        self, isolated_agilevv_dir: TestPathConfig
    ) -> None:
        """Test parsing valid JSON response."""
        sdk_config = SDKConfig(api_key="test-key")
        agent = RequirementsAnalystAgent(path_config=isolated_agilevv_dir, sdk_config=sdk_config)

        json_response = json.dumps(
            {
                "functional_requirements": [{"id": "FR-001", "description": "Test requirement"}],
                "acceptance_criteria": [{"id": "AC-001", "scenario": "Test scenario"}],
            }
        )

        story = {"id": "US-001", "title": "Test Story"}

        result = await agent._parse_requirements_response(json_response, story)

        assert result["id"] == "US-001"
        assert "functional_requirements" in result
        assert "original_story" in result
        assert "elaborated_at" in result
        assert result["agent"] == "requirements_analyst"

    async def test_parse_requirements_response_invalid_json(
        self, isolated_agilevv_dir: TestPathConfig
    ) -> None:
        """Test parsing invalid JSON response."""
        sdk_config = SDKConfig(api_key="test-key")
        agent = RequirementsAnalystAgent(path_config=isolated_agilevv_dir, sdk_config=sdk_config)

        text_response = "This is not JSON format response from Claude."
        story = {"id": "US-002", "title": "Test Story 2"}

        result = await agent._parse_requirements_response(text_response, story)

        assert result["id"] == "US-002"
        assert result["response_text"] == text_response
        assert "functional_requirements" in result
        assert isinstance(result["functional_requirements"], list)
        assert len(result["functional_requirements"]) == 0

    async def test_parse_requirements_response_malformed_json(
        self, isolated_agilevv_dir: TestPathConfig
    ) -> None:
        """Test parsing malformed JSON response."""
        sdk_config = SDKConfig(api_key="test-key")
        agent = RequirementsAnalystAgent(path_config=isolated_agilevv_dir, sdk_config=sdk_config)

        malformed_json = (
            '{"functional_requirements": [{"id": "FR-001", "description": "Test"'  # Missing closing
        )
        story = {"id": "US-003", "title": "Test Story 3"}

        result = await agent._parse_requirements_response(malformed_json, story)

        assert result["id"] == "US-003"
        assert "parse_error" in result
        assert result["response_text"] == malformed_json

    async def test_story_quality_scoring_high_quality(
        self, isolated_agilevv_dir: TestPathConfig
    ) -> None:
        """Test story quality scoring for high-quality requirements."""
        sdk_config = SDKConfig(api_key="test-key")
        agent = RequirementsAnalystAgent(path_config=isolated_agilevv_dir, sdk_config=sdk_config)

        high_quality_requirements = {
            "id": "REQ-001",
            "original_story": {
                "title": "High Quality Story",
                "description": "Well-defined story with clear business value",
                "business_value": "Increases user satisfaction by 25%",
            },
            "functional_requirements": [
                {"id": "FR-001", "description": "User can perform primary action efficiently"},
                {"id": "FR-002", "description": "System provides immediate feedback to user"},
            ],
            "non_functional_requirements": [
                {"id": "NFR-001", "description": "Response time must be under 2 seconds"},
                {"id": "NFR-002", "description": "Must support 10,000 concurrent users"},
            ],
            "acceptance_criteria": [
                {
                    "id": "AC-001",
                    "scenario": "Given valid input, user completes action successfully",
                },
                {
                    "id": "AC-002",
                    "scenario": "System displays confirmation message within 1 second",
                },
            ],
            "dependencies": ["Authentication service"],
        }

        validation = await agent.validate_requirements(high_quality_requirements)

        assert validation["overall_score"] > 0.8
        assert validation["is_valid"] is True
        assert validation["invest_criteria"]["testable"]["score"] > 0.5
        assert validation["smart_criteria"]["measurable"]["score"] > 0.5

    async def test_story_quality_scoring_low_quality(
        self, isolated_agilevv_dir: TestPathConfig
    ) -> None:
        """Test story quality scoring for low-quality requirements."""
        sdk_config = SDKConfig(api_key="test-key")
        agent = RequirementsAnalystAgent(path_config=isolated_agilevv_dir, sdk_config=sdk_config)

        low_quality_requirements = {
            "id": "REQ-002",
            "original_story": {
                "title": "Vague Story",
                "description": "Do something",  # Very vague
            },
            "functional_requirements": [],  # Empty
            "acceptance_criteria": [],  # Missing
            "dependencies": ["A", "B", "C", "D", "E", "F"],  # Too many
        }

        validation = await agent.validate_requirements(low_quality_requirements)

        assert validation["overall_score"] < 0.6
        assert validation["is_valid"] is False
        assert len(validation["recommendations"]) > 0


@pytest.mark.asyncio
class TestRequirementsAnalystIntegration:
    """Test Requirements Analyst integration with SDK and templates."""

    async def test_sdk_integration_with_requirements_prompt(
        self, isolated_agilevv_dir: TestPathConfig
    ) -> None:
        """Test SDK integration with requirements analysis prompt."""
        sdk_config = SDKConfig(api_key="test-key")
        agent = RequirementsAnalystAgent(
            path_config=isolated_agilevv_dir, sdk_config=sdk_config, mock_mode=True
        )

        mock_response = json.dumps(
            {
                "functional_requirements": [
                    {"id": "FR-001", "description": "SDK integration test"}
                ],
                "acceptance_criteria": [{"id": "AC-001", "scenario": "SDK responds correctly"}],
            }
        )

        with patch.object(agent, "_call_claude_sdk", new_callable=AsyncMock) as mock_sdk:
            mock_sdk.return_value = mock_response

            input_data = {
                "story": {
                    "id": "US-SDK-001",
                    "title": "SDK Integration Test",
                    "description": "Test SDK integration",
                }
            }

            result = await agent.process(input_data)

            # Verify SDK was called
            mock_sdk.assert_called_once()

            # Verify result structure
            assert result["id"] == "US-SDK-001"
            assert "functional_requirements" in result
            assert result["functional_requirements"][0]["description"] == "SDK integration test"

    async def test_template_loading_and_context_building(
        self, isolated_agilevv_dir: TestPathConfig
    ) -> None:
        """Test template loading and context building for prompts."""
        sdk_config = SDKConfig(api_key="test-key")
        agent = RequirementsAnalystAgent(
            path_config=isolated_agilevv_dir, sdk_config=sdk_config, mock_mode=True
        )

        mock_response = '{"functional_requirements": []}'

        with patch.object(agent, "load_prompt_template") as mock_template:
            mock_template.return_value = "Loaded template with context"

            with patch.object(agent, "_call_claude_sdk", new_callable=AsyncMock) as mock_sdk:
                mock_sdk.return_value = mock_response

                input_data = {
                    "story": {"id": "US-TEMPLATE-001", "title": "Template Test"},
                    "context": {"project_name": "TestProject", "sprint_number": 2},
                }

                await agent.process(input_data)

                # Verify template was loaded with correct context
                mock_template.assert_called_once()
                call_args = mock_template.call_args
                assert call_args[0][0] == "requirements"  # template name
                assert "project_name" in call_args[1]
                assert "sprint_number" in call_args[1]

    async def test_session_management_and_context_preservation(
        self, isolated_agilevv_dir: TestPathConfig
    ) -> None:
        """Test session management and context preservation across requests."""
        sdk_config = SDKConfig(api_key="test-key")
        agent = RequirementsAnalystAgent(
            path_config=isolated_agilevv_dir, sdk_config=sdk_config, mock_mode=True
        )

        # First request
        mock_response_1 = (
            '{"functional_requirements": [{"id": "FR-001", "description": "First requirement"}]}'
        )

        with patch.object(agent, "_call_claude_sdk", new_callable=AsyncMock) as mock_sdk:
            mock_sdk.return_value = mock_response_1

            input_data_1 = {"story": {"id": "US-SESSION-001", "title": "First Story"}}

            result_1 = await agent.process(input_data_1)

            # Second request
            mock_response_2 = '{"functional_requirements": [{"id": "FR-002", "description": "Second requirement"}]}'
            mock_sdk.return_value = mock_response_2

            input_data_2 = {"story": {"id": "US-SESSION-002", "title": "Second Story"}}

            result_2 = await agent.process(input_data_2)

            # Verify both requests were processed independently
            assert result_1["id"] == "US-SESSION-001"
            assert result_2["id"] == "US-SESSION-002"
            assert mock_sdk.call_count == 2

    async def test_error_recovery_and_fallback_behavior(
        self, isolated_agilevv_dir: TestPathConfig
    ) -> None:
        """Test error recovery and fallback behavior."""
        sdk_config = SDKConfig(api_key="test-key")
        agent = RequirementsAnalystAgent(
            path_config=isolated_agilevv_dir, sdk_config=sdk_config, mock_mode=True
        )

        # Test various error scenarios
        error_scenarios = [
            ("Network timeout", Exception("Network timeout")),
            ("Rate limit", Exception("Rate limit exceeded")),
            ("Invalid response", Exception("Invalid response format")),
        ]

        for scenario_name, exception in error_scenarios:
            with patch.object(agent, "_call_claude_sdk", new_callable=AsyncMock) as mock_sdk:
                mock_sdk.side_effect = exception

                input_data = {
                    "story": {
                        "id": f"US-ERROR-{scenario_name}",
                        "title": f"Error Test {scenario_name}",
                    }
                }

                with pytest.raises(Exception, match=".*"):
                    await agent.process(input_data)

                # Verify SDK was attempted
                mock_sdk.assert_called_once()
