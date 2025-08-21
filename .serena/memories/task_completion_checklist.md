# Task Completion Checklist for VeriFlowCC

## Pre-Task Setup

- [ ] Ensure development environment is ready (`uv sync`)
- [ ] Check current git status and branch
- [ ] Verify no development server conflicts
- [ ] Confirm test isolation setup if needed

## During Development

- [ ] Follow AgileVV V-Model methodology:
  - [ ] Requirements analysis and refinement
  - [ ] Design planning and architecture updates
  - [ ] Implementation following design specs
  - [ ] Verification through testing
  - [ ] Validation against acceptance criteria
  - [ ] Integration testing
  - [ ] Documentation updates

## Code Quality Checks (MANDATORY)

```bash
# Run these commands after any code changes:

# 1. Lint and auto-fix code
uv run ruff check --fix

# 2. Format code
uv run ruff format

# 3. Type checking
uv run mypy verifflowcc

# 4. Run all tests with coverage
uv run pytest

# 5. Run pre-commit hooks (optional - runs on commit)
uv run pre-commit run --all-files
```

## Testing Requirements

- [ ] All tests must pass: `uv run pytest`
- [ ] Maintain minimum 80% code coverage
- [ ] Add tests for new features/functions
- [ ] Use appropriate test markers (unit, integration, e2e)
- [ ] Ensure test isolation using PathConfig fixtures

## Documentation Updates

- [ ] Update docstrings for new/modified functions
- [ ] Update CLAUDE.md if project-wide changes made
- [ ] Update architecture.md for design changes
- [ ] Update backlog.md for requirement changes

## Git Workflow

- [ ] Commit changes with descriptive messages
- [ ] Use conventional commit format when applicable
- [ ] Ensure pre-commit hooks pass
- [ ] Create checkpoints at V-Model gates
- [ ] Push to appropriate branch

## Integration Checks

- [ ] Verify no regressions in existing functionality
- [ ] Run integration test suite if applicable
- [ ] Check agent communication still works
- [ ] Validate orchestrator workflow if modified

## Final Validation

- [ ] All acceptance criteria met
- [ ] Code follows project standards
- [ ] No security vulnerabilities introduced
- [ ] Memory usage and context engineering considered
- [ ] Error handling and logging appropriate

## Before Marking Task Complete

- [ ] Double-check all tests pass: `uv run pytest`
- [ ] Verify code quality: `uv run ruff check` and `uv run mypy verifflowcc`
- [ ] Confirm no TODO comments left unaddressed
- [ ] Validate against original task requirements
- [ ] Update task status in tracking system

## Emergency Rollback

If issues are discovered:

- [ ] Use git checkout to rollback changes
- [ ] Or use VeriFlowCC checkpoint restore feature
- [ ] Document the issue for future reference
- [ ] Plan corrective action

## Notes

- Never commit broken tests or failing code quality checks
- Always run the full test suite before marking tasks complete
- Use the test isolation framework to prevent test interference
- Follow the AgileVV V-Model process for all feature development
- Maintain clean git history with meaningful commit messages
