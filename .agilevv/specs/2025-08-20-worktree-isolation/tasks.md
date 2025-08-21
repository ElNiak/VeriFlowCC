# Spec Tasks

These are the tasks to be completed for the spec detailed in @.agilevv/specs/2025-08-20-worktree-isolation/spec.md

> Created: 2025-08-20
> Status: Ready for Implementation

## Tasks

- [ ] 1. **Worktree Detection System** - Implement core git worktree detection and validation logic

  - [ ] 1.1 Write tests for WorktreeDetector class and git worktree detection methods
  - [ ] 1.2 Implement git worktree detection using `git worktree list` command parsing
  - [ ] 1.3 Create worktree root path resolution and validation logic
  - [ ] 1.4 Add environment variable detection and CLAUDE_PROJECT_DIR management
  - [ ] 1.5 Implement worktree metadata collection (branch, root, status)
  - [ ] 1.6 Create error handling for invalid or corrupted worktree scenarios
  - [ ] 1.7 Add performance optimization for repeated path checking operations
  - [ ] 1.8 Verify all worktree detection tests pass

- [ ] 2. **Hook-Based Enforcement** - Create UserPromptSubmit and PreToolUse hooks for boundary validation

  - [ ] 2.1 Write tests for worktree_validator.py UserPromptSubmit hook
  - [ ] 2.2 Implement UserPromptSubmit hook with worktree context injection
  - [ ] 2.3 Write tests for worktree_guard.py PreToolUse hook
  - [ ] 2.4 Implement PreToolUse hook with path validation and blocking logic
  - [ ] 2.5 Create comprehensive error messages for boundary violations
  - [ ] 2.6 Add hook integration with existing .claude/hooks architecture
  - [ ] 2.7 Implement configuration inheritance and worktree-specific settings
  - [ ] 2.8 Verify all hook enforcement tests pass

- [ ] 3. **Path Validation Framework** - Build comprehensive path checking and boundary enforcement

  - [ ] 3.1 Write tests for PathValidator class and boundary checking methods
  - [ ] 3.2 Implement absolute and relative path resolution against worktree root
  - [ ] 3.3 Create directory traversal attack prevention and path sanitization
  - [ ] 3.4 Add file operation validation for read, write, and execute operations
  - [ ] 3.5 Implement cross-worktree boundary detection and blocking
  - [ ] 3.6 Create allowlist/blocklist system for configuration and template access
  - [ ] 3.7 Add performance benchmarking to meet \<10ms validation requirement
  - [ ] 3.8 Verify all path validation tests pass

- [ ] 4. **VeriFlowCC Integration** - Update agents and orchestrator for worktree awareness

  - [ ] 4.1 Write tests for agent factory worktree constraint integration
  - [ ] 4.2 Update AgentFactory to create worktree-aware agents
  - [ ] 4.3 Write tests for orchestrator worktree stage validation
  - [ ] 4.4 Modify Orchestrator to enforce worktree boundaries in V-Model stages
  - [ ] 4.5 Update path_config.py for worktree-aware project root detection
  - [ ] 4.6 Integrate worktree validation with existing git_integration.py
  - [ ] 4.7 Ensure all V-Model agents respect worktree constraints
  - [ ] 4.8 Verify all VeriFlowCC integration tests pass

- [ ] 5. **Documentation and Final Validation** - Complete setup with docs and comprehensive testing

  - [ ] 5.1 Write integration tests for complete worktree isolation workflow
  - [ ] 5.2 Create user documentation and troubleshooting guide
  - [ ] 5.3 Update CLAUDE.md with worktree isolation usage instructions
  - [ ] 5.4 Create launcher scripts for worktree-specific Claude sessions
  - [ ] 5.5 Add configuration templates and example setups
  - [ ] 5.6 Implement performance benchmarking and validation
  - [ ] 5.7 Create end-to-end testing scenarios with multiple worktrees
  - [ ] 5.8 Verify all final integration and documentation tests pass
