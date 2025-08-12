"""Orchestrator for V-Model stage execution."""

import json
from collections.abc import Callable
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, cast

from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from verifflowcc.agents import RequirementsAnalystAgent


class VModelStage(Enum):
    """V-Model stages enumeration."""

    PLANNING = "planning"
    REQUIREMENTS = "requirements"
    DESIGN = "design"
    CODING = "coding"
    UNIT_TESTING = "unit_testing"
    INTEGRATION_TESTING = "integration_testing"
    SYSTEM_TESTING = "system_testing"
    VALIDATION = "validation"


class GatingMode(Enum):
    """Gating control modes."""

    HARD = "hard"  # Must pass to proceed
    SOFT = "soft"  # Warning but can proceed
    OFF = "off"  # No gating


class Orchestrator:
    """Orchestrates V-Model workflow execution with stage transitions and gating."""

    def __init__(self, config_path: Path | None = None):
        """Initialize the Orchestrator.

        Args:
            config_path: Path to configuration file
        """
        self.config_path = config_path or Path(".agilevv/config.yaml")
        self.state_path = Path(".agilevv/state.json")
        self.console = Console()
        self.current_stage = VModelStage.PLANNING
        self.state = self._load_state()
        self.config = self._load_config()
        self.agents = self._initialize_agents()
        self.stage_callbacks: dict[VModelStage, list[Callable]] = {}

    def _load_state(self) -> dict[str, Any]:
        """Load project state from state.json."""
        if self.state_path.exists():
            return cast(dict[str, Any], json.loads(self.state_path.read_text()))
        return {
            "current_stage": VModelStage.PLANNING.value,
            "sprint_number": 0,
            "completed_stages": [],
            "active_story": None,
            "stage_artifacts": {},
            "checkpoint_history": [],
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
        }

    def _save_state(self) -> None:
        """Save project state to state.json."""
        self.state["updated_at"] = datetime.now().isoformat()
        self.state["current_stage"] = self.current_stage.value
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        self.state_path.write_text(json.dumps(self.state, indent=2))

    def _load_config(self) -> dict[str, Any]:
        """Load configuration from config.yaml."""
        if self.config_path.exists():
            import yaml

            return cast(dict[str, Any], yaml.safe_load(self.config_path.read_text()))
        return {
            "v_model": {
                "gating_mode": "soft",
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
                "requirements_analyst": {"model": "claude-3-sonnet", "max_tokens": 4000},
                "architect": {"model": "claude-3-sonnet", "max_tokens": 4000},
                "developer": {"model": "claude-3-sonnet", "max_tokens": 8000},
                "qa_tester": {"model": "claude-3-sonnet", "max_tokens": 4000},
            },
        }

    def _initialize_agents(self) -> dict[str, Any]:
        """Initialize all subagents."""
        return {
            "requirements_analyst": RequirementsAnalystAgent(self.config_path),
            # Additional agents would be initialized here
            # "architect": ArchitectAgent(self.config_path),
            # "developer": DeveloperAgent(self.config_path),
            # "qa_tester": QATesterAgent(self.config_path)
        }

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
        """Execute a specific V-Model stage.

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

        # Execute stage-specific logic
        result = await self._execute_stage_logic(stage, context)

        # Apply gating controls
        gating_result = await self._apply_gating(stage, result)

        if gating_result["passed"]:
            self.state["completed_stages"].append(stage.value)
            self.console.print(f"[green]✓ Stage {stage.value} completed successfully[/green]")
        else:
            if stage_config.get("gating") == "hard":
                self.console.print(f"[red]✗ Stage {stage.value} failed gating controls[/red]")
                raise Exception(f"Stage {stage.value} failed hard gating")
            else:
                self.console.print(
                    f"[yellow]⚠ Stage {stage.value} has warnings but proceeding[/yellow]"
                )

        # Execute callbacks
        for callback in self.stage_callbacks.get(stage, []):
            await callback(result)

        # Save artifacts
        self.state["stage_artifacts"][stage.value] = result.get("artifacts", {})
        self._save_state()

        return result

    async def _execute_stage_logic(
        self, stage: VModelStage, context: dict[str, Any]
    ) -> dict[str, Any]:
        """Execute the actual logic for a stage.

        Args:
            stage: Stage to execute
            context: Execution context

        Returns:
            Stage execution results
        """
        if stage == VModelStage.REQUIREMENTS:
            agent = self.agents.get("requirements_analyst")
            if agent:
                result = await agent.execute(**context)
                return cast(dict[str, Any], result)

        # Placeholder for other stages
        return {"status": "success", "stage": stage.value, "artifacts": {}, "metrics": {}}

    async def _apply_gating(self, stage: VModelStage, result: dict[str, Any]) -> dict[str, Any]:
        """Apply gating controls to stage results.

        Args:
            stage: Current stage
            result: Stage execution results

        Returns:
            Gating results
        """
        stage_config = self.config["v_model"]["stages"].get(stage.value, {})
        gating_mode = stage_config.get("gating", "soft")

        if gating_mode == "off":
            return {"passed": True, "mode": "off"}

        # Check stage-specific criteria
        criteria_met = True
        issues = []

        if stage == VModelStage.REQUIREMENTS:
            # Check if requirements are complete
            if not result.get("result", {}).get("acceptance_criteria"):
                criteria_met = False
                issues.append("Missing acceptance criteria")
        elif stage == VModelStage.UNIT_TESTING:
            # Check test coverage
            coverage = result.get("metrics", {}).get("coverage", 0)
            if coverage < 80:
                criteria_met = False
                issues.append(f"Test coverage {coverage}% below 80% threshold")

        return {"passed": criteria_met, "mode": gating_mode, "issues": issues}

    async def run_sprint(self, story: dict[str, Any]) -> dict[str, Any]:
        """Run a complete sprint through all V-Model stages.

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
            "started_at": datetime.now().isoformat(),
        }

        # V-Model left side (requirements down to coding)
        left_stages = [
            VModelStage.PLANNING,
            VModelStage.REQUIREMENTS,
            VModelStage.DESIGN,
            VModelStage.CODING,
        ]

        # V-Model right side (testing up to validation)
        right_stages = [
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
            # Execute left side of V
            for stage in left_stages:
                task = progress.add_task(f"Executing {stage.value}...", total=None)
                try:
                    result = await self.execute_stage(stage, {"story": story})
                    sprint_results["stages"][stage.value] = result
                except Exception as e:
                    sprint_results["stages"][stage.value] = {"status": "failed", "error": str(e)}
                    if self.config["v_model"]["stages"][stage.value].get("gating") == "hard":
                        break
                progress.remove_task(task)

            # Execute right side of V
            for stage in right_stages:
                task = progress.add_task(f"Executing {stage.value}...", total=None)
                try:
                    result = await self.execute_stage(stage, sprint_results)
                    sprint_results["stages"][stage.value] = result
                except Exception as e:
                    sprint_results["stages"][stage.value] = {"status": "failed", "error": str(e)}
                    if self.config["v_model"]["stages"][stage.value].get("gating") == "hard":
                        break
                progress.remove_task(task)

        sprint_results["completed_at"] = datetime.now().isoformat()
        self.state["active_story"] = None
        self._save_state()

        return sprint_results

    def get_status(self) -> dict[str, Any]:
        """Get current orchestrator status.

        Returns:
            Current status information
        """
        return {
            "current_stage": self.current_stage.value,
            "sprint_number": self.state.get("sprint_number", 0),
            "active_story": self.state.get("active_story"),
            "completed_stages": self.state.get("completed_stages", []),
            "last_updated": self.state.get("updated_at"),
        }

    def display_status(self) -> None:
        """Display current status in a formatted table."""
        status = self.get_status()

        table = Table(title="V-Model Orchestrator Status")
        table.add_column("Property", style="cyan")
        table.add_column("Value", style="white")

        table.add_row("Current Stage", status["current_stage"])
        table.add_row("Sprint Number", str(status["sprint_number"]))
        table.add_row(
            "Active Story", status["active_story"]["title"] if status["active_story"] else "None"
        )
        table.add_row(
            "Completed Stages",
            ", ".join(status["completed_stages"][-3:]) if status["completed_stages"] else "None",
        )
        table.add_row("Last Updated", status["last_updated"])

        self.console.print(table)

    async def checkpoint(self, name: str, description: str = "") -> dict[str, Any]:
        """Create a checkpoint of current state.

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
        }

        # Save checkpoint
        checkpoint_dir = Path(".agilevv/checkpoints")
        checkpoint_dir.mkdir(parents=True, exist_ok=True)
        checkpoint_path = checkpoint_dir / f"{name}.json"
        checkpoint_path.write_text(json.dumps(checkpoint, indent=2))

        # Update history
        self.state["checkpoint_history"].append(
            {"name": name, "timestamp": checkpoint["timestamp"]}
        )
        self._save_state()

        return checkpoint

    async def restore_checkpoint(self, name: str) -> bool:
        """Restore from a checkpoint.

        Args:
            name: Checkpoint name

        Returns:
            True if successful
        """
        checkpoint_path = Path(f".agilevv/checkpoints/{name}.json")
        if not checkpoint_path.exists():
            return False

        checkpoint = json.loads(checkpoint_path.read_text())
        self.state = checkpoint["state"]
        self.current_stage = VModelStage(checkpoint["stage"])
        self._save_state()

        return True
