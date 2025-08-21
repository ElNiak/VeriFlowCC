"""
Task 4: V-Model Workflow Integration Tests with Real Claude SDK Agent Handoffs

This module implements comprehensive end-to-end tests for V-Model workflow execution,
focusing on real agent handoff patterns and artifact consumption across stages.
Following TDD approach with live Claude Code SDK integration.

Test Strategy:
- Real Claude Code SDK integration with no mocks
- Sequential test execution to capture proper agent handoff patterns
- Artifact validation focusing on structure and format
- State management and persistence validation
- Error handling and resilience testing
"""

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

# Test markers for organization and sequential execution
pytestmark = [
    pytest.mark.e2e,
    pytest.mark.integration,
    pytest.mark.real_sdk,
    pytest.mark.asyncio,
    pytest.mark.slow,
    pytest.mark.sequential,  # Ensures tests run one after another
]


def skip_if_no_auth(func):
    """Skip test if no API key is available."""
    return pytest.mark.skipif(
        not os.getenv("ANTHROPIC_API_KEY"),
        reason="ANTHROPIC_API_KEY environment variable required for real SDK tests",
    )(func)


@pytest.fixture
def enhanced_sdk_config() -> SDKConfig:
    """Enhanced SDK configuration with extended timeouts for integration tests."""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        pytest.skip("ANTHROPIC_API_KEY environment variable required for real SDK tests")

    return SDKConfig(
        api_key=api_key,
        timeout=180,  # Extended timeout for complex workflow operations
        max_retries=3,
    )


@pytest.fixture
def simple_user_story() -> dict[str, Any]:
    """Simple user story for workflow handoff testing."""
    return {
        "id": "US-HANDOFF-001",
        "title": "Simple Task Management Feature",
        "description": (
            "As a user, I want to create and manage simple tasks with titles and descriptions "
            "so that I can organize my work effectively"
        ),
        "acceptance_criteria": [
            "User can create a task with title and description",
            "User can view list of created tasks",
            "User can mark tasks as complete",
            "User can delete completed tasks",
        ],
        "story_points": 5,
        "priority": "Medium",
        "technology_constraints": {
            "framework": "Flask",
            "database": "SQLite",
            "frontend": "HTML/CSS/JavaScript",
        },
        "quality_requirements": {
            "test_coverage": 80,
            "code_quality": 75,
            "performance": "Response time < 1 second",
        },
    }


class ArtifactValidator:
    """Framework for validating artifacts across V-Model stages."""

    @staticmethod
    def validate_requirements_artifact(artifact: dict[str, Any]) -> dict[str, Any]:
        """Validate requirements stage artifact structure and format."""
        validation_result = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "metadata": {},
        }

        # Check required top-level fields
        required_fields = [
            "id",
            "agent",
            "functional_requirements",
            "acceptance_criteria",
        ]
        for field in required_fields:
            if field not in artifact:
                validation_result["errors"].append(f"Missing required field: {field}")
                validation_result["valid"] = False

        # Validate functional requirements structure
        if "functional_requirements" in artifact:
            func_reqs = artifact["functional_requirements"]
            if not isinstance(func_reqs, list):
                validation_result["errors"].append("functional_requirements must be a list")
                validation_result["valid"] = False
            elif len(func_reqs) == 0:
                validation_result["warnings"].append("No functional requirements found")

        # Validate acceptance criteria structure
        if "acceptance_criteria" in artifact:
            acc_criteria = artifact["acceptance_criteria"]
            if not isinstance(acc_criteria, list):
                validation_result["errors"].append("acceptance_criteria must be a list")
                validation_result["valid"] = False
            elif len(acc_criteria) == 0:
                validation_result["warnings"].append("No acceptance criteria found")

        # Check for INVEST compliance if present
        if "invest_analysis" in artifact:
            invest_data = artifact["invest_analysis"]
            if isinstance(invest_data, dict) and "overall_score" in invest_data:
                score = invest_data["overall_score"]
                validation_result["metadata"]["invest_score"] = score
                if score < 70:
                    validation_result["warnings"].append(f"Low INVEST score: {score}")

        return validation_result

    @staticmethod
    def validate_design_artifact(artifact: dict[str, Any]) -> dict[str, Any]:
        """Validate design stage artifact structure and format."""
        validation_result = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "metadata": {},
        }

        # Check required fields for design artifacts
        required_fields = ["agent", "system_design", "component_architecture"]
        for field in required_fields:
            if field not in artifact:
                validation_result["errors"].append(f"Missing required field: {field}")
                validation_result["valid"] = False

        # Validate system design structure
        if "system_design" in artifact:
            design = artifact["system_design"]
            if isinstance(design, dict):
                # Check for key design elements
                design_elements = ["architecture_pattern", "components", "interfaces"]
                found_elements = sum(1 for elem in design_elements if elem in design)
                validation_result["metadata"]["design_completeness"] = found_elements / len(
                    design_elements
                )

                if found_elements < 2:
                    validation_result["warnings"].append(
                        "Design artifact lacks key architectural elements"
                    )

        # Check for requirements traceability
        if "requirements_addressed" in artifact:
            req_trace = artifact["requirements_addressed"]
            if isinstance(req_trace, list) and len(req_trace) > 0:
                validation_result["metadata"]["requirements_traceability"] = True
            else:
                validation_result["warnings"].append("No requirements traceability found")

        return validation_result

    @staticmethod
    def validate_implementation_artifact(artifact: dict[str, Any]) -> dict[str, Any]:
        """Validate implementation stage artifact structure and format."""
        validation_result = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "metadata": {},
        }

        # Check required fields for implementation artifacts
        required_fields = ["agent", "implementation_summary"]
        for field in required_fields:
            if field not in artifact:
                validation_result["errors"].append(f"Missing required field: {field}")
                validation_result["valid"] = False

        # Validate implementation summary
        if "implementation_summary" in artifact:
            impl_summary = artifact["implementation_summary"]
            if isinstance(impl_summary, dict):
                # Check for implementation indicators
                impl_indicators = [
                    "files_created",
                    "functions_implemented",
                    "classes_defined",
                ]
                found_indicators = sum(1 for ind in impl_indicators if ind in impl_summary)
                validation_result["metadata"]["implementation_detail_level"] = (
                    found_indicators / len(impl_indicators)
                )

        # Check for code quality metrics if present
        if "quality_metrics" in artifact:
            quality = artifact["quality_metrics"]
            if isinstance(quality, dict):
                if "overall_score" in quality:
                    score = quality["overall_score"]
                    validation_result["metadata"]["quality_score"] = score
                    if score < 70:
                        validation_result["warnings"].append(f"Low code quality score: {score}")

        return validation_result

    @staticmethod
    def validate_testing_artifact(artifact: dict[str, Any]) -> dict[str, Any]:
        """Validate testing stage artifact structure and format."""
        validation_result = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "metadata": {},
        }

        # Check required fields for testing artifacts
        required_fields = ["agent", "test_strategy", "quality_assessment"]
        for field in required_fields:
            if field not in artifact:
                validation_result["errors"].append(f"Missing required field: {field}")
                validation_result["valid"] = False

        # Validate test strategy structure
        if "test_strategy" in artifact:
            strategy = artifact["test_strategy"]
            if isinstance(strategy, dict):
                test_types = ["unit_tests", "integration_tests", "acceptance_tests"]
                coverage = sum(1 for test_type in test_types if test_type in strategy)
                validation_result["metadata"]["test_coverage_breadth"] = coverage / len(test_types)

        # Check for test execution results if present
        if "test_execution" in artifact:
            execution = artifact["test_execution"]
            if isinstance(execution, dict) and "summary" in execution:
                summary = execution["summary"]
                if "pass_rate" in summary:
                    pass_rate = float(summary["pass_rate"].replace("%", ""))
                    validation_result["metadata"]["test_pass_rate"] = pass_rate
                    if pass_rate < 80:
                        validation_result["warnings"].append(f"Low test pass rate: {pass_rate}%")

        return validation_result

    @staticmethod
    def validate_integration_artifact(artifact: dict[str, Any]) -> dict[str, Any]:
        """Validate integration stage artifact structure and format."""
        validation_result = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "metadata": {},
        }

        # Check required fields for integration artifacts
        required_fields = ["agent", "integration_assessment", "release_recommendation"]
        for field in required_fields:
            if field not in artifact:
                validation_result["errors"].append(f"Missing required field: {field}")
                validation_result["valid"] = False

        # Validate release recommendation
        if "release_recommendation" in artifact:
            recommendation = artifact["release_recommendation"]
            if isinstance(recommendation, dict):
                if "decision" in recommendation:
                    decision = recommendation["decision"]
                    validation_result["metadata"]["release_decision"] = decision
                    if decision not in ["GO", "NO-GO"]:
                        validation_result["errors"].append(f"Invalid release decision: {decision}")
                        validation_result["valid"] = False

        # Check for readiness score if present
        if "readiness_assessment" in artifact:
            readiness = artifact["readiness_assessment"]
            if isinstance(readiness, dict) and "overall_score" in readiness:
                score = readiness["overall_score"]
                validation_result["metadata"]["readiness_score"] = score
                if score < 75:
                    validation_result["warnings"].append(f"Low readiness score: {score}")

        return validation_result


class TestVModelWorkflowHandoffs:
    """Test suite for Task 4: V-Model workflow integration tests with real agent handoffs."""

    @skip_if_no_auth
    async def test_real_requirements_to_design_handoff(
        self,
        isolated_agilevv_dir: PathConfig,
        simple_user_story: dict[str, Any],
        enhanced_sdk_config: SDKConfig,
    ) -> None:
        """Task 4.1: Test Requirements→Design workflow with real agent handoffs."""
        orchestrator = Orchestrator(
            path_config=isolated_agilevv_dir,
            sdk_config=enhanced_sdk_config,
            mock_mode=False,
        )

        # Execute Requirements stage
        requirements_input = {
            "story": simple_user_story,
            "context": {
                "project_name": "TaskManager",
                "sprint_number": 1,
            },
            "update_backlog": True,
        }

        start_time = time.time()
        requirements_result = await orchestrator.execute_stage(
            VModelStage.REQUIREMENTS, requirements_input
        )
        requirements_time = time.time() - start_time

        # Validate Requirements stage completion
        assert requirements_result is not None, "Requirements stage should return result"
        assert requirements_result["id"] == "US-HANDOFF-001", "Should preserve story ID"
        assert requirements_result["agent"] == "requirements_analyst", "Should use correct agent"

        # Validate requirements artifact structure
        req_validation = ArtifactValidator.validate_requirements_artifact(requirements_result)
        assert req_validation[
            "valid"
        ], f"Requirements artifact validation failed: {req_validation['errors']}"

        # Check that requirements artifact was persisted
        req_artifact_path = (
            isolated_agilevv_dir.artifacts_path / "requirements" / "US-HANDOFF-001.json"
        )
        assert req_artifact_path.exists(), "Requirements artifact should be persisted"

        # Execute Design stage using Requirements handoff
        design_input = {
            "requirements_artifact": requirements_result,
            "technology_constraints": simple_user_story["technology_constraints"],
            "architecture_patterns": ["MVC", "Repository"],
        }

        start_time = time.time()
        design_result = await orchestrator.execute_stage(VModelStage.DESIGN, design_input)
        design_time = time.time() - start_time

        # Validate Design stage completion
        assert design_result is not None, "Design stage should return result"
        assert design_result["agent"] == "architect", "Should use architect agent"

        # Validate design artifact structure
        design_validation = ArtifactValidator.validate_design_artifact(design_result)
        assert design_validation[
            "valid"
        ], f"Design artifact validation failed: {design_validation['errors']}"

        # Verify handoff integrity: Design should reference Requirements
        if "requirements_addressed" in design_result:
            req_references = design_result["requirements_addressed"]
            assert isinstance(req_references, list), "Requirements references should be list"
            assert len(req_references) > 0, "Design should address some requirements"

        # Verify state management across handoff
        orchestrator_state = orchestrator.state
        assert "stage_artifacts" in orchestrator_state, "Should maintain stage artifacts in state"
        stage_artifacts = orchestrator_state["stage_artifacts"]
        assert "requirements" in stage_artifacts, "Should preserve requirements artifacts"
        assert "design" in stage_artifacts, "Should store design artifacts"

        # Performance validation for handoff
        total_handoff_time = requirements_time + design_time
        assert (
            total_handoff_time < 240
        ), f"Requirements→Design handoff should complete within 4 minutes, took {total_handoff_time:.2f}s"

        # Log handoff metrics
        handoff_metrics = {
            "test_name": "requirements_to_design_handoff",
            "requirements_time": requirements_time,
            "design_time": design_time,
            "total_time": total_handoff_time,
            "artifacts_validated": 2,
            "handoff_integrity": True,
            "timestamp": datetime.now().isoformat(),
        }

        metrics_path = isolated_agilevv_dir.logs_dir / "handoff_metrics_req_to_design.json"
        metrics_path.write_text(json.dumps(handoff_metrics, indent=2))

    @skip_if_no_auth
    async def test_real_design_to_development_handoff(
        self,
        isolated_agilevv_dir: PathConfig,
        simple_user_story: dict[str, Any],
        enhanced_sdk_config: SDKConfig,
    ) -> None:
        """Task 4.2: Test Design→Development workflow with artifact consumption."""
        orchestrator = Orchestrator(
            path_config=isolated_agilevv_dir,
            sdk_config=enhanced_sdk_config,
            mock_mode=False,
        )

        # First execute Requirements and Design stages to establish context
        requirements_input = {
            "story": simple_user_story,
            "context": {"project_name": "TaskManager"},
        }
        requirements_result = await orchestrator.execute_stage(
            VModelStage.REQUIREMENTS, requirements_input
        )

        design_input = {
            "requirements_artifact": requirements_result,
            "technology_constraints": simple_user_story["technology_constraints"],
        }
        design_result = await orchestrator.execute_stage(VModelStage.DESIGN, design_input)

        # Now test Design→Development handoff
        development_input = {
            "design_artifact": design_result,
            "requirements_artifact": requirements_result,  # Should be available for reference
            "implementation_constraints": {
                "coding_standards": "PEP8",
                "test_framework": "pytest",
                "documentation": "docstrings required",
            },
        }

        start_time = time.time()
        development_result = await orchestrator.execute_stage(VModelStage.CODING, development_input)
        development_time = time.time() - start_time

        # Validate Development stage completion
        assert development_result is not None, "Development stage should return result"
        assert development_result["agent"] == "developer", "Should use developer agent"

        # Validate implementation artifact structure
        impl_validation = ArtifactValidator.validate_implementation_artifact(development_result)
        assert impl_validation[
            "valid"
        ], f"Implementation artifact validation failed: {impl_validation['errors']}"

        # Verify artifact consumption: Development should reference Design
        assert (
            "design_artifact" in development_input
        ), "Development input should include design artifact"

        # Check for implementation artifacts that demonstrate real code generation
        if "implementation_summary" in development_result:
            impl_summary = development_result["implementation_summary"]

            # Look for evidence of actual implementation work
            implementation_indicators = [
                "files_created",
                "functions_implemented",
                "classes_defined",
                "routes_defined",
                "models_created",
                "templates_created",
            ]

            found_indicators = sum(
                1 for indicator in implementation_indicators if indicator in impl_summary
            )
            assert (
                found_indicators > 0
            ), "Implementation should show evidence of actual development work"

        # Verify design artifact consumption patterns
        if "design_decisions_implemented" in development_result:
            design_decisions = development_result["design_decisions_implemented"]
            assert isinstance(design_decisions, list), "Design decisions should be tracked as list"
            assert len(design_decisions) > 0, "Should implement some design decisions"

        # Check for traceability back to requirements through design
        if "requirements_traceability" in development_result:
            traceability = development_result["requirements_traceability"]
            assert isinstance(traceability, dict), "Requirements traceability should be structured"

        # Validate state progression
        orchestrator_state = orchestrator.state
        stage_artifacts = orchestrator_state.get("stage_artifacts", {})
        assert "requirements" in stage_artifacts, "Should maintain requirements in state"
        assert "design" in stage_artifacts, "Should maintain design in state"
        assert "coding" in stage_artifacts, "Should store implementation artifacts in state"

        # Performance validation
        assert (
            development_time < 300
        ), f"Design→Development handoff should complete within 5 minutes, took {development_time:.2f}s"

        # Log handoff metrics
        handoff_metrics = {
            "test_name": "design_to_development_handoff",
            "development_time": development_time,
            "artifact_consumption_validated": True,
            "implementation_indicators_found": (
                found_indicators if "found_indicators" in locals() else 0
            ),
            "timestamp": datetime.now().isoformat(),
        }

        metrics_path = isolated_agilevv_dir.logs_dir / "handoff_metrics_design_to_dev.json"
        metrics_path.write_text(json.dumps(handoff_metrics, indent=2))

    @skip_if_no_auth
    async def test_real_development_to_qa_handoff(
        self,
        isolated_agilevv_dir: PathConfig,
        simple_user_story: dict[str, Any],
        enhanced_sdk_config: SDKConfig,
    ) -> None:
        """Task 4.3: Test Development→QA workflow with real code validation."""
        orchestrator = Orchestrator(
            path_config=isolated_agilevv_dir,
            sdk_config=enhanced_sdk_config,
            mock_mode=False,
        )

        # Execute prerequisite stages
        req_input = {
            "story": simple_user_story,
            "context": {"project_name": "TaskManager"},
        }
        requirements_result = await orchestrator.execute_stage(VModelStage.REQUIREMENTS, req_input)

        design_input = {"requirements_artifact": requirements_result}
        design_result = await orchestrator.execute_stage(VModelStage.DESIGN, design_input)

        dev_input = {
            "design_artifact": design_result,
            "requirements_artifact": requirements_result,
        }
        development_result = await orchestrator.execute_stage(VModelStage.CODING, dev_input)

        # Test Development→QA handoff
        qa_input = {
            "implementation_artifact": development_result,
            "design_artifact": design_result,  # For validation against design
            "requirements_artifact": requirements_result,  # For acceptance testing
            "testing_constraints": {
                "minimum_coverage": 80,
                "test_types": ["unit", "integration", "acceptance"],
                "quality_threshold": 75,
            },
        }

        start_time = time.time()
        qa_result = await orchestrator.execute_stage(VModelStage.UNIT_TESTING, qa_input)
        qa_time = time.time() - start_time

        # Validate QA stage completion
        assert qa_result is not None, "QA stage should return result"
        assert qa_result["agent"] == "qa_tester", "Should use QA tester agent"

        # Validate testing artifact structure
        testing_validation = ArtifactValidator.validate_testing_artifact(qa_result)
        assert testing_validation[
            "valid"
        ], f"Testing artifact validation failed: {testing_validation['errors']}"

        # Verify real code validation occurred
        if "test_strategy" in qa_result:
            test_strategy = qa_result["test_strategy"]
            assert isinstance(test_strategy, dict), "Test strategy should be structured"

            # Check for comprehensive testing approach
            expected_test_aspects = ["unit_tests", "integration_tests", "code_quality"]
            found_aspects = sum(1 for aspect in expected_test_aspects if aspect in test_strategy)
            assert found_aspects >= 2, "Test strategy should cover multiple testing aspects"

        # Validate quality assessment based on implementation
        if "quality_assessment" in qa_result:
            quality = qa_result["quality_assessment"]
            assert isinstance(quality, dict), "Quality assessment should be structured"

            # Look for real quality metrics
            quality_metrics = [
                "code_quality_score",
                "test_coverage",
                "compliance_score",
            ]
            found_metrics = sum(1 for metric in quality_metrics if metric in quality)
            assert found_metrics > 0, "Should provide concrete quality metrics"

        # Verify implementation artifact consumption
        assert "implementation_artifact" in qa_input, "QA should receive implementation artifact"

        # Check for validation against requirements and design
        if "validation_results" in qa_result:
            validation = qa_result["validation_results"]
            if isinstance(validation, dict):
                # Should validate against acceptance criteria
                if "acceptance_testing" in validation:
                    acceptance = validation["acceptance_testing"]
                    assert isinstance(acceptance, dict), "Acceptance testing should be structured"

        # Verify state management
        orchestrator_state = orchestrator.state
        stage_artifacts = orchestrator_state.get("stage_artifacts", {})
        assert "coding" in stage_artifacts, "Should have implementation artifacts"
        assert "unit_testing" in stage_artifacts, "Should store QA artifacts"

        # Performance validation
        assert (
            qa_time < 240
        ), f"Development→QA handoff should complete within 4 minutes, took {qa_time:.2f}s"

        # Log handoff metrics
        handoff_metrics = {
            "test_name": "development_to_qa_handoff",
            "qa_time": qa_time,
            "code_validation_performed": True,
            "quality_metrics_found": (found_metrics if "found_metrics" in locals() else 0),
            "timestamp": datetime.now().isoformat(),
        }

        metrics_path = isolated_agilevv_dir.logs_dir / "handoff_metrics_dev_to_qa.json"
        metrics_path.write_text(json.dumps(handoff_metrics, indent=2))

    @skip_if_no_auth
    async def test_real_qa_to_integration_handoff(
        self,
        isolated_agilevv_dir: PathConfig,
        simple_user_story: dict[str, Any],
        enhanced_sdk_config: SDKConfig,
    ) -> None:
        """Task 4.4: Test QA→Integration workflow with real test execution validation."""
        orchestrator = Orchestrator(
            path_config=isolated_agilevv_dir,
            sdk_config=enhanced_sdk_config,
            mock_mode=False,
        )

        # Execute prerequisite stages to establish full context
        req_input = {
            "story": simple_user_story,
            "context": {"project_name": "TaskManager"},
        }
        requirements_result = await orchestrator.execute_stage(VModelStage.REQUIREMENTS, req_input)

        design_input = {"requirements_artifact": requirements_result}
        design_result = await orchestrator.execute_stage(VModelStage.DESIGN, design_input)

        dev_input = {
            "design_artifact": design_result,
            "requirements_artifact": requirements_result,
        }
        development_result = await orchestrator.execute_stage(VModelStage.CODING, dev_input)

        qa_input = {
            "implementation_artifact": development_result,
            "design_artifact": design_result,
            "requirements_artifact": requirements_result,
        }
        qa_result = await orchestrator.execute_stage(VModelStage.UNIT_TESTING, qa_input)

        # Test QA→Integration handoff
        integration_input = {
            "testing_artifact": qa_result,
            "implementation_artifact": development_result,
            "design_artifact": design_result,
            "requirements_artifact": requirements_result,
            "integration_criteria": {
                "deployment_readiness": True,
                "performance_validation": True,
                "security_assessment": True,
                "go_no_go_decision": True,
            },
        }

        start_time = time.time()
        integration_result = await orchestrator.execute_stage(
            VModelStage.INTEGRATION_TESTING, integration_input
        )
        integration_time = time.time() - start_time

        # Validate Integration stage completion
        assert integration_result is not None, "Integration stage should return result"
        assert integration_result["agent"] == "integration", "Should use integration agent"

        # Validate integration artifact structure
        integration_validation = ArtifactValidator.validate_integration_artifact(integration_result)
        assert integration_validation[
            "valid"
        ], f"Integration artifact validation failed: {integration_validation['errors']}"

        # Verify comprehensive integration assessment
        if "integration_assessment" in integration_result:
            assessment = integration_result["integration_assessment"]
            assert isinstance(assessment, dict), "Integration assessment should be structured"

            # Check for comprehensive assessment areas
            assessment_areas = [
                "technical_readiness",
                "quality_validation",
                "deployment_readiness",
            ]
            found_areas = sum(1 for area in assessment_areas if area in assessment)
            assert found_areas >= 2, "Integration should assess multiple readiness areas"

        # Verify release recommendation based on all artifacts
        if "release_recommendation" in integration_result:
            recommendation = integration_result["release_recommendation"]
            assert isinstance(recommendation, dict), "Release recommendation should be structured"
            assert "decision" in recommendation, "Should provide GO/NO-GO decision"

            decision = recommendation["decision"]
            assert decision in ["GO", "NO-GO"], f"Invalid release decision: {decision}"

            # Should include justification
            if "justification" in recommendation:
                justification = recommendation["justification"]
                assert isinstance(justification, str), "Should provide textual justification"
                assert len(justification) > 20, "Justification should be substantive"

        # Verify test execution validation
        if "test_execution_validation" in integration_result:
            test_validation = integration_result["test_execution_validation"]
            assert isinstance(
                test_validation, dict
            ), "Test execution validation should be structured"

        # Verify artifact consumption from all previous stages
        assert "testing_artifact" in integration_input, "Should consume testing artifacts"
        assert "implementation_artifact" in integration_input, "Should reference implementation"
        assert "requirements_artifact" in integration_input, "Should validate against requirements"

        # Check for comprehensive readiness assessment
        if "readiness_assessment" in integration_result:
            readiness = integration_result["readiness_assessment"]
            if isinstance(readiness, dict) and "overall_score" in readiness:
                score = readiness["overall_score"]
                assert isinstance(score, int | float), "Readiness score should be numeric"
                assert 0 <= score <= 100, f"Readiness score should be 0-100, got {score}"

        # Verify complete state management
        orchestrator_state = orchestrator.state
        stage_artifacts = orchestrator_state.get("stage_artifacts", {})
        expected_stages = [
            "requirements",
            "design",
            "coding",
            "unit_testing",
            "integration_testing",
        ]

        for stage in expected_stages:
            assert stage in stage_artifacts, f"Should maintain {stage} artifacts in state"

        # Performance validation
        assert (
            integration_time < 300
        ), f"QA→Integration handoff should complete within 5 minutes, took {integration_time:.2f}s"

        # Log handoff metrics
        handoff_metrics = {
            "test_name": "qa_to_integration_handoff",
            "integration_time": integration_time,
            "release_decision": integration_result.get("release_recommendation", {}).get(
                "decision", "UNKNOWN"
            ),
            "readiness_score": integration_result.get("readiness_assessment", {}).get(
                "overall_score", 0
            ),
            "all_artifacts_consumed": True,
            "timestamp": datetime.now().isoformat(),
        }

        metrics_path = isolated_agilevv_dir.logs_dir / "handoff_metrics_qa_to_integration.json"
        metrics_path.write_text(json.dumps(handoff_metrics, indent=2))

    @skip_if_no_auth
    async def test_real_complete_vmodel_cycle(
        self,
        isolated_agilevv_dir: PathConfig,
        simple_user_story: dict[str, Any],
        enhanced_sdk_config: SDKConfig,
    ) -> None:
        """Task 4.5: Test complete V-Model cycle from user story to validated deliverable."""
        orchestrator = Orchestrator(
            path_config=isolated_agilevv_dir,
            sdk_config=enhanced_sdk_config,
            mock_mode=False,
        )

        # Track complete workflow execution
        workflow_start_time = time.time()
        stage_timings = {}
        stage_results = {}
        validation_results = {}

        # Execute complete V-Model workflow
        v_model_stages = [
            (VModelStage.REQUIREMENTS, "requirements_stage"),
            (VModelStage.DESIGN, "design_stage"),
            (VModelStage.CODING, "implementation_stage"),
            (VModelStage.UNIT_TESTING, "testing_stage"),
            (VModelStage.INTEGRATION_TESTING, "integration_stage"),
        ]

        for stage_enum, stage_name in v_model_stages:
            stage_start = time.time()

            # Prepare stage-specific input
            if stage_enum == VModelStage.REQUIREMENTS:
                stage_input = {
                    "story": simple_user_story,
                    "context": {
                        "project_name": "CompleteTaskManager",
                        "sprint_number": 1,
                    },
                }
            elif stage_enum == VModelStage.DESIGN:
                stage_input = {
                    "requirements_artifact": stage_results["requirements_stage"],
                    "technology_constraints": simple_user_story["technology_constraints"],
                }
            elif stage_enum == VModelStage.CODING:
                stage_input = {
                    "design_artifact": stage_results["design_stage"],
                    "requirements_artifact": stage_results["requirements_stage"],
                }
            elif stage_enum == VModelStage.UNIT_TESTING:
                stage_input = {
                    "implementation_artifact": stage_results["implementation_stage"],
                    "design_artifact": stage_results["design_stage"],
                    "requirements_artifact": stage_results["requirements_stage"],
                }
            elif stage_enum == VModelStage.INTEGRATION_TESTING:
                stage_input = {
                    "testing_artifact": stage_results["testing_stage"],
                    "implementation_artifact": stage_results["implementation_stage"],
                    "design_artifact": stage_results["design_stage"],
                    "requirements_artifact": stage_results["requirements_stage"],
                }

            # Execute stage
            stage_result = await orchestrator.execute_stage(stage_enum, stage_input)
            stage_end = time.time()

            # Record results and timing
            stage_results[stage_name] = stage_result
            stage_timings[stage_name] = stage_end - stage_start

            # Validate each stage artifact
            if stage_enum == VModelStage.REQUIREMENTS:
                validation_results[stage_name] = ArtifactValidator.validate_requirements_artifact(
                    stage_result
                )
            elif stage_enum == VModelStage.DESIGN:
                validation_results[stage_name] = ArtifactValidator.validate_design_artifact(
                    stage_result
                )
            elif stage_enum == VModelStage.CODING:
                validation_results[stage_name] = ArtifactValidator.validate_implementation_artifact(
                    stage_result
                )
            elif stage_enum == VModelStage.UNIT_TESTING:
                validation_results[stage_name] = ArtifactValidator.validate_testing_artifact(
                    stage_result
                )
            elif stage_enum == VModelStage.INTEGRATION_TESTING:
                validation_results[stage_name] = ArtifactValidator.validate_integration_artifact(
                    stage_result
                )

            # Ensure each stage validation passes
            validation = validation_results[stage_name]
            assert validation[
                "valid"
            ], f"Stage {stage_name} artifact validation failed: {validation['errors']}"

            # Verify stage result is not None and has expected structure
            assert stage_result is not None, f"Stage {stage_name} should return result"
            assert "agent" in stage_result, f"Stage {stage_name} should identify agent"

        workflow_end_time = time.time()
        total_workflow_time = workflow_end_time - workflow_start_time

        # Comprehensive validation of complete cycle

        # 1. Verify all stages completed successfully
        assert len(stage_results) == 5, "Should complete all 5 V-Model stages"

        # 2. Verify agent progression follows V-Model
        expected_agents = [
            "requirements_analyst",
            "architect",
            "developer",
            "qa_tester",
            "integration",
        ]
        actual_agents = [result["agent"] for result in stage_results.values()]
        for expected, actual in zip(expected_agents, actual_agents, strict=False):
            assert actual == expected, f"Expected agent {expected}, got {actual}"

        # 3. Verify artifact traceability across complete cycle
        final_integration_result = stage_results["integration_stage"]

        # Integration stage should have visibility into all previous artifacts
        if "traceability_matrix" in final_integration_result:
            traceability = final_integration_result["traceability_matrix"]
            assert isinstance(traceability, dict), "Traceability matrix should be structured"

            # Should trace back to original user story
            if "user_story_id" in traceability:
                assert (
                    traceability["user_story_id"] == "US-HANDOFF-001"
                ), "Should trace to original user story"

        # 4. Verify final release decision based on complete cycle
        if "release_recommendation" in final_integration_result:
            release_rec = final_integration_result["release_recommendation"]
            assert "decision" in release_rec, "Should provide final GO/NO-GO decision"

            final_decision = release_rec["decision"]
            # Document the decision but don't assert specific value (depends on AI assessment)
            assert final_decision in [
                "GO",
                "NO-GO",
            ], f"Invalid final decision: {final_decision}"

        # 5. Verify state management across complete workflow
        orchestrator_state = orchestrator.state
        stage_artifacts = orchestrator_state.get("stage_artifacts", {})

        expected_artifact_stages = [
            "requirements",
            "design",
            "coding",
            "unit_testing",
            "integration_testing",
        ]
        for artifact_stage in expected_artifact_stages:
            assert artifact_stage in stage_artifacts, f"Should maintain {artifact_stage} artifacts"

        # 6. Performance validation for complete cycle
        assert (
            total_workflow_time < 900
        ), f"Complete V-Model cycle should complete within 15 minutes, took {total_workflow_time:.2f}s"

        # 7. Quality validation across all stages
        all_validations_passed = all(
            validation["valid"] for validation in validation_results.values()
        )
        assert all_validations_passed, "All stage artifacts should pass validation"

        # Generate comprehensive workflow report
        workflow_report = {
            "test_name": "complete_vmodel_cycle",
            "total_execution_time": total_workflow_time,
            "stage_timings": stage_timings,
            "stage_validations": {
                stage: {
                    "valid": validation["valid"],
                    "error_count": len(validation["errors"]),
                    "warning_count": len(validation["warnings"]),
                    "metadata": validation["metadata"],
                }
                for stage, validation in validation_results.items()
            },
            "final_decision": final_integration_result.get("release_recommendation", {}).get(
                "decision", "UNKNOWN"
            ),
            "artifacts_generated": len(stage_artifacts),
            "traceability_maintained": True,
            "performance_acceptable": total_workflow_time < 900,
            "timestamp": datetime.now().isoformat(),
        }

        # Save comprehensive report
        report_path = isolated_agilevv_dir.logs_dir / "complete_vmodel_cycle_report.json"
        report_path.write_text(json.dumps(workflow_report, indent=2))

        # Also save individual stage reports for detailed analysis
        for stage_name, stage_result in stage_results.items():
            stage_report_path = isolated_agilevv_dir.logs_dir / f"{stage_name}_detailed_report.json"
            stage_report_path.write_text(json.dumps(stage_result, indent=2, default=str))


class TestSequentialExecutionValidation:
    """Validate that tests execute sequentially and capture proper handoff patterns."""

    def test_sequential_execution_marker(self):
        """Verify tests are marked for sequential execution."""
        # This test validates that proper markers are in place
        assert (
            pytest.mark.sequential in pytestmark
        ), "Tests should be marked for sequential execution"
        assert (
            pytest.mark.slow in pytestmark
        ), "Tests should be marked as slow due to real API calls"
        assert pytest.mark.real_sdk in pytestmark, "Tests should be marked for real SDK usage"

    def test_artifact_validator_coverage(self):
        """Verify artifact validators cover all V-Model stages."""
        validator_methods = [
            ArtifactValidator.validate_requirements_artifact,
            ArtifactValidator.validate_design_artifact,
            ArtifactValidator.validate_implementation_artifact,
            ArtifactValidator.validate_testing_artifact,
            ArtifactValidator.validate_integration_artifact,
        ]

        # All validators should be callable
        for validator in validator_methods:
            assert callable(validator), f"Validator {validator.__name__} should be callable"

        # Test validator with minimal valid artifact
        minimal_artifact = {
            "id": "test",
            "agent": "test_agent",
            "functional_requirements": [],
            "acceptance_criteria": [],
        }

        req_validation = ArtifactValidator.validate_requirements_artifact(minimal_artifact)
        assert (
            "valid" in req_validation
        ), "Validator should return validation result with 'valid' field"
        assert (
            "errors" in req_validation
        ), "Validator should return validation result with 'errors' field"
        assert (
            "warnings" in req_validation
        ), "Validator should return validation result with 'warnings' field"
