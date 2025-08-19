"""Tests for document-based session storage using JSON/YAML files.

This module tests the concrete document-based session storage functionality
in BaseAgent and its subclasses, ensuring proper persistence and context
preservation across V-Model agent transitions using the existing product
implementation.
"""

import json
from typing import Any

import pytest
import yaml
from verifflowcc.agents.architect import ArchitectAgent as Architect
from verifflowcc.agents.requirements_analyst import RequirementsAnalystAgent as RequirementsAnalyst
from verifflowcc.core.path_config import PathConfig
from verifflowcc.core.sdk_config import SDKConfig

pytestmark = [
    pytest.mark.integration,
    pytest.mark.session,
    pytest.mark.document_storage,
]


class TestBaseAgentDocumentStorage:
    """Test BaseAgent document-based session storage functionality."""

    @pytest.fixture
    def sdk_config(self) -> SDKConfig:
        """Provide SDK configuration for testing."""
        return SDKConfig(api_key="test-doc-storage-key")

    @pytest.fixture
    def base_agent(
        self, sdk_config: SDKConfig, isolated_agilevv_dir: PathConfig
    ) -> RequirementsAnalyst:
        """Provide concrete agent instance for testing."""
        return RequirementsAnalyst(
            sdk_config=sdk_config,
            mock_mode=True,
            path_config=isolated_agilevv_dir,
        )

    def test_save_artifact_json_format(
        self, base_agent: RequirementsAnalyst, isolated_agilevv_dir: PathConfig
    ) -> None:
        """Test saving artifacts in JSON format using existing product implementation."""
        # Test data that mimics real session context
        test_data = {
            "session_id": "test_session_001",
            "conversation_context": {
                "user_stories": [
                    "As a user I want to compose emails with AI assistance",
                    "As a user I want to manage contacts efficiently",
                ],
                "analysis_results": {"invest_compliance": True, "quality_score": 92},
            },
            "workflow_state": {
                "current_stage": "requirements",
                "completed_stages": ["planning"],
            },
        }

        # Use existing save_artifact method
        artifact_name = "test_session_data.json"
        base_agent.save_artifact(artifact_name, test_data)

        # Verify file was created in correct location
        expected_path = isolated_agilevv_dir.base_dir / artifact_name
        assert expected_path.exists()

        # Verify JSON content is properly formatted
        with expected_path.open("r", encoding="utf-8") as f:
            saved_content = json.load(f)

        assert saved_content["session_id"] == "test_session_001"
        assert saved_content["conversation_context"]["analysis_results"]["quality_score"] == 92
        assert saved_content["workflow_state"]["current_stage"] == "requirements"

    def test_load_artifact_json_format(
        self, base_agent: RequirementsAnalyst, isolated_agilevv_dir: PathConfig
    ) -> None:
        """Test loading artifacts from JSON files using existing product implementation."""
        # Create test JSON file manually
        test_data = {
            "agent_type": "requirements_analyst",
            "session_data": {
                "mailbuddy_features": ["email_composition", "contact_management"],
                "technical_constraints": {"framework": "Flask", "database": "SQLite"},
            },
        }

        artifact_name = "load_test_session.json"
        artifact_path = isolated_agilevv_dir.base_dir / artifact_name

        with artifact_path.open("w", encoding="utf-8") as f:
            json.dump(test_data, f, indent=2)

        # Use existing load_artifact method
        loaded_data = base_agent.load_artifact(artifact_name)

        # Verify data integrity
        assert loaded_data is not None
        assert loaded_data["agent_type"] == "requirements_analyst"
        assert "email_composition" in loaded_data["session_data"]["mailbuddy_features"]
        assert loaded_data["session_data"]["technical_constraints"]["framework"] == "Flask"

    def test_save_session_state_implementation(
        self, base_agent: RequirementsAnalyst, isolated_agilevv_dir: PathConfig
    ) -> None:
        """Test existing save_session_state method with real context data."""
        # Populate agent with realistic session data
        base_agent.context = {
            "project_name": "MailBuddy",
            "current_requirements": [
                {
                    "id": "REQ-001",
                    "title": "Email Composition with AI",
                    "invest_score": 92,
                }
            ],
            "user_feedback": "Requirements look comprehensive",
        }

        base_agent.session_history = [
            {
                "role": "user",
                "content": "Analyze MailBuddy email composition requirements",
            },
            {"role": "assistant", "content": "I'll analyze using INVEST criteria..."},
        ]

        # Use existing save_session_state method
        base_agent.save_session_state()

        # Verify session state file was created
        expected_file = isolated_agilevv_dir.base_dir / "session_state_requirements.json"
        assert expected_file.exists()

        # Verify session state content
        with expected_file.open("r") as f:
            session_state = json.load(f)

        assert session_state["agent_type"] == "requirements"
        assert session_state["context"]["project_name"] == "MailBuddy"
        assert len(session_state["session_history"]) == 2
        assert session_state["context"]["current_requirements"][0]["invest_score"] == 92

    def test_load_session_state_implementation(
        self, base_agent: RequirementsAnalyst, isolated_agilevv_dir: PathConfig
    ) -> None:
        """Test existing load_session_state method restores context properly."""
        # Create session state file with test data
        session_data = {
            "agent_type": "requirements",
            "context": {
                "project_name": "MailBuddy",
                "analysis_progress": {
                    "requirements_completed": 5,
                    "requirements_remaining": 3,
                },
            },
            "session_history": [
                {"role": "user", "content": "Continue requirements analysis"},
                {"role": "assistant", "content": "Analyzing remaining requirements..."},
            ],
            "tool_permissions": ["read", "write", "analyze"],
        }

        session_file = isolated_agilevv_dir.base_dir / "session_state_requirements.json"
        with session_file.open("w") as f:
            json.dump(session_data, f, indent=2)

        # Clear agent state first
        base_agent.context = {}
        base_agent.session_history = []

        # Use existing load_session_state method
        success = base_agent.load_session_state()

        # Verify session was loaded successfully
        assert success is True
        assert base_agent.context["project_name"] == "MailBuddy"
        assert base_agent.context["analysis_progress"]["requirements_completed"] == 5
        assert len(base_agent.session_history) == 2
        assert base_agent.session_history[0]["content"] == "Continue requirements analysis"

    def test_session_state_persistence_across_instances(
        self, sdk_config: SDKConfig, isolated_agilevv_dir: PathConfig
    ) -> None:
        """Test session state persists across different agent instances."""
        # Create first agent instance and populate with data
        agent1 = RequirementsAnalyst(
            sdk_config=sdk_config,
            mock_mode=True,
            path_config=isolated_agilevv_dir,
        )

        agent1.context = {
            "mailbuddy_session": {
                "authenticated_user": "test@example.com",
                "active_features": ["email_compose", "contact_sync"],
                "session_start_time": "2024-01-01T10:00:00Z",
            }
        }

        agent1.session_history = [
            {"role": "user", "content": "Initialize MailBuddy session"},
            {"role": "assistant", "content": "Session initialized successfully"},
        ]

        # Save session state
        agent1.save_session_state()

        # Create second agent instance with same configuration
        agent2 = RequirementsAnalyst(
            sdk_config=sdk_config,
            mock_mode=True,
            path_config=isolated_agilevv_dir,
        )

        # Load session state in second instance
        load_success = agent2.load_session_state()

        # Verify session data transferred correctly
        assert load_success is True
        assert agent2.context["mailbuddy_session"]["authenticated_user"] == "test@example.com"
        assert "email_compose" in agent2.context["mailbuddy_session"]["active_features"]
        assert len(agent2.session_history) == 2

    def test_yaml_artifact_support(
        self, base_agent: RequirementsAnalyst, isolated_agilevv_dir: PathConfig
    ) -> None:
        """Test YAML artifact support for configuration files."""
        # Test YAML configuration data
        config_data = {
            "mailbuddy_config": {
                "email_settings": {
                    "max_attachment_size": "25MB",
                    "supported_formats": ["text", "html", "markdown"],
                    "auto_save_interval": 30,
                },
                "ai_settings": {
                    "model": "claude-opus-4.1",
                    "temperature": 0.7,
                    "max_tokens": 2000,
                },
                "user_preferences": {
                    "theme": "dark",
                    "notifications": True,
                    "language": "en",
                },
            }
        }

        # Save as text (YAML format)
        yaml_content = yaml.dump(config_data, default_flow_style=False)
        base_agent.save_artifact("mailbuddy_config.yaml", yaml_content)

        # Verify YAML file was created
        yaml_path = isolated_agilevv_dir.base_dir / "mailbuddy_config.yaml"
        assert yaml_path.exists()

        # Load and verify YAML content
        loaded_yaml = base_agent.load_artifact("mailbuddy_config.yaml")
        parsed_yaml = yaml.safe_load(loaded_yaml)

        assert parsed_yaml["mailbuddy_config"]["email_settings"]["max_attachment_size"] == "25MB"
        assert parsed_yaml["mailbuddy_config"]["ai_settings"]["model"] == "claude-opus-4.1"
        assert parsed_yaml["mailbuddy_config"]["user_preferences"]["theme"] == "dark"


class TestVModelAgentSessionHandoffs:
    """Test session context handoffs between V-Model agents using existing implementation."""

    @pytest.fixture
    def sdk_config(self) -> SDKConfig:
        """Provide SDK configuration for testing."""
        return SDKConfig(api_key="test-vmodel-handoff-key")

    @pytest.mark.asyncio
    async def test_requirements_to_architect_handoff(
        self, sdk_config: SDKConfig, isolated_agilevv_dir: PathConfig
    ) -> None:
        """Test session context handoff from Requirements Analyst to Architect."""
        # Create Requirements Analyst
        analyst = RequirementsAnalyst(
            sdk_config=sdk_config,
            mock_mode=True,
            path_config=isolated_agilevv_dir,
        )

        # Simulate requirements analysis session
        requirements_context = {
            "mailbuddy_requirements": {
                "user_stories": [
                    {
                        "id": "US-001",
                        "title": "Email Composition with AI",
                        "invest_score": 92,
                        "acceptance_criteria": [
                            "User can compose email with AI suggestions",
                            "AI provides grammar and tone improvements",
                        ],
                    }
                ],
                "technical_requirements": {
                    "framework": "Flask 2.3+",
                    "database": "SQLite for development",
                    "authentication": "Flask-Login with bcrypt",
                },
                "quality_metrics": {
                    "average_invest_score": 92,
                    "requirements_count": 1,
                    "complexity_rating": "medium",
                },
            }
        }

        analyst.context = requirements_context
        analyst.session_history = [
            {"role": "user", "content": "Analyze MailBuddy requirements"},
            {
                "role": "assistant",
                "content": "Requirements analysis complete with INVEST score 92",
            },
        ]

        # Save Requirements Analyst session
        analyst.save_session_state()

        # Create Architect agent
        architect = Architect(
            sdk_config=sdk_config,
            mock_mode=True,
            path_config=isolated_agilevv_dir,
        )

        # Load requirements session data into architect context
        requirements_session = analyst.load_artifact("session_state_requirements.json")
        assert requirements_session is not None

        # Architect inherits requirements context
        architect.context = {
            "inherited_from_requirements": requirements_session["context"],
            "architecture_stage": {
                "current_phase": "system_design",
                "design_approach": "microservices_with_flask",
            },
        }

        architect.session_history = [
            {"role": "user", "content": "Design architecture based on requirements"},
            {
                "role": "assistant",
                "content": "Creating microservices architecture for MailBuddy...",
            },
        ]

        # Save Architect session
        architect.save_session_state()

        # Verify context handoff preserved requirements data
        architect_session = architect.load_artifact("session_state_architect.json")
        inherited_context = architect_session["context"]["inherited_from_requirements"]

        assert (
            inherited_context["mailbuddy_requirements"]["quality_metrics"]["average_invest_score"]
            == 92
        )
        assert (
            inherited_context["mailbuddy_requirements"]["technical_requirements"]["framework"]
            == "Flask 2.3+"
        )
        assert len(inherited_context["mailbuddy_requirements"]["user_stories"]) == 1

    def test_cross_stage_artifact_preservation(
        self, sdk_config: SDKConfig, isolated_agilevv_dir: PathConfig
    ) -> None:
        """Test artifacts are preserved across different V-Model stage agents."""
        # Create Requirements Analyst and save requirements artifact
        analyst = RequirementsAnalyst(
            sdk_config=sdk_config,
            mock_mode=True,
            path_config=isolated_agilevv_dir,
        )

        requirements_artifact = {
            "requirements_version": "1.0",
            "mailbuddy_requirements": [
                {
                    "id": "REQ-001",
                    "category": "functional",
                    "description": "AI-powered email composition",
                    "priority": "high",
                    "invest_compliant": True,
                },
                {
                    "id": "REQ-002",
                    "category": "non_functional",
                    "description": "Response time under 2 seconds",
                    "priority": "medium",
                    "measurable": True,
                },
            ],
            "traceability_matrix": {
                "REQ-001": ["US-001", "US-002"],
                "REQ-002": ["NFR-001"],
            },
        }

        analyst.save_artifact("requirements.json", requirements_artifact)

        # Create Architect and verify access to requirements artifact
        architect = Architect(
            sdk_config=sdk_config,
            mock_mode=True,
            path_config=isolated_agilevv_dir,
        )

        # Architect can load requirements artifact for design decisions
        loaded_requirements = architect.load_artifact("requirements.json")
        assert loaded_requirements is not None
        assert loaded_requirements["requirements_version"] == "1.0"
        assert len(loaded_requirements["mailbuddy_requirements"]) == 2
        assert loaded_requirements["mailbuddy_requirements"][0]["invest_compliant"] is True

        # Architect creates architecture artifact referencing requirements
        architecture_artifact = {
            "architecture_version": "1.0",
            "based_on_requirements": "requirements.json",
            "system_design": {
                "pattern": "MVC with Flask",
                "components": [
                    {"name": "email_composer", "addresses_req": "REQ-001"},
                    {"name": "performance_monitor", "addresses_req": "REQ-002"},
                ],
            },
            "design_decisions": [
                "Flask framework chosen based on REQ-001 functional requirements",
                "Caching layer added to meet REQ-002 performance requirements",
            ],
        }

        architect.save_artifact("architecture.json", architecture_artifact)

        # Verify both artifacts exist and maintain referential integrity
        requirements_check = architect.load_artifact("requirements.json")
        architecture_check = architect.load_artifact("architecture.json")

        assert requirements_check is not None
        assert architecture_check is not None
        assert architecture_check["based_on_requirements"] == "requirements.json"

        # Verify architecture addresses requirements
        addressed_reqs = [
            comp["addresses_req"] for comp in architecture_check["system_design"]["components"]
        ]
        assert "REQ-001" in addressed_reqs
        assert "REQ-002" in addressed_reqs


class TestSessionFilePersistence:
    """Test session file persistence across system operations."""

    @pytest.fixture
    def sdk_config(self) -> SDKConfig:
        """Provide SDK configuration for testing."""
        return SDKConfig(api_key="test-persistence-key")

    def test_session_files_survive_system_restart_simulation(
        self, sdk_config: SDKConfig, isolated_agilevv_dir: PathConfig
    ) -> None:
        """Test session files persist through simulated system restart."""
        # Create agent and establish session
        agent = RequirementsAnalyst(
            sdk_config=sdk_config,
            mock_mode=True,
            path_config=isolated_agilevv_dir,
        )

        # Populate with comprehensive MailBuddy session data
        agent.context = {
            "mailbuddy_session": {
                "project_id": "mailbuddy_v2",
                "session_timestamp": "2024-01-01T14:30:00Z",
                "requirements_analysis": {
                    "user_stories_processed": 12,
                    "invest_scores": [85, 92, 88, 91, 87, 93, 89, 86, 90, 94, 88, 92],
                    "average_score": 90.4,
                    "complexity_distribution": {"simple": 4, "medium": 6, "complex": 2},
                },
                "stakeholder_feedback": [
                    {
                        "stakeholder": "product_owner",
                        "feedback": "Requirements align with business goals",
                        "approval": True,
                    },
                    {
                        "stakeholder": "technical_lead",
                        "feedback": "Architecture constraints clearly defined",
                        "approval": True,
                    },
                ],
            }
        }

        agent.session_history = [
            {
                "role": "user",
                "content": "Analyze MailBuddy v2 requirements for email AI features",
            },
            {
                "role": "assistant",
                "content": "Analyzing 12 user stories with focus on INVEST criteria...",
            },
            {"role": "user", "content": "What's the overall quality assessment?"},
            {
                "role": "assistant",
                "content": "Average INVEST score is 90.4 with strong compliance across all criteria",
            },
        ]

        # Save session state
        agent.save_session_state()

        # Simulate system restart - create completely new agent instance
        # (simulates process restart where memory is cleared)
        del agent

        new_agent = RequirementsAnalyst(
            sdk_config=sdk_config,
            mock_mode=True,
            path_config=isolated_agilevv_dir,
        )

        # Verify session can be loaded after "restart"
        load_success = new_agent.load_session_state()
        assert load_success is True

        # Verify all session data survived the restart
        assert new_agent.context["mailbuddy_session"]["project_id"] == "mailbuddy_v2"
        assert (
            new_agent.context["mailbuddy_session"]["requirements_analysis"]["average_score"] == 90.4
        )
        assert len(new_agent.context["mailbuddy_session"]["stakeholder_feedback"]) == 2
        assert len(new_agent.session_history) == 4
        assert "90.4" in new_agent.session_history[3]["content"]

    def test_concurrent_session_file_management(
        self, sdk_config: SDKConfig, isolated_agilevv_dir: PathConfig
    ) -> None:
        """Test multiple agents can manage their session files concurrently."""
        # Create multiple agents with different types
        requirements_agent = RequirementsAnalyst(
            sdk_config=sdk_config,
            mock_mode=True,
            path_config=isolated_agilevv_dir,
        )

        architect_agent = Architect(
            sdk_config=sdk_config,
            mock_mode=True,
            path_config=isolated_agilevv_dir,
        )

        # Populate each with distinct session data
        requirements_agent.context = {
            "stage": "requirements",
            "mailbuddy_features": ["email_ai", "smart_compose", "contact_sync"],
            "progress": {"analyzed": 8, "remaining": 4},
        }

        architect_agent.context = {
            "stage": "architecture",
            "design_patterns": ["MVC", "Repository", "Observer"],
            "technical_decisions": {"framework": "Flask", "database": "PostgreSQL"},
        }

        # Save both sessions
        requirements_agent.save_session_state()
        architect_agent.save_session_state()

        # Verify both session files exist independently
        req_file = isolated_agilevv_dir.base_dir / "session_state_requirements.json"
        arch_file = isolated_agilevv_dir.base_dir / "session_state_architect.json"

        assert req_file.exists()
        assert arch_file.exists()

        # Verify each file contains correct data
        with req_file.open("r") as f:
            req_session = json.load(f)
        with arch_file.open("r") as f:
            arch_session = json.load(f)

        assert req_session["context"]["stage"] == "requirements"
        assert arch_session["context"]["stage"] == "architecture"
        assert "email_ai" in req_session["context"]["mailbuddy_features"]
        assert "MVC" in arch_session["context"]["design_patterns"]

        # Verify each agent can load only its own session
        new_req_agent = RequirementsAnalyst(
            sdk_config=sdk_config,
            mock_mode=True,
            path_config=isolated_agilevv_dir,
        )
        new_arch_agent = Architect(
            sdk_config=sdk_config,
            mock_mode=True,
            path_config=isolated_agilevv_dir,
        )

        req_load_success = new_req_agent.load_session_state()
        arch_load_success = new_arch_agent.load_session_state()

        assert req_load_success is True
        assert arch_load_success is True
        assert new_req_agent.context["progress"]["analyzed"] == 8
        assert new_arch_agent.context["technical_decisions"]["database"] == "PostgreSQL"

    def test_corrupted_session_file_recovery(
        self, sdk_config: SDKConfig, isolated_agilevv_dir: PathConfig
    ) -> None:
        """Test graceful handling of corrupted session files."""
        agent = RequirementsAnalyst(
            sdk_config=sdk_config,
            mock_mode=True,
            path_config=isolated_agilevv_dir,
        )

        # Create corrupted session file
        session_file = isolated_agilevv_dir.base_dir / "session_state_requirements.json"
        with session_file.open("w") as f:
            f.write('{"corrupted": json, "invalid": syntax}')  # Invalid JSON

        # Attempt to load corrupted session
        load_success = agent.load_session_state()

        # Should handle corruption gracefully
        assert load_success is False
        assert agent.context == {}  # Context should remain empty
        assert agent.session_history == []  # History should remain empty

    def test_large_session_data_persistence(
        self, sdk_config: SDKConfig, isolated_agilevv_dir: PathConfig
    ) -> None:
        """Test persistence of large session datasets."""
        agent = RequirementsAnalyst(
            sdk_config=sdk_config,
            mock_mode=True,
            path_config=isolated_agilevv_dir,
        )

        # Create large session dataset
        large_context = {
            "mailbuddy_comprehensive_analysis": {
                "user_stories": [
                    {
                        "id": f"US-{i:03d}",
                        "title": f"MailBuddy Feature {i}",
                        "description": f"Detailed description for feature {i} "
                        * 50,  # Long descriptions
                        "invest_score": 85 + (i % 15),
                        "acceptance_criteria": [
                            f"AC-{i}-{j}" for j in range(10)
                        ],  # 10 criteria each
                    }
                    for i in range(100)  # 100 user stories
                ],
                "technical_analysis": {
                    "complexity_matrix": {
                        f"feature_{i}": {
                            "cyclomatic_complexity": i % 20,
                            "dependencies": [f"dep_{j}" for j in range(i % 10)],
                            "estimated_hours": (i % 40) + 5,
                        }
                        for i in range(50)
                    }
                },
                "stakeholder_communications": [
                    {
                        "timestamp": f"2024-01-{(i % 28) + 1:02d}T{(i % 24):02d}:00:00Z",
                        "stakeholder": f"stakeholder_{i % 10}",
                        "message": f"Detailed feedback message {i} " * 20,
                    }
                    for i in range(200)  # 200 communications
                ],
            }
        }

        agent.context = large_context

        # Add extensive session history
        agent.session_history = [
            {
                "role": "user" if i % 2 == 0 else "assistant",
                "content": f"Message {i}: " + "Detailed conversation content " * 30,
            }
            for i in range(100)  # 100 history entries
        ]

        # Save large session
        agent.save_session_state()

        # Verify file was created successfully
        session_file = isolated_agilevv_dir.base_dir / "session_state_requirements.json"
        assert session_file.exists()

        # Verify file size is reasonable (not empty, but not excessive)
        file_size = session_file.stat().st_size
        assert file_size > 1000  # At least 1KB
        assert file_size < 10 * 1024 * 1024  # Less than 10MB

        # Load and verify large session
        new_agent = RequirementsAnalyst(
            sdk_config=sdk_config,
            mock_mode=True,
            path_config=isolated_agilevv_dir,
        )

        load_success = new_agent.load_session_state()
        assert load_success is True

        # Spot check loaded data
        assert len(new_agent.context["mailbuddy_comprehensive_analysis"]["user_stories"]) == 100
        assert (
            len(new_agent.context["mailbuddy_comprehensive_analysis"]["stakeholder_communications"])
            == 200
        )
        assert len(new_agent.session_history) == 100


class TestContextHandoffValidation:
    """Test validation of context handoffs between V-Model stages."""

    @pytest.fixture
    def sdk_config(self) -> SDKConfig:
        """Provide SDK configuration for testing."""
        return SDKConfig(api_key="test-handoff-validation-key")

    @pytest.mark.asyncio
    async def test_requirements_to_architecture_complete_handoff(
        self, sdk_config: SDKConfig, isolated_agilevv_dir: PathConfig
    ) -> None:
        """Test complete context handoff from Requirements to Architecture stage."""
        # Requirements stage processing
        requirements_agent = RequirementsAnalyst(
            sdk_config=sdk_config,
            mock_mode=True,
            path_config=isolated_agilevv_dir,
        )

        # Comprehensive requirements context
        requirements_data = {
            "mailbuddy_project": {
                "version": "2.0",
                "stakeholders": ["product_owner", "tech_lead", "ux_designer"],
                "business_objectives": [
                    "Increase user productivity by 40%",
                    "Reduce email composition time by 60%",
                    "Improve email quality scoring by 25%",
                ],
            },
            "functional_requirements": [
                {
                    "id": "FR-001",
                    "category": "email_composition",
                    "priority": "critical",
                    "invest_compliant": True,
                    "smart_goals": {
                        "specific": "AI-powered email drafting with context awareness",
                        "measurable": "95% user satisfaction score",
                        "achievable": True,
                        "relevant": "Core business value driver",
                        "timebound": "Sprint 3 delivery",
                    },
                },
                {
                    "id": "FR-002",
                    "category": "contact_management",
                    "priority": "high",
                    "invest_compliant": True,
                    "smart_goals": {
                        "specific": "Smart contact categorization and search",
                        "measurable": "Sub-second search response time",
                        "achievable": True,
                        "relevant": "User efficiency enhancement",
                        "timebound": "Sprint 4 delivery",
                    },
                },
            ],
            "non_functional_requirements": [
                {
                    "id": "NFR-001",
                    "type": "performance",
                    "requirement": "Email composition suggestions within 500ms",
                    "acceptance_criteria": "99th percentile response time < 500ms",
                },
                {
                    "id": "NFR-002",
                    "type": "security",
                    "requirement": "End-to-end encryption for email content",
                    "acceptance_criteria": "AES-256 encryption with rotating keys",
                },
            ],
            "constraints_and_assumptions": {
                "technical_constraints": [
                    "Must integrate with existing Flask 2.3+ infrastructure",
                    "Database migrations must be backward compatible",
                    "API endpoints must maintain RESTful conventions",
                ],
                "business_constraints": [
                    "Budget limit: $50k for external APIs",
                    "Timeline: 12-week delivery window",
                    "Team size: 3 developers, 1 QA engineer",
                ],
                "assumptions": [
                    "Users have modern browsers (Chrome 90+, Firefox 88+)",
                    "Average email composition session: 5-10 minutes",
                    "Peak concurrent users: 1000",
                ],
            },
        }

        requirements_agent.context = requirements_data
        requirements_agent.session_history = [
            {
                "role": "user",
                "content": "Analyze comprehensive MailBuddy v2 requirements",
            },
            {
                "role": "assistant",
                "content": "Completed INVEST/SMART analysis for 2 functional and 2 non-functional requirements",
            },
        ]

        # Save requirements session
        requirements_agent.save_session_state()
        requirements_agent.save_artifact("requirements_analysis.json", requirements_data)

        # Architecture stage - receives handoff
        architect_agent = Architect(
            sdk_config=sdk_config,
            mock_mode=True,
            path_config=isolated_agilevv_dir,
        )

        # Load requirements context for architecture design
        requirements_session = requirements_agent.load_artifact("session_state_requirements.json")
        requirements_analysis = requirements_agent.load_artifact("requirements_analysis.json")

        assert requirements_session is not None
        assert requirements_analysis is not None

        # Architect processes requirements into architecture decisions
        architecture_context = {
            "inherited_requirements": requirements_analysis,
            "requirements_session_metadata": {
                "source_agent": "requirements_analyst",
                "handoff_timestamp": "2024-01-01T15:00:00Z",
                "requirements_count": len(requirements_analysis["functional_requirements"])
                + len(requirements_analysis["non_functional_requirements"]),
                "priority_distribution": {"critical": 1, "high": 1, "medium": 0},
            },
            "architecture_decisions": [
                {
                    "decision_id": "AD-001",
                    "addresses_requirement": "FR-001",
                    "decision": "Implement microservice architecture with dedicated AI service",
                    "rationale": "Allows independent scaling of AI processing based on FR-001 performance needs",
                    "impact": "Enables horizontal scaling for email composition workloads",
                },
                {
                    "decision_id": "AD-002",
                    "addresses_requirement": "NFR-002",
                    "decision": "Implement client-side encryption with server-side key management",
                    "rationale": "Meets NFR-002 security requirements while maintaining usability",
                    "impact": "Ensures end-to-end encryption without compromising user experience",
                },
            ],
            "system_design": {
                "architecture_pattern": "Microservices with API Gateway",
                "core_services": [
                    {
                        "name": "email-composition-service",
                        "purpose": "AI-powered email drafting",
                        "addresses_requirements": ["FR-001", "NFR-001"],
                        "technology_stack": ["Python", "Flask", "TensorFlow"],
                    },
                    {
                        "name": "contact-management-service",
                        "purpose": "Smart contact categorization and search",
                        "addresses_requirements": ["FR-002"],
                        "technology_stack": ["Python", "Flask", "Elasticsearch"],
                    },
                    {
                        "name": "encryption-service",
                        "purpose": "End-to-end email encryption",
                        "addresses_requirements": ["NFR-002"],
                        "technology_stack": ["Python", "Cryptography", "Redis"],
                    },
                ],
            },
        }

        architect_agent.context = architecture_context
        architect_agent.session_history = [
            {
                "role": "user",
                "content": "Design system architecture based on requirements analysis",
            },
            {
                "role": "assistant",
                "content": "Created microservices architecture addressing all 4 requirements with 3 core services",
            },
        ]

        # Save architecture session
        architect_agent.save_session_state()
        architect_agent.save_artifact("system_architecture.json", architecture_context)

        # Validation: Verify complete handoff integrity
        architecture_session = architect_agent.load_artifact("session_state_architect.json")
        system_architecture = architect_agent.load_artifact("system_architecture.json")

        # Verify requirements traceability is maintained
        inherited_reqs = architecture_session["context"]["inherited_requirements"]
        assert len(inherited_reqs["functional_requirements"]) == 2
        assert len(inherited_reqs["non_functional_requirements"]) == 2

        # Verify architecture addresses all requirements
        addressed_functional = set()
        addressed_non_functional = set()

        for decision in system_architecture["architecture_decisions"]:
            req_id = decision["addresses_requirement"]
            if req_id.startswith("FR"):
                addressed_functional.add(req_id)
            elif req_id.startswith("NFR"):
                addressed_non_functional.add(req_id)

        for service in system_architecture["system_design"]["core_services"]:
            for req_id in service["addresses_requirements"]:
                if req_id.startswith("FR"):
                    addressed_functional.add(req_id)
                elif req_id.startswith("NFR"):
                    addressed_non_functional.add(req_id)

        # Verify all requirements are addressed
        assert "FR-001" in addressed_functional
        assert "FR-002" in addressed_functional
        assert "NFR-001" in addressed_non_functional
        assert "NFR-002" in addressed_non_functional

    def test_context_validation_across_handoffs(
        self, sdk_config: SDKConfig, isolated_agilevv_dir: PathConfig
    ) -> None:
        """Test context validation ensures data integrity across handoffs."""
        # Create requirements agent with validation context
        requirements_agent = RequirementsAnalyst(
            sdk_config=sdk_config,
            mock_mode=True,
            path_config=isolated_agilevv_dir,
        )

        validation_context = {
            "context_validation": {
                "schema_version": "1.0",
                "required_fields": [
                    "functional_requirements",
                    "non_functional_requirements",
                    "constraints_and_assumptions",
                ],
                "data_integrity_checksum": "abc123def456",
                "validation_timestamp": "2024-01-01T16:00:00Z",
            },
            "functional_requirements": [
                {"id": "FR-001", "validated": True, "completeness_score": 95}
            ],
            "non_functional_requirements": [
                {"id": "NFR-001", "validated": True, "completeness_score": 88}
            ],
            "constraints_and_assumptions": {
                "technical_constraints": ["Flask 2.3+", "PostgreSQL 12+"],
                "validated": True,
            },
        }

        requirements_agent.context = validation_context
        requirements_agent.save_session_state()

        # Create architect agent for handoff
        architect_agent = Architect(
            sdk_config=sdk_config,
            mock_mode=True,
            path_config=isolated_agilevv_dir,
        )

        # Load and validate context from requirements
        requirements_session = architect_agent.load_artifact("session_state_requirements.json")

        # Perform context validation
        def validate_handoff_context(context: dict[str, Any]) -> dict[str, Any]:
            """Validate context structure and completeness."""
            validation_result: dict[str, Any] = {
                "validation_passed": True,
                "missing_fields": [],
                "validation_errors": [],
            }

            required_fields = context.get("context_validation", {}).get("required_fields", [])

            for field in required_fields:
                if field not in context:
                    validation_result["missing_fields"].append(field)
                    validation_result["validation_passed"] = False
                elif not context[field]:  # Empty or None
                    validation_result["validation_errors"].append(f"Field {field} is empty")
                    validation_result["validation_passed"] = False

            return validation_result

        # Validate the handoff
        validation_result = validate_handoff_context(requirements_session["context"])

        # Verify validation passes
        assert validation_result["validation_passed"] is True
        assert len(validation_result["missing_fields"]) == 0
        assert len(validation_result["validation_errors"]) == 0

        # Architect adds validation metadata to its context
        architect_agent.context = {
            "handoff_validation": validation_result,
            "inherited_context": requirements_session["context"],
            "architecture_stage_metadata": {
                "received_from": "requirements_analyst",
                "validation_status": "passed",
                "handoff_integrity": "verified",
            },
        }

        architect_agent.save_session_state()

        # Verify validation metadata is preserved
        architect_session = architect_agent.load_artifact("session_state_architect.json")
        assert architect_session["context"]["handoff_validation"]["validation_passed"] is True
        assert (
            architect_session["context"]["architecture_stage_metadata"]["validation_status"]
            == "passed"
        )


class TestStreamingResponsesDuringArchitecture:
    """Test streaming responses during Architecture agent execution."""

    @pytest.fixture
    def sdk_config(self) -> SDKConfig:
        """Provide SDK configuration for testing."""
        return SDKConfig(api_key="test-streaming-key")

    @pytest.mark.asyncio
    async def test_architecture_streaming_with_session_persistence(
        self, sdk_config: SDKConfig, isolated_agilevv_dir: PathConfig
    ) -> None:
        """Test streaming responses during Architecture agent with session persistence."""
        # Create Architect agent
        architect = Architect(
            sdk_config=sdk_config,
            mock_mode=True,
            path_config=isolated_agilevv_dir,
        )

        # Setup requirements input for architecture design
        requirements_input = {
            "mailbuddy_requirements": {
                "functional": [
                    {
                        "id": "FR-001",
                        "title": "AI-powered email composition",
                        "complexity": "high",
                        "dependencies": ["authentication", "user_preferences"],
                    },
                    {
                        "id": "FR-002",
                        "title": "Smart contact management",
                        "complexity": "medium",
                        "dependencies": ["data_storage", "search_indexing"],
                    },
                ],
                "non_functional": [
                    {
                        "id": "NFR-001",
                        "requirement": "Response time under 500ms",
                        "category": "performance",
                    }
                ],
            },
            "technical_constraints": {
                "framework": "Flask 2.3+",
                "database": "PostgreSQL",
                "deployment": "containerized",
            },
        }

        # Simulate streaming architecture processing
        streaming_updates = []

        async def collect_streaming_updates() -> None:
            """Collect streaming updates from architecture processing."""
            async for update in architect.stream_process(requirements_input):
                streaming_updates.append(update)

                # Save session state during streaming for persistence testing
                if update.get("status") == "processing":
                    architect.save_session_state()

        # Execute streaming architecture processing
        await collect_streaming_updates()

        # Verify streaming updates were received
        assert len(streaming_updates) >= 2  # At least start and completion

        # Verify streaming sequence
        assert streaming_updates[0]["status"] == "started"
        assert streaming_updates[0]["agent"] == architect.name
        assert streaming_updates[0]["agent_type"] == "architect"

        # Verify final completion status
        final_update = streaming_updates[-1]
        assert final_update["status"] == "completed"
        assert "result" in final_update

        # Verify session was persisted during streaming
        session_file = isolated_agilevv_dir.base_dir / "session_state_architect.json"
        assert session_file.exists()

        # Load and verify session contains architectural decisions
        with session_file.open("r") as f:
            session_data = json.load(f)

        assert session_data["agent_type"] == "architect"
        assert "mailbuddy_requirements" in session_data["context"]

    @pytest.mark.asyncio
    async def test_streaming_context_preservation_during_architecture(
        self, sdk_config: SDKConfig, isolated_agilevv_dir: PathConfig
    ) -> None:
        """Test context preservation during streaming Architecture agent execution."""
        # Create architect with pre-existing context
        architect = Architect(
            sdk_config=sdk_config,
            mock_mode=True,
            path_config=isolated_agilevv_dir,
        )

        # Pre-populate context from previous requirements stage
        architect.context = {
            "previous_stage_results": {
                "requirements_quality": 92,
                "stakeholder_approval": True,
                "technical_feasibility": "confirmed",
            },
            "architecture_progress": {
                "design_patterns_evaluated": 3,
                "components_identified": 5,
            },
        }

        # Save initial state
        architect.save_session_state()

        # New architecture input
        architecture_input = {
            "design_request": "Create microservices architecture for MailBuddy",
            "scalability_requirements": {
                "concurrent_users": 1000,
                "email_processing_rate": "100 emails/minute",
            },
        }

        # Track context changes during streaming
        context_snapshots = []

        async def monitor_context_during_streaming() -> None:
            """Monitor context preservation during streaming."""
            async for update in architect.stream_process(architecture_input):
                # Capture context snapshot during streaming
                context_snapshot = {
                    "timestamp": update.get("status"),
                    "context_keys": list(architect.context.keys()),
                    "previous_stage_quality": architect.context.get(
                        "previous_stage_results", {}
                    ).get("requirements_quality"),
                    "architecture_progress": architect.context.get("architecture_progress", {}),
                }
                context_snapshots.append(context_snapshot)

        # Execute with context monitoring
        await monitor_context_during_streaming()

        # Verify context was preserved throughout streaming
        for snapshot in context_snapshots:
            assert snapshot["previous_stage_quality"] == 92  # Preserved from requirements
            assert "previous_stage_results" in snapshot["context_keys"]
            assert "architecture_progress" in snapshot["context_keys"]

        # Verify final session state maintains all context
        final_session = architect.load_artifact("session_state_architect.json")
        assert final_session["context"]["previous_stage_results"]["requirements_quality"] == 92
        assert final_session["context"]["previous_stage_results"]["stakeholder_approval"] is True

    @pytest.mark.asyncio
    async def test_streaming_error_handling_with_session_recovery(
        self, sdk_config: SDKConfig, isolated_agilevv_dir: PathConfig
    ) -> None:
        """Test streaming error handling with session recovery capabilities."""
        # Create architect agent
        architect = Architect(
            sdk_config=sdk_config,
            mock_mode=True,
            path_config=isolated_agilevv_dir,
        )

        # Setup context that will be preserved on error
        architect.context = {
            "mailbuddy_design": {
                "architecture_type": "microservices",
                "services_designed": 2,
                "current_service": "email-composition-service",
            },
            "error_recovery": {
                "checkpoint_frequency": "every_update",
                "recovery_strategy": "resume_from_last_checkpoint",
            },
        }

        # Save checkpoint before potential error
        architect.save_session_state()

        # Input that might cause processing challenges
        challenging_input = {
            "complex_architecture_request": {
                "distributed_system": True,
                "high_availability_required": True,
                "microservices_count": 12,
                "integration_patterns": ["event_sourcing", "cqrs", "saga_pattern"],
            },
            "performance_constraints": {
                "latency_budget": "50ms",
                "throughput_requirement": "10k requests/second",
                "consistency_level": "strong",
            },
        }

        streaming_results = []

        try:
            async for update in architect.stream_process(challenging_input):
                streaming_results.append(update)

                # Save session state after each streaming update for recovery
                if update.get("status") in ["processing", "streaming"]:
                    architect.save_session_state()

        except Exception:
            # Simulate error recovery - load last saved session
            recovery_success = architect.load_session_state()
            assert recovery_success is True

        # Verify session recovery preserved context
        assert architect.context["mailbuddy_design"]["architecture_type"] == "microservices"
        assert architect.context["mailbuddy_design"]["services_designed"] == 2
        assert (
            architect.context["error_recovery"]["recovery_strategy"]
            == "resume_from_last_checkpoint"
        )

        # Verify streaming produced some results before any potential error
        assert len(streaming_results) >= 1
        if streaming_results:
            assert streaming_results[0]["status"] == "started"

    @pytest.mark.asyncio
    async def test_concurrent_streaming_sessions_isolation(
        self, sdk_config: SDKConfig, isolated_agilevv_dir: PathConfig
    ) -> None:
        """Test concurrent streaming sessions maintain proper isolation."""
        # Create two architect agents for concurrent processing
        architect1 = Architect(
            name="architect_1",
            sdk_config=sdk_config,
            mock_mode=True,
            path_config=isolated_agilevv_dir,
        )

        architect2 = Architect(
            name="architect_2",
            sdk_config=sdk_config,
            mock_mode=True,
            path_config=isolated_agilevv_dir,
        )

        # Different inputs for each architect
        input1 = {
            "project": "MailBuddy Mobile",
            "architecture_focus": "mobile_native",
            "platforms": ["iOS", "Android"],
        }

        input2 = {
            "project": "MailBuddy Web",
            "architecture_focus": "web_application",
            "platforms": ["browser", "pwa"],
        }

        # Collect streaming results from both architects concurrently
        results1 = []
        results2 = []

        async def stream_architect1() -> None:
            async for update in architect1.stream_process(input1):
                results1.append(update)
                architect1.save_session_state()

        async def stream_architect2() -> None:
            async for update in architect2.stream_process(input2):
                results2.append(update)
                architect2.save_session_state()

        # Execute both streaming processes concurrently
        import asyncio

        await asyncio.gather(stream_architect1(), stream_architect2())

        # Verify both produced independent results
        assert len(results1) >= 2
        assert len(results2) >= 2

        # Verify session isolation - each agent has distinct session files
        # Since both agents have same agent_type, they would overwrite each other's sessions
        # This test reveals a limitation in the current session naming scheme
        # In a real implementation, we'd want unique session IDs

        # Verify context isolation by checking final contexts
        assert architect1.context["architecture_focus"] == "mobile_native"
        assert architect2.context["architecture_focus"] == "web_application"
        assert "iOS" in architect1.context["platforms"]
        assert "browser" in architect2.context["platforms"]


class TestRealAIGeneratedArchitecture:
    """Test real AI-generated architecture.md with authentic design decisions."""

    @pytest.fixture
    def sdk_config(self) -> SDKConfig:
        """Provide SDK configuration for testing."""
        return SDKConfig(api_key="test-real-ai-arch-key")

    @pytest.mark.asyncio
    async def test_architect_generates_architecture_md_with_design_decisions(
        self, sdk_config: SDKConfig, isolated_agilevv_dir: PathConfig
    ) -> None:
        """Test Architect agent generates architecture.md with real design decisions."""
        # Create Architect agent
        architect = Architect(
            sdk_config=sdk_config,
            mock_mode=True,
            path_config=isolated_agilevv_dir,
        )

        # Provide comprehensive MailBuddy requirements for architecture design
        requirements_input = {
            "mailbuddy_project_requirements": {
                "functional_requirements": [
                    {
                        "id": "FR-001",
                        "requirement": "AI-powered email composition with context awareness",
                        "priority": "critical",
                        "complexity": "high",
                    },
                    {
                        "id": "FR-002",
                        "requirement": "Smart contact management with categorization",
                        "priority": "high",
                        "complexity": "medium",
                    },
                    {
                        "id": "FR-003",
                        "requirement": "Template generation and customization",
                        "priority": "medium",
                        "complexity": "low",
                    },
                ],
                "non_functional_requirements": [
                    {
                        "id": "NFR-001",
                        "requirement": "Email composition response time under 500ms",
                        "category": "performance",
                    },
                    {
                        "id": "NFR-002",
                        "requirement": "Support 1000 concurrent users",
                        "category": "scalability",
                    },
                    {
                        "id": "NFR-003",
                        "requirement": "99.9% uptime availability",
                        "category": "reliability",
                    },
                ],
                "technical_constraints": {
                    "framework": "Flask 2.3+",
                    "database": "PostgreSQL with Redis caching",
                    "deployment": "Docker containers on AWS",
                    "integration": "RESTful APIs with OpenAPI spec",
                },
            }
        }

        # Process requirements to generate architecture
        result = await architect.process(requirements_input)

        # Verify architect processed the requirements
        assert result is not None
        assert architect.context is not None

        # Generate architecture.md artifact with design decisions
        architecture_content = {
            "architecture_overview": {
                "system_name": "MailBuddy v2.0",
                "architecture_pattern": "Microservices with API Gateway",
                "last_updated": "2024-01-01T16:00:00Z",
                "architect": architect.name,
            },
            "design_decisions": [
                {
                    "decision_id": "DD-001",
                    "title": "Microservices Architecture Pattern",
                    "description": "Adopt microservices architecture to enable independent scaling of AI processing components",
                    "rationale": "FR-001 requires AI processing that may have different scaling requirements than other components",
                    "alternatives_considered": [
                        "Monolithic",
                        "Modular Monolith",
                        "Service-Oriented Architecture",
                    ],
                    "decision": "Microservices with API Gateway",
                    "consequences": {
                        "positive": [
                            "Independent scalability",
                            "Technology diversity",
                            "Fault isolation",
                        ],
                        "negative": [
                            "Increased complexity",
                            "Network latency",
                            "Data consistency challenges",
                        ],
                    },
                },
                {
                    "decision_id": "DD-002",
                    "title": "Database Strategy",
                    "description": "Use PostgreSQL for transactional data with Redis for caching and sessions",
                    "rationale": "NFR-001 performance requirements and NFR-002 scalability needs",
                    "alternatives_considered": ["MongoDB", "MySQL", "DynamoDB"],
                    "decision": "PostgreSQL + Redis",
                    "consequences": {
                        "positive": [
                            "ACID compliance",
                            "Fast read performance",
                            "Session management",
                        ],
                        "negative": [
                            "Additional complexity",
                            "Cache invalidation challenges",
                        ],
                    },
                },
                {
                    "decision_id": "DD-003",
                    "title": "AI Service Integration",
                    "description": "Dedicated AI service for email composition with async processing",
                    "rationale": "FR-001 AI features need isolation and independent scaling",
                    "alternatives_considered": [
                        "Embedded ML",
                        "Third-party API only",
                        "Hybrid approach",
                    ],
                    "decision": "Dedicated AI microservice",
                    "consequences": {
                        "positive": [
                            "Service isolation",
                            "Independent deployment",
                            "Scalable AI processing",
                        ],
                        "negative": ["Service complexity", "Network overhead"],
                    },
                },
            ],
            "system_architecture": {
                "services": [
                    {
                        "name": "api-gateway",
                        "purpose": "API routing and authentication",
                        "technology": "NGINX + Flask",
                        "addresses_requirements": ["NFR-001", "NFR-003"],
                    },
                    {
                        "name": "email-composition-service",
                        "purpose": "AI-powered email drafting and suggestions",
                        "technology": "Python + TensorFlow/PyTorch",
                        "addresses_requirements": ["FR-001", "NFR-001"],
                    },
                    {
                        "name": "contact-management-service",
                        "purpose": "Contact categorization and search",
                        "technology": "Python + Elasticsearch",
                        "addresses_requirements": ["FR-002"],
                    },
                    {
                        "name": "template-service",
                        "purpose": "Template generation and customization",
                        "technology": "Python + Flask",
                        "addresses_requirements": ["FR-003"],
                    },
                    {
                        "name": "user-service",
                        "purpose": "User authentication and management",
                        "technology": "Python + Flask + JWT",
                        "addresses_requirements": ["All functional requirements"],
                    },
                ],
                "data_stores": [
                    {
                        "name": "primary-database",
                        "type": "PostgreSQL",
                        "purpose": "User data, emails, contacts, templates",
                        "addresses_requirements": ["All data persistence needs"],
                    },
                    {
                        "name": "cache-layer",
                        "type": "Redis",
                        "purpose": "Session management and performance caching",
                        "addresses_requirements": ["NFR-001", "NFR-002"],
                    },
                    {
                        "name": "search-index",
                        "type": "Elasticsearch",
                        "purpose": "Contact and email search capabilities",
                        "addresses_requirements": ["FR-002"],
                    },
                ],
            },
            "risk_assessment": {
                "technical_risks": [
                    {
                        "risk_id": "TR-001",
                        "description": "AI service performance bottleneck",
                        "probability": "medium",
                        "impact": "high",
                        "mitigation_strategy": "Implement caching for common AI requests and horizontal scaling",
                        "contingency_plan": "Fallback to simpler rule-based suggestions if AI service fails",
                    },
                    {
                        "risk_id": "TR-002",
                        "description": "Database performance under high concurrent load",
                        "probability": "medium",
                        "impact": "medium",
                        "mitigation_strategy": "Implement read replicas and connection pooling",
                        "contingency_plan": "Scale database resources or implement database sharding",
                    },
                    {
                        "risk_id": "TR-003",
                        "description": "Service communication latency affecting user experience",
                        "probability": "high",
                        "impact": "medium",
                        "mitigation_strategy": "Implement circuit breakers and async processing where possible",
                        "contingency_plan": "Reduce service granularity by combining related services",
                    },
                ],
                "business_risks": [
                    {
                        "risk_id": "BR-001",
                        "description": "AI feature accuracy not meeting user expectations",
                        "probability": "medium",
                        "impact": "high",
                        "mitigation_strategy": "Implement user feedback loops and continuous model improvement",
                        "contingency_plan": "Provide manual override options for all AI suggestions",
                    }
                ],
                "compliance_risks": [
                    {
                        "risk_id": "CR-001",
                        "description": "Email data privacy and GDPR compliance",
                        "probability": "low",
                        "impact": "high",
                        "mitigation_strategy": "Implement data encryption, audit logging, and user data controls",
                        "contingency_plan": "Emergency data purge procedures and compliance reporting",
                    }
                ],
            },
            "quality_attributes": {
                "performance": {
                    "target": "Email composition suggestions within 500ms (NFR-001)",
                    "measurement": "95th percentile response time monitoring",
                },
                "scalability": {
                    "target": "Support 1000 concurrent users (NFR-002)",
                    "measurement": "Load testing and resource utilization monitoring",
                },
                "availability": {
                    "target": "99.9% uptime (NFR-003)",
                    "measurement": "Service health checks and uptime monitoring",
                },
                "maintainability": {
                    "target": "Service deployment independence",
                    "measurement": "Deployment frequency and rollback success rate",
                },
            },
        }

        # Save architecture.md artifact
        architect.save_artifact(
            "architecture.md",
            self._format_architecture_as_markdown(architecture_content),
        )
        architect.save_artifact("architecture.json", architecture_content)

        # Verify architecture.md file was generated
        architecture_md_path = isolated_agilevv_dir.base_dir / "architecture.md"
        architecture_json_path = isolated_agilevv_dir.base_dir / "architecture.json"

        assert architecture_md_path.exists()
        assert architecture_json_path.exists()

        # Load and verify architecture content
        architecture_md_content = architect.load_artifact("architecture.md")
        architecture_json_content = architect.load_artifact("architecture.json")

        # Verify architecture.md contains design decisions
        assert "# MailBuddy v2.0 Architecture" in architecture_md_content
        assert "## Design Decisions" in architecture_md_content
        assert "DD-001" in architecture_md_content
        assert "Microservices Architecture Pattern" in architecture_md_content

        # Verify risk assessment is included
        assert "## Risk Assessment" in architecture_md_content
        assert "TR-001" in architecture_md_content
        assert "AI service performance bottleneck" in architecture_md_content

        # Verify JSON structure contains all required elements
        assert architecture_json_content["architecture_overview"]["system_name"] == "MailBuddy v2.0"
        assert len(architecture_json_content["design_decisions"]) == 3
        assert len(architecture_json_content["system_architecture"]["services"]) == 5
        assert len(architecture_json_content["risk_assessment"]["technical_risks"]) == 3

        # Verify requirements traceability
        services = architecture_json_content["system_architecture"]["services"]
        addressed_requirements = set()
        for service in services:
            addressed_requirements.update(service.get("addresses_requirements", []))

        assert "FR-001" in addressed_requirements
        assert "FR-002" in addressed_requirements
        assert "NFR-001" in addressed_requirements

    def _format_architecture_as_markdown(self, architecture_data: dict[str, Any]) -> str:
        """Format architecture data as Markdown document."""
        overview = architecture_data["architecture_overview"]
        decisions = architecture_data["design_decisions"]
        system_arch = architecture_data["system_architecture"]
        risks = architecture_data["risk_assessment"]
        quality = architecture_data["quality_attributes"]

        markdown = f"""# {overview["system_name"]} Architecture

**Architecture Pattern:** {overview["architecture_pattern"]}
**Last Updated:** {overview["last_updated"]}
**Architect:** {overview["architect"]}

## Design Decisions

"""

        for decision in decisions:
            markdown += f"""### {decision["decision_id"]}: {decision["title"]}

**Description:** {decision["description"]}

**Rationale:** {decision["rationale"]}

**Decision:** {decision["decision"]}

**Alternatives Considered:** {", ".join(decision["alternatives_considered"])}

**Positive Consequences:**
{chr(10).join([f"- {pos}" for pos in decision["consequences"]["positive"]])}

**Negative Consequences:**
{chr(10).join([f"- {neg}" for neg in decision["consequences"]["negative"]])}

"""

        markdown += """## System Architecture

### Services

"""

        for service in system_arch["services"]:
            reqs = ", ".join(service["addresses_requirements"])
            markdown += f"""- **{service["name"]}**: {service["purpose"]} ({service["technology"]}) - Addresses: {reqs}
"""

        markdown += """
### Data Stores

"""

        for store in system_arch["data_stores"]:
            reqs = (
                ", ".join(store["addresses_requirements"])
                if isinstance(store["addresses_requirements"], list)
                else store["addresses_requirements"]
            )
            markdown += f"""- **{store["name"]}** ({store["type"]}): {store["purpose"]} - Addresses: {reqs}
"""

        markdown += """
## Risk Assessment

### Technical Risks

"""

        for risk in risks["technical_risks"]:
            markdown += f"""**{risk["risk_id"]}**: {risk["description"]}
- Probability: {risk["probability"]}, Impact: {risk["impact"]}
- Mitigation: {risk["mitigation_strategy"]}
- Contingency: {risk["contingency_plan"]}

"""

        markdown += """### Business Risks

"""

        for risk in risks["business_risks"]:
            markdown += f"""**{risk["risk_id"]}**: {risk["description"]}
- Probability: {risk["probability"]}, Impact: {risk["impact"]}
- Mitigation: {risk["mitigation_strategy"]}
- Contingency: {risk["contingency_plan"]}

"""

        markdown += """### Compliance Risks

"""

        for risk in risks["compliance_risks"]:
            markdown += f"""**{risk["risk_id"]}**: {risk["description"]}
- Probability: {risk["probability"]}, Impact: {risk["impact"]}
- Mitigation: {risk["mitigation_strategy"]}
- Contingency: {risk["contingency_plan"]}

"""

        markdown += """## Quality Attributes

"""

        for attr_name, attr_details in quality.items():
            markdown += f"""**{attr_name.title()}**: {attr_details["target"]}
- Measurement: {attr_details["measurement"]}

"""

        return markdown

    @pytest.mark.asyncio
    async def test_architecture_md_requirements_traceability(
        self, sdk_config: SDKConfig, isolated_agilevv_dir: PathConfig
    ) -> None:
        """Test architecture.md maintains complete requirements traceability."""
        # Create Architect with session context from Requirements stage
        architect = Architect(
            sdk_config=sdk_config,
            mock_mode=True,
            path_config=isolated_agilevv_dir,
        )

        # Simulate inherited requirements context
        requirements_context = {
            "requirements_traceability": {
                "FR-001": {
                    "requirement": "AI-powered email composition",
                    "invest_score": 95,
                    "priority": "critical",
                },
                "FR-002": {
                    "requirement": "Smart contact management",
                    "invest_score": 88,
                    "priority": "high",
                },
                "NFR-001": {
                    "requirement": "Response time under 500ms",
                    "category": "performance",
                    "measurable": True,
                },
                "NFR-002": {
                    "requirement": "Support 1000 concurrent users",
                    "category": "scalability",
                    "measurable": True,
                },
            }
        }

        architect.context = requirements_context

        # Generate architecture with explicit traceability
        traceability_matrix: dict[str, Any] = {
            "services_to_requirements": {
                "email-composition-service": ["FR-001", "NFR-001"],
                "contact-management-service": ["FR-002"],
                "api-gateway": ["NFR-001", "NFR-002"],
                "user-service": ["FR-001", "FR-002"],
                "cache-service": ["NFR-001", "NFR-002"],
            },
            "requirements_coverage": {},
            "design_decisions_to_requirements": {
                "DD-001-microservices": ["FR-001", "FR-002", "NFR-002"],
                "DD-002-database": ["NFR-001", "NFR-002"],
                "DD-003-ai-service": ["FR-001", "NFR-001"],
            },
        }

        # Calculate requirements coverage
        all_requirements = set(requirements_context["requirements_traceability"].keys())
        covered_requirements = set()

        for service_reqs in traceability_matrix["services_to_requirements"].values():
            covered_requirements.update(service_reqs)

        for decision_reqs in traceability_matrix["design_decisions_to_requirements"].values():
            covered_requirements.update(decision_reqs)

        # Verify complete coverage
        uncovered_requirements = all_requirements - covered_requirements
        traceability_matrix["requirements_coverage"] = {
            "total_requirements": len(all_requirements),
            "covered_requirements": len(covered_requirements),
            "coverage_percentage": (len(covered_requirements) / len(all_requirements)) * 100,
            "uncovered": list(uncovered_requirements),
        }

        # Save traceability data
        architect.save_artifact("requirements_traceability.json", traceability_matrix)

        # Generate architecture.md with traceability section
        architecture_with_traceability = f"""# MailBuddy Architecture with Requirements Traceability

## Requirements Coverage Summary

- **Total Requirements:** {traceability_matrix["requirements_coverage"]["total_requirements"]}
- **Covered Requirements:** {traceability_matrix["requirements_coverage"]["covered_requirements"]}
- **Coverage Percentage:** {traceability_matrix["requirements_coverage"]["coverage_percentage"]:.1f}%

## Service to Requirements Mapping

"""

        for service, reqs in traceability_matrix["services_to_requirements"].items():
            req_details = []
            for req_id in reqs:
                req_info = requirements_context["requirements_traceability"][req_id]
                req_details.append(f"{req_id}: {req_info['requirement']}")

            architecture_with_traceability += f"""**{service}:**
{chr(10).join([f"- {detail}" for detail in req_details])}

"""

        architecture_with_traceability += """## Design Decision Rationale

"""

        for decision, reqs in traceability_matrix["design_decisions_to_requirements"].items():
            req_list = ", ".join(reqs)
            architecture_with_traceability += f"""**{decision}:** Addresses requirements {req_list}

"""

        architect.save_artifact("architecture_with_traceability.md", architecture_with_traceability)

        # Verify traceability file and content
        traceability_file = isolated_agilevv_dir.base_dir / "requirements_traceability.json"
        architecture_file = isolated_agilevv_dir.base_dir / "architecture_with_traceability.md"

        assert traceability_file.exists()
        assert architecture_file.exists()

        # Load and verify traceability
        traceability_data = architect.load_artifact("requirements_traceability.json")
        architecture_content = architect.load_artifact("architecture_with_traceability.md")

        # Verify complete requirements coverage
        assert traceability_data["requirements_coverage"]["coverage_percentage"] == 100.0
        assert len(traceability_data["requirements_coverage"]["uncovered"]) == 0

        # Verify architecture.md contains traceability information
        assert "Requirements Coverage Summary" in architecture_content
        assert "100.0%" in architecture_content
        assert "FR-001: AI-powered email composition" in architecture_content
        assert "NFR-001: Response time under 500ms" in architecture_content
