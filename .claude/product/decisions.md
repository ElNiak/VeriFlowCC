# VeriFlowCC Architectural Decisions

## Decision Log

### ADR-001: File-based Memory Management

**Date**: Project Inception
**Status**: Accepted

**Context**: Need persistent storage for project artifacts and memory across sessions.

**Decision**: Use file-based storage with structured markdown and YAML files.

**Consequences**:

- ✅ Simple implementation for single developers
- ✅ Git-friendly for version control
- ✅ Human-readable artifacts
- ✅ No database dependencies
- ⚠️ May need optimization for large projects
- ❌ Not suitable for multi-user concurrent access

**Alternatives Considered**:

- SQLite database (too complex for MVP)
- Redis cache (requires external service)
- In-memory only (loses state between sessions)

______________________________________________________________________

### ADR-002: Claude-Code Native Agent Integration

**Date**: Project Inception
**Status**: Accepted

**Context**: Need to implement multiple specialized agents for V-Model phases.

**Decision**: Use Claude-Code's native agent spawning with context injection via Jinja2 templates.

**Consequences**:

- ✅ Leverages existing Claude-Code capabilities
- ✅ No need for custom agent framework
- ✅ Direct integration with Claude models
- ✅ Simplified implementation
- ⚠️ Dependent on Claude-Code API stability
- ❌ Less control over agent lifecycle

**Alternatives Considered**:

- Custom agent framework (too complex)
- External LLM orchestration (adds dependencies)
- Single monolithic agent (loses specialization benefits)

______________________________________________________________________

### ADR-003: Python-based Hook System

**Date**: Project Inception
**Status**: Accepted

**Context**: Need to enforce workflow rules and automate repetitive tasks.

**Decision**: Implement Python hooks for PreToolUse, PostToolUse, and Stop events.

**Consequences**:

- ✅ Native Python implementation
- ✅ Easy to extend and customize
- ✅ Synchronous execution model
- ✅ Direct file system access
- ⚠️ Performance overhead for each hook
- ❌ No async hook support initially

**Alternatives Considered**:

- Shell script hooks (less portable)
- Plugin system (too complex for MVP)
- No hooks (loses automation benefits)

______________________________________________________________________

### ADR-004: Typer for CLI Framework

**Date**: Project Inception
**Status**: Accepted

**Context**: Need a modern, type-safe CLI framework.

**Decision**: Use Typer for command-line interface implementation.

**Consequences**:

- ✅ Type-safe by default
- ✅ Automatic help generation
- ✅ Modern Python features
- ✅ Excellent developer experience
- ⚠️ Relatively new framework
- ❌ Smaller community than Click

**Alternatives Considered**:

- Click (more verbose, less type-safe)
- argparse (too low-level)
- Fire (too magical, less control)

______________________________________________________________________

### ADR-005: UV Package Manager

**Date**: Project Inception
**Status**: Accepted

**Context**: Need fast, reliable dependency management.

**Decision**: Use UV instead of pip/poetry for package management.

**Consequences**:

- ✅ 10-100x faster than alternatives
- ✅ Built-in lock file support
- ✅ Simpler dependency resolution
- ✅ Native workspace support
- ⚠️ Newer tool, less widespread adoption
- ❌ Team members may need to learn it

**Alternatives Considered**:

- pip + requirements.txt (slower, no lock file)
- Poetry (slower, more complex)
- pipenv (slower, less maintained)

______________________________________________________________________

### ADR-006: Agile V-Model Methodology

**Date**: Project Inception
**Status**: Accepted

**Context**: Need structured methodology for AI-assisted development.

**Decision**: Implement Agile V-Model with sprint-based V-cycles.

**Consequences**:

- ✅ Rigorous verification at each stage
- ✅ Clear traceability requirements to tests
- ✅ Suitable for safety-critical systems
- ✅ Combines agility with discipline
- ⚠️ More overhead than pure Agile
- ❌ May slow down rapid prototyping

**Alternatives Considered**:

- Pure Agile (lacks verification rigor)
- Waterfall V-Model (not iterative enough)
- No methodology (too chaotic with AI)

______________________________________________________________________

### ADR-007: Pydantic for Data Validation

**Date**: Project Inception
**Status**: Accepted

**Context**: Need to validate LLM outputs and ensure structured communication.

**Decision**: Use Pydantic for all data models and validation.

**Consequences**:

- ✅ Automatic validation of AI outputs
- ✅ Type safety throughout codebase
- ✅ Schema generation for documentation
- ✅ Excellent error messages
- ⚠️ Learning curve for complex validations
- ❌ Some performance overhead

**Alternatives Considered**:

- Manual validation (error-prone)
- marshmallow (less integrated with typing)
- attrs (less validation features)

______________________________________________________________________

### ADR-008: Full CLI-First MVP Approach

**Date**: 2025-08-10
**Status**: Accepted

**Context**: Need working PoC quickly with complete production commands, not simplified demos.

**Decision**: Implement full CLI with all commands from the start, no placeholders.

**Rationale**:

- User wants complete interface immediately
- No demo/simplified versions
- Full workflow validation from day one
- Performance and security optimizations deferred

**Implementation Order**:

1. `verifflowcc/cli.py` - All commands: init, plan, sprint, status, validate, checkpoint
1. `verifflowcc/core/orchestrator.py` - Complete V-Model state machine
1. `verifflowcc/agents/` - All 5 agent personas
1. `verifflowcc/core/context_manager.py` - Memory management

______________________________________________________________________

### ADR-009: Claude Code SDK Integration

**Date**: 2025-08-13
**Status**: Accepted

**Context**: Need to transition from mock agent implementations to real AI integration for production-ready V-Model workflow.

**Decision**: Use Claude Code SDK (`claude-code-sdk`) instead of traditional Anthropic API for all agent implementations.

**Rationale**:

- Claude Code SDK provides enhanced code generation capabilities
- Built-in streaming support for real-time feedback
- Session management and context persistence
- Optimized for development workflows
- Better integration with development tools

**Implementation Details**:

- SDK configuration centralized in `SDKConfig` class
- Agent factory pattern ensures consistent SDK integration
- Jinja2 templates for specialized V-Model prompts
- Mock mode fallback for testing and development
- Session state persistence across V-Model stages

**Consequences**:

- ✅ Real AI-powered V-Model execution
- ✅ Enhanced code generation capabilities
- ✅ Streaming responses for better UX
- ✅ Session persistence across stages
- ✅ Professional development-focused interface
- ⚠️ Dependency on Claude Code SDK stability
- ⚠️ Requires API key management
- ❌ Additional complexity over simple HTTP calls

**Alternatives Considered**:

- Traditional Anthropic API (limited development features)
- OpenAI API (less specialized for code workflows)
- Local LLM hosting (resource intensive, less capable)
- Continue with mock implementations (no real functionality)

______________________________________________________________________

## Design Principles

### 1. Simplicity First

- Prefer file-based over database
- Use existing tools over custom solutions
- Clear over clever code

### 2. Developer Experience

- Type hints everywhere
- Comprehensive error messages
- Interactive feedback during execution

### 3. Extensibility

- Plugin-ready architecture
- Clear interfaces between components
- Configuration over code changes

### 4. Quality Assurance

- Every feature must be testable
- 80% coverage minimum
- Automated quality checks

### 5. Context Preservation

- Never lose project state
- Automatic checkpointing
- Clear rollback mechanisms

## Open Questions

1. **Agent Communication**: Should agents communicate through files or Python objects?

   - Current thinking: Python objects with Pydantic, files for persistence

1. **Async vs Sync**: Should the orchestrator be async from the start?

   - Current thinking: Start sync, refactor to async in Phase 2

1. **Plugin System**: When to introduce plugin architecture?

   - Current thinking: Phase 4, after core is stable

1. **Web Interface**: Should we plan for web UI from the start?

   - Current thinking: CLI-first, web as optional in Phase 4

## Decisions Made for MVP

- [x] **Sprint Duration**: Flexible, user-defined per sprint
- [x] **Default Gating**: Soft gating (warnings but continue)
- [x] **Context Management**: Simple truncation at 100k tokens
- [x] **Error Recovery**: Basic retry with exponential backoff
- [x] **Logging**: Rich console output with --verbose flag

## Decisions Deferred (Post-MVP)

- [ ] Performance optimization strategies
- [ ] Security hardening approach
- [ ] Multi-user support architecture
- [ ] Plugin system design
- [ ] Web UI framework selection
