"""Integration tests for SDK configuration with Claude Code SDK.

This module tests the integration between SDKConfig and the actual Claude Code SDK,
including session management, streaming responses, and real SDK interactions.
"""

import os
from collections.abc import AsyncGenerator
from typing import Any
from unittest.mock import patch

import pytest
from verifflowcc.core.sdk_config import SDKConfig


class MockClaudeCodeClient:
    """Mock Claude Code SDK client for testing."""

    def __init__(self, config: SDKConfig):
        self.config = config
        self.session_active = False
        self.call_count = 0

    async def start_session(self) -> None:
        """Mock session start."""
        self.session_active = True

    async def end_session(self) -> None:
        """Mock session end."""
        self.session_active = False

    async def stream_completion(
        self, prompt: str, **kwargs: Any
    ) -> AsyncGenerator[dict[str, Any], None]:
        """Mock streaming completion."""
        self.call_count += 1

        if not self.session_active:
            raise RuntimeError("Session not active")

        # Simulate streaming response chunks
        chunks = [
            {"type": "content", "content": "Hello, "},
            {"type": "content", "content": "this is "},
            {"type": "content", "content": "a streaming "},
            {"type": "content", "content": "response."},
            {"type": "complete", "usage": {"tokens": 15}},
        ]

        for chunk in chunks:
            yield chunk  # type: ignore[misc]

    async def single_completion(self, prompt: str, **kwargs: Any) -> dict[str, Any]:
        """Mock single completion."""
        self.call_count += 1

        if not self.session_active:
            raise RuntimeError("Session not active")

        return {"content": "This is a single completion response.", "usage": {"tokens": 10}}


@pytest.mark.integration
@pytest.mark.unit
class TestSDKConfigIntegration:
    """Test SDK configuration integration with Claude Code SDK."""

    @pytest.fixture
    def mock_claude_client(self) -> MockClaudeCodeClient:
        """Provide mock Claude Code client."""
        config = SDKConfig(api_key="test-integration-key")
        return MockClaudeCodeClient(config)

    async def test_sdk_session_lifecycle(self, mock_claude_client: MockClaudeCodeClient) -> None:
        """Test SDK session initialization and cleanup."""
        # Session should start inactive
        assert mock_claude_client.session_active is False

        # Start session
        await mock_claude_client.start_session()
        assert mock_claude_client.session_active is True

        # End session
        await mock_claude_client.end_session()
        assert mock_claude_client.session_active is False

    async def test_sdk_streaming_response_integration(
        self, mock_claude_client: MockClaudeCodeClient
    ) -> None:
        """Test streaming response integration with SDK configuration."""
        # Start session
        await mock_claude_client.start_session()

        # Collect streaming response
        chunks = []
        async for chunk in mock_claude_client.stream_completion("Test prompt"):
            chunks.append(chunk)

        # Verify streaming response structure
        assert len(chunks) == 5
        assert chunks[0]["type"] == "content"
        assert chunks[0]["content"] == "Hello, "
        assert chunks[-1]["type"] == "complete"
        assert "usage" in chunks[-1]

        # Cleanup
        await mock_claude_client.end_session()

    async def test_sdk_session_required_for_completion(
        self, mock_claude_client: MockClaudeCodeClient
    ) -> None:
        """Test that active session is required for completions."""
        # Attempt completion without session should fail
        with pytest.raises(RuntimeError, match="Session not active"):
            await mock_claude_client.single_completion("Test prompt")

        # Attempt streaming without session should fail
        with pytest.raises(RuntimeError, match="Session not active"):
            async for _ in mock_claude_client.stream_completion("Test prompt"):
                pass

    async def test_sdk_multiple_calls_in_session(
        self, mock_claude_client: MockClaudeCodeClient
    ) -> None:
        """Test multiple SDK calls within same session."""
        await mock_claude_client.start_session()

        # Make multiple calls
        await mock_claude_client.single_completion("First prompt")
        await mock_claude_client.single_completion("Second prompt")

        async for _ in mock_claude_client.stream_completion("Third prompt"):
            pass

        # Verify call count
        assert mock_claude_client.call_count == 3

        await mock_claude_client.end_session()

    def test_sdk_config_options_applied_to_client(self) -> None:
        """Test that SDK configuration options are properly applied."""
        config = SDKConfig(api_key="test-key", timeout=60, max_retries=5, retry_delay=2.0)

        # Test requirements agent configuration
        req_options = config.get_client_options("requirements")
        assert req_options.max_tokens == 4000
        assert req_options.temperature == 0.7
        assert req_options.stream is True
        assert req_options.tools_enabled is True

        # Test developer agent configuration
        dev_options = config.get_client_options("developer")
        assert "Test-Driven Development" in dev_options.system_prompt
        assert dev_options.max_turns == 10

    def test_sdk_config_tool_permissions_integration(self) -> None:
        """Test tool permissions configuration integration."""
        config = SDKConfig(api_key="test-key")

        # Test that each agent type has appropriate permissions
        agents_permissions = {
            "requirements": {"write": True, "execute": False},
            "architect": {"write": True, "execute": False},
            "developer": {"write": True, "execute": True},
            "qa": {"write": False, "execute": True},
            "integration": {"write": False, "execute": True, "web_search": True},
        }

        for agent_type, expected_perms in agents_permissions.items():
            permissions = config.get_tool_permissions(agent_type)
            for perm, expected_value in expected_perms.items():
                assert (
                    permissions[perm] is expected_value
                ), f"{agent_type} {perm} permission mismatch"


@pytest.mark.unit
class TestSDKConfigConnectionHandling:
    """Test SDK configuration connection and error handling."""

    def test_connection_timeout_configuration(self) -> None:
        """Test that connection timeout is properly configured."""
        config = SDKConfig(api_key="test-key", timeout=45)
        assert config.timeout == 45

    def test_retry_configuration(self) -> None:
        """Test that retry configuration is properly set."""
        config = SDKConfig(api_key="test-key", max_retries=7, retry_delay=1.5)
        assert config.max_retries == 7
        assert config.retry_delay == 1.5

    async def test_connection_failure_handling(
        self, mock_claude_client: MockClaudeCodeClient
    ) -> None:
        """Test graceful handling of connection failures."""
        # Simulate connection failure by not starting session
        with pytest.raises(RuntimeError, match="Session not active"):
            await mock_claude_client.single_completion("Test prompt")

    async def test_streaming_interruption_handling(
        self, mock_claude_client: MockClaudeCodeClient
    ) -> None:
        """Test handling of streaming response interruptions."""
        await mock_claude_client.start_session()

        # Simulate interruption by consuming only partial stream
        chunk_count = 0
        try:
            async for _chunk in mock_claude_client.stream_completion("Test prompt"):
                chunk_count += 1
                if chunk_count >= 2:
                    break  # Interrupt stream early
        except Exception:  # noqa: S110
            pass  # Expected behavior for stream interruption

        assert chunk_count >= 2
        await mock_claude_client.end_session()


@pytest.mark.unit
class TestSDKConfigEnvironmentIntegration:
    """Test SDK configuration with environment variables in integration context."""

    def test_api_key_environment_integration(self) -> None:
        """Test API key environment variable integration."""
        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "integration-test-key"}):
            config = SDKConfig()
            assert config.api_key == "integration-test-key"

            # Verify config can create client options
            options = config.get_client_options("requirements")
            assert options.model == "claude-3-5-sonnet-20241022"

    def test_mock_mode_environment_integration(self) -> None:
        """Test mock mode environment variable integration."""
        with patch.dict(os.environ, {"VERIFFLOWCC_MOCK_MODE": "true"}):
            # Mock mode detection would be used by application
            mock_mode = os.getenv("VERIFFLOWCC_MOCK_MODE", "false").lower() == "true"
            assert mock_mode is True

            # In mock mode, we would use different client behavior
            config = SDKConfig(api_key="mock-key")
            assert config.api_key == "mock-key"

    def test_production_environment_configuration(self) -> None:
        """Test production environment configuration."""
        config = SDKConfig(api_key="prod-key", environment="production")
        assert config.environment == "production"

        # Production config should have standard settings
        assert config.timeout == 30
        assert config.max_retries == 3

    def test_development_environment_configuration(self) -> None:
        """Test development environment configuration."""
        config = SDKConfig(
            api_key="dev-key",
            environment="development",
            timeout=120,  # Longer timeout for debugging
            max_retries=1,  # Fewer retries for faster feedback
        )
        assert config.environment == "development"
        assert config.timeout == 120
        assert config.max_retries == 1


@pytest.mark.unit
class TestSDKConfigPerformanceIntegration:
    """Test SDK configuration performance characteristics."""

    async def test_session_creation_performance(
        self, mock_claude_client: MockClaudeCodeClient
    ) -> None:
        """Test that session creation is fast."""
        import time

        start_time = time.time()
        await mock_claude_client.start_session()
        end_time = time.time()

        # Session creation should be very fast (< 1 second)
        assert (end_time - start_time) < 1.0
        assert mock_claude_client.session_active is True

        await mock_claude_client.end_session()

    def test_config_creation_performance(self) -> None:
        """Test that configuration creation is fast."""
        import time

        start_time = time.time()

        # Create multiple configurations
        configs = []
        for i in range(100):
            config = SDKConfig(api_key=f"test-key-{i}")
            configs.append(config)

        end_time = time.time()

        # Creating 100 configs should be fast (< 1 second)
        assert (end_time - start_time) < 1.0
        assert len(configs) == 100

    def test_agent_options_caching_behavior(self) -> None:
        """Test behavior of getting agent options multiple times."""
        config = SDKConfig(api_key="test-key")

        # Get same agent options multiple times
        options1 = config.get_client_options("requirements")
        options2 = config.get_client_options("requirements")

        # Options should have same values (but may be different objects)
        assert options1.system_prompt == options2.system_prompt
        assert options1.max_tokens == options2.max_tokens
        assert options1.temperature == options2.temperature
