"""Tests for agent data schemas.

This module tests the Pydantic schemas used for agent input/output validation.
"""

import pytest
from pydantic import ValidationError
from verifflowcc.core.orchestrator import VModelStage
from verifflowcc.schemas.agent_schemas import (
    AgentInput,
    AgentOutput,
    DesignInput,
    DesignOutput,
    ImplementationInput,
    ImplementationOutput,
    IntegrationInput,
    IntegrationOutput,
    TestingInput,
    TestingOutput,
)


class TestBaseAgentSchemas:
    """Test base AgentInput and AgentOutput schemas."""

    def test_agent_input_valid_data(self):
        """Test AgentInput with valid data."""
        data = {
            "story_id": "US-001",
            "stage": VModelStage.REQUIREMENTS,
            "context": {"key": "value"},
            "previous_artifacts": {"requirements": "data"},
        }

        agent_input = AgentInput(**data)

        assert agent_input.story_id == "US-001"
        assert agent_input.stage == VModelStage.REQUIREMENTS
        assert agent_input.context == {"key": "value"}
        assert agent_input.previous_artifacts == {"requirements": "data"}

    def test_agent_input_minimal_data(self):
        """Test AgentInput with minimal required data."""
        data = {"story_id": "US-002", "stage": VModelStage.DESIGN, "context": {}}

        agent_input = AgentInput(**data)

        assert agent_input.story_id == "US-002"
        assert agent_input.stage == VModelStage.DESIGN
        assert agent_input.context == {}
        assert agent_input.previous_artifacts == {}

    def test_agent_input_missing_required_fields(self):
        """Test AgentInput validation with missing required fields."""
        with pytest.raises(ValidationError) as exc_info:
            AgentInput(stage=VModelStage.CODING, context={})

        assert "story_id" in str(exc_info.value)

    def test_agent_input_invalid_stage(self):
        """Test AgentInput with invalid stage value."""
        with pytest.raises(ValidationError):
            AgentInput(story_id="US-003", stage="INVALID_STAGE", context={})

    def test_agent_output_valid_data(self):
        """Test AgentOutput with valid data."""
        data = {
            "status": "success",
            "artifacts": {"design": "spec"},
            "metrics": {"time": 300},
            "next_stage_ready": True,
            "errors": [],
        }

        agent_output = AgentOutput(**data)

        assert agent_output.status == "success"
        assert agent_output.artifacts == {"design": "spec"}
        assert agent_output.metrics == {"time": 300}
        assert agent_output.next_stage_ready is True
        assert agent_output.errors == []

    def test_agent_output_minimal_data(self):
        """Test AgentOutput with minimal required data."""
        data = {"status": "error", "artifacts": {}}

        agent_output = AgentOutput(**data)

        assert agent_output.status == "error"
        assert agent_output.artifacts == {}
        assert agent_output.metrics == {}
        assert agent_output.next_stage_ready is False
        assert agent_output.errors == []

    def test_agent_output_invalid_status(self):
        """Test AgentOutput with invalid status value."""
        with pytest.raises(ValidationError):
            AgentOutput(status="invalid_status", artifacts={})

    def test_agent_output_with_errors(self):
        """Test AgentOutput with error messages."""
        data = {
            "status": "error",
            "artifacts": {},
            "errors": ["Failed to process", "Timeout occurred"],
        }

        agent_output = AgentOutput(**data)

        assert agent_output.status == "error"
        assert len(agent_output.errors) == 2
        assert "Failed to process" in agent_output.errors


class TestDesignSchemas:
    """Test DesignInput and DesignOutput schemas."""

    def test_design_input_valid_data(self):
        """Test DesignInput with valid data."""
        data = {
            "story_id": "US-001",
            "stage": VModelStage.DESIGN,
            "context": {"user_story": "As a user..."},
            "requirements_artifacts": {"acceptance_criteria": ["Given...", "When...", "Then..."]},
        }

        design_input = DesignInput(**data)

        assert design_input.story_id == "US-001"
        assert design_input.stage == VModelStage.DESIGN
        assert design_input.requirements_artifacts == {
            "acceptance_criteria": ["Given...", "When...", "Then..."]
        }

    def test_design_input_missing_requirements(self):
        """Test DesignInput validation with missing requirements artifacts."""
        with pytest.raises(ValidationError) as exc_info:
            DesignInput(story_id="US-001", stage=VModelStage.DESIGN, context={})

        assert "requirements_artifacts" in str(exc_info.value)

    def test_design_output_valid_data(self):
        """Test DesignOutput with valid data."""
        data = {
            "status": "success",
            "artifacts": {"design_doc": "content"},
            "design_specifications": {"components": ["A", "B"]},
            "architecture_updates": {"diagrams": ["diagram1.puml"]},
            "interface_contracts": {"api": {"endpoints": ["/users"]}},
        }

        design_output = DesignOutput(**data)

        assert design_output.status == "success"
        assert design_output.design_specifications == {"components": ["A", "B"]}
        assert design_output.architecture_updates == {"diagrams": ["diagram1.puml"]}
        assert design_output.interface_contracts == {"api": {"endpoints": ["/users"]}}

    def test_design_output_missing_specifications(self):
        """Test DesignOutput validation with missing design specifications."""
        with pytest.raises(ValidationError) as exc_info:
            DesignOutput(status="success", artifacts={})

        assert "design_specifications" in str(exc_info.value)


class TestImplementationSchemas:
    """Test ImplementationInput and ImplementationOutput schemas."""

    def test_implementation_input_valid_data(self):
        """Test ImplementationInput with valid data."""
        data = {
            "story_id": "US-001",
            "stage": VModelStage.CODING,
            "context": {"design_ready": True},
            "design_artifacts": {"specification": "content"},
            "architecture_context": {"components": ["A", "B"]},
        }

        impl_input = ImplementationInput(**data)

        assert impl_input.story_id == "US-001"
        assert impl_input.stage == VModelStage.CODING
        assert impl_input.design_artifacts == {"specification": "content"}
        assert impl_input.architecture_context == {"components": ["A", "B"]}

    def test_implementation_output_valid_data(self):
        """Test ImplementationOutput with valid data."""
        data = {
            "status": "success",
            "artifacts": {"code": "implementation"},
            "source_files": ["src/module.py", "src/utils.py"],
            "code_metrics": {"lines": 100, "complexity": 5},
            "implementation_report": {"features": ["login", "logout"]},
        }

        impl_output = ImplementationOutput(**data)

        assert impl_output.status == "success"
        assert impl_output.source_files == ["src/module.py", "src/utils.py"]
        assert impl_output.code_metrics == {"lines": 100, "complexity": 5}
        assert impl_output.implementation_report == {"features": ["login", "logout"]}


class TestTestingSchemas:
    """Test TestingInput and TestingOutput schemas."""

    def test_testing_input_valid_data(self):
        """Test TestingInput with valid data."""
        data = {
            "story_id": "US-001",
            "stage": VModelStage.UNIT_TESTING,
            "context": {"implementation_complete": True},
            "test_scope": ["unit", "integration"],
            "acceptance_criteria": ["User can login", "User can logout"],
        }

        test_input = TestingInput(**data)

        assert test_input.story_id == "US-001"
        assert test_input.stage == VModelStage.UNIT_TESTING
        assert test_input.test_scope == ["unit", "integration"]
        assert test_input.acceptance_criteria == ["User can login", "User can logout"]

    def test_testing_output_valid_data(self):
        """Test TestingOutput with valid data."""
        data = {
            "status": "success",
            "artifacts": {"test_suite": "content"},
            "test_files": ["tests/test_login.py", "tests/test_logout.py"],
            "test_results": {"passed": 10, "failed": 0},
            "coverage_report": {"percentage": 95.5, "missing_lines": []},
            "quality_metrics": {"test_count": 10, "assertions": 25},
        }

        test_output = TestingOutput(**data)

        assert test_output.status == "success"
        assert test_output.test_files == ["tests/test_login.py", "tests/test_logout.py"]
        assert test_output.test_results == {"passed": 10, "failed": 0}
        assert test_output.coverage_report == {"percentage": 95.5, "missing_lines": []}
        assert test_output.quality_metrics == {"test_count": 10, "assertions": 25}


class TestIntegrationSchemas:
    """Test IntegrationInput and IntegrationOutput schemas."""

    def test_integration_input_valid_data(self):
        """Test IntegrationInput with valid data."""
        data = {
            "story_id": "US-001",
            "stage": VModelStage.INTEGRATION_TESTING,
            "context": {"all_tests_passed": True},
            "system_artifacts": {"deployment": "config"},
            "integration_scope": ["database", "api", "frontend"],
        }

        integration_input = IntegrationInput(**data)

        assert integration_input.story_id == "US-001"
        assert integration_input.stage == VModelStage.INTEGRATION_TESTING
        assert integration_input.system_artifacts == {"deployment": "config"}
        assert integration_input.integration_scope == ["database", "api", "frontend"]

    def test_integration_output_valid_data(self):
        """Test IntegrationOutput with valid data."""
        data = {
            "status": "success",
            "artifacts": {"deployment": "manifest"},
            "integration_results": {"status": "healthy", "services": 3},
            "deployment_validation": {"environment": "staging", "health_checks": True},
            "system_health": {"cpu": 25, "memory": 60, "uptime": "99.9%"},
        }

        integration_output = IntegrationOutput(**data)

        assert integration_output.status == "success"
        assert integration_output.integration_results == {"status": "healthy", "services": 3}
        assert integration_output.deployment_validation == {
            "environment": "staging",
            "health_checks": True,
        }
        assert integration_output.system_health == {"cpu": 25, "memory": 60, "uptime": "99.9%"}


class TestSchemaInheritance:
    """Test that specialized schemas properly inherit from base schemas."""

    def test_design_input_inherits_agent_input(self):
        """Test that DesignInput inherits from AgentInput."""
        assert issubclass(DesignInput, AgentInput)

    def test_design_output_inherits_agent_output(self):
        """Test that DesignOutput inherits from AgentOutput."""
        assert issubclass(DesignOutput, AgentOutput)

    def test_implementation_input_inherits_agent_input(self):
        """Test that ImplementationInput inherits from AgentInput."""
        assert issubclass(ImplementationInput, AgentInput)

    def test_implementation_output_inherits_agent_output(self):
        """Test that ImplementationOutput inherits from AgentOutput."""
        assert issubclass(ImplementationOutput, AgentOutput)

    def test_testing_input_inherits_agent_input(self):
        """Test that TestingInput inherits from AgentInput."""
        assert issubclass(TestingInput, AgentInput)

    def test_testing_output_inherits_agent_output(self):
        """Test that TestingOutput inherits from AgentOutput."""
        assert issubclass(TestingOutput, AgentOutput)

    def test_integration_input_inherits_agent_input(self):
        """Test that IntegrationInput inherits from AgentInput."""
        assert issubclass(IntegrationInput, AgentInput)

    def test_integration_output_inherits_agent_output(self):
        """Test that IntegrationOutput inherits from AgentOutput."""
        assert issubclass(IntegrationOutput, AgentOutput)


class TestSchemaValidationRules:
    """Test specific validation rules and constraints."""

    def test_story_id_cannot_be_empty(self):
        """Test that story_id cannot be empty string."""
        with pytest.raises(ValidationError):
            AgentInput(story_id="", stage=VModelStage.REQUIREMENTS, context={})

    def test_status_must_be_valid_enum(self):
        """Test that status must be one of allowed values."""
        valid_statuses = ["success", "error", "partial"]

        for status in valid_statuses:
            output = AgentOutput(status=status, artifacts={})
            assert output.status == status

    def test_metrics_must_be_dict(self):
        """Test that metrics field must be a dictionary."""
        with pytest.raises(ValidationError):
            AgentOutput(status="success", artifacts={}, metrics="invalid")

    def test_errors_must_be_list_of_strings(self):
        """Test that errors field must be list of strings."""
        with pytest.raises(ValidationError):
            AgentOutput(status="error", artifacts={}, errors=["valid", 123, "invalid_number"])

    def test_next_stage_ready_is_boolean(self):
        """Test that next_stage_ready must be boolean."""
        output = AgentOutput(status="success", artifacts={}, next_stage_ready=True)
        assert output.next_stage_ready is True

        with pytest.raises(ValidationError):
            AgentOutput(status="success", artifacts={}, next_stage_ready="not_boolean")
