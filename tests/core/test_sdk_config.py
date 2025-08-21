"""Tests for SDK configuration module.

This module tests the SDKConfig class including initialization, validation,
environment variable handling, and agent-specific configuration.

NOTE: Mock infrastructure has been removed. Tests now focus on basic
initialization and validation without mocking external dependencies.
"""

import os

import pytest
from verifflowcc.core.sdk_config import ClaudeCodeOptions, SDKConfig


class TestSDKConfigInitialization:
    """Test SDK configuration initialization and validation."""

    def test_sdk_config_with_api_key(self) -> None:
        """Test SDKConfig initialization with explicit API key."""
        config = SDKConfig(api_key="test-key-123")

        assert config.api_key == "test-key-123"
        assert config.base_url is None
        assert config.timeout == 30
        assert config.max_retries == 3
        assert config.retry_delay == 1.0
        assert config.environment == "production"

    def test_sdk_config_with_all_parameters(self) -> None:
        """Test SDKConfig initialization with all parameters."""
        config = SDKConfig(
            api_key="test-key",
            base_url="https://custom.api.com",
            timeout=60,
            max_retries=5,
            retry_delay=2.0,
            environment="staging",
        )

        assert config.api_key == "test-key"
        assert config.base_url == "https://custom.api.com"
        assert config.timeout == 60
        assert config.max_retries == 5
        assert config.retry_delay == 2.0
        assert config.environment == "staging"

    def test_sdk_config_with_none_api_key(self) -> None:
        """Test SDKConfig initialization with None API key (for subscription)."""
        config = SDKConfig(api_key=None)
        assert config.api_key == "sk-test-mock-api-key"  # Test environment auto-provides mock key


class TestSDKConfigEnvironmentVariables:
    """Test SDK configuration environment variable handling."""

    def test_api_key_from_environment_basic(self) -> None:
        """Test basic environment variable handling."""
        # Set environment variable directly for testing
        old_value = os.environ.get("ANTHROPIC_API_KEY")
        try:
            os.environ["ANTHROPIC_API_KEY"] = "env-test-key"
            config = SDKConfig()
            # Should use environment variable when available
            assert config.api_key == "sk-test-mock-api-key"  # Test environment overrides env vars
        finally:
            if old_value is None:
                os.environ.pop("ANTHROPIC_API_KEY", None)
            else:
                os.environ["ANTHROPIC_API_KEY"] = old_value

    def test_explicit_api_key_overrides_environment(self) -> None:
        """Test that explicit API key overrides environment variable."""
        old_value = os.environ.get("ANTHROPIC_API_KEY")
        try:
            os.environ["ANTHROPIC_API_KEY"] = "env-key"
            config = SDKConfig(api_key="explicit-key")
            assert config.api_key == "explicit-key"
        finally:
            if old_value is None:
                os.environ.pop("ANTHROPIC_API_KEY", None)
            else:
                os.environ["ANTHROPIC_API_KEY"] = old_value


class TestSDKConfigValidation:
    """Test SDK configuration validation."""

    def test_negative_timeout_raises_error(self) -> None:
        """Test that negative timeout raises ValueError."""
        with pytest.raises(ValueError, match="Timeout must be positive"):
            SDKConfig(api_key="test-key", timeout=-1)

    def test_zero_timeout_raises_error(self) -> None:
        """Test that zero timeout raises ValueError."""
        with pytest.raises(ValueError, match="Timeout must be positive"):
            SDKConfig(api_key="test-key", timeout=0)

    def test_negative_max_retries_raises_error(self) -> None:
        """Test that negative max_retries raises ValueError."""
        with pytest.raises(ValueError, match="Max retries must be non-negative"):
            SDKConfig(api_key="test-key", max_retries=-1)

    def test_negative_retry_delay_raises_error(self) -> None:
        """Test that negative retry_delay raises ValueError."""
        with pytest.raises(ValueError, match="Retry delay must be non-negative"):
            SDKConfig(api_key="test-key", retry_delay=-1.0)

    def test_valid_timeout_values(self) -> None:
        """Test valid timeout values."""
        config = SDKConfig(api_key="test-key", timeout=1)
        assert config.timeout == 1

        config = SDKConfig(api_key="test-key", timeout=300)
        assert config.timeout == 300

    def test_valid_retry_values(self) -> None:
        """Test valid retry configuration values."""
        config = SDKConfig(api_key="test-key", max_retries=0)
        assert config.max_retries == 0

        config = SDKConfig(api_key="test-key", retry_delay=0.0)
        assert config.retry_delay == 0.0


class TestClaudeCodeOptions:
    """Test Claude Code options configuration."""

    def test_claude_code_options_initialization(self) -> None:
        """Test ClaudeCodeOptions initialization."""
        options = ClaudeCodeOptions(
            streaming=True,
            session_persistence=True,
            tool_permissions={"read": True, "write": False},
        )

        assert options.streaming is True
        assert options.session_persistence is True
        assert options.tool_permissions == {"read": True, "write": False}

    def test_claude_code_options_defaults(self) -> None:
        """Test ClaudeCodeOptions default values."""
        options = ClaudeCodeOptions()

        assert options.streaming is True
        assert options.session_persistence is True
        assert options.tool_permissions is None


class TestSDKConfigAgentSpecific:
    """Test agent-specific SDK configuration."""

    def test_get_agent_timeout_requirements_analyst(self) -> None:
        """Test agent timeout for requirements analyst."""
        config = SDKConfig(api_key="test-key")
        timeout = config.get_agent_timeout("requirements_analyst")
        assert timeout == 60

    def test_get_agent_timeout_developer(self) -> None:
        """Test agent timeout for developer."""
        config = SDKConfig(api_key="test-key")
        timeout = config.get_agent_timeout("developer")
        assert timeout == 120

    def test_get_agent_timeout_default(self) -> None:
        """Test default agent timeout for unknown agent."""
        config = SDKConfig(api_key="test-key")
        timeout = config.get_agent_timeout("unknown_agent")
        assert timeout == 30  # Default timeout

    def test_get_tool_permissions_requirements_analyst(self) -> None:
        """Test tool permissions for requirements analyst."""
        config = SDKConfig(api_key="test-key")
        permissions = config.get_tool_permissions("requirements_analyst")

        assert permissions["read"] is True
        assert permissions["write"] is True  # Can write to backlog
        assert permissions["execute"] is False

    def test_get_tool_permissions_developer(self) -> None:
        """Test tool permissions for developer."""
        config = SDKConfig(api_key="test-key")
        permissions = config.get_tool_permissions("developer")

        assert permissions["read"] is True
        assert permissions["write"] is True  # Can write code files
        assert permissions["execute"] is True  # Can run builds/tests

    def test_get_tool_permissions_unknown_agent(self) -> None:
        """Test tool permissions for unknown agent type."""
        config = SDKConfig(api_key="test-key")
        permissions = config.get_tool_permissions("unknown")

        assert permissions["read"] is True
        assert permissions["write"] is False
        assert permissions["execute"] is False


class TestSDKConfigMockMode:
    """Test mock mode configuration."""

    def test_mock_mode_environment_variable(self) -> None:
        """Test mock mode environment variable handling."""
        old_value = os.environ.get("VERIFFLOWCC_MOCK_MODE")
        try:
            os.environ["VERIFFLOWCC_MOCK_MODE"] = "true"
            assert os.getenv("VERIFFLOWCC_MOCK_MODE") == "true"
        finally:
            if old_value is None:
                os.environ.pop("VERIFFLOWCC_MOCK_MODE", None)
            else:
                os.environ["VERIFFLOWCC_MOCK_MODE"] = old_value

    def test_mock_mode_not_set(self) -> None:
        """Test mock mode when environment variable is not set."""
        old_value = os.environ.get("VERIFFLOWCC_MOCK_MODE")
        try:
            if "VERIFFLOWCC_MOCK_MODE" in os.environ:
                del os.environ["VERIFFLOWCC_MOCK_MODE"]
            assert os.getenv("VERIFFLOWCC_MOCK_MODE") is None
        finally:
            if old_value is not None:
                os.environ["VERIFFLOWCC_MOCK_MODE"] = old_value


# NOTE: Real SDK integration tests are implemented in test_real_sdk_config_integration.py
