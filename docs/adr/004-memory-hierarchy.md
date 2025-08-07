# ADR-004: Memory Hierarchy Architecture

**Status:** Accepted
**Date:** 2025-08-07
**Deciders:** VeriFlowCC Architecture Team

## Context

VeriFlowCC agents need access to various types of information:
- Project-wide conventions and decisions
- Sprint-specific goals and progress
- Stage-specific artifacts and results
- Agent-specific operational context

Without proper organization, agents receive too much irrelevant context (increasing tokens) or too little context (reducing effectiveness). We need a hierarchical memory system that provides the right information at the right time.

## Decision

We will implement a **4-layer memory hierarchy** with selective loading based on current context:

1. **Project Layer** - Persistent across all sprints
2. **Sprint Layer** - Specific to current sprint
3. **Stage Layer** - Specific to current V-Model stage
4. **Agent Layer** - Runtime context for specific agent

### Memory Hierarchy Structure

```
Memory Hierarchy
├── Project (Persistent)
│   ├── CLAUDE.md           # Core project knowledge
│   ├── conventions/        # Coding standards, patterns
│   └── decisions/          # Architectural decisions
├── Sprint (Sprint-scoped)
│   ├── goals.md           # Sprint objectives
│   ├── progress.json      # Completion tracking
│   └── context.md         # Sprint-specific knowledge
├── Stage (Stage-scoped)
│   ├── artifacts/         # Stage outputs
│   ├── feedback.md        # Review comments
│   └── metrics.json       # Stage metrics
└── Agent (Runtime)
    ├── prompt.md          # Agent-specific prompt
    ├── tools.yaml         # Available tools
    └── context.json       # Runtime context
```

## Rationale

### Why Hierarchical?

1. **Context Relevance**
   - Agents only see what they need
   - Reduces noise in prompts
   - Improves response quality

2. **Token Efficiency**
   - Selective loading reduces context size
   - Can fit more relevant information
   - Lower API costs

3. **Maintainability**
   - Clear organization
   - Easy to update specific layers
   - Simple debugging

### Alternatives Considered

**Flat Memory Structure**
- Pros: Simple to implement
- Cons: Everything loaded always, token wasteful
- Rejected: Doesn't scale

**Database-backed Memory**
- Pros: Powerful queries, versioning
- Cons: Complex for CLI tool
- Rejected: Over-engineered

**No Persistent Memory**
- Pros: No state management
- Cons: Agents forget everything
- Rejected: Poor user experience

## Implementation

### Memory Manager

```python
# verifflowcc/memory/manager.py
from pathlib import Path
from typing import Dict, List, Optional
import json
import yaml
from pydantic import BaseModel

class MemoryLayer(str, Enum):
    PROJECT = "project"
    SPRINT = "sprint"
    STAGE = "stage"
    AGENT = "agent"

class MemoryEntry(BaseModel):
    """Single memory entry"""
    layer: MemoryLayer
    key: str
    content: str
    metadata: Dict[str, any]
    tokens: int  # Estimated token count

class MemoryContext(BaseModel):
    """Complete memory context for an agent"""
    project: List[MemoryEntry]
    sprint: List[MemoryEntry]
    stage: List[MemoryEntry]
    agent: List[MemoryEntry]
    total_tokens: int

class MemoryManager:
    """Manages hierarchical memory system"""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.memory_root = project_root / ".memory"
        self.token_budget = 50000  # Max context size

    def load_context_for_agent(
        self,
        agent_name: str,
        sprint_id: str,
        stage: str,
        token_budget: Optional[int] = None
    ) -> MemoryContext:
        """Load appropriate context for an agent"""

        budget = token_budget or self.token_budget
        context = MemoryContext(
            project=[],
            sprint=[],
            stage=[],
            agent=[],
            total_tokens=0
        )

        # Load in priority order
        priorities = [
            (MemoryLayer.AGENT, 0.4),   # 40% for agent-specific
            (MemoryLayer.STAGE, 0.3),   # 30% for stage artifacts
            (MemoryLayer.SPRINT, 0.2),  # 20% for sprint context
            (MemoryLayer.PROJECT, 0.1), # 10% for project knowledge
        ]

        for layer, allocation in priorities:
            layer_budget = int(budget * allocation)
            entries = self.load_layer(
                layer, agent_name, sprint_id, stage, layer_budget
            )
            setattr(context, layer.value, entries)
            context.total_tokens += sum(e.tokens for e in entries)

        return context

    def load_layer(
        self,
        layer: MemoryLayer,
        agent_name: str,
        sprint_id: str,
        stage: str,
        token_budget: int
    ) -> List[MemoryEntry]:
        """Load specific memory layer"""

        if layer == MemoryLayer.PROJECT:
            return self.load_project_memory(token_budget)
        elif layer == MemoryLayer.SPRINT:
            return self.load_sprint_memory(sprint_id, token_budget)
        elif layer == MemoryLayer.STAGE:
            return self.load_stage_memory(stage, token_budget)
        elif layer == MemoryLayer.AGENT:
            return self.load_agent_memory(agent_name, token_budget)

    def load_project_memory(self, budget: int) -> List[MemoryEntry]:
        """Load project-wide memory"""
        entries = []

        # Always load CLAUDE.md if it fits
        claude_md = self.project_root / "CLAUDE.md"
        if claude_md.exists():
            content = claude_md.read_text()
            tokens = self.estimate_tokens(content)
            if tokens <= budget:
                entries.append(MemoryEntry(
                    layer=MemoryLayer.PROJECT,
                    key="claude_md",
                    content=content,
                    metadata={"priority": "high"},
                    tokens=tokens
                ))
                budget -= tokens

        # Load recent decisions if space
        decisions_dir = self.memory_root / "project" / "decisions"
        if decisions_dir.exists():
            for decision in sorted(decisions_dir.glob("*.md"),
                                  key=lambda p: p.stat().st_mtime,
                                  reverse=True):
                content = decision.read_text()
                tokens = self.estimate_tokens(content)
                if tokens <= budget:
                    entries.append(MemoryEntry(
                        layer=MemoryLayer.PROJECT,
                        key=f"decision_{decision.stem}",
                        content=content,
                        metadata={"type": "decision"},
                        tokens=tokens
                    ))
                    budget -= tokens
                else:
                    break  # Stop if we can't fit more

        return entries
```

### Memory Loading Strategy

```yaml
# .memory/config.yaml
loading_strategy:
  project:
    always_load:
      - CLAUDE.md
      - conventions/python.md
    conditional_load:
      - decisions/*.md  # Load recent first
    max_tokens: 5000

  sprint:
    always_load:
      - goals.md
      - progress.json
    conditional_load:
      - retrospectives/*.md
    max_tokens: 10000

  stage:
    always_load:
      - current_artifacts/*
    conditional_load:
      - previous_stage_summary.md
    max_tokens: 15000

  agent:
    always_load:
      - prompt_template.md
      - tools_config.yaml
    conditional_load:
      - recent_actions.json
    max_tokens: 20000

token_allocation:
  # How to split token budget
  planner:
    project: 0.3  # More project context
    sprint: 0.4   # More sprint context
    stage: 0.2
    agent: 0.1

  coder:
    project: 0.1
    sprint: 0.1
    stage: 0.3   # More stage artifacts
    agent: 0.5   # More agent-specific
```

### Memory Update Patterns

```python
# After each stage completion
def update_stage_memory(stage: str, artifacts: Dict):
    """Update stage memory with results"""
    stage_dir = Path(f".memory/stage/{stage}")
    stage_dir.mkdir(parents=True, exist_ok=True)

    # Save artifacts
    for name, content in artifacts.items():
        (stage_dir / f"{name}.json").write_text(
            json.dumps(content, indent=2)
        )

    # Create summary for next stage
    summary = create_stage_summary(artifacts)
    (stage_dir / "summary.md").write_text(summary)

# After sprint completion
def update_sprint_memory(sprint_id: str, results: Dict):
    """Update sprint memory with results"""
    sprint_dir = Path(f".memory/sprint/{sprint_id}")

    # Update progress
    progress = json.loads((sprint_dir / "progress.json").read_text())
    progress.update(results)
    (sprint_dir / "progress.json").write_text(
        json.dumps(progress, indent=2)
    )

    # Add to sprint knowledge
    knowledge = (sprint_dir / "knowledge.md")
    knowledge.write_text(
        knowledge.read_text() + f"\n\n## Learnings\n{results['learnings']}"
    )
```

### Context Injection Example

```python
# How context is injected into agent prompts
def build_agent_prompt(agent: Agent, memory: MemoryContext) -> str:
    """Build complete prompt with memory context"""

    sections = []

    # Project context (if any)
    if memory.project:
        sections.append("## Project Context")
        for entry in memory.project:
            sections.append(f"### {entry.key}")
            sections.append(entry.content)

    # Sprint context
    if memory.sprint:
        sections.append("## Current Sprint")
        for entry in memory.sprint:
            sections.append(entry.content)

    # Stage context
    if memory.stage:
        sections.append("## Stage Artifacts")
        for entry in memory.stage:
            sections.append(f"```json\n{entry.content}\n```")

    # Agent-specific prompt
    sections.append("## Your Task")
    sections.append(agent.prompt_template)

    return "\n\n".join(sections)
```

## Consequences

### Positive

1. **Optimal Context Usage**
   - Right information at right time
   - No wasted tokens on irrelevant data
   - Better agent responses

2. **Clear Organization**
   - Easy to find information
   - Simple to update
   - Good debugging

3. **Scalability**
   - Handles project growth
   - Supports multiple sprints
   - Extensible layers

### Negative

1. **Complexity**
   - Multiple storage locations
   - Loading logic needed
   - Token counting overhead

2. **Maintenance**
   - Must update multiple layers
   - Potential inconsistencies
   - More files to manage

3. **Performance**
   - File I/O overhead
   - Token estimation cost
   - Loading time increases

## Mitigations

1. **Complexity**: Clear documentation and tooling
2. **Maintenance**: Automated update scripts
3. **Performance**: Caching and lazy loading

## Testing Strategy

```python
def test_memory_loading():
    """Test memory loads within budget"""
    manager = MemoryManager(Path("."))
    context = manager.load_context_for_agent(
        "planner", "sprint-01", "planning", 10000
    )
    assert context.total_tokens <= 10000
    assert len(context.project) > 0
    assert len(context.sprint) > 0

def test_memory_priority():
    """Test priority loading order"""
    # With limited budget, agent memory loads first
    context = manager.load_context_for_agent(
        "coder", "sprint-01", "coding", 1000
    )
    assert len(context.agent) > 0
    assert len(context.project) == 0  # Didn't fit
```

## References

- Hierarchical Memory Systems
- Context Management in LLMs
- Token Optimization Strategies
- Claude Memory Best Practices

## Notes

Review if:
- Token usage patterns change significantly
- Memory grows beyond filesystem capacity
- Need real-time memory updates
- Move to distributed architecture
