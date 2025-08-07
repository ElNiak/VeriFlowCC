# Python Coding Guidelines for VeriFlowCC

## Package Management
- Use UV for dependency management (10-100x faster than pip/poetry)
- Lock dependencies with uv.lock for reproducibility
- Use pyproject.toml for all project configuration
- Keep development dependencies separate from runtime dependencies

## Core Principles
1. **Follow PEP 8** with 100-character line limit
2. **Use type hints** for all function signatures and class attributes
3. **Implement async/await** for AI agent calls to maximize concurrency
4. **Use Pydantic** for all data validation and structured outputs

## Multi-Agent Architecture Patterns

### Agent Design
- Agents as classes inheriting from `BaseAgent`
- Context isolation between agents (no shared mutable state)
- Structured data transfer via Pydantic models
- Tool calls through MCP interface abstraction

### Agent Communication
```python
# Good: Structured communication
class PlannerOutput(BaseModel):
    requirements: List[str]
    tasks: List[Task]
    acceptance_criteria: List[str]

# Bad: Unstructured dictionaries
return {"requirements": [...], "tasks": [...]}
```

## Error Handling

### Best Practices
- Never use bare `except:` - always specify exception types
- Log errors with structured logging (include context)
- Implement retry logic with exponential backoff for API calls
- Validate all LLM outputs with Pydantic before processing

### Example Pattern
```python
from typing import Optional
import asyncio
from pydantic import ValidationError

async def call_agent_with_retry(
    agent: BaseAgent,
    prompt: str,
    max_retries: int = 3
) -> Optional[BaseModel]:
    for attempt in range(max_retries):
        try:
            response = await agent.generate(prompt)
            return agent.parse_response(response)
        except ValidationError as e:
            logger.warning(f"Validation failed (attempt {attempt + 1}): {e}")
            if attempt == max_retries - 1:
                raise
        except Exception as e:
            logger.error(f"Agent call failed: {e}")
            await asyncio.sleep(2 ** attempt)  # Exponential backoff
    return None
```

## Code Organization

### Module Structure
```
verifflowcc/
├── agents/        # Agent implementations
├── core/          # Core business logic
├── prompts/       # Jinja2 templates
├── schemas/       # Pydantic models
└── utils/         # Shared utilities
```

### Import Order
1. Standard library imports
2. Related third-party imports
3. Local application imports

## Documentation

### Docstrings
Use Google style docstrings for all public methods and classes:
```python
def process_plan(plan: Plan, context: Context) -> ExecutionResult:
    """Process a plan through the V-Model pipeline.

    Args:
        plan: The plan to execute
        context: Execution context with memory and configuration

    Returns:
        ExecutionResult with status and artifacts

    Raises:
        ValidationError: If plan validation fails
        ExecutionError: If pipeline execution fails
    """
```

### Type Hints
- Use `Optional[T]` for nullable types
- Use `List[T]`, `Dict[K, V]` from typing (Python 3.10+)
- Use `Union[T1, T2]` sparingly - prefer single types
- Use `TypeAlias` for complex repeated types

## Testing

### Requirements
- Use pytest with asyncio support for async tests
- Minimum 80% code coverage
- Mock external API calls in unit tests
- Test Pydantic schema validation explicitly
- Use fixtures for common test data

### Test Organization
```python
# tests/test_agents/test_planner.py
import pytest
from unittest.mock import AsyncMock

@pytest.fixture
def mock_claude_api():
    return AsyncMock()

@pytest.mark.asyncio
async def test_planner_generates_valid_plan(mock_claude_api):
    # Test implementation
    pass
```

## Security

### API Keys and Secrets
- Never hardcode API keys or secrets
- Use environment variables or secure vaults
- Validate and sanitize all user inputs
- Log sensitive data with redaction

### File Operations
- Use pathlib.Path for file operations
- Validate file paths before operations
- Implement proper access controls
- Use context managers for file handling

## Performance

### Optimization Guidelines
- Use async/await for I/O operations
- Implement caching where appropriate
- Batch API calls when possible
- Profile code before optimizing

### Token Management
- Track token usage per agent call
- Implement context windowing for long conversations
- Use structured prompts to minimize token usage
- Cache prompt templates after rendering

## Logging

### Structure
```python
import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)

def log_agent_call(agent_type: str, context: Dict[str, Any]) -> None:
    logger.info(
        "Agent call initiated",
        extra={
            "agent_type": agent_type,
            "context_size": len(str(context)),
            "timestamp": datetime.utcnow().isoformat()
        }
    )
```

## Git Workflow

### Commit Messages
- Use conventional commits format
- Include ticket/issue number when applicable
- Keep commits atomic and focused

### Branch Naming
- `feature/` for new features
- `fix/` for bug fixes
- `refactor/` for code improvements
- `docs/` for documentation updates

## Code Review Checklist

Before submitting PR:
- [ ] All tests pass (`uv run pytest`)
- [ ] Linting passes (`uv run ruff check .`)
- [ ] Type checking passes (`uv run mypy verifflowcc`)
- [ ] Documentation updated
- [ ] No hardcoded values or secrets
- [ ] Error handling implemented
- [ ] Logging added for debugging

## AI Agent Specific Guidelines

### Prompt Engineering
- Use Jinja2 templates for all prompts
- Keep prompts versioned and tested
- Include clear output format instructions
- Use few-shot examples when needed

### Context Management
- Implement context windowing for long sessions
- Store conversation history efficiently
- Use structured memory (CLAUDE.md pattern)
- Clear context between independent tasks

### Output Validation
- Always validate LLM outputs with Pydantic
- Implement fallback for validation failures
- Log validation errors for analysis
- Provide clear error messages to users
