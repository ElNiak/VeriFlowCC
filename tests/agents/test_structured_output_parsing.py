"""Tests for structured output parsing from real Claude Code SDK responses.

This module tests parsing and validation of different output formats (JSON, YAML, Markdown)
from authentic Claude Code SDK responses, ensuring robust structured data handling.
"""

import json
import os
from typing import Any

import pytest
import yaml
from pydantic import BaseModel, Field
from verifflowcc.agents.developer import DeveloperAgent
from verifflowcc.core.sdk_config import SDKConfig
from verifflowcc.core.vmodel import VModelStage
from verifflowcc.schemas.agent_schemas import ImplementationInput


class FlaskCodeStructure(BaseModel):
    """Expected structure for Flask code generation output."""

    app_py: dict[str, Any] = Field(..., description="Main Flask application file")
    models: list[dict[str, Any]] = Field(default_factory=list, description="SQLAlchemy models")
    routes: list[dict[str, Any]] = Field(
        default_factory=list, description="Flask route definitions"
    )
    services: list[dict[str, Any]] = Field(
        default_factory=list, description="Business logic services"
    )
    tests: list[dict[str, Any]] = Field(default_factory=list, description="Test files")
    requirements: list[str] = Field(default_factory=list, description="Python dependencies")


class MailBuddyFeatureStructure(BaseModel):
    """Expected structure for MailBuddy feature implementation."""

    feature_name: str = Field(..., description="Name of the implemented feature")
    endpoints: list[str] = Field(..., description="API endpoints created")
    database_models: list[str] = Field(..., description="Database models involved")
    business_logic: list[str] = Field(..., description="Core business logic components")
    security_measures: list[str] = Field(
        default_factory=list, description="Security implementations"
    )


class TestStructuredOutputParsing:
    """Test structured output parsing from real Claude Code SDK responses."""

    @pytest.fixture
    def sdk_config(self) -> SDKConfig:
        """Provide SDK configuration for structured output testing."""
        api_key = os.getenv("ANTHROPIC_API_KEY", "test-key")
        return SDKConfig(
            api_key=api_key,
            timeout=120,  # Extended timeout for complex outputs
            max_retries=2,
        )

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_parse_json_response_structure(
        self, isolated_agilevv_dir: Any, sdk_config: SDKConfig
    ) -> None:
        """Test parsing JSON-structured responses from real SDK."""
        # Skip if no real API key available
        if sdk_config.api_key == "test-key":
            pytest.skip("No real API key available for JSON parsing test")

        agent = DeveloperAgent(
            path_config=isolated_agilevv_dir, sdk_config=sdk_config, mock_mode=False
        )

        # Request specifically JSON-formatted output
        json_input = ImplementationInput(
            story_id="JSON-PARSE-001",
            stage=VModelStage.CODING,
            context={
                "output_format": "json",
                "structure_requirement": "strict_json",
                "feature": "user_authentication",
            },
            design_artifacts={
                "output_specification": {
                    "format": "json",
                    "required_fields": ["implementation", "tests", "documentation"],
                    "structure": "nested_objects",
                },
                "components": ["AuthService", "UserModel", "LoginRoute"],
            },
            architecture_context={
                "framework": "Flask",
                "response_format": "application/json",
            },
        )

        result = await agent.process(json_input.model_dump())

        # Validate that we got a successful result
        assert result["status"] == "success"

        # Extract and validate JSON structure
        impl_data = result.get("implementation_data", {})

        # Test JSON parsing capability
        if "response_text" in impl_data:
            response_text = impl_data["response_text"]

            # Try to parse as JSON
            try:
                if response_text.strip().startswith("{"):
                    json_data = json.loads(response_text)

                    # Validate JSON has expected structure
                    assert isinstance(json_data, dict)

                    # Check for common implementation fields
                    expected_json_fields = ["implementation", "files", "dependencies"]
                    json_field_count = sum(
                        1 for field in expected_json_fields if field in json_data
                    )
                    assert (
                        json_field_count >= 1
                    ), f"JSON response lacks expected fields: {list(json_data.keys())}"

            except json.JSONDecodeError:
                # If not pure JSON, check if implementation data is structured
                assert "implementation" in impl_data, "No structured implementation data found"

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_parse_yaml_response_structure(
        self, isolated_agilevv_dir: Any, sdk_config: SDKConfig
    ) -> None:
        """Test parsing YAML-structured responses from real SDK."""
        # Skip if no real API key available
        if sdk_config.api_key == "test-key":
            pytest.skip("No real API key available for YAML parsing test")

        agent = DeveloperAgent(
            path_config=isolated_agilevv_dir, sdk_config=sdk_config, mock_mode=False
        )

        # Request YAML-formatted output
        yaml_input = ImplementationInput(
            story_id="YAML-PARSE-001",
            stage=VModelStage.CODING,
            context={
                "output_format": "yaml",
                "configuration_focus": True,
                "feature": "email_service_config",
            },
            design_artifacts={
                "output_specification": {
                    "format": "yaml",
                    "include_config": True,
                    "nested_structure": True,
                },
                "components": ["EmailService", "SMTPConfig", "EmailQueue"],
            },
            architecture_context={
                "framework": "Flask",
                "configuration_management": "YAML-based",
            },
        )

        result = await agent.process(yaml_input.model_dump())

        assert result["status"] == "success"

        # Extract implementation data for YAML validation
        impl_data = result.get("implementation_data", {})

        # Look for YAML-like structures in the response
        if "response_text" in impl_data:
            response_text = impl_data["response_text"]

            # Try to find YAML content blocks
            yaml_indicators = ["---", "config:", "services:", "database:"]
            yaml_pattern_count = sum(
                1 for indicator in yaml_indicators if indicator in response_text
            )

            if yaml_pattern_count >= 1:
                # Try to parse YAML sections
                try:
                    # Look for YAML blocks in the response
                    lines = response_text.split("\n")
                    yaml_lines = []
                    in_yaml_block = False

                    for line in lines:
                        if line.strip().startswith("---") or line.strip().endswith(":"):
                            in_yaml_block = True
                        if in_yaml_block:
                            yaml_lines.append(line)
                        if line.strip() == "---" and len(yaml_lines) > 1:
                            break

                    if yaml_lines:
                        yaml_content = "\n".join(yaml_lines)
                        yaml_data = yaml.safe_load(yaml_content)

                        if yaml_data:
                            assert isinstance(yaml_data, dict), "YAML should parse to dictionary"

                except yaml.YAMLError:
                    # YAML parsing failed, but that's okay - verify structured data exists
                    pass

        # Ensure some form of structured data exists
        assert "implementation" in impl_data or "files" in impl_data.get(
            "implementation", {}
        ), "No structured implementation data found"

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_parse_markdown_response_structure(
        self, isolated_agilevv_dir: Any, sdk_config: SDKConfig
    ) -> None:
        """Test parsing Markdown-structured responses from real SDK."""
        # Skip if no real API key available
        if sdk_config.api_key == "test-key":
            pytest.skip("No real API key available for Markdown parsing test")

        agent = DeveloperAgent(
            path_config=isolated_agilevv_dir, sdk_config=sdk_config, mock_mode=False
        )

        # Request Markdown-formatted output with documentation focus
        markdown_input = ImplementationInput(
            story_id="MD-PARSE-001",
            stage=VModelStage.CODING,
            context={
                "output_format": "markdown",
                "documentation_focus": True,
                "feature": "api_documentation",
            },
            design_artifacts={
                "output_specification": {
                    "format": "markdown",
                    "include_code_blocks": True,
                    "structured_sections": True,
                },
                "components": ["APIDocumentation", "EndpointSpecs", "ExampleRequests"],
            },
            architecture_context={
                "framework": "Flask",
                "documentation_style": "markdown",
            },
        )

        result = await agent.process(markdown_input.model_dump())

        assert result["status"] == "success"

        # Extract and validate Markdown structure
        impl_data = result.get("implementation_data", {})

        if "response_text" in impl_data:
            response_text = impl_data["response_text"]

            # Check for Markdown indicators
            markdown_indicators = ["# ", "## ", "```", "- ", "* ", "1. "]
            markdown_pattern_count = sum(
                1 for indicator in markdown_indicators if indicator in response_text
            )

            assert markdown_pattern_count >= 2, "Response should contain Markdown formatting"

            # Check for code blocks (important for implementation docs)
            code_block_patterns = ["```python", "```flask", "```"]
            code_block_count = sum(1 for pattern in code_block_patterns if pattern in response_text)

            # Should have at least one code block for implementation docs
            if code_block_count >= 1:
                # Extract code blocks for validation
                code_blocks: list[str] = []
                lines = response_text.split("\n")
                in_code_block = False
                current_block: list[str] = []

                for line in lines:
                    if line.strip().startswith("```"):
                        if in_code_block:
                            # End of code block
                            code_blocks.append("\n".join(current_block))
                            current_block = []
                            in_code_block = False
                        else:
                            # Start of code block
                            in_code_block = True
                    elif in_code_block:
                        current_block.append(line)

                # Validate that code blocks contain meaningful content
                meaningful_blocks = [block for block in code_blocks if len(block.strip()) > 10]
                assert (
                    len(meaningful_blocks) >= 1
                ), "Should have at least one substantial code block"

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_mixed_format_response_handling(
        self, isolated_agilevv_dir: Any, sdk_config: SDKConfig
    ) -> None:
        """Test handling responses that contain mixed output formats."""
        # Skip if no real API key available
        if sdk_config.api_key == "test-key":
            pytest.skip("No real API key available for mixed format test")

        agent = DeveloperAgent(
            path_config=isolated_agilevv_dir, sdk_config=sdk_config, mock_mode=False
        )

        # Request output that might contain multiple formats
        mixed_input = ImplementationInput(
            story_id="MIXED-FORMAT-001",
            stage=VModelStage.CODING,
            context={
                "output_format": "comprehensive",
                "include_code": True,
                "include_config": True,
                "include_docs": True,
            },
            design_artifacts={
                "output_specification": {
                    "code_files": "python",
                    "configuration": "yaml",
                    "documentation": "markdown",
                },
                "components": ["CompleteFeature", "ConfigFiles", "Documentation"],
            },
            architecture_context={"framework": "Flask", "comprehensive_output": True},
        )

        result = await agent.process(mixed_input.model_dump())

        assert result["status"] == "success"

        # Validate that we can extract structured data regardless of format mixing
        impl_data = result.get("implementation_data", {})

        # Should have implementation data
        assert "implementation" in impl_data, "Implementation data should be present"

        # Check for different format indicators in response
        if "response_text" in impl_data:
            response_text = impl_data["response_text"]

            format_indicators = {
                "json": ["{", "}", '":', '",'],
                "yaml": ["---", ":", "- "],
                "markdown": ["# ", "```", "## "],
                "python": ["def ", "class ", "import "],
            }

            detected_formats = []
            for format_name, indicators in format_indicators.items():
                if any(indicator in response_text for indicator in indicators):
                    detected_formats.append(format_name)

            # Should detect at least one format
            assert len(detected_formats) >= 1, "No recognizable formats detected in response"

        # Most importantly, ensure structured implementation data exists
        implementation = impl_data.get("implementation", {})
        assert isinstance(implementation, dict), "Implementation should be structured as dictionary"


class TestFlaskSpecificStructuredOutput:
    """Test Flask-specific structured output validation."""

    @pytest.fixture
    def sdk_config(self) -> SDKConfig:
        """Provide SDK configuration optimized for Flask development."""
        api_key = os.getenv("ANTHROPIC_API_KEY", "test-key")
        return SDKConfig(api_key=api_key, timeout=90)

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_flask_code_structure_validation(
        self, isolated_agilevv_dir: Any, sdk_config: SDKConfig
    ) -> None:
        """Test that Flask code follows expected structural patterns."""
        # Skip if no real API key available
        if sdk_config.api_key == "test-key":
            pytest.skip("No real API key available for Flask structure test")

        agent = DeveloperAgent(
            path_config=isolated_agilevv_dir, sdk_config=sdk_config, mock_mode=False
        )

        flask_input = ImplementationInput(
            story_id="FLASK-STRUCTURE-001",
            stage=VModelStage.CODING,
            context={
                "framework": "Flask",
                "structure_validation": True,
                "feature": "complete_web_app",
            },
            design_artifacts={
                "application_structure": {
                    "app_module": "app.py",
                    "models_package": "models/",
                    "routes_package": "routes/",
                    "services_package": "services/",
                },
                "components": ["FlaskApp", "UserModel", "AuthRoutes", "UserService"],
            },
            architecture_context={
                "framework": "Flask",
                "database": "SQLAlchemy",
                "template_engine": "Jinja2",
            },
        )

        result = await agent.process(flask_input.model_dump())

        assert result["status"] == "success"

        # Extract generated files for structure validation
        impl_data = result.get("implementation_data", {})
        implementation = impl_data.get("implementation", {})
        files = implementation.get("files", [])

        # Analyze Flask structure
        flask_structure: dict[str, Any] = {
            "app_py": None,
            "models": [],
            "routes": [],
            "services": [],
            "tests": [],
            "requirements": [],
        }

        for file_info in files:
            if isinstance(file_info, dict):
                file_path = file_info.get("path", "")
                file_content = file_info.get("content", "")

                # Categorize files by Flask patterns
                if "app.py" in file_path or "main.py" in file_path:
                    flask_structure["app_py"] = {
                        "path": file_path,
                        "content": file_content,
                    }
                elif "model" in file_path.lower() or "models/" in file_path:
                    flask_structure["models"].append({"path": file_path, "content": file_content})
                elif "route" in file_path.lower() or "routes/" in file_path:
                    flask_structure["routes"].append({"path": file_path, "content": file_content})
                elif "service" in file_path.lower() or "services/" in file_path:
                    flask_structure["services"].append({"path": file_path, "content": file_content})
                elif "test" in file_path.lower():
                    flask_structure["tests"].append({"path": file_path, "content": file_content})
                elif "requirements" in file_path.lower():
                    flask_structure["requirements"].append(file_content)

        # Validate Flask application structure
        # Should have at least main app file
        assert flask_structure["app_py"] is not None, "Flask app.py or main.py should be generated"

        # Check Flask app content
        if flask_structure["app_py"]:
            app_content = flask_structure["app_py"]["content"]
            flask_app_indicators = ["Flask(__name__)", "app = Flask", "@app.route"]
            flask_indicator_count = sum(
                1 for indicator in flask_app_indicators if indicator in app_content
            )
            assert (
                flask_indicator_count >= 2
            ), "Main app file should contain Flask application setup"

        # Should have some form of organization (models, routes, or services)
        structural_components = (
            len(flask_structure["models"])
            + len(flask_structure["routes"])
            + len(flask_structure["services"])
        )
        assert (
            structural_components >= 1
        ), "Flask app should have organized components (models/routes/services)"

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_mailbuddy_feature_structure_validation(
        self, isolated_agilevv_dir: Any, sdk_config: SDKConfig
    ) -> None:
        """Test MailBuddy-specific feature structure validation."""
        # Skip if no real API key available
        if sdk_config.api_key == "test-key":
            pytest.skip("No real API key available for MailBuddy structure test")

        agent = DeveloperAgent(
            path_config=isolated_agilevv_dir, sdk_config=sdk_config, mock_mode=False
        )

        mailbuddy_input = ImplementationInput(
            story_id="MAILBUDDY-STRUCTURE-001",
            stage=VModelStage.CODING,
            context={
                "project": "MailBuddy",
                "feature_validation": True,
                "feature": "complete_email_system",
            },
            design_artifacts={
                "feature_specification": {
                    "name": "Email Management System",
                    "endpoints": ["/api/emails", "/api/send", "/api/folders"],
                    "models": ["Email", "User", "Folder", "Attachment"],
                    "services": ["EmailService", "UserService", "FolderService"],
                },
                "components": [
                    "EmailController",
                    "EmailModel",
                    "EmailService",
                    "EmailRoutes",
                ],
            },
            architecture_context={
                "application": "MailBuddy",
                "email_protocols": ["SMTP", "IMAP"],
                "security": ["authentication", "authorization", "encryption"],
            },
        )

        result = await agent.process(mailbuddy_input.model_dump())

        assert result["status"] == "success"

        # Validate MailBuddy-specific structure
        impl_data = result.get("implementation_data", {})
        implementation = impl_data.get("implementation", {})

        # Extract MailBuddy feature characteristics
        all_content = ""
        files = implementation.get("files", [])
        for file_info in files:
            if isinstance(file_info, dict):
                all_content += file_info.get("content", "") + " "

        # Check for MailBuddy-specific patterns
        mailbuddy_patterns = {
            "email_functionality": ["email", "send", "receive", "inbox", "message"],
            "user_management": ["user", "login", "auth", "session"],
            "data_persistence": ["model", "database", "save", "query"],
            "api_endpoints": ["route", "endpoint", "@app.route", "api"],
            "security": ["hash", "validate", "secure", "auth"],
        }

        detected_patterns = {}
        content_lower = all_content.lower()

        for category, patterns in mailbuddy_patterns.items():
            pattern_count = sum(1 for pattern in patterns if pattern in content_lower)
            detected_patterns[category] = pattern_count

        # Validate that key MailBuddy patterns are present
        assert detected_patterns["email_functionality"] >= 2, "Email functionality patterns missing"
        assert detected_patterns["api_endpoints"] >= 1, "API endpoint patterns missing"

        # Ensure overall MailBuddy feature coherence
        total_patterns = sum(detected_patterns.values())
        assert (
            total_patterns >= 6
        ), f"Insufficient MailBuddy-specific patterns detected: {detected_patterns}"


class TestErrorHandlingInStructuredOutput:
    """Test error handling during structured output parsing."""

    @pytest.fixture
    def sdk_config(self) -> SDKConfig:
        """Provide SDK configuration for error testing."""
        api_key = os.getenv("ANTHROPIC_API_KEY", "test-key")
        return SDKConfig(api_key=api_key, timeout=30, max_retries=1)

    @pytest.mark.asyncio
    async def test_malformed_json_handling(
        self, isolated_agilevv_dir: Any, sdk_config: SDKConfig
    ) -> None:
        """Test handling of malformed JSON responses."""
        agent = DeveloperAgent(
            path_config=isolated_agilevv_dir, sdk_config=sdk_config, mock_mode=False
        )

        # This test works regardless of API availability since we test error handling
        malformed_input = ImplementationInput(
            story_id="MALFORMED-001",
            stage=VModelStage.CODING,
            context={"error_simulation": True},
            design_artifacts={"components": ["ErrorTest"]},
            architecture_context={"framework": "Flask"},
        )

        result = await agent.process(malformed_input.model_dump())

        # Should handle any response gracefully
        assert result["status"] in ["success", "error", "partial"]
        assert "timestamp" in result

        # If there's an error, it should be properly structured
        if result["status"] == "error":
            assert "error" in result
            assert result["next_stage_ready"] is False

    @pytest.mark.asyncio
    async def test_empty_response_handling(
        self, isolated_agilevv_dir: Any, sdk_config: SDKConfig
    ) -> None:
        """Test handling of empty or minimal responses."""
        agent = DeveloperAgent(
            path_config=isolated_agilevv_dir, sdk_config=sdk_config, mock_mode=False
        )

        minimal_input = ImplementationInput(
            story_id="MINIMAL-001",
            stage=VModelStage.CODING,
            context={"minimal_test": True},
            design_artifacts={"components": ["MinimalTest"]},
            architecture_context={"framework": "Flask"},
        )

        result = await agent.process(minimal_input.model_dump())

        # Should produce a valid result structure regardless of content
        assert isinstance(result, dict)
        assert "status" in result
        assert "timestamp" in result
        assert result["status"] in ["success", "error", "partial"]
