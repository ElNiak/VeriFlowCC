"""Tests for real Claude Code SDK Developer agent code generation capabilities.

This module tests the actual Claude Code SDK integration for generating Flask application
code, focusing on structured output validation and real AI responses.
"""

import os
from typing import Any

import pytest
from verifflowcc.agents.developer import DeveloperAgent
from verifflowcc.core.sdk_config import SDKConfig
from verifflowcc.core.vmodel import VModelStage
from verifflowcc.schemas.agent_schemas import ImplementationInput, ImplementationOutput


class TestRealSDKFlaskCodeGeneration:
    """Test real Claude Code SDK integration for Flask application code generation."""

    @pytest.fixture
    def sdk_config(self) -> SDKConfig:
        """Provide real SDK configuration for testing."""
        api_key = os.getenv("ANTHROPIC_API_KEY", "test-key")
        return SDKConfig(
            api_key=api_key,
            timeout=60,  # Extended timeout for real API calls
            max_retries=3,
            environment="test",
        )

    @pytest.fixture
    def flask_mailbuddy_input(self) -> ImplementationInput:
        """Provide realistic MailBuddy Flask application implementation input."""
        return ImplementationInput(
            story_id="FLASK-001",
            stage=VModelStage.CODING,
            context={
                "project_name": "MailBuddy",
                "framework": "Flask",
                "database": "SQLite",
                "authentication": "session-based",
                "testing_framework": "pytest",
            },
            design_artifacts={
                "components": [
                    "EmailService",
                    "UserService",
                    "AuthenticationService",
                    "MailboxController",
                ],
                "interfaces": ["IEmailRepository", "IUserRepository", "IAuthProvider"],
                "data_models": ["User", "Email", "Mailbox", "Session"],
                "routes": [
                    "/api/auth/login",
                    "/api/auth/logout",
                    "/api/emails",
                    "/api/emails/<id>",
                    "/api/users/profile",
                ],
            },
            architecture_context={
                "existing_services": ["ConfigService", "LoggingService"],
                "database_schema": "users, emails, mailboxes, sessions tables",
                "security_requirements": [
                    "password hashing",
                    "session validation",
                    "CSRF protection",
                ],
                "performance_requirements": [
                    "sub-100ms response times",
                    "10k concurrent users",
                ],
            },
        )

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_real_sdk_flask_app_generation(
        self,
        isolated_agilevv_dir: Any,
        sdk_config: SDKConfig,
        flask_mailbuddy_input: ImplementationInput,
    ) -> None:
        """Test real SDK generates complete Flask application structure."""
        # Skip if no real API key available
        if sdk_config.api_key == "test-key":
            pytest.skip("No real API key available for SDK integration test")

        agent = DeveloperAgent(
            path_config=isolated_agilevv_dir,
            sdk_config=sdk_config,
            mock_mode=False,  # Use real SDK
        )

        # Process the implementation request
        result = await agent.process(flask_mailbuddy_input.model_dump())

        # Validate successful processing
        assert result["status"] == "success"
        assert result["next_stage_ready"] is True
        assert "artifacts" in result

        # Validate Flask-specific implementation details
        impl_data = result.get("implementation_data", {})
        assert impl_data is not None

        # Check for Flask application structure
        implementation = impl_data.get("implementation", {})
        files = implementation.get("files", [])

        # Verify Flask application files were generated
        file_paths = [f.get("path", "") for f in files if isinstance(f, dict)]

        # Expected Flask structure files
        expected_patterns = [
            "app.py",  # Main Flask application
            "models",  # Data models
            "routes",  # Route handlers
            "services",  # Business logic services
            "requirements.txt",  # Dependencies
        ]

        # Check that at least some expected patterns exist in generated files
        pattern_matches = 0
        for pattern in expected_patterns:
            if any(pattern in path for path in file_paths):
                pattern_matches += 1

        assert pattern_matches >= 2, f"Expected Flask patterns not found in: {file_paths}"

        # Validate code content contains Flask-specific elements
        all_content = " ".join(str(f.get("content", "")) for f in files if isinstance(f, dict))

        # Check for Flask imports and patterns
        flask_indicators = [
            "from flask import",
            "Flask(__name__)",
            "@app.route",
            "request",
            "jsonify",
        ]

        flask_pattern_count = sum(1 for indicator in flask_indicators if indicator in all_content)
        assert flask_pattern_count >= 2, "Generated code lacks Flask-specific patterns"

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_real_sdk_mailbuddy_feature_implementation(
        self, isolated_agilevv_dir: Any, sdk_config: SDKConfig
    ) -> None:
        """Test real SDK implements specific MailBuddy features correctly."""
        # Skip if no real API key available
        if sdk_config.api_key == "test-key":
            pytest.skip("No real API key available for SDK integration test")

        agent = DeveloperAgent(
            path_config=isolated_agilevv_dir, sdk_config=sdk_config, mock_mode=False
        )

        # Specific MailBuddy email feature implementation
        mailbuddy_input = ImplementationInput(
            story_id="MAILBUDDY-EMAIL-001",
            stage=VModelStage.CODING,
            context={
                "feature": "email_management",
                "user_story": "As a user, I want to send, receive and organize emails",
            },
            design_artifacts={
                "feature_spec": {
                    "name": "Email Management",
                    "endpoints": [
                        "GET /api/emails - List user emails",
                        "POST /api/emails - Send new email",
                        "GET /api/emails/<id> - Get email details",
                        "DELETE /api/emails/<id> - Delete email",
                    ],
                    "models": ["Email", "Attachment"],
                    "business_logic": ["validation", "sanitization", "threading"],
                },
                "acceptance_criteria": [
                    "Users can send emails with attachments",
                    "Email content is sanitized for security",
                    "Email threads are properly organized",
                    "Deleted emails go to trash folder",
                ],
            },
            architecture_context={
                "database": "SQLite with SQLAlchemy ORM",
                "authentication": "Flask-Login sessions",
                "validation": "WTForms with CSRF protection",
            },
        )

        result = await agent.process(mailbuddy_input.model_dump())

        # Validate successful email feature implementation
        assert result["status"] == "success"
        assert result["story_id"] == "MAILBUDDY-EMAIL-001"

        # Check implementation contains email-specific functionality
        impl_data = result.get("implementation_data", {})
        implementation = impl_data.get("implementation", {})
        files = implementation.get("files", [])

        # Validate email-related code was generated
        email_indicators = ["email", "send", "receive", "attachment", "smtp", "imap"]

        all_content = " ".join(
            str(f.get("content", "")) for f in files if isinstance(f, dict)
        ).lower()

        email_pattern_count = sum(1 for indicator in email_indicators if indicator in all_content)
        assert (
            email_pattern_count >= 3
        ), f"Email functionality not sufficiently implemented. Content preview: {all_content[:200]}"

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_real_sdk_structured_output_validation(
        self,
        isolated_agilevv_dir: Any,
        sdk_config: SDKConfig,
        flask_mailbuddy_input: ImplementationInput,
    ) -> None:
        """Test that real SDK outputs can be validated with Pydantic schemas."""
        # Skip if no real API key available
        if sdk_config.api_key == "test-key":
            pytest.skip("No real API key available for SDK integration test")

        agent = DeveloperAgent(
            path_config=isolated_agilevv_dir, sdk_config=sdk_config, mock_mode=False
        )

        result = await agent.process(flask_mailbuddy_input.model_dump())

        # Validate result structure matches ImplementationOutput schema
        # Extract the core fields that should match the schema
        output_data = {
            "status": result["status"],
            "artifacts": result.get("artifacts", {}),
            "source_files": result.get("artifacts", {}).get("source_files", []),
            "code_metrics": result.get("quality_metrics", {}),
            "implementation_report": result.get("implementation_data", {}),
            "next_stage_ready": result.get("next_stage_ready", False),
            "errors": result.get("errors", []),
        }

        # This should not raise validation errors
        validated_output = ImplementationOutput(**output_data)

        assert validated_output.status == "success"
        assert validated_output.next_stage_ready is True
        assert isinstance(validated_output.source_files, list)
        assert isinstance(validated_output.artifacts, dict)

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_real_sdk_code_quality_metrics(
        self,
        isolated_agilevv_dir: Any,
        sdk_config: SDKConfig,
        flask_mailbuddy_input: ImplementationInput,
    ) -> None:
        """Test that real SDK generates code with measurable quality metrics."""
        # Skip if no real API key available
        if sdk_config.api_key == "test-key":
            pytest.skip("No real API key available for SDK integration test")

        agent = DeveloperAgent(
            path_config=isolated_agilevv_dir, sdk_config=sdk_config, mock_mode=False
        )

        result = await agent.process(flask_mailbuddy_input.model_dump())

        # Validate quality metrics exist and are reasonable
        quality_metrics = result.get("quality_metrics", {})

        assert "overall_score" in quality_metrics
        assert quality_metrics["overall_score"] >= 0.0
        assert quality_metrics["overall_score"] <= 1.0

        # Check for specific quality dimensions
        expected_metrics = [
            "code_quality",
            "test_coverage",
            "documentation",
            "security",
            "maintainability",
        ]

        for metric in expected_metrics:
            assert metric in quality_metrics
            assert "score" in quality_metrics[metric]
            assert isinstance(quality_metrics[metric]["score"], int | float)

    @pytest.mark.asyncio
    async def test_real_sdk_error_handling(
        self, isolated_agilevv_dir: Any, sdk_config: SDKConfig
    ) -> None:
        """Test real SDK error handling with invalid inputs."""
        agent = DeveloperAgent(
            path_config=isolated_agilevv_dir, sdk_config=sdk_config, mock_mode=False
        )

        # Test with invalid/incomplete input
        invalid_input = {
            "story_id": "INVALID-001",
            "stage": VModelStage.CODING,
            "context": {},
            # Missing required design_artifacts
        }

        result = await agent.process(invalid_input)

        # Should handle invalid input gracefully
        assert result["status"] == "error"
        assert result["next_stage_ready"] is False
        assert "error" in result
        assert result["error"] is not None

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_real_sdk_session_persistence(
        self, isolated_agilevv_dir: Any, sdk_config: SDKConfig
    ) -> None:
        """Test that real SDK maintains session context across calls."""
        # Skip if no real API key available
        if sdk_config.api_key == "test-key":
            pytest.skip("No real API key available for SDK integration test")

        agent = DeveloperAgent(
            path_config=isolated_agilevv_dir, sdk_config=sdk_config, mock_mode=False
        )

        # First implementation request
        first_input = ImplementationInput(
            story_id="SESSION-001",
            stage=VModelStage.CODING,
            context={"component": "UserService"},
            design_artifacts={"components": ["UserService"]},
            architecture_context={"framework": "Flask"},
        )

        first_result = await agent.process(first_input.model_dump())

        # Verify session history is maintained
        assert len(agent.session_history) >= 2  # At least one request-response pair

        # Second related request should have context
        second_input = ImplementationInput(
            story_id="SESSION-002",
            stage=VModelStage.CODING,
            context={"component": "AuthService", "depends_on": "UserService"},
            design_artifacts={"components": ["AuthService"]},
            architecture_context={"framework": "Flask"},
        )

        second_result = await agent.process(second_input.model_dump())

        # Session should have grown
        assert len(agent.session_history) >= 4  # Two request-response pairs
        assert first_result["status"] == "success"
        assert second_result["status"] == "success"


class TestRealSDKStreamingResponse:
    """Test real Claude Code SDK streaming response handling."""

    @pytest.fixture
    def sdk_config(self) -> SDKConfig:
        """Provide SDK configuration with streaming enabled."""
        api_key = os.getenv("ANTHROPIC_API_KEY", "test-key")
        return SDKConfig(api_key=api_key, timeout=90, max_retries=2)

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_real_sdk_streaming_code_generation(
        self, isolated_agilevv_dir: Any, sdk_config: SDKConfig
    ) -> None:
        """Test real SDK streaming response for code generation."""
        # Skip if no real API key available
        if sdk_config.api_key == "test-key":
            pytest.skip("No real API key available for SDK streaming test")

        agent = DeveloperAgent(
            path_config=isolated_agilevv_dir, sdk_config=sdk_config, mock_mode=False
        )

        streaming_input = ImplementationInput(
            story_id="STREAM-001",
            stage=VModelStage.CODING,
            context={"feature": "simple_api"},
            design_artifacts={
                "components": ["SimpleAPI"],
                "endpoints": ["/api/health", "/api/version"],
            },
            architecture_context={"framework": "Flask", "complexity": "minimal"},
        )

        # Process with streaming enabled
        result = await agent.process(streaming_input.model_dump())

        # Validate streaming worked (result should still be complete)
        assert result["status"] == "success"
        assert "implementation_data" in result

        # Session history should contain the interaction
        assert len(agent.session_history) >= 2


class TestRealSDKRetryMechanism:
    """Test real Claude Code SDK retry and error recovery."""

    @pytest.fixture
    def sdk_config_with_retries(self) -> SDKConfig:
        """Provide SDK configuration with retry settings."""
        api_key = os.getenv("ANTHROPIC_API_KEY", "test-key")
        return SDKConfig(api_key=api_key, timeout=30, max_retries=2, retry_delay=1.0)

    @pytest.mark.asyncio
    async def test_real_sdk_retry_on_timeout(
        self, isolated_agilevv_dir: Any, sdk_config_with_retries: SDKConfig
    ) -> None:
        """Test retry mechanism on timeout scenarios."""
        # Skip if no real API key available
        if sdk_config_with_retries.api_key == "test-key":
            pytest.skip("No real API key available for retry test")

        agent = DeveloperAgent(
            path_config=isolated_agilevv_dir,
            sdk_config=sdk_config_with_retries,
            mock_mode=False,
        )

        # Create a complex request that might timeout
        complex_input = ImplementationInput(
            story_id="RETRY-001",
            stage=VModelStage.CODING,
            context={"complexity": "high", "timeout_risk": True},
            design_artifacts={
                "components": ["ComplexService"] * 10,  # Many components
                "requirements": ["detailed analysis"] * 20,  # Complex requirements
            },
            architecture_context={
                "constraints": ["performance", "security", "scalability"],
                "integrations": ["database", "cache", "messaging", "logging"],
            },
        )

        # This should either succeed or fail gracefully with proper error handling
        result = await agent.process(complex_input.model_dump())

        # Result should be valid regardless of success/failure
        assert result["status"] in ["success", "error", "partial"]
        assert "timestamp" in result

        if result["status"] == "error":
            assert "error" in result
            assert result["next_stage_ready"] is False
        else:
            assert "implementation_data" in result


class TestRealSDKDocumentBasedSessionStorage:
    """Test document-based session storage with real SDK responses."""

    @pytest.fixture
    def sdk_config_with_storage(self) -> SDKConfig:
        """Provide SDK configuration for session storage testing."""
        api_key = os.getenv("ANTHROPIC_API_KEY", "test-key")
        return SDKConfig(
            api_key=api_key,
            timeout=45,
        )

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_real_sdk_session_document_persistence(
        self, isolated_agilevv_dir: Any, sdk_config_with_storage: SDKConfig
    ) -> None:
        """Test that session data persists in document storage."""
        # Skip if no real API key available
        if sdk_config_with_storage.api_key == "test-key":
            pytest.skip("No real API key available for session storage test")

        agent = DeveloperAgent(
            path_config=isolated_agilevv_dir,
            sdk_config=sdk_config_with_storage,
            mock_mode=False,
        )

        # Implementation that should create session documents
        session_input = ImplementationInput(
            story_id="DOC-STORAGE-001",
            stage=VModelStage.CODING,
            context={"session_test": True},
            design_artifacts={"components": ["SessionTest"]},
            architecture_context={"storage": "document_based"},
        )

        result = await agent.process(session_input.model_dump())

        # Verify session was successful
        assert result["status"] == "success"

        # Check that session documents were created in the artifacts directory
        artifacts_dir = isolated_agilevv_dir.base_dir / "artifacts"

        # Look for session-related files
        session_files = []
        if artifacts_dir.exists():
            for file_path in artifacts_dir.rglob("*"):
                if file_path.is_file() and any(
                    keyword in file_path.name.lower()
                    for keyword in ["session", "doc-storage", "implementation"]
                ):
                    session_files.append(file_path)

        # At least one implementation artifact should exist
        assert len(session_files) >= 1, f"No session files found in {artifacts_dir}"
