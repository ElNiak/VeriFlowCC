"""Agent factory for creating SDK-based V-Model agents."""

import logging
from typing import Any

from verifflowcc.core.path_config import PathConfig
from verifflowcc.core.sdk_config import SDKConfig, get_sdk_config

from .base import BaseAgent

logger = logging.getLogger(__name__)


class AgentFactory:
    """Factory for creating V-Model agents with Claude Code SDK integration."""

    def __init__(
        self,
        sdk_config: SDKConfig | None = None,
        path_config: PathConfig | None = None,
        mock_mode: bool = False,
    ):
        """Initialize the agent factory.

        Args:
            sdk_config: SDK configuration instance
            path_config: Path configuration instance
            mock_mode: Whether to create agents in mock mode
        """
        self.sdk_config = sdk_config or get_sdk_config()
        self.path_config = path_config or PathConfig()
        self.mock_mode = mock_mode
        self._agent_registry: dict[str, type[BaseAgent]] = {}
        self._register_default_agents()

    def _register_default_agents(self) -> None:
        """Register default V-Model agents."""
        try:
            from .architect import ArchitectAgent
            from .developer import DeveloperAgent
            from .integration import IntegrationAgent
            from .qa_tester import QATesterAgent
            from .requirements_analyst import RequirementsAnalystAgent

            self._agent_registry = {
                "requirements_analyst": RequirementsAnalystAgent,
                "architect": ArchitectAgent,
                "developer": DeveloperAgent,
                "qa_tester": QATesterAgent,
                "integration": IntegrationAgent,
            }
            logger.info("Registered default V-Model agents")

        except ImportError as e:
            logger.warning(f"Could not import some agents: {e}. They may not be updated yet.")
            # Keep registry empty if imports fail - agents will be created with fallback

    def register_agent(self, agent_type: str, agent_class: type[BaseAgent]) -> None:
        """Register a custom agent type.

        Args:
            agent_type: Type identifier for the agent
            agent_class: Agent class to register
        """
        self._agent_registry[agent_type] = agent_class
        logger.info(f"Registered custom agent type: {agent_type}")

    def create_agent(self, agent_type: str, name: str | None = None) -> BaseAgent:
        """Create an agent of the specified type.

        Args:
            agent_type: Type of agent to create (requirements, architect, developer, qa, integration)
            name: Custom name for the agent (defaults to agent_type)

        Returns:
            BaseAgent instance

        Raises:
            ValueError: If agent_type is not supported
        """
        # Map short names to full names for backwards compatibility
        short_name_mapping = {
            "requirements": "requirements_analyst",
            "qa": "qa_tester",
        }

        # Use full name if short name is provided
        full_agent_type = short_name_mapping.get(agent_type, agent_type)

        # Check if it's a valid default agent type or registered custom type
        default_agent_types = [
            "requirements_analyst",
            "architect",
            "developer",
            "qa_tester",
            "integration",
        ]

        if full_agent_type not in default_agent_types and agent_type not in self._agent_registry:
            raise ValueError(f"Unsupported agent type: {agent_type}")

        # Use the original agent_type for lookups (to allow custom registered names)
        lookup_type = agent_type if agent_type in self._agent_registry else full_agent_type

        agent_name = name or f"{agent_type}_agent"

        # Try to use registered agent class
        if lookup_type in self._agent_registry:
            agent_class = self._agent_registry[lookup_type]
            return agent_class(
                name=agent_name,
                agent_type=agent_type,
                path_config=self.path_config,
                sdk_config=self.sdk_config,
                mock_mode=self.mock_mode,
            )

        # Fallback: create a generic agent with the base class
        logger.warning(f"No specific agent class for {agent_type}, creating task agent")
        return TaskAgent(
            name=agent_name,
            agent_type=agent_type,
            path_config=self.path_config,
            sdk_config=self.sdk_config,
            mock_mode=self.mock_mode,
        )

    def create_all_agents(self) -> dict[str, BaseAgent]:
        """Create all V-Model agents.

        Returns:
            Dictionary mapping agent types to agent instances
        """
        agent_types = ["requirements_analyst", "architect", "developer", "qa_tester", "integration"]
        agents = {}

        for agent_type in agent_types:
            try:
                agents[agent_type] = self.create_agent(agent_type)
                logger.info(f"Created {agent_type} agent")
            except Exception as e:
                logger.error(f"Failed to create {agent_type} agent: {e}")

        return agents

    def list_available_agents(self) -> dict[str, str]:
        """List all available agent types and their descriptions.

        Returns:
            Dictionary mapping agent types to descriptions
        """
        return {
            "requirements_analyst": "Requirements Analyst - Elaborates user stories and defines acceptance criteria",
            "architect": "System Architect - Designs system architecture and component interfaces",
            "developer": "Developer - Implements code following design specifications",
            "qa_tester": "QA Tester - Creates and executes test strategies and cases",
            "integration": "Integration Engineer - Validates system integration and deployment readiness",
        }


class TaskAgent(BaseAgent):
    """Generic task agent when specific agent implementations are not available."""

    async def process(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """Process input using generic agent logic.

        Args:
            input_data: Input data for processing

        Returns:
            Structured output from generic processing
        """
        # Load appropriate template or use fallback
        prompt = self.load_prompt_template(self.agent_type, **input_data)

        # Call Claude SDK or return mock response
        response = await self._call_claude_sdk(prompt, input_data)

        # Parse and return response
        return await self._parse_response(response, input_data)


# Global factory instance
_agent_factory: AgentFactory | None = None


def get_agent_factory(
    sdk_config: SDKConfig | None = None,
    path_config: PathConfig | None = None,
    mock_mode: bool = False,
) -> AgentFactory:
    """Get the global agent factory instance.

    Args:
        sdk_config: SDK configuration instance
        path_config: Path configuration instance
        mock_mode: Whether to use mock mode

    Returns:
        AgentFactory instance
    """
    global _agent_factory
    if _agent_factory is None:
        _agent_factory = AgentFactory(sdk_config, path_config, mock_mode)
    return _agent_factory


def set_agent_factory(factory: AgentFactory) -> None:
    """Set the global agent factory instance.

    Args:
        factory: AgentFactory instance to set
    """
    global _agent_factory
    _agent_factory = factory
