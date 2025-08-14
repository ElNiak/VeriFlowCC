"""Base Agent class for VeriFlowCC subagents."""

import json
import logging
from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator
from pathlib import Path
from typing import Any

try:
    from claude_code_sdk import ClaudeCodeOptions as SDKClaudeCodeOptions
    from claude_code_sdk import ClaudeSDKClient

    SDK_AVAILABLE = True
except ImportError:
    # Fallback for testing or when SDK not available
    class MockSDKClient:
        pass

    class MockSDKOptions:
        pass

    SDKClaudeCodeOptions = MockSDKOptions  # type: ignore[misc,assignment]
    ClaudeSDKClient = MockSDKClient  # type: ignore[misc,assignment]
    SDK_AVAILABLE = False

from jinja2 import Template

from verifflowcc.core.path_config import PathConfig
from verifflowcc.core.sdk_config import SDKConfig, get_sdk_config

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """Base class for all VeriFlowCC subagents using Claude Code SDK."""

    def __init__(
        self,
        name: str,
        agent_type: str,
        path_config: PathConfig | None = None,
        sdk_config: SDKConfig | None = None,
        mock_mode: bool = False,
    ):
        """Initialize the base agent.

        Args:
            name: Agent name identifier
            agent_type: Type of agent (requirements, architect, developer, qa, integration)
            path_config: PathConfig instance for managing project paths
            sdk_config: SDK configuration instance
            mock_mode: Whether to use mock responses instead of real API calls
        """
        self.name = name
        self.agent_type = agent_type
        self.path_config = path_config or PathConfig()
        self.sdk_config = sdk_config or get_sdk_config()
        self.mock_mode = mock_mode or not SDK_AVAILABLE
        self.context: dict[str, Any] = {}
        self.session_history: list[dict[str, str]] = []

        # Get agent-specific configuration
        self.client_options = self.sdk_config.get_client_options(agent_type)
        self.tool_permissions = self.sdk_config.get_tool_permissions(agent_type)

    @abstractmethod
    async def process(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """Process input and return structured output.

        Args:
            input_data: Input data for the agent

        Returns:
            Structured output from the agent
        """
        pass

    async def _call_claude_sdk(self, prompt: str, context: dict[str, Any] | None = None) -> str:
        """Call Claude Code SDK with the given prompt.

        Args:
            prompt: The prompt to send to Claude
            context: Additional context data

        Returns:
            Response from Claude

        Raises:
            RuntimeError: If SDK is not available and not in mock mode
        """
        if self.mock_mode:
            return self._get_mock_response(prompt, context)

        if not SDK_AVAILABLE:
            raise RuntimeError(
                "Claude Code SDK not available. Install with: pip install claude-code-sdk"
            )

        try:
            # Create SDK-compatible options
            sdk_options: Any = None
            if SDK_AVAILABLE:
                sdk_options = SDKClaudeCodeOptions(**self.client_options.__dict__)

            async with ClaudeSDKClient(options=sdk_options) as client:
                await client.query(prompt)

                response_parts: list[str] = []
                async for message in client.receive_response():
                    # Handle different message types properly
                    if hasattr(message, "type") and message.type == "text":
                        content = getattr(message, "content", "")
                        response_parts.append(content)
                    elif isinstance(message, dict):
                        if message.get("type") == "text":
                            response_parts.append(message.get("content", ""))

                response = "".join(response_parts)

                # Store in session history
                self.session_history.append({"role": "user", "content": prompt})
                self.session_history.append({"role": "assistant", "content": response})

                return response

        except Exception as e:
            logger.error(f"Error calling Claude SDK for agent {self.name}: {e}")
            raise

        # This should never be reached, but satisfies mypy
        return ""

    def _get_mock_response(self, prompt: str, context: dict[str, Any] | None = None) -> str:
        """Get a mock response for testing purposes.
        TODO: Create separate MockAgent class for better separation of concerns.
        Args:
            prompt: The prompt that was sent
            context: Additional context data

        Returns:
            Mock JSON response appropriate for the agent type
        """
        mock_responses = {  # TODO: Create separate file for mock responses
            "requirements": {
                "functional_requirements": [
                    "REQ-001: System shall provide user authentication",
                    "REQ-002: System shall maintain user session state",
                ],
                "non_functional_requirements": [
                    "NFR-001: System response time shall be <200ms",
                    "NFR-002: System shall handle 100 concurrent users",
                ],
                "acceptance_criteria": [
                    "AC-001: User can log in with valid credentials",
                    "AC-002: Invalid credentials show error message",
                ],
                "dependencies": ["Authentication service", "Database connectivity"],
            },
            "architect": {
                "architecture_overview": "Microservices architecture with API gateway",
                "components": [
                    {"name": "API Gateway", "type": "service", "interfaces": ["REST"]},
                    {"name": "Auth Service", "type": "service", "interfaces": ["gRPC"]},
                ],
                "interfaces": [{"name": "UserAuth", "type": "REST", "endpoint": "/auth/login"}],
                "risks": ["Single point of failure in API gateway"],
                "implementation_notes": "Use containerized deployment with Kubernetes",
            },
            "developer": {
                "implementation": "# Implementation code would go here\nclass UserService:\n    def authenticate(self, credentials):\n        pass",
                "tests": "# Test code would go here\ndef test_authentication():\n    assert True",
                "documentation": "## UserService\n\nProvides user authentication functionality",
                "dependencies": ["fastapi", "sqlalchemy"],
                "setup_instructions": ["pip install requirements", "run migrations"],
            },
            "qa": {
                "test_strategy": "Risk-based testing focusing on authentication flow",
                "test_cases": [
                    {"id": "TC-001", "description": "Valid login test", "priority": "high"},
                    {"id": "TC-002", "description": "Invalid login test", "priority": "high"},
                ],
                "test_execution_results": [
                    {"test_case": "TC-001", "status": "pass", "execution_time": "0.5s"},
                    {"test_case": "TC-002", "status": "pass", "execution_time": "0.3s"},
                ],
                "quality_assessment": {"coverage": "85%", "pass_rate": "100%", "risk_level": "low"},
            },
            "integration": {
                "integration_results": {
                    "component_tests": "All components integrated successfully",
                    "api_tests": "All API endpoints responding correctly",
                    "database_tests": "Database connections established",
                },
                "deployment_status": {
                    "environment": "staging",
                    "status": "ready",
                    "health_check": "passed",
                },
                "performance_metrics": {
                    "response_time": "150ms",
                    "throughput": "95 req/s",
                    "error_rate": "0.1%",
                },
                "recommendations": [
                    "Ready for production deployment",
                    "Monitor error rates closely",
                ],
            },
        }

        mock_data = mock_responses.get(
            self.agent_type, {"status": "mock_response", "agent": self.agent_type}
        )
        return json.dumps(mock_data, indent=2)

    def load_prompt_template(self, template_name: str, **variables: Any) -> str:
        """Load and render a Jinja2 template from the prompts directory.

        Args:
            template_name: Name of the template file (without .j2 extension)
            **variables: Variables to substitute in the template

        Returns:
            Rendered template content as string
        """
        template_path = Path("verifflowcc/prompts") / f"{template_name}.j2"

        if template_path.exists():
            template_content = template_path.read_text()
            template = Template(template_content)
            return template.render(**variables, **self.context)

        # Fallback: return a basic template based on agent type
        return self._get_fallback_template(template_name, **variables)

    def _get_fallback_template(self, template_name: str, **variables: Any) -> str:
        """Get a fallback template when template file doesn't exist.

        Args:
            template_name: Name of the template
            **variables: Template variables

        Returns:
            Basic template string
        """
        base_template = f"""You are a {self.agent_type} agent working on: {{task_description}}

Context:
{{context}}

Please provide your response in structured JSON format appropriate for a {self.agent_type} agent.
"""

        template = Template(base_template)
        return template.render(**variables, **self.context)

    def save_artifact(self, artifact_name: str, content: Any) -> None:
        """Save an artifact to the .agilevv directory.

        Args:
            artifact_name: Name of the artifact
            content: Content to save
        """
        artifact_path = self.path_config.base_dir / artifact_name
        artifact_path.parent.mkdir(parents=True, exist_ok=True)

        if isinstance(content, dict):
            artifact_path.write_text(json.dumps(content, indent=2))
        else:
            artifact_path.write_text(str(content))

        logger.debug(f"Saved artifact {artifact_name} for agent {self.name}")

    def load_artifact(self, artifact_name: str) -> Any:
        """Load an artifact from the .agilevv directory.

        Args:
            artifact_name: Name of the artifact

        Returns:
            Artifact content
        """
        artifact_path = self.path_config.base_dir / artifact_name
        if artifact_path.exists():
            content = artifact_path.read_text()
            if artifact_name.endswith(".json"):
                return json.loads(content)
            return content
        return None

    def save_session_state(self) -> None:
        """Save the current session state to an artifact."""
        session_state = {
            "agent_type": self.agent_type,
            "context": self.context,
            "session_history": self.session_history,
            "tool_permissions": self.tool_permissions,
        }
        self.save_artifact(f"session_state_{self.agent_type}.json", session_state)

    def load_session_state(self) -> bool:
        """Load session state from an artifact.

        Returns:
            True if session state was loaded, False otherwise
        """
        session_state = self.load_artifact(f"session_state_{self.agent_type}.json")
        if session_state:
            self.context.update(session_state.get("context", {}))
            self.session_history = session_state.get("session_history", [])
            return True
        return False

    async def execute(self, **kwargs: Any) -> dict[str, Any]:
        """Execute the agent with given parameters.

        Args:
            **kwargs: Parameters for agent execution

        Returns:
            Agent execution results
        """
        try:
            logger.info(f"Executing agent {self.name} ({self.agent_type})")

            # Load any existing session state
            self.load_session_state()

            # Update context with execution parameters
            self.context.update(kwargs)

            # Process the request
            result = await self.process(kwargs)

            # Save session state after processing
            self.save_session_state()

            return {
                "status": "success",
                "agent": self.name,
                "agent_type": self.agent_type,
                "result": result,
                "session_turns": len(self.session_history)
                // 2,  # Divide by 2 for user/assistant pairs
            }

        except Exception as e:
            logger.error(f"Error executing agent {self.name}: {e}")
            return {
                "status": "error",
                "agent": self.name,
                "agent_type": self.agent_type,
                "error": str(e),
                "error_type": type(e).__name__,
            }

    async def stream_process(
        self, input_data: dict[str, Any]
    ) -> AsyncGenerator[dict[str, Any], None]:
        """Process input with streaming responses.

        Args:
            input_data: Input data for the agent

        Yields:
            Streaming updates from the agent processing
        """
        try:
            yield {"status": "started", "agent": self.name, "agent_type": self.agent_type}

            # Load session state
            self.load_session_state()
            self.context.update(input_data)

            # If in mock mode, yield mock response
            if self.mock_mode:
                yield {"status": "processing", "message": "Processing with mock data"}
                result = await self.process(input_data)
                yield {"status": "completed", "result": result}
                return

            # Real streaming with Claude Code SDK
            if not SDK_AVAILABLE:
                raise RuntimeError("Claude Code SDK not available")

            prompt = self.load_prompt_template(self.agent_type, **input_data)

            # Create SDK-compatible options
            sdk_options: Any = None
            if SDK_AVAILABLE:
                sdk_options = SDKClaudeCodeOptions(**self.client_options.__dict__)

            async with ClaudeSDKClient(options=sdk_options) as client:
                await client.query(prompt)

                response_parts: list[str] = []
                async for message in client.receive_response():
                    # Handle different message types properly
                    if hasattr(message, "type") and message.type == "text":
                        content = getattr(message, "content", "")
                        response_parts.append(content)
                        yield {"status": "streaming", "content": content}
                    elif isinstance(message, dict):
                        if message.get("type") == "text":
                            content = message.get("content", "")
                            response_parts.append(content)
                            yield {"status": "streaming", "content": content}

                # Process complete response
                full_response = "".join(response_parts)
                result = await self._parse_response(full_response, input_data)

                # Save session state
                self.save_session_state()

                yield {"status": "completed", "result": result}

        except Exception as e:
            logger.error(f"Error in stream_process for agent {self.name}: {e}")
            yield {"status": "error", "error": str(e), "error_type": type(e).__name__}

    async def _parse_response(self, response: str, input_data: dict[str, Any]) -> dict[str, Any]:
        """Parse the response from Claude into structured data.

        Args:
            response: Raw response from Claude
            input_data: Original input data

        Returns:
            Parsed and structured response data
        """
        try:
            # Try to parse as JSON first
            if response.strip().startswith("{") and response.strip().endswith("}"):
                parsed_result: dict[str, Any] = json.loads(response)
                return parsed_result

            # If not JSON, return as structured text response
            structured_response: dict[str, Any] = {
                "response_text": response,
                "agent_type": self.agent_type,
                "processed_at": self.context.get("timestamp", "unknown"),
                "input_summary": str(input_data)[:200] + "..."
                if len(str(input_data)) > 200
                else str(input_data),
            }
            return structured_response

        except json.JSONDecodeError:
            logger.warning(f"Could not parse response as JSON for agent {self.name}")
            error_response: dict[str, Any] = {
                "response_text": response,
                "agent_type": self.agent_type,
                "parse_error": "Could not parse as JSON",
            }
            return error_response
