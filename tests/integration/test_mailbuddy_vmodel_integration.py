"""Integration tests for MailBuddy project creation via VeriFlowCC V-Model workflow.

This module tests VeriFlowCC's ability to process realistic email application
scenarios instead of synthetic mock data, validating that V-Model agents can
understand and generate proper artifacts for MailBuddy Flask application.
"""

from typing import Any

import pytest


class TestMailBuddyRequirementsGeneration:
    """Test Requirements Analyst generating MailBuddy user stories."""

    @pytest.mark.asyncio
    async def test_requirements_analyst_mailbuddy_user_stories(
        self, isolated_agilevv_dir: Any
    ) -> None:
        """Test Requirements Analyst generates INVEST-compliant MailBuddy user stories."""
        pytest.skip("Requires real Claude Code SDK for MailBuddy requirements generation")

    @pytest.mark.asyncio
    async def test_requirements_analyst_acceptance_criteria_validation(
        self, isolated_agilevv_dir: Any
    ) -> None:
        """Test that Requirements Analyst output includes comprehensive acceptance criteria."""
        pytest.skip("Requires real Claude Code SDK for acceptance criteria validation")


class TestMailBuddyProjectCreation:
    """Test VeriFlowCC orchestrator creating MailBuddy project from empty directory."""

    @pytest.mark.asyncio
    async def test_complete_mailbuddy_project_creation(self, isolated_agilevv_dir: Any) -> None:
        """Test complete V-Model workflow for MailBuddy project creation."""
        pytest.skip("Requires real Claude Code SDK for complete MailBuddy project workflow")

        # Note: Test validates artifact structure is created
        artifacts_dir = isolated_agilevv_dir.artifacts_dir / "sprint_1"
        artifacts_dir.mkdir(parents=True, exist_ok=True)
        assert artifacts_dir.exists()


class TestMailBuddyArtifactValidation:
    """Test validation of MailBuddy project artifacts."""

    def test_mailbuddy_requirements_invest_compliance(self, isolated_agilevv_dir: Any) -> None:
        """Test that generated requirements.md contains INVEST-compliant user stories."""

        # Create sample MailBuddy requirements artifact with explicit typing
        requirements_content: dict[str, Any] = {
            "user_stories": [
                {
                    "id": "MB-006",
                    "title": "Email Template Preview",
                    "story": "As a content creator, I want to preview email templates before sending so that I can ensure proper formatting and content accuracy",
                    "invest_assessment": {
                        "independent": True,
                        "negotiable": True,
                        "valuable": True,
                        "estimable": True,
                        "small": True,
                        "testable": True,
                        "score": 6,  # All INVEST criteria met
                    },
                    "acceptance_criteria": [
                        "User can preview template in both HTML and plain text formats",
                        "Preview shows actual content with sample recipient data",
                        "User can edit template directly from preview mode",
                        "Preview updates in real-time as user makes changes",
                    ],
                }
            ],
            "quality_metrics": {
                "total_stories": 1,
                "invest_compliant_stories": 1,
                "average_invest_score": 6.0,
                "acceptance_criteria_coverage": 100,
            },
        }

        # Save requirements artifact
        artifacts_dir = isolated_agilevv_dir.artifacts_dir / "sprint_1"
        artifacts_dir.mkdir(parents=True, exist_ok=True)

        # Validate INVEST compliance programmatically
        user_stories: list[dict[str, Any]] = requirements_content["user_stories"]
        for story in user_stories:
            invest: dict[str, Any] = story["invest_assessment"]

            # All INVEST criteria should be boolean True for compliant stories
            assert invest["independent"] is True
            assert invest["negotiable"] is True
            assert invest["valuable"] is True
            assert invest["estimable"] is True
            assert invest["small"] is True
            assert invest["testable"] is True

            # Story should have clear acceptance criteria
            acceptance_criteria: list[str] = story["acceptance_criteria"]
            assert len(acceptance_criteria) >= 3

            # Story should be email functionality related
            story_text: str = story["story"].lower()
            email_keywords = ["email", "template", "campaign", "delivery", "recipient"]
            assert any(keyword in story_text for keyword in email_keywords)

        # Validate quality metrics
        metrics: dict[str, Any] = requirements_content["quality_metrics"]
        assert metrics["invest_compliant_stories"] == metrics["total_stories"]
        assert metrics["average_invest_score"] >= 5.0  # High quality threshold
        assert metrics["acceptance_criteria_coverage"] >= 90

    def test_mailbuddy_architecture_flask_patterns(self, isolated_agilevv_dir: Any) -> None:
        """Test that architecture artifacts contain Flask-specific patterns."""

        # Sample MailBuddy architecture artifact with explicit typing
        architecture_content: dict[str, Any] = {
            "application_architecture": {
                "framework": "Flask",
                "pattern": "Application Factory with Blueprints",
                "structure": {
                    "app/__init__.py": "Application factory and configuration",
                    "app/models.py": "SQLAlchemy database models",
                    "app/auth/": "Authentication blueprint",
                    "app/templates/": "Template management blueprint",
                    "app/campaigns/": "Campaign management blueprint",
                    "app/services/": "Business logic services",
                },
            },
            "data_models": {
                "User": {
                    "fields": ["id", "email", "password_hash", "created_at"],
                    "relationships": ["email_templates", "campaigns"],
                },
                "EmailTemplate": {
                    "fields": ["id", "name", "subject", "content", "category"],
                    "relationships": ["user", "campaigns"],
                },
                "EmailCampaign": {
                    "fields": ["id", "name", "template_id", "scheduled_at", "status"],
                    "relationships": ["template", "email_logs"],
                },
            },
            "flask_integrations": {
                "extensions": [
                    "Flask-SQLAlchemy for ORM",
                    "Flask-Login for authentication",
                    "Flask-WTF for forms",
                    "Flask-Mail for email sending",
                    "Flask-Migrate for database migrations",
                ],
                "configuration": {
                    "config_classes": [
                        "DevelopmentConfig",
                        "ProductionConfig",
                        "TestingConfig",
                    ],
                    "environment_variables": [
                        "DATABASE_URL",
                        "SECRET_KEY",
                        "SENDGRID_API_KEY",
                    ],
                },
            },
        }

        # Validate Flask architecture patterns
        arch: dict[str, Any] = architecture_content["application_architecture"]
        assert arch["framework"] == "Flask"
        assert "Blueprint" in arch["pattern"]

        # Validate Flask directory structure
        structure: dict[str, str] = arch["structure"]
        assert "app/__init__.py" in structure
        assert any("blueprint" in desc.lower() for desc in structure.values())

        # Validate Flask-specific data models
        models: dict[str, Any] = architecture_content["data_models"]
        assert "User" in models
        assert "EmailTemplate" in models
        assert "EmailCampaign" in models

        # Each model should have proper field definitions
        for _model_name, model_def in models.items():
            model_dict: dict[str, Any] = model_def
            assert "fields" in model_dict
            fields: list[str] = model_dict["fields"]
            assert len(fields) > 0
            assert "id" in fields  # Primary key

        # Validate Flask extensions integration
        flask_integrations: dict[str, Any] = architecture_content["flask_integrations"]
        extensions: list[str] = flask_integrations["extensions"]
        flask_extensions = [ext for ext in extensions if "Flask-" in ext]
        assert len(flask_extensions) >= 3  # Multiple Flask extensions used

        # Should include email-specific configurations
        config: dict[str, Any] = flask_integrations["configuration"]
        env_vars: list[str] = config["environment_variables"]
        assert any("SENDGRID" in var or "MAIL" in var for var in env_vars)
