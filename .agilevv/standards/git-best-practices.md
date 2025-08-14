# Git Best Practices

## Context

Git workflow and version control guidelines for AgileVerifFlowCC projects to ensure clean, maintainable, and traceable code history.

<conditional-block context-check="commit-standards">
IF this Commit Standards section already read in current context:
  SKIP: Re-reading this section
  NOTE: "Using Commit Standards already in context"
ELSE:
  READ: The following standards

## Commit Standards

### Conventional Commits

- Use format: `<type>(<scope>): <subject>`
- Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`, `perf`, `ci`, `build`, `revert`
- Example: `feat(auth): add OAuth2 integration`
- Keep subject line under 50 characters
- Use imperative mood ("add" not "added" or "adds")

### Commit Hygiene

- Make atomic commits (one logical change per commit)
- Never commit broken code to main/master
- Write meaningful commit messages explaining "why" not just "what"
- Avoid commits like "WIP", "fix", "updates", "minor changes"
- Squash related commits before merging to main branch
  </conditional-block>

<conditional-block context-check="branching-strategy" task-condition="creating-branch">
IF current task involves creating or managing branches:
  READ: The following branching guidelines
ELSE:
  SKIP: Branching strategy not relevant to current task

## Branching Strategy

### Branch Naming

- Format: `<type>/<ticket-id>-<short-description>`
- Examples:
  - `feature/JIRA-123-user-authentication`
  - `bugfix/JIRA-456-login-error`
  - `hotfix/critical-security-patch`
  - `release/v1.2.0`

### Branch Lifecycle

- Create branches from latest main/master
- Keep branches short-lived (merge within 2 weeks)
- Delete branches after merging
- Never reuse branch names
- Regularly rebase feature branches on main to avoid conflicts
  </conditional-block>

<conditional-block context-check="forbidden-practices">
IF this Forbidden Practices section already read in current context:
  SKIP: Re-reading this section
  NOTE: "Using Forbidden Practices already in context"
ELSE:
  READ: The following restrictions

## Forbidden Practices

### Never Use These Commands/Flags

- `--no-verify`: Always run pre-commit hooks and checks
- `--force` or `-f` on shared branches: Use `--force-with-lease` if absolutely necessary
- `git add .` or `git add -A` blindly: Review changes with `git status` first
- Direct commits to main/master: Always use pull requests
- `git commit --amend` on pushed commits: Create a new commit instead

### Security Restrictions

- Never commit secrets, API keys, or passwords
- Never commit `.env` files with real credentials
- Never commit large binary files (use Git LFS instead)
- Never commit `node_modules`, `vendor`, or build artifacts
- Always use `.gitignore` for generated/sensitive files
  </conditional-block>

<conditional-block context-check="merge-strategies" task-condition="merging-code">
IF current task involves merging or pull requests:
  READ: The following merge guidelines
ELSE:
  SKIP: Merge strategies not relevant to current task

## Merge Strategies

### Pull Request Standards

- Require at least 1 code review approval
- Ensure CI/CD passes before merging
- Use PR templates for consistency
- Link related issues/tickets
- Include screenshots for UI changes
- Resolve all conversations before merging

### Merge Methods

- Prefer squash merge for feature branches
- Use merge commit for release branches
- Never use rebase on public/shared branches
- Resolve conflicts locally, not in GitHub UI
- Test merged code before pushing
  </conditional-block>

<conditional-block context-check="workflow-practices">
IF this Workflow Practices section already read in current context:
  SKIP: Re-reading this section
  NOTE: "Using Workflow Practices already in context"
ELSE:
  READ: The following workflow guidelines

## Daily Workflow Practices

### Before Starting Work

- Always pull latest changes: `git pull origin main`
- Check branch status: `git status`
- Ensure clean working directory
- Create feature branch from updated main

### During Development

- Commit frequently with meaningful messages
- Push to remote at least once per day
- Run tests before committing
- Use `git stash` for temporary changes
- Review diff before committing: `git diff --staged`

### Before Creating PR

- Rebase on latest main: `git rebase main`
- Run full test suite locally
- Review entire changeset: `git log --oneline main..HEAD`
- Ensure no debugging code or console.logs
- Update documentation if needed
  </conditional-block>

<conditional-block context-check="recovery-procedures" task-condition="fixing-git-issues">
IF current task involves fixing Git problems:
  READ: The following recovery procedures
ELSE:
  SKIP: Recovery procedures not relevant to current task

## Recovery Procedures

### Common Fixes

- Undo last commit (not pushed): `git reset HEAD~1`
- Undo last commit (keep changes): `git reset --soft HEAD~1`
- Discard local changes: `git checkout -- <file>`
- Remove untracked files: `git clean -fd` (use with caution)
- Recover deleted branch: `git reflog` then `git checkout -b <branch> <commit>`

### Conflict Resolution

- Always communicate with team during conflicts
- Use `git log --merge` to see conflicting commits
- Test thoroughly after resolving conflicts
- Document conflict resolution in commit message
  </conditional-block>

## Git Configuration

### Recommended Global Settings

```bash
# User identity
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"

# Helpful aliases
git config --global alias.co checkout
git config --global alias.br branch
git config --global alias.ci commit
git config --global alias.st status
git config --global alias.last 'log -1 HEAD'
git config --global alias.unstage 'reset HEAD --'

# Better diffs
git config --global diff.algorithm histogram
git config --global merge.conflictstyle diff3

# Automatic line ending handling
git config --global core.autocrlf input  # On Mac/Linux
git config --global core.autocrlf true   # On Windows

# Default branch name
git config --global init.defaultBranch main

# Rebase by default for pull
git config --global pull.rebase true

# Prune on fetch
git config --global fetch.prune true
```

## Pre-commit Hooks

### Required Checks

Always ensure these run before commits:

- Code linting (ESLint, Pylint, etc.)
- Code formatting (Prettier, Black, etc.)
- Unit tests for changed files
- Security scanning for secrets
- Commit message validation

### Setup Example

```bash
# Install pre-commit framework
pip install pre-commit

# Install hooks
pre-commit install

# Never bypass with --no-verify!
```

## Team Collaboration

### Communication Rules

- Announce when working on shared files
- Coordinate before major refactoring
- Document breaking changes in commits
- Use draft PRs for work in progress
- Tag reviewers explicitly in PRs

### Code Review Etiquette

- Review within 24 hours when tagged
- Provide constructive feedback
- Approve only when truly satisfied
- Use "Request changes" sparingly
- Suggest specific improvements

## References

- [Conventional Commits](https://www.conventionalcommits.org/)
- [Git Flow](https://nvie.com/posts/a-successful-git-branching-model/)
- [GitHub Flow](https://guides.github.com/introduction/flow/)
- [Semantic Versioning](https://semver.org/)
