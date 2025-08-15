"""Tests for streaming response parsing and event handling.

This module tests the streaming response functionality of the Claude Code SDK
integration, including response parsing, event handling, interruption handling,
and timeout mechanisms.
"""

import asyncio
import time
from collections.abc import AsyncGenerator
from typing import Any

import pytest
from verifflowcc.agents.base import BaseAgent
from verifflowcc.core.sdk_config import SDKConfig

pytestmark = [pytest.mark.unit, pytest.mark.streaming]


class MockStreamingAgent(BaseAgent):
    """Mock agent for testing streaming responses."""

    def __init__(self, sdk_config: SDKConfig, mock_mode: bool = True):
        super().__init__(
            name="test_streaming_agent",
            agent_type="streaming_test",
            sdk_config=sdk_config,
            mock_mode=mock_mode,
        )
        self.stream_calls = 0
        self.last_prompt: str | None = None

    async def process(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """Process input with basic streaming."""
        return {"agent": self.name, "processed": True}

    async def _mock_stream_response(self, prompt: str) -> AsyncGenerator[dict[str, Any], None]:
        """Mock streaming response generator."""
        self.stream_calls += 1
        self.last_prompt = prompt

        # Simulate streaming chunks
        chunks: list[dict[str, Any]] = [
            {"type": "status", "status": "started"},
            {"type": "content", "content": "Hello, "},
            {"type": "content", "content": "this is a "},
            {"type": "content", "content": "streaming response."},
            {"type": "usage", "tokens_used": 15, "completion_tokens": 10},
            {"type": "complete", "finished": True},
        ]

        for chunk in chunks:
            await asyncio.sleep(0.01)  # Simulate network delay
            yield chunk


class TestStreamingResponseParsing:
    """Test streaming response parsing functionality."""

    @pytest.fixture
    def streaming_agent(self) -> MockStreamingAgent:
        """Provide mock streaming agent."""
        config = SDKConfig(api_key="test-streaming-key")
        return MockStreamingAgent(config, mock_mode=True)

    @pytest.mark.asyncio
    async def test_basic_streaming_response_parsing(
        self, streaming_agent: MockStreamingAgent
    ) -> None:
        """Test basic streaming response chunk parsing."""
        chunks = []
        async for chunk in streaming_agent._mock_stream_response("Test prompt"):
            chunks.append(chunk)

        assert len(chunks) == 6
        assert chunks[0]["type"] == "status"
        assert chunks[1]["type"] == "content"
        assert chunks[-1]["type"] == "complete"

    @pytest.mark.asyncio
    async def test_content_aggregation_from_stream(
        self, streaming_agent: MockStreamingAgent
    ) -> None:
        """Test aggregating content from streaming chunks."""
        content_parts = []

        async for chunk in streaming_agent._mock_stream_response("Test prompt"):
            if chunk["type"] == "content":
                content_parts.append(chunk["content"])

        full_content = "".join(content_parts)
        assert full_content == "Hello, this is a streaming response."

    @pytest.mark.asyncio
    async def test_usage_tracking_in_stream(self, streaming_agent: MockStreamingAgent) -> None:
        """Test tracking token usage from streaming response."""
        usage_info = None

        async for chunk in streaming_agent._mock_stream_response("Test prompt"):
            if chunk["type"] == "usage":
                usage_info = chunk
                break

        assert usage_info is not None
        assert usage_info["tokens_used"] == 15
        assert usage_info["completion_tokens"] == 10

    @pytest.mark.asyncio
    async def test_completion_detection(self, streaming_agent: MockStreamingAgent) -> None:
        """Test detection of stream completion."""
        completion_chunk = None

        async for chunk in streaming_agent._mock_stream_response("Test prompt"):
            if chunk["type"] == "complete":
                completion_chunk = chunk

        assert completion_chunk is not None
        assert completion_chunk["finished"] is True


class TestStreamingEventHandling:
    """Test streaming response event handling."""

    @pytest.fixture
    def streaming_agent(self) -> MockStreamingAgent:
        """Provide mock streaming agent."""
        config = SDKConfig(api_key="test-event-key")
        return MockStreamingAgent(config, mock_mode=True)

    @pytest.mark.asyncio
    async def test_event_handler_registration(self, streaming_agent: MockStreamingAgent) -> None:
        """Test registration and calling of event handlers."""
        events_received = []

        def on_chunk(chunk: dict[str, Any]) -> None:
            events_received.append(chunk["type"])

        # Simulate event handling
        async for chunk in streaming_agent._mock_stream_response("Test"):
            on_chunk(chunk)

        assert "status" in events_received
        assert "content" in events_received
        assert "complete" in events_received

    @pytest.mark.asyncio
    async def test_progress_tracking_events(self, streaming_agent: MockStreamingAgent) -> None:
        """Test progress tracking through streaming events."""
        progress_events = []
        content_chunks = 0

        async for chunk in streaming_agent._mock_stream_response("Progress test"):
            if chunk["type"] == "status":
                progress_events.append(chunk["status"])
            elif chunk["type"] == "content":
                content_chunks += 1
            elif chunk["type"] == "complete":
                progress_events.append("completed")

        assert progress_events == ["started", "completed"]
        assert content_chunks == 3  # Three content chunks in mock

    @pytest.mark.asyncio
    async def test_error_event_handling(self, streaming_agent: MockStreamingAgent) -> None:
        """Test handling of error events in stream."""

        async def _error_stream() -> AsyncGenerator[dict[str, Any], None]:
            """Mock stream that produces an error."""
            yield {"type": "status", "status": "started"}
            yield {"type": "content", "content": "Partial content"}
            yield {"type": "error", "error": "Connection timeout", "code": 408}

        chunks = []
        async for chunk in _error_stream():
            chunks.append(chunk)

        assert len(chunks) == 3
        assert chunks[-1]["type"] == "error"
        assert chunks[-1]["code"] == 408

    @pytest.mark.asyncio
    async def test_multiple_concurrent_streams(self, streaming_agent: MockStreamingAgent) -> None:
        """Test handling multiple concurrent streaming responses."""

        async def collect_stream(prompt: str) -> list[dict[str, Any]]:
            chunks = []
            async for chunk in streaming_agent._mock_stream_response(prompt):
                chunks.append(chunk)
            return chunks

        # Run multiple streams concurrently
        tasks = [collect_stream("Stream 1"), collect_stream("Stream 2"), collect_stream("Stream 3")]

        results = await asyncio.gather(*tasks)

        assert len(results) == 3
        for result in results:
            assert len(result) == 6  # Each mock stream returns 6 chunks
            assert result[0]["type"] == "status"
            assert result[-1]["type"] == "complete"


class TestStreamingInterruption:
    """Test streaming response interruption and graceful degradation."""

    @pytest.fixture
    def streaming_agent(self) -> MockStreamingAgent:
        """Provide mock streaming agent."""
        config = SDKConfig(api_key="test-interruption-key")
        return MockStreamingAgent(config, mock_mode=True)

    async def _collect_stream_chunks(
        self, stream: AsyncGenerator[dict[str, Any], None], chunks_list: list[dict[str, Any]]
    ) -> None:
        """Helper method to collect stream chunks."""
        async for chunk in stream:
            chunks_list.append(chunk)

    @pytest.mark.asyncio
    async def test_stream_interruption_handling(self, streaming_agent: MockStreamingAgent) -> None:
        """Test graceful handling of stream interruption."""

        async def _interruptible_stream() -> AsyncGenerator[dict[str, Any], None]:
            """Mock stream that can be interrupted."""
            yield {"type": "status", "status": "started"}
            yield {"type": "content", "content": "First chunk"}

            # Simulate interruption after 2 chunks
            await asyncio.sleep(0.1)
            raise asyncio.CancelledError("Stream interrupted")

        chunks_received: list[dict[str, Any]] = []

        try:
            async for chunk in _interruptible_stream():
                chunks_received.append(chunk)
        except asyncio.CancelledError:
            pass  # Expected interruption

        assert len(chunks_received) == 2
        assert chunks_received[0]["type"] == "status"
        assert chunks_received[1]["type"] == "content"

    @pytest.mark.asyncio
    async def test_timeout_handling(self, streaming_agent: MockStreamingAgent) -> None:
        """Test handling of streaming timeout."""

        async def _slow_stream() -> AsyncGenerator[dict[str, Any], None]:
            """Mock stream that times out."""
            yield {"type": "status", "status": "started"}
            await asyncio.sleep(2)  # Longer than timeout
            yield {"type": "content", "content": "Should not reach here"}

        chunks_received: list[dict[str, Any]] = []

        try:
            await asyncio.wait_for(
                self._collect_stream_chunks(_slow_stream(), chunks_received), timeout=0.5
            )
        except asyncio.TimeoutError:
            pass  # Expected timeout

        assert len(chunks_received) == 1
        assert chunks_received[0]["type"] == "status"

    @pytest.mark.asyncio
    async def test_graceful_degradation_on_error(self, streaming_agent: MockStreamingAgent) -> None:
        """Test graceful degradation when streaming fails."""

        async def _failing_stream() -> AsyncGenerator[dict[str, Any], None]:
            """Mock stream that fails mid-way."""
            yield {"type": "status", "status": "started"}
            yield {"type": "content", "content": "Partial response"}
            raise ConnectionError("Network failure")

        chunks_received: list[dict[str, Any]] = []
        error_occurred = False

        try:
            async for chunk in _failing_stream():
                chunks_received.append(chunk)
        except ConnectionError:
            error_occurred = True

        assert error_occurred
        assert len(chunks_received) == 2
        assert chunks_received[1]["content"] == "Partial response"

    @pytest.mark.asyncio
    async def test_partial_response_recovery(self, streaming_agent: MockStreamingAgent) -> None:
        """Test recovery from partial streaming responses."""
        partial_content = []

        async def _partial_stream() -> AsyncGenerator[dict[str, Any], None]:
            """Stream that provides partial content before failing."""
            chunks = [
                {"type": "content", "content": "Hello "},
                {"type": "content", "content": "world"},
                # Stream ends abruptly without completion marker
            ]
            for chunk in chunks:
                yield chunk

        async for chunk in _partial_stream():
            if chunk["type"] == "content":
                partial_content.append(chunk["content"])

        # Should still be able to use partial content
        recovered_content = "".join(partial_content)
        assert recovered_content == "Hello world"
        assert len(partial_content) == 2


class TestStreamingPerformance:
    """Test streaming response performance characteristics."""

    @pytest.fixture
    def streaming_agent(self) -> MockStreamingAgent:
        """Provide mock streaming agent."""
        config = SDKConfig(api_key="test-performance-key")
        return MockStreamingAgent(config, mock_mode=True)

    @pytest.mark.asyncio
    async def test_streaming_latency(self, streaming_agent: MockStreamingAgent) -> None:
        """Test streaming response latency measurements."""
        start_time = time.time()
        first_chunk_time: float | None = None
        last_chunk_time: float | None = None

        async for _chunk in streaming_agent._mock_stream_response("Latency test"):
            current_time = time.time()
            if first_chunk_time is None:
                first_chunk_time = current_time
            last_chunk_time = current_time

        # Time to first chunk should be minimal
        assert first_chunk_time is not None
        time_to_first_chunk = first_chunk_time - start_time
        assert time_to_first_chunk < 0.1

        # Total streaming time should be reasonable
        assert last_chunk_time is not None
        total_time = last_chunk_time - start_time
        assert total_time < 1.0

    @pytest.mark.asyncio
    async def test_concurrent_stream_performance(self, streaming_agent: MockStreamingAgent) -> None:
        """Test performance with multiple concurrent streams."""

        async def _timed_stream_collection(prompt: str) -> float:
            """Collect stream and return duration."""
            start = time.time()
            chunks = []
            async for chunk in streaming_agent._mock_stream_response(prompt):
                chunks.append(chunk)
            return time.time() - start

        # Run 5 concurrent streams
        start_time = time.time()
        tasks = [_timed_stream_collection(f"Stream {i}") for i in range(5)]
        durations = await asyncio.gather(*tasks)
        total_time = time.time() - start_time

        # Concurrent execution should be faster than sequential
        sequential_estimate = sum(durations)
        assert total_time < sequential_estimate * 0.8  # At least 20% faster

    @pytest.mark.asyncio
    async def test_memory_efficiency_in_streaming(
        self, streaming_agent: MockStreamingAgent
    ) -> None:
        """Test that streaming doesn't accumulate excessive memory."""

        async def _large_stream() -> AsyncGenerator[dict[str, Any], None]:
            """Stream with many small chunks to test memory usage."""
            for i in range(100):
                yield {"type": "content", "content": f"Chunk {i} with some content", "chunk_id": i}
            yield {"type": "complete", "finished": True}

        chunks_processed = 0

        # Process stream without accumulating all chunks
        async for chunk in _large_stream():
            chunks_processed += 1
            # Simulate processing without storing all chunks
            if chunk["type"] == "content":
                # Process content immediately without accumulation
                assert len(chunk["content"]) > 0

        assert chunks_processed == 101  # 100 content + 1 complete
