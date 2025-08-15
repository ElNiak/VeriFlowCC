"""
End-to-End V-Model Workflow Integration Tests - Part 2

This module contains additional comprehensive tests for workflow rollback, error handling,
and artifact management functionality.
"""

import asyncio

# Import MockSDKAgent from the main workflow test file
import sys
from datetime import datetime
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest
from verifflowcc.agents.factory import AgentFactory
from verifflowcc.core.orchestrator import Orchestrator
from verifflowcc.core.path_config import PathConfig
from verifflowcc.core.sdk_config import SDKConfig
from verifflowcc.core.vmodel import VModelStage

sys.path.append(str(Path(__file__).parent))
from test_e2e_vmodel_workflow import MockSDKAgent

# Test markers for organization
pytestmark = [pytest.mark.e2e, pytest.mark.integration, pytest.mark.workflow, pytest.mark.asyncio]


class TestWorkflowRollbackAndCheckpoints:
    """Test suite for Task 5.4: Workflow rollback and checkpoint restoration capabilities."""

    @pytest.mark.asyncio
    async def test_checkpoint_creation_and_restoration(
        self, isolated_agilevv_dir: PathConfig, mock_agent_factory, sample_user_story
    ) -> None:
        """Test creating checkpoints and restoring workflow state."""
        with patch.object(AgentFactory, "create_agent") as mock_create_agent:
            mock_create_agent.side_effect = lambda name: mock_agent_factory(name)

            orchestrator = Orchestrator(
                path_config=isolated_agilevv_dir,
                sdk_config=SDKConfig(api_key="mock-key"),
                mock_mode=True,
            )

            # Execute partial workflow
            await orchestrator.execute_stage(VModelStage.REQUIREMENTS, {"story": sample_user_story})
            await orchestrator.execute_stage(VModelStage.DESIGN, {"story": sample_user_story})

            # Create checkpoint after design
            checkpoint_info = await orchestrator.checkpoint(
                "after_design", "Design phase completed"
            )

            assert checkpoint_info["name"] == "after_design"
            assert checkpoint_info["stage"] == "design"
            assert "timestamp" in checkpoint_info
            assert "state" in checkpoint_info

            # Verify checkpoint file exists
            checkpoint_path = isolated_agilevv_dir.checkpoints_dir / "after_design.json"
            assert checkpoint_path.exists(), "Checkpoint file should be created"

            # Continue workflow and modify state
            await orchestrator.execute_stage(VModelStage.CODING, {"story": sample_user_story})
            assert orchestrator.current_stage == VModelStage.CODING

            # Restore checkpoint
            restore_success = await orchestrator.restore_checkpoint("after_design")
            assert restore_success is True, "Checkpoint restoration should succeed"
            assert (
                orchestrator.current_stage == VModelStage.DESIGN
            ), "Should restore to design stage"

            # Verify state was properly restored
            completed_stages = orchestrator.state.get("completed_stages", [])
            assert "requirements" in completed_stages, "Requirements should remain completed"
            assert "design" in completed_stages, "Design should remain completed"
            assert "coding" not in completed_stages, "Coding should be rolled back"

    @pytest.mark.asyncio
    async def test_checkpoint_with_session_state(
        self, isolated_agilevv_dir: PathConfig, mock_agent_factory, sample_user_story
    ) -> None:
        """Test checkpoint includes and restores SDK session state."""
        session_data = {}

        def session_tracking_factory(agent_type: str) -> MockSDKAgent:
            agent = mock_agent_factory(agent_type)
            original_process = agent.process

            async def session_tracked_process(input_data: dict[str, Any]) -> dict[str, Any]:
                result = await original_process(input_data)
                # Track session state
                session_data[agent_type] = {
                    "session_id": f"{agent_type}_session_001",
                    "context_data": {"agent": agent_type, "timestamp": datetime.now().isoformat()},
                }
                result["session_state"] = session_data[agent_type]
                return result

            agent.process = session_tracked_process
            return agent

        with patch.object(AgentFactory, "create_agent") as mock_create_agent:
            mock_create_agent.side_effect = session_tracking_factory

            orchestrator = Orchestrator(
                path_config=isolated_agilevv_dir,
                sdk_config=SDKConfig(api_key="mock-key"),
                mock_mode=True,
            )

            # Execute stages to build session state
            await orchestrator.execute_stage(VModelStage.REQUIREMENTS, {"story": sample_user_story})
            await orchestrator.execute_stage(VModelStage.DESIGN, {"story": sample_user_story})

            # Verify session state exists
            session_states = orchestrator.state.get("session_state", {})
            assert len(session_states) > 0, "Session state should be preserved"

            # Create checkpoint
            checkpoint_info = await orchestrator.checkpoint(
                "with_sessions", "Including session state"
            )

            # Verify checkpoint contains session state
            assert "state" in checkpoint_info
            checkpoint_sessions = checkpoint_info["state"].get("session_state", {})
            assert len(checkpoint_sessions) > 0, "Checkpoint should include session state"

            # Modify session state
            orchestrator.state["session_state"]["modified"] = {"test": "modified"}

            # Restore checkpoint
            restore_success = await orchestrator.restore_checkpoint("with_sessions")
            assert restore_success is True

            # Verify session state was restored
            restored_sessions = orchestrator.state.get("session_state", {})
            assert "modified" not in restored_sessions, "Modified session should be rolled back"
            assert (
                "requirements" in restored_sessions
            ), "Original requirements session should be restored"

    @pytest.mark.asyncio
    async def test_rollback_after_stage_failure(
        self, isolated_agilevv_dir: PathConfig, mock_agent_factory, sample_user_story
    ) -> None:
        """Test automatic rollback after stage failure."""

        def failing_coding_factory(agent_type: str) -> MockSDKAgent:
            agent = mock_agent_factory(agent_type)

            if agent_type == "developer":

                async def failing_process(input_data: dict[str, Any]) -> dict[str, Any]:
                    raise Exception("Critical development error requiring rollback")

                agent.process = failing_process

            return agent

        with patch.object(AgentFactory, "create_agent") as mock_create_agent:
            mock_create_agent.side_effect = failing_coding_factory

            orchestrator = Orchestrator(
                path_config=isolated_agilevv_dir,
                sdk_config=SDKConfig(api_key="mock-key"),
                mock_mode=True,
            )

            # Execute successful stages first
            await orchestrator.execute_stage(VModelStage.REQUIREMENTS, {"story": sample_user_story})
            await orchestrator.execute_stage(VModelStage.DESIGN, {"story": sample_user_story})

            # Create automatic checkpoint before risky stage
            await orchestrator.checkpoint("before_coding", "Auto checkpoint before coding")

            # Attempt failing stage
            coding_result = await orchestrator.execute_stage(
                VModelStage.CODING, {"story": sample_user_story}
            )

            assert coding_result["status"] == "error", "Coding stage should fail"
            assert "Critical development error" in coding_result["error"]

            # Verify orchestrator can restore to safe state
            restore_success = await orchestrator.restore_checkpoint("before_coding")
            assert restore_success is True

            # Verify system is in stable state after rollback
            assert orchestrator.current_stage == VModelStage.DESIGN
            completed_stages = orchestrator.state.get("completed_stages", [])
            assert "requirements" in completed_stages
            assert "design" in completed_stages

    @pytest.mark.asyncio
    async def test_multiple_checkpoint_management(
        self, isolated_agilevv_dir: PathConfig, mock_agent_factory, sample_user_story
    ) -> None:
        """Test managing multiple checkpoints throughout workflow."""
        with patch.object(AgentFactory, "create_agent") as mock_create_agent:
            mock_create_agent.side_effect = lambda name: mock_agent_factory(name)

            orchestrator = Orchestrator(
                path_config=isolated_agilevv_dir,
                sdk_config=SDKConfig(api_key="mock-key"),
                mock_mode=True,
            )

            checkpoints_created = []

            # Execute workflow with checkpoints at each major stage
            await orchestrator.execute_stage(VModelStage.REQUIREMENTS, {"story": sample_user_story})
            await orchestrator.checkpoint("requirements_complete", "After requirements")
            checkpoints_created.append("requirements_complete")

            await orchestrator.execute_stage(VModelStage.DESIGN, {"story": sample_user_story})
            await orchestrator.checkpoint("design_complete", "After design")
            checkpoints_created.append("design_complete")

            await orchestrator.execute_stage(VModelStage.CODING, {"story": sample_user_story})
            await orchestrator.checkpoint("coding_complete", "After coding")
            checkpoints_created.append("coding_complete")

            # Verify all checkpoints exist
            for checkpoint_name in checkpoints_created:
                checkpoint_path = isolated_agilevv_dir.checkpoints_dir / f"{checkpoint_name}.json"
                assert checkpoint_path.exists(), f"Checkpoint {checkpoint_name} should exist"

            # Verify checkpoint history tracking
            checkpoint_history = orchestrator.state.get("checkpoint_history", [])
            assert len(checkpoint_history) == 3, "Should track all checkpoint creations"

            for i, checkpoint_name in enumerate(checkpoints_created):
                history_entry = checkpoint_history[i]
                assert history_entry["name"] == checkpoint_name
                assert "timestamp" in history_entry

            # Test restoring to different checkpoints
            restore_success = await orchestrator.restore_checkpoint("requirements_complete")
            assert restore_success is True
            assert orchestrator.current_stage == VModelStage.REQUIREMENTS

            restore_success = await orchestrator.restore_checkpoint("design_complete")
            assert restore_success is True
            assert orchestrator.current_stage == VModelStage.DESIGN


class TestRealisticFeatureDevelopment:
    """Test suite for Task 5.5: End-to-end tests for realistic feature development scenarios."""

    @pytest.fixture
    def complex_user_story(self) -> dict[str, Any]:
        """Complex user story for realistic testing."""
        return {
            "id": "US-COMPLEX-001",
            "title": "Multi-Factor Authentication System",
            "description": "As a security-conscious user, I want multi-factor authentication so that my account is protected against unauthorized access",
            "acceptance_criteria": [
                "System supports SMS, email, and TOTP authentication methods",
                "Users can configure multiple backup methods",
                "Failed authentication attempts are logged and rate-limited",
                "Recovery codes are provided for account recovery",
                "Admin users can enforce MFA policies",
                "Integration with existing OAuth providers",
                "Graceful degradation when MFA services are unavailable",
            ],
            "story_points": 13,
            "priority": "Critical",
            "dependencies": ["US-AUTH-001", "US-LOGGING-002"],
            "non_functional_requirements": {
                "performance": "MFA verification within 2 seconds",
                "security": "PCI DSS compliance for payment-related features",
                "availability": "99.9% uptime for authentication services",
                "scalability": "Support 10,000 concurrent authentication requests",
            },
        }

    @pytest.mark.asyncio
    async def test_realistic_microservice_development(
        self, isolated_agilevv_dir: PathConfig, mock_agent_factory, complex_user_story
    ) -> None:
        """Test realistic microservice development scenario."""

        def realistic_agent_factory(agent_type: str) -> MockSDKAgent:
            agent = mock_agent_factory(agent_type)
            original_process = agent.process

            async def realistic_process(input_data: dict[str, Any]) -> dict[str, Any]:
                result = await original_process(input_data)

                # Enhance with realistic complexity
                if agent_type == "requirements_analyst":
                    result["requirements_data"]["non_functional_requirements"] = {
                        "performance_requirements": [
                            "Response time < 2s",
                            "Throughput > 10k req/s",
                        ],
                        "security_requirements": ["PCI DSS compliance", "SOC 2 Type II"],
                        "scalability_requirements": ["Horizontal scaling", "Load balancing"],
                    }
                    result["requirements_data"]["dependency_analysis"] = {
                        "upstream_services": ["user-service", "notification-service"],
                        "downstream_impacts": ["payment-service", "audit-service"],
                    }

                elif agent_type == "architect":
                    result["design_data"]["microservice_architecture"] = {
                        "services": [
                            {"name": "mfa-service", "type": "core", "scaling": "horizontal"},
                            {"name": "sms-provider", "type": "external", "sla": "99.9%"},
                            {"name": "totp-service", "type": "internal", "caching": "redis"},
                        ],
                        "event_flows": [
                            {"event": "mfa_challenge_requested", "publisher": "mfa-service"},
                            {"event": "mfa_verified", "subscriber": "user-service"},
                        ],
                    }
                    result["design_data"]["infrastructure_requirements"] = {
                        "databases": ["PostgreSQL for user data", "Redis for session cache"],
                        "messaging": "Kafka for event streaming",
                        "monitoring": "Prometheus + Grafana",
                    }

                elif agent_type == "developer":
                    result["implementation_data"]["code_generation"]["services"] = [
                        {"service": "mfa-service", "files": 45, "tests": 78, "coverage": 94},
                        {"service": "sms-provider", "files": 12, "tests": 24, "coverage": 89},
                        {"service": "totp-service", "files": 18, "tests": 36, "coverage": 96},
                    ]
                    result["implementation_data"]["integration_points"] = [
                        {"type": "REST API", "service": "user-service", "endpoints": 8},
                        {"type": "Message Queue", "topic": "auth_events", "handlers": 5},
                    ]

                return result

            agent.process = realistic_process
            return agent

        with patch.object(AgentFactory, "create_agent") as mock_create_agent:
            mock_create_agent.side_effect = realistic_agent_factory

            orchestrator = Orchestrator(
                path_config=isolated_agilevv_dir,
                sdk_config=SDKConfig(api_key="mock-key"),
                mock_mode=True,
            )

            result = await orchestrator.run_sprint(complex_user_story)

            # Verify realistic complexity handling
            assert result["final_decision"] == "GO", "Complex story should still succeed"

            # Verify requirements handled complexity
            requirements_artifacts = orchestrator.state["stage_artifacts"]["requirements"]
            requirements_data = requirements_artifacts.get("requirements_data", {})
            assert "non_functional_requirements" in requirements_data
            assert "dependency_analysis" in requirements_data

            # Verify architectural complexity
            design_artifacts = orchestrator.state["stage_artifacts"]["design"]
            design_data = design_artifacts.get("design_data", {})
            assert "microservice_architecture" in design_data
            assert "infrastructure_requirements" in design_data

            # Verify implementation complexity
            coding_artifacts = orchestrator.state["stage_artifacts"]["coding"]
            implementation_data = coding_artifacts.get("implementation_data", {})
            assert "services" in implementation_data["code_generation"]
            assert "integration_points" in implementation_data

    @pytest.mark.asyncio
    async def test_cross_functional_requirements_validation(
        self, isolated_agilevv_dir: PathConfig, mock_agent_factory, complex_user_story
    ) -> None:
        """Test validation of cross-functional requirements throughout workflow."""

        def cfr_tracking_factory(agent_type: str) -> MockSDKAgent:
            agent = mock_agent_factory(agent_type)
            original_process = agent.process

            async def cfr_tracked_process(input_data: dict[str, Any]) -> dict[str, Any]:
                result = await original_process(input_data)

                # Track cross-functional requirement handling
                if agent_type == "qa_tester":
                    result["testing_data"]["non_functional_testing"] = {
                        "performance_tests": {
                            "load_testing": "1000 concurrent users tested",
                            "stress_testing": "Peak load 150% capacity tested",
                            "response_times": "Average 1.2s, 95th percentile 1.8s",
                        },
                        "security_tests": {
                            "penetration_testing": "OWASP Top 10 validated",
                            "vulnerability_scanning": "Zero critical vulnerabilities",
                            "compliance_checks": "PCI DSS Level 1 compliant",
                        },
                        "reliability_tests": {
                            "failover_testing": "Auto-failover under 30s",
                            "disaster_recovery": "RTO 4 hours, RPO 1 hour",
                            "chaos_engineering": "Service mesh resilience verified",
                        },
                    }

                elif agent_type == "integration":
                    result["integration_data"]["cfr_validation"] = {
                        "performance_validation": {
                            "response_time_sla": "Met - 1.2s average",
                            "throughput_sla": "Met - 12k req/s peak",
                            "scalability_validation": "Horizontal scaling verified",
                        },
                        "security_validation": {
                            "compliance_audit": "PCI DSS Level 1 certified",
                            "security_scan_results": "No critical vulnerabilities",
                            "access_control_validation": "RBAC properly implemented",
                        },
                        "operational_readiness": {
                            "monitoring_setup": "Prometheus metrics configured",
                            "alerting_rules": "SLA breach alerts configured",
                            "runbook_documentation": "Incident response procedures ready",
                        },
                    }

                return result

            agent.process = cfr_tracked_process
            return agent

        with patch.object(AgentFactory, "create_agent") as mock_create_agent:
            mock_create_agent.side_effect = cfr_tracking_factory

            orchestrator = Orchestrator(
                path_config=isolated_agilevv_dir,
                sdk_config=SDKConfig(api_key="mock-key"),
                mock_mode=True,
            )

            await orchestrator.run_sprint(complex_user_story)

            # Verify CFR validation throughout workflow
            testing_artifacts = orchestrator.state["stage_artifacts"]["unit_testing"]
            if "testing_data" in testing_artifacts:
                testing_data = testing_artifacts["testing_data"]
                assert "non_functional_testing" in testing_data
                nft = testing_data["non_functional_testing"]
                assert "performance_tests" in nft
                assert "security_tests" in nft
                assert "reliability_tests" in nft

            # Verify final CFR validation
            integration_artifacts = orchestrator.state["stage_artifacts"]["validation"]
            if "integration_data" in integration_artifacts:
                integration_data = integration_artifacts["integration_data"]
                assert "cfr_validation" in integration_data
                cfr_val = integration_data["cfr_validation"]
                assert "performance_validation" in cfr_val
                assert "security_validation" in cfr_val
                assert "operational_readiness" in cfr_val

    @pytest.mark.asyncio
    async def test_feature_flag_development_scenario(
        self, isolated_agilevv_dir: PathConfig, mock_agent_factory
    ) -> None:
        """Test development scenario with feature flags and progressive rollout."""
        feature_flag_story = {
            "id": "US-FEATURE-FLAG-001",
            "title": "Progressive Feature Rollout System",
            "description": "As a product manager, I want to control feature releases with progressive rollout",
            "acceptance_criteria": [
                "Features can be enabled for specific user segments",
                "Rollout percentage can be gradually increased",
                "Feature flags can be toggled without deployment",
                "A/B testing integration for feature validation",
                "Real-time monitoring of feature performance",
            ],
        }

        def feature_flag_factory(agent_type: str) -> MockSDKAgent:
            agent = mock_agent_factory(agent_type)
            original_process = agent.process

            async def feature_flag_process(input_data: dict[str, Any]) -> dict[str, Any]:
                result = await original_process(input_data)

                if agent_type == "architect":
                    result["design_data"]["feature_flag_architecture"] = {
                        "flag_storage": "Redis for fast lookups",
                        "configuration_api": "RESTful API for flag management",
                        "client_sdks": ["JavaScript", "Python", "Mobile"],
                        "analytics_integration": "Event tracking for A/B testing",
                    }

                elif agent_type == "developer":
                    result["implementation_data"]["feature_flag_implementation"] = {
                        "flag_evaluation": "Client-side with server fallback",
                        "caching_strategy": "Local cache with TTL refresh",
                        "rollout_algorithms": ["Percentage-based", "User-segment", "Geographic"],
                        "monitoring_hooks": "Custom metrics and alerts",
                    }

                elif agent_type == "qa_tester":
                    result["testing_data"]["feature_flag_testing"] = {
                        "flag_state_testing": "All flag combinations tested",
                        "rollout_testing": "Gradual rollout scenarios validated",
                        "fallback_testing": "Graceful degradation verified",
                        "performance_testing": "Feature flag evaluation latency < 10ms",
                    }

                return result

            agent.process = feature_flag_process
            return agent

        with patch.object(AgentFactory, "create_agent") as mock_create_agent:
            mock_create_agent.side_effect = feature_flag_factory

            orchestrator = Orchestrator(
                path_config=isolated_agilevv_dir,
                sdk_config=SDKConfig(api_key="mock-key"),
                mock_mode=True,
            )

            result = await orchestrator.run_sprint(feature_flag_story)

            # Verify feature flag specific handling
            assert result["final_decision"] == "GO"

            # Check feature flag architecture
            design_artifacts = orchestrator.state["stage_artifacts"]["design"]
            design_data = design_artifacts.get("design_data", {})
            assert "feature_flag_architecture" in design_data

            # Check feature flag implementation
            coding_artifacts = orchestrator.state["stage_artifacts"]["coding"]
            implementation_data = coding_artifacts.get("implementation_data", {})
            assert "feature_flag_implementation" in implementation_data

            # Check feature flag testing
            testing_artifacts = orchestrator.state["stage_artifacts"]["unit_testing"]
            if "testing_data" in testing_artifacts:
                testing_data = testing_artifacts["testing_data"]
                assert "feature_flag_testing" in testing_data


class TestErrorPropagationAndRecovery:
    """Test suite for Task 5.6: Error propagation and recovery across V-Model stages."""

    @pytest.mark.asyncio
    async def test_error_propagation_chain(
        self, isolated_agilevv_dir: PathConfig, mock_agent_factory, sample_user_story
    ) -> None:
        """Test how errors propagate through workflow stages."""
        error_chain = []

        def error_tracking_factory(agent_type: str) -> MockSDKAgent:
            agent = mock_agent_factory(agent_type)
            original_process = agent.process

            async def error_tracked_process(input_data: dict[str, Any]) -> dict[str, Any]:
                try:
                    # Inject error in design stage
                    if agent_type == "architect":
                        error_chain.append({"stage": "design", "type": "primary_error"})
                        raise Exception("Design validation failed: missing security architecture")

                    result = await original_process(input_data)
                    return result

                except Exception as e:
                    error_chain.append(
                        {"stage": agent_type, "type": "propagated_error", "error": str(e)}
                    )
                    raise

            agent.process = error_tracked_process
            return agent

        with patch.object(AgentFactory, "create_agent") as mock_create_agent:
            mock_create_agent.side_effect = error_tracking_factory

            orchestrator = Orchestrator(
                path_config=isolated_agilevv_dir,
                sdk_config=SDKConfig(api_key="mock-key"),
                mock_mode=True,
            )

            result = await orchestrator.run_sprint(sample_user_story)

            # Verify error propagation
            assert len(error_chain) > 0, "Should track error propagation"
            assert error_chain[0]["type"] == "primary_error", "Should identify primary error"

            # Verify error is recorded in stage results
            assert "design" in result["stages"]
            design_result = result["stages"]["design"]
            assert design_result["status"] == "error"
            assert "missing security architecture" in design_result["error"]

            # Verify downstream stages were not executed due to hard gate
            assert result["success_rate"] < 0.5, "Success rate should be low due to error"

    @pytest.mark.asyncio
    async def test_retry_mechanism_on_transient_failures(
        self, isolated_agilevv_dir: PathConfig, mock_agent_factory, sample_user_story
    ) -> None:
        """Test retry mechanism for transient failures."""
        call_counts = {}

        def retry_agent_factory(agent_type: str) -> MockSDKAgent:
            agent = mock_agent_factory(agent_type)
            original_process = agent.process
            call_counts[agent_type] = 0

            async def retry_process(input_data: dict[str, Any]) -> dict[str, Any]:
                call_counts[agent_type] += 1

                # Make developer fail twice, then succeed
                if agent_type == "developer" and call_counts[agent_type] <= 2:
                    raise Exception("Transient SDK connection error")

                return await original_process(input_data)

            agent.process = retry_process
            return agent

        with patch.object(AgentFactory, "create_agent") as mock_create_agent:
            mock_create_agent.side_effect = retry_agent_factory

            orchestrator = Orchestrator(
                path_config=isolated_agilevv_dir,
                sdk_config=SDKConfig(api_key="mock-key", max_retries=3),
                mock_mode=True,
            )

            # Mock the stage execution to include retry logic
            original_execute_stage_logic = orchestrator._execute_stage_logic

            async def retrying_execute_stage_logic(stage, context):
                max_retries = 3
                last_exception = None

                for attempt in range(max_retries):
                    try:
                        return await original_execute_stage_logic(stage, context)
                    except Exception as e:
                        last_exception = e
                        if attempt < max_retries - 1:
                            await asyncio.sleep(0.1)  # Brief delay between retries
                        else:
                            raise last_exception

                raise last_exception

            orchestrator._execute_stage_logic = retrying_execute_stage_logic

            result = await orchestrator.run_sprint(sample_user_story)

            # Verify retry mechanism worked
            assert (
                call_counts.get("developer", 0) == 3
            ), "Developer should be called 3 times (2 failures + 1 success)"

            # Verify final success despite transient failures
            assert result["final_decision"] == "GO", "Should succeed after retries"
            coding_result = result["stages"]["coding"]
            assert coding_result["status"] == "success", "Coding should eventually succeed"

    @pytest.mark.asyncio
    async def test_graceful_degradation_on_optional_services(
        self, isolated_agilevv_dir: PathConfig, mock_agent_factory, sample_user_story
    ) -> None:
        """Test graceful degradation when optional services fail."""

        def degradation_factory(agent_type: str) -> MockSDKAgent:
            agent = mock_agent_factory(agent_type)
            original_process = agent.process

            async def degradation_process(input_data: dict[str, Any]) -> dict[str, Any]:
                result = await original_process(input_data)

                # Simulate optional service failure
                if agent_type == "qa_tester":
                    # Simulate performance testing service failure
                    result["testing_data"]["service_failures"] = {
                        "performance_testing_service": "unavailable",
                        "security_scanning_service": "timeout",
                    }
                    result["testing_data"]["degraded_testing"] = {
                        "basic_functional_tests": "completed",
                        "unit_tests": "completed",
                        "integration_tests": "completed",
                        "performance_tests": "skipped - service unavailable",
                        "security_tests": "partial - timeout occurred",
                    }
                    # Adjust quality score due to degradation
                    result["metrics"]["overall_quality_score"] = 75  # Reduced but acceptable

                return result

            agent.process = degradation_process
            return agent

        with patch.object(AgentFactory, "create_agent") as mock_create_agent:
            mock_create_agent.side_effect = degradation_factory

            orchestrator = Orchestrator(
                path_config=isolated_agilevv_dir,
                sdk_config=SDKConfig(api_key="mock-key"),
                mock_mode=True,
            )

            result = await orchestrator.run_sprint(sample_user_story)

            # Verify graceful degradation
            assert (
                result["final_decision"] == "GO"
            ), "Should proceed despite optional service failures"

            # Check degradation was handled properly
            testing_artifacts = orchestrator.state["stage_artifacts"]["unit_testing"]
            if "testing_data" in testing_artifacts:
                testing_data = testing_artifacts["testing_data"]
                assert "degraded_testing" in testing_data
                degraded = testing_data["degraded_testing"]
                assert degraded["basic_functional_tests"] == "completed"
                assert "skipped" in degraded["performance_tests"]

    @pytest.mark.asyncio
    async def test_circuit_breaker_pattern_on_repeated_failures(
        self, isolated_agilevv_dir: PathConfig, mock_agent_factory, sample_user_story
    ) -> None:
        """Test circuit breaker pattern for repeated service failures."""
        failure_counts = {}
        circuit_states = {}

        def circuit_breaker_factory(agent_type: str) -> MockSDKAgent:
            agent = mock_agent_factory(agent_type)
            original_process = agent.process
            failure_counts[agent_type] = 0
            circuit_states[agent_type] = "CLOSED"  # CLOSED, OPEN, HALF_OPEN

            async def circuit_breaker_process(input_data: dict[str, Any]) -> dict[str, Any]:
                # Circuit breaker logic
                if circuit_states[agent_type] == "OPEN":
                    raise Exception(f"Circuit breaker OPEN for {agent_type}")

                try:
                    # Simulate failures for architect agent
                    if agent_type == "architect":
                        failure_counts[agent_type] += 1
                        if failure_counts[agent_type] <= 3:
                            raise Exception("External design service unavailable")

                    result = await original_process(input_data)

                    # Reset failure count on success
                    failure_counts[agent_type] = 0
                    circuit_states[agent_type] = "CLOSED"
                    return result

                except Exception as e:
                    failure_counts[agent_type] += 1

                    # Open circuit breaker after 3 failures
                    if failure_counts[agent_type] >= 3:
                        circuit_states[agent_type] = "OPEN"

                    raise e

            agent.process = circuit_breaker_process
            return agent

        with patch.object(AgentFactory, "create_agent") as mock_create_agent:
            mock_create_agent.side_effect = circuit_breaker_factory

            orchestrator = Orchestrator(
                path_config=isolated_agilevv_dir,
                sdk_config=SDKConfig(api_key="mock-key"),
                mock_mode=True,
            )

            result = await orchestrator.run_sprint(sample_user_story)

            # Verify circuit breaker activated
            assert failure_counts.get("architect", 0) >= 3, "Should reach failure threshold"
            assert circuit_states.get("architect") == "OPEN", "Circuit should be OPEN"

            # Verify design stage failed due to circuit breaker
            assert "design" in result["stages"]
            design_result = result["stages"]["design"]
            assert design_result["status"] == "error"
            assert "unavailable" in design_result["error"]


class TestArtifactGenerationAndPersistence:
    """Test suite for Task 5.7: Artifact generation, validation, and persistence."""

    @pytest.mark.asyncio
    async def test_comprehensive_artifact_generation(
        self, isolated_agilevv_dir: PathConfig, mock_agent_factory, sample_user_story
    ) -> None:
        """Test generation of all required artifacts throughout workflow."""
        with patch.object(AgentFactory, "create_agent") as mock_create_agent:
            mock_create_agent.side_effect = lambda name: mock_agent_factory(name)

            orchestrator = Orchestrator(
                path_config=isolated_agilevv_dir,
                sdk_config=SDKConfig(api_key="mock-key"),
                mock_mode=True,
            )

            await orchestrator.run_sprint(sample_user_story)

            # Verify artifact generation at each stage
            artifacts_dir = isolated_agilevv_dir.artifacts_dir
            artifacts_dir.mkdir(parents=True, exist_ok=True)

            # Check stage artifacts in orchestrator state
            stage_artifacts = orchestrator.state.get("stage_artifacts", {})

            expected_artifacts = {
                "requirements": ["requirements_document", "validation_report"],
                "design": ["architecture_diagram", "interface_spec", "design_doc"],
                "coding": ["source_code", "unit_tests", "documentation"],
                "unit_testing": ["test_report", "coverage_report", "test_cases"],
                "validation": ["deployment_checklist", "release_notes", "validation_report"],
            }

            for stage, expected_artifact_types in expected_artifacts.items():
                assert stage in stage_artifacts, f"Stage {stage} should have artifacts"
                artifacts = stage_artifacts[stage].get("artifacts", {})

                for artifact_type in expected_artifact_types:
                    assert artifact_type in artifacts, f"Stage {stage} should have {artifact_type}"
                    artifact_file = artifacts[artifact_type]
                    assert isinstance(
                        artifact_file, str
                    ), f"Artifact {artifact_type} should be filename"
                    assert artifact_file.endswith(
                        (".md", ".json", ".yaml", ".puml", ".html", ".xml", ".zip")
                    ), f"Artifact {artifact_type} should have proper file extension"

    @pytest.mark.asyncio
    async def test_artifact_versioning_and_history(
        self, isolated_agilevv_dir: PathConfig, mock_agent_factory, sample_user_story
    ) -> None:
        """Test artifact versioning and historical tracking."""

        def versioning_factory(agent_type: str) -> MockSDKAgent:
            agent = mock_agent_factory(agent_type)
            original_process = agent.process

            async def versioning_process(input_data: dict[str, Any]) -> dict[str, Any]:
                result = await original_process(input_data)

                # Add versioning information to artifacts
                if "artifacts" in result:
                    versioned_artifacts = {}
                    for artifact_name, artifact_file in result["artifacts"].items():
                        # Add version suffix
                        base_name, ext = artifact_file.rsplit(".", 1)
                        versioned_file = f"{base_name}_v1.{ext}"
                        versioned_artifacts[artifact_name] = versioned_file

                    result["artifacts"] = versioned_artifacts
                    result["artifact_metadata"] = {
                        "version": "1.0.0",
                        "timestamp": datetime.now().isoformat(),
                        "agent": agent_type,
                        "story_id": input_data.get("story_id"),
                    }

                return result

            agent.process = versioning_process
            return agent

        with patch.object(AgentFactory, "create_agent") as mock_create_agent:
            mock_create_agent.side_effect = versioning_factory

            orchestrator = Orchestrator(
                path_config=isolated_agilevv_dir,
                sdk_config=SDKConfig(api_key="mock-key"),
                mock_mode=True,
            )

            await orchestrator.run_sprint(sample_user_story)

            # Verify artifact versioning
            stage_artifacts = orchestrator.state.get("stage_artifacts", {})

            for _stage_name, stage_data in stage_artifacts.items():
                if "artifacts" in stage_data:
                    artifacts = stage_data["artifacts"]

                    # Check that artifacts have version suffixes
                    for _artifact_name, artifact_file in artifacts.items():
                        assert (
                            "_v1." in artifact_file
                        ), f"Artifact {artifact_file} should be versioned"

                # Check for artifact metadata
                if "artifact_metadata" in stage_data:
                    metadata = stage_data["artifact_metadata"]
                    assert "version" in metadata
                    assert "timestamp" in metadata
                    assert metadata["story_id"] == sample_user_story["id"]

    @pytest.mark.asyncio
    async def test_artifact_validation_and_integrity(
        self, isolated_agilevv_dir: PathConfig, mock_agent_factory, sample_user_story
    ) -> None:
        """Test artifact validation and integrity checking."""

        def validating_factory(agent_type: str) -> MockSDKAgent:
            agent = mock_agent_factory(agent_type)
            original_process = agent.process

            async def validating_process(input_data: dict[str, Any]) -> dict[str, Any]:
                result = await original_process(input_data)

                # Add validation information
                if "artifacts" in result:
                    result["artifact_validation"] = {
                        "validation_timestamp": datetime.now().isoformat(),
                        "integrity_checks": {
                            "schema_validation": "passed",
                            "content_validation": "passed",
                            "cross_references": "validated",
                        },
                        "quality_metrics": {
                            "completeness": 95,
                            "consistency": 92,
                            "traceability": 88,
                        },
                    }

                return result

            agent.process = validating_process
            return agent

        with patch.object(AgentFactory, "create_agent") as mock_create_agent:
            mock_create_agent.side_effect = validating_factory

            orchestrator = Orchestrator(
                path_config=isolated_agilevv_dir,
                sdk_config=SDKConfig(api_key="mock-key"),
                mock_mode=True,
            )

            await orchestrator.run_sprint(sample_user_story)

            # Verify artifact validation
            stage_artifacts = orchestrator.state.get("stage_artifacts", {})

            validation_stages = ["requirements", "design", "coding", "unit_testing", "validation"]
            for stage in validation_stages:
                if stage in stage_artifacts:
                    stage_data = stage_artifacts[stage]

                    if "artifact_validation" in stage_data:
                        validation = stage_data["artifact_validation"]
                        assert "integrity_checks" in validation
                        assert "quality_metrics" in validation

                        # Check integrity checks passed
                        checks = validation["integrity_checks"]
                        for check_name, check_result in checks.items():
                            assert check_result == "passed", f"Check {check_name} should pass"

                        # Check quality metrics
                        quality = validation["quality_metrics"]
                        assert quality["completeness"] >= 80, "Completeness should be high"
                        assert quality["consistency"] >= 80, "Consistency should be high"

    @pytest.mark.asyncio
    async def test_artifact_cross_stage_traceability(
        self, isolated_agilevv_dir: PathConfig, mock_agent_factory, sample_user_story
    ) -> None:
        """Test traceability of artifacts across V-Model stages."""

        def traceability_factory(agent_type: str) -> MockSDKAgent:
            agent = mock_agent_factory(agent_type)
            original_process = agent.process

            async def traceability_process(input_data: dict[str, Any]) -> dict[str, Any]:
                result = await original_process(input_data)

                # Add traceability information
                result["traceability"] = {
                    "source_requirements": input_data.get("story_id"),
                    "derived_from": [],
                    "influences": [],
                    "stage": agent_type,
                }

                # Add stage-specific traceability
                if agent_type == "architect":
                    result["traceability"]["derived_from"] = ["requirements_document"]
                    result["traceability"]["influences"] = [
                        "architecture_diagram",
                        "interface_spec",
                    ]

                elif agent_type == "developer":
                    result["traceability"]["derived_from"] = [
                        "architecture_diagram",
                        "interface_spec",
                    ]
                    result["traceability"]["influences"] = ["source_code", "unit_tests"]

                elif agent_type == "qa_tester":
                    result["traceability"]["derived_from"] = [
                        "source_code",
                        "requirements_document",
                    ]
                    result["traceability"]["influences"] = ["test_cases", "test_report"]

                elif agent_type == "integration":
                    result["traceability"]["derived_from"] = ["all_stage_artifacts"]
                    result["traceability"]["influences"] = ["deployment_checklist", "release_notes"]

                return result

            agent.process = traceability_process
            return agent

        with patch.object(AgentFactory, "create_agent") as mock_create_agent:
            mock_create_agent.side_effect = traceability_factory

            orchestrator = Orchestrator(
                path_config=isolated_agilevv_dir,
                sdk_config=SDKConfig(api_key="mock-key"),
                mock_mode=True,
            )

            await orchestrator.run_sprint(sample_user_story)

            # Verify traceability across stages
            stage_artifacts = orchestrator.state.get("stage_artifacts", {})

            # Check traceability chain
            traceability_chain = []
            for stage_name in ["requirements", "design", "coding", "unit_testing", "validation"]:
                if stage_name in stage_artifacts:
                    stage_data = stage_artifacts[stage_name]
                    if "traceability" in stage_data:
                        traceability_chain.append(
                            {"stage": stage_name, "traceability": stage_data["traceability"]}
                        )

            assert len(traceability_chain) > 0, "Should have traceability information"

            # Verify each stage traces back to requirements
            for trace_item in traceability_chain:
                traceability = trace_item["traceability"]
                assert traceability["source_requirements"] == sample_user_story["id"]
                assert "derived_from" in traceability
                assert "influences" in traceability

            # Verify downstream stages reference upstream artifacts
            design_trace = next((t for t in traceability_chain if t["stage"] == "design"), None)
            if design_trace:
                assert "requirements_document" in design_trace["traceability"]["derived_from"]

            coding_trace = next((t for t in traceability_chain if t["stage"] == "coding"), None)
            if coding_trace:
                derived_from = coding_trace["traceability"]["derived_from"]
                assert "architecture_diagram" in derived_from or "interface_spec" in derived_from
