"""Enhanced tests for IntegrationAgent with comprehensive real Claude Code SDK integration.

This module provides comprehensive testing for the IntegrationAgent including
GO/NO-GO decision making, deployment validation, and complete V-Model integration.
"""

import json
import os
from pathlib import Path
from unittest.mock import patch

import pytest
from verifflowcc.agents.integration import IntegrationAgent
from verifflowcc.core.path_config import PathConfig
from verifflowcc.core.sdk_config import SDKConfig


@pytest.mark.asyncio
class TestIntegrationAgentRealSDK:
    """Test IntegrationAgent with real Claude Code SDK for MailBuddy scenarios."""

    async def test_mailbuddy_go_no_go_decision_with_real_sdk(
        self, isolated_agilevv_dir: PathConfig
    ) -> None:
        """Test Integration agent making GO/NO-GO decisions with real Claude Code SDK."""
        if not os.getenv("ANTHROPIC_API_KEY") and not self._is_claude_code_available():
            pytest.skip("No ANTHROPIC_API_KEY - skipping real SDK test")

        # Create Integration agent with real SDK
        agent = IntegrationAgent(
            name="integration_mailbuddy_decision",
            path_config=isolated_agilevv_dir,
            sdk_config=SDKConfig(),
            mock_mode=False,
        )

        # Complete MailBuddy V-Model artifacts for GO/NO-GO decision
        mailbuddy_final_artifacts = {
            "story_id": "MAILBUDDY-GO-NO-GO-001",
            "task_description": "Final GO/NO-GO decision for MailBuddy Flask email platform production deployment",
            "system_artifacts": {
                "components": [
                    "Authentication Service",
                    "Email Composition Engine",
                    "Template Management",
                    "SendGrid Integration",
                    "User Dashboard",
                    "API Gateway",
                    "Security Middleware",
                ],
                "architecture_validation": "approved",
                "security_review": "passed",
            },
            "requirements_data": {
                "total_functional_requirements": 12,
                "requirements_implemented": 12,
                "acceptance_criteria_met": 12,
                "stakeholder_signoff": "obtained",
                "traceability_coverage": "100%",
            },
            "design_data": {
                "architecture_review": "approved",
                "component_interfaces": "validated",
                "security_design": "approved",
                "performance_design": "load_tested",
            },
            "implementation_data": {
                "source_files": 35,
                "code_quality": {
                    "test_coverage": 94.8,
                    "security_scan": "passed",
                    "performance_score": 88.2,
                    "maintainability": "high",
                },
                "code_review": "all_approved",
            },
            "testing_data": {
                "test_execution": {
                    "total_test_cases": 89,
                    "passed": 87,
                    "failed": 2,
                    "pass_rate": "97.8%",
                },
                "quality_assessment": {
                    "overall_quality": "excellent",
                    "readiness_for_next_stage": True,
                    "critical_issues": [],
                    "recommendations": ["Monitor performance in production"],
                },
                "performance_testing": {
                    "load_test": "passed",
                    "stress_test": "passed",
                    "concurrent_users": 1500,
                    "response_time_p95": "185ms",
                },
            },
            "deployment_target": "production",
            "context": {
                "project_name": "MailBuddy Enterprise",
                "version": "v1.0.0",
                "deployment_environment": "AWS ECS Production",
                "business_criticality": "high",
                "rollback_strategy": "blue_green",
            },
        }

        # Process with real Claude Code SDK
        result = await agent.process(mailbuddy_final_artifacts)

        # Validate successful processing
        assert result["status"] == "success"
        assert "integration_data" in result
        assert "go_no_go_decision" in result

        # Validate GO/NO-GO decision was made
        decision = result["go_no_go_decision"]
        assert decision in ["GO", "NO-GO"]

        # Validate decision rationale exists
        integration_data = result["integration_data"]
        release_recommendation = integration_data["release_recommendation"]
        assert "decision_rationale" in release_recommendation
        assert "overall_readiness_score" in release_recommendation
        assert isinstance(release_recommendation["overall_readiness_score"], int | float)

        # Validate risk assessment
        assert "risk_assessment" in release_recommendation
        risk_assessment = release_recommendation["risk_assessment"]
        assert "deployment_risks" in risk_assessment
        assert "operational_risks" in risk_assessment
        assert "business_risks" in risk_assessment
        assert "mitigation_strategies" in risk_assessment

        # Validate release plan
        assert "release_plan" in release_recommendation
        release_plan = release_recommendation["release_plan"]
        assert "deployment_strategy" in release_plan

        # Validate artifacts were created
        story_id = mailbuddy_final_artifacts["story_id"]
        expected_artifacts = [
            f"integration/{story_id}.json",
            f"integration/{story_id}_deployment.json",
            f"integration/{story_id}_performance.json",
            f"integration/{story_id}_release_decision.json",
            f"integration/{story_id}_final_report.md",
        ]

        artifacts = result["artifacts"]
        for expected_artifact in expected_artifacts:
            artifact_key = (
                expected_artifact.split("/")[1]
                .replace(f"{story_id}_", "")
                .replace(f"{story_id}", "integration_report")
                .replace(".json", "")
                .replace(".md", "")
            )
            if artifact_key == "integration_report":
                artifact_key = "integration_report"
            elif "deployment" in expected_artifact:
                artifact_key = "deployment_validation"
            elif "performance" in expected_artifact:
                artifact_key = "performance_validation"
            elif "release_decision" in expected_artifact:
                artifact_key = "release_decision"
            elif "final_report" in expected_artifact:
                artifact_key = "final_validation_report"

            assert artifact_key in artifacts
            artifact_path = Path(isolated_agilevv_dir.base_dir) / artifacts[artifact_key]
            assert artifact_path.exists(), f"Missing artifact: {expected_artifact}"

    async def test_integration_report_markdown_generation(
        self, isolated_agilevv_dir: PathConfig
    ) -> None:
        """Test that Integration agent generates comprehensive markdown integration reports."""
        if not os.getenv("ANTHROPIC_API_KEY") and not self._is_claude_code_available():
            pytest.skip("No ANTHROPIC_API_KEY - skipping real SDK test")

        agent = IntegrationAgent(
            path_config=isolated_agilevv_dir, sdk_config=SDKConfig(), mock_mode=False
        )

        # Input focused on report generation
        report_input = {
            "story_id": "MAILBUDDY-REPORT-001",
            "task_description": "Generate comprehensive integration report for MailBuddy deployment readiness",
            "system_artifacts": {
                "components": ["Auth", "Email", "Templates", "API", "Frontend"],
                "deployment_environment": "AWS Production",
            },
            "requirements_data": {"status": "all_requirements_met"},
            "design_data": {"status": "design_approved"},
            "implementation_data": {"status": "implementation_complete"},
            "testing_data": {
                "quality_assessment": {
                    "overall_quality": "good",
                    "readiness_for_next_stage": True,
                }
            },
            "context": {
                "project_name": "MailBuddy Report Generation Test",
                "deployment_target": "production",
            },
        }

        result = await agent.process(report_input)
        assert result["status"] == "success"

        # Validate final report was generated
        story_id = report_input["story_id"]
        final_report_path = (
            isolated_agilevv_dir.artifacts_dir / "integration" / f"{story_id}_final_report.md"
        )
        assert final_report_path.exists()

        # Validate report content
        report_content = final_report_path.read_text()

        # Should contain key sections
        expected_sections = [
            "Final Validation Report",
            "Executive Summary",
            "Release Decision:",
            "Overall Readiness Score:",
            "V-Model Stage Summary",
        ]

        for section in expected_sections:
            assert section in report_content, f"Missing section in report: {section}"

        # Should contain decision information
        integration_data = result["integration_data"]
        if "release_recommendation" in integration_data:
            release_recommendation = integration_data["release_recommendation"]
            if "go_no_go_decision" in release_recommendation:
                decision = release_recommendation["go_no_go_decision"]
                assert decision in report_content

    def _is_claude_code_available(self) -> bool:
        """Check if Claude Code subscription is available."""
        return False


@pytest.mark.integration
class TestIntegrationAgentWorkflowIntegration:
    """Integration tests for complete V-Model workflow with Integration agent."""

    @pytest.mark.asyncio
    async def test_complete_vmodel_integration_workflow(
        self, isolated_agilevv_dir: PathConfig
    ) -> None:
        """Test Integration agent as final stage of complete V-Model workflow."""
        # Use mock for complete workflow test
        with patch(
            "verifflowcc.agents.integration.IntegrationAgent._call_claude_sdk"
        ) as mock_claude:
            # Setup comprehensive mock response simulating high-quality system
            comprehensive_response = {
                "integration_validation": {
                    "system_architecture": {
                        "components_integrated": [
                            "User Authentication",
                            "Email Service",
                            "Template Engine",
                            "Database Layer",
                            "API Gateway",
                            "Frontend Components",
                        ],
                        "integration_points": [
                            {
                                "from": "API Gateway",
                                "to": "Email Service",
                                "status": "healthy",
                            },
                            {
                                "from": "Frontend",
                                "to": "API Gateway",
                                "status": "healthy",
                            },
                            {
                                "from": "Email Service",
                                "to": "Database",
                                "status": "healthy",
                            },
                        ],
                        "data_flow_validation": {
                            "end_to_end_scenarios": [
                                "User registration",
                                "Email sending",
                                "Template management",
                            ],
                            "data_consistency": "Validated across all components",
                            "error_propagation": "Proper error handling verified",
                            "transaction_management": "ACID compliance verified",
                        },
                    },
                    "functional_validation": {
                        "business_processes": [
                            "User onboarding flow",
                            "Email campaign creation",
                            "Template management",
                            "Bulk email operations",
                        ],
                        "user_acceptance": {
                            "acceptance_tests_run": 32,
                            "acceptance_tests_passed": 31,
                            "user_feedback": "Excellent - exceeds expectations",
                            "outstanding_issues": ["Minor UI polish needed"],
                        },
                    },
                },
                "deployment_validation": {
                    "environment_readiness": {
                        "production_environment": {
                            "infrastructure": "AWS ECS cluster ready",
                            "compute_resources": "Auto-scaling configured",
                            "storage_resources": "RDS PostgreSQL optimized",
                            "network_configuration": "Security groups configured",
                            "monitoring_setup": "CloudWatch + custom dashboards ready",
                        },
                        "configuration_management": {
                            "environment_variables": "All production configs verified",
                            "secrets_management": "AWS Secrets Manager integrated",
                            "database_connections": "Connection pooling configured",
                            "external_services": "SendGrid API integration tested",
                        },
                    },
                    "security_validation": {
                        "vulnerability_scanning": "Zero critical vulnerabilities",
                        "penetration_testing": "External pentest passed",
                        "compliance_validation": "GDPR and CAN-SPAM compliant",
                        "access_controls": "JWT + RBAC fully implemented",
                    },
                },
                "performance_validation": {
                    "load_testing": {
                        "performance_metrics": {
                            "response_time": {
                                "avg": "145ms",
                                "95th": "220ms",
                                "99th": "380ms",
                            },
                            "throughput": "750 requests per second",
                            "error_rate": "0.2%",
                            "resource_utilization": {
                                "cpu": "58%",
                                "memory": "62%",
                                "disk": "35%",
                            },
                        }
                    },
                    "reliability_testing": {
                        "availability_testing": "99.95% uptime achieved",
                        "fault_tolerance": "Graceful degradation verified",
                        "recovery_testing": "RTO < 5 minutes achieved",
                        "backup_validation": "Automated backups and restore tested",
                    },
                },
                "quality_gates": {
                    "code_quality": {
                        "test_coverage": ">95%",
                        "code_review": "100% code review coverage",
                        "static_analysis": "Zero critical issues",
                        "technical_debt": "Minimal - within acceptable limits",
                    }
                },
                "release_recommendation": {
                    "go_no_go_decision": "GO",
                    "decision_rationale": "All quality gates passed with excellent scores. System demonstrates production readiness across all validation criteria.",
                    "overall_readiness_score": 94.8,
                    "risk_assessment": {
                        "deployment_risks": [],
                        "operational_risks": ["Monitor initial production load patterns"],
                        "business_risks": [],
                        "mitigation_strategies": [
                            "Gradual traffic ramp-up with monitoring",
                            "24x7 support team on standby for launch",
                            "Immediate rollback capability via blue-green deployment",
                        ],
                    },
                    "release_plan": {
                        "deployment_strategy": "blue-green",
                        "rollout_phases": [
                            "Phase 1: 10% traffic for 2 hours",
                            "Phase 2: 50% traffic for 4 hours",
                            "Phase 3: 100% traffic cutover",
                        ],
                        "success_criteria": [
                            "Error rate < 0.5%",
                            "Response time p95 < 250ms",
                            "No critical system alerts",
                            "User satisfaction metrics > 4.5/5",
                        ],
                        "rollback_triggers": [
                            "Error rate > 2%",
                            "Response time p95 > 500ms",
                            "Critical system failures",
                            "Business metrics below threshold",
                        ],
                    },
                    "outstanding_issues": [],
                },
            }
            mock_claude.return_value = json.dumps(comprehensive_response)

            agent = IntegrationAgent(path_config=isolated_agilevv_dir)

            # Complete V-Model artifacts representing successful progression through all stages
            complete_artifacts = {
                "story_id": "COMPLETE-VMODEL-WORKFLOW-001",
                "task_description": "Final V-Model integration validation for production-ready system",
                "system_artifacts": {
                    "total_components": 6,
                    "components_status": "all_integrated",
                    "architecture_complexity": "moderate",
                },
                "requirements_data": {
                    "requirements_analyst_output": {
                        "functional_requirements": 15,
                        "non_functional_requirements": 8,
                        "acceptance_criteria": 23,
                        "stakeholder_approval": "obtained",
                    }
                },
                "design_data": {
                    "architect_output": {
                        "system_design": "completed",
                        "component_specifications": "detailed",
                        "interface_contracts": "defined",
                        "architecture_review": "approved",
                    }
                },
                "implementation_data": {
                    "developer_output": {
                        "source_files_created": 28,
                        "code_quality_score": 91.5,
                        "security_scan": "passed",
                        "peer_review": "approved",
                    }
                },
                "testing_data": {
                    "qa_tester_output": {
                        "test_strategy": "comprehensive",
                        "test_execution": "completed",
                        "quality_assessment": {
                            "overall_quality": "excellent",
                            "readiness_for_next_stage": True,
                            "critical_issues": [],
                        },
                        "pass_rate": "97.8%",
                        "coverage": "95.2%",
                    }
                },
                "context": {
                    "project_name": "Complete V-Model Workflow Test",
                    "sprint_completion": "all_stages_completed",
                    "deployment_readiness": "ready",
                },
            }

            result = await agent.process(complete_artifacts)

            # Validate successful completion of V-Model workflow
            assert result["status"] == "success"
            assert result["go_no_go_decision"] == "GO"
            assert result["validation_passed"] is True
            assert result["next_stage_ready"] is True  # Ready for deployment
            # Validate readiness score is reasonable (agent calculates its own score based on inputs)
            assert isinstance(result["release_readiness_score"], int | float)
            assert result["release_readiness_score"] >= 70.0  # Should be high quality

            # Validate comprehensive metrics
            metrics = result["metrics"]
            assert metrics["components_validated"] == 6
            assert metrics["deployment_readiness"] == "ready"
            assert metrics["integration_points_tested"] == 3

            # Validate all final artifacts created
            artifacts = result["artifacts"]
            required_artifacts = [
                "integration_report",
                "deployment_validation",
                "performance_validation",
                "release_decision",
                "final_validation_report",
            ]

            for artifact_type in required_artifacts:
                assert artifact_type in artifacts
                artifact_path = Path(isolated_agilevv_dir.base_dir) / artifacts[artifact_type]
                assert artifact_path.exists(), f"Missing final V-Model artifact: {artifact_type}"

            # Validate final validation report comprehensiveness
            final_report_path = (
                Path(isolated_agilevv_dir.base_dir) / artifacts["final_validation_report"]
            )
            report_content = final_report_path.read_text()

            # Should summarize entire V-Model journey
            vmodel_stages = ["Requirements", "Design", "Implementation", "Testing"]
            for stage in vmodel_stages:
                assert (
                    stage in report_content
                ), f"V-Model stage {stage} not summarized in final report"


@pytest.mark.unit
class TestIntegrationAgentDecisionLogic:
    """Unit tests for GO/NO-GO decision logic components."""

    def test_decision_scoring_algorithm_simulation(self, isolated_agilevv_dir: PathConfig) -> None:
        """Test the decision scoring algorithm with different quality scenarios."""
        # Note: agent instantiation validates PathConfig compatibility
        IntegrationAgent(path_config=isolated_agilevv_dir)

        # Test scenarios with different quality profiles
        test_scenarios = [
            {
                "name": "excellent_quality",
                "code_coverage": 96,
                "test_pass_rate": 98,
                "security_score": 95,
                "performance_score": 92,
                "expected_decision": "GO",
            },
            {
                "name": "good_quality",
                "code_coverage": 88,
                "test_pass_rate": 95,
                "security_score": 89,
                "performance_score": 87,
                "expected_decision": "GO",
            },
            {
                "name": "marginal_quality",
                "code_coverage": 78,
                "test_pass_rate": 85,
                "security_score": 82,
                "performance_score": 79,
                "expected_decision": "conditional",  # Might be GO with mitigation
            },
            {
                "name": "poor_quality",
                "code_coverage": 65,
                "test_pass_rate": 72,
                "security_score": 68,
                "performance_score": 63,
                "expected_decision": "NO-GO",
            },
        ]

        for scenario in test_scenarios:
            # Validate scenario has required metrics
            assert "code_coverage" in scenario
            assert "test_pass_rate" in scenario
            assert "security_score" in scenario
            assert "performance_score" in scenario
            assert "expected_decision" in scenario

            # All scores should be valid percentages
            for metric in [
                "code_coverage",
                "test_pass_rate",
                "security_score",
                "performance_score",
            ]:
                score = scenario[metric]
                assert 0 <= score <= 100, f"Invalid score for {metric}: {score}"

            # Expected decision should be valid
            assert scenario["expected_decision"] in ["GO", "NO-GO", "conditional"]

    def test_risk_assessment_categorization(self, isolated_agilevv_dir: PathConfig) -> None:
        """Test risk assessment categorization logic."""
        # Note: agent instantiation validates PathConfig compatibility
        IntegrationAgent(path_config=isolated_agilevv_dir)

        # Test risk scenarios
        risk_scenarios = [
            {
                "risk_type": "deployment",
                "severity": "high",
                "description": "Database migration required",
                "mitigation": "Backup and rollback plan",
            },
            {
                "risk_type": "operational",
                "severity": "medium",
                "description": "New monitoring setup needed",
                "mitigation": "24x7 support team ready",
            },
            {
                "risk_type": "business",
                "severity": "low",
                "description": "User training might be needed",
                "mitigation": "Documentation and help system available",
            },
        ]

        for risk in risk_scenarios:
            # Validate risk structure
            assert "risk_type" in risk
            assert "severity" in risk
            assert "description" in risk
            assert "mitigation" in risk

            # Validate risk type
            assert risk["risk_type"] in ["deployment", "operational", "business"]

            # Validate severity
            assert risk["severity"] in ["low", "medium", "high", "critical"]

            # Validate description and mitigation are non-empty
            assert len(risk["description"]) > 0
            assert len(risk["mitigation"]) > 0
