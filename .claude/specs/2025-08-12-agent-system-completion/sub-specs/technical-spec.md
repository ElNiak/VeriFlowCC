# Technical Specification

This is the technical specification for the spec detailed in @.claude/specs/2025-08-12-agent-system-completion/spec.md

> Created: 2025-08-12
> Version: 1.0.0

## Technical Requirements

### Agent Architecture Requirements

- **BaseAgent Inheritance**: All agents must inherit from `verifflowcc.agents.base.BaseAgent` and implement the abstract `process()` method
- **Async Operation**: All agent operations must be async to support AI API calls using `anthropic` SDK
- **PathConfig Integration**: All agents must accept `path_config` parameter for test isolation compatibility
- **Pydantic Validation**: All agent inputs and outputs must use Pydantic models for structured data validation
- **Artifact Management**: Agents must save artifacts using standardized naming in appropriate subdirectories under `.agilevv/`
- **Error Handling**: Comprehensive error handling with structured logging and retry logic for API failures

### Specific Agent Requirements

#### ArchitectAgent (Design Stage)
- **Input**: Requirements artifacts from RequirementsAnalyst
- **Output**: Design documents, architecture.md updates, interface specifications  
- **Responsibilities**: System design creation, component architecture, interface contracts
- **Artifacts**: `design/{story_id}.json`, architecture.md updates, interface specifications
- **V-Model Stage**: DESIGN

#### DeveloperAgent (Coding Stage)
- **Input**: Design specifications from ArchitectAgent
- **Output**: Source code, implementation reports, code metrics
- **Responsibilities**: Feature implementation, code generation, quality validation
- **Artifacts**: Source files, `implementation/{story_id}.json`, code metrics
- **V-Model Stage**: CODING

#### QATesterAgent (Testing Stages)
- **Input**: Requirements, design, and implementation artifacts
- **Output**: Test suites, test reports, coverage analysis, quality validation
- **Responsibilities**: Test generation, test execution, acceptance criteria validation
- **Artifacts**: Test files, `testing/{story_id}.json`, coverage reports
- **V-Model Stages**: UNIT_TESTING, INTEGRATION_TESTING, SYSTEM_TESTING

#### IntegrationAgent (Integration Stage)
- **Input**: All previous stage artifacts
- **Output**: Integration reports, deployment validation, system health checks
- **Responsibilities**: System integration validation, deployment verification, end-to-end testing
- **Artifacts**: Integration configs, `integration/{story_id}.json`, system reports
- **V-Model Stage**: INTEGRATION_TESTING

### Data Schema Requirements

#### Base Schemas
```python
class AgentInput(BaseModel):
    story_id: str
    stage: VModelStage
    context: dict[str, Any]
    previous_artifacts: dict[str, Any] = {}

class AgentOutput(BaseModel):
    status: str  # "success" | "error" | "partial"
    artifacts: dict[str, Any]
    metrics: dict[str, Any] = {}
    next_stage_ready: bool = False
    errors: list[str] = []
```

#### Agent-Specific Schemas
- **DesignInput/DesignOutput**: For ArchitectAgent with requirements and design artifacts
- **ImplementationInput/ImplementationOutput**: For DeveloperAgent with design specs and code
- **TestingInput/TestingOutput**: For QATesterAgent with multi-stage test requirements
- **IntegrationInput/IntegrationOutput**: For IntegrationAgent with comprehensive system data

### Orchestrator Integration Requirements

#### _initialize_agents() Method Updates
```python
def _initialize_agents(self) -> dict[str, Any]:
    return {
        "requirements_analyst": RequirementsAnalystAgent(self.config_path),
        "architect": ArchitectAgent(self.config_path),
        "developer": DeveloperAgent(self.config_path),
        "qa_tester": QATesterAgent(self.config_path),
        "integration": IntegrationAgent(self.config_path),
    }
```

#### _execute_stage_logic() Method Updates
- **DESIGN Stage**: Execute ArchitectAgent with requirements context
- **CODING Stage**: Execute DeveloperAgent with design context  
- **UNIT_TESTING/INTEGRATION_TESTING/SYSTEM_TESTING**: Execute QATesterAgent with appropriate context
- **INTEGRATION_TESTING**: Execute IntegrationAgent for system validation

### Quality Assurance Requirements

- **Test Coverage**: Minimum 90% code coverage for all new agent implementations
- **TDD Approach**: Tests must be written before implementation for each agent
- **Integration Testing**: Full orchestrator integration tests with all agents
- **Performance**: Agent execution must complete within reasonable timeframes (< 5 minutes per stage)
- **Error Recovery**: Graceful handling of AI API failures with retry mechanisms

### File Structure Requirements

```
verifflowcc/
├── agents/
│   ├── architect.py          # ArchitectAgent implementation
│   ├── developer.py          # DeveloperAgent implementation  
│   ├── qa_tester.py          # QATesterAgent implementation
│   └── integration.py        # IntegrationAgent implementation
├── schemas/
│   └── agent_schemas.py      # Pydantic schemas for all agents
└── core/
    └── orchestrator.py       # Updated with agent integration

tests/
├── agents/
│   ├── test_architect.py     # ArchitectAgent tests
│   ├── test_developer.py     # DeveloperAgent tests
│   ├── test_qa_tester.py     # QATesterAgent tests
│   └── test_integration.py   # IntegrationAgent tests
└── integration/
    └── test_orchestrator_integration.py  # Full integration tests
```

### Configuration Requirements

- **Model Configuration**: Support for different Claude models per agent via config
- **Token Limits**: Configurable max_tokens per agent for different use cases
- **Timeout Settings**: Configurable timeouts for AI API calls
- **Retry Logic**: Configurable retry attempts and backoff strategies