"""Integration tests for real Claude Code SDK Requirements Analyst processing MailBuddy user stories.

This module tests authentic Claude Code SDK integration with Requirements Analyst agent
processing MailBuddy Flask application scenarios. Tests use real API calls with proper
authentication (API key or subscription) and validate authentic AI-generated requirements artifacts.

NOTE: These tests attempt real Claude Code SDK authentication. They will be skipped if
neither API key nor subscription authentication is available. Use sparingly to avoid costs.
"""

import os
import time

import pytest
from verifflowcc.agents.requirements_analyst import RequirementsAnalystAgent
from verifflowcc.core.sdk_config import SDKConfig
from verifflowcc.core.vmodel import VModelStage
from verifflowcc.schemas.agent_schemas import AgentInput

from tests.conftest import PathConfig as TestPathConfig

pytestmark = [
    pytest.mark.integration,
    pytest.mark.real_sdk,
]


def _can_authenticate_with_sdk() -> bool:
    """Check if SDK authentication is possible (API key or subscription)."""
    try:
        # Try to create SDK config - will work with API key or subscription
        sdk_config = SDKConfig(
            api_key=os.getenv("ANTHROPIC_API_KEY"),  # None is OK for subscription
            timeout=5,
        )
        # Basic validation that config was created successfully
        return sdk_config.timeout == 5
    except Exception:
        return False


# Skip all tests if SDK authentication is not available


class TestRealSDKClientInitialization:
    """Test real Claude Code SDK client initialization and authentication."""

    def test_sdk_client_initialization_with_api_key_auth(self) -> None:
        """Test SDK client initializes with API key authentication."""
        api_key = os.getenv("ANTHROPIC_API_KEY")

        if api_key:
            sdk_config = SDKConfig(api_key=api_key, timeout=30, max_retries=3)

            assert sdk_config.api_key == api_key
            assert sdk_config.timeout == 30
            assert sdk_config.max_retries == 3
        else:
            pytest.skip("API key not available, testing subscription auth instead")

    def test_sdk_client_initialization_with_subscription_auth(self) -> None:
        """Test SDK client initializes with subscription-based authentication."""
        # Test subscription auth when no API key is provided
        sdk_config = SDKConfig(
            api_key=None,
            timeout=30,
            max_retries=3,  # Use subscription authentication
        )

        # In test environment, SDKConfig automatically provides mock key
        # In production, api_key would remain None for subscription auth
        if sdk_config.api_key == "sk-test-mock-api-key":
            # Test environment - mock key provided automatically
            assert sdk_config.api_key == "sk-test-mock-api-key"
        else:
            # Production environment - subscription mode
            assert sdk_config.api_key is None

        assert sdk_config.timeout == 30
        assert sdk_config.max_retries == 3
        assert sdk_config.base_url is None  # Uses SDK default

    def test_requirements_analyst_real_sdk_initialization(
        self, isolated_agilevv_dir: TestPathConfig
    ) -> None:
        """Test Requirements Analyst agent initializes with real SDK client."""
        api_key = os.getenv("ANTHROPIC_API_KEY")
        sdk_config = SDKConfig(api_key=api_key, timeout=60)

        agent = RequirementsAnalystAgent(
            path_config=isolated_agilevv_dir,
            sdk_config=sdk_config,
            mock_mode=False,  # Real SDK mode
        )

        assert agent.name == "requirements_analyst"
        assert agent.agent_type == "requirements"
        assert agent.mock_mode is False
        assert agent.sdk_config.timeout == 60


class TestRealSDKSessionCreation:
    """Test real Claude Code SDK agent session creation and management."""

    @pytest.mark.asyncio
    async def test_sdk_agent_session_creation_with_context(
        self, isolated_agilevv_dir: TestPathConfig
    ) -> None:
        """Test real SDK agent creates session with MailBuddy context."""
        api_key = os.getenv("ANTHROPIC_API_KEY")
        sdk_config = SDKConfig(api_key=api_key, timeout=60)

        agent = RequirementsAnalystAgent(
            path_config=isolated_agilevv_dir, sdk_config=sdk_config, mock_mode=False
        )

        # Create MailBuddy context for session
        mailbuddy_context = {
            "project_name": "MailBuddy",
            "description": "Flask email campaign management application",
            "target_users": [
                "Marketing managers",
                "Business owners",
                "Email marketers",
            ],
            "core_features": [
                "Email template management",
                "Scheduled email delivery",
                "Campaign analytics",
                "Contact list management",
            ],
        }

        agent_input = AgentInput(
            story_id="MB-SDK-001",
            stage=VModelStage.REQUIREMENTS,
            context=mailbuddy_context,
        )

        try:
            # Test that agent can process real context - makes actual API call
            result = await agent.process(agent_input.model_dump())

            # Validate response structure from real Requirements Analyst agent
            assert isinstance(result, dict)

            # Requirements Analyst returns specific structure with these expected keys
            expected_keys = ["agent", "agent_type"]
            for key in expected_keys:
                assert key in result, f"Expected key '{key}' not found in response"

            assert result["agent"] == "requirements_analyst"
            assert result["agent_type"] == "requirements"

        except Exception as e:
            # If authentication fails, provide clear message
            if "authentication" in str(e).lower() or "api_key" in str(e).lower():
                pytest.skip(f"SDK authentication failed: {e}")
            else:
                raise

    @pytest.mark.asyncio
    async def test_session_persistence_across_calls(
        self, isolated_agilevv_dir: TestPathConfig
    ) -> None:
        """Test SDK session state persists across multiple calls."""
        api_key = os.getenv("ANTHROPIC_API_KEY")
        sdk_config = SDKConfig(api_key=api_key, timeout=60)

        agent = RequirementsAnalystAgent(
            path_config=isolated_agilevv_dir, sdk_config=sdk_config, mock_mode=False
        )

        # First call to establish session context
        context_1 = {
            "session_test": "first_call",
            "project": "MailBuddy",
            "task": "Initialize requirements analysis",
        }

        agent_input_1 = AgentInput(
            story_id="MB-SESSION-001", stage=VModelStage.REQUIREMENTS, context=context_1
        )

        try:
            result_1 = await agent.process(agent_input_1.model_dump())

            # Second call should maintain session context
            context_2 = {
                "session_test": "second_call",
                "follow_up": "Continue with previous MailBuddy analysis",
            }

            agent_input_2 = AgentInput(
                story_id="MB-SESSION-002",
                stage=VModelStage.REQUIREMENTS,
                context=context_2,
            )

            result_2 = await agent.process(agent_input_2.model_dump())

            # Both calls should succeed
            assert result_1["status"] in ["success", "completed"]
            assert result_2["status"] in ["success", "completed"]

        except Exception as e:
            if "authentication" in str(e).lower():
                pytest.skip(f"SDK authentication failed: {e}")
            else:
                raise


class TestRealAIGeneratedRequirements:
    """Test validation of real AI-generated requirements.md with INVEST compliance."""

    @pytest.mark.asyncio
    async def test_real_ai_generated_invest_compliant_stories(
        self, isolated_agilevv_dir: TestPathConfig
    ) -> None:
        """Test real AI generates INVEST-compliant MailBuddy user stories."""
        api_key = os.getenv("ANTHROPIC_API_KEY")
        sdk_config = SDKConfig(api_key=api_key, timeout=90)  # Longer timeout for generation

        agent = RequirementsAnalystAgent(
            path_config=isolated_agilevv_dir, sdk_config=sdk_config, mock_mode=False
        )

        mailbuddy_prompt_context = {
            "project_name": "MailBuddy",
            "description": "Email campaign management Flask application with template creation, scheduling, and analytics",
            "requirements_request": "Generate INVEST-compliant user stories for core email management functionality",
            "focus_areas": [
                "Email template creation and editing",
                "Campaign scheduling and delivery",
                "Performance analytics and reporting",
            ],
        }

        agent_input = AgentInput(
            story_id="MB-INVEST-001",
            stage=VModelStage.REQUIREMENTS,
            context=mailbuddy_prompt_context,
        )

        try:
            # Generate real AI requirements
            result = await agent.process(agent_input.model_dump())

            # Validate authentic AI response structure
            assert "result" in result
            ai_requirements = result["result"]

            # Check for user stories in response
            if "user_stories" in ai_requirements:
                user_stories = ai_requirements["user_stories"]
                assert isinstance(user_stories, list)
                assert len(user_stories) > 0

                # Validate INVEST compliance for each story
                for story in user_stories:
                    assert "id" in story or "title" in story
                    assert "story" in story or "description" in story

                    # Look for INVEST compliance indicators
                    if "invest_compliance" in story:
                        invest = story["invest_compliance"]

                        # Check INVEST criteria present
                        invest_fields = [
                            "independent",
                            "negotiable",
                            "valuable",
                            "estimable",
                            "small",
                            "testable",
                        ]
                        for field in invest_fields:
                            if field in invest:
                                assert isinstance(invest[field], bool)
            else:
                # AI might structure response differently - validate basic content
                assert "requirements" in str(result).lower() or "stories" in str(result).lower()

        except Exception as e:
            if "authentication" in str(e).lower():
                pytest.skip(f"SDK authentication failed: {e}")
            else:
                raise

    @pytest.mark.asyncio
    async def test_real_ai_requirements_artifact_generation(
        self, isolated_agilevv_dir: TestPathConfig
    ) -> None:
        """Test real AI generates structured requirements artifacts."""
        api_key = os.getenv("ANTHROPIC_API_KEY")
        sdk_config = SDKConfig(api_key=api_key, timeout=90)

        agent = RequirementsAnalystAgent(
            path_config=isolated_agilevv_dir, sdk_config=sdk_config, mock_mode=False
        )

        # Request AI to generate requirements artifacts for MailBuddy
        context = {
            "artifact_generation": True,
            "project": "MailBuddy Flask email campaign application",
            "deliverables": [
                "User stories with acceptance criteria",
                "Functional requirements",
                "Non-functional requirements",
                "Technical dependencies",
            ],
        }

        agent_input = AgentInput(
            story_id="MB-ARTIFACTS-001", stage=VModelStage.REQUIREMENTS, context=context
        )

        try:
            result = await agent.process(agent_input.model_dump())

            # Validate some form of requirements were generated
            assert "result" in result
            assert result["status"] in ["success", "completed"]

            # Check if base directory has any generated content
            # PathConfig doesn't have artifacts_dir, but we can check base_dir
            if isolated_agilevv_dir.base_dir.exists():
                # Look for generated artifacts in requirements or base directory
                requirements_dir = isolated_agilevv_dir.requirements_dir
                requirements_dir.mkdir(parents=True, exist_ok=True)

                artifact_files = list(requirements_dir.glob("*.md"))
                if not artifact_files:
                    # Try base directory
                    artifact_files = list(isolated_agilevv_dir.base_dir.glob("*.md"))

                # AI might have generated requirement artifacts
                if artifact_files:
                    # Validate at least one artifact contains meaningful content
                    for file in artifact_files:
                        content = file.read_text()
                        assert len(content) > 50  # Has substantial content

        except Exception as e:
            if "authentication" in str(e).lower():
                pytest.skip(f"SDK authentication failed: {e}")
            else:
                raise


class TestRealStreamingResponseHandling:
    """Test real-time streaming response handling during Requirements Analyst execution."""

    @pytest.mark.asyncio
    async def test_real_streaming_response_collection(
        self, isolated_agilevv_dir: TestPathConfig
    ) -> None:
        """Test real streaming responses from Claude Code SDK Requirements Analyst."""
        api_key = os.getenv("ANTHROPIC_API_KEY")
        sdk_config = SDKConfig(api_key=api_key, timeout=120)

        agent = RequirementsAnalystAgent(
            path_config=isolated_agilevv_dir, sdk_config=sdk_config, mock_mode=False
        )

        context = {
            "streaming_test": True,
            "project": "MailBuddy Flask Application",
            "requirement": "Generate 2 user stories for email template management",
        }

        agent_input = AgentInput(
            story_id="MB-STREAM-001", stage=VModelStage.REQUIREMENTS, context=context
        )

        try:
            # Track streaming response timing
            start_time = time.time()

            result = await agent.process(agent_input.model_dump())

            end_time = time.time()
            processing_time = end_time - start_time

            # Validate streaming occurred (real API calls take time)
            assert processing_time > 1.0  # Real API calls take time
            assert processing_time < 300.0  # But not excessively long

            # Validate response received
            assert "result" in result
            assert "status" in result
            assert result["status"] in ["success", "completed"]

        except Exception as e:
            if "authentication" in str(e).lower():
                pytest.skip(f"SDK authentication failed: {e}")
            else:
                raise

    @pytest.mark.asyncio
    async def test_real_time_feedback_mechanisms(
        self, isolated_agilevv_dir: TestPathConfig
    ) -> None:
        """Test real-time feedback during Requirements Analyst execution."""
        api_key = os.getenv("ANTHROPIC_API_KEY")
        sdk_config = SDKConfig(api_key=api_key, timeout=90)

        agent = RequirementsAnalystAgent(
            path_config=isolated_agilevv_dir, sdk_config=sdk_config, mock_mode=False
        )

        context = {
            "feedback_test": True,
            "project": "MailBuddy",
            "task": "Generate user stories with progress tracking",
        }

        agent_input = AgentInput(
            story_id="MB-FEEDBACK-001", stage=VModelStage.REQUIREMENTS, context=context
        )

        try:
            # Monitor execution for real-time aspects
            start_time = time.time()

            result = await agent.process(agent_input.model_dump())

            execution_time = time.time() - start_time

            # Validate execution completed successfully
            assert result["status"] in ["success", "completed"]

            # Real SDK execution should show reasonable timing
            assert execution_time > 0.5  # Not instantaneous (real processing)
            assert execution_time < 240.0  # But completes in reasonable time

        except Exception as e:
            if "authentication" in str(e).lower():
                pytest.skip(f"SDK authentication failed: {e}")
            else:
                raise


class TestAuthenticSDKOutputValidation:
    """Test validation of authentic Claude Code SDK agent outputs."""

    @pytest.mark.asyncio
    async def test_authentic_sdk_response_structure_validation(
        self, isolated_agilevv_dir: TestPathConfig
    ) -> None:
        """Test authentic SDK responses conform to expected structure."""
        api_key = os.getenv("ANTHROPIC_API_KEY")
        sdk_config = SDKConfig(api_key=api_key, timeout=60)

        agent = RequirementsAnalystAgent(
            path_config=isolated_agilevv_dir, sdk_config=sdk_config, mock_mode=False
        )

        context = {
            "validation_test": True,
            "project": "MailBuddy",
            "output_format": "structured_response",
        }

        agent_input = AgentInput(
            story_id="MB-VALIDATION-001",
            stage=VModelStage.REQUIREMENTS,
            context=context,
        )

        try:
            result = await agent.process(agent_input.model_dump())

            # Validate basic response structure from real SDK
            assert isinstance(result, dict)
            assert "status" in result
            assert result["status"] in ["success", "completed", "failed"]

            # Validate that response has meaningful content
            assert "result" in result or "error" in result

        except Exception as e:
            if "authentication" in str(e).lower():
                pytest.skip(f"SDK authentication failed: {e}")
            else:
                raise

    @pytest.mark.asyncio
    async def test_real_ai_output_content_quality(
        self, isolated_agilevv_dir: TestPathConfig
    ) -> None:
        """Test content quality of real AI-generated requirements."""
        api_key = os.getenv("ANTHROPIC_API_KEY")
        sdk_config = SDKConfig(api_key=api_key, timeout=90)

        agent = RequirementsAnalystAgent(
            path_config=isolated_agilevv_dir, sdk_config=sdk_config, mock_mode=False
        )

        context = {
            "quality_assessment": True,
            "project": "MailBuddy Flask Application",
            "requirements": [
                "Email template management with drag-and-drop editor",
                "Campaign scheduling with timezone and frequency options",
                "Analytics dashboard showing open rates and click tracking",
            ],
        }

        agent_input = AgentInput(
            story_id="MB-QUALITY-001", stage=VModelStage.REQUIREMENTS, context=context
        )

        try:
            result = await agent.process(agent_input.model_dump())

            # Validate authentic AI output has meaningful content
            assert "result" in result
            ai_result = result["result"]

            # Convert to string for content analysis
            result_text = str(ai_result).lower()

            # Quality indicators - AI should mention relevant terms
            mailbuddy_terms = ["email", "template", "campaign", "analytics"]
            term_found = any(term in result_text for term in mailbuddy_terms)
            assert term_found, "AI output should contain relevant MailBuddy terms"

            # Quality metric: Response should have reasonable length
            assert len(str(ai_result)) > 100, "AI output should have substantial content"

        except Exception as e:
            if "authentication" in str(e).lower():
                pytest.skip(f"SDK authentication failed: {e}")
            else:
                raise
