"""Tests for QATesterAgent (Testing stage agent).

This module tests the QATesterAgent functionality including test generation,
test execution, and quality validation.
"""

import json
import os
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest
from verifflowcc.agents.qa_tester import QATesterAgent
from verifflowcc.core.orchestrator import VModelStage
from verifflowcc.core.path_config import PathConfig
from verifflowcc.core.sdk_config import SDKConfig
from verifflowcc.schemas.agent_schemas import TestingInput, TestingOutput


class TestQATesterAgentInitialization:
    """Test QATesterAgent initialization and configuration."""

    def test_qa_tester_agent_initialization(self, isolated_agilevv_dir: PathConfig) -> None:
        """Test QATesterAgent initializes correctly."""
        agent = QATesterAgent(name="qa_tester", path_config=isolated_agilevv_dir)

        assert agent.name == "qa_tester"
        assert agent.path_config == isolated_agilevv_dir
        assert agent.agent_type == "qa"


class TestQATesterAgentInputValidation:
    """Test QATesterAgent input validation and processing."""

    def test_testing_input_validation(self, isolated_agilevv_dir: PathConfig) -> None:
        """Test that QATesterAgent validates TestingInput correctly."""
        # Instantiate agent to verify it can be created with valid config
        QATesterAgent(path_config=isolated_agilevv_dir)

        # Valid input
        valid_input = TestingInput(
            story_id="US-001",
            stage=VModelStage.UNIT_TESTING,
            context={"implementation_complete": True},
            test_scope=["unit", "integration"],
            acceptance_criteria=["User can login", "User can logout"],
        )

        # Should not raise any validation errors
        assert valid_input.story_id == "US-001"
        assert valid_input.stage == VModelStage.UNIT_TESTING
        assert valid_input.test_scope == ["unit", "integration"]


@pytest.mark.asyncio
class TestQATesterAgentProcessing:
    """Test QATesterAgent main processing functionality."""

    @patch("verifflowcc.agents.qa_tester.QATesterAgent._call_claude_sdk")
    async def test_process_test_generation(
        self, mock_claude_api: Any, isolated_agilevv_dir: PathConfig
    ) -> None:
        """Test the main process method for test generation."""
        # Setup mock response with complete structure expected by QA agent
        mock_response = {
            "test_strategy": {
                "approach": "comprehensive",
                "scope": "Unit and integration testing",
                "test_levels": ["unit", "integration"],
            },
            "test_cases": [
                {
                    "id": "TC-001",
                    "title": "User login test",
                    "category": "functional",
                    "priority": "high",
                }
            ],
            "test_execution": {
                "execution_summary": {
                    "total_test_cases": 10,
                    "passed": 10,
                    "failed": 0,
                    "pass_rate": "100%",
                },
                "test_results": [],
            },
            "quality_metrics": {
                "coverage_analysis": {
                    "requirements_coverage": "95%",
                    "code_coverage": "95.5%",
                }
            },
        }
        mock_claude_api.return_value = json.dumps(mock_response)

        agent = QATesterAgent(path_config=isolated_agilevv_dir)

        # Create input
        testing_input = TestingInput(
            story_id="US-001",
            stage=VModelStage.UNIT_TESTING,
            context={"implementation_complete": True},
            test_scope=["unit", "integration"],
            acceptance_criteria=["User can login", "User can logout"],
        )

        # Process
        result = await agent.process(testing_input.model_dump())

        # Validate result structure
        assert isinstance(result, dict)
        assert result["status"] == "success"
        assert result["next_stage_ready"] is True
        assert "testing_data" in result
        assert "quality_assessment" in result

        # Validate that artifacts were saved
        test_artifact_path = isolated_agilevv_dir.base_dir / "testing" / "US-001.json"
        assert test_artifact_path.exists()

    @patch("verifflowcc.agents.qa_tester.QATesterAgent._call_claude_sdk")
    async def test_process_with_api_failure(
        self, mock_claude_api: Any, isolated_agilevv_dir: PathConfig
    ) -> None:
        """Test process method handles API failures gracefully."""
        # Setup mock to raise an exception
        mock_claude_api.side_effect = Exception("API Error: Test generation failed")

        agent = QATesterAgent(path_config=isolated_agilevv_dir)

        testing_input = TestingInput(
            story_id="US-002",
            stage=VModelStage.UNIT_TESTING,
            context={},
            test_scope=["unit"],
            acceptance_criteria=["Basic functionality works"],
        )

        # Process should handle the error
        result = await agent.process(testing_input.model_dump())

        assert result["status"] == "error"
        assert result["next_stage_ready"] is False
        assert "error" in result


class TestQATesterAgentIntegration:
    """Integration tests for QATesterAgent with V-Model workflow."""

    def test_testing_output_validation(self) -> None:
        """Test TestingOutput validation for next stage."""
        # Create valid testing output
        testing_output_data: dict[str, Any] = {
            "status": "success",
            "artifacts": {"test_report": "path/to/tests.json"},
            "test_files": ["tests/test_user.py", "tests/test_auth.py"],
            "test_results": {"passed": 15, "failed": 0, "total": 15},
            "coverage_report": {"percentage": 95.0, "missing_lines": []},
            "quality_metrics": {"test_count": 15, "assertions": 40},
            "next_stage_ready": True,
        }

        # Should validate successfully
        testing_output = TestingOutput(**testing_output_data)
        assert testing_output.status == "success"
        assert testing_output.next_stage_ready is True
        assert len(testing_output.test_files) == 2


@pytest.mark.integration
class TestQATesterAgentRealWorldScenarios:
    """Integration tests simulating real-world QA testing scenarios."""

    @pytest.mark.asyncio
    async def test_mailbuddy_complete_qa_workflow(self, isolated_agilevv_dir: PathConfig) -> None:
        """Test complete QA workflow for MailBuddy Flask application."""
        if not os.getenv("ANTHROPIC_API_KEY") and not self._is_claude_code_available():
            pytest.skip("No ANTHROPIC_API_KEY - skipping real workflow test")

        # Simulate complete V-Model context for MailBuddy
        mailbuddy_context = {
            "story_id": "MAILBUDDY-COMPLETE-QA-001",
            "task_description": "Complete QA validation for MailBuddy Flask email management system",
            "implementation_data": {
                "implementation": {
                    "source_files": [
                        "app.py",
                        "config.py",
                        "requirements.txt",
                        "models/__init__.py",
                        "models/user.py",
                        "models/email.py",
                        "models/template.py",
                        "services/__init__.py",
                        "services/auth_service.py",
                        "services/email_service.py",
                        "services/template_service.py",
                        "services/notification_service.py",
                        "api/__init__.py",
                        "api/auth_routes.py",
                        "api/email_routes.py",
                        "api/template_routes.py",
                        "api/user_routes.py",
                        "utils/__init__.py",
                        "utils/security.py",
                        "utils/validation.py",
                        "utils/helpers.py",
                        "middleware/auth_middleware.py",
                        "middleware/rate_limiter.py",
                        "templates/email_base.html",
                        "templates/welcome_email.html",
                        "templates/notification_email.html",
                        "static/css/style.css",
                        "static/js/app.js",
                        "tests/__init__.py",
                        "migrations/001_initial.sql",
                    ],
                    "technologies_used": [
                        "Flask 2.3.2",
                        "SQLAlchemy 2.0",
                        "Alembic",
                        "JWT",
                        "SendGrid API",
                        "Redis",
                        "PostgreSQL",
                        "Docker",
                        "pytest",
                        "coverage",
                    ],
                    "features_implemented": [
                        "User registration and email verification",
                        "JWT-based authentication and authorization",
                        "Email composition with rich text editor",
                        "Email template management system",
                        "Bulk email sending with queue processing",
                        "Email delivery tracking and analytics",
                        "User dashboard with email history",
                        "RESTful API endpoints",
                        "Rate limiting and security middleware",
                        "Database migrations and seed data",
                    ],
                    "code_metrics": {
                        "total_lines": 2847,
                        "complexity_score": 6.2,
                        "test_coverage": 0,  # No tests yet - QA should generate them
                        "security_scan_passed": True,
                    },
                },
                "design_reference": {
                    "functional_requirements": [
                        {
                            "id": "FR-001",
                            "description": "User registration with email verification",
                            "priority": "high",
                        },
                        {
                            "id": "FR-002",
                            "description": "Secure user authentication using JWT",
                            "priority": "critical",
                        },
                        {
                            "id": "FR-003",
                            "description": "Email composition with WYSIWYG editor",
                            "priority": "high",
                        },
                        {
                            "id": "FR-004",
                            "description": "Email template creation and management",
                            "priority": "medium",
                        },
                        {
                            "id": "FR-005",
                            "description": "Bulk email sending functionality",
                            "priority": "high",
                        },
                        {
                            "id": "FR-006",
                            "description": "Email delivery status tracking",
                            "priority": "medium",
                        },
                        {
                            "id": "FR-007",
                            "description": "User dashboard with email history",
                            "priority": "medium",
                        },
                        {
                            "id": "FR-008",
                            "description": "RESTful API for all operations",
                            "priority": "high",
                        },
                    ],
                    "non_functional_requirements": [
                        {
                            "id": "NFR-001",
                            "description": "Support 1000+ concurrent users",
                            "type": "performance",
                        },
                        {
                            "id": "NFR-002",
                            "description": "API response time < 200ms for 95% of requests",
                            "type": "performance",
                        },
                        {
                            "id": "NFR-003",
                            "description": "Email sending rate: 500 emails/minute",
                            "type": "performance",
                        },
                        {
                            "id": "NFR-004",
                            "description": "99.9% uptime availability",
                            "type": "reliability",
                        },
                        {
                            "id": "NFR-005",
                            "description": "GDPR compliance for user data",
                            "type": "security",
                        },
                        {
                            "id": "NFR-006",
                            "description": "SSL/TLS encryption for all communications",
                            "type": "security",
                        },
                    ],
                },
            },
            "testing_phase": "system",
            "context": {
                "project_name": "MailBuddy Enterprise Email Management System",
                "sprint_number": "Sprint 3",
                "team_size": 5,
                "timeline": "4 weeks",
                "deployment_target": "AWS ECS with PostgreSQL RDS",
                "expected_load": "1000 concurrent users, 10k emails/day",
                "compliance_requirements": ["GDPR", "CAN-SPAM Act"],
                "integration_services": ["SendGrid", "Redis", "PostgreSQL", "AWS S3"],
            },
        }

        # Create QA agent and process complete scenario
        agent = QATesterAgent(
            name="mailbuddy_qa_complete",
            path_config=isolated_agilevv_dir,
            sdk_config=SDKConfig(),
            mock_mode=False,
        )

        result = await agent.process(mailbuddy_context)

        # Validate comprehensive QA processing
        assert result["status"] == "success"
        assert "testing_data" in result
        assert "quality_assessment" in result

        testing_data = result["testing_data"]

        # Validate test strategy addresses all requirement types
        test_strategy = testing_data["test_strategy"]
        assert "functional" in str(test_strategy).lower()
        assert "performance" in str(test_strategy).lower() or "load" in str(test_strategy).lower()
        assert "security" in str(test_strategy).lower()

        # Validate test execution results
        test_execution = testing_data.get("test_execution", {})
        execution_summary = test_execution.get("execution_summary", {})
        assert "total_test_cases" in execution_summary
        assert "pass_rate" in execution_summary

        # Validate quality assessment for next stage readiness
        quality_assessment = result["quality_assessment"]
        assert "overall_quality" in quality_assessment
        assert "readiness_for_next_stage" in quality_assessment
        assert "recommendations" in quality_assessment
        assert quality_assessment["overall_quality"] in [
            "excellent",
            "good",
            "acceptable",
            "poor",
        ]

        # Validate all artifacts are created
        artifacts = result["artifacts"]
        for artifact_type in [
            "test_report",
            "test_strategy",
            "test_cases",
            "test_results",
            "traceability_matrix",
        ]:
            assert artifact_type in artifacts
            artifact_path = Path(isolated_agilevv_dir.base_dir) / artifacts[artifact_type]
            assert artifact_path.exists(), f"Missing artifact: {artifact_type}"

    def _is_claude_code_available(self) -> bool:
        """Check if Claude Code subscription is available."""
        return False
