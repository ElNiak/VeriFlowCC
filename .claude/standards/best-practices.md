# Development Best Practices

## Context

Global development guidelines for AgileVerifFlowCC projects.

<conditional-block context-check="core-principles">
IF this Core Principles section already read in current context:
  SKIP: Re-reading this section
  NOTE: "Using Core Principles already in context"
ELSE:
  READ: The following principles

## Core Principles

### Keep It Simple

- Implement code in the fewest lines possible
- Avoid over-engineering solutions
- Choose straightforward approaches over clever ones

### Optimize for Readability

- Prioritize code clarity over micro-optimizations
- Write self-documenting code with clear variable names
- Add comments for "why" not "what"

### DRY (Don't Repeat Yourself)

- Extract repeated business logic to private methods
- Extract repeated UI markup to reusable components
- Create utility functions for common operations

### File Structure

- Keep files focused on a single responsibility
- Group related functionality together
- Use consistent naming conventions
  </conditional-block>

<conditional-block context-check="dependencies" task-condition="choosing-external-library">
IF current task involves choosing an external library:
  IF Dependencies section already read in current context:
    SKIP: Re-reading this section
    NOTE: "Using Dependencies guidelines already in context"
  ELSE:
    READ: The following guidelines
ELSE:
  SKIP: Dependencies section not relevant to current task

## Dependencies

### Choose Libraries Wisely

When adding third-party dependencies:

- Select the most popular and actively maintained option
- Check the library's GitHub repository for:
  - Recent commits (within last 6 months)
  - Active issue resolution
  - Number of stars/downloads
  - Clear documentation
    </conditional-block>

### Code Quality Restrictions

- **Never commit placeholder code:**

  - No `TODO` without a ticket number: Use `TODO(JIRA-123): description`
  - No `FIXME` without immediate resolution plan
  - No dummy data in production code
  - No hardcoded test values (use configuration/environment variables)

- **Never commit mock implementations:**

  - No mock services without `mock` in filename (e.g., `service.mock.ts`)
  - No stub functions returning static data in production code
  - No commented-out real implementations replaced with mocks
  - Mock code must be in test directories only

- **Never commit oversimplified solutions:**

  - No bypassing error handling with empty catch blocks
  - No ignoring edge cases with comments like "will handle later"
  - No removing validation "temporarily"
  - No shortcuts that compromise security or data integrity

- **Never commit incomplete features:**

  - No partially implemented functions
  - No features with "coming soon" messages
  - No UI elements without backend implementation
  - No endpoints returning hardcoded responses

### Pre-commit Validation

Before ANY commit, verify:

```bash
# Check for forbidden patterns
grep -r "TODO[^(]" --include="*.{js,ts,py,java}" .  # TODOs without ticket
grep -r "FIXME" --include="*.{js,ts,py,java}" .
grep -r "console.log\|print\|System.out" --include="*.{js,ts,py,java}" .
grep -r "any\s*=" --include="*.{ts}" .  # TypeScript 'any' types
grep -r "//\s*return\|#\s*return" --include="*.{js,ts,py}" .  # Commented returns
grep -r "catch\s*{\s*}" --include="*.{js,ts,java}" .  # Empty catch blocks
```

### Implementation Standards

When implementing features:

1. **Complete or Don't Commit:**

   - Feature works end-to-end or isn't merged
   - All error cases handled
   - All inputs validated
   - All outputs verified

1. **Real Data Only:**

   - Use actual database connections
   - Implement real API calls
   - Use proper authentication/authorization
   - Handle real-world scenarios

1. **No Simplification Debt:**

   - Don't simplify to "make it work"
   - Implement proper patterns from start
   - Include all necessary checks
   - Consider performance implications

1. **Feature Flags Instead of Mocks:**

   - Use feature flags for gradual rollout
   - Hide incomplete features behind flags
   - Never use mocks as temporary solutions
   - Document flag removal timeline

</conditional-block>
