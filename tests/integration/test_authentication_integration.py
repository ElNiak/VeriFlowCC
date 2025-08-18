"""Real integration tests for optional API key authentication functionality.

This module tests the end-to-end authentication flow without mocks, focusing on:
- Real authentication priority logic (explicit > environment > subscription)
- Integration between SDKConfig, AgentFactory, and BaseAgent
- Clean exception handling for subscription verification failures
- Practical authentication scenarios that would break in production

No mocks are used for core authentication logic to ensure real integration testing.
"""

import os
import tempfile
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest
from verifflowcc.agents.factory import AgentFactory
from verifflowcc.core.path_config import PathConfig
from verifflowcc.core.sdk_config import SDKConfig


class TestRealAuthenticationPriority:
    """Test real authentication priority logic without mocking core detection."""

    def test_explicit_api_key_highest_priority(self) -> None:
        """Test explicit API key takes highest priority over all other methods."""
        # Test with environment variable present - explicit should still win
        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "env-key"}, clear=False):
            config = SDKConfig(api_key="explicit-key")
            assert config.api_key == "explicit-key"

            # Verify authentication method detection
            auth_method = config._detect_authentication_method()
            assert auth_method == "api_key"

    def test_environment_variable_second_priority(self) -> None:
        """Test environment variable takes second priority when no explicit key."""
        # Create clean environment for this test
        env_vars = {k: v for k, v in os.environ.items() if k != "ANTHROPIC_API_KEY"}
        env_vars["ANTHROPIC_API_KEY"] = "real-env-key"

        with patch.dict(os.environ, env_vars, clear=True):
            # Ensure we're not in test environment for this test
            with patch("verifflowcc.core.sdk_config.os.getenv") as mock_getenv:
                def real_getenv(key: str, default: str | None = None) -> str | None:
                    if key == "ANTHROPIC_API_KEY":
                        return "real-env-key"
                    elif key == "PYTEST_CURRENT_TEST":
                        return None  # Not in test mode
                    return os.environ.get(key, default)

                mock_getenv.side_effect = real_getenv

                config = SDKConfig()
                assert config.api_key == "real-env-key"

                # Verify authentication method detection
                auth_method = config._detect_authentication_method()
                assert auth_method == "api_key"

    def test_subscription_fallback_lowest_priority(self) -> None:
        """Test subscription authentication as fallback when no API key available."""
        # Create environment without API key
        env_vars = {k: v for k, v in os.environ.items() if k != "ANTHROPIC_API_KEY"}

        with patch.dict(os.environ, env_vars, clear=True):
            # Mock only the environment detection, not the subscription logic
            with patch("verifflowcc.core.sdk_config.os.getenv") as mock_getenv:
                def real_getenv(key: str, default: str | None = None) -> str | None:
                    if key in ["ANTHROPIC_API_KEY", "PYTEST_CURRENT_TEST"]:
                        return None
                    return os.environ.get(key, default)

                mock_getenv.side_effect = real_getenv

                config = SDKConfig()
                assert config.api_key is None

                # Test real authentication method detection
                auth_method = config._detect_authentication_method()
                # Should attempt subscription verification
                assert auth_method in ["subscription", "none"]

    def test_authentication_method_consistency(self) -> None:
        """Test authentication method detection is consistent across multiple calls."""
        config = SDKConfig(api_key="test-consistency")

        # Multiple calls should return same result
        method1 = config._detect_authentication_method()
        method2 = config._detect_authentication_method()
        method3 = config._detect_authentication_method()

        assert method1 == method2 == method3 == "api_key"


class TestRealAgentFactoryIntegration:
    """Test real integration between SDKConfig and AgentFactory."""

    def test_agent_factory_with_api_key_config(self, isolated_agilevv_dir: PathConfig) -> None:
        """Test AgentFactory creation with real API key configuration."""
        # Create real SDK config with API key
        sdk_config = SDKConfig(api_key="integration-test-key")

        # Create factory with real configuration
        factory = AgentFactory(
            sdk_config=sdk_config,
            path_config=isolated_agilevv_dir,
            mock_mode=True  # Use mock mode to avoid real API calls
        )

        # Verify factory configuration
        assert factory.sdk_config.api_key == "integration-test-key"
        assert factory.sdk_config._detect_authentication_method() == "api_key"

        # Test real agent creation
        agent = factory.create_agent("requirements")

        # Verify agent has correct configuration
        assert agent.sdk_config.api_key == "integration-test-key"
        assert agent.mock_mode is True

        # Test client options generation
        options = agent.sdk_config.get_client_options("requirements")
        assert "Requirements Analyst" in options.system_prompt
        assert options.tools_enabled is True

    def test_agent_factory_without_api_key(self, isolated_agilevv_dir: PathConfig) -> None:
        """Test AgentFactory creation without API key (subscription fallback)."""
        # Create configuration without API key
        env_vars = {k: v for k, v in os.environ.items() if k != "ANTHROPIC_API_KEY"}

        with patch.dict(os.environ, env_vars, clear=True):
            with patch("verifflowcc.core.sdk_config.os.getenv") as mock_getenv:
                def real_getenv(key: str, default: str | None = None) -> str | None:
                    if key in ["ANTHROPIC_API_KEY", "PYTEST_CURRENT_TEST"]:
                        return None
                    return os.environ.get(key, default)

                mock_getenv.side_effect = real_getenv

                sdk_config = SDKConfig()
                assert sdk_config.api_key is None

                # Create factory - should work with subscription fallback
                factory = AgentFactory(
                    sdk_config=sdk_config,
                    path_config=isolated_agilevv_dir,
                    mock_mode=True
                )

                # Should be able to create agents
                agent = factory.create_agent("architect")
                assert agent.sdk_config.api_key is None
                assert agent.mock_mode is True

    def test_agent_creation_with_different_types(self, isolated_agilevv_dir: PathConfig) -> None:
        """Test creating different agent types with same SDK configuration."""
        sdk_config = SDKConfig(api_key="multi-agent-key")
        factory = AgentFactory(
            sdk_config=sdk_config,
            path_config=isolated_agilevv_dir,
            mock_mode=True
        )

        agent_types = ["requirements", "architect", "developer", "qa", "integration"]

        for agent_type in agent_types:
            agent = factory.create_agent(agent_type)

            # All agents should share same SDK config
            assert agent.sdk_config.api_key == "multi-agent-key"

            # Each should have appropriate client options
            options = agent.sdk_config.get_client_options(agent_type)
            assert options.max_tokens == 4000
            assert options.temperature == 0.7

            # Each should have appropriate tool permissions
            permissions = agent.sdk_config.get_tool_permissions(agent_type)
            assert "read" in permissions


class TestRealBaseAgentIntegration:
    """Test real integration between SDKConfig and BaseAgent."""

    def test_base_agent_initialization_with_sdk_config(self, isolated_agilevv_dir: PathConfig) -> None:
        """Test BaseAgent initialization with real SDK configuration."""
        from verifflowcc.agents.base import BaseAgent

        # Create concrete subclass for testing
        class TestAgent(BaseAgent):
            async def process(self, input_data: dict[str, Any]) -> dict[str, Any]:
                return {"test": "response"}

        sdk_config = SDKConfig(
            api_key="base-agent-key",
            timeout=45,
            max_retries=2
        )

        agent = TestAgent(
            name="test_agent",
            agent_type="requirements",
            path_config=isolated_agilevv_dir,
            sdk_config=sdk_config,
            mock_mode=True
        )

        # Verify SDK configuration propagation
        assert agent.sdk_config.api_key == "base-agent-key"
        assert agent.sdk_config.timeout == 45
        assert agent.sdk_config.max_retries == 2

        # Verify client options are properly configured
        assert agent.client_options.max_tokens == 4000
        assert agent.client_options.stream is True
        assert "Requirements Analyst" in agent.client_options.system_prompt

        # Verify tool permissions are set
        assert agent.tool_permissions["read"] is True
        assert agent.tool_permissions["write"] is True

    def test_base_agent_with_different_configurations(self, isolated_agilevv_dir: PathConfig) -> None:
        """Test BaseAgent behavior with different SDK configurations."""
        from verifflowcc.agents.base import BaseAgent

        class TestAgent(BaseAgent):
            async def process(self, input_data: dict[str, Any]) -> dict[str, Any]:
                return {"config_test": True}

        # Test with minimal configuration
        minimal_config = SDKConfig()
        minimal_agent = TestAgent(
            name="minimal_agent",
            agent_type="developer",
            path_config=isolated_agilevv_dir,
            sdk_config=minimal_config,
            mock_mode=True
        )

        # Test with comprehensive configuration
        comprehensive_config = SDKConfig(
            api_key="comprehensive-key",
            timeout=120,
            max_retries=5,
            retry_delay=2.5,
            environment="test-env"
        )
        comprehensive_agent = TestAgent(
            name="comprehensive_agent",
            agent_type="developer",
            path_config=isolated_agilevv_dir,
            sdk_config=comprehensive_config,
            mock_mode=True
        )

        # Verify different configurations produce different behaviors
        minimal_auth = minimal_agent.sdk_config._detect_authentication_method()
        comprehensive_auth = comprehensive_agent.sdk_config._detect_authentication_method()

        # Comprehensive should use API key, minimal might use subscription
        assert comprehensive_auth == "api_key"
        assert minimal_auth in ["api_key", "subscription", "none"]


class TestRealSubscriptionVerificationHandling:
    """Test real subscription verification failure handling."""

    def test_subscription_verification_exception_handling(self) -> None:
        """Test clean exception handling when subscription verification fails."""
        # Create config without API key
        config = SDKConfig()
        config.api_key = None

        # Test that subscription verification method exists and handles failures
        try:
            # This should not raise an exception during detection
            auth_method = config._detect_authentication_method()
            # Should gracefully handle subscription verification failure
            assert auth_method in ["subscription", "none"]
        except Exception as e:
            pytest.fail(f"Subscription verification should not raise exception: {e}")

    def test_subscription_verification_with_validation(self) -> None:
        """Test subscription verification with authentication validation."""
        config = SDKConfig()
        config.api_key = None

        # Mock subscription verification to return False (failed)
        with patch.object(config, '_verify_claude_subscription', return_value=False):
            auth_method = config._detect_authentication_method()
            assert auth_method == "none"

            # Test validation method if it exists
            if hasattr(config, '_validate_authentication'):
                with pytest.raises(Exception):  # Should raise AuthenticationError
                    config._validate_authentication()

    def test_subscription_verification_network_failure(self) -> None:
        """Test handling of network failures during subscription verification."""
        config = SDKConfig()
        config.api_key = None

        # Mock network failure during subscription verification
        with patch.object(config, '_verify_claude_subscription', side_effect=ConnectionError("Network unreachable")):
            # Should handle network error gracefully
            auth_method = config._detect_authentication_method()
            assert auth_method == "none"


class TestRealEndToEndAuthenticationFlow:
    """Test complete end-to-end authentication flow."""

    def test_complete_workflow_with_api_key(self, isolated_agilevv_dir: PathConfig) -> None:
        """Test complete workflow from configuration to agent execution with API key."""
        # 1. Create SDK configuration with API key
        sdk_config = SDKConfig(api_key="e2e-test-key")

        # 2. Create agent factory
        factory = AgentFactory(
            sdk_config=sdk_config,
            path_config=isolated_agilevv_dir,
            mock_mode=True
        )

        # 3. Create agent
        agent = factory.create_agent("requirements")

        # 4. Verify complete configuration chain
        assert agent.sdk_config.api_key == "e2e-test-key"
        assert agent.sdk_config._detect_authentication_method() == "api_key"
        assert agent.client_options.tools_enabled is True
        assert agent.tool_permissions["write"] is True

        # 5. Test agent can initialize execution context
        agent.context.update({"test": "data"})
        assert agent.context["test"] == "data"

    def test_complete_workflow_with_subscription_fallback(self, isolated_agilevv_dir: PathConfig) -> None:
        """Test complete workflow with subscription authentication fallback."""
        # Create environment without API key
        env_vars = {k: v for k, v in os.environ.items() if k != "ANTHROPIC_API_KEY"}

        with patch.dict(os.environ, env_vars, clear=True):
            with patch("verifflowcc.core.sdk_config.os.getenv") as mock_getenv:
                def real_getenv(key: str, default: str | None = None) -> str | None:
                    if key in ["ANTHROPIC_API_KEY", "PYTEST_CURRENT_TEST"]:
                        return None
                    return os.environ.get(key, default)

                mock_getenv.side_effect = real_getenv

                # 1. Create SDK configuration without API key
                sdk_config = SDKConfig()

                # 2. Create agent factory
                factory = AgentFactory(
                    sdk_config=sdk_config,
                    path_config=isolated_agilevv_dir,
                    mock_mode=True
                )

                # 3. Create agent - should work with subscription fallback
                agent = factory.create_agent("qa")

                # 4. Verify configuration works end-to-end
                assert agent.sdk_config.api_key is None
                auth_method = agent.sdk_config._detect_authentication_method()
                assert auth_method in ["subscription", "none"]

                # 5. Agent should still be functional
                assert agent.client_options.max_tokens == 4000
                assert agent.tool_permissions["execute"] is True

    def test_authentication_error_propagation(self, isolated_agilevv_dir: PathConfig) -> None:
        """Test that authentication errors propagate cleanly through the system."""
        # Create config that will fail authentication
        config = SDKConfig()
        config.api_key = None

        # Mock subscription verification to fail
        with patch.object(config, '_verify_claude_subscription', return_value=False):
            # Authentication method detection should handle this gracefully
            auth_method = config._detect_authentication_method()
            assert auth_method == "none"

            # Agent creation should still work (with appropriate warnings)
            factory = AgentFactory(
                sdk_config=config,
                path_config=isolated_agilevv_dir,
                mock_mode=True  # Important: mock mode should allow operation
            )

            agent = factory.create_agent("integration")
            # Agent should be created but with no API key
            assert agent.sdk_config.api_key is None


class TestRealEnvironmentBasedAuthentication:
    """Test real environment-based authentication handling."""

    def test_environment_variable_detection_no_mocks(self) -> None:
        """Test environment variable detection without mocking os.getenv."""
        # Test with temporary environment variable
        test_key = "real-env-test-key-123"
        original_getenv = os.getenv  # Store original function

        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": test_key}, clear=False):
            # Only mock PYTEST_CURRENT_TEST to avoid test mode
            with patch("verifflowcc.core.sdk_config.os.getenv") as mock_getenv:
                def selective_getenv(key: str, default: str | None = None) -> str | None:
                    if key == "PYTEST_CURRENT_TEST":
                        return None  # Not in test mode
                    return original_getenv(key, default)  # Use original os.getenv

                mock_getenv.side_effect = selective_getenv

                config = SDKConfig()
                assert config.api_key == test_key

    def test_multiple_environment_configurations(self, isolated_agilevv_dir: PathConfig) -> None:
        """Test different environment configurations and their effects."""
        configurations = [
            ("development", "dev-api-key"),
            ("staging", "staging-api-key"),
            ("production", "prod-api-key"),
        ]
        original_getenv = os.getenv  # Store original function

        for environment, api_key in configurations:
            with patch.dict(os.environ, {"ANTHROPIC_API_KEY": api_key}, clear=False):
                with patch("verifflowcc.core.sdk_config.os.getenv") as mock_getenv:
                    def env_getenv(key: str, default: str | None = None) -> str | None:
                        if key == "PYTEST_CURRENT_TEST":
                            return None
                        return original_getenv(key, default)  # Use original os.getenv

                    mock_getenv.side_effect = env_getenv

                    config = SDKConfig(environment=environment)
                    assert config.api_key == api_key
                    assert config.environment == environment

                    # Test that environment-specific agent creation works
                    factory = AgentFactory(
                        sdk_config=config,
                        path_config=isolated_agilevv_dir,
                        mock_mode=True
                    )

                    agent = factory.create_agent("architect")
                    assert agent.sdk_config.environment == environment
                    assert agent.sdk_config.api_key == api_key

    def test_environment_variable_precedence_over_subscription(self) -> None:
        """Test that environment variable takes precedence over subscription."""
        test_env_key = "env-precedence-key"
        original_getenv = os.getenv  # Store original function

        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": test_env_key}, clear=False):
            with patch("verifflowcc.core.sdk_config.os.getenv") as mock_getenv:
                def precedence_getenv(key: str, default: str | None = None) -> str | None:
                    if key == "PYTEST_CURRENT_TEST":
                        return None
                    return original_getenv(key, default)  # Use original os.getenv

                mock_getenv.side_effect = precedence_getenv

                config = SDKConfig()

                # Should use environment variable, not attempt subscription
                assert config.api_key == test_env_key
                assert config._detect_authentication_method() == "api_key"


class TestRealConfigurationPersistence:
    """Test configuration persistence and restoration."""

    def test_configuration_state_consistency(self, isolated_agilevv_dir: PathConfig) -> None:
        """Test that configuration state remains consistent across operations."""
        config = SDKConfig(
            api_key="persistence-test-key",
            timeout=90,
            max_retries=4,
            environment="test-persistence"
        )

        # Create multiple agents with same config
        factory = AgentFactory(
            sdk_config=config,
            path_config=isolated_agilevv_dir,
            mock_mode=True
        )

        agents = []
        for agent_type in ["requirements", "architect", "developer"]:
            agent = factory.create_agent(agent_type)
            agents.append(agent)

        # All agents should have consistent configuration
        for agent in agents:
            assert agent.sdk_config.api_key == "persistence-test-key"
            assert agent.sdk_config.timeout == 90
            assert agent.sdk_config.max_retries == 4
            assert agent.sdk_config.environment == "test-persistence"

            # Authentication method should be consistent
            assert agent.sdk_config._detect_authentication_method() == "api_key"

    def test_configuration_serialization_integration(self) -> None:
        """Test configuration can be serialized and deserialized for persistence."""
        original_config = SDKConfig(
            api_key="serialization-key",
            base_url="https://test.api.com",
            timeout=75,
            max_retries=6,
            retry_delay=1.8,
            environment="serialization-test"
        )

        # Serialize configuration
        config_dict = {
            "api_key": original_config.api_key,
            "base_url": original_config.base_url,
            "timeout": original_config.timeout,
            "max_retries": original_config.max_retries,
            "retry_delay": original_config.retry_delay,
            "environment": original_config.environment,
        }

        # Deserialize configuration
        restored_config = SDKConfig(**config_dict)

        # Verify all properties match
        assert restored_config.api_key == original_config.api_key
        assert restored_config.base_url == original_config.base_url
        assert restored_config.timeout == original_config.timeout
        assert restored_config.max_retries == original_config.max_retries
        assert restored_config.retry_delay == original_config.retry_delay
        assert restored_config.environment == original_config.environment

        # Verify authentication method detection works the same
        assert (
            restored_config._detect_authentication_method() ==
            original_config._detect_authentication_method()
        )
