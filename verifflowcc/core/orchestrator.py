"""Orchestrator for V-Model stage execution with Claude Code SDK integration."""

import json
import logging
from collections.abc import Callable
from datetime import datetime
from pathlib import Path
from typing import Any, cast

from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from verifflowcc.agents.factory import AgentFactory
from verifflowcc.core.path_config import PathConfig
from verifflowcc.core.sdk_config import SDKConfig
from verifflowcc.core.vmodel import VModelStage

logger = logging.getLogger(__name__)


class Orchestrator:
    """Orchestrates V-Model workflow execution with stage transitions, gating, and Claude Code SDK coordination."""

    def __init__(
        self,
        config_path: Path | None = None,
        path_config: PathConfig | None = None,
        sdk_config: SDKConfig | None = None,
    ):
        """Initialize the Orchestrator with SDK integration.

        Args:
            config_path: Path to configuration file (deprecated, use path_config)
            path_config: PathConfig instance for managing project paths
            sdk_config: SDK configuration for agents
        """
        # Use provided PathConfig or create default
        self.path_config = path_config or PathConfig()

        # Support legacy config_path parameter for backward compatibility
        if config_path and not path_config:
            # If only config_path is provided, derive base_dir from it
            base_dir = config_path.parent if config_path.parent.name == ".agilevv" else None
            self.path_config = PathConfig(base_dir=base_dir)
            self.config_path = config_path
        else:
            self.config_path = self.path_config.config_path

        self.state_path = self.path_config.state_path
        self.sdk_config = sdk_config or SDKConfig()
        self.console = Console()
        self.current_stage = VModelStage.PLANNING
        self.state = self._load_state()
        self.config = self._load_config()
        self.agent_factory = AgentFactory(self.sdk_config, self.path_config)
        self.agents = self._initialize_agents()
        self.stage_callbacks: dict[VModelStage, list[Callable]] = {}

    def _load_state(self) -> dict[str, Any]:
        """Load project state from state.json."""
        if self.state_path.exists():
            return cast("dict[str, Any]", json.loads(self.state_path.read_text()))
        return {
            "current_stage": VModelStage.PLANNING.value,
            "sprint_number": 0,
            "completed_stages": [],
            "active_story": None,
            "stage_artifacts": {},
            "checkpoint_history": [],
            "session_state": {},  # For SDK session persistence
            "agent_metrics": {},  # Track agent performance metrics
            "quality_gates": {},  # Track quality gate results
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
        }

    def _save_state(self) -> None:
        """Save project state to state.json."""
        self.state["updated_at"] = datetime.now().isoformat()
        self.state["current_stage"] = self.current_stage.value
        self.path_config.ensure_base_exists()
        self.state_path.write_text(json.dumps(self.state, indent=2))

    def _load_config(self) -> dict[str, Any]:
        """Load configuration from config.yaml."""
        if self.config_path.exists():
            import yaml

            return cast("dict[str, Any]", yaml.safe_load(self.config_path.read_text()))

        return {
            "v_model": {
                "gating_mode": "soft",
                "quality_thresholds": {
                    "test_coverage": 80,
                    "code_quality_score": 70,
                    "requirements_validation_score": 80,
                    "overall_readiness_score": 75,
                },
                "stages": {
                    "planning": {"enabled": True, "gating": "soft"},
                    "requirements": {"enabled": True, "gating": "hard"},
                    "design": {"enabled": True, "gating": "hard"},
                    "coding": {"enabled": True, "gating": "soft"},
                    "unit_testing": {"enabled": True, "gating": "hard"},
                    "integration_testing": {"enabled": True, "gating": "hard"},
                    "system_testing": {"enabled": True, "gating": "soft"},
                    "validation": {"enabled": True, "gating": "hard"},
                },
            },
            "agents": {
                "requirements_analyst": {
                    "agent_type": "requirements",
                    "system_prompt_override": None,
                    "timeout": 60,
                },
                "architect": {
                    "agent_type": "architect",
                    "system_prompt_override": None,
                    "timeout": 90,
                },
                "developer": {
                    "agent_type": "developer",
                    "system_prompt_override": None,
                    "timeout": 120,
                },
                "qa_tester": {
                    "agent_type": "qa",
                    "system_prompt_override": None,
                    "timeout": 90,
                },
                "integration": {
                    "agent_type": "integration",
                    "system_prompt_override": None,
                    "timeout": 150,
                },
            },
            "sdk": {
                "max_retries": 3,
                "timeout": 120,
                "session_persistence": True,
                "streaming": True,
            },
        }

    def _initialize_agents(self) -> dict[str, Any]:
        """Initialize all SDK-based subagents."""
        agents = {}

        try:
            # Initialize all agents using the factory
            agents["requirements_analyst"] = self.agent_factory.create_agent("requirements_analyst")
            agents["architect"] = self.agent_factory.create_agent("architect")
            agents["developer"] = self.agent_factory.create_agent("developer")
            agents["qa_tester"] = self.agent_factory.create_agent("qa_tester")
            agents["integration"] = self.agent_factory.create_agent("integration")

            logger.info(f"Initialized {len(agents)} SDK-based agents")

        except Exception as e:
            logger.error(f"Failed to initialize agents: {e}")
            # Fallback to empty dict - agents will be created on demand
            agents = {}

        return agents

    def register_callback(self, stage: VModelStage, callback: Callable) -> None:
        """Register a callback for a specific stage.

        Args:
            stage: V-Model stage
            callback: Callback function
        """
        if stage not in self.stage_callbacks:
            self.stage_callbacks[stage] = []
        self.stage_callbacks[stage].append(callback)

    async def execute_stage(self, stage: VModelStage, context: dict[str, Any]) -> dict[str, Any]:
        """Execute a specific V-Model stage with SDK-based agents.

        Args:
            stage: Stage to execute
            context: Execution context

        Returns:
            Stage execution results
        """
        self.current_stage = stage
        self.console.print(Panel(f"[bold cyan]Executing Stage: {stage.value.upper()}[/bold cyan]"))

        # Check if stage is enabled
        stage_config = self.config["v_model"]["stages"].get(stage.value, {})
        if not stage_config.get("enabled", True):
            self.console.print(f"[yellow]Stage {stage.value} is disabled, skipping...[/yellow]")
            return {"status": "skipped", "stage": stage.value}

        try:
            # Execute stage-specific logic with SDK agents
            result = await self._execute_stage_logic(stage, context)

            # Update agent metrics
            self._update_agent_metrics(stage, result)

            # Apply quality gating controls
            gating_result = await self._apply_advanced_gating(stage, result)

            if gating_result["passed"]:
                self.state["completed_stages"].append(stage.value)
                self.console.print(f"[green]✓ Stage {stage.value} completed successfully[/green]")
            else:
                if stage_config.get("gating") == "hard":
                    self.console.print(f"[red]✗ Stage {stage.value} failed gating controls[/red]")
                    self.console.print(f"[red]Issues: {', '.join(gating_result.get('issues', []))}")
                    raise Exception(
                        f"Stage {stage.value} failed hard gating: {gating_result['issues']}"
                    )
                else:
                    self.console.print(
                        f"[yellow]⚠ Stage {stage.value} has warnings but proceeding[/yellow]"
                    )
                    if gating_result.get("issues"):
                        self.console.print(
                            f"[yellow]Warnings: {', '.join(gating_result['issues'])}"
                        )

            # Store quality gate results
            self.state["quality_gates"][stage.value] = gating_result

            # Execute callbacks
            for callback in self.stage_callbacks.get(stage, []):
                await callback(result)

            # Save artifacts and session state
            self.state["stage_artifacts"][stage.value] = result.get("artifacts", {})
            if "session_state" in result:
                self.state["session_state"][stage.value] = result["session_state"]

            self._save_state()

            return result

        except Exception as e:
            logger.error(f"Error executing stage {stage.value}: {e}")
            error_result: dict[str, Any] = {
                "status": "error",
                "stage": stage.value,
                "error": str(e),
                "artifacts": {},
                "metrics": {},
                "timestamp": datetime.now().isoformat(),
            }

            # Save error state
            self.state["stage_artifacts"][stage.value] = error_result["artifacts"]
            self._save_state()

            return error_result

    async def _execute_stage_logic(
        self, stage: VModelStage, context: dict[str, Any]
    ) -> dict[str, Any]:
        """Execute the actual logic for a stage using SDK-based agents.

        Args:
            stage: Stage to execute
            context: Execution context

        Returns:
            Stage execution results
        """
        # Map V-Model stages to appropriate agents
        stage_agent_mapping = {
            VModelStage.REQUIREMENTS: "requirements_analyst",
            VModelStage.DESIGN: "architect",
            VModelStage.CODING: "developer",
            VModelStage.UNIT_TESTING: "qa_tester",
            VModelStage.INTEGRATION_TESTING: "qa_tester",
            VModelStage.SYSTEM_TESTING: "qa_tester",
            VModelStage.VALIDATION: "integration",
        }

        agent_name = stage_agent_mapping.get(stage)

        if agent_name:
            agent = self.agents.get(agent_name)
            if not agent:
                # Create agent on demand if not initialized
                try:
                    agent = self.agent_factory.create_agent(agent_name)
                    self.agents[agent_name] = agent
                except Exception as e:
                    logger.error(f"Failed to create agent {agent_name}: {e}")
                    return {"status": "error", "error": f"Agent creation failed: {e}"}

            # Prepare input data based on stage and previous results
            input_data = self._prepare_comprehensive_agent_input(stage, context)

            try:
                # Execute agent with SDK
                if hasattr(agent, "process"):
                    result = await agent.process(input_data)
                else:
                    # Legacy compatibility
                    result = await agent.execute(**input_data)

                return cast("dict[str, Any]", result)

            except Exception as e:
                logger.error(f"Agent {agent_name} execution failed: {e}")
                return {
                    "status": "error",
                    "agent": agent_name,
                    "error": str(e),
                    "stage": stage.value,
                    "artifacts": {},
                    "metrics": {},
                    "timestamp": datetime.now().isoformat(),
                }

        # Handle unimplemented stages
        logger.warning(f"No agent mapped for stage {stage.value}")
        return {
            "status": "success",
            "stage": stage.value,
            "artifacts": {},
            "metrics": {},
            "message": f"Stage {stage.value} executed without specific agent",
        }

    def _prepare_comprehensive_agent_input(
        self, stage: VModelStage, context: dict[str, Any]
    ) -> dict[str, Any]:
        """Prepare comprehensive input data for SDK-based agents.

        Args:
            stage: Current V-Model stage
            context: Execution context

        Returns:
            Formatted input data for the agent
        """
        # Get story information
        story = context.get("story", self.state.get("active_story", {}))
        story_id = (
            story.get("id")
            if isinstance(story, dict)
            else context.get("story_id", f"STORY-{datetime.now().strftime('%Y%m%d-%H%M%S')}")
        )

        # Base input structure for SDK agents
        input_data = {
            "story_id": story_id,
            "task_description": context.get(
                "task_description",
                story.get("description", "") if isinstance(story, dict) else str(story),
            ),
            "context": {
                "project_name": "VeriFlowCC",
                "sprint_number": self.state.get("sprint_number", 1),
                "stage": stage.value,
                "previous_stages": self.state.get("completed_stages", []),
                "tech_stack": "Python, FastAPI, Claude Code SDK",
                **context,
            },
        }

        # Add stage-specific data from previous artifacts
        stage_artifacts = self.state.get("stage_artifacts", {})

        if stage == VModelStage.DESIGN:
            # Architect needs requirements
            requirements_artifacts = stage_artifacts.get("requirements", {})
            input_data["requirements"] = requirements_artifacts.get("requirements_data", {})

        elif stage == VModelStage.CODING:
            # Developer needs design and requirements
            design_artifacts = stage_artifacts.get("design", {})
            input_data["design_spec"] = design_artifacts.get("design_data", {})

        elif stage in [
            VModelStage.UNIT_TESTING,
            VModelStage.INTEGRATION_TESTING,
            VModelStage.SYSTEM_TESTING,
        ]:
            # QA Tester needs implementation and previous stage data
            implementation_artifacts = stage_artifacts.get("coding", {})
            input_data["implementation_data"] = implementation_artifacts.get(
                "implementation_data", {}
            )
            input_data["testing_phase"] = stage.value.replace("_testing", "")

        elif stage == VModelStage.VALIDATION:
            # Integration agent needs all previous stage data
            input_data["system_artifacts"] = stage_artifacts
            input_data["requirements_data"] = stage_artifacts.get("requirements", {})
            input_data["design_data"] = stage_artifacts.get("design", {})
            input_data["implementation_data"] = stage_artifacts.get("coding", {})
            input_data["testing_data"] = stage_artifacts.get("unit_testing", {})
            input_data["deployment_target"] = context.get("deployment_target", "production")

        # Add session state for continuity
        session_state = self.state.get("session_state", {})
        if session_state:
            input_data["session_state"] = session_state

        return input_data

    def _update_agent_metrics(self, stage: VModelStage, result: dict[str, Any]) -> None:
        """Update agent performance metrics.

        Args:
            stage: Executed stage
            result: Stage execution result
        """
        if "agent_metrics" not in self.state:
            self.state["agent_metrics"] = {}

        stage_key = stage.value
        metrics = result.get("metrics", {})

        self.state["agent_metrics"][stage_key] = {
            "last_execution": datetime.now().isoformat(),
            "status": result.get("status", "unknown"),
            "execution_time": metrics.get("execution_time", "unknown"),
            "quality_score": metrics.get("overall_quality_score", 0),
            "artifacts_created": len(result.get("artifacts", {})),
            **metrics,
        }

    async def _apply_advanced_gating(
        self, stage: VModelStage, result: dict[str, Any]
    ) -> dict[str, Any]:
        """Apply advanced gating controls with quality thresholds.

        Args:
            stage: Current stage
            result: Stage execution results

        Returns:
            Gating results with detailed analysis
        """
        stage_config = self.config["v_model"]["stages"].get(stage.value, {})
        gating_mode = stage_config.get("gating", "soft")

        if gating_mode == "off":
            return {"passed": True, "mode": "off", "issues": []}

        # Get quality thresholds
        thresholds = self.config["v_model"].get("quality_thresholds", {})

        criteria_met = True
        issues = []
        warnings = []

        # Check stage-specific quality criteria
        if stage == VModelStage.REQUIREMENTS:
            requirements_data = result.get("requirements_data", {})
            validation_score = requirements_data.get("validation_score", 0)
            min_score = thresholds.get("requirements_validation_score", 80)

            if validation_score < min_score:
                criteria_met = False
                issues.append(
                    f"Requirements validation score {validation_score}% below {min_score}% threshold"
                )

            # Check for acceptance criteria
            acceptance_criteria = requirements_data.get("acceptance_criteria", [])
            if not acceptance_criteria:
                criteria_met = False
                issues.append("Missing acceptance criteria")

        elif stage == VModelStage.DESIGN:
            design_data = result.get("design_data", {})
            components = design_data.get("components", [])

            if not components:
                criteria_met = False
                issues.append("Design must specify system components")

            interfaces = design_data.get("interface_specifications", [])
            if not interfaces:
                warnings.append("No interface specifications defined")

        elif stage == VModelStage.CODING:
            implementation_data = result.get("implementation_data", {})
            quality_metrics = implementation_data.get("quality_metrics", {})
            overall_score = quality_metrics.get("overall_score", 0)
            min_score = thresholds.get("code_quality_score", 70)

            if overall_score < min_score:
                criteria_met = False
                issues.append(
                    f"Code quality score {overall_score:.1f}% below {min_score}% threshold"
                )

            # Check for created files
            created_files = result.get("metrics", {}).get("files_created", 0)
            if created_files == 0:
                warnings.append("No source files were created")

        elif stage in [
            VModelStage.UNIT_TESTING,
            VModelStage.INTEGRATION_TESTING,
            VModelStage.SYSTEM_TESTING,
        ]:
            testing_data = result.get("testing_data", {})
            quality_assessment = testing_data.get("quality_assessment", {})

            # Check if ready for next stage
            if not quality_assessment.get("readiness_for_next_stage", False):
                criteria_met = False
                issues.extend(quality_assessment.get("critical_issues", []))

            # Check test execution results
            test_execution = testing_data.get("test_execution", {})
            execution_summary = test_execution.get("execution_summary", {})
            pass_rate_str = execution_summary.get("pass_rate", "0%")

            try:
                pass_rate = int(pass_rate_str.replace("%", ""))
                if pass_rate < 80:
                    criteria_met = False
                    issues.append(f"Test pass rate {pass_rate}% below 80% threshold")
            except (ValueError, AttributeError):
                warnings.append("Could not determine test pass rate")

        elif stage == VModelStage.VALIDATION:
            integration_data = result.get("integration_data", {})
            release_decision = integration_data.get("release_recommendation", {})
            go_no_go = release_decision.get("go_no_go_decision", "NO-GO")

            if go_no_go != "GO":
                criteria_met = False
                issues.append(f"Integration validation resulted in {go_no_go} decision")
                issues.extend(release_decision.get("outstanding_issues", []))

            # Check readiness score
            readiness_score = release_decision.get("overall_readiness_score", 0)
            min_readiness = thresholds.get("overall_readiness_score", 75)

            if readiness_score < min_readiness:
                criteria_met = False
                issues.append(
                    f"Overall readiness score {readiness_score:.1f}% below {min_readiness}% threshold"
                )

        # Combine issues and warnings
        all_issues = issues + warnings

        return {
            "passed": criteria_met,
            "mode": gating_mode,
            "issues": issues,
            "warnings": warnings,
            "all_issues": all_issues,
            "quality_score": result.get("metrics", {}).get("overall_quality_score", 0),
        }

    async def run_sprint(self, story: dict[str, Any]) -> dict[str, Any]:
        """Run a complete sprint through all V-Model stages with SDK coordination.

        Args:
            story: User story to implement

        Returns:
            Sprint execution results
        """
        self.state["sprint_number"] += 1
        self.state["active_story"] = story
        self._save_state()

        sprint_results = {
            "sprint_number": self.state["sprint_number"],
            "story": story,
            "stages": {},
            "quality_summary": {},
            "agent_performance": {},
            "started_at": datetime.now().isoformat(),
        }

        # V-Model execution order
        v_model_stages = [
            VModelStage.PLANNING,
            VModelStage.REQUIREMENTS,
            VModelStage.DESIGN,
            VModelStage.CODING,
            VModelStage.UNIT_TESTING,
            VModelStage.INTEGRATION_TESTING,
            VModelStage.SYSTEM_TESTING,
            VModelStage.VALIDATION,
        ]

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console,
        ) as progress:
            for stage in v_model_stages:
                task = progress.add_task(f"Executing {stage.value}...", total=None)

                try:
                    # Prepare stage context
                    stage_context = {
                        "story": story,
                        "sprint_results": sprint_results,
                        "previous_artifacts": self.state.get("stage_artifacts", {}),
                        "session_state": self.state.get("session_state", {}),
                    }

                    result = await self.execute_stage(stage, stage_context)
                    sprint_results["stages"][stage.value] = result

                    # Update quality summary
                    if result.get("status") == "success":
                        quality_gates = self.state.get("quality_gates", {}).get(stage.value, {})
                        sprint_results["quality_summary"][stage.value] = {
                            "passed": quality_gates.get("passed", False),
                            "quality_score": quality_gates.get("quality_score", 0),
                            "issues_count": len(quality_gates.get("issues", [])),
                        }

                except Exception as e:
                    logger.error(f"Sprint execution failed at stage {stage.value}: {e}")
                    sprint_results["stages"][stage.value] = {
                        "status": "failed",
                        "error": str(e),
                        "stage": stage.value,
                        "timestamp": datetime.now().isoformat(),
                    }

                    # Check if this is a hard gate failure
                    stage_config = self.config["v_model"]["stages"].get(stage.value, {})
                    if stage_config.get("gating") == "hard":
                        self.console.print(
                            f"[red]Hard gate failure at {stage.value}, stopping sprint[/red]"
                        )
                        break

                progress.remove_task(task)

        # Finalize sprint results
        sprint_results["completed_at"] = datetime.now().isoformat()
        sprint_results["agent_performance"] = self.state.get("agent_metrics", {})

        # Calculate overall sprint success
        successful_stages = [
            stage
            for stage, result in sprint_results["stages"].items()
            if result.get("status") == "success"
        ]
        sprint_results["success_rate"] = len(successful_stages) / len(v_model_stages)
        sprint_results["completed_stages"] = successful_stages

        # Final validation decision
        validation_result = sprint_results["stages"].get("validation", {})
        if validation_result.get("status") == "success":
            integration_data = validation_result.get("integration_data", {})
            release_recommendation = integration_data.get("release_recommendation", {})
            sprint_results["final_decision"] = release_recommendation.get(
                "go_no_go_decision", "NO-GO"
            )
            sprint_results["readiness_score"] = release_recommendation.get(
                "overall_readiness_score", 0
            )
        else:
            sprint_results["final_decision"] = "NO-GO"
            sprint_results["readiness_score"] = 0

        self.state["active_story"] = None
        self._save_state()

        return sprint_results

    def get_status(self) -> dict[str, Any]:
        """Get current orchestrator status with SDK metrics.

        Returns:
            Current status information
        """
        return {
            "current_stage": self.current_stage.value,
            "sprint_number": self.state.get("sprint_number", 0),
            "active_story": self.state.get("active_story"),
            "completed_stages": self.state.get("completed_stages", []),
            "agent_metrics": self.state.get("agent_metrics", {}),
            "quality_gates": self.state.get("quality_gates", {}),
            "sdk_config": {
                "agents_initialized": len(self.agents),
                "session_persistence": self.config.get("sdk", {}).get("session_persistence", True),
            },
            "last_updated": self.state.get("updated_at"),
        }

    def display_status(self) -> None:
        """Display current status in a formatted table with SDK information."""
        status = self.get_status()

        table = Table(title="V-Model Orchestrator Status (Claude Code SDK)")
        table.add_column("Property", style="cyan")
        table.add_column("Value", style="white")

        table.add_row("Current Stage", status["current_stage"])
        table.add_row("Sprint Number", str(status["sprint_number"]))

        active_story = status["active_story"]
        story_display = (
            active_story.get("title", "Unknown")
            if isinstance(active_story, dict)
            else str(active_story)
            if active_story
            else "None"
        )
        table.add_row("Active Story", story_display)

        table.add_row(
            "Completed Stages",
            (", ".join(status["completed_stages"][-3:]) if status["completed_stages"] else "None"),
        )

        # SDK status
        sdk_info = status["sdk_config"]
        table.add_row("SDK Mode", "Live")
        table.add_row("Agents Initialized", str(sdk_info["agents_initialized"]))
        table.add_row("Session Persistence", str(sdk_info["session_persistence"]))

        table.add_row("Last Updated", status["last_updated"])

        self.console.print(table)

        # Display quality gates summary if available
        quality_gates = status.get("quality_gates", {})
        if quality_gates:
            quality_table = Table(title="Quality Gates Status")
            quality_table.add_column("Stage", style="cyan")
            quality_table.add_column("Status", style="white")
            quality_table.add_column("Issues", style="yellow")

            for stage, gate_info in quality_gates.items():
                status_symbol = "✓" if gate_info.get("passed", False) else "✗"
                issues_count = len(gate_info.get("issues", []))
                quality_table.add_row(stage, status_symbol, str(issues_count))

            self.console.print(quality_table)

    async def checkpoint(self, name: str, description: str = "") -> dict[str, Any]:
        """Create a checkpoint of current state including SDK session data.

        Args:
            name: Checkpoint name
            description: Checkpoint description

        Returns:
            Checkpoint information
        """
        checkpoint = {
            "name": name,
            "description": description,
            "timestamp": datetime.now().isoformat(),
            "state": self.state.copy(),
            "stage": self.current_stage.value,
            "sdk_config": {
                "agents_count": len(self.agents),
            },
        }

        # Save checkpoint
        checkpoint_dir = self.path_config.checkpoints_dir
        checkpoint_dir.mkdir(parents=True, exist_ok=True)
        checkpoint_path = checkpoint_dir / f"{name}.json"
        checkpoint_path.write_text(json.dumps(checkpoint, indent=2))

        # Update history
        self.state["checkpoint_history"].append(
            {"name": name, "timestamp": checkpoint["timestamp"]}
        )
        self._save_state()

        logger.info(f"Created checkpoint '{name}' with SDK session data")
        return checkpoint

    async def restore_checkpoint(self, name: str) -> bool:
        """Restore from a checkpoint including SDK session state.

        Args:
            name: Checkpoint name

        Returns:
            True if successful
        """
        checkpoint_path = self.path_config.checkpoints_dir / f"{name}.json"
        if not checkpoint_path.exists():
            logger.error(f"Checkpoint '{name}' not found")
            return False

        try:
            checkpoint = json.loads(checkpoint_path.read_text())
            self.state = checkpoint["state"]
            self.current_stage = VModelStage(checkpoint["stage"])

            # Reinitialize agents to restore session state
            self.agents = self._initialize_agents()

            self._save_state()

            logger.info(f"Restored checkpoint '{name}' with SDK session data")
            return True

        except Exception as e:
            logger.error(f"Failed to restore checkpoint '{name}': {e}")
            return False

    def get_agent_performance_summary(self) -> dict[str, Any]:
        """Get summary of agent performance metrics.

        Returns:
            Agent performance summary
        """
        agent_metrics = self.state.get("agent_metrics", {})

        if not agent_metrics:
            return {"message": "No agent performance data available"}

        summary: dict[str, Any] = {
            "total_executions": len(agent_metrics),
            "successful_executions": len(
                [m for m in agent_metrics.values() if m.get("status") == "success"]
            ),
            "average_quality_score": 0,
            "stage_performance": {},
        }

        # Calculate averages
        quality_scores = [
            m.get("quality_score", 0)
            for m in agent_metrics.values()
            if isinstance(m.get("quality_score"), int | float)
        ]
        if quality_scores:
            summary["average_quality_score"] = sum(quality_scores) / len(quality_scores)

        # Per-stage performance
        for stage, metrics in agent_metrics.items():
            summary["stage_performance"][stage] = {
                "last_execution": metrics.get("last_execution"),
                "status": metrics.get("status"),
                "quality_score": metrics.get("quality_score", 0),
                "artifacts_created": metrics.get("artifacts_created", 0),
            }

        return summary
