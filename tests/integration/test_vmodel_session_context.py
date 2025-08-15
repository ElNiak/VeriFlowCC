"""Tests for session context preservation across V-Model stages.

This module tests the preservation of session context and state
as workflows transition between V-Model stages, ensuring continuity
of agent sessions and data consistency across the development lifecycle.
"""

import json
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest
from verifflowcc.agents.base import BaseAgent
from verifflowcc.core.path_config import PathConfig
from verifflowcc.core.sdk_config import SDKConfig

# Import will use fixture directly

pytestmark = [pytest.mark.integration, pytest.mark.vmodel, pytest.mark.session]


class MockVModelAgent(BaseAgent):
    """Mock agent representing a V-Model stage agent."""

    def __init__(
        self,
        stage_name: str,
        sdk_config: SDKConfig,
        path_config: PathConfig,
        mock_mode: bool = True,
    ):
        super().__init__(
            name=f"{stage_name}_agent",
            agent_type=stage_name,
            sdk_config=sdk_config,
            mock_mode=mock_mode,
        )
        self.stage = stage_name
        self.path_config = path_config
        self.session_context: dict[str, Any] = {}
        self.stage_artifacts: list[str] = []
        self.previous_stage_data: dict[str, Any] | None = None

    async def process(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """Process input while maintaining session context."""
        # Inherit context from previous stage if available
        if "session_context" in input_data:
            self.session_context.update(input_data["session_context"])

        # Perform stage-specific processing
        stage_output = await self._process_stage_specific(input_data)

        # Update session context with stage results
        self.session_context[f"{self.stage}_output"] = stage_output
        self.session_context["current_stage"] = self.stage
        current_sequence = self.session_context.get("stage_sequence", [])
        self.session_context["stage_sequence"] = [*current_sequence, self.stage]

        return {
            "agent": self.name,
            "stage": self.stage,
            "output": stage_output,
            "session_context": self.session_context,
            "artifacts": self.stage_artifacts,
        }

    async def _process_stage_specific(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """Stage-specific processing logic."""
        if self.stage == "requirements":
            return {
                "requirements": ["REQ-001: User authentication", "REQ-002: Data storage"],
                "acceptance_criteria": ["AC-001: Login with username/password"],
                "quality_score": 85,
            }
        elif self.stage == "design":
            return {
                "architecture": "microservices",
                "components": ["auth-service", "data-service", "api-gateway"],
                "interfaces": {"auth": "/api/auth", "data": "/api/data"},
            }
        elif self.stage == "coding":
            return {
                "files_created": ["auth_service.py", "data_service.py", "api_gateway.py"],
                "tests_written": 15,
                "coverage": 92,
            }
        elif self.stage == "testing":
            return {"tests_run": 15, "tests_passed": 14, "tests_failed": 1, "coverage_achieved": 89}
        elif self.stage == "integration":
            return {
                "integration_tests": 5,
                "deployment_ready": True,
                "performance_benchmarks": {"latency": "50ms", "throughput": "1000rps"},
            }
        else:
            return {"processed": True}

    def get_stage_context(self) -> dict[str, Any]:
        """Get current stage context for handoff to next stage."""
        return {
            "stage": self.stage,
            "session_context": self.session_context,
            "artifacts": self.stage_artifacts,
            "metadata": {"agent_name": self.name, "processing_complete": True},
        }

    def inherit_context(self, previous_context: dict[str, Any]) -> None:
        """Inherit context from previous V-Model stage."""
        if "session_context" in previous_context:
            self.session_context.update(previous_context["session_context"])

        if "artifacts" in previous_context:
            self.stage_artifacts.extend(previous_context["artifacts"])

        self.previous_stage_data = previous_context


class MockVModelOrchestrator:
    """Mock orchestrator for V-Model workflow."""

    def __init__(self, sdk_config: SDKConfig, path_config: PathConfig):
        self.sdk_config = sdk_config
        self.path_config = path_config
        self.stages = ["requirements", "design", "coding", "testing", "integration"]
        self.agents: dict[str, MockVModelAgent] = {}
        self.workflow_context: dict[str, Any] = {}

        # Initialize agents for each stage
        for stage in self.stages:
            self.agents[stage] = MockVModelAgent(stage, sdk_config, path_config)

    async def execute_vmodel_workflow(self, initial_input: dict[str, Any]) -> dict[str, Any]:
        """Execute complete V-Model workflow with context preservation."""
        workflow_results: dict[str, Any] = {}
        current_context = {"session_context": self.workflow_context}

        for i, stage in enumerate(self.stages):
            agent = self.agents[stage]

            # Inherit context from previous stage
            if i > 0:
                previous_stage = self.stages[i - 1]
                previous_context = workflow_results[previous_stage]["context"]
                agent.inherit_context(previous_context)

            # Process current stage
            stage_input = {**initial_input, **current_context}
            result = await agent.process(stage_input)

            # Store results and update context for next stage
            workflow_results[stage] = {"result": result, "context": agent.get_stage_context()}
            current_context = {"session_context": result["session_context"]}

        return {
            "workflow_complete": True,
            "stages_executed": len(self.stages),
            "results": workflow_results,
            "final_context": current_context,
        }


class TestVModelSessionContext:
    """Test session context preservation across V-Model stages."""

    @pytest.fixture
    def vmodel_orchestrator(self, isolated_agilevv_dir: PathConfig) -> MockVModelOrchestrator:
        """Provide mock V-Model orchestrator."""
        config = SDKConfig(api_key="test-vmodel-key")
        return MockVModelOrchestrator(config, isolated_agilevv_dir)

    @pytest.mark.asyncio
    async def test_context_preservation_across_stages(
        self, vmodel_orchestrator: MockVModelOrchestrator
    ) -> None:
        """Test that session context is preserved across all V-Model stages."""
        initial_input = {"project": "test_project", "user_id": "user123", "sprint": 1}

        result = await vmodel_orchestrator.execute_vmodel_workflow(initial_input)

        # Verify workflow completion
        assert result["workflow_complete"] is True
        assert result["stages_executed"] == 5

        # Check context preservation through stages
        final_context = result["final_context"]["session_context"]
        assert final_context["current_stage"] == "integration"
        assert len(final_context["stage_sequence"]) == 5
        assert final_context["stage_sequence"] == [
            "requirements",
            "design",
            "coding",
            "testing",
            "integration",
        ]

        # Verify each stage has access to previous stage outputs
        results = result["results"]
        assert "requirements_output" in results["design"]["result"]["session_context"]
        assert "design_output" in results["coding"]["result"]["session_context"]
        assert "coding_output" in results["testing"]["result"]["session_context"]
        assert "testing_output" in results["integration"]["result"]["session_context"]

    @pytest.mark.asyncio
    async def test_stage_specific_context_accumulation(
        self, vmodel_orchestrator: MockVModelOrchestrator
    ) -> None:
        """Test that stage-specific context accumulates correctly."""
        initial_input = {"feature": "user_authentication"}

        result = await vmodel_orchestrator.execute_vmodel_workflow(initial_input)
        results = result["results"]

        # Check requirements stage context
        req_context = results["requirements"]["result"]["session_context"]
        assert "requirements_output" in req_context
        assert req_context["requirements_output"]["quality_score"] == 85

        # Check design stage inherits requirements and adds design
        design_context = results["design"]["result"]["session_context"]
        assert "requirements_output" in design_context
        assert "design_output" in design_context
        assert design_context["design_output"]["architecture"] == "microservices"

        # Check final stage has all accumulated context
        final_context = results["integration"]["result"]["session_context"]
        assert all(f"{stage}_output" in final_context for stage in vmodel_orchestrator.stages)

    @pytest.mark.asyncio
    async def test_artifact_chain_preservation(
        self, vmodel_orchestrator: MockVModelOrchestrator
    ) -> None:
        """Test that artifacts are preserved and chained across stages."""
        initial_input = {"create_artifacts": True}

        # Add some initial artifacts
        vmodel_orchestrator.agents["requirements"].stage_artifacts = ["requirements.json"]
        vmodel_orchestrator.agents["design"].stage_artifacts = ["architecture.puml"]
        vmodel_orchestrator.agents["coding"].stage_artifacts = ["source_files.py"]

        result = await vmodel_orchestrator.execute_vmodel_workflow(initial_input)
        results = result["results"]

        # Verify artifacts accumulate through stages
        req_artifacts = results["requirements"]["result"]["artifacts"]
        assert "requirements.json" in req_artifacts

        design_artifacts = results["design"]["result"]["artifacts"]
        assert "requirements.json" in design_artifacts  # Inherited
        assert "architecture.puml" in design_artifacts  # Stage-specific

        final_artifacts = results["integration"]["result"]["artifacts"]
        assert "requirements.json" in final_artifacts
        assert "architecture.puml" in final_artifacts
        assert "source_files.py" in final_artifacts

    @pytest.mark.asyncio
    async def test_error_context_propagation(
        self, vmodel_orchestrator: MockVModelOrchestrator
    ) -> None:
        """Test that error context propagates correctly across stages."""

        # Get the coding agent and modify it directly
        coding_agent = vmodel_orchestrator.agents["coding"]

        # Store original method
        original_process = coding_agent._process_stage_specific

        async def _failing_stage_process(input_data: dict[str, Any]) -> dict[str, Any]:
            """Mock process that simulates stage failure."""
            # Simulate error in coding stage
            error_context = {
                "error": "Compilation failed",
                "stage": "coding",
                "recoverable": True,
                "attempted_fixes": ["syntax_check", "dependency_resolve"],
            }
            coding_agent.session_context["error_context"] = error_context
            raise RuntimeError("Coding stage failed")

        # Temporarily replace the method
        coding_agent._process_stage_specific = _failing_stage_process  # type: ignore[method-assign]

        try:
            try:
                await vmodel_orchestrator.execute_vmodel_workflow({"test": "error_handling"})
                raise AssertionError("Should have raised RuntimeError")
            except RuntimeError:
                pass
        finally:
            # Restore original method
            coding_agent._process_stage_specific = original_process  # type: ignore[method-assign]

        # Check that error context is preserved in coding agent
        assert "error_context" in coding_agent.session_context
        assert coding_agent.session_context["error_context"]["stage"] == "coding"
        assert coding_agent.session_context["error_context"]["recoverable"] is True


class TestSessionStateTransition:
    """Test session state transitions between V-Model stages."""

    @pytest.fixture
    def vmodel_orchestrator(self, isolated_agilevv_dir: PathConfig) -> MockVModelOrchestrator:
        """Provide mock V-Model orchestrator."""
        config = SDKConfig(api_key="test-transition-key")
        return MockVModelOrchestrator(config, isolated_agilevv_dir)

    @pytest.mark.asyncio
    async def test_clean_stage_transitions(
        self, vmodel_orchestrator: MockVModelOrchestrator
    ) -> None:
        """Test clean transitions between V-Model stages."""
        initial_input = {"transition_test": True}

        # Execute workflow and track transitions
        transition_log = []

        original_inherit = MockVModelAgent.inherit_context

        def _track_transitions(self: MockVModelAgent, previous_context: dict[str, Any]) -> None:
            transition_log.append(
                {
                    "stage": self.stage,
                    "inherited_from": previous_context.get("stage", "initial"),
                    "context_keys": list(previous_context.get("session_context", {}).keys()),
                }
            )
            return original_inherit(self, previous_context)

        with patch.object(MockVModelAgent, "inherit_context", _track_transitions):
            await vmodel_orchestrator.execute_vmodel_workflow(initial_input)

        # Verify transitions
        assert len(transition_log) == 4  # Design inherits from requirements, etc.
        assert transition_log[0]["stage"] == "design"
        assert transition_log[0]["inherited_from"] == "requirements"
        assert "requirements_output" in transition_log[0]["context_keys"]

        assert transition_log[3]["stage"] == "integration"
        assert transition_log[3]["inherited_from"] == "testing"

    @pytest.mark.asyncio
    async def test_rollback_capability(self, vmodel_orchestrator: MockVModelOrchestrator) -> None:
        """Test ability to rollback to previous stage context."""
        # Execute partial workflow
        initial_input = {"partial_workflow": True}

        # Execute first three stages
        partial_results: dict[str, Any] = {}
        for stage in vmodel_orchestrator.stages[:3]:  # requirements, design, coding
            agent = vmodel_orchestrator.agents[stage]

            if stage != "requirements":
                prev_stage = vmodel_orchestrator.stages[vmodel_orchestrator.stages.index(stage) - 1]
                agent.inherit_context(partial_results[prev_stage]["context"])

            result = await agent.process(initial_input)
            partial_results[stage] = {"result": result, "context": agent.get_stage_context()}

        # Simulate rollback to design stage
        design_context = partial_results["design"]["context"]

        # Create new coding agent with rollback context
        rollback_agent = MockVModelAgent(
            "coding", vmodel_orchestrator.sdk_config, vmodel_orchestrator.path_config
        )
        rollback_agent.inherit_context(design_context)

        # Verify rollback state
        assert rollback_agent.session_context["current_stage"] == "design"
        assert "requirements_output" in rollback_agent.session_context
        assert "design_output" in rollback_agent.session_context
        assert (
            "coding_output" not in rollback_agent.session_context
        )  # Should not exist after rollback

    @pytest.mark.asyncio
    async def test_concurrent_stage_isolation(
        self, vmodel_orchestrator: MockVModelOrchestrator
    ) -> None:
        """Test that concurrent V-Model workflows maintain session isolation."""

        async def _run_isolated_workflow(workflow_id: str) -> dict[str, Any]:
            """Run isolated V-Model workflow."""
            # Create separate orchestrator for isolation
            isolated_config = SDKConfig(api_key=f"test-isolated-{workflow_id}")
            isolated_orchestrator = MockVModelOrchestrator(
                isolated_config, vmodel_orchestrator.path_config
            )

            input_data = {"workflow_id": workflow_id, "feature": f"feature_{workflow_id}"}
            return await isolated_orchestrator.execute_vmodel_workflow(input_data)

        # Run three concurrent workflows
        import asyncio

        workflows = await asyncio.gather(
            _run_isolated_workflow("A"), _run_isolated_workflow("B"), _run_isolated_workflow("C")
        )

        # Verify isolation
        workflow_contexts = [w["final_context"]["session_context"] for w in workflows]

        # Each workflow should have unique stage sequence
        for i, context in enumerate(workflow_contexts):
            # workflow_id = chr(65 + i)  # A, B, C - not used in loop

            # Verify workflow-specific data exists
            assert context["current_stage"] == "integration"
            assert len(context["stage_sequence"]) == 5

            # Context should not contain data from other workflows
            for other_i, _other_context in enumerate(workflow_contexts):
                if i != other_i:
                    other_id = chr(65 + other_i)
                    # Should not have cross-contamination
                    assert f"feature_{other_id}" not in str(context)


class TestSessionPersistenceAcrossStages:
    """Test session persistence and restoration across V-Model stages."""

    @pytest.fixture
    def vmodel_orchestrator(self, isolated_agilevv_dir: PathConfig) -> MockVModelOrchestrator:
        """Provide mock V-Model orchestrator."""
        config = SDKConfig(api_key="test-persistence-key")
        return MockVModelOrchestrator(config, isolated_agilevv_dir)

    @pytest.mark.asyncio
    async def test_session_checkpoint_restoration(
        self, vmodel_orchestrator: MockVModelOrchestrator, tmp_path: Path
    ) -> None:
        """Test checkpointing and restoration of session state between stages."""
        initial_input = {"checkpoint_test": True}

        # Execute first two stages
        req_agent = vmodel_orchestrator.agents["requirements"]
        await req_agent.process(initial_input)

        design_agent = vmodel_orchestrator.agents["design"]
        design_agent.inherit_context(req_agent.get_stage_context())
        design_result = await design_agent.process(initial_input)

        # Save checkpoint after design stage
        checkpoint_file = tmp_path / "design_checkpoint.json"
        checkpoint_data = {
            "stage": "design",
            "session_context": design_result["session_context"],
            "workflow_metadata": {
                "completed_stages": ["requirements", "design"],
                "next_stage": "coding",
            },
        }

        with checkpoint_file.open("w") as f:
            json.dump(checkpoint_data, f)

        # Simulate restoration from checkpoint
        with checkpoint_file.open() as f:
            restored_data = json.load(f)

        # Create new coding agent and restore from checkpoint
        coding_agent = MockVModelAgent(
            "coding", vmodel_orchestrator.sdk_config, vmodel_orchestrator.path_config
        )
        coding_agent.session_context = restored_data["session_context"]

        coding_result = await coding_agent.process(initial_input)

        # Verify restoration worked correctly
        assert "requirements_output" in coding_result["session_context"]
        assert "design_output" in coding_result["session_context"]
        assert coding_result["session_context"]["current_stage"] == "coding"

    @pytest.mark.asyncio
    async def test_cross_session_context_continuity(
        self, vmodel_orchestrator: MockVModelOrchestrator, tmp_path: Path
    ) -> None:
        """Test context continuity across multiple sessions."""

        # Session 1: Execute first two stages
        session1_input = {"session": 1, "feature": "authentication"}

        await vmodel_orchestrator.agents["requirements"].process(session1_input)
        design_agent = vmodel_orchestrator.agents["design"]
        design_agent.inherit_context(vmodel_orchestrator.agents["requirements"].get_stage_context())
        design_result = await design_agent.process(session1_input)

        # Save session state
        session1_file = tmp_path / "session1_state.json"
        with session1_file.open("w") as f:
            json.dump(
                {
                    "session_context": design_result["session_context"],
                    "completed_stages": ["requirements", "design"],
                    "session_metadata": {"session_id": "sess_1", "user": "dev_1"},
                },
                f,
            )

        # Session 2: Continue from where session 1 left off
        with session1_file.open() as f:
            previous_session = json.load(f)

        # Create new orchestrator for session 2
        session2_orchestrator = MockVModelOrchestrator(
            SDKConfig(api_key="test-session2-key"), vmodel_orchestrator.path_config
        )

        # Restore context in coding agent
        coding_agent = session2_orchestrator.agents["coding"]
        coding_agent.session_context = previous_session["session_context"]
        coding_agent.session_context["session_continued"] = True
        coding_agent.session_context["original_session"] = "sess_1"

        session2_input = {"session": 2, "continuation": True}
        coding_result = await coding_agent.process(session2_input)

        # Verify continuity
        assert coding_result["session_context"]["session_continued"] is True
        assert coding_result["session_context"]["original_session"] == "sess_1"
        assert "requirements_output" in coding_result["session_context"]
        assert "design_output" in coding_result["session_context"]
        assert coding_result["session_context"]["current_stage"] == "coding"

    @pytest.mark.asyncio
    async def test_context_versioning_across_iterations(
        self, vmodel_orchestrator: MockVModelOrchestrator
    ) -> None:
        """Test context versioning across multiple V-Model iterations."""

        # Iteration 1
        iter1_input = {"iteration": 1, "feature": "basic_auth"}
        iter1_result = await vmodel_orchestrator.execute_vmodel_workflow(iter1_input)
        iter1_context = iter1_result["final_context"]["session_context"].copy()

        # Add iteration metadata
        iter1_context["iteration"] = 1
        iter1_context["version"] = "1.0.0"

        # Iteration 2: Build on iteration 1
        iter2_orchestrator = MockVModelOrchestrator(
            SDKConfig(api_key="test-iter2-key"), vmodel_orchestrator.path_config
        )

        # Initialize iteration 2 with previous context
        iter2_orchestrator.workflow_context = {
            "previous_iteration": iter1_context,
            "iteration": 2,
            "version": "2.0.0",
        }

        iter2_input = {"iteration": 2, "feature": "advanced_auth", "extends": "basic_auth"}
        iter2_result = await iter2_orchestrator.execute_vmodel_workflow(iter2_input)
        iter2_context = iter2_result["final_context"]["session_context"]

        # Verify iteration context
        assert iter2_context["iteration"] == 2
        assert iter2_context["version"] == "2.0.0"
        assert "previous_iteration" in iter2_context

        # Verify that both iterations' outputs are preserved
        prev_iter = iter2_context["previous_iteration"]
        assert prev_iter["iteration"] == 1
        assert prev_iter["version"] == "1.0.0"
        assert "requirements_output" in prev_iter  # Previous iteration context preserved
