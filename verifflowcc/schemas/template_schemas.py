"""Pydantic schemas for unified agent template validation system.

This module defines the data structures used for validating YAML front matter,
context requirements, input/output schemas, and overall template structure
for the VeriFlowCC context engineering standardization project.
"""

import re
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator, model_validator


class ContextRequirements(BaseModel):
    """Schema for agent context requirements specification.

    Defines which context elements are required, optional, or excluded
    for optimal token usage and context isolation.
    """

    required: list[str] = Field(
        default_factory=list,
        description="Context elements that must be present for agent execution",
    )
    optional: list[str] = Field(
        default_factory=list,
        description="Context elements that enhance processing when available",
    )
    excluded: list[str] = Field(
        default_factory=list,
        description="Context elements that must not be included for security/privacy",
    )

    @field_validator("required", "optional", "excluded")
    @classmethod
    def validate_field_names(cls, v: list[str]) -> list[str]:
        """Validate that all field names are valid Python identifiers."""
        for field_name in v:
            if not field_name.isidentifier():
                raise ValueError(f"field names must be valid identifiers, got: {field_name}")
        return v

    @model_validator(mode="after")
    def validate_no_overlapping_fields(self) -> "ContextRequirements":
        """Validate that fields don't appear in multiple categories."""
        all_fields = set(self.required + self.optional + self.excluded)
        total_count = len(self.required) + len(self.optional) + len(self.excluded)

        if len(all_fields) != total_count:
            # Find overlapping fields
            seen = set()
            overlapping = []
            for field in self.required + self.optional + self.excluded:
                if field in seen:
                    overlapping.append(field)
                seen.add(field)

            raise ValueError(f"field cannot be in multiple categories: {overlapping}")

        return self


class InputFieldSpec(BaseModel):
    """Specification for an input field in the schema."""

    type: str = Field(..., description="Python type for the field")
    required: bool = Field(default=True, description="Whether the field is required")
    min_length: int | None = Field(default=None, description="Minimum length for string fields")
    max_length: int | None = Field(default=None, description="Maximum length for string fields")
    choices: list[str] | None = Field(default=None, description="Valid choices for enum fields")
    description: str | None = Field(default=None, description="Field description")

    @field_validator("type")
    @classmethod
    def validate_field_type(cls, v: str) -> str:
        """Validate that field type is a valid Python type."""
        valid_types = {
            "str",
            "int",
            "float",
            "bool",
            "dict",
            "list",
            "Any",
            "Optional[str]",
            "Optional[int]",
            "Optional[dict]",
            "Optional[list]",
        }
        if v not in valid_types:
            raise ValueError(f"invalid field type: {v}")
        return v


class InputSchema(BaseModel):
    """Schema for agent input validation specification."""

    fields: dict[str, InputFieldSpec] = Field(
        default_factory=dict,
        description="Field specifications for input validation",
    )
    validation_rules: list[str] = Field(
        default_factory=list,
        description="List of validation rule names to apply",
    )

    @field_validator("fields")
    @classmethod
    def validate_fields_not_empty_if_rules(
        cls, v: dict[str, InputFieldSpec]
    ) -> dict[str, InputFieldSpec]:
        """Convert dict values to InputFieldSpec if needed."""
        validated_fields = {}
        for field_name, field_spec in v.items():
            if isinstance(field_spec, dict):
                validated_fields[field_name] = InputFieldSpec(**field_spec)
            else:
                validated_fields[field_name] = field_spec
        return validated_fields

    @field_validator("validation_rules")
    @classmethod
    def validate_rule_names(cls, v: list[str]) -> list[str]:
        """Validate that validation rule names are valid identifiers."""
        for rule in v:
            if not rule.isidentifier():
                raise ValueError(f"validation rule names must be valid identifiers: {rule}")
        return v


class OutputFieldSpec(BaseModel):
    """Specification for an output field in the schema."""

    type: str = Field(..., description="Python type for the field")
    required: bool = Field(default=True, description="Whether the field is required")
    choices: list[str] | None = Field(default=None, description="Valid choices for enum fields")
    items: str | None = Field(default=None, description="Type of items for list fields")
    default: Any | None = Field(default=None, description="Default value for the field")
    description: str | None = Field(default=None, description="Field description")

    @field_validator("type")
    @classmethod
    def validate_field_type(cls, v: str) -> str:
        """Validate that field type is a valid Python type."""
        valid_types = {
            "str",
            "int",
            "float",
            "bool",
            "dict",
            "list",
            "Any",
            "Optional[str]",
            "Optional[int]",
            "Optional[dict]",
            "Optional[list]",
        }
        if v not in valid_types:
            raise ValueError(f"invalid field type: {v}")
        return v


class OutputFormat(BaseModel):
    """Schema for agent output format specification."""

    structure: Literal["json", "text", "yaml"] = Field(..., description="Output structure type")
    schema: dict[str, dict[str, Any] | OutputFieldSpec] = Field(
        default_factory=dict,
        description="Output schema definition",
    )
    validation_rules: list[str] = Field(
        default_factory=list,
        description="List of validation rule names to apply to output",
    )

    @field_validator("schema")
    @classmethod
    def validate_schema_fields(
        cls, v: dict[str, dict[str, Any] | OutputFieldSpec]
    ) -> dict[str, OutputFieldSpec]:
        """Convert dict values to OutputFieldSpec if needed."""
        validated_schema = {}
        for field_name, field_spec in v.items():
            if isinstance(field_spec, dict):
                validated_schema[field_name] = OutputFieldSpec(**field_spec)
            else:
                validated_schema[field_name] = field_spec
        return validated_schema

    @field_validator("validation_rules")
    @classmethod
    def validate_rule_names(cls, v: list[str]) -> list[str]:
        """Validate that validation rule names are valid identifiers."""
        for rule in v:
            if not rule.isidentifier():
                raise ValueError(f"validation rule names must be valid identifiers: {rule}")
        return v


class TemplateConfig(BaseModel):
    """Complete configuration schema for agent template YAML front matter.

    This schema validates the entire YAML front matter section of agent templates,
    ensuring compliance with context engineering standards and token budget constraints.
    """

    name: str = Field(..., description="Agent name in snake_case format")
    description: str = Field(..., description="Brief description of agent purpose")
    model: str = Field(..., description="Claude model to use for this agent")
    context_requirements: ContextRequirements = Field(
        ..., description="Context requirements specification"
    )
    input_schema: InputSchema = Field(..., description="Input validation schema")
    output_format: OutputFormat = Field(..., description="Output format specification")
    version: str = Field(default="1.0.0", description="Template schema version")

    @field_validator("name")
    @classmethod
    def validate_name_format(cls, v: str) -> str:
        """Validate that agent name is in snake_case format."""
        if not re.match(r"^[a-z][a-z0-9_]*[a-z0-9]$", v) and v != v.lower():
            raise ValueError(
                "name must be in snake_case format with only lowercase letters, numbers, and underscores"
            )
        return v

    @field_validator("model")
    @classmethod
    def validate_model_name(cls, v: str) -> str:
        """Validate that model is a valid Claude model."""
        valid_models = {
            "claude-3-5-sonnet-20241022",
            "claude-3-5-haiku-20241022",
            "claude-3-opus-20240229",
            "claude-3-sonnet-20240229",
            "claude-3-haiku-20240307",
        }
        if v not in valid_models:
            raise ValueError(f"model must be a valid Claude model: {', '.join(valid_models)}")
        return v

    @field_validator("description")
    @classmethod
    def validate_description_length(cls, v: str) -> str:
        """Validate that description is reasonable length."""
        if len(v) < 10:
            raise ValueError("description must be at least 10 characters")
        if len(v) > 200:
            raise ValueError("description must be no more than 200 characters")
        return v

    @field_validator("version")
    @classmethod
    def validate_version_format(cls, v: str) -> str:
        """Validate that version follows semantic versioning."""
        version_pattern = r"^\d+\.\d+\.\d+(-[a-zA-Z0-9]+)?$"
        if not re.match(version_pattern, v):
            raise ValueError("version must follow semantic versioning format (e.g., 1.0.0)")
        return v


class TemplateStructureValidation(BaseModel):
    """Schema for validating template structure requirements."""

    required_sections: list[str] = Field(
        default=[
            "Role Definition",
            "Context Requirements",
            "Working Process",
            "Output Specification",
        ],
        description="Required sections in template body",
    )
    max_token_budget: int = Field(
        default=4000, description="Maximum token budget for agent template"
    )
    min_sections: int = Field(default=4, description="Minimum number of sections required")

    @field_validator("max_token_budget")
    @classmethod
    def validate_token_budget_positive(cls, v: int) -> int:
        """Validate that token budget is positive and reasonable."""
        if v <= 0:
            raise ValueError("max_token_budget must be positive")
        if v > 100000:
            raise ValueError("max_token_budget is unreasonably large")
        return v


class ValidationResult(BaseModel):
    """Result of template validation process."""

    is_valid: bool = Field(..., description="Whether template passed validation")
    errors: list[str] = Field(default_factory=list, description="List of validation errors if any")
    warnings: list[str] = Field(
        default_factory=list, description="List of validation warnings if any"
    )
    token_count: int | None = Field(default=None, description="Estimated token count for template")
    quality_score: float | None = Field(default=None, description="Quality score from 0.0 to 1.0")

    @field_validator("quality_score")
    @classmethod
    def validate_quality_score_range(cls, v: float | None) -> float | None:
        """Validate that quality score is in valid range."""
        if v is not None and (v < 0.0 or v > 1.0):
            raise ValueError("quality_score must be between 0.0 and 1.0")
        return v
