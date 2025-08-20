"""
End-to-End V-Model Workflow Integration Tests with SDK

This module contains comprehensive tests for validating complete V-Model workflow execution,
orchestrator coordination, quality gate enforcement, error handling, and SDK integration.
"""

import asyncio
from collections.abc import Callable
from datetime import datetime
from typing import Any
from unittest.mock import patch

import pytest
from verifflowcc.agents.factory import AgentFactory
from verifflowcc.core.orchestrator import Orchestrator
from verifflowcc.core.path_config import PathConfig
from verifflowcc.core.sdk_config import SDKConfig

# Test markers for organization
pytestmark = [
    pytest.mark.e2e,
    pytest.mark.integration,
    pytest.mark.workflow,
    pytest.mark.asyncio,
]


class MockSDKAgent:
    """Mock SDK agent for comprehensive testing."""

    def __init__(self, agent_type: str, mock_responses: dict[str, Any] | None = None):
        self.agent_type = agent_type
        self.mock_responses = mock_responses or {}
        self.session_active = False
        self.session_context: dict[str, Any] = {}
        self.call_count = 0
        self.last_input: dict[str, Any] | None = None

    async def process(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """Mock agent processing with realistic responses."""
        self.call_count += 1
        self.last_input = input_data

        # Simulate processing delay
        await asyncio.sleep(0.01)

        # Return agent-specific responses
        if self.agent_type == "requirements_analyst":
            return self._mock_requirements_response(input_data)
        elif self.agent_type == "architect":
            return self._mock_architect_response(input_data)
        elif self.agent_type == "developer":
            return self._mock_developer_response(input_data)
        elif self.agent_type == "qa_tester":
            return self._mock_qa_response(input_data)
        elif self.agent_type == "integration":
            return self._mock_integration_response(input_data)
        else:
            return {"status": "success", "agent_type": self.agent_type}

    def _mock_requirements_response(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """Mock requirements analyst response."""
        return {
            "status": "success",
            "agent_type": "requirements_analyst",
            "requirements_data": {
                "story_id": input_data.get("story_id", "TEST-001"),
                "validated_requirements": [
                    {
                        "id": "REQ-001",
                        "description": "System shall process user authentication",
                        "acceptance_criteria": [
                            "Valid credentials allow access",
                            "Invalid credentials are rejected",
                            "Session timeout after 30 minutes",
                        ],
                        "invest_score": 95,
                        "smart_score": 90,
                    }
                ],
                "validation_score": 92,
                "acceptance_criteria": [
                    "All requirements follow INVEST principles",
                    "Each requirement has measurable acceptance criteria",
                    "Requirements are traceable to user stories",
                ],
            },
            "artifacts": {
                "requirements_document": "requirements_v1.md",
                "validation_report": "requirements_validation.json",
            },
            "metrics": {
                "execution_time": 2.5,
                "overall_quality_score": 92,
                "requirements_validated": 1,
                "issues_found": 0,
            },
            "session_state": {
                "stage": "requirements",
                "context_preserved": True,
                "session_id": "req_session_001",
            },
        }

    def _mock_architect_response(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """Mock architect response."""
        return {
            "status": "success",
            "agent_type": "architect",
            "design_data": {
                "components": [
                    {
                        "name": "AuthenticationService",
                        "type": "microservice",
                        "responsibilities": [
                            "User authentication",
                            "Session management",
                        ],
                        "interfaces": ["REST API", "Database"],
                    },
                    {
                        "name": "UserDatabase",
                        "type": "data_store",
                        "responsibilities": ["User credential storage"],
                        "interfaces": ["SQL"],
                    },
                ],
                "data_flows": [
                    {
                        "from": "Client",
                        "to": "AuthenticationService",
                        "data": "Login credentials",
                    }
                ],
                "interface_specifications": [
                    {
                        "name": "AuthAPI",
                        "type": "REST",
                        "endpoints": [
                            {
                                "method": "POST",
                                "path": "/login",
                                "description": "User login",
                            }
                        ],
                    }
                ],
                "quality_attributes": {
                    "performance": "Response time < 200ms",
                    "security": "OAuth 2.0 compliance",
                    "scalability": "Support 1000 concurrent users",
                },
            },
            "artifacts": {
                "architecture_diagram": "system_architecture_v1.puml",
                "interface_spec": "api_specification.yaml",
                "design_doc": "system_design_v1.md",
            },
            "metrics": {
                "execution_time": 3.8,
                "overall_quality_score": 88,
                "components_designed": 2,
                "interfaces_defined": 1,
            },
            "session_state": {
                "stage": "design",
                "context_preserved": True,
                "previous_stage": "requirements",
                "session_id": "arch_session_001",
            },
        }

    def _mock_developer_response(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """Mock developer response."""
        return {
            "status": "success",
            "agent_type": "developer",
            "implementation_data": {
                "code_generation": {
                    "files_created": [
                        {
                            "path": "<project_dir>/auth/service.py",
                            "type": "python",
                            "lines": 150,
                        },
                        {
                            "path": "<project_dir>/auth/models.py",
                            "type": "python",
                            "lines": 45,
                        },
                        {"path": "tests/test_auth.py", "type": "python", "lines": 85},
                    ],
                    "total_lines": 280,
                },
                "quality_metrics": {
                    "overall_score": 85.5,
                    "test_coverage": 92,
                    "code_complexity": "Low",
                    "documentation_score": 88,
                },
                "implementation_notes": [
                    "Implemented OAuth 2.0 authentication flow",
                    "Added comprehensive error handling",
                    "Included unit tests with 92% coverage",
                ],
            },
            "artifacts": {
                "source_code": "auth_implementation_v1.zip",
                "unit_tests": "auth_tests_v1.zip",
                "documentation": "implementation_guide.md",
            },
            "metrics": {
                "execution_time": 5.2,
                "overall_quality_score": 85.5,
                "files_created": 3,
                "lines_of_code": 280,
            },
            "session_state": {
                "stage": "coding",
                "context_preserved": True,
                "previous_stages": ["requirements", "design"],
                "session_id": "dev_session_001",
            },
        }

    def _mock_qa_response(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """Mock QA tester response."""
        testing_phase = input_data.get("testing_phase", "unit")

        return {
            "status": "success",
            "agent_type": "qa_tester",
            "testing_data": {
                "test_strategy": {
                    "testing_type": testing_phase,
                    "test_cases_designed": 25,
                    "coverage_target": 90,
                    "test_frameworks": ["pytest", "unittest"],
                },
                "test_execution": {
                    "execution_summary": {
                        "total_tests": 25,
                        "passed": 23,
                        "failed": 2,
                        "pass_rate": "92%",
                    },
                    "failed_tests": [
                        {"name": "test_invalid_token", "reason": "Assertion error"},
                        {"name": "test_session_timeout", "reason": "Timeout exceeded"},
                    ],
                },
                "quality_assessment": {
                    "readiness_for_next_stage": True,
                    "critical_issues": [],
                    "recommendations": [
                        "Fix timeout handling in session management",
                        "Improve error messages for invalid tokens",
                    ],
                },
            },
            "artifacts": {
                "test_report": f"{testing_phase}_test_report.html",
                "coverage_report": f"{testing_phase}_coverage.xml",
                "test_cases": f"{testing_phase}_test_cases.json",
            },
            "metrics": {
                "execution_time": 4.1,
                "overall_quality_score": 78,
                "tests_executed": 25,
                "issues_found": 2,
            },
            "session_state": {
                "stage": f"{testing_phase}_testing",
                "context_preserved": True,
                "test_results": "available",
                "session_id": f"qa_{testing_phase}_session_001",
            },
        }

    def _mock_integration_response(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """Mock integration agent response."""
        return {
            "status": "success",
            "agent_type": "integration",
            "integration_data": {
                "system_validation": {
                    "all_stages_completed": True,
                    "quality_gates_passed": 7,
                    "total_quality_gates": 8,
                    "critical_issues": [],
                },
                "deployment_readiness": {
                    "environment_ready": True,
                    "dependencies_resolved": True,
                    "configuration_validated": True,
                },
                "release_recommendation": {
                    "go_no_go_decision": "GO",
                    "overall_readiness_score": 87.5,
                    "outstanding_issues": [],
                    "deployment_notes": [
                        "System ready for production deployment",
                        "Monitor authentication performance metrics",
                        "Schedule post-deployment validation tests",
                    ],
                },
            },
            "artifacts": {
                "deployment_checklist": "deployment_checklist_v1.md",
                "release_notes": "release_notes_v1.md",
                "validation_report": "system_validation_report.json",
            },
            "metrics": {
                "execution_time": 6.8,
                "overall_quality_score": 87.5,
                "validations_performed": 15,
                "issues_resolved": 8,
            },
            "session_state": {
                "stage": "validation",
                "context_preserved": True,
                "final_decision": "GO",
                "session_id": "integration_session_001",
            },
        }


@pytest.fixture
def mock_agent_factory() -> Callable[[str, dict[str, Any] | None], MockSDKAgent]:
    """Factory for creating mock agents."""

    def _create_mock_agent(
        agent_type: str, responses: dict[str, Any] | None = None
    ) -> MockSDKAgent:
        return MockSDKAgent(agent_type, responses)

    return _create_mock_agent


@pytest.fixture
def sample_user_story() -> dict[str, Any]:
    """Sample user story for testing."""
    return {
        "id": "US-001",
        "title": "User Authentication System",
        "description": "As a user, I want to securely authenticate to access the system",
        "acceptance_criteria": [
            "System accepts valid username/password combinations",
            "System rejects invalid credentials with appropriate error message",
            "User sessions expire after 30 minutes of inactivity",
            "System supports password recovery functionality",
        ],
        "story_points": 8,
        "priority": "High",
    }


class TestCompleteVModelWorkflowExecution:
    """Test suite for Task 5.1: Complete V-Model workflow execution with SDK."""

    @pytest.mark.asyncio
    async def test_complete_workflow_execution_success(
        self,
        isolated_agilevv_dir: PathConfig,
        mock_agent_factory: Callable[[str, dict[str, Any] | None], MockSDKAgent],
        sample_user_story: dict[str, Any],
    ) -> None:
        """Test successful execution of complete V-Model workflow."""
        # Setup orchestrator with mocked agents
        with patch.object(AgentFactory, "create_agent") as mock_create_agent:
            mock_create_agent.side_effect = lambda name: mock_agent_factory(name, None)

            orchestrator = Orchestrator(
                path_config=isolated_agilevv_dir,
                sdk_config=SDKConfig(api_key="mock-key"),
                mock_mode=True,
            )

            # Execute complete sprint
            result = await orchestrator.run_sprint(sample_user_story)

            # Validate workflow completion
            assert result["success_rate"] > 0.8, "Workflow should have high success rate"
            assert result["final_decision"] == "GO", "Final decision should be GO"
            assert result["readiness_score"] > 80, "Readiness score should be high"

            # Verify all stages were executed
            expected_stages = [
                "planning",
                "requirements",
                "design",
                "coding",
                "unit_testing",
                "integration_testing",
                "system_testing",
                "validation",
            ]

            for stage in expected_stages:
                assert stage in result["stages"], f"Stage {stage} should be executed"
                stage_result = result["stages"][stage]
                assert stage_result.get("status") == "success", f"Stage {stage} should succeed"

            # Verify context preservation across stages
            for _stage_name, stage_result in result["stages"].items():
                if "session_state" in stage_result:
                    session_state = stage_result["session_state"]
                    assert session_state.get("context_preserved") is True
                    assert session_state.get("session_id") is not None

    @pytest.mark.asyncio
    async def test_workflow_with_sdk_session_management(
        self,
        isolated_agilevv_dir: PathConfig,
        mock_agent_factory: Callable[[str, dict[str, Any] | None], MockSDKAgent],
        sample_user_story: dict[str, Any],
    ) -> None:
        """Test workflow execution with proper SDK session management."""
        with patch.object(AgentFactory, "create_agent") as mock_create_agent:
            mock_agents = {}

            def create_agent_with_session(name: str) -> MockSDKAgent:
                agent = mock_agent_factory(name, None)
                mock_agents[name] = agent
                return agent

            mock_create_agent.side_effect = create_agent_with_session

            orchestrator = Orchestrator(
                path_config=isolated_agilevv_dir,
                sdk_config=SDKConfig(api_key="mock-key"),
                mock_mode=True,
            )

            # Execute workflow
            await orchestrator.run_sprint(sample_user_story)

            # Verify session state preservation
            orchestrator.get_status()
            session_states = orchestrator.state.get("session_state", {})

            assert len(session_states) > 0, "Session states should be preserved"

            # Verify each agent was called with proper context
            for agent_name, agent in mock_agents.items():
                assert agent.call_count > 0, f"Agent {agent_name} should be called"

                if agent.last_input and "session_state" in agent.last_input:
                    # Verify session continuity
                    session_data = agent.last_input["session_state"]
                    assert isinstance(session_data, dict), "Session data should be dict"

    @pytest.mark.asyncio
    async def test_workflow_performance_metrics(
        self,
        isolated_agilevv_dir: PathConfig,
        mock_agent_factory: Callable[[str, dict[str, Any] | None], MockSDKAgent],
        sample_user_story: dict[str, Any],
    ) -> None:
        """Test workflow execution performance tracking."""
        with patch.object(AgentFactory, "create_agent") as mock_create_agent:
            mock_create_agent.side_effect = lambda name: mock_agent_factory(name, None)

            orchestrator = Orchestrator(
                path_config=isolated_agilevv_dir,
                sdk_config=SDKConfig(api_key="mock-key"),
                mock_mode=True,
            )

            start_time = datetime.now()
            result = await orchestrator.run_sprint(sample_user_story)
            end_time = datetime.now()

            execution_time = (end_time - start_time).total_seconds()

            # Performance assertions
            assert execution_time < 30, "Workflow should complete within 30 seconds"
            assert "agent_performance" in result, "Should track agent performance"

            # Verify performance metrics for each stage
            agent_performance = result["agent_performance"]
            for stage, metrics in agent_performance.items():
                assert "execution_time" in metrics, f"Stage {stage} should have execution time"
                assert "quality_score" in metrics, f"Stage {stage} should have quality score"

    @pytest.mark.asyncio
    async def test_workflow_artifact_generation(
        self,
        isolated_agilevv_dir: PathConfig,
        mock_agent_factory: Callable[[str, dict[str, Any] | None], MockSDKAgent],
        sample_user_story: dict[str, Any],
    ) -> None:
        """Test artifact generation and persistence during workflow."""
        with patch.object(AgentFactory, "create_agent") as mock_create_agent:
            mock_create_agent.side_effect = lambda name: mock_agent_factory(name, None)

            orchestrator = Orchestrator(
                path_config=isolated_agilevv_dir,
                sdk_config=SDKConfig(api_key="mock-key"),
                mock_mode=True,
            )

            await orchestrator.run_sprint(sample_user_story)

            # Verify artifacts were generated at each stage
            stage_artifacts = orchestrator.state.get("stage_artifacts", {})

            expected_artifact_types = {
                "requirements": ["requirements_document", "validation_report"],
                "design": ["architecture_diagram", "interface_spec", "design_doc"],
                "coding": ["source_code", "unit_tests", "documentation"],
                "unit_testing": ["test_report", "coverage_report", "test_cases"],
                "validation": [
                    "deployment_checklist",
                    "release_notes",
                    "validation_report",
                ],
            }

            for stage, expected_artifacts in expected_artifact_types.items():
                if stage in stage_artifacts:
                    artifacts = stage_artifacts[stage].get("artifacts", {})
                    for artifact_type in expected_artifacts:
                        assert (
                            artifact_type in artifacts
                        ), f"Stage {stage} should have {artifact_type}"

    @pytest.mark.asyncio
    async def test_concurrent_workflow_execution(
        self,
        isolated_agilevv_dir: PathConfig,
        mock_agent_factory: Callable[[str, dict[str, Any] | None], MockSDKAgent],
    ) -> None:
        """Test concurrent workflow execution isolation."""
        stories = [
            {
                "id": "US-001",
                "title": "Auth System",
                "description": "User authentication",
            },
            {
                "id": "US-002",
                "title": "User Profile",
                "description": "User profile management",
            },
            {"id": "US-003", "title": "Data Export", "description": "Export user data"},
        ]

        async def run_isolated_workflow(
            story: dict[str, Any], path_config: PathConfig
        ) -> dict[str, Any]:
            with patch.object(AgentFactory, "create_agent") as mock_create_agent:
                mock_create_agent.side_effect = lambda name: mock_agent_factory(name, None)

                orchestrator = Orchestrator(
                    path_config=path_config,
                    sdk_config=SDKConfig(api_key="mock-key"),
                    mock_mode=True,
                )

                return await orchestrator.run_sprint(story)

        # Run workflows concurrently
        results = await asyncio.gather(
            run_isolated_workflow(stories[0], isolated_agilevv_dir),
            run_isolated_workflow(stories[1], isolated_agilevv_dir),
            run_isolated_workflow(stories[2], isolated_agilevv_dir),
            return_exceptions=True,
        )

        # Verify all workflows completed successfully
        assert len(results) == 3, "All workflows should complete"

        for i, result in enumerate(results):
            if isinstance(result, Exception):
                pytest.fail(f"Workflow {i} failed with exception: {result}")

            # Type narrowing: result is now known to be dict[str, Any]
            assert isinstance(result, dict), f"Result should be dict, got {type(result)}"
            assert result["final_decision"] == "GO", f"Workflow {i} should succeed"
            assert (
                result["story"]["id"] == stories[i]["id"]
            ), f"Workflow {i} should process correct story"


class TestOrchestratorCoordination:
    """Test suite for Task 5.2: Orchestrator coordination of all V-Model agents."""

    @pytest.mark.asyncio
    async def test_agent_coordination_sequence(
        self,
        isolated_agilevv_dir: PathConfig,
        mock_agent_factory: Callable[[str, dict[str, Any] | None], MockSDKAgent],
        sample_user_story: dict[str, Any],
    ) -> None:
        """Test proper sequencing and coordination of V-Model agents."""
        call_sequence = []

        def tracking_agent_factory(agent_type: str) -> MockSDKAgent:
            agent = mock_agent_factory(agent_type, None)
            original_process = agent.process

            async def tracked_process(input_data: dict[str, Any]) -> dict[str, Any]:
                call_sequence.append(
                    {
                        "agent": agent_type,
                        "timestamp": datetime.now(),
                        "input_story_id": input_data.get("story_id"),
                    }
                )
                return await original_process(input_data)

            # Replace the process method directly with typing compatibility
            agent.process = tracked_process  # type: ignore[method-assign]
            return agent

        with patch.object(AgentFactory, "create_agent") as mock_create_agent:
            mock_create_agent.side_effect = tracking_agent_factory

            orchestrator = Orchestrator(
                path_config=isolated_agilevv_dir,
                sdk_config=SDKConfig(api_key="mock-key"),
                mock_mode=True,
            )

            await orchestrator.run_sprint(sample_user_story)

            # Verify correct agent sequence

            actual_sequence = [call["agent"] for call in call_sequence]

            # Should have requirements first, then architect, etc.
            assert actual_sequence[0] == "requirements_analyst", "Requirements should be first"
            assert actual_sequence[1] == "architect", "Architect should be second"
            assert actual_sequence[2] == "developer", "Developer should be third"
            assert "integration" in actual_sequence, "Integration should be in sequence"

            # Verify story context is passed through
            for call in call_sequence:
                assert (
                    call["input_story_id"] == sample_user_story["id"]
                ), "Story ID should be consistent"

    @pytest.mark.asyncio
    async def test_agent_failure_handling(
        self,
        isolated_agilevv_dir: PathConfig,
        mock_agent_factory: Callable[[str, dict[str, Any] | None], MockSDKAgent],
        sample_user_story: dict[str, Any],
    ) -> None:
        """Test orchestrator handling of agent failures."""

        def failing_agent_factory(agent_type: str) -> MockSDKAgent:
            agent = mock_agent_factory(agent_type, None)

            # Make architect agent fail
            if agent_type == "architect":

                async def failing_process(input_data: dict[str, Any]) -> dict[str, Any]:
                    raise Exception("Mock architect failure")

                # Replace the process method directly
                agent.process = failing_process  # type: ignore[method-assign]

            return agent

        with patch.object(AgentFactory, "create_agent") as mock_create_agent:
            mock_create_agent.side_effect = failing_agent_factory

            orchestrator = Orchestrator(
                path_config=isolated_agilevv_dir,
                sdk_config=SDKConfig(api_key="mock-key"),
                mock_mode=True,
            )

            result = await orchestrator.run_sprint(sample_user_story)

            # Verify failure handling
            assert "design" in result["stages"], "Design stage should be recorded"
            design_result = result["stages"]["design"]
            assert design_result["status"] == "error", "Design stage should show error"
            assert "Mock architect failure" in design_result["error"]

            # Verify workflow stopped at failure point (hard gate)
            assert result["success_rate"] < 1.0, "Success rate should be reduced"

    @pytest.mark.asyncio
    async def test_agent_context_passing(
        self,
        isolated_agilevv_dir: PathConfig,
        mock_agent_factory: Callable[[str, dict[str, Any] | None], MockSDKAgent],
        sample_user_story: dict[str, Any],
    ) -> None:
        """Test proper context passing between agents."""
        context_chain = []

        def context_tracking_factory(agent_type: str) -> MockSDKAgent:
            agent = mock_agent_factory(agent_type, None)
            original_process = agent.process

            async def context_tracked_process(
                input_data: dict[str, Any],
            ) -> dict[str, Any]:
                context_chain.append(
                    {
                        "agent": agent_type,
                        "received_context": input_data.get("context", {}),
                        "previous_artifacts": input_data.get("requirements", {})
                        or input_data.get("design_spec", {})
                        or input_data.get("implementation_data", {}),
                        "session_state": input_data.get("session_state", {}),
                    }
                )
                return await original_process(input_data)

            # Replace the process method directly
            agent.process = context_tracked_process  # type: ignore[method-assign]
            return agent

        with patch.object(AgentFactory, "create_agent") as mock_create_agent:
            mock_create_agent.side_effect = context_tracking_factory

            orchestrator = Orchestrator(
                path_config=isolated_agilevv_dir,
                sdk_config=SDKConfig(api_key="mock-key"),
                mock_mode=True,
            )

            await orchestrator.run_sprint(sample_user_story)

            # Verify context progression
            assert len(context_chain) > 0, "Should have context tracking data"

            # Verify architect receives requirements context
            architect_context = next(
                (ctx for ctx in context_chain if ctx["agent"] == "architect"), None
            )
            assert architect_context is not None, "Architect should receive context"
            assert (
                len(architect_context["previous_artifacts"]) > 0
            ), "Architect should receive requirements"

            # Verify developer receives design context
            developer_context = next(
                (ctx for ctx in context_chain if ctx["agent"] == "developer"), None
            )
            assert developer_context is not None, "Developer should receive context"
            assert (
                len(developer_context["previous_artifacts"]) > 0
            ), "Developer should receive design"

    @pytest.mark.asyncio
    async def test_agent_performance_tracking(
        self,
        isolated_agilevv_dir: PathConfig,
        mock_agent_factory: Callable[[str, dict[str, Any] | None], MockSDKAgent],
        sample_user_story: dict[str, Any],
    ) -> None:
        """Test orchestrator tracking of agent performance metrics."""
        with patch.object(AgentFactory, "create_agent") as mock_create_agent:
            mock_create_agent.side_effect = lambda name: mock_agent_factory(name, None)

            orchestrator = Orchestrator(
                path_config=isolated_agilevv_dir,
                sdk_config=SDKConfig(api_key="mock-key"),
                mock_mode=True,
            )

            await orchestrator.run_sprint(sample_user_story)

            # Get agent performance summary
            performance_summary = orchestrator.get_agent_performance_summary()

            assert "total_executions" in performance_summary, "Should track total executions"
            assert (
                "successful_executions" in performance_summary
            ), "Should track successful executions"
            assert "average_quality_score" in performance_summary, "Should track average quality"
            assert "stage_performance" in performance_summary, "Should track per-stage performance"

            # Verify performance data for each stage
            stage_performance = performance_summary["stage_performance"]
            for stage in [
                "requirements",
                "design",
                "coding",
                "unit_testing",
                "validation",
            ]:
                if stage in stage_performance:
                    stage_metrics = stage_performance[stage]
                    assert (
                        "last_execution" in stage_metrics
                    ), f"Stage {stage} should have execution time"
                    assert (
                        "quality_score" in stage_metrics
                    ), f"Stage {stage} should have quality score"


class TestQualityGateEnforcement:
    """Test suite for Task 5.3: Quality gate enforcement and stage transition validation."""

    @pytest.mark.asyncio
    async def test_hard_gate_enforcement(
        self,
        isolated_agilevv_dir: PathConfig,
        mock_agent_factory: Callable[[str, dict[str, Any] | None], MockSDKAgent],
        sample_user_story: dict[str, Any],
    ) -> None:
        """Test hard quality gate enforcement stops workflow on failure."""

        def low_quality_agent_factory(agent_type: str) -> MockSDKAgent:
            agent = mock_agent_factory(agent_type, None)

            # Make requirements agent return low quality score
            if agent_type == "requirements_analyst":
                original_process = agent.process

                async def low_quality_process(
                    input_data: dict[str, Any],
                ) -> dict[str, Any]:
                    result = await original_process(input_data)
                    # Set validation score below threshold
                    result["requirements_data"]["validation_score"] = 60  # Below 80% threshold
                    result["requirements_data"]["acceptance_criteria"] = []  # Missing criteria
                    return result

                # Replace the process method directly
                agent.process = low_quality_process  # type: ignore[method-assign]

            return agent

        with patch.object(AgentFactory, "create_agent") as mock_create_agent:
            mock_create_agent.side_effect = low_quality_agent_factory

            # Configure hard gating for requirements
            orchestrator = Orchestrator(
                path_config=isolated_agilevv_dir,
                sdk_config=SDKConfig(api_key="mock-key"),
                mock_mode=True,
            )
            orchestrator.config["v_model"]["stages"]["requirements"]["gating"] = "hard"

            result = await orchestrator.run_sprint(sample_user_story)

            # Verify hard gate stopped workflow
            assert "requirements" in result["stages"], "Requirements stage should be executed"
            requirements_result = result["stages"]["requirements"]
            assert requirements_result["status"] == "error", "Requirements should fail hard gate"

            # Verify subsequent stages were not executed
            assert (
                "design" not in result["stages"]
                or result["stages"]["design"]["status"] != "success"
            )
            assert (
                result["success_rate"] < 0.5
            ), "Success rate should be low due to hard gate failure"

    @pytest.mark.asyncio
    async def test_soft_gate_warnings(
        self,
        isolated_agilevv_dir: PathConfig,
        mock_agent_factory: Callable[[str, dict[str, Any] | None], MockSDKAgent],
        sample_user_story: dict[str, Any],
    ) -> None:
        """Test soft quality gate allows continuation with warnings."""

        def warning_agent_factory(agent_type: str) -> MockSDKAgent:
            agent = mock_agent_factory(agent_type, None)

            # Make coding agent return medium quality score
            if agent_type == "developer":
                original_process = agent.process

                async def warning_quality_process(
                    input_data: dict[str, Any],
                ) -> dict[str, Any]:
                    result = await original_process(input_data)
                    # Set quality score slightly below threshold
                    result["implementation_data"]["quality_metrics"]["overall_score"] = (
                        65  # Below 70%
                    )
                    result["metrics"]["overall_quality_score"] = 65
                    return result

                # Replace the process method directly
                agent.process = warning_quality_process  # type: ignore[method-assign]

            return agent

        with patch.object(AgentFactory, "create_agent") as mock_create_agent:
            mock_create_agent.side_effect = warning_agent_factory

            # Configure soft gating for coding
            orchestrator = Orchestrator(
                path_config=isolated_agilevv_dir,
                sdk_config=SDKConfig(api_key="mock-key"),
                mock_mode=True,
            )
            orchestrator.config["v_model"]["stages"]["coding"]["gating"] = "soft"

            result = await orchestrator.run_sprint(sample_user_story)

            # Verify soft gate allowed continuation
            assert "coding" in result["stages"], "Coding stage should be executed"
            coding_result = result["stages"]["coding"]
            assert coding_result["status"] == "success", "Coding should succeed with warnings"

            # Verify quality gate recorded warnings
            quality_gates = orchestrator.state.get("quality_gates", {})
            if "coding" in quality_gates:
                coding_gate = quality_gates["coding"]
                assert not coding_gate.get("passed", True), "Quality gate should not pass"
                assert len(coding_gate.get("issues", [])) > 0, "Should have quality issues"

            # Verify workflow continued
            assert result["final_decision"] == "GO", "Should still reach final decision"

    @pytest.mark.asyncio
    async def test_quality_threshold_configuration(
        self,
        isolated_agilevv_dir: PathConfig,
        mock_agent_factory: Callable[[str, dict[str, Any] | None], MockSDKAgent],
        sample_user_story: dict[str, Any],
    ) -> None:
        """Test configurable quality thresholds for different stages."""
        with patch.object(AgentFactory, "create_agent") as mock_create_agent:
            mock_create_agent.side_effect = lambda name: mock_agent_factory(name, None)

            orchestrator = Orchestrator(
                path_config=isolated_agilevv_dir,
                sdk_config=SDKConfig(api_key="mock-key"),
                mock_mode=True,
            )

            # Customize quality thresholds
            orchestrator.config["v_model"]["quality_thresholds"] = {
                "test_coverage": 95,  # High coverage requirement
                "code_quality_score": 85,  # High quality requirement
                "requirements_validation_score": 90,  # High requirements quality
                "overall_readiness_score": 85,  # High readiness requirement
            }

            await orchestrator.run_sprint(sample_user_story)

            # Verify custom thresholds were applied
            quality_gates = orchestrator.state.get("quality_gates", {})

            # Check if any stages failed due to higher thresholds
            for stage, gate_info in quality_gates.items():
                if not gate_info.get("passed", True):
                    issues = gate_info.get("issues", [])
                    # Should have threshold-related issues
                    threshold_issues = [issue for issue in issues if "threshold" in issue.lower()]
                    assert (
                        len(threshold_issues) > 0
                    ), f"Stage {stage} should have threshold-related issues"

    @pytest.mark.asyncio
    async def test_stage_dependency_validation(
        self,
        isolated_agilevv_dir: PathConfig,
        mock_agent_factory: Callable[[str, dict[str, Any] | None], MockSDKAgent],
        sample_user_story: dict[str, Any],
    ) -> None:
        """Test validation of stage dependencies and prerequisites."""

        def incomplete_agent_factory(agent_type: str) -> MockSDKAgent:
            agent = mock_agent_factory(agent_type, None)

            # Make requirements agent return incomplete data
            if agent_type == "requirements_analyst":
                original_process = agent.process

                async def incomplete_process(
                    input_data: dict[str, Any],
                ) -> dict[str, Any]:
                    result = await original_process(input_data)
                    # Remove acceptance criteria to make it incomplete
                    result["requirements_data"]["acceptance_criteria"] = []
                    result["requirements_data"]["validated_requirements"] = []
                    return result

                # Replace the process method directly
                agent.process = incomplete_process  # type: ignore[method-assign]

            return agent

        with patch.object(AgentFactory, "create_agent") as mock_create_agent:
            mock_create_agent.side_effect = incomplete_agent_factory

            orchestrator = Orchestrator(
                path_config=isolated_agilevv_dir,
                sdk_config=SDKConfig(api_key="mock-key"),
                mock_mode=True,
            )

            result = await orchestrator.run_sprint(sample_user_story)

            # Verify dependency validation
            result["stages"]["requirements"]

            # Should detect missing dependencies
            quality_gates = orchestrator.state.get("quality_gates", {})
            if "requirements" in quality_gates:
                requirements_gate = quality_gates["requirements"]
                issues = requirements_gate.get("issues", [])

                # Should identify missing acceptance criteria
                missing_criteria_issues = [
                    issue for issue in issues if "acceptance criteria" in issue.lower()
                ]
                assert len(missing_criteria_issues) > 0, "Should detect missing acceptance criteria"
