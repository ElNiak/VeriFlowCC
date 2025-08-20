# API Specification

This is the API specification for the spec detailed in @.agilevv/specs/2025-08-18-mailbuddy-integration-testing/spec.md

> Created: 2025-08-19
> Version: 1.0.0

## Claude Code SDK Integration Patterns

### SDK Client Initialization

#### Basic Client Setup

```python
from claude_code_sdk import Client
from verifflowcc.core.sdk_config import SDKConfig


class BaseAgent:
    def __init__(self, config: SDKConfig):
        self.config = config
        self.client = Client(
            api_key=config.api_key, base_url=config.base_url, timeout=config.timeout
        )
```

#### Environment-Based Configuration

```python
import os
from claude_code_sdk import Client

# Auto-detect API key from environment
client = Client(api_key=os.getenv("ANTHROPIC_API_KEY"), timeout=30, max_retries=3)
```

### Session Management with Document Storage

#### Session Creation and Context Preservation

```python
from claude_code_sdk import Client, Session
from pathlib import Path
import json


class VModelSessionManager:
    def __init__(self, client: Client, base_path: Path):
        self.client = client
        self.base_path = base_path
        self.session_file = base_path / "session_context.json"

    def create_session(self, stage: str) -> Session:
        """Create new session for V-Model stage"""
        session = self.client.create_session()

        # Load existing context if available
        context = self._load_session_context()
        if context:
            session.add_context(context)

        # Add stage-specific context
        session.add_context(
            {
                "stage": stage,
                "artifacts_path": str(self.base_path / "artifacts"),
                "previous_stages": self._get_completed_stages(),
            }
        )

        return session

    def save_session_context(self, session: Session):
        """Persist session context to disk"""
        context = {
            "messages": session.get_messages(),
            "artifacts": session.get_artifacts(),
            "metadata": session.get_metadata(),
        }

        with open(self.session_file, "w") as f:
            json.dump(context, f, indent=2)

    def _load_session_context(self) -> dict:
        """Load session context from disk"""
        if self.session_file.exists():
            with open(self.session_file, "r") as f:
                return json.load(f)
        return {}
```

### Agent Execution Patterns

#### Requirements Analyst Agent

```python
from claude_code_sdk import Session
from jinja2 import Template
import json


class RequirementsAnalyst:
    def __init__(self, client: Client, session_manager: VModelSessionManager):
        self.client = client
        self.session_manager = session_manager
        self.prompt_template = Template(self._load_prompt_template())

    async def analyze_requirements(self, user_stories: list) -> dict:
        """Analyze user stories for INVEST/SMART criteria"""
        session = self.session_manager.create_session("requirements")

        prompt = self.prompt_template.render(user_stories=user_stories, criteria="INVEST and SMART")

        response = await session.send_message(
            content=prompt,
            system="You are a Requirements Analyst specializing in INVEST/SMART validation.",
        )

        # Parse structured output
        analysis = self._parse_requirements_response(response.content)

        # Save session context
        self.session_manager.save_session_context(session)

        return analysis

    def _load_prompt_template(self) -> str:
        """Load Jinja2 template for requirements analysis"""
        template_path = Path("verifflowcc/prompts/requirements.j2")
        return template_path.read_text()

    def _parse_requirements_response(self, content: str) -> dict:
        """Parse AI response into structured format"""
        # Extract JSON from AI response
        # Implementation depends on response format
        pass
```

#### Architecture Agent

```python
class Architect:
    def __init__(self, client: Client, session_manager: VModelSessionManager):
        self.client = client
        self.session_manager = session_manager

    async def design_system(self, requirements: dict) -> dict:
        """Generate system design and PlantUML diagrams"""
        session = self.session_manager.create_session("architecture")

        # Add requirements context
        session.add_context(
            {
                "requirements": requirements,
                "existing_architecture": self._load_existing_architecture(),
            }
        )

        prompt = self._build_architecture_prompt(requirements)

        response = await session.send_message(
            content=prompt, system="You are a System Architect creating detailed technical designs."
        )

        design = self._extract_design_artifacts(response.content)

        # Generate PlantUML diagrams
        diagrams = await self._generate_plantuml_diagrams(session, design)
        design["diagrams"] = diagrams

        self.session_manager.save_session_context(session)
        return design

    async def _generate_plantuml_diagrams(self, session: Session, design: dict) -> list:
        """Generate PlantUML diagrams from design"""
        diagram_prompt = f"""
        Based on this system design, generate PlantUML diagrams:
        {json.dumps(design, indent=2)}

        Include: component diagram, sequence diagram for key flows
        """

        response = await session.send_message(content=diagram_prompt)
        return self._extract_plantuml_code(response.content)
```

#### Development Agent

```python
class Developer:
    def __init__(self, client: Client, session_manager: VModelSessionManager):
        self.client = client
        self.session_manager = session_manager

    async def implement_feature(self, design: dict, requirements: dict) -> dict:
        """Generate source code based on design and requirements"""
        session = self.session_manager.create_session("development")

        # Load full context
        session.add_context(
            {
                "design": design,
                "requirements": requirements,
                "codebase_structure": self._analyze_codebase(),
                "coding_standards": self._load_coding_standards(),
            }
        )

        prompt = self._build_implementation_prompt(design, requirements)

        # Stream response for real-time feedback
        async for chunk in session.stream_message(
            content=prompt,
            system="You are a Senior Developer implementing features with quality focus.",
        ):
            yield chunk  # Stream progress to user

        # Get final response
        response = await session.get_last_response()

        implementation = self._extract_code_artifacts(response.content)

        # Calculate quality metrics
        metrics = self._calculate_quality_metrics(implementation)
        implementation["quality_metrics"] = metrics

        self.session_manager.save_session_context(session)
        return implementation
```

#### QA Tester Agent

```python
class QATester:
    def __init__(self, client: Client, session_manager: VModelSessionManager):
        self.client = client
        self.session_manager = session_manager

    async def create_test_strategy(self, implementation: dict, requirements: dict) -> dict:
        """Develop comprehensive testing strategy"""
        session = self.session_manager.create_session("qa")

        session.add_context(
            {
                "implementation": implementation,
                "requirements": requirements,
                "test_framework": "pytest",
                "coverage_target": 80,
            }
        )

        prompt = self._build_qa_prompt(implementation, requirements)

        response = await session.send_message(
            content=prompt, system="You are a QA Engineer creating comprehensive test strategies."
        )

        test_strategy = self._parse_test_strategy(response.content)

        # Generate actual test code
        test_code = await self._generate_test_code(session, test_strategy)
        test_strategy["test_code"] = test_code

        self.session_manager.save_session_context(session)
        return test_strategy
```

#### Integration Agent

```python
class IntegrationAgent:
    def __init__(self, client: Client, session_manager: VModelSessionManager):
        self.client = client
        self.session_manager = session_manager

    async def validate_integration(self, all_artifacts: dict) -> dict:
        """Perform end-to-end validation and GO/NO-GO decision"""
        session = self.session_manager.create_session("integration")

        # Load complete V-Model context
        session.add_context(
            {
                "requirements": all_artifacts["requirements"],
                "architecture": all_artifacts["architecture"],
                "implementation": all_artifacts["implementation"],
                "test_results": all_artifacts["test_results"],
                "quality_gates": self._load_quality_gates(),
            }
        )

        validation_prompt = self._build_integration_prompt(all_artifacts)

        response = await session.send_message(
            content=validation_prompt,
            system="You are an Integration Specialist making GO/NO-GO release decisions.",
        )

        decision = self._parse_integration_decision(response.content)

        self.session_manager.save_session_context(session)
        return decision
```

### Streaming Response Handling

#### Real-Time Progress Updates

```python
async def stream_agent_execution(session: Session, prompt: str) -> AsyncGenerator[str, None]:
    """Stream agent responses for real-time feedback"""

    async for chunk in session.stream_message(content=prompt):
        if chunk.type == "content_delta":
            yield chunk.delta
        elif chunk.type == "message_start":
            yield f"Agent started: {chunk.message.role}\n"
        elif chunk.type == "message_stop":
            yield f"Agent completed.\n"


# Usage in orchestrator
async def execute_with_streaming(agent, method, *args):
    """Execute agent method with streaming output"""

    print(f"Starting {agent.__class__.__name__}...")

    async for chunk in method(*args):
        if isinstance(chunk, str):
            print(chunk, end="", flush=True)
        else:
            # Handle structured chunk data
            print(f"Progress: {chunk}")

    print(f"\n{agent.__class__.__name__} completed.")
```

### Structured Output Validation

#### Pydantic Models for AI Responses

```python
from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
from enum import Enum


class RequirementStatus(str, Enum):
    VALID = "valid"
    NEEDS_REFINEMENT = "needs_refinement"
    INVALID = "invalid"


class RequirementAnalysis(BaseModel):
    requirement_id: str
    content: str
    invest_score: float = Field(ge=0, le=1)
    smart_score: float = Field(ge=0, le=1)
    status: RequirementStatus
    issues: List[str] = []
    suggestions: List[str] = []


class ArchitectureDesign(BaseModel):
    components: List[Dict[str, Any]]
    interfaces: List[Dict[str, Any]]
    data_flow: List[Dict[str, Any]]
    plantuml_diagrams: List[str]
    design_decisions: List[Dict[str, Any]]


class ImplementationOutput(BaseModel):
    files: List[Dict[str, str]]  # filename -> content
    dependencies: List[str]
    quality_metrics: Dict[str, float]
    documentation: str


class TestStrategy(BaseModel):
    test_types: List[str]
    test_cases: List[Dict[str, Any]]
    coverage_plan: Dict[str, Any]
    test_code: List[Dict[str, str]]


class IntegrationDecision(BaseModel):
    decision: str = Field(regex=r"^(GO|NO-GO)$")
    confidence: float = Field(ge=0, le=1)
    criteria_met: List[str]
    blockers: List[str]
    recommendations: List[str]


# Validation decorator
def validate_ai_response(model_class: BaseModel):
    """Decorator to validate AI responses with Pydantic models"""

    def decorator(func):
        async def wrapper(*args, **kwargs):
            response = await func(*args, **kwargs)

            try:
                # Parse and validate response
                validated = model_class.parse_obj(response)
                return validated.dict()
            except Exception as e:
                raise ValueError(f"AI response validation failed: {e}")

        return wrapper

    return decorator


# Usage
class RequirementsAnalyst:
    @validate_ai_response(RequirementAnalysis)
    async def analyze_requirement(self, story: str) -> dict:
        # Implementation returns raw dict that gets validated
        pass
```

## Controllers

### V-Model Orchestrator Integration

```python
from verifflowcc.core.orchestrator import VModelOrchestrator


class SDKOrchestrator(VModelOrchestrator):
    """V-Model orchestrator with Claude Code SDK integration"""

    def __init__(self, config: SDKConfig):
        self.config = config
        self.client = Client(api_key=config.api_key)
        self.session_manager = VModelSessionManager(self.client, Path(".agilevv"))

        # Initialize all agents
        self.requirements_analyst = RequirementsAnalyst(self.client, self.session_manager)
        self.architect = Architect(self.client, self.session_manager)
        self.developer = Developer(self.client, self.session_manager)
        self.qa_tester = QATester(self.client, self.session_manager)
        self.integration_agent = IntegrationAgent(self.client, self.session_manager)

    async def execute_vmodel_sprint(self, user_stories: list) -> dict:
        """Execute complete V-Model sprint with SDK agents"""

        # Requirements phase
        requirements = await self.requirements_analyst.analyze_requirements(user_stories)

        # Architecture phase
        design = await self.architect.design_system(requirements)

        # Development phase (with streaming)
        implementation = {}
        async for progress in self.developer.implement_feature(design, requirements):
            print(progress, end="", flush=True)
            implementation = progress

        # QA phase
        test_strategy = await self.qa_tester.create_test_strategy(implementation, requirements)

        # Integration phase
        all_artifacts = {
            "requirements": requirements,
            "architecture": design,
            "implementation": implementation,
            "test_results": test_strategy,
        }

        decision = await self.integration_agent.validate_integration(all_artifacts)

        return {
            "sprint_results": all_artifacts,
            "integration_decision": decision,
            "session_context": self.session_manager._load_session_context(),
        }
```

### Error Handling Patterns

```python
from claude_code_sdk.exceptions import APIError, RateLimitError, TimeoutError


class SDKErrorHandler:
    """Simple error handling for SDK operations"""

    @staticmethod
    def handle_sdk_errors(func):
        """Decorator for basic SDK error handling"""

        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except RateLimitError as e:
                raise Exception(f"Rate limit exceeded: {e}")
            except TimeoutError as e:
                raise Exception(f"Request timeout: {e}")
            except APIError as e:
                raise Exception(f"API error: {e}")
            except Exception as e:
                raise Exception(f"Unexpected error: {e}")

        return wrapper


# Usage in agents
class BaseAgent:
    @SDKErrorHandler.handle_sdk_errors
    async def execute_agent_task(self, prompt: str) -> dict:
        # Agent implementation
        pass
```
