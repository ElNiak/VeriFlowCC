"""Tests for unified agent template validation system.

This module tests the YAML front matter parsing, Pydantic schema validation,
and template structure validation for the new unified agent template system.
"""

import tempfile
from pathlib import Path
from typing import Any

import pytest
import yaml
from pydantic import ValidationError
from verifflowcc.schemas.template_schemas import (
    ContextRequirements,
    InputSchema,
    OutputFormat,
    TemplateConfig,
)
from verifflowcc.validation.template_validator import TemplateValidator


class TestTemplateConfig:
    """Test TemplateConfig schema for YAML front matter validation."""

    def test_template_config_valid_data(self) -> None:
        """Test TemplateConfig with valid YAML front matter data."""
        config_data: dict[str, Any] = {
            "name": "requirements_analyst",
            "description": "Analyzes user stories and creates detailed requirements",
            "model": "claude-3-5-sonnet-20241022",
            "context_requirements": {
                "required": ["user_story", "project_context"],
                "optional": ["previous_requirements", "stakeholder_feedback"],
                "excluded": ["sensitive_data", "credentials"],
            },
            "input_schema": {
                "fields": {
                    "story_id": {"type": "str", "required": True},
                    "user_story": {"type": "str", "required": True},
                    "context": {"type": "dict", "required": False},
                },
                "validation_rules": [
                    "story_id_not_empty",
                    "user_story_invest_compliant",
                ],
            },
            "output_format": {
                "structure": "json",
                "schema": {
                    "functional_requirements": {"type": "list"},
                    "acceptance_criteria": {"type": "list"},
                    "dependencies": {"type": "list"},
                },
                "validation_rules": ["requirements_not_empty", "criteria_testable"],
            },
        }

        template_config = TemplateConfig(**config_data)

        assert template_config.name == "requirements_analyst"
        assert (
            template_config.description == "Analyzes user stories and creates detailed requirements"
        )
        assert template_config.model == "claude-3-5-sonnet-20241022"
        assert isinstance(template_config.context_requirements, ContextRequirements)
        assert isinstance(template_config.input_schema, InputSchema)
        assert isinstance(template_config.output_format, OutputFormat)

    def test_template_config_minimal_data(self) -> None:
        """Test TemplateConfig with minimal required data."""
        config_data: dict[str, Any] = {
            "name": "simple_agent",
            "description": "A simple agent for testing",
            "model": "claude-3-5-sonnet-20241022",
            "context_requirements": {"required": [], "optional": [], "excluded": []},
            "input_schema": {"fields": {}, "validation_rules": []},
            "output_format": {
                "structure": "text",
                "schema": {},
                "validation_rules": [],
            },
        }

        template_config = TemplateConfig(**config_data)

        assert template_config.name == "simple_agent"
        assert template_config.description == "A simple agent for testing"
        assert template_config.model == "claude-3-5-sonnet-20241022"

    def test_template_config_missing_required_fields(self) -> None:
        """Test TemplateConfig validation with missing required fields."""
        with pytest.raises(ValidationError) as exc_info:
            TemplateConfig(
                description="Missing name field",
                model="claude-3-5-sonnet-20241022",
            )  # type: ignore[call-arg]

        assert "name" in str(exc_info.value)

    def test_template_config_invalid_name_format(self) -> None:
        """Test TemplateConfig with invalid name format (non-snake_case)."""
        with pytest.raises(ValidationError) as exc_info:
            TemplateConfig(
                name="InvalidName-Format!",
                description="Invalid name format",
                model="claude-3-5-sonnet-20241022",
                context_requirements={
                    "required": [],
                    "optional": [],
                    "excluded": [],
                },
                input_schema={"fields": {}, "validation_rules": []},
                output_format={
                    "structure": "text",
                    "schema": {},
                    "validation_rules": [],
                },
            )

        assert "name must be in snake_case format" in str(exc_info.value)

    def test_template_config_invalid_model(self) -> None:
        """Test TemplateConfig with invalid model name."""
        with pytest.raises(ValidationError) as exc_info:
            TemplateConfig(
                name="test_agent",
                description="Test agent",
                model="invalid-model",
                context_requirements={
                    "required": [],
                    "optional": [],
                    "excluded": [],
                },
                input_schema={"fields": {}, "validation_rules": []},
                output_format={
                    "structure": "text",
                    "schema": {},
                    "validation_rules": [],
                },
            )

        assert "model must be a valid Claude model" in str(exc_info.value)


class TestContextRequirements:
    """Test ContextRequirements schema."""

    def test_context_requirements_valid_data(self) -> None:
        """Test ContextRequirements with valid data."""
        context_data: dict[str, Any] = {
            "required": ["user_story", "project_context", "business_goals"],
            "optional": ["previous_artifacts", "stakeholder_input", "constraints"],
            "excluded": ["credentials", "api_keys", "personal_data"],
        }

        context_req = ContextRequirements(**context_data)

        assert context_req.required == [
            "user_story",
            "project_context",
            "business_goals",
        ]
        assert context_req.optional == [
            "previous_artifacts",
            "stakeholder_input",
            "constraints",
        ]
        assert context_req.excluded == ["credentials", "api_keys", "personal_data"]

    def test_context_requirements_empty_lists(self) -> None:
        """Test ContextRequirements with empty lists."""
        context_data: dict[str, Any] = {
            "required": [],
            "optional": [],
            "excluded": [],
        }

        context_req = ContextRequirements(**context_data)

        assert context_req.required == []
        assert context_req.optional == []
        assert context_req.excluded == []

    def test_context_requirements_overlapping_fields(self) -> None:
        """Test ContextRequirements validation with overlapping fields."""
        with pytest.raises(ValidationError) as exc_info:
            ContextRequirements(
                required=["field1", "field2"],
                optional=["field2", "field3"],  # field2 overlaps with required
                excluded=["field4"],
            )

        assert "field cannot be in multiple categories" in str(exc_info.value)

    def test_context_requirements_invalid_field_names(self) -> None:
        """Test ContextRequirements with invalid field names."""
        with pytest.raises(ValidationError) as exc_info:
            ContextRequirements(
                required=["valid_field", "Invalid-Field!"],
                optional=["another_valid_field"],
                excluded=["excluded_field"],
            )

        assert "field names must be valid identifiers" in str(exc_info.value)


class TestInputSchema:
    """Test InputSchema schema."""

    def test_input_schema_valid_data(self) -> None:
        """Test InputSchema with valid data."""
        schema_data: dict[str, Any] = {
            "fields": {
                "story_id": {"type": "str", "required": True, "min_length": 1},
                "user_story": {"type": "str", "required": True, "max_length": 2000},
                "priority": {
                    "type": "str",
                    "required": False,
                    "choices": ["high", "medium", "low"],
                },
                "context": {"type": "dict", "required": False},
            },
            "validation_rules": [
                "story_id_not_empty",
                "user_story_invest_compliant",
                "priority_valid_enum",
            ],
        }

        input_schema = InputSchema(**schema_data)

        assert len(input_schema.fields) == 4
        assert input_schema.fields["story_id"]["type"] == "str"
        assert input_schema.fields["story_id"]["required"] is True
        assert "story_id_not_empty" in input_schema.validation_rules

    def test_input_schema_empty_fields(self) -> None:
        """Test InputSchema with empty fields dictionary."""
        schema_data: dict[str, Any] = {
            "fields": {},
            "validation_rules": [],
        }

        input_schema = InputSchema(**schema_data)

        assert input_schema.fields == {}
        assert input_schema.validation_rules == []

    def test_input_schema_invalid_field_type(self) -> None:
        """Test InputSchema with invalid field type."""
        with pytest.raises(ValidationError) as exc_info:
            InputSchema(
                fields={
                    "invalid_field": {
                        "type": "invalid_type",  # Not a valid Python type
                        "required": True,
                    }
                },
                validation_rules=[],
            )

        assert "invalid field type" in str(exc_info.value)


class TestOutputFormat:
    """Test OutputFormat schema."""

    def test_output_format_valid_json_structure(self) -> None:
        """Test OutputFormat with valid JSON structure."""
        format_data: dict[str, Any] = {
            "structure": "json",
            "schema": {
                "functional_requirements": {"type": "list", "items": "dict"},
                "non_functional_requirements": {"type": "list", "items": "dict"},
                "acceptance_criteria": {"type": "list", "items": "str"},
                "dependencies": {"type": "list", "items": "dict"},
            },
            "validation_rules": [
                "requirements_not_empty",
                "criteria_testable",
                "dependencies_valid",
            ],
        }

        output_format = OutputFormat(**format_data)

        assert output_format.structure == "json"
        assert len(output_format.schema) == 4
        assert "requirements_not_empty" in output_format.validation_rules

    def test_output_format_valid_text_structure(self) -> None:
        """Test OutputFormat with valid text structure."""
        format_data: dict[str, Any] = {
            "structure": "text",
            "schema": {},
            "validation_rules": ["content_not_empty", "proper_formatting"],
        }

        output_format = OutputFormat(**format_data)

        assert output_format.structure == "text"
        assert output_format.schema == {}
        assert "content_not_empty" in output_format.validation_rules

    def test_output_format_invalid_structure(self) -> None:
        """Test OutputFormat with invalid structure type."""
        with pytest.raises(ValidationError) as exc_info:
            OutputFormat(
                structure="invalid_structure",  # Not json, text, or yaml
                schema={},
                validation_rules=[],
            )

        assert "structure must be one of" in str(exc_info.value)


class TestTemplateValidator:
    """Test TemplateValidator functionality."""

    def test_validate_yaml_front_matter_valid_file(self) -> None:
        """Test YAML front matter validation with valid template file."""
        template_content = """---
name: test_agent
description: A test agent for validation
model: claude-3-5-sonnet-20241022
context_requirements:
  required:
    - user_story
    - project_context
  optional:
    - previous_artifacts
  excluded:
    - sensitive_data
input_schema:
  fields:
    story_id:
      type: str
      required: true
    context:
      type: dict
      required: false
  validation_rules:
    - story_id_not_empty
output_format:
  structure: json
  schema:
    requirements:
      type: list
    criteria:
      type: list
  validation_rules:
    - requirements_not_empty
---

# Test Agent Template

You are a Test Agent for validating the unified template system.

## Role Definition
Your role is to process test inputs and generate test outputs.

## Context Requirements
- Required: user_story, project_context
- Optional: previous_artifacts
- Excluded: sensitive_data

## Working Process
1. Validate input data
2. Process requirements
3. Generate structured output

## Output Specification
Return JSON with requirements and criteria lists.
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".j2", delete=False) as f:
            f.write(template_content)
            template_path = Path(f.name)

        try:
            validator = TemplateValidator()
            config = validator.validate_yaml_front_matter(template_path)

            assert config.name == "test_agent"
            assert config.description == "A test agent for validation"
            assert "user_story" in config.context_requirements.required
            assert "story_id_not_empty" in config.input_schema.validation_rules

        finally:
            template_path.unlink()

    def test_validate_yaml_front_matter_missing_front_matter(self) -> None:
        """Test YAML front matter validation with missing front matter."""
        template_content = """# Test Agent Template

This template has no YAML front matter.
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".j2", delete=False) as f:
            f.write(template_content)
            template_path = Path(f.name)

        try:
            validator = TemplateValidator()
            with pytest.raises(ValueError) as exc_info:
                validator.validate_yaml_front_matter(template_path)

            assert "YAML front matter not found" in str(exc_info.value)

        finally:
            template_path.unlink()

    def test_validate_yaml_front_matter_invalid_yaml(self) -> None:
        """Test YAML front matter validation with invalid YAML syntax."""
        template_content = """---
name: test_agent
description: A test agent
invalid_yaml: [unclosed list
model: claude-3-5-sonnet-20241022
---

# Test Template
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".j2", delete=False) as f:
            f.write(template_content)
            template_path = Path(f.name)

        try:
            validator = TemplateValidator()
            with pytest.raises(yaml.YAMLError):
                validator.validate_yaml_front_matter(template_path)

        finally:
            template_path.unlink()

    def test_validate_template_structure_valid_template(self) -> None:
        """Test template structure validation with valid template."""
        template_content = """---
name: test_agent
description: A test agent
model: claude-3-5-sonnet-20241022
context_requirements:
  required: []
  optional: []
  excluded: []
input_schema:
  fields: {}
  validation_rules: []
output_format:
  structure: text
  schema: {}
  validation_rules: []
---

# Test Agent Template

## Role Definition
Agent role description here.

## Context Requirements
Context requirements description.

## Working Process
1. Step 1
2. Step 2
3. Step 3

## Output Specification
Output format description.
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".j2", delete=False) as f:
            f.write(template_content)
            template_path = Path(f.name)

        try:
            validator = TemplateValidator()
            is_valid = validator.validate_template_structure(template_path)

            assert is_valid is True

        finally:
            template_path.unlink()

    def test_validate_template_structure_missing_sections(self) -> None:
        """Test template structure validation with missing required sections."""
        template_content = """---
name: test_agent
description: A test agent
model: claude-3-5-sonnet-20241022
context_requirements:
  required: []
  optional: []
  excluded: []
input_schema:
  fields: {}
  validation_rules: []
output_format:
  structure: text
  schema: {}
  validation_rules: []
---

# Test Agent Template

## Role Definition
Agent role description here.

## Missing Context Requirements and Working Process sections
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".j2", delete=False) as f:
            f.write(template_content)
            template_path = Path(f.name)

        try:
            validator = TemplateValidator()
            with pytest.raises(ValueError) as exc_info:
                validator.validate_template_structure(template_path)

            assert "missing required sections" in str(exc_info.value)

        finally:
            template_path.unlink()

    def test_validate_complete_template_valid(self) -> None:
        """Test complete template validation with valid template."""
        template_content = """---
name: complete_test_agent
description: A complete test agent for validation
model: claude-3-5-sonnet-20241022
context_requirements:
  required:
    - user_story
  optional:
    - context
  excluded:
    - sensitive_data
input_schema:
  fields:
    story_id:
      type: str
      required: true
  validation_rules:
    - story_id_not_empty
output_format:
  structure: json
  schema:
    requirements:
      type: list
  validation_rules:
    - requirements_not_empty
---

# Complete Test Agent Template

You are a Complete Test Agent for comprehensive validation.

## Role Definition
Process user stories and generate requirements.

## Context Requirements
- Required: user_story
- Optional: context
- Excluded: sensitive_data

## Working Process
1. Input Validation
2. Processing
3. Output Generation

## Output Specification
Return JSON with requirements list.
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".j2", delete=False) as f:
            f.write(template_content)
            template_path = Path(f.name)

        try:
            validator = TemplateValidator()
            config = validator.validate_complete_template(template_path)

            assert config.name == "complete_test_agent"
            assert config.description == "A complete test agent for validation"
            assert "user_story" in config.context_requirements.required
            assert config.input_schema.fields["story_id"]["type"] == "str"
            assert config.output_format.structure == "json"

        finally:
            template_path.unlink()

    def test_validate_complete_template_invalid(self) -> None:
        """Test complete template validation with invalid template."""
        template_content = """---
name: invalid-name
description: Invalid template
model: invalid-model
context_requirements:
  required: ["field1"]
  optional: ["field1"]  # Overlap with required
  excluded: []
input_schema:
  fields: {}
  validation_rules: []
output_format:
  structure: invalid_structure
  schema: {}
  validation_rules: []
---

# Invalid Template
Missing required sections.
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".j2", delete=False) as f:
            f.write(template_content)
            template_path = Path(f.name)

        try:
            validator = TemplateValidator()
            with pytest.raises(ValidationError):
                validator.validate_complete_template(template_path)

        finally:
            template_path.unlink()

    def test_token_budget_validation(self) -> None:
        """Test token budget validation for template."""
        # Create a template that's too long (over 4000 tokens)
        long_template_content = (
            """---
name: long_test_agent
description: A very long test agent template
model: claude-3-5-sonnet-20241022
context_requirements:
  required: []
  optional: []
  excluded: []
input_schema:
  fields: {}
  validation_rules: []
output_format:
  structure: text
  schema: {}
  validation_rules: []
---

# Long Test Agent Template

"""
            + "This is a very long template content. " * 1000
            + """

## Role Definition
Long role definition.

## Context Requirements
Context requirements.

## Working Process
Working process.

## Output Specification
Output specification.
"""
        )

        with tempfile.NamedTemporaryFile(mode="w", suffix=".j2", delete=False) as f:
            f.write(long_template_content)
            template_path = Path(f.name)

        try:
            validator = TemplateValidator()
            with pytest.raises(ValueError) as exc_info:
                validator.validate_token_budget(template_path)

            assert "exceeds maximum token budget" in str(exc_info.value)

        finally:
            template_path.unlink()


class TestEdgeCasesAndBoundaryConditions:
    """Test edge cases and boundary conditions."""

    def test_empty_template_file(self) -> None:
        """Test validation with completely empty template file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".j2", delete=False) as f:
            f.write("")
            template_path = Path(f.name)

        try:
            validator = TemplateValidator()
            with pytest.raises(ValueError) as exc_info:
                validator.validate_yaml_front_matter(template_path)

            assert "YAML front matter not found" in str(exc_info.value)

        finally:
            template_path.unlink()

    def test_template_with_only_front_matter(self) -> None:
        """Test template with only YAML front matter and no content."""
        template_content = """---
name: minimal_agent
description: Minimal agent with no content
model: claude-3-5-sonnet-20241022
context_requirements:
  required: []
  optional: []
  excluded: []
input_schema:
  fields: {}
  validation_rules: []
output_format:
  structure: text
  schema: {}
  validation_rules: []
---"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".j2", delete=False) as f:
            f.write(template_content)
            template_path = Path(f.name)

        try:
            validator = TemplateValidator()
            with pytest.raises(ValueError) as exc_info:
                validator.validate_template_structure(template_path)

            assert "missing required sections" in str(exc_info.value)

        finally:
            template_path.unlink()

    def test_maximum_field_count_input_schema(self) -> None:
        """Test input schema with maximum number of fields."""
        # Create schema with many fields (boundary test)
        fields = {f"field_{i}": {"type": "str", "required": False} for i in range(50)}

        schema_data: dict[str, Any] = {
            "fields": fields,
            "validation_rules": [f"field_{i}_valid" for i in range(10)],
        }

        input_schema = InputSchema(**schema_data)
        assert len(input_schema.fields) == 50
        assert len(input_schema.validation_rules) == 10

    def test_unicode_characters_in_template(self) -> None:
        """Test template with Unicode characters."""
        template_content = """---
name: unicode_agent
description: Agent with Unicode characters: 中文, العربية, 🚀
model: claude-3-5-sonnet-20241022
context_requirements:
  required: []
  optional: []
  excluded: []
input_schema:
  fields: {}
  validation_rules: []
output_format:
  structure: text
  schema: {}
  validation_rules: []
---

# Unicode Agent Template 🤖

Agent with Unicode support: 中文, العربية, Русский

## Role Definition
Process Unicode text data.

## Context Requirements
Handle international text.

## Working Process
1. Validate Unicode input
2. Process text
3. Generate Unicode output

## Output Specification
Return Unicode text.
"""

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".j2", delete=False, encoding="utf-8"
        ) as f:
            f.write(template_content)
            template_path = Path(f.name)

        try:
            validator = TemplateValidator()
            config = validator.validate_complete_template(template_path)

            assert "Unicode characters" in config.description
            assert config.name == "unicode_agent"

        finally:
            template_path.unlink()
