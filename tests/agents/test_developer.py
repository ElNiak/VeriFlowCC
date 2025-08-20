"""Tests for DeveloperAgent (Coding stage agent).

This module tests the DeveloperAgent functionality including feature implementation,
code generation, and implementation reporting.

NOTE: Mock infrastructure has been removed. Tests requiring SDK calls are skipped
and will be replaced with real SDK integration tests.
"""

import json
from pathlib import Path
from typing import Any

import pytest
from verifflowcc.agents.developer import DeveloperAgent
from verifflowcc.core.vmodel import VModelStage
from verifflowcc.schemas.agent_schemas import ImplementationInput, ImplementationOutput


@pytest.fixture
def sample_implementation_input() -> dict[str, Any]:
    """Fixture providing sample implementation input data."""
    return {
        "story_id": "US-001",
        "stage": VModelStage.CODING,
        "context": {"sprint": 1, "priority": "high"},
        "design_artifacts": {
            "architecture_diagram": "user_auth_flow.puml",
            "component_specifications": {
                "UserService": {
                    "methods": ["login", "logout"],
                    "dependencies": ["Database"],
                },
                "AuthService": {"methods": ["validate", "generateToken"]},
            },
            "interface_contracts": {"IUserRepository": {"methods": ["findById", "save"]}},
        },
    }


class TestDeveloperAgentInitialization:
    """Test DeveloperAgent initialization and configuration."""

    def test_developer_agent_initialization(self, isolated_agilevv_dir: Any) -> None:
        """Test DeveloperAgent initializes correctly."""
        agent = DeveloperAgent(name="developer", path_config=isolated_agilevv_dir)

        assert agent.name == "developer"
        assert agent.path_config == isolated_agilevv_dir
        assert agent.agent_type == "developer"

    def test_developer_agent_custom_configuration(self, isolated_agilevv_dir: Any) -> None:
        """Test DeveloperAgent with custom configuration."""
        agent = DeveloperAgent(
            name="custom_developer",
            path_config=isolated_agilevv_dir,
        )

        assert agent.name == "custom_developer"
        assert agent.agent_type == "developer"

    def test_developer_agent_initialization_mock_mode(self, isolated_agilevv_dir: Any) -> None:
        """Test DeveloperAgent initialization in mock mode."""
        agent = DeveloperAgent(path_config=isolated_agilevv_dir, mock_mode=True)

        assert agent.mock_mode is True
        assert agent.agent_type == "developer"


class TestDeveloperAgentInputValidation:
    """Test DeveloperAgent input validation and processing."""

    def test_implementation_input_validation(self, isolated_agilevv_dir: Any) -> None:
        """Test that DeveloperAgent validates ImplementationInput correctly."""
        # Instantiate agent to verify it can be created with valid config
        DeveloperAgent(path_config=isolated_agilevv_dir)

        # Valid input
        valid_input = ImplementationInput(
            story_id="US-001",
            stage=VModelStage.CODING,
            context={"user_story": "As a user I want to login"},
            design_artifacts={
                "component_specifications": {
                    "UserService": {"methods": ["login"], "dependencies": ["Database"]}
                },
                "interface_contracts": {"IUserRepo": {"methods": ["findById", "save"]}},
            },
        )

        # Should not raise any validation errors
        assert valid_input.story_id == "US-001"
        assert valid_input.stage == VModelStage.CODING
        assert valid_input.design_artifacts is not None

    def test_implementation_input_missing_design_artifacts(self) -> None:
        """Test that ImplementationInput requires design artifacts."""
        with pytest.raises(ValueError, match="design_artifacts cannot be empty"):
            ImplementationInput(
                story_id="US-001",
                stage=VModelStage.CODING,
                context={},
                design_artifacts={},
            )


class TestDeveloperAgentArtifactManagement:
    """Test DeveloperAgent artifact creation and management."""

    def test_save_implementation_artifacts(self, isolated_agilevv_dir: Any) -> None:
        """Test saving implementation artifacts to correct subdirectory."""
        agent = DeveloperAgent(path_config=isolated_agilevv_dir, mock_mode=True)

        # Create implementation artifacts directory
        impl_dir = isolated_agilevv_dir.base_dir / "implementation"
        impl_dir.mkdir(parents=True, exist_ok=True)

        # Sample implementation data
        implementation_data = {
            "story_id": "US-001",
            "implementation_details": {
                "source_files": ["user_service.py", "auth_service.py"],
                "test_files": ["test_user_service.py"],
                "config_files": ["config.json"],
            },
            "implementation_report": {
                "features_implemented": ["User login", "Session management"],
                "technologies_used": ["Python", "FastAPI"],
                "lines_of_code": 150,
            },
        }

        # Save artifacts
        agent._save_implementation_artifacts("US-001", implementation_data)

        # Verify artifacts were saved
        artifact_file = impl_dir / "US-001.json"
        assert artifact_file.exists()

        # Verify artifact content
        saved_data = json.loads(artifact_file.read_text())
        assert saved_data["story_id"] == "US-001"
        assert "implementation_details" in saved_data
        assert "implementation_report" in saved_data


@pytest.mark.asyncio
class TestDeveloperAgentProcessing:
    """Test DeveloperAgent main processing functionality."""

    async def test_process_implementation_generation(self, isolated_agilevv_dir: Any) -> None:
        """Test the main process method for implementation generation."""
        # Note: This test now uses real SDK integration
        # Skip for now - to be replaced with real SDK integration test
        pytest.skip("Real SDK integration testing in progress")

    async def test_process_with_api_failure(self, isolated_agilevv_dir: Any) -> None:
        """Test process method handles API failures gracefully."""
        # Note: This test would now require real API failure conditions
        # Skip for now - to be replaced with integration test scenarios
        pytest.skip("Real API failure testing requires specific test conditions")

    async def test_process_partial_implementation(self, isolated_agilevv_dir: Any) -> None:
        """Test process method handles partial implementation scenarios."""
        # Note: This test would require specific SDK response conditions
        # Skip for now - to be replaced with integration test scenarios
        pytest.skip("Partial implementation testing requires specific SDK response conditions")


class TestDeveloperAgentIntegration:
    """Integration tests for DeveloperAgent with V-Model workflow."""

    def test_integration_with_architect_output(self, isolated_agilevv_dir: Any) -> None:
        """Test DeveloperAgent can process ArchitectAgent output."""
        # Instantiate agent to verify it can be created with valid config
        DeveloperAgent(path_config=isolated_agilevv_dir)

        # Simulate architect output
        architect_output = {
            "design_specifications": {
                "components": ["UserService", "AuthService"],
                "interfaces": ["IUserRepository"],
                "data_models": ["User", "Session"],
            },
            "architecture_updates": {
                "diagrams": ["user_auth_flow.puml"],
                "component_descriptions": {"UserService": "Manages user lifecycle"},
            },
            "interface_contracts": {
                "IUserRepository": {
                    "methods": ["findById", "save"],
                    "return_types": ["User", "boolean"],
                }
            },
        }

        # Should be able to create valid input from architect output
        ImplementationInput(
            story_id="US-001",
            stage=VModelStage.CODING,
            context={"architect_output": architect_output},
            design_artifacts=architect_output,
        )

        # Create expected output structure
        impl_output = ImplementationOutput(
            story_id="US-001",
            status="success",
            implementation_details={
                "source_files": ["user_service.py", "auth_service.py"],
                "test_files": ["test_user_service.py"],
                "config_files": ["app_config.json"],
            },
            implementation_report={
                "features_implemented": ["User registration", "Authentication"],
                "technologies_used": ["Python", "FastAPI", "SQLAlchemy"],
                "code_metrics": {"total_lines": 250, "complexity_score": 3.2},
            },
            artifacts={
                "source_code": ["UserService.py"],
                "tests": ["TestUserService.py"],
            },
            next_stage_ready=True,
        )
        assert impl_output.status == "success"
        assert impl_output.next_stage_ready is True
        assert impl_output.implementation_details is not None


class TestCodeQualityAndMetrics:
    """Test code quality analysis and metrics calculation."""

    def test_calculate_code_metrics_high_quality(self, isolated_agilevv_dir: Any) -> None:
        """Test code metrics calculation for high-quality implementation."""
        agent = DeveloperAgent(path_config=isolated_agilevv_dir, mock_mode=True)

        # High-quality code sample
        high_quality_code = {
            "source_files": [
                "user_service.py",  # Well-structured service
                "auth_service.py",  # Clean authentication logic
            ],
            "test_files": [
                "test_user_service.py",
                "test_auth_service.py",
            ],  # Good test coverage
            "config_files": ["settings.json"],
        }

        high_quality_metrics = agent._calculate_code_metrics(high_quality_code)

        # Low-quality code sample
        low_quality_code = {
            "source_files": ["monolith_service.py"],  # Single large file
            "test_files": [],  # No tests
            "config_files": [],
        }

        low_quality_metrics = agent._calculate_code_metrics(low_quality_code)

        # Verify metrics structure
        assert "total_lines" in high_quality_metrics
        assert "complexity_score" in high_quality_metrics
        assert "test_coverage" in high_quality_metrics
        assert "maintainability_index" in high_quality_metrics

        assert "total_lines" in low_quality_metrics
        assert "complexity_score" in low_quality_metrics
        assert "test_coverage" in low_quality_metrics
        assert "maintainability_index" in low_quality_metrics

        # Verify that high quality metrics have better values than low quality
        assert high_quality_metrics["complexity_score"] < low_quality_metrics["complexity_score"]
        assert high_quality_metrics["test_coverage"] > low_quality_metrics["test_coverage"]
        assert (
            high_quality_metrics["maintainability_index"]
            > low_quality_metrics["maintainability_index"]
        )


@pytest.mark.asyncio
class TestDeveloperAgentErrorRecovery:
    """Test DeveloperAgent error handling and recovery mechanisms."""

    async def test_retry_mechanism_for_compilation_errors(self, isolated_agilevv_dir: Any) -> None:
        """Test that agent retries when generated code has compilation errors."""
        # Note: This test would require real compilation error retry logic
        # Skip for now - to be replaced with integration test scenarios
        pytest.skip("Compilation error retry testing requires specific test conditions")

    async def test_validation_error_handling(self, isolated_agilevv_dir: Any) -> None:
        """Test handling of input validation errors."""
        agent = DeveloperAgent(path_config=isolated_agilevv_dir, mock_mode=True)

        # Invalid input that should trigger validation error
        invalid_input = {"story_id": "US-005", "stage": "INVALID_STAGE", "context": {}}

        result = await agent.process(invalid_input)

        assert result["status"] == "error"
        assert result["next_stage_ready"] is False
        assert "error" in result
        assert result["error"] and "validation" in result["error"].lower()


class TestDeveloperAgentPromptTemplates:
    """Test DeveloperAgent prompt template handling."""

    def test_load_implementation_prompt_template(self, isolated_agilevv_dir: Any) -> None:
        """Test loading implementation prompt template."""
        agent = DeveloperAgent(path_config=isolated_agilevv_dir, mock_mode=True)

        # Create mock template
        template_dir = Path("verifflowcc/prompts")
        template_dir.mkdir(parents=True, exist_ok=True)
        template_path = template_dir / "implementation.j2"
        template_content = """
        Implementation prompt for: {{ story_id }}
        Design artifacts: {{ design_artifacts }}
        Context: {{ context }}
        """
        template_path.write_text(template_content)

        try:
            # Load template
            template = agent.load_prompt_template("implementation.j2", {"story_id": "US-001"})

            # Verify template was loaded and rendered
            assert "Implementation prompt for: US-001" in template
        finally:
            # Cleanup
            if template_path.exists():
                template_path.unlink()
            if template_dir.exists() and not any(template_dir.iterdir()):
                template_dir.rmdir()

    def test_template_context_building(self, isolated_agilevv_dir: Any) -> None:
        """Test building template context from implementation input."""
        agent = DeveloperAgent(path_config=isolated_agilevv_dir, mock_mode=True)

        impl_input = ImplementationInput(
            story_id="US-001",
            stage=VModelStage.CODING,
            context={"sprint": 2, "team": "backend"},
            design_artifacts={
                "components": ["UserService", "AuthService"],
                "interfaces": ["IUserRepo"],
            },
        )

        # Build context
        context = agent._build_template_context(impl_input.model_dump())

        # Verify context structure
        assert context["story_id"] == "US-001"
        assert context["stage"] == VModelStage.CODING
        assert "design_artifacts" in context
        assert context["design_artifacts"]["components"] == [
            "UserService",
            "AuthService",
        ]
        assert context["context"]["sprint"] == 2


# Note: Additional SDK-dependent tests have been removed/skipped
# They will be replaced with real SDK integration tests in separate modules
@pytest.mark.asyncio
class TestSDKIntegrationPlaceholders:
    """Placeholder tests for SDK integration - to be replaced with real tests."""

    async def test_sdk_integration_basic(self, isolated_agilevv_dir: Any) -> None:
        """Test basic SDK integration."""
        # Skip - will be replaced with real SDK integration test
        pytest.skip("Real SDK integration testing in progress")

    async def test_streaming_response_handling(self, isolated_agilevv_dir: Any) -> None:
        """Test handling of streaming responses from SDK."""
        # Skip - will be replaced with real SDK integration test
        pytest.skip("Real SDK streaming integration testing in progress")

    async def test_large_codebase_generation(self, isolated_agilevv_dir: Any) -> None:
        """Test generation of large codebases with multiple files."""
        # Skip - will be replaced with real SDK integration test
        pytest.skip("Real SDK large codebase testing in progress")
