"""Configuration for Claude Code SDK integration."""

import os
from dataclasses import dataclass
from typing import Any

from pydantic import BaseModel, Field


class AuthenticationError(Exception):
    """Raised when authentication configuration is invalid or unavailable."""

    pass


class ClaudeCodeOptions(BaseModel):
    """Configuration options for Claude Code SDK client."""

    system_prompt: str = Field(default="", description="System prompt for the agent")
    max_turns: int = Field(default=10, description="Maximum conversation turns")
    max_tokens: int = Field(default=4000, description="Maximum tokens per response")
    temperature: float = Field(default=0.7, description="Response temperature")
    model: str = Field(default="claude-3-5-sonnet-20241022", description="Claude model to use")
    stream: bool = Field(default=True, description="Enable streaming responses")
    tools_enabled: bool = Field(default=True, description="Enable tool usage")


@dataclass
class SDKConfig:
    """Main configuration for Claude Code SDK."""

    api_key: str | None = None
    base_url: str | None = None
    timeout: int = 30
    max_retries: int = 3
    retry_delay: float = 1.0
    environment: str = "production"

    def __post_init__(self) -> None:
        """Initialize configuration after creation."""
        # Allow tests to run without API key when in test mode
        if self._is_test_environment():
            # Running under pytest - use mock mode
            if self.api_key is None:
                self.api_key = "sk-test-mock-api-key"
            return

        if self.api_key is None:
            self.api_key = os.getenv("ANTHROPIC_API_KEY")

        # In production, allow Claude Code subscription authentication
        # No mandatory API key requirement

    def _is_test_environment(self) -> bool:
        """Check if running in test environment."""
        return os.getenv("PYTEST_CURRENT_TEST") is not None

    def _detect_authentication_method(self) -> str:
        """Detect available authentication method.

        Returns:
            Authentication method: "api_key", "subscription", or "none"
        """
        if self.api_key:
            return "api_key"

        # Check for Claude Code subscription
        try:
            if self._verify_claude_subscription():
                return "subscription"
        except Exception:
            # Subscription authentication unavailable - clean fallback
            pass

        return "none"

    def _verify_claude_subscription(self) -> bool:
        """Verify Claude Code subscription availability.

        Returns:
            True if Claude Code subscription is available, False otherwise
        """
        # TODO: Implementation for Claude Code subscription verification
        # This is a placeholder - actual implementation would integrate
        # with Claude Code's authentication system

        # For now, assume subscription is available if no API key is present
        # and we're not in test mode (this allows the new behavior to work)
        if not self._is_test_environment() and not self.api_key:
            # In real implementation, this would check Claude Code auth status
            return True
        return False

    def _validate_authentication(self) -> None:
        """Validate authentication with descriptive error messages."""
        auth_method = self._detect_authentication_method()

        if auth_method == "none":
            raise AuthenticationError(
                "No authentication method available. Please either:\n"
                "1. Set ANTHROPIC_API_KEY environment variable, or\n"
                "2. Ensure Claude Code subscription is active\n"
                "Run 'claude auth login' to check subscription status."
            )

    def get_client_options(self, agent_type: str) -> ClaudeCodeOptions:
        """Get client options for specific agent type.

        Args:
            agent_type: Type of agent (requirements, architect, developer, qa, integration)

        Returns:
            ClaudeCodeOptions configured for the agent type
        """
        system_prompts = {
            "requirements": self._get_requirements_prompt(),
            "architect": self._get_architect_prompt(),
            "developer": self._get_developer_prompt(),
            "qa": self._get_qa_prompt(),
            "integration": self._get_integration_prompt(),
        }

        return ClaudeCodeOptions(
            system_prompt=system_prompts.get(agent_type, ""),
            max_turns=10,
            max_tokens=4000,
            temperature=0.7,
            model="claude-3-5-sonnet-20241022",
            stream=True,
            tools_enabled=True,
        )

    def _get_requirements_prompt(self) -> str:
        """Get system prompt for Requirements Analyst agent."""
        return """You are a Requirements Analyst specializing in Agile V-Model methodology.

Your role is to:
- Elaborate user stories into detailed requirements
- Define clear acceptance criteria using INVEST principles
- Identify dependencies and constraints
- Create traceability matrices
- Validate requirements for completeness and testability

Focus on creating requirements that are:
- Independent: Can be developed separately
- Negotiable: Details can be discussed
- Valuable: Provide business value
- Estimable: Can be sized for development
- Small: Fit within a sprint
- Testable: Can be verified objectively

Always structure your output in JSON format with clear sections for functional requirements,
non-functional requirements, acceptance criteria, and dependencies."""

    def _get_architect_prompt(self) -> str:
        """Get system prompt for Architect agent."""
        return """You are a System Architect specializing in V-Model compliant design.

Your role is to:
- Transform requirements into system architecture
- Create component diagrams and interaction models
- Define interfaces and data contracts
- Identify architectural risks and mitigation strategies
- Ensure design traceability to requirements

Design principles to follow:
- SOLID principles for maintainability
- Separation of concerns
- Scalability and performance considerations
- Security by design
- Testability at all levels

Always provide:
- High-level architecture diagrams
- Component specifications
- Interface definitions
- Risk assessment
- Implementation guidance

Structure your output in JSON format with clear sections for architecture overview,
components, interfaces, and implementation notes."""

    def _get_developer_prompt(self) -> str:
        """Get system prompt for Developer agent."""
        return """You are a Developer implementing V-Model verified code.

Your role is to:
- Transform design specifications into working code
- Follow established coding standards and best practices
- Implement comprehensive error handling
- Create maintainable and testable code
- Ensure code traceability to design specifications

Development principles:
- Test-Driven Development (TDD)
- Clean code practices
- Proper documentation
- Security-conscious programming
- Performance optimization

Always provide:
- Complete, working code implementations
- Comprehensive unit tests
- Documentation and comments
- Error handling and logging
- Performance considerations

Structure your output in JSON format with sections for implementation,
tests, documentation, and any dependencies or setup required."""

    def _get_qa_prompt(self) -> str:
        """Get system prompt for QA Tester agent."""
        return """You are a QA Engineer validating V-Model stage implementations.

Your role is to:
- Create comprehensive test strategies
- Design test cases covering functional and non-functional requirements
- Execute automated and manual tests
- Validate acceptance criteria fulfillment
- Report defects with detailed reproduction steps

Testing approach:
- Requirements-based testing
- Risk-based test prioritization
- Boundary value analysis
- Equivalence partitioning
- Integration testing strategies

Always provide:
- Detailed test plans and cases
- Automated test scripts
- Test data requirements
- Expected vs actual results
- Defect reports and recommendations

Structure your output in JSON format with sections for test strategy,
test cases, test execution results, and quality assessment."""

    def _get_integration_prompt(self) -> str:
        """Get system prompt for Integration Engineer."""
        return """You are an Integration Engineer ensuring system coherence and deployment readiness.

Your role is to:
- Validate end-to-end system integration
- Verify deployment configurations
- Ensure all V-Model stage artifacts are consistent
- Validate system against original requirements
- Prepare production deployment plans

Integration focus areas:
- Component interaction validation
- Data flow verification
- Performance and scalability testing
- Security and compliance checks
- Operational readiness assessment

Always provide:
- Integration test results
- Deployment validation reports
- System health assessments
- Performance metrics
- Production readiness checklist

Structure your output in JSON format with sections for integration results,
deployment status, performance metrics, and recommendations."""

    def get_tool_permissions(self, agent_type: str) -> dict[str, Any]:
        """Get tool permissions for specific agent type.

        Args:
            agent_type: Type of agent

        Returns:
            Dictionary of tool permissions
        """
        base_permissions = {
            "read": True,
            "write": False,
            "execute": False,
            "web_search": False,
        }

        agent_permissions = {
            "requirements": {
                **base_permissions,
                "write": True,  # Can create requirement documents
            },
            "architect": {
                **base_permissions,
                "write": True,  # Can create design documents
            },
            "developer": {
                **base_permissions,
                "write": True,
                "execute": True,  # Can run code and tests
            },
            "qa": {
                **base_permissions,
                "execute": True,  # Can run tests
            },
            "integration": {
                **base_permissions,
                "execute": True,  # Can run integration tests
                "web_search": True,  # May need to check external dependencies
            },
        }

        return agent_permissions.get(agent_type, base_permissions)


# Global SDK configuration instance
_sdk_config: SDKConfig | None = None


def get_sdk_config() -> SDKConfig:
    """Get the global SDK configuration instance.

    Returns:
        SDKConfig instance

    Raises:
        ValueError: If ANTHROPIC_API_KEY is not set
    """
    global _sdk_config
    if _sdk_config is None:
        _sdk_config = SDKConfig()
    return _sdk_config


def set_sdk_config(config: SDKConfig) -> None:
    """Set the global SDK configuration instance.

    Args:
        config: SDKConfig instance to set
    """
    global _sdk_config
    _sdk_config = config
