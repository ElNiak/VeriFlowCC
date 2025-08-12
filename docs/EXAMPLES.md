# VeriFlowCC Examples

## Example 1: Todo Application Development

### Sprint 0 - Project Setup

```bash
# Initialize the project
verifflowcc init

# Add initial stories to backlog
cat >> .agilevv/backlog.md << EOF
## User Stories

- [ ] As a user, I want to create todo items with title and description
- [ ] As a user, I want to mark todos as complete
- [ ] As a user, I want to filter todos by status
- [ ] As a user, I want to set due dates for todos
- [ ] As a user, I want to categorize todos with tags
EOF
```

### Sprint 1 - Basic Todo CRUD

```bash
# Plan the sprint
verifflowcc plan
# Select: "As a user, I want to create todo items with title and description"

# Execute the sprint
verifflowcc sprint -s "As a user, I want to create todo items with title and description"

# The orchestrator will:
# 1. Analyze requirements with Claude-Code
# 2. Design the todo model and API
# 3. Generate implementation code
# 4. Create unit tests
# 5. Run integration tests
# 6. Validate acceptance criteria

# Create checkpoint after success
verifflowcc checkpoint -n "todo-crud-complete" -m "Basic CRUD operations implemented"

# Check status
verifflowcc status
```

### Sprint 2 - Status Management

```bash
# Continue with next story
verifflowcc plan --story-id 2

# Execute sprint
verifflowcc sprint -s "As a user, I want to mark todos as complete"

# Validate the implementation
verifflowcc validate

# Create checkpoint
verifflowcc checkpoint -n "status-feature" -m "Todo status management added"
```

## Example 2: REST API Development

### Initial Setup

```bash
verifflowcc init --force

# Configure for API development
cat > .agilevv/config.yaml << EOF
project:
  name: "REST API Service"
  type: "api"

v_model:
  gating_mode: hard
  stages:
    requirements:
      enabled: true
      gating: hard
    design:
      enabled: true
      gating: hard
      artifacts:
        - openapi_spec.yaml
        - database_schema.sql
    coding:
      enabled: true
      gating: soft
    unit_testing:
      enabled: true
      gating: hard
      min_coverage: 80
    integration_testing:
      enabled: true
      gating: hard
    system_testing:
      enabled: true
      gating: soft
    validation:
      enabled: true
      gating: hard

agents:
  requirements_analyst:
    model: claude-3-sonnet
    max_tokens: 4000
  architect:
    model: claude-3-sonnet
    max_tokens: 6000
  developer:
    model: claude-3-sonnet
    max_tokens: 8000
  qa_tester:
    model: claude-3-sonnet
    max_tokens: 4000
EOF
```

### Development Workflow

```bash
# Add API stories
cat > .agilevv/backlog.md << EOF
# REST API Backlog

## Authentication
- [ ] As an API client, I want to authenticate using JWT tokens
- [ ] As an API client, I want to refresh expired tokens

## Resource Management
- [ ] As an API client, I want to GET resources with pagination
- [ ] As an API client, I want to POST new resources
- [ ] As an API client, I want to PUT/PATCH to update resources
- [ ] As an API client, I want to DELETE resources

## Error Handling
- [ ] As an API client, I want consistent error responses
- [ ] As an API client, I want rate limiting information
EOF

# Execute authentication sprint
verifflowcc plan
verifflowcc sprint -s "As an API client, I want to authenticate using JWT tokens"

# After implementation, validate
verifflowcc validate --stage integration_testing

# Checkpoint the progress
verifflowcc checkpoint -n "jwt-auth" -m "JWT authentication implemented and tested"
```

## Example 3: Rollback Scenario

### When Things Go Wrong

```bash
# Start a risky refactoring
verifflowcc sprint -s "Refactor database layer for better performance"

# Tests start failing...
# Check what went wrong
verifflowcc status --verbose

# List available checkpoints
verifflowcc checkpoint list

# Rollback to last stable state
verifflowcc checkpoint restore jwt-auth

# Try a different approach
verifflowcc sprint -s "Implement caching layer instead of DB refactor"
```

## Example 4: Integration with CI/CD

### GitHub Actions Workflow

```yaml
name: VeriFlowCC Sprint Execution

on:
  workflow_dispatch:
    inputs:
      story:
        description: 'User story to implement'
        required: true

jobs:
  sprint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Setup Python with UV
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install UV
        run: pip install uv

      - name: Install dependencies
        run: uv sync

      - name: Execute Sprint
        run: |
          verifflowcc sprint -s "${{ github.event.inputs.story }}"
        env:
          CLAUDE_API_KEY: ${{ secrets.CLAUDE_API_KEY }}

      - name: Run Validation
        run: verifflowcc validate

      - name: Create Checkpoint
        if: success()
        run: |
          STORY_SLUG=$(echo "${{ github.event.inputs.story }}" | tr ' ' '-' | tr '[:upper:]' '[:lower:]' | cut -c1-20)
          verifflowcc checkpoint -n "ci-${STORY_SLUG}" -m "Automated checkpoint from CI"

      - name: Upload Artifacts
        uses: actions/upload-artifact@v3
        with:
          name: sprint-artifacts
          path: .agilevv/
```

## Example 5: Multi-Stage Development

### Complex Feature with Dependencies

```bash
# Initialize with advanced configuration
verifflowcc init

# Plan multi-stage feature
cat > .agilevv/backlog.md << EOF
# E-Commerce Platform

## Epic: Shopping Cart
- [ ] As a user, I want to add items to cart
- [ ] As a user, I want to update item quantities
- [ ] As a user, I want to remove items from cart
- [ ] As a user, I want to save cart for later

## Epic: Checkout Process
- [ ] As a user, I want to enter shipping information
- [ ] As a user, I want to select payment method
- [ ] As a user, I want to review order before purchase
- [ ] As a user, I want to receive order confirmation
EOF

# Execute dependent stories in sequence
for story in "add items to cart" "update item quantities" "remove items from cart"; do
  verifflowcc sprint -s "As a user, I want to $story"
  verifflowcc validate
  verifflowcc checkpoint -n "cart-${story// /-}" -m "Cart feature: $story"
done

# Check overall progress
verifflowcc status --verbose
```

## Example 6: Test-Driven Development

### TDD Workflow

```bash
# Configure for TDD
cat >> .agilevv/config.yaml << EOF
development:
  methodology: tdd
  test_first: true
EOF

# Plan with test scenarios
verifflowcc plan

# The orchestrator will:
# 1. Generate test cases from requirements
# 2. Create failing tests
# 3. Implement code to pass tests
# 4. Refactor while keeping tests green

verifflowcc sprint -s "As a user, I want input validation for email addresses"

# Validate with focus on tests
verifflowcc validate --tests-only

# Check coverage
verifflowcc validate --coverage-only
```

## Example 7: Hotfix Workflow

### Emergency Fix Process

```bash
# Save current state
verifflowcc checkpoint -n "pre-hotfix" -m "State before emergency fix"

# Create hotfix branch (if using git)
git checkout -b hotfix/critical-bug

# Quick fix execution
verifflowcc sprint -s "HOTFIX: Fix critical authentication bypass"

# Immediate validation
verifflowcc validate --stage unit_testing
verifflowcc validate --stage integration_testing

# Deploy checkpoint
verifflowcc checkpoint -n "hotfix-deployed" -m "Critical security fix applied"

# Merge back (if using git)
git checkout main
git merge hotfix/critical-bug
```

## Tips and Tricks

### 1. Batch Processing Stories

```bash
# Process multiple related stories
while IFS= read -r story; do
  verifflowcc sprint -s "$story"
  verifflowcc validate || break
done < stories.txt
```

### 2. Custom Validation Scripts

```bash
# Add custom validation
cat > .agilevv/custom_validate.sh << 'EOF'
#!/bin/bash
echo "Running custom validations..."
python -m pytest tests/ --cov=src --cov-report=term-missing
python -m mypy src/
python -m black --check src/
python -m flake8 src/
EOF

chmod +x .agilevv/custom_validate.sh
```

### 3. Parallel Development

```bash
# Team member 1
verifflowcc sprint -s "Frontend: User interface for login"

# Team member 2 (different terminal)
verifflowcc sprint -s "Backend: Authentication API endpoints"

# Integrate both
verifflowcc validate --stage integration_testing
```

### 4. Progress Monitoring

```bash
# Create status dashboard
watch -n 5 'verifflowcc status --verbose'

# Monitor in separate terminal while developing
verifflowcc sprint -s "Complex feature implementation"
```

## Common Patterns

### Pattern 1: Feature Flags

```bash
# Implement feature behind flag
verifflowcc sprint -s "As a developer, I want feature flags for gradual rollout"

# Test with flag enabled
FEATURE_NEW_UI=true verifflowcc validate

# Test with flag disabled
FEATURE_NEW_UI=false verifflowcc validate
```

### Pattern 2: A/B Testing

```bash
# Implement variants
verifflowcc sprint -s "As a product owner, I want A/B testing for checkout flow"

# Validate both variants
verifflowcc validate --stage system_testing --variant A
verifflowcc validate --stage system_testing --variant B
```

### Pattern 3: Performance Testing

```bash
# Add performance requirements
echo "- [ ] System must handle 1000 requests/second" >> .agilevv/backlog.md

# Execute with performance focus
verifflowcc sprint -s "Performance: Optimize API response times"

# Validate performance
verifflowcc validate --stage system_testing --performance
```

These examples demonstrate the flexibility and power of VeriFlowCC in managing various development scenarios while maintaining the rigor of the V-Model methodology.
