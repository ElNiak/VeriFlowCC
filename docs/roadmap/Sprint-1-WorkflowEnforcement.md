# Sprint 1: Workflow Enforcement Integration

**Sprint Duration:** 1 week (Week 2)
**Sprint Goal:** Implement Agent-OS pause-resume functionality with state management
**Sprint Type:** Core Feature Implementation
**Prerequisites:** Sprint 0.5 completed (foundation in place)

## Sprint Objectives

This sprint focuses on integrating the core workflow enforcement features from Agent-OS, enabling pause-resume capabilities, state persistence, and gate-based progression control. This is the heart of the V-Model enforcement system.

## User Stories & Tasks

### Story 1: Finite State Machine Implementation
**As a** developer
**I want** persistent workflow state management
**So that** I can pause work and resume exactly where I left off

**Tasks:**
- [ ] Create `.vv/state.json` structure (3h)
- [ ] Implement StateManager class with Pydantic validation (3h)
- [ ] Add state transition logic following V-Model rules (2h)
- [ ] Implement file locking for concurrent access safety (1h)
- [ ] Create state recovery mechanisms (1h)

**Acceptance Criteria:**
- State persists across CLI sessions
- Invalid transitions are blocked with clear errors
- State can be inspected via `vv status` command
- Concurrent access is handled safely
- State corruption is detected and recoverable

### Story 2: Hook System Integration
**As a** system
**I want** tool usage controlled by current stage
**So that** agents cannot perform inappropriate actions

**Tasks:**
- [ ] Set up hook directory structure (1h)
- [ ] Port Agent-OS UX hooks (2h)
- [ ] Implement gate enforcement hooks (3h)
- [ ] Configure hook precedence and timeout (1h)
- [ ] Add hook testing framework (2h)

**Acceptance Criteria:**
- Hooks prevent unauthorized tool usage
- UX provides clear feedback on operations
- Hook failures are logged and recoverable
- Performance overhead < 100ms per operation
- All hooks have unit tests

### Story 3: CLI Extension with VV Commands
**As a** user
**I want** intuitive commands to control workflow
**So that** I can easily manage sprint execution

**Tasks:**
- [ ] Add `vv` command group to Typer CLI (2h)
- [ ] Implement `vv sprint-init <ID>` command (1h)
- [ ] Implement `vv resume` command (2h)
- [ ] Implement `vv status` command (1h)
- [ ] Implement `vv rollback` command (2h)
- [ ] Add colorful progress indicators (1h)

**Acceptance Criteria:**
- All commands have help text and examples
- Commands provide clear feedback
- Error messages are actionable
- Progress is visually indicated
- Commands integrate with existing CLI

### Story 4: Checkpoint and Rollback System
**As a** developer
**I want** to rollback to previous states
**So that** I can recover from failures or wrong decisions

**Tasks:**
- [ ] Implement Git-based checkpointing (2h)
- [ ] Create checkpoint at each gate pass (1h)
- [ ] Add rollback logic with state restoration (2h)
- [ ] Implement rollback confirmation flow (1h)
- [ ] Add checkpoint management commands (1h)

**Acceptance Criteria:**
- Checkpoints created automatically at gates
- Rollback restores both code and state
- User must confirm destructive rollbacks
- Checkpoint history is viewable
- Old checkpoints can be pruned

## Technical Implementation Details

### State.json Schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "version": {
      "type": "string",
      "const": "1.0.0"
    },
    "sprint_id": {
      "type": "string",
      "pattern": "^[A-Z0-9-]+$"
    },
    "session_id": {
      "type": "string",
      "format": "uuid"
    },
    "current_stage": {
      "type": "string",
      "enum": ["init", "planning", "requirements", "design", "coding", "testing", "validation", "complete"]
    },
    "previous_stage": {
      "type": ["string", "null"]
    },
    "gates_passed": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "gate": {"type": "string"},
          "timestamp": {"type": "string", "format": "date-time"},
          "commit_sha": {"type": "string"}
        }
      }
    },
    "artifacts": {
      "type": "object",
      "additionalProperties": {
        "type": "string"
      }
    },
    "checkpoints": {
      "type": "array",
      "items": {
        "type": "string"
      }
    },
    "locked": {
      "type": "boolean"
    },
    "created_at": {
      "type": "string",
      "format": "date-time"
    },
    "updated_at": {
      "type": "string",
      "format": "date-time"
    }
  },
  "required": ["version", "sprint_id", "session_id", "current_stage", "created_at", "updated_at"]
}
```

### Hook Implementation Examples

```bash
#!/bin/bash
# ~/.claude/hooks/before_edit.d/10-vv-gate-check.sh

# Load current state
STATE_FILE="${HOME}/.vv/state.json"
if [[ ! -f "$STATE_FILE" ]]; then
    echo "⚠️  No active VeriFlowCC session" >&2
    exit 0  # Allow if no session
fi

CURRENT_STAGE=$(jq -r '.current_stage' "$STATE_FILE")

# Define allowed operations per stage
case "$CURRENT_STAGE" in
    "planning"|"requirements"|"design")
        echo "❌ Cannot edit files during $CURRENT_STAGE stage" >&2
        echo "   Move to coding stage first: vv advance" >&2
        exit 1
        ;;
    "coding")
        echo "✅ File editing allowed in coding stage" >&2
        ;;
    "testing"|"validation")
        echo "⚠️  Warning: Editing during $CURRENT_STAGE may invalidate tests" >&2
        read -p "Continue? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
        ;;
    *)
        echo "❓ Unknown stage: $CURRENT_STAGE" >&2
        ;;
esac
```

### CLI Command Specifications

```python
# verifflowcc/cli/vv_commands.py
import typer
from rich.console import Console
from rich.progress import Progress
from pathlib import Path

app = typer.Typer(help="VeriFlowCC workflow commands")
console = Console()

@app.command()
def sprint_init(
    sprint_id: str = typer.Argument(..., help="Sprint identifier (e.g., S01)"),
    force: bool = typer.Option(False, "--force", "-f", help="Force overwrite existing sprint")
):
    """Initialize a new sprint with VeriFlowCC workflow"""
    with console.status(f"Initializing sprint {sprint_id}..."):
        # Create sprint directory structure
        sprint_dir = Path(f"sprints/{sprint_id}")
        if sprint_dir.exists() and not force:
            console.print(f"[red]Sprint {sprint_id} already exists![/red]")
            raise typer.Exit(1)

        # Initialize state
        state = WorkflowState(
            sprint_id=sprint_id,
            session_id=str(uuid.uuid4()),
            current_stage=VModelStage.INIT,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )

        # Save state
        state_manager = StateManager()
        state_manager.save(state)

        # Create directory structure
        create_sprint_structure(sprint_dir)

        console.print(f"[green]✓[/green] Sprint {sprint_id} initialized")
        console.print(f"[blue]Next:[/blue] Run 'vv resume' to start planning")

@app.command()
def resume():
    """Resume workflow from current state"""
    state_manager = StateManager()
    state = state_manager.load()

    if not state:
        console.print("[red]No active session found![/red]")
        console.print("[yellow]Initialize a sprint first:[/yellow] vv sprint-init S01")
        raise typer.Exit(1)

    console.print(f"[green]Resuming sprint {state.sprint_id}[/green]")
    console.print(f"Current stage: [blue]{state.current_stage}[/blue]")

    # Launch appropriate agent based on stage
    agent = get_agent_for_stage(state.current_stage)

    with Progress() as progress:
        task = progress.add_task(f"Running {agent}...", total=100)
        result = run_agent(agent, state)
        progress.update(task, completed=100)

    if result.success:
        # Advance to next stage
        next_stage = get_next_stage(state.current_stage)
        state_manager.transition(next_stage)
        console.print(f"[green]✓[/green] Advanced to {next_stage}")
    else:
        console.print(f"[red]✗[/red] Stage failed: {result.error}")

@app.command()
def status():
    """Show current workflow status"""
    state_manager = StateManager()
    state = state_manager.load()

    if not state:
        console.print("[yellow]No active session[/yellow]")
        return

    # Display status table
    from rich.table import Table

    table = Table(title=f"Sprint {state.sprint_id} Status")
    table.add_column("Property", style="cyan")
    table.add_column("Value", style="white")

    table.add_row("Session ID", state.session_id[:8])
    table.add_row("Current Stage", state.current_stage)
    table.add_row("Gates Passed", str(len(state.gates_passed)))
    table.add_row("Checkpoints", str(len(state.checkpoints)))
    table.add_row("Last Updated", state.updated_at.strftime("%Y-%m-%d %H:%M"))

    console.print(table)

    # Show stage progression
    stages = ["planning", "requirements", "design", "coding", "testing", "validation", "complete"]
    current_idx = stages.index(state.current_stage) if state.current_stage in stages else -1

    console.print("\n[bold]Progress:[/bold]")
    for i, stage in enumerate(stages):
        if i < current_idx:
            console.print(f"  [green]✓[/green] {stage}")
        elif i == current_idx:
            console.print(f"  [blue]●[/blue] {stage} [italic](current)[/italic]")
        else:
            console.print(f"  [dim]○[/dim] {stage}")
```

## Testing Strategy

### Unit Tests
```python
# tests/test_state_manager.py
def test_state_persistence():
    """Test state saves and loads correctly"""
    manager = StateManager()
    state = WorkflowState(...)
    manager.save(state)
    loaded = manager.load()
    assert loaded.sprint_id == state.sprint_id

def test_invalid_transition():
    """Test invalid transitions are blocked"""
    manager = StateManager()
    state = WorkflowState(current_stage="planning")
    with pytest.raises(ValueError):
        manager.transition("testing")  # Can't skip stages

def test_concurrent_access():
    """Test file locking prevents corruption"""
    # Simulate concurrent access
    # Verify only one succeeds
```

### Integration Tests
```bash
# tests/integration/test_workflow.sh
#!/bin/bash

# Test full workflow
vv sprint-init TEST-01
vv resume  # Planning
vv resume  # Requirements
vv status  # Check state
vv rollback  # Go back
vv resume  # Requirements again
```

## Definition of Done

### Sprint Level
- [ ] All stories completed and tested
- [ ] Integration tests passing
- [ ] Documentation updated
- [ ] Performance targets met (<100ms hook overhead)
- [ ] No critical bugs

### Story Level
- [ ] Implementation complete
- [ ] Unit tests passing
- [ ] Code reviewed
- [ ] Documentation updated
- [ ] Integrated with main branch

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| State corruption | High | File locking, validation, backups |
| Hook conflicts | Medium | Clear precedence, timeout handling |
| Performance degradation | Medium | Profiling, caching, lazy loading |
| Complex rollback scenarios | High | Comprehensive testing, clear warnings |

## Dependencies

- Sprint 0.5 completion (foundation)
- Git installed and configured
- jq for JSON parsing in hooks
- Python 3.10+ with required packages

## Next Sprint Preview

**Sprint 2: Helper Agents & Tooling**
- Import Agent-OS helper agents
- Convert to YAML format
- Integrate with primary agents
- Implement memory hierarchy
- Measure token reduction

## Success Metrics

- State persists correctly 100% of time
- Hooks block inappropriate operations
- CLI commands work intuitively
- Rollback restores complete state
- Performance overhead < 100ms

## Notes

1. Focus on robustness - this is core functionality
2. Test edge cases thoroughly
3. Make error messages helpful
4. Document hook behavior clearly
5. Consider user experience in all interactions
