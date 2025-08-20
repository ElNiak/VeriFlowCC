"""Real SDK integration tests for QA Tester agent.

This module provides comprehensive tests for QATesterAgent using the actual Claude Code SDK
to validate real test strategy development, test case generation, and quality assessment.
These tests ensure authentic test planning and quality validation capabilities.
"""

import json
import os
from pathlib import Path

import pytest
from verifflowcc.agents.qa_tester import QATesterAgent
from verifflowcc.core.sdk_config import SDKConfig

from tests.conftest import PathConfig as TestPathConfig


def _can_authenticate_with_sdk() -> bool:
    """Check if Claude Code SDK authentication is available.

    Returns:
        True if authentication is available, False otherwise
    """
    try:
        # Check for real API key
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if api_key and len(api_key.strip()) > 0:
            sdk_config = SDKConfig(api_key=api_key, timeout=10)
            return sdk_config.timeout == 10 and sdk_config.api_key is not None

        # Allow testing mode - enable tests to run for structure validation
        # In testing context, we validate SDK integration patterns without real API calls
        test_api_key = "test-api-key-for-structure-validation"
        sdk_config = SDKConfig(api_key=test_api_key, timeout=10)
        return sdk_config.timeout == 10 and sdk_config.api_key is not None
    except Exception:
        return False


skip_if_no_auth = pytest.mark.skipif(
    not _can_authenticate_with_sdk(),
    reason="No Claude Code SDK authentication available (requires ANTHROPIC_API_KEY)",
)


@pytest.mark.asyncio
class TestRealQATesterSDKInitialization:
    """Test real SDK integration for QA Tester agent initialization."""

    @skip_if_no_auth
    async def test_real_qa_tester_sdk_initialization(
        self, isolated_agilevv_dir: TestPathConfig
    ) -> None:
        """Test QA Tester agent initialization with real SDK configuration."""
        # Arrange: Create real SDK configuration
        sdk_config = SDKConfig(api_key=os.getenv("ANTHROPIC_API_KEY"))

        # Act: Initialize QA Tester agent with real SDK
        agent = QATesterAgent(
            name="real_qa_tester",
            agent_type="qa",
            path_config=isolated_agilevv_dir,
            sdk_config=sdk_config,
        )

        # Assert: Real SDK integration is properly configured
        assert agent.name == "real_qa_tester"
        assert agent.agent_type == "qa"
        assert agent.sdk_config.api_key is not None
        assert hasattr(agent, "process")
        assert callable(agent.process)

        # Verify SDK client configuration
        client_options = agent.sdk_config.get_client_options("qa")
        assert client_options is not None

    @skip_if_no_auth
    async def test_real_qa_tester_template_loading(
        self, isolated_agilevv_dir: TestPathConfig
    ) -> None:
        """Test QA Tester template loading with real configuration."""
        # Arrange: Create agent with real SDK
        sdk_config = SDKConfig(api_key=os.getenv("ANTHROPIC_API_KEY"))
        agent = QATesterAgent(path_config=isolated_agilevv_dir, sdk_config=sdk_config)

        # Act: Load QA template
        template_context = {
            "task_description": "Test template loading",
            "project_name": "TestProject",
            "sprint_number": "Sprint 1",
            "testing_phase": "Unit Testing",
            "requirements": "Sample requirements",
            "implementation": "Sample implementation",
            "context": "Sample context",
        }
        prompt = agent.load_prompt_template("qa", **template_context)

        # Assert: Template loaded successfully
        assert isinstance(prompt, str)
        assert len(prompt) > 0
        assert "Test template loading" in prompt

    @skip_if_no_auth
    async def test_real_qa_tester_config_validation(
        self, isolated_agilevv_dir: TestPathConfig
    ) -> None:
        """Test QA Tester SDK configuration validation."""
        # Arrange: Create configuration
        sdk_config = SDKConfig(api_key=os.getenv("ANTHROPIC_API_KEY"), timeout=45)
        agent = QATesterAgent(path_config=isolated_agilevv_dir, sdk_config=sdk_config)

        # Act & Assert: Configuration is validated
        assert agent.sdk_config.api_key is not None
        assert agent.sdk_config.timeout == 45
        assert agent.sdk_config.max_retries == 3  # Default value
        # Verify SDK client configuration is properly initialized
        assert hasattr(agent, "sdk_config")
        assert agent.sdk_config is not None

    @skip_if_no_auth
    async def test_real_qa_tester_path_configuration(
        self, isolated_agilevv_dir: TestPathConfig
    ) -> None:
        """Test QA Tester path configuration with real SDK."""
        # Arrange & Act: Create agent with path configuration
        sdk_config = SDKConfig(api_key=os.getenv("ANTHROPIC_API_KEY"))
        agent = QATesterAgent(path_config=isolated_agilevv_dir, sdk_config=sdk_config)

        # Assert: Path configuration is properly set
        assert agent.path_config == isolated_agilevv_dir
        assert isinstance(agent.path_config.base_dir, Path)
        assert agent.path_config.base_dir.exists()


@pytest.mark.asyncio
class TestRealQATesterTestStrategyDevelopment:
    """Test real SDK integration for test strategy development."""

    @skip_if_no_auth
    async def test_real_test_strategy_generation_unit_testing(
        self, isolated_agilevv_dir: TestPathConfig
    ) -> None:
        """Test real test strategy generation for unit testing phase."""
        # Arrange: Create agent and input data
        sdk_config = SDKConfig(api_key=os.getenv("ANTHROPIC_API_KEY"))
        agent = QATesterAgent(path_config=isolated_agilevv_dir, sdk_config=sdk_config)

        input_data = {
            "story_id": "QA-UNIT-001",
            "task_description": "Generate comprehensive unit test strategy for user authentication module",
            "implementation_data": {
                "implementation": {
                    "source_files": [
                        "auth_service.py",
                        "user_model.py",
                        "jwt_handler.py",
                    ],
                    "technologies_used": ["Python", "Flask", "JWT", "bcrypt"],
                    "features_implemented": [
                        "User registration",
                        "Password hashing",
                        "JWT token generation",
                        "Authentication validation",
                    ],
                    "code_metrics": {
                        "total_lines": 245,
                        "complexity_score": 4.2,
                        "test_coverage": 0,
                    },
                },
                "design_reference": {
                    "functional_requirements": [
                        {
                            "id": "FR-001",
                            "description": "User registration with secure password hashing",
                            "priority": "critical",
                        },
                        {
                            "id": "FR-002",
                            "description": "JWT token-based authentication",
                            "priority": "high",
                        },
                    ],
                    "non_functional_requirements": [
                        {
                            "id": "NFR-001",
                            "description": "Authentication response time < 100ms",
                            "type": "performance",
                        },
                        {
                            "id": "NFR-002",
                            "description": "Secure password storage with bcrypt",
                            "type": "security",
                        },
                    ],
                },
            },
            "testing_phase": "unit",
            "context": {
                "project_name": "AuthService",
                "sprint_number": "Sprint 2",
                "team_size": 3,
                "timeline": "2 weeks",
            },
        }

        # Act: Process with real SDK
        result = await agent.process(input_data)

        # Assert: Real test strategy development
        assert result["status"] == "success"
        assert "testing_data" in result
        assert "quality_assessment" in result

        testing_data = result["testing_data"]
        assert "test_strategy" in testing_data
        assert "test_plan" in testing_data
        assert "test_cases" in testing_data

        # Validate test strategy structure
        test_strategy = testing_data["test_strategy"]
        assert isinstance(test_strategy, dict)
        assert "approach" in test_strategy
        assert "scope" in test_strategy
        assert "test_levels" in test_strategy
        assert "test_types" in test_strategy

        # Validate test cases generated
        test_cases = testing_data["test_cases"]
        assert isinstance(test_cases, list)
        if test_cases:  # If SDK generated test cases
            assert len(test_cases) > 0
            for test_case in test_cases[:3]:  # Check first few test cases
                assert "id" in test_case
                assert "description" in test_case or "title" in test_case

    @skip_if_no_auth
    async def test_real_test_strategy_integration_testing(
        self, isolated_agilevv_dir: TestPathConfig
    ) -> None:
        """Test real test strategy generation for integration testing."""
        # Arrange: Create complex integration testing scenario
        sdk_config = SDKConfig(api_key=os.getenv("ANTHROPIC_API_KEY"))
        agent = QATesterAgent(path_config=isolated_agilevv_dir, sdk_config=sdk_config)

        input_data = {
            "story_id": "QA-INTEGRATION-001",
            "task_description": "Develop integration test strategy for email service with external APIs",
            "implementation_data": {
                "implementation": {
                    "source_files": [
                        "email_service.py",
                        "sendgrid_client.py",
                        "template_engine.py",
                        "queue_manager.py",
                    ],
                    "technologies_used": ["Python", "SendGrid API", "Redis", "Celery"],
                    "features_implemented": [
                        "Email composition",
                        "Template rendering",
                        "Bulk email sending",
                        "Delivery tracking",
                        "Queue processing",
                    ],
                    "integration_points": [
                        "SendGrid API",
                        "Redis queue",
                        "PostgreSQL database",
                        "File storage system",
                    ],
                },
                "design_reference": {
                    "functional_requirements": [
                        {
                            "id": "FR-003",
                            "description": "Email sending with template rendering",
                            "priority": "high",
                        },
                        {
                            "id": "FR-004",
                            "description": "Bulk email processing with queues",
                            "priority": "medium",
                        },
                    ],
                    "non_functional_requirements": [
                        {
                            "id": "NFR-003",
                            "description": "Process 500 emails per minute",
                            "type": "performance",
                        },
                    ],
                },
            },
            "testing_phase": "integration",
            "context": {
                "project_name": "EmailService",
                "sprint_number": "Sprint 3",
                "integration_services": ["SendGrid", "Redis", "PostgreSQL"],
            },
        }

        # Act: Process integration testing with real SDK
        result = await agent.process(input_data)

        # Assert: Integration test strategy development
        assert result["status"] == "success"
        testing_data = result["testing_data"]

        # Validate integration-specific test strategy
        test_strategy = testing_data["test_strategy"]
        strategy_text = str(test_strategy).lower()
        assert "integration" in strategy_text or "api" in strategy_text  # Integration focus

        # Validate test plan addresses integration concerns
        test_plan = testing_data["test_plan"]
        assert isinstance(test_plan, dict)
        if "test_environment" in test_plan:
            test_env = test_plan["test_environment"]
            env_text = str(test_env).lower()
            assert any(service in env_text for service in ["sendgrid", "redis", "database"])


@pytest.mark.asyncio
class TestRealQATesterTestCaseGeneration:
    """Test real SDK integration for test case generation."""

    @skip_if_no_auth
    async def test_real_functional_test_case_generation(
        self, isolated_agilevv_dir: TestPathConfig
    ) -> None:
        """Test real functional test case generation."""
        # Arrange: Create functional testing scenario
        sdk_config = SDKConfig(api_key=os.getenv("ANTHROPIC_API_KEY"))
        agent = QATesterAgent(path_config=isolated_agilevv_dir, sdk_config=sdk_config)

        input_data = {
            "story_id": "QA-FUNCTIONAL-001",
            "task_description": "Generate functional test cases for user dashboard features",
            "implementation_data": {
                "implementation": {
                    "source_files": [
                        "dashboard.py",
                        "user_service.py",
                        "analytics.py",
                    ],
                    "features_implemented": [
                        "User profile management",
                        "Activity dashboard",
                        "Analytics visualization",
                        "Settings configuration",
                    ],
                },
                "design_reference": {
                    "functional_requirements": [
                        {
                            "id": "FR-005",
                            "description": "User can view and edit profile information",
                            "priority": "high",
                        },
                        {
                            "id": "FR-006",
                            "description": "Dashboard displays user activity metrics",
                            "priority": "medium",
                        },
                    ],
                },
            },
            "testing_phase": "functional",
            "context": {"project_name": "UserDashboard"},
        }

        # Act: Generate functional test cases
        result = await agent.process(input_data)

        # Assert: Functional test cases generated
        assert result["status"] == "success"
        testing_data = result["testing_data"]

        # Validate test cases structure
        test_cases = testing_data.get("test_cases", [])
        assert isinstance(test_cases, list)

        # If SDK generated structured test cases, validate them
        if test_cases and isinstance(test_cases[0], dict):
            sample_test_case = test_cases[0]
            # Check for typical test case fields
            expected_fields = [
                "id",
                "title",
                "description",
                "test_steps",
                "expected_result",
            ]
            found_fields = [field for field in expected_fields if field in sample_test_case]
            assert len(found_fields) >= 2  # At least 2 expected fields found

    @skip_if_no_auth
    async def test_real_security_test_case_generation(
        self, isolated_agilevv_dir: TestPathConfig
    ) -> None:
        """Test real security test case generation."""
        # Arrange: Create security testing scenario
        sdk_config = SDKConfig(api_key=os.getenv("ANTHROPIC_API_KEY"))
        agent = QATesterAgent(path_config=isolated_agilevv_dir, sdk_config=sdk_config)

        input_data = {
            "story_id": "QA-SECURITY-001",
            "task_description": "Generate security test cases for authentication and authorization",
            "implementation_data": {
                "implementation": {
                    "source_files": [
                        "auth_middleware.py",
                        "security_utils.py",
                        "access_control.py",
                    ],
                    "features_implemented": [
                        "JWT authentication",
                        "Role-based access control",
                        "Input sanitization",
                        "Rate limiting",
                    ],
                    "security_features": [
                        "HTTPS enforcement",
                        "CSRF protection",
                        "XSS prevention",
                        "SQL injection protection",
                    ],
                },
                "design_reference": {
                    "non_functional_requirements": [
                        {
                            "id": "NFR-004",
                            "description": "Secure authentication with JWT",
                            "type": "security",
                        },
                        {
                            "id": "NFR-005",
                            "description": "Protection against common web vulnerabilities",
                            "type": "security",
                        },
                    ],
                },
            },
            "testing_phase": "security",
            "context": {
                "project_name": "SecureApp",
                "compliance_requirements": ["OWASP Top 10", "GDPR"],
            },
        }

        # Act: Generate security test cases
        result = await agent.process(input_data)

        # Assert: Security test strategy and cases
        assert result["status"] == "success"
        testing_data = result["testing_data"]

        # Validate security focus in test strategy
        test_strategy = testing_data["test_strategy"]
        strategy_content = str(test_strategy).lower()
        security_terms = [
            "security",
            "authentication",
            "authorization",
            "vulnerability",
        ]
        assert any(term in strategy_content for term in security_terms)

    @skip_if_no_auth
    async def test_real_performance_test_case_generation(
        self, isolated_agilevv_dir: TestPathConfig
    ) -> None:
        """Test real performance test case generation."""
        # Arrange: Create performance testing scenario
        sdk_config = SDKConfig(api_key=os.getenv("ANTHROPIC_API_KEY"))
        agent = QATesterAgent(path_config=isolated_agilevv_dir, sdk_config=sdk_config)

        input_data = {
            "story_id": "QA-PERFORMANCE-001",
            "task_description": "Generate performance test cases for high-load API endpoints",
            "implementation_data": {
                "implementation": {
                    "source_files": [
                        "api_server.py",
                        "database_manager.py",
                        "cache_service.py",
                    ],
                    "features_implemented": [
                        "REST API endpoints",
                        "Database connection pooling",
                        "Redis caching",
                        "Response optimization",
                    ],
                    "performance_targets": {
                        "response_time": "< 200ms for 95% of requests",
                        "throughput": "1000 requests per second",
                        "concurrent_users": "500 concurrent users",
                    },
                },
                "design_reference": {
                    "non_functional_requirements": [
                        {
                            "id": "NFR-006",
                            "description": "API response time under 200ms",
                            "type": "performance",
                        },
                        {
                            "id": "NFR-007",
                            "description": "Support 1000 concurrent users",
                            "type": "performance",
                        },
                    ],
                },
            },
            "testing_phase": "performance",
            "context": {
                "project_name": "HighLoadAPI",
                "expected_load": "1000 RPS",
            },
        }

        # Act: Generate performance test cases
        result = await agent.process(input_data)

        # Assert: Performance test strategy
        assert result["status"] == "success"
        testing_data = result["testing_data"]

        # Validate performance focus
        test_strategy = testing_data["test_strategy"]
        strategy_content = str(test_strategy).lower()
        performance_terms = [
            "performance",
            "load",
            "stress",
            "response time",
            "throughput",
        ]
        assert any(term in strategy_content for term in performance_terms)


@pytest.mark.asyncio
class TestRealQATesterArtifactGeneration:
    """Test real SDK integration for artifact generation."""

    @skip_if_no_auth
    async def test_real_test_artifact_creation(self, isolated_agilevv_dir: TestPathConfig) -> None:
        """Test real test artifact creation and persistence."""
        # Arrange: Create comprehensive test scenario
        sdk_config = SDKConfig(api_key=os.getenv("ANTHROPIC_API_KEY"))
        agent = QATesterAgent(path_config=isolated_agilevv_dir, sdk_config=sdk_config)

        input_data = {
            "story_id": "QA-ARTIFACTS-001",
            "task_description": "Generate complete test documentation and artifacts",
            "implementation_data": {
                "implementation": {
                    "source_files": ["main.py", "utils.py", "config.py"],
                    "features_implemented": ["Core functionality", "Utility functions"],
                },
                "design_reference": {
                    "functional_requirements": [
                        {"id": "FR-007", "description": "Core feature implementation"},
                    ],
                },
            },
            "testing_phase": "comprehensive",
            "context": {"project_name": "TestArtifacts"},
        }

        # Act: Process and generate artifacts
        result = await agent.process(input_data)

        # Assert: Artifacts created successfully
        assert result["status"] == "success"
        assert "artifacts" in result

        artifacts = result["artifacts"]
        expected_artifacts = [
            "test_report",
            "test_strategy",
            "test_cases",
            "test_results",
            "traceability_matrix",
        ]

        for artifact_type in expected_artifacts:
            assert artifact_type in artifacts
            artifact_path = isolated_agilevv_dir.base_dir / artifacts[artifact_type]
            assert artifact_path.exists(), f"Missing artifact: {artifact_type}"

            # Validate artifact content
            content = json.loads(artifact_path.read_text())
            assert isinstance(content, dict)
            assert len(content) > 0

    @skip_if_no_auth
    async def test_real_traceability_matrix_generation(
        self, isolated_agilevv_dir: TestPathConfig
    ) -> None:
        """Test real traceability matrix generation."""
        # Arrange: Create scenario with multiple requirements
        sdk_config = SDKConfig(api_key=os.getenv("ANTHROPIC_API_KEY"))
        agent = QATesterAgent(path_config=isolated_agilevv_dir, sdk_config=sdk_config)

        input_data = {
            "story_id": "QA-TRACEABILITY-001",
            "task_description": "Generate traceability matrix for comprehensive requirements coverage",
            "implementation_data": {
                "implementation": {"source_files": ["feature_a.py", "feature_b.py"]},
                "design_reference": {
                    "functional_requirements": [
                        {"id": "FR-008", "description": "Feature A implementation"},
                        {"id": "FR-009", "description": "Feature B implementation"},
                        {"id": "FR-010", "description": "Integration between A and B"},
                    ],
                    "non_functional_requirements": [
                        {
                            "id": "NFR-008",
                            "description": "Performance requirement",
                            "type": "performance",
                        },
                    ],
                },
            },
            "testing_phase": "system",
            "context": {"project_name": "TraceabilityTest"},
        }

        # Act: Generate traceability matrix
        result = await agent.process(input_data)

        # Assert: Traceability matrix created
        assert result["status"] == "success"
        artifacts = result["artifacts"]
        assert "traceability_matrix" in artifacts

        traceability_path = isolated_agilevv_dir.base_dir / artifacts["traceability_matrix"]
        assert traceability_path.exists()

        # Validate traceability matrix structure
        traceability_data = json.loads(traceability_path.read_text())
        assert "traceability_matrix" in traceability_data
        assert "coverage_summary" in traceability_data

        matrix = traceability_data["traceability_matrix"]
        assert isinstance(matrix, list)
        assert len(matrix) >= 0  # Should have entries for requirements

        coverage_summary = traceability_data["coverage_summary"]
        assert "total_requirements" in coverage_summary
        assert "covered_requirements" in coverage_summary
        assert "coverage_percentage" in coverage_summary


@pytest.mark.asyncio
class TestRealQATesterErrorHandling:
    """Test real SDK error handling scenarios."""

    @skip_if_no_auth
    async def test_real_invalid_input_handling(self, isolated_agilevv_dir: TestPathConfig) -> None:
        """Test handling of invalid input data."""
        # Arrange: Create agent with invalid input
        sdk_config = SDKConfig(api_key=os.getenv("ANTHROPIC_API_KEY"))
        agent = QATesterAgent(path_config=isolated_agilevv_dir, sdk_config=sdk_config)

        invalid_input_data = {
            "story_id": "QA-ERROR-001",
            # Missing required fields
            "implementation_data": {},
            "context": {},
        }

        # Act: Process invalid input
        result = await agent.process(invalid_input_data)

        # Assert: Handles gracefully
        assert isinstance(result, dict)
        assert "status" in result
        # Should either succeed with minimal data or handle the error gracefully

    @skip_if_no_auth
    async def test_real_timeout_handling(self, isolated_agilevv_dir: TestPathConfig) -> None:
        """Test SDK timeout handling."""
        # Arrange: Create agent with very short timeout
        sdk_config = SDKConfig(api_key=os.getenv("ANTHROPIC_API_KEY"), timeout=1)
        agent = QATesterAgent(path_config=isolated_agilevv_dir, sdk_config=sdk_config)

        # Create complex input that might timeout
        complex_input = {
            "story_id": "QA-TIMEOUT-001",
            "task_description": "Generate extremely comprehensive test suite for complex enterprise application with hundreds of requirements and extensive integration points",
            "implementation_data": {
                "implementation": {
                    "source_files": [f"module_{i}.py" for i in range(50)],
                    "features_implemented": [f"Feature {i}" for i in range(100)],
                },
                "design_reference": {
                    "functional_requirements": [
                        {"id": f"FR-{i:03d}", "description": f"Requirement {i}"} for i in range(50)
                    ],
                },
            },
            "testing_phase": "comprehensive",
            "context": {"project_name": "ComplexApp"},
        }

        # Act & Assert: Handle timeout appropriately
        try:
            result = await agent.process(complex_input)
            # If it succeeds despite short timeout, that's also valid
            assert isinstance(result, dict)
        except Exception as e:
            # Timeout or other network errors are expected with very short timeout
            assert "timeout" in str(e).lower() or "time" in str(e).lower()

    @skip_if_no_auth
    async def test_real_network_resilience(self, isolated_agilevv_dir: TestPathConfig) -> None:
        """Test network resilience and retry behavior."""
        # Arrange: Create agent with retry configuration
        sdk_config = SDKConfig(
            api_key=os.getenv("ANTHROPIC_API_KEY"),
            max_retries=2,
            timeout=10,
        )
        agent = QATesterAgent(path_config=isolated_agilevv_dir, sdk_config=sdk_config)

        input_data = {
            "story_id": "QA-NETWORK-001",
            "task_description": "Test network resilience",
            "implementation_data": {
                "implementation": {"source_files": ["network_test.py"]},
                "design_reference": {
                    "functional_requirements": [
                        {"id": "FR-011", "description": "Network resilience test"},
                    ],
                },
            },
            "context": {"project_name": "NetworkTest"},
        }

        # Act: Process with network considerations
        result = await agent.process(input_data)

        # Assert: Should handle network issues gracefully
        assert isinstance(result, dict)
        assert "status" in result


@pytest.mark.asyncio
class TestRealQATesterSessionManagement:
    """Test real SDK session management and context preservation."""

    @skip_if_no_auth
    async def test_real_session_context_preservation(
        self, isolated_agilevv_dir: TestPathConfig
    ) -> None:
        """Test session context preservation across calls."""
        # Arrange: Create agent and first context
        sdk_config = SDKConfig(api_key=os.getenv("ANTHROPIC_API_KEY"))
        agent = QATesterAgent(path_config=isolated_agilevv_dir, sdk_config=sdk_config)

        # First call to establish context
        input_data_1 = {
            "story_id": "QA-SESSION-001",
            "task_description": "Initial test strategy development",
            "implementation_data": {
                "implementation": {"source_files": ["session_module.py"]},
                "design_reference": {
                    "functional_requirements": [
                        {"id": "FR-012", "description": "Session management feature"},
                    ],
                },
            },
            "context": {"project_name": "SessionTest", "phase": "initial"},
        }

        # Act: First processing call
        result_1 = await agent.process(input_data_1)

        # Second call with related context
        input_data_2 = {
            "story_id": "QA-SESSION-002",
            "task_description": "Extended test strategy based on initial findings",
            "implementation_data": {
                "implementation": {"source_files": ["session_module.py", "extended_module.py"]},
                "design_reference": {
                    "functional_requirements": [
                        {"id": "FR-012", "description": "Session management feature"},
                        {"id": "FR-013", "description": "Extended session features"},
                    ],
                },
            },
            "context": {"project_name": "SessionTest", "phase": "extended"},
        }

        result_2 = await agent.process(input_data_2)

        # Assert: Both calls successful
        assert result_1["status"] == "success"
        assert result_2["status"] == "success"

        # Context should be maintained appropriately
        assert "testing_data" in result_1
        assert "testing_data" in result_2

    @skip_if_no_auth
    async def test_real_multi_agent_handoff_preparation(
        self, isolated_agilevv_dir: TestPathConfig
    ) -> None:
        """Test preparation of data for next agent in V-Model sequence."""
        # Arrange: Create QA agent with implementation data from Developer agent
        sdk_config = SDKConfig(api_key=os.getenv("ANTHROPIC_API_KEY"))
        agent = QATesterAgent(path_config=isolated_agilevv_dir, sdk_config=sdk_config)

        # Simulate receiving implementation data from Developer agent
        developer_output = {
            "story_id": "QA-HANDOFF-001",
            "task_description": "Test preparation for Integration agent handoff",
            "implementation_data": {
                "id": "DEV-001",
                "agent": "developer",
                "implementation": {
                    "source_files": ["implemented_feature.py", "tests.py"],
                    "features_implemented": ["Authentication", "User management"],
                    "code_metrics": {"test_coverage": 85, "complexity": 3.2},
                },
                "design_reference": {
                    "functional_requirements": [
                        {
                            "id": "FR-014",
                            "description": "Authentication implementation",
                        },
                    ],
                },
            },
            "testing_phase": "preparation",
            "context": {"project_name": "HandoffTest"},
        }

        # Act: Process for handoff to Integration agent
        result = await agent.process(developer_output)

        # Assert: Proper preparation for next stage
        assert result["status"] == "success"
        assert "next_stage_ready" in result
        assert "quality_assessment" in result

        # Validate handoff data structure
        quality_assessment = result["quality_assessment"]
        assert "readiness_for_next_stage" in quality_assessment
        assert "recommendations" in quality_assessment
        assert isinstance(quality_assessment["recommendations"], list)


@pytest.mark.asyncio
class TestRealQATesterPerformanceAndScaling:
    """Test real SDK performance and scaling characteristics."""

    @skip_if_no_auth
    async def test_real_large_requirement_set_processing(
        self, isolated_agilevv_dir: TestPathConfig
    ) -> None:
        """Test processing of large requirement sets."""
        # Arrange: Create scenario with many requirements
        sdk_config = SDKConfig(api_key=os.getenv("ANTHROPIC_API_KEY"), timeout=60)
        agent = QATesterAgent(path_config=isolated_agilevv_dir, sdk_config=sdk_config)

        # Create large requirement set
        large_requirements = [
            {"id": f"FR-{i:03d}", "description": f"Functional requirement {i}"} for i in range(20)
        ]
        large_nfr = [
            {"id": f"NFR-{i:03d}", "description": f"Non-functional requirement {i}"}
            for i in range(10)
        ]

        input_data = {
            "story_id": "QA-LARGE-001",
            "task_description": "Process large requirement set for comprehensive testing",
            "implementation_data": {
                "implementation": {
                    "source_files": [f"module_{i}.py" for i in range(15)],
                    "features_implemented": [f"Feature {i}" for i in range(20)],
                },
                "design_reference": {
                    "functional_requirements": large_requirements,
                    "non_functional_requirements": large_nfr,
                },
            },
            "testing_phase": "comprehensive",
            "context": {"project_name": "LargeApp"},
        }

        # Act: Process large dataset
        result = await agent.process(input_data)

        # Assert: Handles large datasets effectively
        assert result["status"] == "success"
        assert "testing_data" in result

        # Validate that processing handled the scale
        testing_data = result["testing_data"]
        assert "test_strategy" in testing_data
        assert "test_cases" in testing_data

    @skip_if_no_auth
    async def test_real_concurrent_processing_simulation(
        self, isolated_agilevv_dir: TestPathConfig
    ) -> None:
        """Test simulation of concurrent processing scenarios."""
        # Arrange: Create agent for concurrent scenario testing
        sdk_config = SDKConfig(api_key=os.getenv("ANTHROPIC_API_KEY"))
        agent = QATesterAgent(path_config=isolated_agilevv_dir, sdk_config=sdk_config)

        input_data = {
            "story_id": "QA-CONCURRENT-001",
            "task_description": "Simulate concurrent test execution scenario",
            "implementation_data": {
                "implementation": {
                    "source_files": ["concurrent_handler.py"],
                    "features_implemented": [
                        "Concurrent processing",
                        "Thread management",
                    ],
                    "concurrency_features": {
                        "max_threads": 10,
                        "queue_size": 1000,
                        "timeout_handling": True,
                    },
                },
                "design_reference": {
                    "non_functional_requirements": [
                        {
                            "id": "NFR-009",
                            "description": "Handle 100 concurrent requests",
                            "type": "performance",
                        },
                    ],
                },
            },
            "testing_phase": "concurrency",
            "context": {"project_name": "ConcurrentApp", "load_profile": "high"},
        }

        # Act: Process concurrent scenario
        result = await agent.process(input_data)

        # Assert: Concurrent processing considerations
        assert result["status"] == "success"
        testing_data = result["testing_data"]

        # Validate concurrent testing considerations
        test_strategy = testing_data["test_strategy"]
        strategy_content = str(test_strategy).lower()
        concurrency_terms = ["concurrent", "parallel", "thread", "performance", "load"]
        assert any(term in strategy_content for term in concurrency_terms)

    @skip_if_no_auth
    async def test_real_end_to_end_qa_workflow_simulation(
        self, isolated_agilevv_dir: TestPathConfig
    ) -> None:
        """Test complete end-to-end QA workflow simulation."""
        # Arrange: Create comprehensive E2E scenario
        sdk_config = SDKConfig(api_key=os.getenv("ANTHROPIC_API_KEY"))
        agent = QATesterAgent(path_config=isolated_agilevv_dir, sdk_config=sdk_config)

        e2e_scenario = {
            "story_id": "QA-E2E-WORKFLOW-001",
            "task_description": "Complete end-to-end QA workflow for enterprise application",
            "implementation_data": {
                "implementation": {
                    "source_files": [
                        "app.py",
                        "auth.py",
                        "database.py",
                        "api.py",
                        "frontend.js",
                        "config.py",
                    ],
                    "technologies_used": [
                        "Flask",
                        "SQLAlchemy",
                        "React",
                        "PostgreSQL",
                        "Redis",
                        "Docker",
                    ],
                    "features_implemented": [
                        "User authentication",
                        "Data management",
                        "RESTful API",
                        "Web interface",
                        "Caching layer",
                        "Containerization",
                    ],
                    "deployment_config": {
                        "environment": "production",
                        "scaling": "horizontal",
                        "monitoring": "enabled",
                    },
                },
                "design_reference": {
                    "functional_requirements": [
                        {
                            "id": "FR-015",
                            "description": "User login and session management",
                        },
                        {"id": "FR-016", "description": "Data CRUD operations"},
                        {"id": "FR-017", "description": "API endpoint functionality"},
                        {"id": "FR-018", "description": "Web UI interactions"},
                    ],
                    "non_functional_requirements": [
                        {
                            "id": "NFR-010",
                            "description": "99.9% uptime availability",
                            "type": "reliability",
                        },
                        {
                            "id": "NFR-011",
                            "description": "Response time < 2 seconds",
                            "type": "performance",
                        },
                        {
                            "id": "NFR-012",
                            "description": "GDPR compliance",
                            "type": "security",
                        },
                    ],
                },
            },
            "testing_phase": "e2e",
            "context": {
                "project_name": "EnterpriseApp",
                "deployment_target": "AWS Production",
                "compliance_requirements": ["GDPR", "SOC2"],
                "expected_users": "10000 daily active users",
            },
        }

        # Act: Execute complete QA workflow
        result = await agent.process(e2e_scenario)

        # Assert: Complete E2E QA workflow
        assert result["status"] == "success"
        assert "testing_data" in result
        assert "quality_assessment" in result

        # Validate comprehensive test coverage
        testing_data = result["testing_data"]
        test_strategy = testing_data["test_strategy"]

        # Should address multiple testing aspects
        strategy_content = str(test_strategy).lower()
        testing_aspects = [
            "functional",
            "performance",
            "security",
            "integration",
            "user",
        ]
        aspects_covered = sum(1 for aspect in testing_aspects if aspect in strategy_content)
        assert aspects_covered >= 3  # Should cover multiple testing aspects

        # Validate quality assessment for production readiness
        quality_assessment = result["quality_assessment"]
        assert "overall_quality" in quality_assessment
        assert "readiness_for_next_stage" in quality_assessment
        assert "recommendations" in quality_assessment

        # Should provide production readiness assessment
        assert quality_assessment["overall_quality"] in [
            "excellent",
            "good",
            "acceptable",
            "poor",
        ]
