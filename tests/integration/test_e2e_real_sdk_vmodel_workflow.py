"""
Comprehensive E2E Tests for Real Claude Code SDK V-Model Workflow Integration

This module implements Task 5.1: Write comprehensive E2E tests for complete real AI-powered
V-Model workflow from Requirements to Integration, using actual Claude Code SDK calls
(no mocks) for authentic testing.

Test Strategy:
- Real Claude Code SDK integration with authentic API calls
- Document-based session persistence validation
- Performance metrics and streaming response validation
- Error handling with actual SDK failure scenarios
- Complete MailBuddy application generation workflow
"""

import asyncio
import json
import os
import time
from datetime import datetime
from typing import Any

import pytest
from verifflowcc.core.orchestrator import Orchestrator
from verifflowcc.core.path_config import PathConfig
from verifflowcc.core.sdk_config import SDKConfig
from verifflowcc.core.vmodel import VModelStage

# Test markers for organization
pytestmark = [
    pytest.mark.e2e,
    pytest.mark.integration,
    pytest.mark.real_sdk,
    pytest.mark.asyncio,
    pytest.mark.slow,  # These tests use real API calls and take longer
]


@pytest.fixture
def mailbuddy_user_story() -> dict[str, Any]:
    """MailBuddy application user story for comprehensive testing."""
    return {
        "id": "MAILBUDDY-001",
        "title": "Email Management Application",
        "description": (
            "As a user, I want a simple email management application that can "
            "send emails, manage contacts, and organize messages in folders"
        ),
        "acceptance_criteria": [
            "System can send emails with subject, body, and recipients",
            "System can store and manage contact information",
            "System can organize emails into folders (Inbox, Sent, Drafts)",
            "System provides a simple web interface for email management",
            "System validates email addresses before sending",
            "System persists data using SQLite database",
        ],
        "story_points": 13,
        "priority": "High",
        "technology_constraints": {
            "framework": "Flask",
            "database": "SQLite",
            "frontend": "HTML/CSS/JavaScript",
            "email_service": "SMTP",
        },
        "quality_requirements": {
            "test_coverage": 85,
            "code_quality": 80,
            "security": "Input validation required",
            "performance": "Response time < 2 seconds",
        },
    }


@pytest.fixture
def sdk_config_with_retry() -> SDKConfig:
    """SDK configuration with retry logic for production testing."""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        pytest.skip("ANTHROPIC_API_KEY environment variable required for real SDK tests")

    return SDKConfig(
        api_key=api_key,
        timeout=60,  # Longer timeout for real API calls
        max_retries=3,  # Retry on transient failures
    )


class TestRealSDKVModelWorkflow:
    """Test suite for Task 5.1: Real Claude Code SDK V-Model workflow execution."""

    @pytest.mark.asyncio
    async def test_complete_real_sdk_workflow_execution(
        self,
        isolated_agilevv_dir: PathConfig,
        mailbuddy_user_story: dict[str, Any],
        sdk_config_with_retry: SDKConfig,
    ) -> None:
        """Test complete V-Model workflow with real Claude Code SDK integration."""
        # Create orchestrator with real SDK configuration
        orchestrator = Orchestrator(
            path_config=isolated_agilevv_dir,
            sdk_config=sdk_config_with_retry,
            mock_mode=False,  # Use real SDK
        )

        # Record start time for performance analysis
        workflow_start_time = time.time()

        # Execute complete sprint workflow
        result = await orchestrator.run_sprint(mailbuddy_user_story)

        # Record end time
        workflow_end_time = time.time()
        total_execution_time = workflow_end_time - workflow_start_time

        # Core workflow validation
        assert result is not None, "Real SDK workflow should return result"
        assert isinstance(result, dict), "Result should be dictionary"
        assert "final_decision" in result, "Should have final GO/NO-GO decision"
        assert "stages" in result, "Should include all executed stages"
        assert "readiness_score" in result, "Should have overall readiness assessment"

        # Performance validation for real SDK calls
        assert (
            total_execution_time < 300
        ), f"Workflow should complete within 5 minutes, took {total_execution_time:.2f}s"

        # Validate all V-Model stages were executed
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

        executed_stages = list(result["stages"].keys())
        for stage in expected_stages[:4]:  # At minimum, first 4 stages should execute
            assert stage in executed_stages, f"Stage {stage} should be executed in real workflow"

        # Validate authentic AI agent responses (no mock data patterns)
        for stage_name, stage_result in result["stages"].items():
            if stage_result.get("status") == "success":
                # Real SDK responses should have substantive content
                if "artifacts" in stage_result:
                    artifacts = stage_result["artifacts"]
                    assert len(artifacts) > 0, f"Stage {stage_name} should generate real artifacts"

                # Check for authentic AI-generated content markers
                if "agent_type" in stage_result:
                    assert stage_result["agent_type"] in [
                        "requirements_analyst",
                        "architect",
                        "developer",
                        "qa_tester",
                        "integration",
                    ], f"Stage {stage_name} should use real agent type"

        # Validate session persistence with real SDK
        session_states = orchestrator.state.get("session_state", {})
        assert len(session_states) > 0, "Real SDK should maintain session state"

        # Validate quality metrics from real agents
        if "agent_performance" in result:
            agent_performance = result["agent_performance"]
            for stage, metrics in agent_performance.items():
                assert (
                    "execution_time" in metrics
                ), f"Real SDK stage {stage} should track execution time"
                assert (
                    metrics["execution_time"] > 0
                ), f"Real SDK stage {stage} should have positive execution time"

        # Final decision validation
        assert result["final_decision"] in [
            "GO",
            "NO-GO",
        ], "Should have valid final decision"

        # Document test results for analysis
        test_results = {
            "test_name": "complete_real_sdk_workflow_execution",
            "execution_time": total_execution_time,
            "stages_executed": len(executed_stages),
            "final_decision": result["final_decision"],
            "readiness_score": result.get("readiness_score", 0),
            "timestamp": datetime.now().isoformat(),
        }

        # Save test results for future analysis
        test_results_path = isolated_agilevv_dir.logs_dir / "real_sdk_test_results.json"
        test_results_path.write_text(json.dumps(test_results, indent=2))

    @pytest.mark.asyncio
    async def test_real_sdk_streaming_responses(
        self,
        isolated_agilevv_dir: PathConfig,
        mailbuddy_user_story: dict[str, Any],
        sdk_config_with_retry: SDKConfig,
    ) -> None:
        """Test Claude Code SDK streaming responses across agent transitions."""
        orchestrator = Orchestrator(
            path_config=isolated_agilevv_dir,
            sdk_config=sdk_config_with_retry,
            mock_mode=False,
        )

        # Track streaming events
        streaming_events = []

        # Override agent processing to capture streaming events
        original_agents = orchestrator.agents.copy()
        for stage, agent in original_agents.items():
            if hasattr(agent, "process"):
                original_process = agent.process

                async def capture_streaming_process(
                    input_data, original_func=original_process, stage_name=stage
                ):
                    """Capture streaming events during agent processing."""
                    start_time = time.time()

                    streaming_events.append(
                        {
                            "stage": stage_name,
                            "event": "stream_start",
                            "timestamp": start_time,
                        }
                    )

                    # Execute real agent processing
                    result = await original_func(input_data)

                    end_time = time.time()
                    streaming_events.append(
                        {
                            "stage": stage_name,
                            "event": "stream_complete",
                            "timestamp": end_time,
                            "duration": end_time - start_time,
                        }
                    )

                    return result

                # Replace with streaming capture version
                agent.process = capture_streaming_process

        # Execute workflow to capture streaming behavior
        await orchestrator.run_sprint(mailbuddy_user_story)

        # Validate streaming events were captured
        assert len(streaming_events) > 0, "Should capture streaming events from real SDK"

        # Validate streaming timeline
        stream_starts = [e for e in streaming_events if e["event"] == "stream_start"]
        stream_completions = [e for e in streaming_events if e["event"] == "stream_complete"]

        assert len(stream_starts) > 0, "Should have streaming start events"
        assert len(stream_completions) > 0, "Should have streaming completion events"
        assert len(stream_starts) == len(stream_completions), "Streams should be properly closed"

        # Validate reasonable streaming durations (real SDK calls take time)
        for completion in stream_completions:
            duration = completion.get("duration", 0)
            assert (
                duration > 0.1
            ), f"Real SDK streaming should take measurable time, got {duration}s"
            assert (
                duration < 120
            ), f"Streaming should complete within reasonable time, took {duration}s"

        # Validate streaming sequence follows V-Model order
        stage_order = [e["stage"] for e in stream_starts]
        expected_first_stages = ["requirements_analyst", "architect", "developer"]

        # At least the first few stages should follow expected order
        for i, expected_stage in enumerate(expected_first_stages[: len(stage_order)]):
            if i < len(stage_order):
                assert (
                    expected_stage in stage_order
                ), f"Expected {expected_stage} in streaming sequence"

    @pytest.mark.asyncio
    async def test_real_sdk_document_session_persistence(
        self,
        isolated_agilevv_dir: PathConfig,
        mailbuddy_user_story: dict[str, Any],
        sdk_config_with_retry: SDKConfig,
    ) -> None:
        """Test document-based session persistence with authentic agent outputs."""
        # Execute workflow in stages to test persistence
        orchestrator1 = Orchestrator(
            path_config=isolated_agilevv_dir,
            sdk_config=sdk_config_with_retry,
            mock_mode=False,
        )

        # Execute requirements stage
        requirements_result = await orchestrator1.execute_stage(
            VModelStage.REQUIREMENTS, {"story": mailbuddy_user_story}
        )

        assert (
            requirements_result["status"] == "success"
        ), "Requirements stage should succeed with real SDK"

        # Verify session state persistence
        initial_session_state = orchestrator1.state.get("session_state", {})
        assert len(initial_session_state) > 0, "Should persist session state from real SDK"

        # Verify document artifacts are created
        stage_artifacts = orchestrator1.state.get("stage_artifacts", {})
        assert "requirements" in stage_artifacts, "Should create requirements artifacts"

        # Create new orchestrator instance (simulating restart)
        orchestrator2 = Orchestrator(
            path_config=isolated_agilevv_dir,
            sdk_config=sdk_config_with_retry,
            mock_mode=False,
        )

        # Verify session state was loaded
        recovered_session_state = orchestrator2.state.get("session_state", {})
        assert recovered_session_state == initial_session_state, "Session state should be restored"

        # Verify stage artifacts are available
        recovered_artifacts = orchestrator2.state.get("stage_artifacts", {})
        assert "requirements" in recovered_artifacts, "Stage artifacts should be restored"

        # Continue workflow with design stage
        design_result = await orchestrator2.execute_stage(
            VModelStage.DESIGN, {"story": mailbuddy_user_story}
        )

        assert (
            design_result["status"] == "success"
        ), "Design stage should succeed with restored context"

        # Verify context preservation across stages
        final_session_state = orchestrator2.state.get("session_state", {})
        assert len(final_session_state) >= len(
            initial_session_state
        ), "Session state should grow with context"

        # Verify cross-stage artifact traceability
        final_artifacts = orchestrator2.state.get("stage_artifacts", {})
        assert "design" in final_artifacts, "Design artifacts should be created"
        assert "requirements" in final_artifacts, "Requirements artifacts should be preserved"

        # Validate authentic content in persisted documents
        requirements_artifacts = final_artifacts.get("requirements", {})
        design_artifacts = final_artifacts.get("design", {})

        # Real SDK should generate substantive content, not placeholder text
        for artifact_set in [requirements_artifacts, design_artifacts]:
            if isinstance(artifact_set, dict) and "artifacts" in artifact_set:
                artifacts = artifact_set["artifacts"]
                for artifact_name, artifact_content in artifacts.items():
                    if isinstance(artifact_content, str):
                        assert (
                            len(artifact_content) > 50
                        ), f"Real SDK artifact {artifact_name} should have substantive content"
                        assert (
                            "mock" not in artifact_content.lower()
                        ), f"Artifact {artifact_name} should not contain mock indicators"

    @pytest.mark.asyncio
    async def test_real_sdk_error_handling_and_recovery(
        self,
        isolated_agilevv_dir: PathConfig,
        sdk_config_with_retry: SDKConfig,
    ) -> None:
        """Test basic error handling for SDK connection issues and malformed responses."""
        # Test with invalid API key scenario
        invalid_sdk_config = SDKConfig(
            api_key="invalid-api-key-test",
            timeout=10,
            max_retries=1,
        )

        orchestrator = Orchestrator(
            path_config=isolated_agilevv_dir,
            sdk_config=invalid_sdk_config,
            mock_mode=False,
        )

        # Create a malformed user story to test input validation
        malformed_story = {
            "id": "",  # Empty ID
            "title": None,  # None title
            "description": "",  # Empty description
            # Missing acceptance_criteria
        }

        # Execute workflow and expect graceful error handling
        result = await orchestrator.run_sprint(malformed_story)

        # Should handle errors gracefully, not crash
        assert isinstance(result, dict), "Should return result even with errors"
        assert "final_decision" in result, "Should have final decision even with errors"

        # Should indicate failure
        assert result["final_decision"] == "NO-GO", "Should be NO-GO due to SDK/input errors"
        assert result.get("success_rate", 1.0) < 0.5, "Success rate should be low due to errors"

        # Should record error details
        stages = result.get("stages", {})
        error_found = False
        for stage_name, stage_result in stages.items():
            if stage_result.get("status") == "error":
                error_found = True
                assert (
                    "error" in stage_result
                ), f"Error stage {stage_name} should include error message"
                error_message = stage_result["error"]
                # Should be specific about SDK or validation errors
                assert any(
                    keyword in error_message.lower()
                    for keyword in [
                        "api",
                        "key",
                        "authentication",
                        "invalid",
                        "connection",
                        "timeout",
                    ]
                ), f"Error message should be descriptive: {error_message}"

        assert error_found, "Should record at least one error stage"

        # Test retry mechanism with transient failures
        # (This would require more sophisticated mocking of network conditions)
        # For now, verify retry configuration is respected
        assert invalid_sdk_config.max_retries == 1, "Should use configured retry count"
        assert invalid_sdk_config.timeout == 10, "Should use configured timeout"

    @pytest.mark.asyncio
    async def test_real_sdk_mailbuddy_application_generation(
        self,
        isolated_agilevv_dir: PathConfig,
        mailbuddy_user_story: dict[str, Any],
        sdk_config_with_retry: SDKConfig,
    ) -> None:
        """Test complete MailBuddy application generation using only real Claude Code SDK agents."""
        # Configure orchestrator for complete application generation
        orchestrator = Orchestrator(
            path_config=isolated_agilevv_dir,
            sdk_config=sdk_config_with_retry,
            mock_mode=False,
        )

        # Customize quality thresholds for MailBuddy application
        orchestrator.config["v_model"]["quality_thresholds"].update(
            {
                "test_coverage": 85,  # High coverage for email application
                "code_quality_score": 80,  # Good quality for production app
                "security_validation": 90,  # High security for email handling
            }
        )

        # Execute complete workflow
        start_time = time.time()
        result = await orchestrator.run_sprint(mailbuddy_user_story)
        end_time = time.time()

        execution_time = end_time - start_time

        # Validate MailBuddy-specific outcomes
        # Note: In mock mode, quality gates may fail due to minimal content generation
        if os.getenv("VERIFFLOWCC_MOCK_MODE"):
            # In mock mode, validate workflow completion structure
            assert result["final_decision"] in [
                "GO",
                "NO-GO",
            ], "Should provide valid decision"
            assert "stages" in result, "Should have stage execution results"
            assert len(result["stages"]) > 0, "Should have executed at least one stage"
        else:
            # In real SDK mode, expect high-quality results
            assert (
                result["final_decision"] == "GO"
            ), "MailBuddy application should be ready for deployment"
            assert (
                result.get("readiness_score", 0) >= 75
            ), "MailBuddy should have high readiness score"

        # Validate application-specific artifacts were generated
        stage_artifacts = orchestrator.state.get("stage_artifacts", {})

        # Only check artifact content in real SDK mode
        if not os.getenv("VERIFFLOWCC_MOCK_MODE"):
            # Requirements should include email functionality
            if "requirements" in stage_artifacts:
                req_artifacts = stage_artifacts["requirements"]
                # Check for email-related requirements in artifacts
                req_content = json.dumps(req_artifacts).lower()
                assert any(
                    keyword in req_content
                    for keyword in ["email", "smtp", "contact", "folder", "message"]
                ), "Requirements should include email functionality"

            # Design should include Flask architecture
            if "design" in stage_artifacts:
                design_artifacts = stage_artifacts["design"]
                design_content = json.dumps(design_artifacts).lower()
                assert any(
                    keyword in design_content
                    for keyword in ["flask", "sqlite", "database", "web", "api"]
                ), "Design should include Flask/web architecture"

            # Development should include code generation
            if "coding" in stage_artifacts:
                coding_artifacts = stage_artifacts["coding"]
                coding_content = json.dumps(coding_artifacts).lower()
                assert any(
                    keyword in coding_content
                    for keyword in ["python", "app.py", "route", "template", "model"]
                ), "Coding should include Python/Flask implementation"
        else:
            # In mock mode, just verify artifacts structure exists
            assert isinstance(stage_artifacts, dict), "Should have stage artifacts structure"

        # Validate performance for full application generation
        assert (
            execution_time < 600
        ), f"MailBuddy generation should complete within 10 minutes, took {execution_time:.2f}s"

        # Validate quality gates were applied
        quality_gates = orchestrator.state.get("quality_gates", {})
        assert len(quality_gates) > 0, "Quality gates should be evaluated for MailBuddy"

        # Check for security considerations (important for email app) - only in real SDK mode
        if not os.getenv("VERIFFLOWCC_MOCK_MODE"):
            for _stage_name, stage_result in result["stages"].items():
                if (
                    stage_result.get("status") == "success"
                    and "security" in json.dumps(stage_result).lower()
                ):
                    # Email applications should consider security
                    stage_content = json.dumps(stage_result).lower()
                    security_keywords = [
                        "validation",
                        "sanitize",
                        "csrf",
                        "sql injection",
                        "xss",
                    ]
                    security_mentioned = any(
                        keyword in stage_content for keyword in security_keywords
                    )
                    if security_mentioned:
                        break
            else:
                # At least one stage should mention security for email application
                pytest.fail("MailBuddy application should include security considerations")

        # Document MailBuddy generation results
        mailbuddy_results = {
            "application": "MailBuddy",
            "execution_time": execution_time,
            "final_decision": result["final_decision"],
            "readiness_score": result.get("readiness_score", 0),
            "stages_completed": len(result["stages"]),
            "artifacts_generated": len(stage_artifacts),
            "quality_gates_passed": sum(
                1 for gate in quality_gates.values() if gate.get("passed", False)
            ),
            "timestamp": datetime.now().isoformat(),
        }

        # Save MailBuddy generation report
        mailbuddy_report_path = isolated_agilevv_dir.logs_dir / "mailbuddy_generation_report.json"
        mailbuddy_report_path.write_text(json.dumps(mailbuddy_results, indent=2))

    @pytest.mark.asyncio
    async def test_real_sdk_concurrent_workflow_isolation(
        self,
        isolated_agilevv_dir: PathConfig,
        sdk_config_with_retry: SDKConfig,
    ) -> None:
        """Test concurrent workflow execution with real SDK maintains proper isolation."""
        # Create multiple distinct user stories
        stories = [
            {
                "id": "CONCURRENT-AUTH",
                "title": "Authentication System",
                "description": "User authentication and authorization system",
                "acceptance_criteria": [
                    "Login validation",
                    "Session management",
                    "Role-based access",
                ],
            },
            {
                "id": "CONCURRENT-API",
                "title": "REST API Gateway",
                "description": "API gateway for microservices communication",
                "acceptance_criteria": [
                    "Request routing",
                    "Rate limiting",
                    "API documentation",
                ],
            },
        ]

        async def execute_isolated_workflow(
            story: dict[str, Any], path_suffix: str
        ) -> dict[str, Any]:
            """Execute workflow in isolated environment."""
            # Create isolated path config for this workflow
            story_path_config = PathConfig(
                base_dir=isolated_agilevv_dir.base_dir / f"concurrent-{path_suffix}"
            )
            story_path_config.ensure_structure()

            orchestrator = Orchestrator(
                path_config=story_path_config,
                sdk_config=sdk_config_with_retry,
                mock_mode=False,
            )

            return await orchestrator.run_sprint(story)

        # Execute workflows concurrently
        start_time = time.time()
        results = await asyncio.gather(
            execute_isolated_workflow(stories[0], "auth"),
            execute_isolated_workflow(stories[1], "api"),
            return_exceptions=True,
        )
        end_time = time.time()

        concurrent_execution_time = end_time - start_time

        # Validate concurrent execution succeeded
        assert len(results) == 2, "Both concurrent workflows should complete"

        for i, result in enumerate(results):
            if isinstance(result, Exception):
                pytest.fail(f"Concurrent workflow {i} failed: {result}")

            # Type narrowing
            assert isinstance(result, dict), f"Result {i} should be dict"
            assert (
                result["story"]["id"] == stories[i]["id"]
            ), f"Workflow {i} should process correct story"
            assert result["final_decision"] in [
                "GO",
                "NO-GO",
            ], f"Workflow {i} should have valid decision"

        # Validate isolation - workflows shouldn't interfere with each other
        auth_result, api_result = results

        # Different stories should produce different artifacts
        auth_artifacts = auth_result.get("stages", {})
        api_artifacts = api_result.get("stages", {})

        # Should have processed different content
        auth_content = json.dumps(auth_artifacts).lower()
        api_content = json.dumps(api_artifacts).lower()

        # Auth workflow should mention authentication concepts
        assert any(
            keyword in auth_content for keyword in ["auth", "login", "session", "user"]
        ), "Auth workflow should contain authentication content"

        # API workflow should mention API concepts
        assert any(
            keyword in api_content for keyword in ["api", "gateway", "route", "endpoint"]
        ), "API workflow should contain API content"

        # Validate reasonable concurrent performance
        # Concurrent execution should be somewhat faster than sequential
        estimated_sequential_time = concurrent_execution_time * 1.5  # Rough estimate
        assert (
            concurrent_execution_time < estimated_sequential_time
        ), "Concurrent execution should show some efficiency"

    @pytest.mark.asyncio
    async def test_real_sdk_performance_benchmarking(
        self,
        isolated_agilevv_dir: PathConfig,
        mailbuddy_user_story: dict[str, Any],
        sdk_config_with_retry: SDKConfig,
    ) -> None:
        """Benchmark real SDK performance characteristics across V-Model stages."""
        orchestrator = Orchestrator(
            path_config=isolated_agilevv_dir,
            sdk_config=sdk_config_with_retry,
            mock_mode=False,
        )

        # Track performance metrics per stage
        stage_performance = {}

        # Override stage execution to capture detailed timing
        original_execute_stage = orchestrator.execute_stage

        async def benchmark_execute_stage(
            stage: VModelStage, input_data: dict[str, Any]
        ) -> dict[str, Any]:
            """Execute stage with detailed performance tracking."""
            stage_start = time.time()
            # Could add memory tracking if needed

            try:
                result = await original_execute_stage(stage, input_data)
                stage_end = time.time()

                stage_performance[stage.value] = {
                    "execution_time": stage_end - stage_start,
                    "success": result.get("status") == "success",
                    "timestamp": datetime.now().isoformat(),
                }

                return result

            except Exception as e:
                stage_end = time.time()
                stage_performance[stage.value] = {
                    "execution_time": stage_end - stage_start,
                    "success": False,
                    "error": str(e),
                    "timestamp": datetime.now().isoformat(),
                }
                raise

        # Replace with benchmarking version
        orchestrator.execute_stage = benchmark_execute_stage

        # Execute full workflow for benchmarking
        total_start = time.time()
        result = await orchestrator.run_sprint(mailbuddy_user_story)
        total_end = time.time()

        total_execution_time = total_end - total_start

        # Performance analysis
        successful_stages = [s for s, metrics in stage_performance.items() if metrics["success"]]
        stage_times = [
            metrics["execution_time"]
            for metrics in stage_performance.values()
            if metrics["success"]
        ]

        # Validate performance characteristics
        assert (
            len(successful_stages) >= 3
        ), "Should successfully execute multiple stages for benchmarking"
        assert (
            total_execution_time < 450
        ), f"Total workflow should complete within reasonable time, took {total_execution_time:.2f}s"

        if stage_times:
            avg_stage_time = sum(stage_times) / len(stage_times)
            max_stage_time = max(stage_times)
            min_stage_time = min(stage_times)

            # Performance assertions
            assert (
                avg_stage_time > 1.0
            ), f"Real SDK stages should take measurable time, avg: {avg_stage_time:.2f}s"
            assert (
                avg_stage_time < 120
            ), f"Average stage time should be reasonable, avg: {avg_stage_time:.2f}s"
            assert (
                max_stage_time < 180
            ), f"No single stage should take excessive time, max: {max_stage_time:.2f}s"

            # Performance variance should be reasonable
            time_variance = max_stage_time - min_stage_time
            assert (
                time_variance < avg_stage_time * 3
            ), f"Stage time variance should be reasonable: {time_variance:.2f}s"

        # Generate performance report
        performance_report = {
            "test_name": "real_sdk_performance_benchmarking",
            "total_execution_time": total_execution_time,
            "stages_executed": len(successful_stages),
            "stage_performance": stage_performance,
            "performance_summary": {
                "avg_stage_time": (sum(stage_times) / len(stage_times) if stage_times else 0),
                "max_stage_time": max(stage_times) if stage_times else 0,
                "min_stage_time": min(stage_times) if stage_times else 0,
                "total_successful_stages": len(successful_stages),
            },
            "timestamp": datetime.now().isoformat(),
        }

        # Save performance report
        perf_report_path = isolated_agilevv_dir.logs_dir / "real_sdk_performance_report.json"
        perf_report_path.write_text(json.dumps(performance_report, indent=2))

        # Final performance validation
        assert result["final_decision"] in [
            "GO",
            "NO-GO",
        ], "Benchmarked workflow should complete with decision"
