"""Performance tests for SDK configuration and operations.

This module contains performance benchmarks for SDK configuration,
session management, and agent operations to establish baseline metrics.
"""

import asyncio
import time
from typing import Any

import pytest
from verifflowcc.core.sdk_config import SDKConfig


@pytest.mark.performance
class TestSDKConfigPerformance:
    """Performance benchmarks for SDK configuration operations."""

    def test_sdk_config_initialization_benchmark(self, benchmark: Any) -> None:
        """Benchmark SDK configuration initialization performance."""

        def create_config() -> SDKConfig:
            return SDKConfig(api_key="benchmark-key")

        result = benchmark(create_config)
        assert result.api_key == "benchmark-key"

    def test_get_client_options_benchmark(self, benchmark: Any) -> None:
        """Benchmark getting client options for different agents."""
        config = SDKConfig(api_key="benchmark-key")

        def get_options() -> Any:
            return config.get_client_options("requirements")

        result = benchmark(get_options)
        assert result.max_tokens == 4000

    def test_get_tool_permissions_benchmark(self, benchmark: Any) -> None:
        """Benchmark getting tool permissions for agents."""
        config = SDKConfig(api_key="benchmark-key")

        def get_permissions() -> dict[str, bool]:
            return config.get_tool_permissions("developer")

        result = benchmark(get_permissions)
        assert result["write"] is True

    def test_multiple_agent_configs_benchmark(self, benchmark: Any) -> None:
        """Benchmark creating configurations for multiple agents."""
        config = SDKConfig(api_key="benchmark-key")
        agent_types = ["requirements", "architect", "developer", "qa", "integration"]

        def get_all_configs() -> dict[str, dict[str, Any]]:
            return {
                agent_type: {
                    "options": config.get_client_options(agent_type),
                    "permissions": config.get_tool_permissions(agent_type),
                }
                for agent_type in agent_types
            }

        result = benchmark(get_all_configs)
        assert len(result) == 5

    @pytest.mark.parametrize(
        "agent_type", ["requirements", "architect", "developer", "qa", "integration"]
    )
    def test_individual_agent_config_benchmark(self, benchmark: Any, agent_type: str) -> None:
        """Benchmark individual agent configuration creation."""
        config = SDKConfig(api_key="benchmark-key")

        def get_agent_config() -> dict[str, Any]:
            return {
                "options": config.get_client_options(agent_type),
                "permissions": config.get_tool_permissions(agent_type),
            }

        result = benchmark(get_agent_config)
        assert "options" in result
        assert "permissions" in result

    def test_config_serialization_benchmark(self, benchmark: Any) -> None:
        """Benchmark configuration serialization performance."""
        config = SDKConfig(
            api_key="benchmark-key",
            base_url="https://api.benchmark.com",
            timeout=60,
            max_retries=5,
            retry_delay=1.5,
            environment="benchmark",
        )

        def serialize_config() -> dict[str, Any]:
            return config.__dict__

        result = benchmark(serialize_config)
        assert result["api_key"] == "benchmark-key"

    def test_config_deserialization_benchmark(self, benchmark: Any) -> None:
        """Benchmark configuration deserialization performance."""
        config_dict: dict[str, Any] = {
            "api_key": "benchmark-key",
            "base_url": "https://api.benchmark.com",
            "timeout": 60,
            "max_retries": 5,
            "retry_delay": 1.5,
            "environment": "benchmark",
        }

        def deserialize_config() -> SDKConfig:
            return SDKConfig(**config_dict)

        result = benchmark(deserialize_config)
        assert result.api_key == "benchmark-key"


@pytest.mark.performance
@pytest.mark.asyncio
class TestSDKSessionPerformance:
    """Performance benchmarks for SDK session operations."""

    class MockPerformanceClient:
        """High-performance mock client for benchmarking."""

        def __init__(self, config: SDKConfig):
            self.config = config
            self.session_active = False

        async def start_session(self) -> None:
            """Mock fast session start."""
            await asyncio.sleep(0.001)  # Simulate minimal overhead
            self.session_active = True

        async def end_session(self) -> None:
            """Mock fast session end."""
            await asyncio.sleep(0.001)  # Simulate minimal overhead
            self.session_active = False

        async def single_completion(self, prompt: str) -> dict[str, Any]:
            """Mock fast completion."""
            if not self.session_active:
                raise RuntimeError("Session not active")
            await asyncio.sleep(0.01)  # Simulate API call
            return {"content": "Fast response", "usage": {"tokens": 5}}

    @pytest.fixture
    def performance_client(self) -> "MockPerformanceClient":
        """Provide high-performance mock client."""
        config = SDKConfig(api_key="performance-key")
        return self.MockPerformanceClient(config)

    async def test_session_lifecycle_benchmark(
        self, performance_client: "MockPerformanceClient"
    ) -> None:
        """Benchmark session lifecycle performance."""
        start_time = time.time()

        # Session lifecycle
        await performance_client.start_session()
        assert performance_client.session_active is True

        await performance_client.end_session()
        assert performance_client.session_active is False

        end_time = time.time()

        # Session lifecycle should be very fast (< 0.1 seconds)
        duration = end_time - start_time
        assert duration < 0.1, f"Session lifecycle took {duration:.3f}s, expected < 0.1s"

    async def test_multiple_sessions_benchmark(
        self, performance_client: "MockPerformanceClient"
    ) -> None:
        """Benchmark creating multiple sessions."""
        start_time = time.time()

        # Create and destroy multiple sessions
        for _ in range(10):
            await performance_client.start_session()
            await performance_client.end_session()

        end_time = time.time()

        # 10 session cycles should be fast (< 1 second)
        duration = end_time - start_time
        assert duration < 1.0, f"10 session cycles took {duration:.3f}s, expected < 1.0s"

    async def test_concurrent_operations_benchmark(
        self, performance_client: "MockPerformanceClient"
    ) -> None:
        """Benchmark concurrent operations within a session."""
        await performance_client.start_session()

        start_time = time.time()

        # Run multiple concurrent operations
        tasks = [performance_client.single_completion(f"Prompt {i}") for i in range(5)]
        results = await asyncio.gather(*tasks)

        end_time = time.time()

        # 5 concurrent operations should complete quickly
        duration = end_time - start_time
        assert len(results) == 5
        assert duration < 0.5, f"5 concurrent ops took {duration:.3f}s, expected < 0.5s"

        await performance_client.end_session()

    async def test_session_reuse_benchmark(
        self, performance_client: "MockPerformanceClient"
    ) -> None:
        """Benchmark session reuse for multiple operations."""
        await performance_client.start_session()

        start_time = time.time()

        # Multiple operations in same session
        for i in range(10):
            result = await performance_client.single_completion(f"Sequential prompt {i}")
            assert result["content"] == "Fast response"

        end_time = time.time()

        # 10 sequential operations should be reasonably fast
        duration = end_time - start_time
        assert duration < 2.0, f"10 sequential ops took {duration:.3f}s, expected < 2.0s"

        await performance_client.end_session()


@pytest.mark.performance
class TestSDKConfigMemoryUsage:
    """Memory usage tests for SDK configuration."""

    def test_config_memory_footprint(self) -> None:
        """Test memory footprint of SDK configuration."""

        # Measure memory before creating configs
        configs = []

        # Create many configurations
        for i in range(1000):
            config = SDKConfig(api_key=f"memory-test-{i}")
            configs.append(config)

        # Verify all configs are created
        assert len(configs) == 1000

        # Memory usage should be reasonable
        # This is more of a smoke test than strict validation
        for i, config in enumerate(configs):
            assert config.api_key == f"memory-test-{i}"

    def test_agent_options_memory_usage(self) -> None:
        """Test memory usage when creating many agent options."""
        config = SDKConfig(api_key="memory-test-key")
        agent_types = ["requirements", "architect", "developer", "qa", "integration"]

        # Create many agent option sets
        options_sets = []
        for _ in range(100):
            option_set = {}
            for agent_type in agent_types:
                option_set[agent_type] = config.get_client_options(agent_type)
            options_sets.append(option_set)

        # Verify all option sets are created
        assert len(options_sets) == 100

        # Verify content consistency
        for option_set in options_sets[:5]:  # Check first 5
            for agent_type in agent_types:
                assert agent_type in option_set
                assert option_set[agent_type].max_tokens == 4000

    def test_long_running_config_stability(self) -> None:
        """Test configuration stability over many operations."""
        config = SDKConfig(api_key="stability-test-key")

        # Perform many operations
        for i in range(1000):
            # Get options for random agent
            agent_type = ["requirements", "architect", "developer", "qa", "integration"][i % 5]
            options = config.get_client_options(agent_type)
            permissions = config.get_tool_permissions(agent_type)

            # Verify consistency
            assert options.max_tokens == 4000
            assert "read" in permissions

        # Config should remain stable
        assert config.api_key == "stability-test-key"
        assert config.timeout == 30


@pytest.mark.performance
class TestSDKConfigScalability:
    """Scalability tests for SDK configuration."""

    @pytest.mark.parametrize("config_count", [10, 50, 100, 500])
    def test_multiple_config_creation_scalability(self, config_count: int) -> None:
        """Test scalability of creating multiple configurations."""
        start_time = time.time()

        configs = []
        for i in range(config_count):
            config = SDKConfig(api_key=f"scale-test-{i}")
            configs.append(config)

        end_time = time.time()
        duration = end_time - start_time

        # Should scale linearly with reasonable performance
        assert len(configs) == config_count

        # Performance should be reasonable (< 10ms per config on average)
        avg_time_per_config = duration / config_count
        assert avg_time_per_config < 0.01, f"Average time per config: {avg_time_per_config:.4f}s"

    @pytest.mark.parametrize("operation_count", [100, 500, 1000])
    def test_repeated_operations_scalability(self, operation_count: int) -> None:
        """Test scalability of repeated operations on same config."""
        config = SDKConfig(api_key="repeated-ops-test")

        start_time = time.time()

        results = []
        for i in range(operation_count):
            agent_type = ["requirements", "architect", "developer", "qa", "integration"][i % 5]
            options = config.get_client_options(agent_type)
            permissions = config.get_tool_permissions(agent_type)
            results.append((options, permissions))

        end_time = time.time()
        duration = end_time - start_time

        # Verify all operations completed
        assert len(results) == operation_count

        # Performance should remain consistent
        avg_time_per_op = duration / operation_count
        assert avg_time_per_op < 0.001, f"Average time per operation: {avg_time_per_op:.5f}s"

    def test_concurrent_config_access_scalability(self) -> None:
        """Test scalability of concurrent access to configurations."""
        import queue
        import threading

        config = SDKConfig(api_key="concurrent-test")
        results_queue: queue.Queue[list[tuple[int, int, int, int]]] = queue.Queue()

        def worker(worker_id: int, operations: int) -> None:
            """Worker thread for concurrent operations."""
            thread_results = []
            for i in range(operations):
                agent_type = ["requirements", "architect", "developer", "qa", "integration"][i % 5]
                options = config.get_client_options(agent_type)
                permissions = config.get_tool_permissions(agent_type)
                thread_results.append((worker_id, i, options.max_tokens, len(permissions)))
            results_queue.put(thread_results)

        # Start multiple worker threads
        threads = []
        thread_count = 5
        operations_per_thread = 100

        start_time = time.time()

        for worker_id in range(thread_count):
            thread = threading.Thread(target=worker, args=(worker_id, operations_per_thread))
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        end_time = time.time()
        duration = end_time - start_time

        # Collect results from all threads
        all_results = []
        while not results_queue.empty():
            thread_results = results_queue.get()
            all_results.extend(thread_results)

        # Verify all operations completed successfully
        expected_total = thread_count * operations_per_thread
        assert len(all_results) == expected_total

        # Concurrent access should be efficient
        total_operations = len(all_results)
        avg_time_per_op = duration / total_operations
        assert avg_time_per_op < 0.001, f"Concurrent avg time per op: {avg_time_per_op:.5f}s"
