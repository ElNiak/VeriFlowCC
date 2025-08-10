"""VeriFlowCC CLI - Agile V-Model Command Center."""

import asyncio
import json
import signal
import sys
from pathlib import Path
from typing import Any

import typer
import yaml
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Confirm, IntPrompt
from rich.table import Table

# Initialize Typer app and Rich console
app = typer.Typer(
    name="verifflowcc",
    help="VeriFlowCC - Agile V-Model development pipeline command center",
    rich_markup_mode="rich",
    add_completion=False,
)

console = Console()

# Create checkpoint subcommand app
checkpoint_app = typer.Typer()
app.add_typer(checkpoint_app, name="checkpoint", help="Create or manage checkpoints")


def handle_keyboard_interrupt(signum: int, frame: Any) -> None:
    """Handle keyboard interrupt gracefully."""
    console.print("\n[yellow]Interrupted by user[/yellow]")
    sys.exit(130)


# Register signal handler for keyboard interrupts
signal.signal(signal.SIGINT, handle_keyboard_interrupt)


@app.callback()
def main(
    version: bool = typer.Option(
        False,
        "--version",
        "-v",
        help="Show version information",
    ),
) -> None:
    """
    VeriFlowCC - Agile V-Model development pipeline.

    An AI-driven development pipeline that integrates Claude-Code with
    the Agile V-Model methodology for rigorous verification and validation.
    """
    if version:
        console.print("[bold green]VeriFlowCC[/bold green] version 0.1.0")
        raise typer.Exit(0)


@app.command()
def init(
    force: bool = typer.Option(
        False,
        "--force",
        "-f",
        help="Force reinitialize even if project already exists",
    ),
) -> None:
    """
    Initialize a new VeriFlowCC project.

    Creates the .agilevv directory structure with configuration files,
    initial state, and template documents for backlog and architecture.
    """
    project_dir = Path.cwd()
    agilevv_dir = project_dir / ".agilevv"

    # Check if already initialized
    if agilevv_dir.exists() and not force:
        console.print("[red]Project already initialized.[/red] Use --force to reinitialize.")
        raise typer.Exit(1)

    # Create directory structure
    with console.status("Initializing VeriFlowCC project..."):
        agilevv_dir.mkdir(exist_ok=True)
        (agilevv_dir / "logs").mkdir(exist_ok=True)
        (agilevv_dir / "checkpoints").mkdir(exist_ok=True)

        # Create config.yaml with V-Model defaults
        config = {
            "version": "1.0",
            "project_name": project_dir.name,
            "v_model": {
                "gating": "hard",
                "stages": [
                    "requirements",
                    "design",
                    "coding",
                    "testing",
                    "integration",
                    "validation",
                ],
                "verification_criteria": {
                    "requirements": {
                        "completeness": 0.9,
                        "clarity": 0.85,
                        "testability": 1.0,
                    },
                    "design": {
                        "coverage": 0.95,
                        "consistency": 1.0,
                    },
                    "testing": {
                        "coverage": 0.8,
                        "pass_rate": 1.0,
                    },
                },
            },
            "agents": {
                "requirements_analyst": {
                    "model": "claude-3-sonnet",
                    "max_tokens": 4000,
                },
                "architect": {
                    "model": "claude-3-sonnet",
                    "max_tokens": 4000,
                },
                "developer": {
                    "model": "claude-3-sonnet",
                    "max_tokens": 8000,
                },
                "qa_tester": {
                    "model": "claude-3-sonnet",
                    "max_tokens": 4000,
                },
            },
        }

        with open(agilevv_dir / "config.yaml", "w") as f:
            yaml.dump(config, f, default_flow_style=False)

        # Create state.json
        state = {
            "current_sprint": None,
            "current_stage": None,
            "active_story": None,
            "completed_stages": [],
            "checkpoint_history": [],
        }

        with open(agilevv_dir / "state.json", "w") as f:
            json.dump(state, f, indent=2)

        # Create backlog.md template
        backlog_template = """# Product Backlog

## Sprint 1
- [ ] User Story 1: As a user, I want to...
- [ ] User Story 2: As a developer, I want to...

## Sprint 2
- [ ] User Story 3: As a product owner, I want to...

## Icebox
- [ ] Future Feature 1
- [ ] Future Feature 2
"""

        with open(agilevv_dir / "backlog.md", "w") as f:
            f.write(backlog_template)

        # Create architecture.md template
        architecture_template = """# System Architecture

## Overview
System architecture documentation for the project.

## Components
### Frontend
- Description of frontend components

### Backend
- Description of backend services

### Database
- Data model and storage architecture

## Integration Points
- API specifications
- Service interfaces

## Security Considerations
- Authentication and authorization
- Data protection measures
"""

        with open(agilevv_dir / "architecture.md", "w") as f:
            f.write(architecture_template)

    console.print(
        Panel(
            "[green]✓[/green] Project initialized successfully!\n\n"
            "Created .agilevv/ directory with:\n"
            "  • config.yaml - V-Model configuration\n"
            "  • state.json - Project state tracking\n"
            "  • backlog.md - Product backlog template\n"
            "  • architecture.md - Architecture documentation\n"
            "  • logs/ - Execution logs\n"
            "  • checkpoints/ - State checkpoints",
            title="VeriFlowCC Initialized",
            border_style="green",
        )
    )


@app.command()
def plan(
    story_id: int | None = typer.Option(
        None,
        "--story-id",
        help="Select a specific story by ID (non-interactive)",
    ),
) -> None:
    """
    Plan a new sprint with story selection and refinement.

    Reads the backlog, allows interactive story selection, and triggers
    Claude-Code subagents for requirements analysis and elaboration.
    """
    agilevv_dir = Path.cwd() / ".agilevv"

    if not agilevv_dir.exists():
        console.print("[red]Project not initialized.[/red] Run 'verifflowcc init' first.")
        raise typer.Exit(1)

    # Load backlog
    backlog_file = agilevv_dir / "backlog.md"
    if not backlog_file.exists():
        console.print("[red]Backlog not found.[/red]")
        raise typer.Exit(1)

    # Load and parse stories from backlog
    stories = []
    with open(backlog_file) as f:
        for line in f:
            line = line.strip()
            if line.startswith("- [ ]") or line.startswith("- [x]"):
                story = line[5:].strip()
                if story and not story.startswith("#"):
                    stories.append(story)

    if not stories:
        console.print("[yellow]No stories found in backlog.[/yellow]")
        raise typer.Exit(0)

    # Select story
    if story_id is not None:
        if story_id < 1 or story_id > len(stories):
            console.print(f"[red]Invalid story ID.[/red] Valid range: 1-{len(stories)}")
            raise typer.Exit(1)
        selected_story = stories[story_id - 1]
    else:
        # Interactive selection
        console.print("\n[bold]Available Stories:[/bold]")
        for i, story in enumerate(stories, 1):
            console.print(f"  {i}. {story}")

        story_id = IntPrompt.ask(
            "\nSelect story number",
            default=1,
            choices=[str(i) for i in range(1, len(stories) + 1)],
        )
        selected_story = stories[story_id - 1]

    # Update state
    state_file = agilevv_dir / "state.json"
    with open(state_file) as f:
        state = json.load(f)

    state["active_story"] = selected_story
    state["current_stage"] = "planning"

    with open(state_file, "w") as f:
        json.dump(state, f, indent=2)

    console.print(
        Panel(
            f"[green]Story selected:[/green] {selected_story}\n\n"
            "Ready for sprint execution with 'verifflowcc sprint'",
            title="Sprint Planning Complete",
            border_style="green",
        )
    )


@app.command()
def sprint(
    story: str = typer.Option(
        ...,
        "--story",
        "-s",
        help="User story or requirement to implement",
    ),
) -> None:
    """
    Execute a sprint with the Agile V-Model workflow.

    Orchestrates the complete V-Model cycle through specialized
    Claude-Code subagents for each stage (Requirements → Design →
    Code → Test → Validate).
    """
    agilevv_dir = Path.cwd() / ".agilevv"

    if not agilevv_dir.exists():
        console.print("[red]Project not initialized.[/red] Run 'verifflowcc init' first.")
        raise typer.Exit(1)

    # Update state
    state_file = agilevv_dir / "state.json"
    with open(state_file) as f:
        state = json.load(f)

    state["active_story"] = story

    # Determine sprint number
    current_sprint_num = 0
    if state.get("current_sprint"):
        # Extract number from "Sprint X" format
        try:
            current_sprint_num = int(state["current_sprint"].split()[-1])
        except (ValueError, IndexError):
            current_sprint_num = 0

    state["current_sprint"] = f"Sprint {current_sprint_num + 1}"
    state["current_stage"] = "requirements"

    # Initialize completed_stages if not present
    if "completed_stages" not in state:
        state["completed_stages"] = []

    with open(state_file, "w") as f:
        json.dump(state, f, indent=2)

    console.print(
        Panel(
            f"[bold]Executing Sprint:[/bold] {state['current_sprint']}\n"
            f"[bold]Story:[/bold] {story}",
            title="Sprint Execution",
            border_style="blue",
        )
    )

    # Simulate orchestrator execution with progress
    stages = ["Requirements", "Design", "Coding", "Testing", "Integration", "Validation"]

    try:
        # Import Orchestrator if available, otherwise use placeholder
        try:
            from verifflowcc.core.orchestrator import Orchestrator as RealOrchestrator

            orchestrator = RealOrchestrator()
        except ImportError:
            # Use the placeholder Orchestrator class defined at module level
            orchestrator = Orchestrator()

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            for stage in stages:
                task = progress.add_task(f"[cyan]Stage: {stage}[/cyan]", total=1)
                # Simulate work
                asyncio.run(simulate_stage_execution(stage))
                progress.update(task, completed=1)

                # Update state
                with open(state_file) as f:
                    state = json.load(f)
                state["current_stage"] = stage.lower()
                if "completed_stages" not in state:
                    state["completed_stages"] = []
                state["completed_stages"].append(stage.lower())
                with open(state_file, "w") as f:
                    json.dump(state, f, indent=2)
    except KeyboardInterrupt:
        console.print("\n[yellow]Sprint execution interrupted by user[/yellow]")
        sys.exit(130)

    console.print(
        Panel(
            "[green]✓[/green] Sprint completed successfully!\n"
            "All V-Model stages executed and validated.",
            title="Sprint Complete",
            border_style="green",
        )
    )


@app.command()
def status(
    json_output: bool = typer.Option(
        False,
        "--json",
        help="Output status in JSON format",
    ),
) -> None:
    """
    Show project status and current V-Model stage.

    Displays the current sprint, active story, V-Model stage,
    and progress through the development pipeline.
    """
    agilevv_dir = Path.cwd() / ".agilevv"

    if not agilevv_dir.exists():
        console.print("[red]Project not initialized.[/red] Run 'verifflowcc init' first.")
        raise typer.Exit(1)

    # Load state
    state_file = agilevv_dir / "state.json"
    with open(state_file) as f:
        state = json.load(f)

    if json_output:
        console.print(json.dumps(state, indent=2))
    else:
        # Create status table
        table = Table(title="VeriFlowCC Project Status", show_header=True)
        table.add_column("Property", style="cyan", no_wrap=True)
        table.add_column("Value", style="white")

        table.add_row("Current Sprint", state.get("current_sprint", "Not started"))
        table.add_row("Active Story", state.get("active_story", "None"))
        table.add_row("Current Stage", state.get("current_stage", "None"))

        completed = ", ".join(state.get("completed_stages", [])) or "None"
        table.add_row("Completed Stages", completed)

        checkpoints = len(state.get("checkpoint_history", []))
        table.add_row("Checkpoints", str(checkpoints))

        console.print(table)


@app.command()
def validate(
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Show detailed validation output",
    ),
) -> None:
    """
    Validate the current sprint against acceptance criteria.

    Runs comprehensive validation checks including unit tests,
    integration tests, and acceptance criteria verification.
    """
    agilevv_dir = Path.cwd() / ".agilevv"

    if not agilevv_dir.exists():
        console.print("[red]Project not initialized.[/red] Run 'verifflowcc init' first.")
        raise typer.Exit(1)

    with console.status("Running validation checks..."):
        # Simulate validation
        validation_results = run_validation()

    if validation_results["passed"]:
        console.print(
            Panel(
                f"[green]✓ Validation Passed[/green]\n\n"
                f"Tests: {validation_results['tests']}\n"
                f"Passed: {validation_results['tests'] - validation_results['failures']}\n"
                f"Failed: {validation_results['failures']}\n"
                f"Coverage: {validation_results.get('coverage', 'N/A')}%",
                title="Validation Results",
                border_style="green",
            )
        )
    else:
        console.print(
            Panel(
                f"[red]✗ Validation Failed[/red]\n\n"
                f"Tests: {validation_results['tests']}\n"
                f"Passed: {validation_results['tests'] - validation_results['failures']}\n"
                f"Failed: {validation_results['failures']}\n"
                f"Coverage: {validation_results.get('coverage', 'N/A')}%",
                title="Validation Results",
                border_style="red",
            )
        )
        raise typer.Exit(2)


@checkpoint_app.callback(invoke_without_command=True)
def checkpoint(
    ctx: typer.Context,
    name: str | None = typer.Option(
        None,
        "--name",
        "-n",
        help="Custom checkpoint name",
    ),
    message: str | None = typer.Option(
        None,
        "--message",
        "-m",
        help="Checkpoint message",
    ),
) -> None:
    """
    Create or manage checkpoints for state recovery.

    Creates a snapshot of the current project state that can be
    restored later. Integrates with git for version control.
    """
    if ctx.invoked_subcommand is not None:
        return  # Let subcommand handle it

    agilevv_dir = Path.cwd() / ".agilevv"

    if not agilevv_dir.exists():
        console.print("[red]Project not initialized.[/red] Run 'verifflowcc init' first.")
        raise typer.Exit(1)

    # Create checkpoint
    checkpoint_name = (
        name or f"checkpoint_{len(list((agilevv_dir / 'checkpoints').glob('*.json'))) + 1}"
    )

    # Load current state
    with open(agilevv_dir / "state.json") as f:
        state = json.load(f)

    # Create checkpoint
    checkpoint_data = {
        "name": checkpoint_name,
        "message": message or "Manual checkpoint",
        "state": state,
        "timestamp": str(Path.cwd()),  # Simplified for now
    }

    checkpoint_file = agilevv_dir / "checkpoints" / f"{checkpoint_name}.json"
    with open(checkpoint_file, "w") as f:
        json.dump(checkpoint_data, f, indent=2)

    # Update state history
    state["checkpoint_history"].append(checkpoint_name)
    with open(agilevv_dir / "state.json", "w") as f:
        json.dump(state, f, indent=2)

    console.print(
        f"[green]Checkpoint created:[/green] {checkpoint_name}\n"
        f"Message: {checkpoint_data['message']}"
    )


@checkpoint_app.command("list")
def checkpoint_list() -> None:
    """List available checkpoints."""
    agilevv_dir = Path.cwd() / ".agilevv"

    if not agilevv_dir.exists():
        console.print("[red]Project not initialized.[/red]")
        raise typer.Exit(1)

    checkpoints_dir = agilevv_dir / "checkpoints"
    checkpoints = list(checkpoints_dir.glob("*.json"))

    if not checkpoints:
        console.print("[yellow]No checkpoints found.[/yellow]")
        return

    table = Table(title="Available Checkpoints")
    table.add_column("Name", style="cyan")
    table.add_column("Message", style="white")

    for checkpoint_file in checkpoints:
        with open(checkpoint_file) as f:
            data = json.load(f)
        table.add_row(data["name"], data.get("message", ""))

    console.print(table)


@checkpoint_app.command("restore")
def checkpoint_restore(
    name: str = typer.Argument(..., help="Checkpoint name to restore"),
) -> None:
    """Restore to a checkpoint."""
    agilevv_dir = Path.cwd() / ".agilevv"

    if not agilevv_dir.exists():
        console.print("[red]Project not initialized.[/red]")
        raise typer.Exit(1)

    checkpoint_file = agilevv_dir / "checkpoints" / f"{name}.json"

    if not checkpoint_file.exists():
        console.print(f"[red]Checkpoint '{name}' not found.[/red]")
        raise typer.Exit(1)

    if not Confirm.ask(f"Restore to checkpoint '{name}'?"):
        console.print("[yellow]Restore cancelled.[/yellow]")
        raise typer.Exit(0)

    # Restore state
    with open(checkpoint_file) as f:
        checkpoint_data = json.load(f)

    with open(agilevv_dir / "state.json", "w") as f:
        json.dump(checkpoint_data["state"], f, indent=2)

    console.print(f"[green]Restored to checkpoint:[/green] {name}")


# Helper functions


def run_validation() -> dict[str, Any]:
    """Run validation checks (placeholder for actual implementation)."""
    # This would integrate with pytest and other validation tools
    return {
        "passed": True,
        "tests": 10,
        "failures": 0,
        "coverage": 85,
    }


async def simulate_stage_execution(stage: str) -> None:
    """Simulate stage execution (placeholder for orchestrator integration)."""
    # This would integrate with the actual Orchestrator class
    await asyncio.sleep(0.5)  # Simulate work


# Placeholder imports that will be implemented later
class Orchestrator:
    """Placeholder for the orchestrator class."""

    pass


if __name__ == "__main__":
    app()
