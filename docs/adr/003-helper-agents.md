# ADR-003: Helper Agent Integration Pattern

**Status:** Accepted
**Date:** 2025-08-07
**Deciders:** VeriFlowCC Architecture Team

## Context

Agent-OS provides several helper agents that handle common operations:
- **context-fetcher**: Gathers relevant context from codebase
- **git-workflow**: Manages git operations and CHANGELOG updates
- **test-runner**: Executes and analyzes test results

These helpers can reduce token usage and improve consistency. We need to decide how to integrate them into our V-Model agent hierarchy without breaking our stage-based architecture.

## Decision

We will implement a **delegation pattern** where primary agents can invoke helper agents for specific tasks. Helper agents are:
1. **Stateless** - No persistent state between calls
2. **Focused** - Single responsibility per helper
3. **Reusable** - Available to all primary agents
4. **Token-efficient** - Reduce context size through specialization

### Agent Hierarchy

```
Primary Agents (Stateful, Stage-bound)
├── planner (Opus 4.1)
├── requirements-analyst (Opus 4.1)
├── architect-designer (Sonnet 4)
├── coder-implementer (Sonnet 4)
├── unit-test-writer (Sonnet 4)
└── acceptance-validator (Opus 4.1)

Helper Agents (Stateless, Cross-cutting)
├── context-fetcher (Sonnet 4)
├── git-workflow (Sonnet 4)
├── test-runner (Sonnet 4)
├── code-analyzer (Sonnet 4) [future]
└── doc-generator (Sonnet 4) [future]
```

## Rationale

### Why Delegation Pattern?

1. **Separation of Concerns**
   - Primary agents focus on stage logic
   - Helpers handle technical operations
   - Clear responsibility boundaries

2. **Token Efficiency**
   - Helpers get minimal context
   - No stage history needed
   - Focused prompts = smaller contexts

3. **Reusability**
   - Any agent can use any helper
   - No duplication of functionality
   - Consistent operations across stages

### Alternatives Considered

**Monolithic Agents**
- Pros: Simpler architecture
- Cons: Large contexts, duplicated logic
- Rejected: Token inefficient, hard to maintain

**Helper as Tools**
- Pros: Tool-like interface
- Cons: Can't leverage LLM reasoning
- Rejected: Loses intelligent behavior

**Microservice Pattern**
- Pros: Complete independence
- Cons: Complex orchestration
- Rejected: Over-engineered for CLI tool

## Implementation

### Helper Agent Schema

```yaml
# .claude/agents/helpers/context-fetcher.yaml
name: context-fetcher
type: helper
model: sonnet-4
description: Gathers relevant context from codebase for analysis
capabilities:
  - file_search
  - symbol_extraction
  - dependency_analysis

input_schema:
  type: object
  properties:
    query:
      type: string
      description: What context to fetch
    scope:
      type: string
      enum: [file, module, project]
    max_tokens:
      type: integer
      default: 2000

output_schema:
  type: object
  properties:
    context:
      type: string
      description: Gathered context
    files_analyzed:
      type: array
      items:
        type: string
    tokens_used:
      type: integer
```

### Helper Integration in Primary Agents

```python
# verifflowcc/agents/coder_implementer.py
from verifflowcc.helpers import HelperRegistry

class CoderImplementer:
    def __init__(self):
        self.helpers = HelperRegistry()

    async def implement_feature(self, design_spec: str) -> str:
        # Step 1: Gather context using helper
        context = await self.helpers.invoke(
            "context-fetcher",
            query=f"Find code related to: {design_spec}",
            scope="module",
            max_tokens=3000
        )

        # Step 2: Generate implementation
        implementation = await self.generate_code(
            design=design_spec,
            context=context.result
        )

        # Step 3: Validate with another helper
        validation = await self.helpers.invoke(
            "code-analyzer",
            code=implementation,
            check_for=["syntax", "style", "security"]
        )

        return implementation
```

### Helper Registry

```python
# verifflowcc/helpers/registry.py
from typing import Dict, Any, Optional
import yaml
from pathlib import Path

class HelperRegistry:
    """Registry for helper agents"""

    def __init__(self):
        self.helpers = {}
        self.load_helpers()

    def load_helpers(self):
        """Load helper definitions from YAML"""
        helper_dir = Path(".claude/agents/helpers")
        for helper_file in helper_dir.glob("*.yaml"):
            with open(helper_file) as f:
                config = yaml.safe_load(f)
                self.helpers[config['name']] = HelperAgent(config)

    async def invoke(self, helper_name: str, **kwargs) -> HelperResult:
        """Invoke a helper agent"""
        if helper_name not in self.helpers:
            raise ValueError(f"Unknown helper: {helper_name}")

        helper = self.helpers[helper_name]

        # Validate input against schema
        helper.validate_input(kwargs)

        # Build minimal context
        context = helper.build_context(kwargs)

        # Invoke via Claude API
        result = await self.call_claude(
            model=helper.model,
            prompt=context,
            max_tokens=helper.max_tokens
        )

        # Validate output against schema
        output = helper.validate_output(result)

        return HelperResult(
            helper=helper_name,
            input=kwargs,
            output=output,
            tokens_used=result.tokens_used
        )
```

### Helper Usage Patterns

```python
# Pattern 1: Simple delegation
context = await helpers.invoke("context-fetcher",
                              query="authentication logic")

# Pattern 2: Chained helpers
context = await helpers.invoke("context-fetcher",
                              query="test files")
results = await helpers.invoke("test-runner",
                              files=context.files)

# Pattern 3: Conditional helpers
if stage == "validation":
    changelog = await helpers.invoke("git-workflow",
                                    action="update_changelog")
```

### Token Usage Optimization

```yaml
# Token budget per operation
token_budgets:
  primary_agent_context: 50000  # Large context for reasoning
  helper_agent_context: 5000    # Minimal context for operation

  # Example savings:
  # Old: Coder reads all files (30K) + generates code (20K) = 50K
  # New: Helper fetches context (5K) + Coder generates (20K) = 25K
  # Savings: 50% reduction in context tokens
```

## Consequences

### Positive

1. **Significant Token Reduction**
   - 30-50% reduction in context size
   - Focused operations use fewer tokens
   - Better cost efficiency

2. **Improved Maintainability**
   - Single responsibility per helper
   - Easy to test in isolation
   - Clear debugging path

3. **Consistent Operations**
   - Git operations always work the same
   - Test running is standardized
   - Context fetching is predictable

### Negative

1. **Additional Complexity**
   - More agents to manage
   - Inter-agent communication overhead
   - More points of failure

2. **Latency Increase**
   - Multiple API calls per operation
   - Sequential helper calls add time
   - ~200-500ms per helper invocation

3. **Debugging Challenges**
   - Distributed logic harder to trace
   - Need to check multiple agents
   - More logs to analyze

## Mitigations

1. **Complexity**: Clear documentation and examples
2. **Latency**: Parallel helper calls where possible
3. **Debugging**: Comprehensive logging with correlation IDs

## Testing Strategy

```python
# Test helper in isolation
def test_context_fetcher():
    result = await helpers.invoke(
        "context-fetcher",
        query="find main function",
        scope="file"
    )
    assert "def main" in result.context
    assert result.tokens_used < 2000

# Test integration with primary agent
def test_coder_with_helpers():
    coder = CoderImplementer()
    code = await coder.implement_feature("add logging")
    assert "import logging" in code
    assert coder.tokens_used < 25000  # With helper
    # vs 50000 without helper
```

## Migration Path

1. **Phase 1**: Import Agent-OS helpers as-is
2. **Phase 2**: Convert to our YAML format
3. **Phase 3**: Integrate with one primary agent
4. **Phase 4**: Roll out to all agents
5. **Phase 5**: Add custom helpers

## References

- Agent-OS Helper Implementation
- Delegation Pattern in Multi-Agent Systems
- Token Optimization Strategies
- Claude API Best Practices

## Notes

Review this decision if:
- Token savings don't materialize (< 20% reduction)
- Latency becomes unacceptable (> 1s per helper)
- Maintenance burden exceeds benefits
- Claude API adds native helper support
