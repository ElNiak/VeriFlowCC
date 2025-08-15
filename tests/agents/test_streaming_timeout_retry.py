"""Tests for streaming timeout handling and retry mechanisms.

This module tests timeout detection, retry logic with backoff strategies,
circuit breaker patterns, and graceful degradation for streaming
responses in the Claude Code SDK integration.
"""

import asyncio
from collections.abc import AsyncGenerator
from typing import Any

import pytest
from verifflowcc.agents.base import BaseAgent
from verifflowcc.core.sdk_config import SDKConfig

pytestmark = [pytest.mark.unit, pytest.mark.streaming, pytest.mark.timeout, pytest.mark.retry]


class MockTimeoutAgent(BaseAgent):
    """Mock agent for testing timeout and retry scenarios."""

    def __init__(self, sdk_config: SDKConfig, mock_mode: bool = True):
        super().__init__(
            name="test_timeout_agent",
            agent_type="timeout_test",
            sdk_config=sdk_config,
            mock_mode=mock_mode,
        )
        self.timeout_count = 0
        self.retry_count = 0
        self.circuit_breaker_state = "closed"  # closed, open, half_open
        self.failure_count = 0
        self.last_failure_time = None
        self.success_count = 0

    async def process(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """Process with timeout and retry handling."""
        return {"agent": self.name, "processed": True}

    async def stream_with_configurable_timeout(
        self,
        chunk_delay: float = 0.1,
        total_chunks: int = 5,
        fail_after_chunk: int | None = None,
    ) -> AsyncGenerator[dict[str, Any], None]:
        """Stream with configurable timeouts and failures."""
        try:
            for i in range(total_chunks):
                if fail_after_chunk is not None and i >= fail_after_chunk:
                    raise asyncio.TimeoutError(f"Timeout after chunk {i}")

                await asyncio.sleep(chunk_delay)
                yield {
                    "type": "content",
                    "content": f"Chunk {i}",
                    "chunk_index": i,
                    "delay_used": chunk_delay,
                }

            yield {"type": "complete", "finished": True}

        except asyncio.TimeoutError as e:
            self.timeout_count += 1
            yield {
                "type": "timeout",
                "error": str(e),
                "chunks_delivered": fail_after_chunk if fail_after_chunk is not None else i,
                "timeout_count": self.timeout_count,
            }
            raise


class TestStreamingTimeoutDetection:
    """Test streaming timeout detection and handling."""

    @pytest.fixture
    def timeout_agent(self) -> MockTimeoutAgent:
        """Provide mock timeout agent."""
        config = SDKConfig(api_key="test-timeout-key", timeout=30)
        return MockTimeoutAgent(config, mock_mode=True)

    @pytest.mark.asyncio
    async def test_basic_timeout_detection(self, timeout_agent: MockTimeoutAgent) -> None:
        """Test basic timeout detection in streaming responses."""
        chunks_received = []
        timeout_occurred = False

        async def _collect_chunks() -> None:
            async for chunk in timeout_agent.stream_with_configurable_timeout(0.05, 5):
                chunks_received.append(chunk)

        try:
            # Set tight timeout on slow stream
            await asyncio.wait_for(_collect_chunks(), timeout=0.1)
        except asyncio.TimeoutError:
            timeout_occurred = True

        assert timeout_occurred
        # Should receive some chunks before timeout
        assert len(chunks_received) >= 1
        assert chunks_received[0]["type"] == "content"

    @pytest.mark.asyncio
    async def test_timeout_with_partial_response_recovery(
        self, timeout_agent: MockTimeoutAgent
    ) -> None:
        """Test recovery of partial response data on timeout."""
        partial_data = []
        timeout_info = None

        try:
            async for chunk in timeout_agent.stream_with_configurable_timeout(
                0.05, 10, fail_after_chunk=3
            ):
                if chunk["type"] == "content":
                    partial_data.append(chunk["content"])
                elif chunk["type"] == "timeout":
                    timeout_info = chunk
        except asyncio.TimeoutError:
            pass

        # Should have partial data and timeout info
        assert len(partial_data) == 3  # Chunks 0, 1, 2
        assert timeout_info is not None
        assert timeout_info["type"] == "timeout"
        assert timeout_info["chunks_delivered"] == 3
        assert timeout_agent.timeout_count == 1
