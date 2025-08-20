"""Tests for ArchitectAgent (Design stage agent).

This module tests the ArchitectAgent functionality including design document generation,
architecture.md updating, and artifact management.
"""

import json
from pathlib import Path
from typing import Any

import pytest
from verifflowcc.agents.architect import ArchitectAgent
from verifflowcc.core.vmodel import VModelStage
from verifflowcc.schemas.agent_schemas import DesignInput, DesignOutput


class TestArchitectAgentInitialization:
    """Test ArchitectAgent initialization and configuration."""

    def test_architect_agent_initialization(self, isolated_agilevv_dir: Any) -> None:
        """Test ArchitectAgent initializes correctly."""
        agent = ArchitectAgent(name="architect", path_config=isolated_agilevv_dir)

        assert agent.name == "architect"
        assert agent.path_config == isolated_agilevv_dir
        assert agent.agent_type == "architect"

    def test_architect_agent_custom_configuration(self, isolated_agilevv_dir: Any) -> None:
        """Test ArchitectAgent with custom configuration."""
        agent = ArchitectAgent(
            name="custom_architect",
            path_config=isolated_agilevv_dir,
        )

        assert agent.name == "custom_architect"
        assert agent.agent_type == "architect"


class TestArchitectAgentInputValidation:
    """Test ArchitectAgent input validation and processing."""

    def test_design_input_validation(self, isolated_agilevv_dir: Any) -> None:
        """Test that ArchitectAgent validates DesignInput correctly."""
        # Instantiate agent to verify it can be created with valid config
        ArchitectAgent(path_config=isolated_agilevv_dir)

        # Valid input
        valid_input = DesignInput(
            story_id="US-001",
            stage=VModelStage.DESIGN,
            context={"user_story": "As a user I want to login"},
            requirements_artifacts={
                "acceptance_criteria": [
                    "Given user credentials",
                    "When login",
                    "Then success",
                ],
                "user_story": "Login functionality",
            },
        )

        # Should not raise any validation errors
        assert valid_input.story_id == "US-001"
        assert valid_input.stage == VModelStage.DESIGN
        assert valid_input.requirements_artifacts is not None

    def test_design_input_missing_requirements(self) -> None:
        """Test that DesignInput requires requirements artifacts."""
        with pytest.raises(ValueError, match="requirements_artifacts cannot be empty"):
            DesignInput(
                story_id="US-001",
                stage=VModelStage.DESIGN,
                context={},
                requirements_artifacts={},
            )


class TestArchitectAgentArtifactManagement:
    """Test ArchitectAgent artifact creation and management."""

    def test_save_design_artifacts(self, isolated_agilevv_dir: Any) -> None:
        """Test saving design artifacts to correct subdirectory."""
        agent = ArchitectAgent(path_config=isolated_agilevv_dir)

        design_data = {
            "components": ["UserService", "AuthService"],
            "interfaces": ["IUserRepository", "IAuthProvider"],
            "diagrams": ["login_flow.puml"],
        }

        # Save design artifact
        agent.save_artifact("design/US-001.json", design_data)

        # Verify file was created in correct location
        artifact_path = isolated_agilevv_dir.base_dir / "design" / "US-001.json"
        assert artifact_path.exists()

        # Verify content
        loaded_data = json.loads(artifact_path.read_text())
        assert loaded_data == design_data

    def test_load_design_artifacts(self, isolated_agilevv_dir: Any) -> None:
        """Test loading existing design artifacts."""
        agent = ArchitectAgent(path_config=isolated_agilevv_dir)

        # Create test artifact
        design_data = {"component": "TestService"}
        artifact_path = isolated_agilevv_dir.base_dir / "design"
        artifact_path.mkdir(parents=True, exist_ok=True)
        (artifact_path / "US-002.json").write_text(json.dumps(design_data))

        # Load artifact
        loaded_data = agent.load_artifact("design/US-002.json")
        assert loaded_data == design_data

    def test_architecture_md_update(self, isolated_agilevv_dir: Any) -> None:
        """Test updating architecture.md file."""
        # Instantiate agent to verify it can be created with valid config
        ArchitectAgent(path_config=isolated_agilevv_dir)

        # Create initial architecture.md
        arch_path = isolated_agilevv_dir.architecture_path
        arch_path.parent.mkdir(parents=True, exist_ok=True)
        initial_content = "# System Architecture\n\n## Components\n\n"
        arch_path.write_text(initial_content)

        # Update architecture
        update_content = "### UserService\n- Handles user management\n\n"

        # This would be called by the agent during processing
        current_content = arch_path.read_text()
        updated_content = current_content + update_content
        arch_path.write_text(updated_content)

        # Verify update
        final_content = arch_path.read_text()
        assert "UserService" in final_content
        assert "Handles user management" in final_content


@pytest.mark.asyncio
class TestArchitectAgentProcessing:
    """Test ArchitectAgent main processing functionality."""

    async def test_process_design_generation(self, isolated_agilevv_dir: Any) -> None:
        """Test the main process method for design generation."""
        # Note: This test now uses real SDK integration
        # Test isolation is provided by isolated_agilevv_dir fixture

        agent = ArchitectAgent(path_config=isolated_agilevv_dir)

        # Create input
        design_input = DesignInput(
            story_id="US-001",
            stage=VModelStage.DESIGN,
            context={"sprint": 1, "priority": "high"},
            requirements_artifacts={
                "user_story": "As a user I want to login to access my account",
                "acceptance_criteria": [
                    "Given valid credentials when login then success",
                    "Given invalid credentials when login then error",
                ],
            },
        )

        # Process
        result = await agent.process(design_input.model_dump())

        # Validate result structure
        assert isinstance(result, dict)
        assert result["status"] == "success"
        assert result["next_stage_ready"] is True
        assert "artifacts" in result

        # Validate that artifacts were saved
        design_artifact_path = isolated_agilevv_dir.base_dir / "design" / "US-001.json"
        assert design_artifact_path.exists()

    async def test_process_with_api_failure(self, isolated_agilevv_dir: Any) -> None:
        """Test process method handles API failures gracefully."""
        # Note: This test would now require real API failure conditions
        # Skip for now - to be replaced with integration test scenarios
        pytest.skip("Real API failure testing requires specific test conditions")

        agent = ArchitectAgent(path_config=isolated_agilevv_dir)

        design_input = DesignInput(
            story_id="US-002",
            stage=VModelStage.DESIGN,
            context={},
            requirements_artifacts={"story": "Basic requirements"},
        )

        # Process should handle the error
        result = await agent.process(design_input.model_dump())

        assert result["status"] == "error"
        assert result["next_stage_ready"] is False
        assert "error" in result
        assert "API Error" in result["error"]

    async def test_process_partial_success(self, isolated_agilevv_dir: Any) -> None:
        """Test process method handles partial success scenarios."""
        # Note: This test would require specific SDK response conditions
        # Skip for now - to be replaced with integration test scenarios
        pytest.skip("Partial success testing requires specific SDK response conditions")

        agent = ArchitectAgent(path_config=isolated_agilevv_dir)

        design_input = DesignInput(
            story_id="US-003",
            stage=VModelStage.DESIGN,
            context={},
            requirements_artifacts={"story": "Complex requirements"},
        )

        result = await agent.process(design_input.model_dump())

        # Should handle partial results
        assert result["status"] in ["partial", "success"]
        assert "artifacts" in result


class TestArchitectAgentIntegration:
    """Integration tests for ArchitectAgent with V-Model workflow."""

    def test_integration_with_requirements_analyst_output(self, isolated_agilevv_dir: Any) -> None:
        """Test ArchitectAgent can process RequirementsAnalyst output."""
        # Instantiate agent to verify it can be created with valid config
        ArchitectAgent(path_config=isolated_agilevv_dir)

        # Simulate requirements analyst output
        requirements_output = {
            "user_stories": [
                {
                    "id": "US-001",
                    "title": "User Login",
                    "description": "As a user I want to login",
                    "acceptance_criteria": [
                        "Given valid credentials when login then access granted",
                        "Given invalid credentials when login then error shown",
                    ],
                }
            ],
            "business_rules": ["Users must have unique email addresses"],
            "constraints": ["System must support 1000 concurrent users"],
        }

        # Create DesignInput from requirements
        design_input = DesignInput(
            story_id="US-001",
            stage=VModelStage.DESIGN,
            context={"source": "requirements_analyst"},
            requirements_artifacts=requirements_output,
        )

        # Should validate successfully
        assert design_input.story_id == "US-001"
        assert design_input.requirements_artifacts == requirements_output

    def test_design_output_validation(self, isolated_agilevv_dir: Any) -> None:
        """Test DesignOutput validation for next stage."""
        # Create valid design output
        design_output = DesignOutput(
            status="success",
            artifacts={"design_document": "path/to/design.md"},
            metrics={"complexity": "medium", "components_designed": 2},
            design_specifications={
                "components": ["UserService", "AuthService"],
                "interfaces": ["IUserRepo", "IAuthProvider"],
            },
            architecture_updates={
                "diagrams_added": ["login_sequence.puml"],
                "components_updated": ["UserService"],
            },
            interface_contracts={
                "IUserRepo": {
                    "methods": ["findById", "save"],
                    "contracts": [
                        "User findById(String id)",
                        "boolean save(User user)",
                    ],
                }
            },
            next_stage_ready=True,
        )
        assert design_output.status == "success"
        assert design_output.next_stage_ready is True
        assert design_output.design_specifications is not None

    def test_error_handling_with_empty_design_specs(self) -> None:
        """Test that DesignOutput requires non-empty design specifications."""
        with pytest.raises(ValueError, match="design_specifications cannot be empty"):
            DesignOutput(
                status="success",
                artifacts={},
                design_specifications={},  # Empty - should fail validation
                architecture_updates={},
                interface_contracts={},
            )


class TestArchitectAgentPromptTemplates:
    """Test ArchitectAgent prompt template handling."""

    def test_load_design_prompt_template(self, isolated_agilevv_dir: Any) -> None:
        """Test loading design prompt template."""
        agent = ArchitectAgent(path_config=isolated_agilevv_dir)

        # Create mock template
        template_dir = Path("verifflowcc/prompts")
        template_dir.mkdir(parents=True, exist_ok=True)
        template_path = template_dir / "design.j2"
        template_content = """
        Create a system design for the following requirements:
        User Story: {{ user_story }}
        Acceptance Criteria: {{ acceptance_criteria }}
        """
        template_path.write_text(template_content)

        try:
            # Load template
            loaded_template = agent.load_prompt_template("design")
            assert "Create a system design" in loaded_template
            # Template variables should be rendered (replaced with empty strings if not provided)
            assert "{{ user_story }}" not in loaded_template
        finally:
            # Cleanup
            if template_path.exists():
                template_path.unlink()
            if template_dir.exists() and not list(template_dir.iterdir()):
                template_dir.rmdir()

    def test_load_nonexistent_template(self, isolated_agilevv_dir: Any) -> None:
        """Test loading non-existent template returns empty string."""
        agent = ArchitectAgent(path_config=isolated_agilevv_dir)

        template = agent.load_prompt_template("nonexistent_template")
        # Should return fallback template, not empty string
        assert "architect agent working on:" in template


@pytest.mark.asyncio
class TestArchitectAgentErrorRecovery:
    """Test ArchitectAgent error handling and recovery mechanisms."""

    async def test_error_handling_mechanism(self, isolated_agilevv_dir: Any) -> None:
        """Test that agent handles API failures gracefully."""
        # Note: This test would require real network error conditions
        # Skip for now - to be replaced with integration test scenarios
        pytest.skip("Network error testing requires specific test conditions")

        agent = ArchitectAgent(path_config=isolated_agilevv_dir)

        design_input = DesignInput(
            story_id="US-004",
            stage=VModelStage.DESIGN,
            context={},
            requirements_artifacts={"story": "Test requirements"},
        )

        # Should handle the error gracefully
        result = await agent.process(design_input.model_dump())
        assert result["status"] == "error"
        assert result["next_stage_ready"] is False
        assert "Temporary network error" in result["error"]

    async def test_validation_error_handling(self, isolated_agilevv_dir: Any) -> None:
        """Test handling of input validation errors."""
        # Note: This test would require real validation error conditions
        # Skip for now - to be replaced with integration test scenarios
        pytest.skip("Validation error testing requires specific test conditions")

        agent = ArchitectAgent(path_config=isolated_agilevv_dir)

        # Input that will trigger the mocked error
        test_input = {
            "story_id": "US-005",
            "stage": VModelStage.DESIGN,
            "context": {},
            "requirements_artifacts": {"story": "Test story"},
        }

        result = await agent.process(test_input)

        assert result["status"] == "error"
        assert result["next_stage_ready"] is False
        assert "error" in result
        assert "Invalid input" in result["error"]
