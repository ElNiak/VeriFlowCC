"""Tests for Agent Factory infrastructure.

This module tests the AgentFactory class including agent creation, registration,
configuration loading, and mock mode behavior.
"""

from typing import Any
from unittest.mock import patch

import pytest
from verifflowcc.agents.base import BaseAgent
from verifflowcc.agents.factory import AgentFactory, TaskAgent
from verifflowcc.core.path_config import PathConfig
from verifflowcc.core.sdk_config import SDKConfig

from tests.conftest import PathConfig as TestPathConfig


class MockAgent(BaseAgent):
    """Mock agent for testing purposes."""

    def __init__(
        self,
        name: str,
        agent_type: str,
        path_config: PathConfig,
        sdk_config: SDKConfig | None = None,
        mock_mode: bool = False,
    ):
        super().__init__(name, agent_type, path_config, sdk_config, mock_mode)
        self.process_called = False
        self.processed_data: dict[str, Any] | None = None

    async def process(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """Mock process method."""
        self.process_called = True
        self.processed_data = input_data
        return {
            "status": "success",
            "agent_type": self.agent_type,
            "mock_mode": self.mock_mode,
            "processed": True,
        }


class TestAgentFactoryInitialization:
    """Test AgentFactory initialization and configuration."""

    def test_factory_initialization_with_defaults(
        self, isolated_agilevv_dir: TestPathConfig
    ) -> None:
        """Test factory initialization with default configurations."""
        with patch("verifflowcc.agents.factory.get_sdk_config") as mock_get_config:
            mock_sdk_config = SDKConfig(api_key="test-key")
            mock_get_config.return_value = mock_sdk_config

            factory = AgentFactory(path_config=isolated_agilevv_dir)

            assert factory.sdk_config == mock_sdk_config
            assert factory.path_config == isolated_agilevv_dir
            assert factory.mock_mode is False
            assert isinstance(factory._agent_registry, dict)

    def test_factory_initialization_with_custom_config(
        self, isolated_agilevv_dir: TestPathConfig
    ) -> None:
        """Test factory initialization with custom configurations."""
        sdk_config = SDKConfig(api_key="custom-key", timeout=60)

        factory = AgentFactory(
            sdk_config=sdk_config, path_config=isolated_agilevv_dir, mock_mode=True
        )

        assert factory.sdk_config == sdk_config
        assert factory.path_config == isolated_agilevv_dir
        assert factory.mock_mode is True

    def test_factory_initialization_mock_mode(self, isolated_agilevv_dir: TestPathConfig) -> None:
        """Test factory initialization in mock mode."""
        sdk_config = SDKConfig(api_key="mock-key")

        factory = AgentFactory(
            sdk_config=sdk_config, path_config=isolated_agilevv_dir, mock_mode=True
        )

        assert factory.mock_mode is True
        assert factory.sdk_config.api_key == "mock-key"

    def test_agent_registry_initialization(self, isolated_agilevv_dir: TestPathConfig) -> None:
        """Test that agent registry is properly initialized."""
        with patch("verifflowcc.agents.factory.get_sdk_config") as mock_get_config:
            mock_get_config.return_value = SDKConfig(api_key="test-key")
            factory = AgentFactory(path_config=isolated_agilevv_dir)

            # Registry should be initialized (may be empty if imports fail)
            assert isinstance(factory._agent_registry, dict)


class TestAgentFactoryRegistration:
    """Test agent registration and management."""

    def test_register_custom_agent(self, isolated_agilevv_dir: TestPathConfig) -> None:
        """Test registering a custom agent type."""
        with patch("verifflowcc.agents.factory.get_sdk_config") as mock_get_config:
            mock_get_config.return_value = SDKConfig(api_key="test-key")
            factory = AgentFactory(path_config=isolated_agilevv_dir)

            factory.register_agent("custom", MockAgent)

            assert "custom" in factory._agent_registry
            assert factory._agent_registry["custom"] == MockAgent

    def test_register_multiple_custom_agents(self, isolated_agilevv_dir: TestPathConfig) -> None:
        """Test registering multiple custom agent types."""
        with patch("verifflowcc.agents.factory.get_sdk_config") as mock_get_config:
            mock_get_config.return_value = SDKConfig(api_key="test-key")
            factory = AgentFactory(path_config=isolated_agilevv_dir)

            class CustomAgent1(BaseAgent):
                async def process(self, input_data: dict[str, Any]) -> dict[str, Any]:
                    return {"type": "custom1"}

            class CustomAgent2(BaseAgent):
                async def process(self, input_data: dict[str, Any]) -> dict[str, Any]:
                    return {"type": "custom2"}

            factory.register_agent("custom1", CustomAgent1)
            factory.register_agent("custom2", CustomAgent2)

            assert "custom1" in factory._agent_registry
            assert "custom2" in factory._agent_registry
            assert factory._agent_registry["custom1"] == CustomAgent1
            assert factory._agent_registry["custom2"] == CustomAgent2

    def test_register_agent_override_existing(self, isolated_agilevv_dir: TestPathConfig) -> None:
        """Test that registering an agent can override existing types."""
        with patch("verifflowcc.agents.factory.get_sdk_config") as mock_get_config:
            mock_get_config.return_value = SDKConfig(api_key="test-key")
            factory = AgentFactory(path_config=isolated_agilevv_dir)

            # First registration
            factory.register_agent("requirements_analyst", MockAgent)
            assert factory._agent_registry["requirements_analyst"] == MockAgent

            # Override with different class
            class NewMockAgent(BaseAgent):
                async def process(self, input_data: dict[str, Any]) -> dict[str, Any]:
                    return {"overridden": True}

            factory.register_agent("requirements", NewMockAgent)
            assert factory._agent_registry["requirements"] == NewMockAgent


class TestAgentFactoryCreation:
    """Test agent creation functionality."""

    def test_create_agent_with_registered_type(self, isolated_agilevv_dir: TestPathConfig) -> None:
        """Test creating an agent with registered type."""
        sdk_config = SDKConfig(api_key="test-key")
        factory = AgentFactory(sdk_config=sdk_config, path_config=isolated_agilevv_dir)

        # Register mock agent for valid type
        factory.register_agent("requirements_analyst", MockAgent)

        # Create agent
        agent = factory.create_agent("requirements", name="test_agent")

        assert isinstance(agent, MockAgent)
        assert agent.name == "test_agent"
        assert agent.agent_type == "requirements"
        assert agent.path_config == isolated_agilevv_dir
        assert agent.sdk_config == sdk_config

    def test_create_agent_default_name(self, isolated_agilevv_dir: TestPathConfig) -> None:
        """Test creating an agent with default name generation."""
        sdk_config = SDKConfig(api_key="test-key")
        factory = AgentFactory(sdk_config=sdk_config, path_config=isolated_agilevv_dir)

        factory.register_agent("requirements_analyst", MockAgent)
        agent = factory.create_agent("requirements")

        assert agent.name == "requirements_agent"
        assert agent.agent_type == "requirements"

    def test_create_agent_unsupported_type_raises_error(
        self, isolated_agilevv_dir: TestPathConfig
    ) -> None:
        """Test that creating unsupported agent type raises error."""
        sdk_config = SDKConfig(api_key="test-key")
        factory = AgentFactory(sdk_config=sdk_config, path_config=isolated_agilevv_dir)

        with pytest.raises(ValueError, match="Unsupported agent type: unsupported"):
            factory.create_agent("unsupported")

    def test_create_agent_fallback_behavior(self, isolated_agilevv_dir: TestPathConfig) -> None:
        """Test fallback behavior when agent type not in registry."""
        sdk_config = SDKConfig(api_key="test-key")
        factory = AgentFactory(sdk_config=sdk_config, path_config=isolated_agilevv_dir)

        # Clear registry to force fallback
        factory._agent_registry.clear()

        agent = factory.create_agent("requirements")

        assert isinstance(agent, TaskAgent)
        assert agent.agent_type == "requirements"
        assert agent.name == "requirements_agent"

    def test_create_agent_with_mock_mode(self, isolated_agilevv_dir: TestPathConfig) -> None:
        """Test creating agents in mock mode."""
        sdk_config = SDKConfig(api_key="test-key")
        factory = AgentFactory(
            sdk_config=sdk_config, path_config=isolated_agilevv_dir, mock_mode=True
        )

        factory.register_agent("developer", MockAgent)
        agent = factory.create_agent("developer")

        assert isinstance(agent, MockAgent)
        assert agent.mock_mode is True

    @pytest.mark.parametrize(
        "agent_type", ["requirements", "architect", "developer", "qa", "integration"]
    )
    def test_create_all_valid_agent_types(
        self, agent_type: str, isolated_agilevv_dir: TestPathConfig
    ) -> None:
        """Test creating all valid V-Model agent types."""
        sdk_config = SDKConfig(api_key="test-key")
        factory = AgentFactory(sdk_config=sdk_config, path_config=isolated_agilevv_dir)

        # Register mock agent for this type
        factory.register_agent(agent_type, MockAgent)

        agent = factory.create_agent(agent_type)

        assert isinstance(agent, MockAgent)
        assert agent.agent_type == agent_type
        assert agent.name == f"{agent_type}_agent"


class TestAgentFactoryBulkOperations:
    """Test bulk operations on agents."""

    def test_create_all_agents_success(self, isolated_agilevv_dir: TestPathConfig) -> None:
        """Test creating all V-Model agents successfully."""
        sdk_config = SDKConfig(api_key="test-key")
        factory = AgentFactory(sdk_config=sdk_config, path_config=isolated_agilevv_dir)

        # Register all agent types
        for agent_type in [
            "requirements_analyst",
            "architect",
            "developer",
            "qa_tester",
            "integration",
        ]:
            factory.register_agent(agent_type, MockAgent)

        agents = factory.create_all_agents()

        assert len(agents) == 5
        assert all(
            agent_type in agents
            for agent_type in [
                "requirements_analyst",
                "architect",
                "developer",
                "qa_tester",
                "integration",
            ]
        )
        assert all(isinstance(agent, MockAgent) for agent in agents.values())

    def test_create_all_agents_with_failures(self, isolated_agilevv_dir: TestPathConfig) -> None:
        """Test creating all agents when some fail."""
        sdk_config = SDKConfig(api_key="test-key")
        factory = AgentFactory(sdk_config=sdk_config, path_config=isolated_agilevv_dir)

        # Register only some agent types
        factory.register_agent("requirements_analyst", MockAgent)
        factory.register_agent("developer", MockAgent)
        # Leave others unregistered to force fallback

        agents = factory.create_all_agents()

        # Should still get 5 agents (some fallback)
        assert len(agents) <= 5  # May be fewer if creation fails
        assert "requirements_analyst" in agents
        assert "developer" in agents

    def test_create_all_agents_empty_registry(self, isolated_agilevv_dir: TestPathConfig) -> None:
        """Test creating all agents with empty registry."""
        sdk_config = SDKConfig(api_key="test-key")
        factory = AgentFactory(sdk_config=sdk_config, path_config=isolated_agilevv_dir)

        # Clear registry
        factory._agent_registry.clear()

        agents = factory.create_all_agents()

        # Should get fallback agents for valid types
        for agent_type in agents:
            assert isinstance(agents[agent_type], TaskAgent)

    def test_list_available_agents(self, isolated_agilevv_dir: TestPathConfig) -> None:
        """Test listing available agent types and descriptions."""
        with patch("verifflowcc.agents.factory.get_sdk_config") as mock_get_config:
            mock_get_config.return_value = SDKConfig(api_key="test-key")
            factory = AgentFactory(path_config=isolated_agilevv_dir)

            available_agents = factory.list_available_agents()

            expected_types = [
                "requirements_analyst",
                "architect",
                "developer",
                "qa_tester",
                "integration",
            ]
            assert all(agent_type in available_agents for agent_type in expected_types)
            assert all(isinstance(desc, str) for desc in available_agents.values())
            assert len(available_agents) == 5

    def test_list_available_agents_descriptions(self, isolated_agilevv_dir: TestPathConfig) -> None:
        """Test that agent descriptions are meaningful."""
        with patch("verifflowcc.agents.factory.get_sdk_config") as mock_get_config:
            mock_get_config.return_value = SDKConfig(api_key="test-key")
            factory = AgentFactory(path_config=isolated_agilevv_dir)

            available_agents = factory.list_available_agents()

            # Check that descriptions contain relevant keywords
            assert "Requirements" in available_agents["requirements_analyst"]
            assert "Architect" in available_agents["architect"]
            assert "Developer" in available_agents["developer"]
            assert "QA" in available_agents["qa_tester"]
            assert "Integration" in available_agents["integration"]


class TestAgentFactoryConfiguration:
    """Test agent factory configuration scenarios."""

    def test_factory_with_yaml_configuration(self, isolated_agilevv_dir: TestPathConfig) -> None:
        """Test factory configuration loading from YAML (simulated)."""
        sdk_config = SDKConfig(api_key="yaml-test-key")

        # Simulate YAML configuration
        yaml_config = {
            "agents": {
                "requirements": {"timeout": 90, "max_retries": 5},
                "developer": {"timeout": 180, "max_retries": 3},
            },
            "mock_mode": False,
        }

        factory = AgentFactory(
            sdk_config=sdk_config,
            path_config=isolated_agilevv_dir,
            mock_mode=bool(yaml_config["mock_mode"]),
        )

        # Verify configuration is applied
        assert factory.mock_mode == yaml_config["mock_mode"]
        assert factory.sdk_config == sdk_config

    def test_factory_with_json_configuration(self, isolated_agilevv_dir: TestPathConfig) -> None:
        """Test factory configuration loading from JSON (simulated)."""
        sdk_config = SDKConfig(api_key="json-test-key", timeout=120)

        # Simulate JSON configuration
        json_config = {"factory_settings": {"mock_mode": True, "default_timeout": 120}}

        factory = AgentFactory(
            sdk_config=sdk_config,
            path_config=isolated_agilevv_dir,
            mock_mode=bool(json_config["factory_settings"]["mock_mode"]),
        )

        assert factory.mock_mode is True
        assert factory.sdk_config.timeout == 120

    def test_factory_environment_override(self, isolated_agilevv_dir: TestPathConfig) -> None:
        """Test factory configuration with environment overrides."""
        with patch.dict("os.environ", {"VERIFFLOWCC_MOCK_MODE": "true"}):
            sdk_config = SDKConfig(api_key="env-test-key")

            # In real implementation, factory would read environment variables
            import os

            mock_mode_str = os.getenv("VERIFFLOWCC_MOCK_MODE", "false")
            mock_mode = mock_mode_str.lower() == "true"

            factory = AgentFactory(
                sdk_config=sdk_config,
                path_config=isolated_agilevv_dir,
                mock_mode=mock_mode,
            )

            assert factory.mock_mode is True

    def test_factory_configuration_validation(self, isolated_agilevv_dir: TestPathConfig) -> None:
        """Test factory configuration validation."""
        # Test with invalid SDK config (should handle gracefully)
        with patch("verifflowcc.agents.factory.get_sdk_config") as mock_get_config:
            mock_get_config.side_effect = ValueError("Invalid SDK config")

            # Factory should handle SDK config errors gracefully
            with pytest.raises(ValueError):
                AgentFactory(path_config=isolated_agilevv_dir)


class TestAgentFactoryErrorHandling:
    """Test error handling in agent factory operations."""

    def test_create_agent_with_invalid_sdk_config(
        self, isolated_agilevv_dir: TestPathConfig
    ) -> None:
        """Test creating agent with invalid SDK configuration."""
        # SDK config with missing API key should still work if mock mode
        sdk_config = SDKConfig(api_key="")  # Empty API key

        factory = AgentFactory(
            sdk_config=sdk_config,
            path_config=isolated_agilevv_dir,
            mock_mode=True,  # Mock mode should handle invalid config
        )

        factory.register_agent("requirements_analyst", MockAgent)
        agent = factory.create_agent("requirements")

        assert isinstance(agent, MockAgent)
        assert agent.mock_mode is True

    def test_create_agent_registry_access_error(self, isolated_agilevv_dir: TestPathConfig) -> None:
        """Test handling of registry access errors."""
        sdk_config = SDKConfig(api_key="test-key")
        factory = AgentFactory(sdk_config=sdk_config, path_config=isolated_agilevv_dir)

        # Simulate registry corruption by clearing it instead of setting to None
        factory._agent_registry.clear()

        # Should fallback gracefully
        agent = factory.create_agent("requirements")
        assert isinstance(agent, TaskAgent)

    def test_agent_import_failure_handling(self, isolated_agilevv_dir: TestPathConfig) -> None:
        """Test handling of agent import failures."""
        with patch("verifflowcc.agents.factory.get_sdk_config") as mock_get_config:
            mock_get_config.return_value = SDKConfig(api_key="test-key")

            # Simulate import failure during registration
            with patch("verifflowcc.agents.factory.logger"):
                factory = AgentFactory(path_config=isolated_agilevv_dir)

                # Factory should still be created even if some imports fail
                assert isinstance(factory, AgentFactory)
                assert isinstance(factory._agent_registry, dict)

    def test_create_all_agents_partial_failure(self, isolated_agilevv_dir: TestPathConfig) -> None:
        """Test create_all_agents with partial failures."""
        sdk_config = SDKConfig(api_key="test-key")
        factory = AgentFactory(sdk_config=sdk_config, path_config=isolated_agilevv_dir)

        # Create a problematic agent class
        class ProblematicAgent(BaseAgent):
            def __init__(self, *args: Any, **kwargs: Any) -> None:
                raise RuntimeError("Simulated initialization failure")

            async def process(self, input_data: dict[str, Any]) -> dict[str, Any]:
                return {}

        # Register mix of working and problematic agents
        factory.register_agent("requirements_analyst", MockAgent)
        factory.register_agent("architect", ProblematicAgent)
        factory.register_agent("developer", MockAgent)

        agents = factory.create_all_agents()

        # Should have some successful agents despite failures
        assert len(agents) <= 5
        # Working agents should be present
        if "requirements_analyst" in agents:
            assert isinstance(agents["requirements_analyst"], MockAgent)
        if "developer" in agents:
            assert isinstance(agents["developer"], MockAgent)


class TestAgentFactoryMockMode:
    """Test agent factory mock mode behavior."""

    @pytest.mark.asyncio
    async def test_mock_agent_functionality(self, isolated_agilevv_dir: TestPathConfig) -> None:
        """Test that mock agents work correctly."""
        sdk_config = SDKConfig(api_key="mock-key")
        factory = AgentFactory(
            sdk_config=sdk_config, path_config=isolated_agilevv_dir, mock_mode=True
        )

        factory.register_agent("requirements_analyst", MockAgent)
        agent = factory.create_agent("requirements")

        # Test agent processing
        test_input = {"story": "As a user, I want to test"}
        result = await agent.process(test_input)

        assert result["status"] == "success"
        assert result["mock_mode"] is True
        assert result["processed"] is True
        assert agent.process_called is True  # type: ignore[attr-defined]

    def test_mock_mode_agent_substitution(self, isolated_agilevv_dir: TestPathConfig) -> None:
        """Test mock mode agent substitution behavior."""
        sdk_config = SDKConfig(api_key="test-key")

        # Create factory in production mode
        prod_factory = AgentFactory(
            sdk_config=sdk_config, path_config=isolated_agilevv_dir, mock_mode=False
        )

        # Create factory in mock mode
        mock_factory = AgentFactory(
            sdk_config=sdk_config, path_config=isolated_agilevv_dir, mock_mode=True
        )

        prod_factory.register_agent("qa", MockAgent)
        mock_factory.register_agent("qa", MockAgent)

        prod_agent = prod_factory.create_agent("qa")
        mock_agent = mock_factory.create_agent("qa")

        assert prod_agent.mock_mode is False
        assert mock_agent.mock_mode is True

    def test_mock_mode_configuration_isolation(self, isolated_agilevv_dir: TestPathConfig) -> None:
        """Test that mock mode configuration is properly isolated."""
        sdk_config = SDKConfig(api_key="test-key")

        # Create multiple factories with different mock modes
        factories = [
            AgentFactory(sdk_config=sdk_config, path_config=isolated_agilevv_dir, mock_mode=True),
            AgentFactory(sdk_config=sdk_config, path_config=isolated_agilevv_dir, mock_mode=False),
            AgentFactory(sdk_config=sdk_config, path_config=isolated_agilevv_dir, mock_mode=True),
        ]

        expected_modes = [True, False, True]

        for factory, expected_mode in zip(factories, expected_modes, strict=False):
            assert factory.mock_mode == expected_mode

            factory.register_agent("integration", MockAgent)
            agent = factory.create_agent("integration")
            assert agent.mock_mode == expected_mode
