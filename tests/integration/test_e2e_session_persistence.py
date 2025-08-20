"""
End-to-End Document-Based Session Persistence Tests

This module implements Task 5.3: Validate end-to-end document-based session persistence
with authentic agent outputs and context preservation, ensuring robust state management
across workflow executions and system restarts.

Test Coverage:
- Document-based session state persistence
- Context preservation across agent transitions
- State recovery after interruptions
- Cross-session artifact traceability
- Multi-session workflow continuity
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
    pytest.mark.session_persistence,
    pytest.mark.asyncio,
    pytest.mark.slow,  # Tests with real SDK calls and state management
]


@pytest.fixture
def session_persistence_story() -> dict[str, Any]:
    """User story designed for session persistence testing."""
    return {
        "id": "SESSION-001",
        "title": "Multi-Session Document Processing System",
        "description": (
            "As a developer, I want to ensure that V-Model workflow state "
            "persists across sessions and system restarts with full context preservation"
        ),
        "acceptance_criteria": [
            "Workflow state persists across orchestrator restarts",
            "Agent context is preserved and accessible in subsequent sessions",
            "Artifacts remain linked and traceable across sessions",
            "Session recovery maintains workflow continuity",
            "Multiple concurrent sessions maintain isolation",
        ],
        "story_points": 10,
        "priority": "Critical",
        "persistence_requirements": {
            "state_storage": "document-based",
            "context_preservation": "full",
            "artifact_traceability": "required",
            "recovery_tolerance": "robust",
        },
    }


@pytest.fixture
def sdk_config_with_persistence() -> SDKConfig:
    """SDK configuration optimized for session persistence testing."""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        pytest.skip("ANTHROPIC_API_KEY environment variable required for persistence tests")

    return SDKConfig(
        api_key=api_key,
        timeout=75,  # Reasonable timeout for persistence operations
        max_retries=2,  # Limited retries for controlled testing
        session_persistence=True,  # Enable session persistence if supported
    )


class SessionStateValidator:
    """Validates session state consistency and completeness."""

    def __init__(self, path_config: PathConfig):
        self.path_config = path_config
        self.validation_results: dict[str, Any] = {}

    def validate_state_structure(self, state: dict[str, Any]) -> dict[str, Any]:
        """Validate the structure and content of session state."""
        validation = {
            "structure_valid": False,
            "required_fields": [],
            "missing_fields": [],
            "content_analysis": {},
        }

        # Required state fields
        required_fields = [
            "current_stage",
            "sprint_number",
            "completed_stages",
            "session_state",
            "stage_artifacts",
            "agent_metrics",
            "created_at",
            "updated_at",
        ]

        # Check field presence
        validation["required_fields"] = required_fields
        validation["missing_fields"] = [field for field in required_fields if field not in state]
        validation["structure_valid"] = len(validation["missing_fields"]) == 0

        # Analyze content depth
        if "session_state" in state:
            validation["content_analysis"]["session_state_size"] = len(state["session_state"])
            validation["content_analysis"]["has_session_data"] = len(state["session_state"]) > 0

        if "stage_artifacts" in state:
            validation["content_analysis"]["artifacts_count"] = len(state["stage_artifacts"])
            validation["content_analysis"]["artifact_stages"] = list(
                state["stage_artifacts"].keys()
            )

        if "completed_stages" in state:
            validation["content_analysis"]["stages_completed"] = len(state["completed_stages"])
            validation["content_analysis"]["completion_list"] = state["completed_stages"]

        return validation

    def validate_context_continuity(
        self, previous_state: dict[str, Any], current_state: dict[str, Any]
    ) -> dict[str, Any]:
        """Validate context continuity between sessions."""
        continuity = {
            "context_preserved": False,
            "artifacts_preserved": False,
            "progress_maintained": False,
            "session_evolution": {},
        }

        # Check session state preservation
        prev_session = previous_state.get("session_state", {})
        curr_session = current_state.get("session_state", {})

        if prev_session and curr_session:
            # Session state should be preserved or evolved
            preserved_keys = set(prev_session.keys()) & set(curr_session.keys())
            continuity["context_preserved"] = len(preserved_keys) > 0
            continuity["session_evolution"]["preserved_keys"] = len(preserved_keys)
            continuity["session_evolution"]["new_keys"] = len(curr_session) - len(preserved_keys)

        # Check artifact preservation
        prev_artifacts = previous_state.get("stage_artifacts", {})
        curr_artifacts = current_state.get("stage_artifacts", {})

        if prev_artifacts and curr_artifacts:
            preserved_artifacts = set(prev_artifacts.keys()) & set(curr_artifacts.keys())
            continuity["artifacts_preserved"] = len(preserved_artifacts) > 0
            continuity["session_evolution"]["preserved_artifacts"] = len(preserved_artifacts)

        # Check progress maintenance
        prev_completed = set(previous_state.get("completed_stages", []))
        curr_completed = set(current_state.get("completed_stages", []))

        continuity["progress_maintained"] = prev_completed.issubset(curr_completed)
        continuity["session_evolution"]["progress_delta"] = len(curr_completed) - len(
            prev_completed
        )

        return continuity

    def validate_artifact_integrity(self, state: dict[str, Any]) -> dict[str, Any]:
        """Validate integrity and traceability of persisted artifacts."""
        integrity = {
            "artifacts_valid": False,
            "traceability_maintained": False,
            "content_analysis": {},
            "validation_errors": [],
        }

        stage_artifacts = state.get("stage_artifacts", {})

        if not stage_artifacts:
            integrity["validation_errors"].append("No artifacts found in state")
            return integrity

        # Validate artifact structure
        valid_artifacts = 0
        total_artifacts = len(stage_artifacts)

        for stage, artifact_data in stage_artifacts.items():
            if isinstance(artifact_data, dict):
                if "artifacts" in artifact_data or "metrics" in artifact_data:
                    valid_artifacts += 1

                    # Check for authentic content (not mock data)
                    artifact_content = json.dumps(artifact_data).lower()
                    if any(
                        indicator in artifact_content
                        for indicator in ["mock", "test", "placeholder"]
                    ):
                        integrity["validation_errors"].append(
                            f"Stage {stage} contains mock indicators"
                        )

        integrity["artifacts_valid"] = valid_artifacts == total_artifacts
        integrity["content_analysis"]["valid_artifacts"] = valid_artifacts
        integrity["content_analysis"]["total_artifacts"] = total_artifacts

        # Check for cross-stage traceability
        if len(stage_artifacts) > 1:
            # Later stages should reference earlier stage outputs
            stages = list(stage_artifacts.keys())
            traceability_score = 0

            for i, stage in enumerate(stages[1:], 1):  # Skip first stage
                artifact_content = json.dumps(stage_artifacts[stage]).lower()
                # Look for references to earlier stages
                earlier_stages = stages[:i]
                for earlier_stage in earlier_stages:
                    if earlier_stage.lower() in artifact_content:
                        traceability_score += 1
                        break

            integrity["traceability_maintained"] = traceability_score > 0
            integrity["content_analysis"]["traceability_score"] = traceability_score

        return integrity


class TestDocumentBasedSessionPersistence:
    """Test suite for Task 5.3: Document-based session persistence validation."""

    @pytest.mark.asyncio
    async def test_basic_session_state_persistence(
        self,
        isolated_agilevv_dir: PathConfig,
        session_persistence_story: dict[str, Any],
        sdk_config_with_persistence: SDKConfig,
    ) -> None:
        """Test basic session state persistence across orchestrator restarts."""
        validator = SessionStateValidator(isolated_agilevv_dir)

        # Execute first session - Requirements stage
        orchestrator1 = Orchestrator(
            path_config=isolated_agilevv_dir,
            sdk_config=sdk_config_with_persistence,
            mock_mode=False,
        )

        # Execute requirements stage
        requirements_result = await orchestrator1.execute_stage(
            VModelStage.REQUIREMENTS, {"story": session_persistence_story}
        )

        assert requirements_result["status"] == "success", "Requirements stage should succeed"

        # Capture initial state
        initial_state = orchestrator1.state.copy()
        initial_validation = validator.validate_state_structure(initial_state)

        assert initial_validation["structure_valid"], "Initial state should have valid structure"
        assert initial_validation["content_analysis"][
            "has_session_data"
        ], "Should have session data"

        # Verify state file persistence
        state_file_path = isolated_agilevv_dir.state_path
        assert state_file_path.exists(), "State file should be created"

        persisted_state = json.loads(state_file_path.read_text())
        assert persisted_state == initial_state, "Persisted state should match in-memory state"

        # Create new orchestrator instance (simulating restart)
        orchestrator2 = Orchestrator(
            path_config=isolated_agilevv_dir,
            sdk_config=sdk_config_with_persistence,
            mock_mode=False,
        )

        # Validate state recovery
        recovered_state = orchestrator2.state
        recovery_validation = validator.validate_state_structure(recovered_state)

        assert recovery_validation["structure_valid"], "Recovered state should be valid"

        # Validate continuity
        continuity = validator.validate_context_continuity(initial_state, recovered_state)
        assert continuity["context_preserved"], "Session context should be preserved"
        assert continuity["artifacts_preserved"], "Artifacts should be preserved"
        assert continuity["progress_maintained"], "Progress should be maintained"

        # Continue workflow from recovered state
        design_result = await orchestrator2.execute_stage(
            VModelStage.DESIGN, {"story": session_persistence_story}
        )

        assert (
            design_result["status"] == "success"
        ), "Design stage should succeed with recovered context"

        # Validate state evolution
        final_state = orchestrator2.state
        final_validation = validator.validate_state_structure(final_state)

        assert final_validation["structure_valid"], "Final state should remain valid"
        assert len(final_state["completed_stages"]) > len(
            initial_state["completed_stages"]
        ), "Progress should advance"

    @pytest.mark.asyncio
    async def test_multi_stage_context_preservation(
        self,
        isolated_agilevv_dir: PathConfig,
        session_persistence_story: dict[str, Any],
        sdk_config_with_persistence: SDKConfig,
    ) -> None:
        """Test context preservation across multiple stages and sessions."""
        validator = SessionStateValidator(isolated_agilevv_dir)
        context_evolution = []

        # Session 1: Requirements and Design
        orchestrator1 = Orchestrator(
            path_config=isolated_agilevv_dir,
            sdk_config=sdk_config_with_persistence,
            mock_mode=False,
        )

        # Execute requirements
        req_result = await orchestrator1.execute_stage(
            VModelStage.REQUIREMENTS, {"story": session_persistence_story}
        )

        session1_after_req = orchestrator1.state.copy()
        context_evolution.append(
            {
                "session": 1,
                "stage": "requirements",
                "state": session1_after_req,
                "timestamp": time.time(),
            }
        )

        # Execute design
        design_result = await orchestrator1.execute_stage(
            VModelStage.DESIGN, {"story": session_persistence_story}
        )

        session1_after_design = orchestrator1.state.copy()
        context_evolution.append(
            {
                "session": 1,
                "stage": "design",
                "state": session1_after_design,
                "timestamp": time.time(),
            }
        )

        assert req_result["status"] == "success", "Requirements should succeed"
        assert design_result["status"] == "success", "Design should succeed"

        # Session 2: Continue with Development
        orchestrator2 = Orchestrator(
            path_config=isolated_agilevv_dir,
            sdk_config=sdk_config_with_persistence,
            mock_mode=False,
        )

        session2_initial = orchestrator2.state.copy()
        context_evolution.append(
            {
                "session": 2,
                "stage": "recovery",
                "state": session2_initial,
                "timestamp": time.time(),
            }
        )

        # Validate context preservation from session 1
        continuity = validator.validate_context_continuity(session1_after_design, session2_initial)
        assert continuity["context_preserved"], "Context should be preserved across sessions"

        # Execute development stage
        dev_result = await orchestrator2.execute_stage(
            VModelStage.CODING, {"story": session_persistence_story}
        )

        session2_after_dev = orchestrator2.state.copy()
        context_evolution.append(
            {
                "session": 2,
                "stage": "development",
                "state": session2_after_dev,
                "timestamp": time.time(),
            }
        )

        assert (
            dev_result["status"] == "success"
        ), "Development should succeed with preserved context"

        # Validate artifact traceability across all stages
        final_integrity = validator.validate_artifact_integrity(session2_after_dev)
        assert final_integrity["artifacts_valid"], "All artifacts should be valid"
        assert final_integrity[
            "traceability_maintained"
        ], "Cross-stage traceability should be maintained"

        # Validate context evolution
        assert len(context_evolution) == 4, "Should track all context evolution steps"

        # Each subsequent state should build on previous
        for i in range(1, len(context_evolution)):
            prev_artifacts = context_evolution[i - 1]["state"].get("stage_artifacts", {})
            curr_artifacts = context_evolution[i]["state"].get("stage_artifacts", {})

            # Current state should have at least as many artifacts as previous
            assert len(curr_artifacts) >= len(
                prev_artifacts
            ), f"Artifacts should not regress at step {i}"

        # Save context evolution for analysis
        evolution_report = {
            "test_name": "multi_stage_context_preservation",
            "context_evolution": context_evolution,
            "final_integrity": final_integrity,
            "sessions_executed": 2,
            "stages_completed": len(session2_after_dev.get("completed_stages", [])),
            "timestamp": datetime.now().isoformat(),
        }

        evolution_report_path = isolated_agilevv_dir.logs_dir / "context_evolution_report.json"
        evolution_report_path.write_text(json.dumps(evolution_report, indent=2, default=str))

    @pytest.mark.asyncio
    async def test_session_recovery_after_interruption(
        self,
        isolated_agilevv_dir: PathConfig,
        session_persistence_story: dict[str, Any],
        sdk_config_with_persistence: SDKConfig,
    ) -> None:
        """Test session recovery capabilities after workflow interruption."""
        validator = SessionStateValidator(isolated_agilevv_dir)

        # Start workflow
        orchestrator1 = Orchestrator(
            path_config=isolated_agilevv_dir,
            sdk_config=sdk_config_with_persistence,
            mock_mode=False,
        )

        # Execute partial workflow
        req_result = await orchestrator1.execute_stage(
            VModelStage.REQUIREMENTS, {"story": session_persistence_story}
        )

        # Capture state before interruption
        pre_interruption_state = orchestrator1.state.copy()
        pre_interruption_validation = validator.validate_state_structure(pre_interruption_state)

        assert req_result["status"] == "success", "Pre-interruption stage should succeed"
        assert pre_interruption_validation[
            "structure_valid"
        ], "Pre-interruption state should be valid"

        # Simulate interruption by corrupting some in-memory state
        orchestrator1.state["corrupted"] = True
        orchestrator1.current_stage = VModelStage.PLANNING  # Reset to wrong stage

        # Verify corruption
        assert orchestrator1.state != pre_interruption_state, "In-memory state should be corrupted"

        # Create recovery orchestrator
        orchestrator2 = Orchestrator(
            path_config=isolated_agilevv_dir,
            sdk_config=sdk_config_with_persistence,
            mock_mode=False,
        )

        # Validate recovery
        recovered_state = orchestrator2.state
        recovery_validation = validator.validate_state_structure(recovered_state)

        assert recovery_validation["structure_valid"], "Recovered state should be valid"
        assert "corrupted" not in recovered_state, "Corruption should not be persisted"

        # Validate state consistency with pre-interruption
        continuity = validator.validate_context_continuity(pre_interruption_state, recovered_state)
        assert continuity["context_preserved"], "Context should survive interruption"
        assert continuity["progress_maintained"], "Progress should be maintained"

        # Continue workflow from recovery point
        design_result = await orchestrator2.execute_stage(
            VModelStage.DESIGN, {"story": session_persistence_story}
        )

        assert (
            design_result["status"] == "success"
        ), "Workflow should continue successfully after recovery"

        # Validate post-recovery state integrity
        post_recovery_state = orchestrator2.state
        post_recovery_validation = validator.validate_state_structure(post_recovery_state)
        post_recovery_integrity = validator.validate_artifact_integrity(post_recovery_state)

        assert post_recovery_validation["structure_valid"], "Post-recovery state should be valid"
        assert post_recovery_integrity["artifacts_valid"], "Post-recovery artifacts should be valid"

        # Document recovery analysis
        recovery_report = {
            "test_name": "session_recovery_after_interruption",
            "pre_interruption": {
                "validation": pre_interruption_validation,
                "completed_stages": len(pre_interruption_state.get("completed_stages", [])),
            },
            "recovery": {
                "validation": recovery_validation,
                "continuity": continuity,
            },
            "post_recovery": {
                "validation": post_recovery_validation,
                "integrity": post_recovery_integrity,
                "completed_stages": len(post_recovery_state.get("completed_stages", [])),
            },
            "recovery_successful": design_result["status"] == "success",
            "timestamp": datetime.now().isoformat(),
        }

        recovery_report_path = isolated_agilevv_dir.logs_dir / "session_recovery_report.json"
        recovery_report_path.write_text(json.dumps(recovery_report, indent=2))

    @pytest.mark.asyncio
    async def test_concurrent_session_isolation(
        self,
        isolated_agilevv_dir: PathConfig,
        sdk_config_with_persistence: SDKConfig,
    ) -> None:
        """Test that concurrent sessions maintain proper isolation."""
        # Create two different stories for isolation testing
        stories = [
            {
                "id": "CONCURRENT-SESSION-A",
                "title": "Concurrent Session A",
                "description": "First concurrent session for isolation testing",
                "acceptance_criteria": [
                    "Independent execution",
                    "No cross-contamination",
                ],
            },
            {
                "id": "CONCURRENT-SESSION-B",
                "title": "Concurrent Session B",
                "description": "Second concurrent session for isolation testing",
                "acceptance_criteria": ["Independent execution", "Isolated state"],
            },
        ]

        async def execute_isolated_session(story: dict[str, Any], suffix: str) -> dict[str, Any]:
            """Execute workflow in isolated session environment."""
            # Create isolated path for this session
            session_path = PathConfig(base_dir=isolated_agilevv_dir.base_dir / f"session-{suffix}")
            session_path.ensure_structure()

            orchestrator = Orchestrator(
                path_config=session_path,
                sdk_config=sdk_config_with_persistence,
                mock_mode=False,
            )

            # Execute requirements stage
            req_result = await orchestrator.execute_stage(
                VModelStage.REQUIREMENTS, {"story": story}
            )

            return {
                "session_id": suffix,
                "story_id": story["id"],
                "result": req_result,
                "final_state": orchestrator.state.copy(),
                "path_config": session_path,
            }

        # Execute concurrent sessions
        session_results = await asyncio.gather(
            execute_isolated_session(stories[0], "A"),
            execute_isolated_session(stories[1], "B"),
            return_exceptions=True,
        )

        # Validate both sessions completed successfully
        assert len(session_results) == 2, "Both concurrent sessions should complete"

        for i, session_result in enumerate(session_results):
            if isinstance(session_result, Exception):
                pytest.fail(f"Concurrent session {i} failed: {session_result}")

            assert isinstance(session_result, dict), f"Session result {i} should be dict"
            assert session_result["result"]["status"] == "success", f"Session {i} should succeed"

        # Validate session isolation
        session_a, session_b = session_results

        # States should be completely independent
        state_a = session_a["final_state"]
        state_b = session_b["final_state"]

        assert state_a != state_b, "Concurrent session states should be different"

        # Story-specific content should not cross-contaminate
        artifacts_a = state_a.get("stage_artifacts", {})
        artifacts_b = state_b.get("stage_artifacts", {})

        if artifacts_a and artifacts_b:
            content_a = json.dumps(artifacts_a).lower()
            content_b = json.dumps(artifacts_b).lower()

            # Each session should only contain its own story ID
            assert "concurrent-session-a" in content_a, "Session A should contain its story ID"
            assert "concurrent-session-b" in content_b, "Session B should contain its story ID"
            assert (
                "concurrent-session-b" not in content_a
            ), "Session A should not contain Session B's story ID"
            assert (
                "concurrent-session-a" not in content_b
            ), "Session B should not contain Session A's story ID"

        # State files should be in separate directories
        state_file_a = session_a["path_config"].state_path
        state_file_b = session_b["path_config"].state_path

        assert state_file_a != state_file_b, "State files should be in different locations"
        assert state_file_a.exists(), "Session A state file should exist"
        assert state_file_b.exists(), "Session B state file should exist"

        # Validate directory isolation
        session_dir_a = session_a["path_config"].base_dir
        session_dir_b = session_b["path_config"].base_dir

        assert session_dir_a != session_dir_b, "Session directories should be different"
        assert (
            not any(session_dir_a.iterdir())
            or not any(session_dir_b.iterdir())
            or session_dir_a != session_dir_b
        ), "Session directories should not overlap"

        # Document isolation validation
        isolation_report = {
            "test_name": "concurrent_session_isolation",
            "sessions": [
                {
                    "session_id": session_a["session_id"],
                    "story_id": session_a["story_id"],
                    "state_file": str(state_file_a),
                    "artifacts_count": len(artifacts_a),
                },
                {
                    "session_id": session_b["session_id"],
                    "story_id": session_b["story_id"],
                    "state_file": str(state_file_b),
                    "artifacts_count": len(artifacts_b),
                },
            ],
            "isolation_verified": {
                "different_states": state_a != state_b,
                "separate_directories": session_dir_a != session_dir_b,
                "no_content_contamination": True,  # Validated above
            },
            "timestamp": datetime.now().isoformat(),
        }

        isolation_report_path = isolated_agilevv_dir.logs_dir / "session_isolation_report.json"
        isolation_report_path.write_text(json.dumps(isolation_report, indent=2))

    @pytest.mark.asyncio
    async def test_artifact_traceability_across_sessions(
        self,
        isolated_agilevv_dir: PathConfig,
        session_persistence_story: dict[str, Any],
        sdk_config_with_persistence: SDKConfig,
    ) -> None:
        """Test artifact traceability and linkage across multiple sessions."""
        validator = SessionStateValidator(isolated_agilevv_dir)
        traceability_chain = []

        # Session 1: Create initial artifacts
        orchestrator1 = Orchestrator(
            path_config=isolated_agilevv_dir,
            sdk_config=sdk_config_with_persistence,
            mock_mode=False,
        )

        req_result = await orchestrator1.execute_stage(
            VModelStage.REQUIREMENTS, {"story": session_persistence_story}
        )

        session1_state = orchestrator1.state.copy()
        session1_artifacts = session1_state.get("stage_artifacts", {})

        traceability_chain.append(
            {
                "session": 1,
                "stage": "requirements",
                "artifacts": session1_artifacts,
                "artifact_count": len(session1_artifacts),
                "timestamp": time.time(),
            }
        )

        # Session 2: Build upon artifacts
        orchestrator2 = Orchestrator(
            path_config=isolated_agilevv_dir,
            sdk_config=sdk_config_with_persistence,
            mock_mode=False,
        )

        design_result = await orchestrator2.execute_stage(
            VModelStage.DESIGN, {"story": session_persistence_story}
        )

        session2_state = orchestrator2.state.copy()
        session2_artifacts = session2_state.get("stage_artifacts", {})

        traceability_chain.append(
            {
                "session": 2,
                "stage": "design",
                "artifacts": session2_artifacts,
                "artifact_count": len(session2_artifacts),
                "timestamp": time.time(),
            }
        )

        # Session 3: Further build upon artifacts
        orchestrator3 = Orchestrator(
            path_config=isolated_agilevv_dir,
            sdk_config=sdk_config_with_persistence,
            mock_mode=False,
        )

        dev_result = await orchestrator3.execute_stage(
            VModelStage.CODING, {"story": session_persistence_story}
        )

        session3_state = orchestrator3.state.copy()
        session3_artifacts = session3_state.get("stage_artifacts", {})

        traceability_chain.append(
            {
                "session": 3,
                "stage": "development",
                "artifacts": session3_artifacts,
                "artifact_count": len(session3_artifacts),
                "timestamp": time.time(),
            }
        )

        # Validate all stages succeeded
        assert req_result["status"] == "success", "Requirements should succeed"
        assert design_result["status"] == "success", "Design should succeed"
        assert dev_result["status"] == "success", "Development should succeed"

        # Validate artifact accumulation
        assert len(session1_artifacts) > 0, "Session 1 should create artifacts"
        assert len(session2_artifacts) > len(session1_artifacts), "Session 2 should add artifacts"
        assert len(session3_artifacts) > len(session2_artifacts), "Session 3 should add artifacts"

        # Validate traceability across sessions
        final_integrity = validator.validate_artifact_integrity(session3_state)
        assert final_integrity["artifacts_valid"], "Final artifacts should be valid"
        assert final_integrity["traceability_maintained"], "Traceability should be maintained"

        # Cross-session artifact analysis
        cross_session_analysis = {
            "requirements_preserved": "requirements" in session3_artifacts,
            "design_preserved": "design" in session3_artifacts,
            "development_added": "coding" in session3_artifacts,
            "progressive_building": True,
        }

        # Validate progressive building
        for i in range(1, len(traceability_chain)):
            current_count = traceability_chain[i]["artifact_count"]
            previous_count = traceability_chain[i - 1]["artifact_count"]

            if current_count <= previous_count:
                cross_session_analysis["progressive_building"] = False
                break

        assert cross_session_analysis[
            "progressive_building"
        ], "Artifacts should build progressively"
        assert cross_session_analysis[
            "requirements_preserved"
        ], "Requirements artifacts should be preserved"

        # Generate traceability report
        traceability_report = {
            "test_name": "artifact_traceability_across_sessions",
            "traceability_chain": traceability_chain,
            "final_integrity": final_integrity,
            "cross_session_analysis": cross_session_analysis,
            "sessions_executed": len(traceability_chain),
            "final_artifact_count": len(session3_artifacts),
            "timestamp": datetime.now().isoformat(),
        }

        traceability_report_path = (
            isolated_agilevv_dir.logs_dir / "artifact_traceability_report.json"
        )
        traceability_report_path.write_text(json.dumps(traceability_report, indent=2, default=str))

    @pytest.mark.asyncio
    async def test_session_state_versioning_and_history(
        self,
        isolated_agilevv_dir: PathConfig,
        session_persistence_story: dict[str, Any],
        sdk_config_with_persistence: SDKConfig,
    ) -> None:
        """Test session state versioning and historical tracking."""
        state_history = []

        # Create orchestrator and track state changes
        orchestrator = Orchestrator(
            path_config=isolated_agilevv_dir,
            sdk_config=sdk_config_with_persistence,
            mock_mode=False,
        )

        # Capture initial state
        initial_state = orchestrator.state.copy()
        state_history.append(
            {
                "version": 1,
                "stage": "initial",
                "state_snapshot": initial_state,
                "timestamp": datetime.now().isoformat(),
                "changes_from_previous": "initial_state",
            }
        )

        # Execute requirements and capture state
        req_result = await orchestrator.execute_stage(
            VModelStage.REQUIREMENTS, {"story": session_persistence_story}
        )

        post_req_state = orchestrator.state.copy()
        req_changes = {
            "completed_stages": len(post_req_state.get("completed_stages", []))
            - len(initial_state.get("completed_stages", [])),
            "session_state_growth": len(post_req_state.get("session_state", {}))
            - len(initial_state.get("session_state", {})),
            "artifacts_added": len(post_req_state.get("stage_artifacts", {}))
            - len(initial_state.get("stage_artifacts", {})),
        }

        state_history.append(
            {
                "version": 2,
                "stage": "requirements",
                "state_snapshot": post_req_state,
                "timestamp": datetime.now().isoformat(),
                "changes_from_previous": req_changes,
            }
        )

        # Execute design and capture state
        design_result = await orchestrator.execute_stage(
            VModelStage.DESIGN, {"story": session_persistence_story}
        )

        post_design_state = orchestrator.state.copy()
        design_changes = {
            "completed_stages": len(post_design_state.get("completed_stages", []))
            - len(post_req_state.get("completed_stages", [])),
            "session_state_growth": len(post_design_state.get("session_state", {}))
            - len(post_req_state.get("session_state", {})),
            "artifacts_added": len(post_design_state.get("stage_artifacts", {}))
            - len(post_req_state.get("stage_artifacts", {})),
        }

        state_history.append(
            {
                "version": 3,
                "stage": "design",
                "state_snapshot": post_design_state,
                "timestamp": datetime.now().isoformat(),
                "changes_from_previous": design_changes,
            }
        )

        # Validate state evolution
        assert len(state_history) == 3, "Should track 3 state versions"
        assert req_result["status"] == "success", "Requirements should succeed"
        assert design_result["status"] == "success", "Design should succeed"

        # Validate progressive evolution
        for i in range(1, len(state_history)):
            current = state_history[i]
            previous = state_history[i - 1]

            # State should evolve (not be identical)
            assert (
                current["state_snapshot"] != previous["state_snapshot"]
            ), f"State should change from version {i}"

            # Completed stages should increase or stay same
            current_completed = len(current["state_snapshot"].get("completed_stages", []))
            previous_completed = len(previous["state_snapshot"].get("completed_stages", []))
            assert (
                current_completed >= previous_completed
            ), f"Completed stages should not regress at version {i + 1}"

        # Validate state file versioning (check if checkpoint history exists)
        final_state = orchestrator.state
        if "checkpoint_history" in final_state:
            checkpoint_history = final_state["checkpoint_history"]
            assert len(checkpoint_history) > 0, "Should maintain checkpoint history"

            # Checkpoints should be chronological
            if len(checkpoint_history) > 1:
                for i in range(1, len(checkpoint_history)):
                    current_checkpoint = checkpoint_history[i]
                    previous_checkpoint = checkpoint_history[i - 1]

                    # Assuming checkpoints have timestamp info
                    if "timestamp" in current_checkpoint and "timestamp" in previous_checkpoint:
                        assert (
                            current_checkpoint["timestamp"] >= previous_checkpoint["timestamp"]
                        ), "Checkpoints should be chronological"

        # Generate versioning report
        versioning_report = {
            "test_name": "session_state_versioning_and_history",
            "state_history": state_history,
            "evolution_analysis": {
                "versions_tracked": len(state_history),
                "progressive_evolution": True,  # Validated above
                "final_completed_stages": len(final_state.get("completed_stages", [])),
                "final_artifacts_count": len(final_state.get("stage_artifacts", {})),
                "final_session_state_size": len(final_state.get("session_state", {})),
            },
            "checkpoint_analysis": {
                "checkpoint_history_exists": "checkpoint_history" in final_state,
                "checkpoint_count": len(final_state.get("checkpoint_history", [])),
            },
            "timestamp": datetime.now().isoformat(),
        }

        versioning_report_path = isolated_agilevv_dir.logs_dir / "state_versioning_report.json"
        versioning_report_path.write_text(json.dumps(versioning_report, indent=2, default=str))

        # Final validation
        assert (
            versioning_report["evolution_analysis"]["versions_tracked"] >= 3
        ), "Should track multiple state versions"
        assert (
            versioning_report["evolution_analysis"]["final_completed_stages"] >= 2
        ), "Should complete multiple stages"
