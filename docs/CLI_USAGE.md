# VeriFlowCC CLI Usage Guide

## Overview

VeriFlowCC provides a command-line interface for orchestrating Agile V-Model development workflows with Claude-Code AI integration.

## Authentication Requirements

VeriFlowCC requires Claude Code authentication to function properly. Users must configure their authentication method through VeriFlow's guidelines before using this tool. The system supports flexible authentication approaches without requiring specific setup steps in this documentation.

## Installation

```bash
# Install with UV (recommended - 10-100x faster than pip)
uv sync

# Or install in development mode
uv pip install -e .
```

## Commands

### Initialize Project

```bash
verifflowcc init [--force]
```

Creates the `.agilevv/` directory structure with:

- `config.yaml` - V-Model configuration and agent settings
- `state.json` - Project state tracking
- `backlog.md` - Product backlog template
- `architecture.md` - System architecture template

Options:

- `--force`: Reinitialize existing project

### Plan Sprint

```bash
verifflowcc plan [--story-id ID]
```

Selects a user story from the backlog and triggers Claude-Code subagents for requirements analysis.

Options:

- `--story-id`: Select specific story by ID (non-interactive)

Example:

```bash
# Interactive story selection
verifflowcc plan

# Direct story selection
verifflowcc plan --story-id 3
```

### Execute Sprint

```bash
verifflowcc sprint --story "User authentication feature"
```

Orchestrates the complete V-Model cycle:

1. Requirements Analysis (Claude-Code subagent)
1. Architecture Design
1. Implementation
1. Unit Testing
1. Integration Testing
1. System Testing
1. Validation

Options:

- `--story, -s`: User story to implement (required)

Example:

```bash
verifflowcc sprint -s "As a user, I want to login with email and password"
```

### Check Status

```bash
verifflowcc status [--verbose]
```

Displays current project state:

- Active sprint and story
- Current V-Model stage
- Completed stages
- Recent checkpoints

Options:

- `--verbose, -v`: Show detailed status

### Validate Project

```bash
verifflowcc validate [--tests-only] [--coverage-only] [--stage STAGE]
```

Runs validation checks:

- Test suite execution
- Coverage analysis
- Stage-specific validation

Options:

- `--tests-only`: Run only tests
- `--coverage-only`: Check only coverage
- `--stage`: Validate specific stage

### Manage Checkpoints

```bash
# Create checkpoint
verifflowcc checkpoint --name "feature-complete" --message "Authentication implemented"

# List checkpoints
verifflowcc checkpoint list

# Restore checkpoint
verifflowcc checkpoint restore checkpoint_name [--force]
```

Git-integrated checkpointing:

- Creates git commits and tags
- Saves state snapshots
- Enables rollback capability

Options:

- `--name, -n`: Custom checkpoint name
- `--message, -m`: Checkpoint description
- `--force`: Force restore with uncommitted changes

## Workflow Examples

### Complete Feature Development

```bash
# 1. Initialize project
verifflowcc init

# 2. Add stories to backlog
echo "- [ ] User login with email/password" >> .agilevv/backlog.md
echo "- [ ] Password reset functionality" >> .agilevv/backlog.md

# 3. Plan sprint
verifflowcc plan

# 4. Execute sprint
verifflowcc sprint -s "User login with email/password"

# 5. Create checkpoint
verifflowcc checkpoint -n "login-complete" -m "Basic authentication working"

# 6. Validate
verifflowcc validate

# 7. Check status
verifflowcc status
```

### Recovery from Failure

```bash
# List available checkpoints
verifflowcc checkpoint list

# Check current status
verifflowcc status

# Restore to previous checkpoint
verifflowcc checkpoint restore login-complete

# Resume development
verifflowcc sprint -s "Fix authentication bug"
```

## Configuration

### V-Model Settings

Edit `.agilevv/config.yaml`:

```yaml
v_model:
  gating_mode: soft # hard, soft, or off
  stages:
    requirements:
      enabled: true
      gating: hard
    design:
      enabled: true
      gating: hard
    coding:
      enabled: true
      gating: soft
    unit_testing:
      enabled: true
      gating: hard
```

### Agent Configuration

```yaml
agents:
  requirements_analyst:
    model: claude-3-sonnet
    max_tokens: 4000
  architect:
    model: claude-3-sonnet
    max_tokens: 4000
  developer:
    model: claude-3-sonnet
    max_tokens: 8000
  qa_tester:
    model: claude-3-sonnet
    max_tokens: 4000
```

## Advanced Features

### Claude-Code Integration

VeriFlowCC integrates with Claude-Code subagents for:

- Requirements elaboration and INVEST criteria validation
- Architecture design with C4 diagrams
- Code generation following design specs
- Test creation and execution
- Documentation generation

### Git Integration

Automatic git operations:

- Checkpoint commits with meaningful messages
- Tagged releases for each checkpoint
- Branch management for features
- Rollback capability with state preservation

### Progress Tracking

Real-time progress visualization:

- Spinner animations for long operations
- Progress bars for stage execution
- Rich console output with colors
- Interactive prompts for user input

## Troubleshooting

### Common Issues

1. **Project not initialized**

   ```bash
   verifflowcc init
   ```

1. **No stories in backlog**

   - Edit `.agilevv/backlog.md`
   - Add stories with format: `- [ ] Story description`

1. **Checkpoint restore fails**

   - Check git status: `git status`
   - Commit or stash changes
   - Use `--force` flag if needed

1. **Import errors**

   ```bash
   uv sync
   uv run pytest
   ```

## Best Practices

1. **Regular Checkpointing**: Create checkpoints after each successful stage
1. **Clear Story Descriptions**: Use INVEST criteria for stories
1. **Incremental Development**: Complete one story per sprint
1. **Validation First**: Run validation before creating checkpoints
1. **Git Integration**: Keep git repository clean and organized

## Environment Variables

- `VERIFFLOWCC_CONFIG`: Custom config path
- `VERIFFLOWCC_DEBUG`: Enable debug logging
- `AGILEVV_BASE_DIR`: Custom base directory for project structure

## Exit Codes

- `0`: Success
- `1`: General error
- `2`: Validation failure
- `130`: User interruption (Ctrl+C)

## Getting Help

```bash
# General help
verifflowcc --help

# Command-specific help
verifflowcc sprint --help
verifflowcc checkpoint --help
```

For more information, see the [project documentation](https://github.com/your-org/verifflowcc).
