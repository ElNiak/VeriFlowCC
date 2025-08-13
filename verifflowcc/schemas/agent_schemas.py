"""Pydantic schemas for agent input/output validation.

This module defines the data structures used for communication between
the orchestrator and various V-Model stage agents.
"""

from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator

from verifflowcc.core.vmodel import VModelStage


class AgentInput(BaseModel):
    """Base input schema for all VeriFlowCC agents.

    This is the foundational input structure that all specialized
    agent input schemas inherit from.
    """

    story_id: str = Field(..., min_length=1, description="Unique identifier for the user story")
    stage: VModelStage = Field(..., description="Current V-Model stage being executed")
    context: dict[str, Any] = Field(..., description="Contextual information for the stage")
    previous_artifacts: dict[str, Any] = Field(
        default_factory=dict, description="Artifacts from previous V-Model stages"
    )

    @field_validator("story_id")
    @classmethod
    def story_id_not_empty(cls, v):
        """Validate that story_id is not empty."""
        if not v or not v.strip():
            raise ValueError("story_id cannot be empty")
        return v.strip()


class AgentOutput(BaseModel):
    """Base output schema for all VeriFlowCC agents.

    This is the foundational output structure that all specialized
    agent output schemas inherit from.
    """

    status: Literal["success", "error", "partial"] = Field(
        ..., description="Execution status of the agent"
    )
    artifacts: dict[str, Any] = Field(..., description="Generated artifacts from this stage")
    metrics: dict[str, Any] = Field(
        default_factory=dict, description="Performance and quality metrics"
    )
    next_stage_ready: bool = Field(
        default=False, description="Whether the next V-Model stage can proceed"
    )
    errors: list[str] = Field(
        default_factory=list, description="Error messages if status is 'error' or 'partial'"
    )

    @field_validator("errors")
    @classmethod
    def validate_errors_are_strings(cls, v):
        """Validate that all error messages are strings."""
        for error in v:
            if not isinstance(error, str):
                raise ValueError("All errors must be strings")
        return v


# Design Stage Schemas (ArchitectAgent)


class DesignInput(AgentInput):
    """Input schema for ArchitectAgent (Design stage)."""

    requirements_artifacts: dict[str, Any] = Field(
        ..., description="Requirements and acceptance criteria from RequirementsAnalyst"
    )

    @field_validator("requirements_artifacts")
    @classmethod
    def requirements_not_empty(cls, v):
        """Validate that requirements artifacts are provided."""
        if not v:
            raise ValueError("requirements_artifacts cannot be empty")
        return v


class DesignOutput(AgentOutput):
    """Output schema for ArchitectAgent (Design stage)."""

    design_specifications: dict[str, Any] = Field(
        ..., description="System design specifications and component definitions"
    )
    architecture_updates: dict[str, Any] = Field(
        ..., description="Updates to architecture.md and system diagrams"
    )
    interface_contracts: dict[str, Any] = Field(
        ..., description="API contracts and interface specifications"
    )

    @field_validator("design_specifications")
    @classmethod
    def design_specs_not_empty(cls, v):
        """Validate that design specifications are provided."""
        if not v:
            raise ValueError("design_specifications cannot be empty")
        return v


# Implementation Stage Schemas (DeveloperAgent)


class ImplementationInput(AgentInput):
    """Input schema for DeveloperAgent (Coding stage)."""

    design_artifacts: dict[str, Any] = Field(
        ..., description="Design specifications from ArchitectAgent"
    )
    architecture_context: dict[str, Any] = Field(
        ..., description="Current architecture and system context"
    )

    @field_validator("design_artifacts")
    @classmethod
    def design_artifacts_not_empty(cls, v):
        """Validate that design artifacts are provided."""
        if not v:
            raise ValueError("design_artifacts cannot be empty")
        return v


class ImplementationOutput(AgentOutput):
    """Output schema for DeveloperAgent (Coding stage)."""

    source_files: list[str] = Field(..., description="List of source files created or modified")
    code_metrics: dict[str, Any] = Field(
        ..., description="Code quality metrics (lines, complexity, etc.)"
    )
    implementation_report: dict[str, Any] = Field(
        ..., description="Summary of implemented features and changes"
    )

    @field_validator("source_files")
    @classmethod
    def source_files_are_strings(cls, v):
        """Validate that all source files are string paths."""
        for file_path in v:
            if not isinstance(file_path, str):
                raise ValueError("All source files must be string paths")
        return v


# Testing Stage Schemas (QATesterAgent)


class TestingInput(AgentInput):
    """Input schema for QATesterAgent (Testing stages)."""

    test_scope: list[str] = Field(
        ..., description="Types of tests to generate/execute (unit, integration, system)"
    )
    acceptance_criteria: list[str] = Field(..., description="Acceptance criteria to validate")

    @field_validator("test_scope")
    @classmethod
    def test_scope_not_empty(cls, v):
        """Validate that test scope is provided."""
        if not v:
            raise ValueError("test_scope cannot be empty")
        return v

    @field_validator("acceptance_criteria")
    @classmethod
    def acceptance_criteria_not_empty(cls, v):
        """Validate that acceptance criteria are provided."""
        if not v:
            raise ValueError("acceptance_criteria cannot be empty")
        return v


class TestingOutput(AgentOutput):
    """Output schema for QATesterAgent (Testing stages)."""

    test_files: list[str] = Field(..., description="List of test files created or modified")
    test_results: dict[str, Any] = Field(..., description="Test execution results and statistics")
    coverage_report: dict[str, Any] = Field(..., description="Code coverage analysis and report")
    quality_metrics: dict[str, Any] = Field(
        ..., description="Quality metrics (test count, assertions, etc.)"
    )

    @field_validator("test_files")
    @classmethod
    def test_files_are_strings(cls, v):
        """Validate that all test files are string paths."""
        for file_path in v:
            if not isinstance(file_path, str):
                raise ValueError("All test files must be string paths")
        return v


# Integration Stage Schemas (IntegrationAgent)


class IntegrationInput(AgentInput):
    """Input schema for IntegrationAgent (Integration stage)."""

    system_artifacts: dict[str, Any] = Field(..., description="All artifacts from previous stages")
    integration_scope: list[str] = Field(..., description="Components to integrate and validate")

    @field_validator("system_artifacts")
    @classmethod
    def system_artifacts_not_empty(cls, v):
        """Validate that system artifacts are provided."""
        if not v:
            raise ValueError("system_artifacts cannot be empty")
        return v

    @field_validator("integration_scope")
    @classmethod
    def integration_scope_not_empty(cls, v):
        """Validate that integration scope is provided."""
        if not v:
            raise ValueError("integration_scope cannot be empty")
        return v


class IntegrationOutput(AgentOutput):
    """Output schema for IntegrationAgent (Integration stage)."""

    integration_results: dict[str, Any] = Field(
        ..., description="Results of system integration validation"
    )
    deployment_validation: dict[str, Any] = Field(
        ..., description="Deployment and environment validation results"
    )
    system_health: dict[str, Any] = Field(
        ..., description="System health checks and performance metrics"
    )

    @field_validator("integration_results")
    @classmethod
    def integration_results_not_empty(cls, v):
        """Validate that integration results are provided."""
        if not v:
            raise ValueError("integration_results cannot be empty")
        return v
