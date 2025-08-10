# Technical Specification

This is the technical specification for the spec detailed in @.claude/specs/2025-08-10-cli-interface/spec.md

## Technical Requirements

### Command Structure

- **Main Application**: Create `verifflowcc/cli.py` as the entry point using Typer framework
- **Command Implementation**: Each command as a separate function decorated with `@app.command()`
- **Async Support**: Use `typer.run()` with asyncio for agent operations
- **Exit Codes**: Proper exit codes (0 for success, 1 for errors, 2 for validation failures)

### Command Specifications

#### `init` Command

- Creates `.agilevv/` directory structure if not exists
- Initializes `config.yaml` with default V-Model settings
- Creates empty `state.json` for state persistence
- Sets up `backlog.md` and `architecture.md` templates
- Integrates with Claude-Code subagents using custom instructions from `.claude/instructions/`
- Options: `--force` to reinitialize existing project

#### `plan` Command

- Reads backlog from `.agilevv/backlog.md`
- Interactive story selection using `typer.prompt()` or numbered menu
- Story refinement with acceptance criteria
- Updates state with selected stories
- Leverages Claude-Code subagents for requirements analysis and story elaboration
- Uses custom agent instructions similar to `.claude/commands/` patterns
- Options: `--story-id` for non-interactive selection

#### `sprint` Command

- Main workflow orchestration command
- Required: `--story` parameter with story description
- Triggers orchestrator to execute V-Model stages
- Shows real-time progress with Rich progress bars
- Captures and displays agent outputs
- Spawns specialized Claude-Code subagents for each V-Model stage (Requirements, Design, Code, Test, Validate)
- Uses custom instructions and prompts from `.claude/instructions/` and Jinja2 templates
- Options: `--stage` to start from specific stage, `--dry-run` for simulation

#### `status` Command

- Reads current state from `.agilevv/state.json`
- Displays formatted table with Rich showing:
  - Current sprint information
  - Active story and stage
  - Completed stages with timestamps
  - Pending stages
  - Any blocking issues
- Options: `--json` for machine-readable output

#### `validate` Command

- Runs validation checks on current sprint
- Executes test suites via pytest integration
- Checks acceptance criteria completion
- Generates validation report
- Updates state with validation results
- Options: `--stage` to validate specific stage, `--fix` to auto-fix issues

#### `checkpoint` Command

- Creates git commit with current state
- Tags with checkpoint name and timestamp
- Saves state snapshot to `.agilevv/checkpoints/`
- Options: `--name` for custom checkpoint name, `--message` for commit message
- Subcommands: `list` to show checkpoints, `restore` to rollback

### UI/UX Specifications

#### Rich Terminal Formatting

- **Progress Bars**: Show stage progression with `rich.progress`
- **Tables**: Format status output with `rich.table`
- **Syntax Highlighting**: Code snippets with `rich.syntax`
- **Panels**: Group related information in bordered panels
- **Console**: Centralized Rich console instance for consistent output

#### Interactive Elements

- **Confirmations**: Use `typer.confirm()` for destructive operations
- **Selections**: Numbered menus for story/option selection
- **Multi-select**: Checkbox-style selection for batch operations
- **Spinners**: Show activity during long operations

#### Error Display

- **Styled Errors**: Red text with error icon for failures
- **Warnings**: Yellow text for non-critical issues
- **Success**: Green text with checkmark for completions
- **Debug Info**: Verbose output with `--verbose` flag

### Integration Requirements

#### Orchestrator Integration

- Import and instantiate `Orchestrator` class from `verifflowcc.core.orchestrator`
- Pass configuration from CLI to orchestrator
- Handle orchestrator events and callbacks
- Stream agent outputs to console

#### State Management

- Read/write operations to `.agilevv/state.json`
- Atomic updates to prevent corruption
- State migration for version changes
- Backup before modifications

#### Agent Communication

- Format agent requests using Pydantic models
- Parse agent responses with validation
- Handle timeouts and retries
- Log all agent interactions

### Performance Criteria

- **Command Response**: < 100ms for simple commands (status, list)
- **Interactive Prompts**: Immediate response to user input
- **Progress Updates**: Real-time streaming of agent outputs
- **State Operations**: < 50ms for read/write operations
- **Graceful Degradation**: Continue with warnings if non-critical components fail

### Error Handling

- **Validation Errors**: Clear messages about what failed validation
- **State Corruption**: Automatic recovery from backup
- **Agent Failures**: Retry logic with exponential backoff
- **Network Issues**: Offline mode for local operations
- **Interrupt Handling**: Graceful shutdown on Ctrl+C with state preservation

### Logging

- **Log Levels**: DEBUG, INFO, WARNING, ERROR, CRITICAL
- **Log Location**: `.agilevv/logs/verifflowcc.log`
- **Format**: Timestamp, level, component, message
- **Console Output**: INFO and above by default, DEBUG with --verbose
