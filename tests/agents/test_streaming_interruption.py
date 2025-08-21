"""Tests for streaming response interruption and graceful degradation.

This module tests the streaming response interruption handling,
graceful degradation on failures, timeout management, and
recovery mechanisms for Claude Code SDK integration.
"""

import asyncio
import time
from collections.abc import AsyncGenerator
from typing import Any

import pytest
from verifflowcc.agents.base import BaseAgent
from verifflowcc.core.sdk_config import SDKConfig

pytestmark = [pytest.mark.unit, pytest.mark.streaming, pytest.mark.interruption]


class MockInterruptibleAgent(BaseAgent):
    """Mock agent that supports interruption scenarios."""

    def __init__(self, sdk_config: SDKConfig):
        super().__init__(
            name="test_interruption_agent",
            agent_type="interruption_test",
            sdk_config=sdk_config,
        )
        self.interruption_count = 0
        self.recovery_attempts = 0
        self.partial_responses: list[str] = []

    async def process(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """Process with interruption handling."""
        return {"agent": self.name, "processed": True}

    async def stream_with_interruption(
        self, interruption_point: int = 3
    ) -> AsyncGenerator[dict[str, Any], None]:
        """Mock stream that gets interrupted at specified point."""
        try:
            for i in range(10):
                if i == interruption_point:
                    self.interruption_count += 1
                    raise asyncio.CancelledError(f"Interrupted at chunk {i}")

                yield {
                    "type": "content",
                    "content": f"Chunk {i} content",
                    "chunk_id": i,
                }
                await asyncio.sleep(0.01)

            yield {"type": "complete", "finished": True}

        except asyncio.CancelledError as e:
            # Graceful degradation - yield partial completion info
            yield {
                "type": "interrupted",
                "partial": True,
                "chunks_delivered": interruption_point,
                "error": str(e),
            }
            raise

    async def stream_with_timeout(
        self, chunk_delay: float = 0.1, total_chunks: int = 5
    ) -> AsyncGenerator[dict[str, Any], None]:
        """Mock stream with configurable delays for timeout testing."""
        for i in range(total_chunks):
            await asyncio.sleep(chunk_delay)
            yield {
                "type": "content",
                "content": f"Delayed chunk {i}",
                "delay": chunk_delay,
            }

        yield {"type": "complete", "finished": True}

    async def stream_with_network_failure(
        self, failure_point: int = 2
    ) -> AsyncGenerator[dict[str, Any], None]:
        """Mock stream that simulates network failures."""
        try:
            for i in range(5):
                if i == failure_point:
                    raise ConnectionError(f"Network failure at chunk {i}")

                yield {"type": "content", "content": f"Network chunk {i}"}
                await asyncio.sleep(0.01)

            yield {"type": "complete", "finished": True}

        except ConnectionError as e:
            # Store partial response for recovery
            self.partial_responses.append(f"Partial up to chunk {failure_point - 1}")
            yield {
                "type": "error",
                "error_type": "network_failure",
                "message": str(e),
                "recoverable": True,
            }
            raise

    async def recover_from_failure(
        self, from_chunk: int = 0
    ) -> AsyncGenerator[dict[str, Any], None]:
        """Attempt to recover streaming from specified point."""
        self.recovery_attempts += 1

        yield {"type": "recovery", "resuming_from": from_chunk}

        for i in range(from_chunk, 5):
            yield {"type": "content", "content": f"Recovered chunk {i}"}
            await asyncio.sleep(0.01)

        yield {"type": "complete", "finished": True, "recovered": True}


class TestStreamingInterruption:
    """Test streaming response interruption handling."""

    @pytest.fixture
    def interruption_agent(self) -> MockInterruptibleAgent:
        """Provide mock interruptible agent."""
        config = SDKConfig(api_key="test-interruption-key")
        return MockInterruptibleAgent(config)

    @pytest.mark.asyncio
    async def test_manual_stream_cancellation(
        self, interruption_agent: MockInterruptibleAgent
    ) -> None:
        """Test manual cancellation of streaming response."""
        chunks_received = []

        try:
            async for chunk in interruption_agent.stream_with_interruption(3):
                chunks_received.append(chunk)
        except asyncio.CancelledError:
            pass  # Expected interruption

        # Should receive chunks up to interruption point plus interruption info
        assert len(chunks_received) == 4  # 3 content + 1 interrupted
        assert chunks_received[2]["chunk_id"] == 2  # Last successful chunk
        assert chunks_received[3]["type"] == "interrupted"
        assert chunks_received[3]["partial"] is True
        assert interruption_agent.interruption_count == 1

    @pytest.mark.asyncio
    async def test_task_cancellation_during_stream(
        self, interruption_agent: MockInterruptibleAgent
    ) -> None:
        """Test task cancellation propagates properly through stream."""

        async def _streaming_task() -> list[dict[str, Any]]:
            chunks: list[dict[str, Any]] = []
            try:
                async for chunk in interruption_agent.stream_with_interruption(
                    10
                ):  # Would normally not interrupt
                    chunks.append(chunk)
                    # Check for cancellation during processing
                    await asyncio.sleep(0.001)
            except asyncio.CancelledError:
                # This is expected when task is cancelled
                raise
            return chunks

        # Start task and cancel it after short delay
        task = asyncio.create_task(_streaming_task())
        await asyncio.sleep(0.05)  # Let some chunks process
        task.cancel()

        with pytest.raises(asyncio.CancelledError):
            await task

        # The interruption count won't be incremented by external cancellation
        # but we can verify the task was properly cancelled
        assert task.cancelled()

    @pytest.mark.asyncio
    async def test_partial_data_preservation_on_interruption(
        self, interruption_agent: MockInterruptibleAgent
    ) -> None:
        """Test that partial data is preserved when stream is interrupted."""
        chunks_received = []
        partial_content = []

        try:
            async for chunk in interruption_agent.stream_with_interruption(4):
                chunks_received.append(chunk)
                if chunk["type"] == "content":
                    partial_content.append(chunk["content"])
        except asyncio.CancelledError:
            pass

        # Verify partial content is usable
        assert len(partial_content) == 4  # Chunks 0-3
        assert "Chunk 3 content" in partial_content[3]

        # Verify interruption metadata
        interrupted_chunk = chunks_received[-1]
        assert interrupted_chunk["type"] == "interrupted"
        assert interrupted_chunk["chunks_delivered"] == 4

    @pytest.mark.asyncio
    async def test_concurrent_interruption_handling(
        self, interruption_agent: MockInterruptibleAgent
    ) -> None:
        """Test interruption handling with multiple concurrent streams."""

        async def _collect_until_interruption(interruption_point: int) -> int:
            count = 0
            try:
                async for chunk in interruption_agent.stream_with_interruption(interruption_point):
                    if chunk["type"] == "content":
                        count += 1
            except asyncio.CancelledError:
                pass
            return count

        # Run multiple streams with different interruption points
        tasks = [
            _collect_until_interruption(2),
            _collect_until_interruption(4),
            _collect_until_interruption(6),
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # All tasks should complete (with interruptions)
        assert len(results) == 3
        assert all(isinstance(r, int) for r in results)
        assert interruption_agent.interruption_count == 3


class TestStreamingTimeouts:
    """Test streaming response timeout handling."""

    @pytest.fixture
    def interruption_agent(self) -> MockInterruptibleAgent:
        """Provide mock interruptible agent."""
        config = SDKConfig(api_key="test-timeout-key", timeout=30)
        return MockInterruptibleAgent(config)

    @pytest.mark.asyncio
    async def test_stream_timeout_detection(
        self, interruption_agent: MockInterruptibleAgent
    ) -> None:
        """Test detection and handling of streaming timeouts."""
        chunks_received = []
        timeout_occurred = False

        async def _collect_timeout_chunks() -> None:
            async for chunk in interruption_agent.stream_with_timeout(0.3, 3):
                chunks_received.append(chunk)

        try:
            # Use 0.2 second timeout with 0.3 second chunk delays
            await asyncio.wait_for(_collect_timeout_chunks(), timeout=0.2)
        except asyncio.TimeoutError:
            timeout_occurred = True

        assert timeout_occurred
        assert len(chunks_received) == 0  # No chunks should complete

    @pytest.mark.asyncio
    async def test_partial_timeout_handling(
        self, interruption_agent: MockInterruptibleAgent
    ) -> None:
        """Test handling timeout after receiving some chunks."""
        chunks_received = []
        timeout_occurred = False

        async def _collect_partial_chunks() -> None:
            async for chunk in interruption_agent.stream_with_timeout(0.1, 5):
                chunks_received.append(chunk)

        try:
            # Use 0.15 second timeout with 0.1 second delays
            await asyncio.wait_for(_collect_partial_chunks(), timeout=0.15)
        except asyncio.TimeoutError:
            timeout_occurred = True

        assert timeout_occurred
        assert len(chunks_received) == 1  # Should get first chunk
        assert chunks_received[0]["content"] == "Delayed chunk 0"

    @pytest.mark.asyncio
    async def test_timeout_recovery_mechanism(
        self, interruption_agent: MockInterruptibleAgent
    ) -> None:
        """Test recovery mechanism after timeout."""

        async def _attempt_stream_with_recovery() -> dict[str, Any]:
            """Attempt stream with timeout and recovery."""
            for attempt in range(3):
                try:
                    chunks: list[dict[str, Any]] = []
                    # Progressively longer timeouts
                    timeout_duration = 0.1 * (attempt + 1)

                    async def _collect_recovery_chunks(
                        chunks_list: list[dict[str, Any]],
                    ) -> None:
                        async for chunk in interruption_agent.stream_with_timeout(0.05, 3):
                            chunks_list.append(chunk)

                    await asyncio.wait_for(
                        _collect_recovery_chunks(chunks), timeout=timeout_duration
                    )

                    return {"success": True, "chunks": len(chunks), "attempt": attempt}

                except asyncio.TimeoutError:
                    if attempt == 2:  # Last attempt
                        return {"success": False, "final_attempt": True}
                    continue

            return {"success": False}

        result = await _attempt_stream_with_recovery()

        # Should succeed on second or third attempt with longer timeout
        assert result["success"] is True
        assert result["chunks"] == 4  # 3 content + 1 complete

    @pytest.mark.asyncio
    async def test_configurable_timeout_behavior(
        self, interruption_agent: MockInterruptibleAgent
    ) -> None:
        """Test configurable timeout behavior from SDK config."""
        # Test with different timeout configurations
        short_config = SDKConfig(api_key="test-short", timeout=1)
        long_config = SDKConfig(api_key="test-long", timeout=60)

        short_agent = MockInterruptibleAgent(short_config)
        long_agent = MockInterruptibleAgent(long_config)

        # Verify timeout values are set correctly
        assert short_agent.sdk_config.timeout == 1
        assert long_agent.sdk_config.timeout == 60

        # Both agents should handle timeouts according to their config
        start_time = time.time()

        async def _collect_config_chunks() -> None:
            async for _chunk in short_agent.stream_with_timeout(0.5, 3):
                pass

        try:
            await asyncio.wait_for(_collect_config_chunks(), timeout=short_agent.sdk_config.timeout)
        except asyncio.TimeoutError:
            elapsed = time.time() - start_time
            assert elapsed < 1.5  # Should timeout quickly


class TestGracefulDegradation:
    """Test graceful degradation on streaming failures."""

    @pytest.fixture
    def interruption_agent(self) -> MockInterruptibleAgent:
        """Provide mock interruptible agent."""
        config = SDKConfig(api_key="test-degradation-key")
        return MockInterruptibleAgent(config)

    @pytest.mark.asyncio
    async def test_network_failure_graceful_handling(
        self, interruption_agent: MockInterruptibleAgent
    ) -> None:
        """Test graceful handling of network failures during streaming."""
        chunks_received = []
        error_info = None

        try:
            async for chunk in interruption_agent.stream_with_network_failure(2):
                chunks_received.append(chunk)
                if chunk["type"] == "error":
                    error_info = chunk
        except ConnectionError:
            pass  # Expected network failure

        # Should receive chunks before failure plus error info
        assert len(chunks_received) == 3  # 2 content + 1 error
        assert chunks_received[0]["content"] == "Network chunk 0"
        assert chunks_received[1]["content"] == "Network chunk 1"

        assert error_info is not None
        assert error_info["type"] == "error"
        assert error_info["error_type"] == "network_failure"
        assert error_info["recoverable"] is True

        # Verify partial response was stored
        assert len(interruption_agent.partial_responses) == 1
        assert "Partial up to chunk 1" in interruption_agent.partial_responses[0]

    @pytest.mark.asyncio
    async def test_automatic_recovery_after_failure(
        self, interruption_agent: MockInterruptibleAgent
    ) -> None:
        """Test automatic recovery after streaming failure."""
        # First, simulate failure to set up recovery state
        try:
            async for _chunk in interruption_agent.stream_with_network_failure(1):
                pass
        except ConnectionError:
            pass

        # Now attempt recovery
        recovery_chunks = []
        async for chunk in interruption_agent.recover_from_failure(1):
            recovery_chunks.append(chunk)

        assert len(recovery_chunks) == 6  # 1 recovery + 4 content + 1 complete
        assert recovery_chunks[0]["type"] == "recovery"
        assert recovery_chunks[0]["resuming_from"] == 1
        assert recovery_chunks[-1]["type"] == "complete"
        assert recovery_chunks[-1]["recovered"] is True
        assert interruption_agent.recovery_attempts == 1

    @pytest.mark.asyncio
    async def test_progressive_backoff_on_repeated_failures(
        self, interruption_agent: MockInterruptibleAgent
    ) -> None:
        """Test progressive backoff strategy on repeated failures."""

        async def _failing_stream_with_backoff() -> AsyncGenerator[dict[str, Any], None]:
            """Stream that fails with progressive delays."""
            for attempt in range(3):
                try:
                    # Simulate increasing delay between retries
                    await asyncio.sleep(0.01 * (2**attempt))  # 0.01, 0.02, 0.04

                    if attempt < 2:  # Fail first two attempts
                        raise ConnectionError(f"Attempt {attempt + 1} failed")

                    # Succeed on third attempt
                    yield {"type": "content", "content": "Success after retries"}
                    yield {"type": "complete", "finished": True}
                    return

                except ConnectionError as e:
                    yield {
                        "type": "retry",
                        "attempt": attempt + 1,
                        "next_delay": 0.01 * (2 ** (attempt + 1)),
                        "error": str(e),
                    }
                    if attempt == 2:  # Max attempts reached
                        yield {"type": "failed", "max_attempts_reached": True}
                        raise

        chunks: list[dict[str, Any]] = []
        success = False

        try:
            async for chunk in _failing_stream_with_backoff():
                chunks.append(chunk)
                if chunk["type"] == "complete":
                    success = True
        except ConnectionError:
            pass

        # Should have retry attempts followed by success
        retry_chunks = [c for c in chunks if c["type"] == "retry"]
        assert len(retry_chunks) == 2  # Two retry attempts
        assert success is True

        # Verify progressive backoff
        assert retry_chunks[0]["next_delay"] == 0.02
        assert retry_chunks[1]["next_delay"] == 0.04

    @pytest.mark.asyncio
    async def test_fallback_to_non_streaming_mode(
        self, interruption_agent: MockInterruptibleAgent
    ) -> None:
        """Test fallback to non-streaming mode on streaming failure."""

        async def _stream_with_fallback() -> dict[str, Any]:
            """Attempt streaming with fallback to batch processing."""
            streaming_chunks = []

            try:
                # Attempt streaming
                async for chunk in interruption_agent.stream_with_network_failure(0):
                    streaming_chunks.append(chunk)

                return {"mode": "streaming", "chunks": len(streaming_chunks)}

            except ConnectionError:
                # Fallback to non-streaming mode
                await asyncio.sleep(0.1)  # Simulate non-streaming processing
                return {
                    "mode": "fallback",
                    "content": "Complete response via fallback",
                    "partial_chunks": len(streaming_chunks),
                }

        result = await _stream_with_fallback()

        assert result["mode"] == "fallback"
        assert result["content"] == "Complete response via fallback"
        assert result["partial_chunks"] == 1  # Error chunk received

    @pytest.mark.asyncio
    async def test_data_integrity_during_degradation(
        self, interruption_agent: MockInterruptibleAgent
    ) -> None:
        """Test data integrity is maintained during graceful degradation."""
        partial_data = []
        error_occurred = False

        try:
            async for chunk in interruption_agent.stream_with_network_failure(3):
                if chunk["type"] == "content":
                    partial_data.append(chunk["content"])
                elif chunk["type"] == "error":
                    error_occurred = True
                    # Verify error info includes data integrity markers
                    assert "recoverable" in chunk
                    assert chunk["recoverable"] is True
        except ConnectionError:
            pass

        # Verify partial data integrity
        assert len(partial_data) == 3
        assert partial_data[0] == "Network chunk 0"
        assert partial_data[1] == "Network chunk 1"
        assert partial_data[2] == "Network chunk 2"
        assert error_occurred is True

        # Verify agent maintains partial responses for recovery
        assert len(interruption_agent.partial_responses) == 1


class TestErrorRecovery:
    """Test error recovery mechanisms for streaming responses."""

    @pytest.fixture
    def interruption_agent(self) -> MockInterruptibleAgent:
        """Provide mock interruptible agent."""
        config = SDKConfig(api_key="test-recovery-key", max_retries=3)
        return MockInterruptibleAgent(config)

    @pytest.mark.asyncio
    async def test_retry_mechanism_with_exponential_backoff(
        self, interruption_agent: MockInterruptibleAgent
    ) -> None:
        """Test retry mechanism with exponential backoff."""

        async def _retry_with_backoff(max_retries: int = 3) -> dict[str, Any]:
            """Retry streaming with exponential backoff."""
            for attempt in range(max_retries):
                try:
                    chunks: list[dict[str, Any]] = []

                    # Simulate network instability - fail first 2 attempts
                    if attempt < 2:
                        await asyncio.sleep(0.01 * (2**attempt))  # Exponential backoff
                        raise ConnectionError(f"Network unstable (attempt {attempt + 1})")

                    # Succeed on third attempt
                    async for chunk in interruption_agent.recover_from_failure(0):
                        chunks.append(chunk)

                    return {
                        "success": True,
                        "attempts": attempt + 1,
                        "chunks": len(chunks),
                    }

                except ConnectionError:
                    if attempt == max_retries - 1:
                        return {"success": False, "attempts": max_retries}
                    continue

            # This should never be reached, but needed for mypy
            return {"success": False, "attempts": max_retries}

        result = await _retry_with_backoff()

        assert result["success"] is True
        assert result["attempts"] == 3
        assert result["chunks"] >= 6  # Recovery stream produces at least 6 chunks
        assert interruption_agent.recovery_attempts == 1

    @pytest.mark.asyncio
    async def test_circuit_breaker_pattern(
        self, interruption_agent: MockInterruptibleAgent
    ) -> None:
        """Test circuit breaker pattern for streaming failures."""
        failure_count = 0
        circuit_open = False

        async def _circuit_breaker_stream() -> AsyncGenerator[dict[str, Any], None]:
            """Stream with circuit breaker pattern."""
            nonlocal failure_count, circuit_open

            if circuit_open:
                yield {"type": "circuit_open", "message": "Circuit breaker open"}
                return

            try:
                failure_count += 1

                # Fail first 3 attempts to open circuit
                if failure_count <= 3:
                    raise ConnectionError(f"Failure #{failure_count}")

                # Success after circuit recovery
                yield {"type": "content", "content": "Circuit recovered"}
                yield {"type": "complete", "finished": True}
                failure_count = 0  # Reset on success

            except ConnectionError:
                if failure_count >= 3:
                    circuit_open = True
                    yield {"type": "circuit_open", "reason": "Too many failures"}
                raise

        # Test circuit opening
        for _i in range(4):
            try:
                chunks: list[dict[str, Any]] = []
                async for chunk in _circuit_breaker_stream():
                    chunks.append(chunk)
            except ConnectionError:
                pass

        assert circuit_open is True
        assert failure_count == 3

        # Test circuit stays open
        open_chunks: list[dict[str, Any]] = []
        async for chunk in _circuit_breaker_stream():
            open_chunks.append(chunk)

        assert len(open_chunks) == 1
        assert open_chunks[0]["type"] == "circuit_open"

    @pytest.mark.asyncio
    async def test_stateful_recovery_coordination(
        self, interruption_agent: MockInterruptibleAgent
    ) -> None:
        """Test stateful coordination of recovery across multiple operations."""
        # Simulate multiple concurrent streams failing
        recovery_states = []

        async def _coordinated_recovery(stream_id: int) -> dict[str, Any]:
            """Coordinated recovery for multiple streams."""
            try:
                # Each stream fails at different points
                chunks: list[dict[str, Any]] = []
                async for chunk in interruption_agent.stream_with_network_failure(stream_id):
                    chunks.append(chunk)

                return {"stream_id": stream_id, "success": True, "chunks": len(chunks)}

            except ConnectionError:
                recovery_states.append(
                    {
                        "stream_id": stream_id,
                        "failed_at": stream_id,
                        "partial_responses": len(interruption_agent.partial_responses),
                    }
                )

                # Attempt coordinated recovery
                recovery_chunks = []
                async for chunk in interruption_agent.recover_from_failure(stream_id):
                    recovery_chunks.append(chunk)

                return {
                    "stream_id": stream_id,
                    "success": True,
                    "recovered": True,
                    "chunks": len(recovery_chunks),
                }

        # Run multiple streams that will fail and recover
        tasks = [_coordinated_recovery(i) for i in range(3)]
        results = await asyncio.gather(*tasks)

        # All streams should recover
        assert len(results) == 3
        assert all(r["success"] for r in results)
        assert all(r["recovered"] for r in results)

        # Verify recovery coordination
        assert len(recovery_states) == 3
        assert interruption_agent.recovery_attempts == 3
        assert len(interruption_agent.partial_responses) == 3
