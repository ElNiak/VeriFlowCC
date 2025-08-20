"""Tests for validating AI-generated task documentation and Flask implementation patterns.

This module tests that real Claude Code SDK generates implementable task documentation
with valid Flask patterns and practical code examples for MailBuddy integration.
"""

import os
import re
from typing import Any

import pytest
from verifflowcc.agents.developer import DeveloperAgent
from verifflowcc.core.sdk_config import SDKConfig
from verifflowcc.core.vmodel import VModelStage
from verifflowcc.schemas.agent_schemas import ImplementationInput


class TestAIGeneratedTaskValidation:
    """Test validation of AI-generated task documentation and implementation patterns."""

    @pytest.fixture
    def sdk_config(self) -> SDKConfig:
        """Provide SDK configuration for task generation testing."""
        api_key = os.getenv("ANTHROPIC_API_KEY", "test-key")
        return SDKConfig(
            api_key=api_key,
            timeout=120,  # Extended timeout for comprehensive task generation
            max_retries=2,
        )

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_ai_generated_flask_task_documentation(
        self, isolated_agilevv_dir: Any, sdk_config: SDKConfig
    ) -> None:
        """Test that AI generates comprehensive Flask task documentation."""
        # Skip if no real API key available
        if sdk_config.api_key == "test-key":
            pytest.skip("No real API key available for Flask task documentation test")

        agent = DeveloperAgent(
            path_config=isolated_agilevv_dir, sdk_config=sdk_config, mock_mode=False
        )

        # Request comprehensive task documentation for MailBuddy Flask features
        task_doc_input = ImplementationInput(
            story_id="FLASK-TASK-DOC-001",
            stage=VModelStage.CODING,
            context={
                "documentation_focus": True,
                "generate_tasks_md": True,
                "project": "MailBuddy",
                "output_format": "markdown",
            },
            design_artifacts={
                "documentation_requirements": {
                    "task_breakdown": "detailed implementation tasks",
                    "code_examples": "practical Flask code snippets",
                    "implementation_patterns": "Flask best practices",
                    "testing_approaches": "pytest test patterns",
                },
                "features_to_document": [
                    "User authentication with Flask-Login",
                    "Email management with SMTP/IMAP",
                    "RESTful API design with Flask-RESTful",
                    "Database operations with SQLAlchemy",
                    "Frontend integration with Flask templates",
                ],
            },
            architecture_context={
                "framework": "Flask",
                "application": "MailBuddy",
                "documentation_style": "task-oriented",
                "target_audience": "developers implementing features",
            },
        )

        result = await agent.process(task_doc_input.model_dump())
        assert result["status"] == "success"

        # Extract generated documentation
        impl_data = result.get("implementation_data", {})

        # Look for task documentation in various locations
        task_content = ""

        # Check response text for task documentation
        if "response_text" in impl_data:
            task_content += impl_data["response_text"]

        # Check generated files for tasks.md
        implementation = impl_data.get("implementation", {})
        files = implementation.get("files", [])

        for file_info in files:
            if isinstance(file_info, dict):
                file_path = file_info.get("path", "")
                file_content = file_info.get("content", "")

                # Look for task-related files
                if any(
                    indicator in file_path.lower()
                    for indicator in ["task", "todo", "implement", "guide"]
                ):
                    task_content += f"\n\n=== {file_path} ===\n{file_content}"
                elif file_path.endswith(".md") and any(
                    keyword in file_content.lower()
                    for keyword in ["task", "implement", "step", "todo"]
                ):
                    task_content += f"\n\n=== {file_path} ===\n{file_content}"

        # Validate task documentation content
        assert len(task_content) >= 100, "Task documentation should be substantial"

        # Check for Flask-specific task patterns
        flask_task_patterns = [
            "Flask",
            "app.route",
            "blueprint",
            "request",
            "jsonify",
            "render_template",
        ]

        flask_pattern_count = sum(
            1 for pattern in flask_task_patterns if pattern.lower() in task_content.lower()
        )
        assert (
            flask_pattern_count >= 3
        ), f"Task documentation should contain Flask patterns. Found: {flask_pattern_count}"

        # Check for MailBuddy-specific patterns
        mailbuddy_patterns = [
            "email",
            "mail",
            "smtp",
            "imap",
            "user",
            "authentication",
            "message",
        ]

        mailbuddy_pattern_count = sum(
            1 for pattern in mailbuddy_patterns if pattern.lower() in task_content.lower()
        )
        assert (
            mailbuddy_pattern_count >= 4
        ), f"Task documentation should contain MailBuddy patterns. Found: {mailbuddy_pattern_count}"

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_implementable_flask_code_examples(
        self, isolated_agilevv_dir: Any, sdk_config: SDKConfig
    ) -> None:
        """Test that AI generates implementable Flask code examples in task documentation."""
        # Skip if no real API key available
        if sdk_config.api_key == "test-key":
            pytest.skip("No real API key available for Flask code examples test")

        agent = DeveloperAgent(
            path_config=isolated_agilevv_dir, sdk_config=sdk_config, mock_mode=False
        )

        # Request task documentation with specific focus on code examples
        code_examples_input = ImplementationInput(
            story_id="FLASK-CODE-EXAMPLES-001",
            stage=VModelStage.CODING,
            context={
                "code_examples_focus": True,
                "practical_implementations": True,
                "working_code_snippets": True,
            },
            design_artifacts={
                "code_example_requirements": {
                    "flask_routes": "Complete route implementations",
                    "database_models": "SQLAlchemy model examples",
                    "authentication": "Flask-Login integration patterns",
                    "api_responses": "JSON response formatting",
                    "error_handling": "Flask error handling patterns",
                },
                "example_scenarios": [
                    "User registration endpoint with validation",
                    "Email sending functionality with SMTP",
                    "Database query patterns for email retrieval",
                    "JWT token generation and validation",
                    "File upload handling for attachments",
                ],
            },
            architecture_context={
                "framework": "Flask",
                "examples_style": "complete_working_code",
                "include_imports": True,
                "include_error_handling": True,
            },
        )

        result = await agent.process(code_examples_input.model_dump())
        assert result["status"] == "success"

        # Extract all generated content
        impl_data = result.get("implementation_data", {})
        all_content = ""

        # Collect all generated content
        if "response_text" in impl_data:
            all_content += impl_data["response_text"]

        implementation = impl_data.get("implementation", {})
        files = implementation.get("files", [])

        for file_info in files:
            if isinstance(file_info, dict):
                all_content += f"\n{file_info.get('content', '')}"

        # Validate implementable code examples
        assert len(all_content) >= 200, "Should have substantial code examples"

        # Check for implementable Flask code patterns
        implementable_patterns = {
            "imports": ["from flask import", "import flask", "from sqlalchemy"],
            "routes": ["@app.route", "@blueprint.route", "def "],
            "database": ["db.Model", "db.Column", "db.create_all"],
            "requests": ["request.json", "request.form", "request.args"],
            "responses": ["jsonify", "return ", "make_response"],
            "authentication": ["login_required", "current_user", "login_user"],
        }

        pattern_matches = {}
        content_lower = all_content.lower()

        for category, patterns in implementable_patterns.items():
            matches = sum(1 for pattern in patterns if pattern.lower() in content_lower)
            pattern_matches[category] = matches

        # Validate that we have implementable code patterns
        assert pattern_matches["imports"] >= 1, "Should have import statements"
        assert pattern_matches["routes"] >= 1, "Should have route definitions"
        assert (
            sum(pattern_matches.values()) >= 6
        ), f"Should have diverse Flask patterns: {pattern_matches}"

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_flask_best_practices_in_tasks(
        self, isolated_agilevv_dir: Any, sdk_config: SDKConfig
    ) -> None:
        """Test that AI-generated tasks include Flask best practices."""
        # Skip if no real API key available
        if sdk_config.api_key == "test-key":
            pytest.skip("No real API key available for Flask best practices test")

        agent = DeveloperAgent(
            path_config=isolated_agilevv_dir, sdk_config=sdk_config, mock_mode=False
        )

        # Request task documentation focused on best practices
        best_practices_input = ImplementationInput(
            story_id="FLASK-BEST-PRACTICES-001",
            stage=VModelStage.CODING,
            context={
                "best_practices_focus": True,
                "production_ready": True,
                "security_considerations": True,
                "performance_optimization": True,
            },
            design_artifacts={
                "best_practices_areas": {
                    "security": "Authentication, CSRF protection, input validation",
                    "performance": "Database queries, caching, request optimization",
                    "maintainability": "Code organization, error handling, logging",
                    "testing": "Unit tests, integration tests, test patterns",
                    "deployment": "Configuration management, environment setup",
                },
                "flask_specific_practices": [
                    "Blueprint organization",
                    "Application factory pattern",
                    "Database migration strategies",
                    "Session management",
                    "API versioning approaches",
                ],
            },
            architecture_context={
                "framework": "Flask",
                "focus": "production_best_practices",
                "target_environment": "production",
            },
        )

        result = await agent.process(best_practices_input.model_dump())
        assert result["status"] == "success"

        # Extract generated content
        impl_data = result.get("implementation_data", {})
        all_content = ""

        if "response_text" in impl_data:
            all_content += impl_data["response_text"]

        implementation = impl_data.get("implementation", {})
        files = implementation.get("files", [])

        for file_info in files:
            if isinstance(file_info, dict):
                all_content += f"\n{file_info.get('content', '')}"

        # Check for Flask best practices patterns
        best_practices_indicators = {
            "security": ["csrf", "validate", "sanitiz", "hash", "encrypt", "secure"],
            "organization": ["blueprint", "factory", "config", "module", "structure"],
            "error_handling": ["try", "except", "error", "handle", "log"],
            "testing": ["test", "assert", "mock", "fixture", "pytest"],
            "performance": ["cache", "query", "optimize", "index", "performance"],
        }

        practices_found = {}
        content_lower = all_content.lower()

        for category, indicators in best_practices_indicators.items():
            count = sum(1 for indicator in indicators if indicator in content_lower)
            practices_found[category] = count

        # Validate best practices are included
        assert practices_found["security"] >= 2, "Should include security best practices"
        assert practices_found["organization"] >= 1, "Should include code organization practices"
        assert (
            sum(practices_found.values()) >= 8
        ), f"Should have diverse best practices: {practices_found}"

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_mailbuddy_specific_implementation_tasks(
        self, isolated_agilevv_dir: Any, sdk_config: SDKConfig
    ) -> None:
        """Test that AI generates MailBuddy-specific implementation tasks."""
        # Skip if no real API key available
        if sdk_config.api_key == "test-key":
            pytest.skip("No real API key available for MailBuddy tasks test")

        agent = DeveloperAgent(
            path_config=isolated_agilevv_dir, sdk_config=sdk_config, mock_mode=False
        )

        # Request MailBuddy-specific task breakdown
        mailbuddy_tasks_input = ImplementationInput(
            story_id="MAILBUDDY-TASKS-001",
            stage=VModelStage.CODING,
            context={
                "project_specific": True,
                "application": "MailBuddy",
                "detailed_task_breakdown": True,
            },
            design_artifacts={
                "mailbuddy_features": {
                    "email_management": {
                        "send_emails": "SMTP integration with Flask-Mail",
                        "receive_emails": "IMAP integration for inbox management",
                        "organize_emails": "Folder and label system",
                        "search_emails": "Full-text search functionality",
                    },
                    "user_management": {
                        "registration": "User account creation with validation",
                        "authentication": "Secure login with session management",
                        "preferences": "User settings and email configuration",
                    },
                    "api_design": {
                        "rest_endpoints": "RESTful API for email operations",
                        "websocket_support": "Real-time email notifications",
                        "api_documentation": "Swagger/OpenAPI documentation",
                    },
                }
            },
            architecture_context={
                "application": "MailBuddy",
                "framework": "Flask",
                "email_protocols": ["SMTP", "IMAP"],
                "real_time_features": True,
            },
        )

        result = await agent.process(mailbuddy_tasks_input.model_dump())
        assert result["status"] == "success"

        # Extract and analyze MailBuddy-specific content
        impl_data = result.get("implementation_data", {})
        all_content = ""

        if "response_text" in impl_data:
            all_content += impl_data["response_text"]

        implementation = impl_data.get("implementation", {})
        files = implementation.get("files", [])

        for file_info in files:
            if isinstance(file_info, dict):
                all_content += f"\n{file_info.get('content', '')}"

        # Check for MailBuddy-specific implementation patterns
        mailbuddy_implementation_patterns = {
            "email_protocols": ["smtp", "imap", "pop3", "email", "mail"],
            "message_handling": ["message", "attachment", "mime", "content", "body"],
            "user_features": ["user", "account", "login", "session", "auth"],
            "data_management": ["database", "model", "query", "store", "persist"],
            "api_patterns": ["route", "endpoint", "api", "json", "response"],
            "integration": ["integration", "service", "client", "connection", "config"],
        }

        mailbuddy_matches = {}
        content_lower = all_content.lower()

        for category, patterns in mailbuddy_implementation_patterns.items():
            count = sum(1 for pattern in patterns if pattern in content_lower)
            mailbuddy_matches[category] = count

        # Validate MailBuddy-specific implementation coverage
        assert (
            mailbuddy_matches["email_protocols"] >= 2
        ), "Should include email protocol implementation tasks"
        assert mailbuddy_matches["message_handling"] >= 3, "Should include message handling tasks"
        assert mailbuddy_matches["user_features"] >= 2, "Should include user management tasks"
        assert (
            sum(mailbuddy_matches.values()) >= 12
        ), f"Should have comprehensive MailBuddy tasks: {mailbuddy_matches}"

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_task_documentation_structure_validation(
        self, isolated_agilevv_dir: Any, sdk_config: SDKConfig
    ) -> None:
        """Test that AI-generated task documentation follows proper structure."""
        # Skip if no real API key available
        if sdk_config.api_key == "test-key":
            pytest.skip("No real API key available for task structure test")

        agent = DeveloperAgent(
            path_config=isolated_agilevv_dir, sdk_config=sdk_config, mock_mode=False
        )

        # Request well-structured task documentation
        structured_tasks_input = ImplementationInput(
            story_id="STRUCTURED-TASKS-001",
            stage=VModelStage.CODING,
            context={
                "structured_documentation": True,
                "markdown_format": True,
                "hierarchical_tasks": True,
            },
            design_artifacts={
                "documentation_structure": {
                    "format": "markdown",
                    "sections": ["overview", "tasks", "implementation", "testing"],
                    "task_format": "numbered_checklist",
                    "code_blocks": "syntax_highlighted",
                },
                "content_requirements": {
                    "clear_headings": "H1, H2, H3 hierarchy",
                    "task_lists": "checkboxes for tracking progress",
                    "code_examples": "properly formatted code blocks",
                    "implementation_notes": "helpful context and tips",
                },
            },
            architecture_context={
                "framework": "Flask",
                "documentation_style": "technical_guide",
                "target_format": "markdown",
            },
        )

        result = await agent.process(structured_tasks_input.model_dump())
        assert result["status"] == "success"

        # Extract documentation content
        impl_data = result.get("implementation_data", {})
        doc_content = ""

        if "response_text" in impl_data:
            doc_content += impl_data["response_text"]

        # Look for markdown files specifically
        implementation = impl_data.get("implementation", {})
        files = implementation.get("files", [])

        for file_info in files:
            if isinstance(file_info, dict):
                file_path = file_info.get("path", "")
                file_content = file_info.get("content", "")

                if file_path.endswith(".md"):
                    doc_content += f"\n{file_content}"

        # Validate markdown structure patterns
        markdown_structure_patterns = {
            "headings": [r"#{1,3}\s+", r"^#+ ", r"##+ "],
            "lists": [r"^\d+\.", r"^- ", r"^\* ", r"- \[ \]", r"- \[x\]"],
            "code_blocks": [r"```\w*", r"```python", r"```flask", r"`[^`]+`"],
            "links": [r"\[.+\]\(.+\)", r"http[s]?://", r"www\."],
        }

        structure_matches = {}
        for category, patterns in markdown_structure_patterns.items():
            count = 0
            for pattern in patterns:
                matches = re.findall(pattern, doc_content, re.MULTILINE | re.IGNORECASE)
                count += len(matches)
            structure_matches[category] = count

        # Validate proper documentation structure
        assert structure_matches["headings"] >= 3, "Should have proper heading hierarchy"
        assert structure_matches["lists"] >= 5, "Should have task lists and bullet points"
        assert structure_matches["code_blocks"] >= 2, "Should have code examples"
        assert len(doc_content) >= 300, "Should have substantial documentation content"

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_task_implementation_completeness(
        self, isolated_agilevv_dir: Any, sdk_config: SDKConfig
    ) -> None:
        """Test that generated tasks provide complete implementation guidance."""
        # Skip if no real API key available
        if sdk_config.api_key == "test-key":
            pytest.skip("No real API key available for implementation completeness test")

        agent = DeveloperAgent(
            path_config=isolated_agilevv_dir, sdk_config=sdk_config, mock_mode=False
        )

        # Request comprehensive implementation guidance
        complete_guidance_input = ImplementationInput(
            story_id="COMPLETE-GUIDANCE-001",
            stage=VModelStage.CODING,
            context={
                "comprehensive_guidance": True,
                "step_by_step": True,
                "implementation_details": True,
            },
            design_artifacts={
                "guidance_requirements": {
                    "setup_instructions": "Environment and dependency setup",
                    "implementation_steps": "Detailed coding steps",
                    "configuration": "Application configuration guidance",
                    "testing_instructions": "How to test implementations",
                    "troubleshooting": "Common issues and solutions",
                },
                "completeness_criteria": [
                    "Dependencies and requirements clearly listed",
                    "Step-by-step implementation instructions",
                    "Code examples for each major component",
                    "Testing strategies and examples",
                    "Deployment and configuration guidance",
                ],
            },
            architecture_context={
                "framework": "Flask",
                "completeness_focus": True,
                "beginner_friendly": True,
            },
        )

        result = await agent.process(complete_guidance_input.model_dump())
        assert result["status"] == "success"

        # Extract all guidance content
        impl_data = result.get("implementation_data", {})
        all_guidance = ""

        if "response_text" in impl_data:
            all_guidance += impl_data["response_text"]

        implementation = impl_data.get("implementation", {})
        files = implementation.get("files", [])

        for file_info in files:
            if isinstance(file_info, dict):
                all_guidance += f"\n{file_info.get('content', '')}"

        # Check for implementation completeness indicators
        completeness_indicators = {
            "setup": ["install", "pip", "requirement", "dependency", "setup"],
            "configuration": [
                "config",
                "setting",
                "environment",
                "variable",
                "configure",
            ],
            "implementation": ["implement", "create", "define", "build", "develop"],
            "testing": ["test", "assert", "verify", "validate", "check"],
            "deployment": ["deploy", "production", "server", "host", "run"],
        }

        completeness_scores = {}
        content_lower = all_guidance.lower()

        for category, indicators in completeness_indicators.items():
            score = sum(1 for indicator in indicators if indicator in content_lower)
            completeness_scores[category] = score

        # Validate implementation completeness
        assert completeness_scores["setup"] >= 2, "Should provide setup instructions"
        assert completeness_scores["implementation"] >= 3, "Should provide implementation guidance"
        assert completeness_scores["testing"] >= 1, "Should include testing guidance"
        assert (
            sum(completeness_scores.values()) >= 10
        ), f"Should have comprehensive guidance: {completeness_scores}"

        # Validate content substance
        assert len(all_guidance) >= 500, "Should provide substantial implementation guidance"
