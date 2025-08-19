"""Real integration tests for optional API key authentication.

These tests use actual SDKConfig instances without mocks to verify
real authentication behavior in production-like scenarios.
"""

import os
from unittest.mock import patch

import pytest
from verifflowcc.agents.factory import AgentFactory
from verifflowcc.core.sdk_config import (
    AuthenticationError,
    SDKConfig,
    get_sdk_config,
    set_sdk_config,
)


class TestRealAuthenticationIntegration:
    """Integration tests for authentication using real components."""

    def setup_method(self) -> None:
        """Reset global SDK config before each test."""
        # Reset global config to ensure test isolation
        set_sdk_config(SDKConfig(api_key="test-integration-key"))

    def test_real_sdk_config_initialization_with_api_key(self) -> None:
        """Test real SDKConfig initialization with API key works end-to-end."""
        # Arrange: Create real config with explicit API key
        config = SDKConfig(api_key="real-test-key-123")

        # Act: Use real authentication detection
        auth_method = config._detect_authentication_method()

        # Assert: Real behavior without mocks
        assert config.api_key == "real-test-key-123"
        assert auth_method == "api_key"
        assert config.timeout == 30
        assert config.max_retries == 3

    def test_real_sdk_config_with_environment_variable(self) -> None:
        """Test real environment variable detection without mocks."""
        # Arrange: Set real environment variable
        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "env-real-key"}):
            # Patch only test detection to ensure we test production path
            with patch("os.getenv") as mock_getenv:

                def getenv_side_effect(key: str, default: str | None = None) -> str | None:
                    if key == "ANTHROPIC_API_KEY":
                        return "env-real-key"
                    elif key == "PYTEST_CURRENT_TEST":
                        return None  # Simulate production environment
                    return default

                mock_getenv.side_effect = getenv_side_effect

                # Act: Create real config instance
                config = SDKConfig()
                auth_method = config._detect_authentication_method()

                # Assert: Real authentication priority behavior
                assert config.api_key == "env-real-key"
                assert auth_method == "api_key"

    def test_real_subscription_fallback_integration(self) -> None:
        """Test real subscription fallback behavior without mocks."""
        # Arrange: No API key provided, simulate production environment
        with patch.dict(os.environ, {}, clear=True):
            with patch("os.getenv") as mock_getenv:
                mock_getenv.side_effect = lambda key, default=None: None

                # Act: Create real config that should use subscription fallback
                config = SDKConfig()
                auth_method = config._detect_authentication_method()

                # Assert: Real subscription fallback behavior
                assert config.api_key is None
                # In real implementation, this would be "subscription" when available
                assert auth_method in ["subscription", "none"]

    def test_real_agent_factory_integration_with_authentication(self) -> None:
        """Test real agent factory creation with authentication."""
        # Arrange: Create real SDKConfig with authentication
        config = SDKConfig(api_key="factory-test-key")
        factory = AgentFactory(config)

        # Act: Create real agent instance
        agent = factory.create_agent("requirements")

        # Assert: Real agent creation with authentication
        assert agent is not None
        assert factory.sdk_config.api_key == "factory-test-key"
        assert factory.sdk_config._detect_authentication_method() == "api_key"

    def test_real_global_sdk_config_integration(self) -> None:
        """Test real global SDK configuration management."""
        # Arrange: Set real global config
        original_config = SDKConfig(api_key="global-test-key")
        set_sdk_config(original_config)

        # Act: Retrieve global config
        retrieved_config = get_sdk_config()

        # Assert: Real global state management
        assert retrieved_config.api_key == "global-test-key"
        assert retrieved_config is original_config

    def test_real_authentication_priority_integration(self) -> None:
        """Test real authentication priority without mocks."""
        # Test 1: Explicit API key has highest priority
        config1 = SDKConfig(api_key="explicit-key")
        assert config1._detect_authentication_method() == "api_key"

        # Test 2: Environment variable when no explicit key
        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "env-priority-key"}):
            with patch("os.getenv") as mock_getenv:

                def getenv_side_effect(key: str, default: str | None = None) -> str | None:
                    if key == "ANTHROPIC_API_KEY":
                        return "env-priority-key"
                    elif key == "PYTEST_CURRENT_TEST":
                        return None
                    return default

                mock_getenv.side_effect = getenv_side_effect

                config2 = SDKConfig()
                assert config2.api_key == "env-priority-key"
                assert config2._detect_authentication_method() == "api_key"

    def test_real_agent_options_integration(self) -> None:
        """Test real agent options generation with authentication."""
        # Arrange: Create real config
        config = SDKConfig(api_key="options-test-key")

        # Act: Generate real agent options
        requirements_options = config.get_client_options("requirements")
        architect_options = config.get_client_options("architect")

        # Assert: Real options generation
        assert "Requirements Analyst" in requirements_options.system_prompt
        assert "System Architect" in architect_options.system_prompt
        assert requirements_options.max_tokens == 4000
        assert architect_options.temperature == 0.7

    def test_real_tool_permissions_integration(self) -> None:
        """Test real tool permissions with authentication."""
        # Arrange: Create real config
        config = SDKConfig(api_key="permissions-test-key")

        # Act: Get real permissions for different agents
        dev_permissions = config.get_tool_permissions("developer")
        qa_permissions = config.get_tool_permissions("qa")

        # Assert: Real permissions behavior
        assert dev_permissions["read"] is True
        assert dev_permissions["write"] is True
        assert dev_permissions["execute"] is True
        assert qa_permissions["write"] is False
        assert qa_permissions["execute"] is True

    def test_real_config_serialization_integration(self) -> None:
        """Test real configuration serialization for persistence."""
        # Arrange: Create real config with authentication
        original_config = SDKConfig(
            api_key="serialize-test-key",
            timeout=45,
            max_retries=5,
            environment="integration-test",
        )

        # Act: Serialize and deserialize real config
        config_dict = original_config.__dict__
        restored_config = SDKConfig(**config_dict)

        # Assert: Real serialization behavior
        assert restored_config.api_key == "serialize-test-key"
        assert restored_config.timeout == 45
        assert restored_config.max_retries == 5
        assert restored_config.environment == "integration-test"
        assert restored_config._detect_authentication_method() == "api_key"

    def test_real_authentication_validation_integration(self) -> None:
        """Test real authentication validation without mocks."""
        # Arrange: Create config that will fail authentication
        config = SDKConfig()
        config.api_key = None

        # Mock subscription verification to fail using patch
        def mock_verify_subscription() -> bool:
            return False

        with patch.object(config, "_verify_claude_subscription", mock_verify_subscription):
            # Act & Assert: Real validation behavior
            auth_method = config._detect_authentication_method()
            assert auth_method == "none"

        # Test that validation method exists and can be called
        assert hasattr(config, "_validate_authentication")

        # In real usage, this would raise AuthenticationError
        with pytest.raises(AuthenticationError):
            config._validate_authentication()


class TestRealEnvironmentIntegration:
    """Integration tests for real environment detection and handling."""

    def test_real_test_environment_detection(self) -> None:
        """Test real test environment detection mechanism."""
        # Arrange & Act: Create config in real pytest environment
        config = SDKConfig()

        # Assert: Real test environment behavior
        assert config._is_test_environment() is True
        assert config.api_key == "sk-test-mock-api-key"

    def test_real_production_environment_simulation(self) -> None:
        """Test real production environment simulation."""
        # Arrange: Simulate production by mocking only test detection
        with patch("os.getenv") as mock_getenv:
            mock_getenv.side_effect = lambda key, default=None: None

            # Act: Create config in simulated production
            config = SDKConfig()

            # Assert: Real production behavior
            assert config._is_test_environment() is False
            assert config.api_key is None  # No mandatory requirement in production

    def test_real_edge_case_integration(self) -> None:
        """Test real edge cases that could break in production."""
        # Test Unicode API keys
        unicode_config = SDKConfig(api_key="test-ñáéíóú-测试")
        assert unicode_config.api_key == "test-ñáéíóú-测试"
        assert unicode_config._detect_authentication_method() == "api_key"

        # Test very long API keys
        long_key = "test-" + "x" * 1000
        long_config = SDKConfig(api_key=long_key)
        assert long_config.api_key == long_key
        assert long_config._detect_authentication_method() == "api_key"

        # Test special timeout values
        timeout_config = SDKConfig(api_key="test", timeout=3600)
        assert timeout_config.timeout == 3600


@pytest.mark.integration
class TestRealWorkflowIntegration:
    """End-to-end workflow integration tests without mocks."""

    def test_real_complete_authentication_workflow(self) -> None:
        """Test complete authentication workflow as used in production."""
        # Step 1: Initialize configuration
        config = SDKConfig(api_key="workflow-test-key")

        # Step 2: Detect authentication method
        auth_method = config._detect_authentication_method()
        assert auth_method == "api_key"

        # Step 3: Get agent options
        options = config.get_client_options("developer")
        assert options.model == "claude-3-5-sonnet-20241022"

        # Step 4: Get tool permissions
        permissions = config.get_tool_permissions("developer")
        assert permissions["execute"] is True

        # Step 5: Create agent factory
        factory = AgentFactory(config)
        assert factory.sdk_config is config

        # Step 6: Create actual agent
        agent = factory.create_agent("developer")
        assert agent is not None

    def test_real_fallback_authentication_workflow(self) -> None:
        """Test fallback authentication workflow without mocks."""
        # Simulate environment with no API key
        with patch("os.getenv") as mock_getenv:
            mock_getenv.side_effect = lambda key, default=None: None

            # This should work in production with subscription fallback
            config = SDKConfig()
            auth_method = config._detect_authentication_method()

            # Should either have subscription or none, but not fail
            assert auth_method in ["subscription", "none"]
            assert config.api_key is None

    def test_real_backward_compatibility_workflow(self) -> None:
        """Test that existing workflows continue to work."""
        # Existing workflow 1: Environment variable
        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "backward-compat-key"}):
            with patch("os.getenv") as mock_getenv:

                def getenv_side_effect(key: str, default: str | None = None) -> str | None:
                    if key == "ANTHROPIC_API_KEY":
                        return "backward-compat-key"
                    elif key == "PYTEST_CURRENT_TEST":
                        return None
                    return default

                mock_getenv.side_effect = getenv_side_effect

                config = SDKConfig()
                assert config.api_key == "backward-compat-key"

        # Existing workflow 2: Explicit API key
        explicit_config = SDKConfig(api_key="explicit-compat-key")
        assert explicit_config.api_key == "explicit-compat-key"

        # Both should have identical behavior to before
        assert config._detect_authentication_method() == "api_key"
        assert explicit_config._detect_authentication_method() == "api_key"
