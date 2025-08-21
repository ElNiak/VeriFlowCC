# API Specification

```
This is the API specification for the spec detailed in @.agilevv/specs/2025-08-20-worktree-isolation/spec.md
```

## Hook Endpoints

### UserPromptSubmit Hook: Worktree Validator

**Purpose:** Validate that Claude Code session is operating within proper worktree boundaries and inject worktree context
**Hook Path:** `.claude/hooks/UserPromptSubmit/worktree_validator.py`
**Parameters:**

- `prompt`: User's input prompt
- `context`: Current session context
- `environment`: Environment variables including CLAUDE_PROJECT_DIR
  **Response:** Modified prompt with worktree context injection or error blocking
  **Errors:**
- `WorktreeNotDetectedError`: When launched outside a git worktree
- `InvalidWorktreePathError`: When worktree path is invalid or corrupted

### PreToolUse Hook: Worktree Guard

**Purpose:** Intercept and validate all tool operations against worktree boundaries before execution
**Hook Path:** `.claude/hooks/PreToolUse/worktree_guard.py`
**Parameters:**

- `tool_name`: Name of the tool being invoked
- `tool_args`: Arguments passed to the tool
- `file_paths`: Any file paths involved in the operation
  **Response:** Allow/block decision with path validation results
  **Errors:**
- `CrossWorktreeBoundaryError`: When operation would access files outside worktree
- `PathTraversalAttemptError`: When path contains directory traversal attempts

## Hook Controllers

### WorktreeDetector

**Purpose:** Core logic for detecting and validating git worktree environment
**Methods:**

- `detect_worktree_root()`: Returns the root path of current worktree
- `is_path_within_worktree(path)`: Validates if given path is within worktree boundaries
- `get_worktree_info()`: Returns metadata about current worktree (branch, root, etc.)

### PathValidator

**Purpose:** Comprehensive path validation against worktree constraints
**Methods:**

- `validate_file_path(path)`: Checks if file path is allowed within worktree
- `resolve_relative_paths(paths)`: Resolves and validates relative path references
- `check_boundary_violation(operation, paths)`: Detects boundary crossing attempts

### ConfigurationManager

**Purpose:** Manage worktree-specific configuration and environment setup
**Methods:**

- `load_worktree_config()`: Load configuration specific to current worktree
- `inherit_main_config()`: Inherit settings from main repository
- `set_environment_variables()`: Configure CLAUDE_PROJECT_DIR and related vars

## Integration APIs

### VeriFlowCC Agent Integration

**Purpose:** Ensure all V-Model agents respect worktree boundaries
**Enhanced Methods:**

- `agent_factory.create_agent()`: Enhanced to pass worktree constraints
- `orchestrator.execute_stage()`: Validates stage operations against worktree
- `path_config.get_project_root()`: Returns worktree root instead of repo root

### Git Operations Integration

**Purpose:** Integrate worktree detection with existing git operations
**Enhanced APIs:**

- `git_integration.get_repository_root()`: Worktree-aware repository detection
- `git_integration.validate_git_operation()`: Ensure git commands stay within worktree
- `git_integration.get_current_branch()`: Return worktree-specific branch information

This API specification ensures consistent interfaces for worktree isolation while maintaining compatibility with the existing VeriFlowCC hook and agent architecture.
