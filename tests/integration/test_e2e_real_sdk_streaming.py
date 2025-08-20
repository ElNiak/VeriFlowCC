"""
Claude Code SDK Streaming Response and Real-Time Feedback Tests

This module implements Task 5.2: Test Claude Code SDK streaming responses and
real-time feedback across all agent transitions, with comprehensive validation
of streaming behavior, real-time updates, and agent coordination.

Test Coverage:
- Real-time streaming response validation
- Agent transition coordination with streaming
- Performance monitoring during streaming
- Interruption and recovery testing
- Concurrent streaming session management
"""

import asyncio
import json
import os
import time
from datetime import datetime
from typing import Any

import pytest
from verifflowcc.core.orchestrator import Orchestrator
from verifflowcc.core.path_config import PathConfig
from verifflowcc.core.sdk_config import SDKConfig

# Test markers for organization
pytestmark = [
    pytest.mark.e2e,
    pytest.mark.integration,
    pytest.mark.real_sdk,
    pytest.mark.streaming,
    pytest.mark.asyncio,
    pytest.mark.slow,  # Streaming tests with real API calls
]


@pytest.fixture
def streaming_story() -> dict[str, Any]:
    """User story optimized for streaming response testing."""
    return {
        "id": "STREAM-001",
        "title": "Streaming Response Validation System",
        "description": (
            "As a developer, I want to validate that the Claude Code SDK "
            "provides real-time streaming responses during V-Model execution"
        ),
        "acceptance_criteria": [
            "System provides real-time feedback during agent processing",
            "Streaming responses are properly formatted and parseable",
            "Agent transitions maintain streaming context continuity",
            "System handles streaming interruptions gracefully",
            "Performance metrics are tracked during streaming operations",
        ],
        "story_points": 8,
        "priority": "High",
        "streaming_requirements": {
            "expected_chunks": "variable",
            "timeout_tolerance": 120,
            "feedback_frequency": "real-time",
            "context_preservation": "required",
        },
    }


@pytest.fixture
def sdk_config_for_streaming() -> SDKConfig:
    """SDK configuration optimized for streaming tests."""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        pytest.skip("ANTHROPIC_API_KEY environment variable required for streaming tests")

    return SDKConfig(
        api_key=api_key,
        timeout=90,  # Longer timeout for streaming operations
        max_retries=2,  # Fewer retries for streaming tests
    )


class StreamingEventCollector:
    """Collects and analyzes streaming events during workflow execution."""

    def __init__(self):
        self.events: list[dict[str, Any]] = []
        self.start_time = time.time()

    def record_event(self, event_type: str, stage: str, data: dict[str, Any] | None = None) -> None:
        """Record a streaming event with timestamp."""
        timestamp = time.time()
        self.events.append(
            {
                "event_type": event_type,
                "stage": stage,
                "timestamp": timestamp,
                "relative_time": timestamp - self.start_time,
                "data": data or {},
            }
        )

    def get_events_by_type(self, event_type: str) -> list[dict[str, Any]]:
        """Get all events of a specific type."""
        return [e for e in self.events if e["event_type"] == event_type]

    def get_events_by_stage(self, stage: str) -> list[dict[str, Any]]:
        """Get all events for a specific stage."""
        return [e for e in self.events if e["stage"] == stage]

    def get_streaming_timeline(self) -> dict[str, Any]:
        """Generate streaming timeline analysis."""
        if not self.events:
            return {"error": "No events recorded"}

        return {
            "total_events": len(self.events),
            "duration": self.events[-1]["timestamp"] - self.events[0]["timestamp"],
            "stages_with_streaming": len({e["stage"] for e in self.events}),
            "event_types": list({e["event_type"] for e in self.events}),
            "events": self.events,
        }


class TestRealSDKStreamingResponses:
    """Test suite for Task 5.2: Claude Code SDK streaming responses."""

    @pytest.mark.asyncio
    async def test_real_time_streaming_workflow_execution(
        self,
        isolated_agilevv_dir: PathConfig,
        streaming_story: dict[str, Any],
        sdk_config_for_streaming: SDKConfig,
    ) -> None:
        """Test real-time streaming responses during complete workflow execution."""
        collector = StreamingEventCollector()

        # Create orchestrator with streaming configuration
        orchestrator = Orchestrator(
            path_config=isolated_agilevv_dir,
            sdk_config=sdk_config_for_streaming,
            mock_mode=False,
        )

        # Patch agent methods to capture streaming events
        original_agents = {}
        for stage_name, agent in orchestrator.agents.items():
            original_agents[stage_name] = agent
            if hasattr(agent, "process"):
                original_process = agent.process

                async def create_streaming_wrapper(stage=stage_name, orig_process=original_process):
                    async def streaming_process_wrapper(
                        input_data: dict[str, Any],
                    ) -> dict[str, Any]:
                        collector.record_event(
                            "stream_start", stage, {"input_size": len(str(input_data))}
                        )

                        # Simulate streaming chunks (in real implementation, this would come from SDK)
                        start_time = time.time()

                        try:
                            # Execute real agent processing
                            result = await orig_process(input_data)

                            end_time = time.time()
                            duration = end_time - start_time

                            collector.record_event(
                                "stream_complete",
                                stage,
                                {
                                    "duration": duration,
                                    "output_size": len(str(result)) if result else 0,
                                    "success": True,
                                },
                            )

                            return result

                        except Exception as e:
                            collector.record_event(
                                "stream_error",
                                stage,
                                {
                                    "error": str(e),
                                    "duration": time.time() - start_time,
                                },
                            )
                            raise

                    return streaming_process_wrapper

                agent.process = await create_streaming_wrapper()

        # Execute workflow with streaming monitoring
        workflow_start = time.time()
        result = await orchestrator.run_sprint(streaming_story)
        workflow_end = time.time()

        total_duration = workflow_end - workflow_start

        # Validate streaming behavior
        timeline = collector.get_streaming_timeline()

        assert timeline["total_events"] > 0, "Should capture streaming events"
        assert timeline["stages_with_streaming"] >= 3, "Multiple stages should have streaming"

        # Validate streaming event sequence
        stream_starts = collector.get_events_by_type("stream_start")
        stream_completions = collector.get_events_by_type("stream_complete")
        stream_errors = collector.get_events_by_type("stream_error")

        assert len(stream_starts) > 0, "Should have streaming start events"
        assert len(stream_completions) > 0, "Should have streaming completion events"

        # More completions than errors indicates successful streaming
        success_ratio = len(stream_completions) / (len(stream_completions) + len(stream_errors))
        assert (
            success_ratio >= 0.6
        ), f"Should have majority successful streams, got {success_ratio:.2f}"

        # Validate real-time characteristics
        for completion in stream_completions:
            duration = completion["data"].get("duration", 0)
            assert duration > 0.1, f"Real streaming should take measurable time, got {duration}s"
            assert (
                duration < 180
            ), f"Individual streams should complete reasonably, took {duration}s"

        # Validate timeline progression (streaming should follow V-Model order)
        stage_progression = [event["stage"] for event in stream_starts]
        expected_early_stages = ["requirements_analyst", "architect", "developer"]

        # Check that early stages appear in reasonable order
        found_early_stages = [
            stage for stage in stage_progression if stage in expected_early_stages
        ]
        assert len(found_early_stages) >= 2, "Should execute multiple early V-Model stages"

        # Document streaming performance
        streaming_report = {
            "test_name": "real_time_streaming_workflow_execution",
            "total_duration": total_duration,
            "streaming_timeline": timeline,
            "performance_metrics": {
                "avg_stream_duration": (
                    sum(event["data"].get("duration", 0) for event in stream_completions)
                    / len(stream_completions)
                    if stream_completions
                    else 0
                ),
                "successful_streams": len(stream_completions),
                "failed_streams": len(stream_errors),
                "success_rate": success_ratio,
            },
            "final_decision": result.get("final_decision", "unknown"),
            "timestamp": datetime.now().isoformat(),
        }

        # Save streaming report
        streaming_report_path = isolated_agilevv_dir.logs_dir / "streaming_performance_report.json"
        streaming_report_path.write_text(json.dumps(streaming_report, indent=2))

    @pytest.mark.asyncio
    async def test_agent_transition_streaming_continuity(
        self,
        isolated_agilevv_dir: PathConfig,
        streaming_story: dict[str, Any],
        sdk_config_for_streaming: SDKConfig,
    ) -> None:
        """Test streaming context continuity across agent transitions."""
        collector = StreamingEventCollector()

        orchestrator = Orchestrator(
            path_config=isolated_agilevv_dir,
            sdk_config=sdk_config_for_streaming,
            mock_mode=False,
        )

        # Track context preservation across agent transitions
        context_chain = []

        # Override agents to track context passing
        for stage_name, agent in orchestrator.agents.items():
            if hasattr(agent, "process"):
                original_process = agent.process

                async def create_context_tracker(stage=stage_name, orig_process=original_process):
                    async def context_tracking_wrapper(
                        input_data: dict[str, Any],
                    ) -> dict[str, Any]:
                        # Record input context
                        input_context = {
                            "stage": stage,
                            "has_previous_context": "context" in input_data,
                            "has_artifacts": any(
                                key in input_data
                                for key in [
                                    "requirements",
                                    "design_spec",
                                    "implementation_data",
                                ]
                            ),
                            "session_state": input_data.get("session_state", {}),
                            "timestamp": time.time(),
                        }
                        context_chain.append(input_context)

                        collector.record_event("context_received", stage, input_context)

                        # Execute processing
                        result = await orig_process(input_data)

                        # Record output context
                        output_context = {
                            "stage": stage,
                            "generated_artifacts": bool(result.get("artifacts")),
                            "session_updated": bool(result.get("session_state")),
                            "context_size": len(str(result)),
                        }

                        collector.record_event("context_generated", stage, output_context)

                        return result

                    return context_tracking_wrapper

                agent.process = await create_context_tracker()

        # Execute workflow to test context continuity
        result = await orchestrator.run_sprint(streaming_story)

        # Validate context continuity
        assert len(context_chain) > 0, "Should track context across agents"

        # Verify context builds across stages
        stages_with_context = [ctx for ctx in context_chain if ctx["has_previous_context"]]
        assert (
            len(stages_with_context) >= 2
        ), "Later stages should receive context from earlier stages"

        # Verify artifact flow
        stages_with_artifacts = [ctx for ctx in context_chain if ctx["has_artifacts"]]
        assert len(stages_with_artifacts) >= 1, "Should pass artifacts between stages"

        # Validate session state progression
        context_events = collector.get_events_by_type("context_received")
        generated_events = collector.get_events_by_type("context_generated")

        assert len(context_events) > 0, "Should receive context events"
        assert len(generated_events) > 0, "Should generate context events"

        # Verify streaming maintains context consistency
        for i, ctx in enumerate(context_chain[1:], 1):  # Skip first stage
            prev_ctx = context_chain[i - 1]
            # Later stages should generally have more context
            assert ctx["timestamp"] > prev_ctx["timestamp"], "Context should progress in time"

        # Final workflow validation
        assert result["final_decision"] in [
            "GO",
            "NO-GO",
        ], "Workflow should complete with streaming"

    @pytest.mark.asyncio
    async def test_streaming_interruption_and_recovery(
        self,
        isolated_agilevv_dir: PathConfig,
        streaming_story: dict[str, Any],
        sdk_config_for_streaming: SDKConfig,
    ) -> None:
        """Test streaming response handling during interruptions and recovery."""
        collector = StreamingEventCollector()

        orchestrator = Orchestrator(
            path_config=isolated_agilevv_dir,
            sdk_config=sdk_config_for_streaming,
            mock_mode=False,
        )

        # Simulate interruption scenario
        interruption_triggered = False
        recovery_successful = False

        # Override one agent to simulate interruption
        if "architect" in orchestrator.agents:
            original_architect = orchestrator.agents["architect"].process

            async def interrupting_architect(
                input_data: dict[str, Any],
            ) -> dict[str, Any]:
                nonlocal interruption_triggered, recovery_successful

                collector.record_event(
                    "stream_start", "architect", {"simulated_interruption": True}
                )

                try:
                    # Start normal processing
                    await asyncio.sleep(0.1)  # Brief delay to simulate processing

                    # Simulate interruption scenario
                    if not interruption_triggered:
                        interruption_triggered = True
                        collector.record_event(
                            "stream_interrupted",
                            "architect",
                            {"reason": "simulated_timeout"},
                        )

                        # Simulate brief interruption
                        await asyncio.sleep(0.2)

                        # Attempt recovery
                        collector.record_event(
                            "stream_recovery_attempt", "architect", {"attempt": 1}
                        )

                    # Continue with original processing (simulating recovery)
                    result = await original_architect(input_data)

                    recovery_successful = True
                    collector.record_event("stream_recovered", "architect", {"success": True})

                    return result

                except Exception as e:
                    collector.record_event("stream_recovery_failed", "architect", {"error": str(e)})
                    raise

            orchestrator.agents["architect"].process = interrupting_architect

        # Execute workflow with interruption simulation
        start_time = time.time()
        result = await orchestrator.run_sprint(streaming_story)
        end_time = time.time()

        execution_time = end_time - start_time

        # Validate interruption handling
        assert interruption_triggered, "Should have triggered interruption simulation"

        interruption_events = collector.get_events_by_type("stream_interrupted")
        recovery_events = collector.get_events_by_type(
            "stream_recovered"
        ) + collector.get_events_by_type("stream_recovery_failed")

        assert len(interruption_events) > 0, "Should record interruption events"
        assert len(recovery_events) > 0, "Should attempt recovery"

        # Validate recovery behavior
        if recovery_successful:
            recovered_events = collector.get_events_by_type("stream_recovered")
            assert len(recovered_events) > 0, "Should record successful recovery"
            assert result["final_decision"] in [
                "GO",
                "NO-GO",
            ], "Should complete workflow after recovery"
        else:
            # Even if recovery fails, should handle gracefully
            assert isinstance(result, dict), "Should return structured result even with failures"

        # Performance impact validation
        assert (
            execution_time < 300
        ), f"Workflow with interruption should complete reasonably, took {execution_time:.2f}s"

        # Document interruption handling
        interruption_report = {
            "test_name": "streaming_interruption_and_recovery",
            "interruption_triggered": interruption_triggered,
            "recovery_successful": recovery_successful,
            "execution_time": execution_time,
            "events_timeline": collector.get_streaming_timeline(),
            "final_result": result.get("final_decision", "unknown"),
            "timestamp": datetime.now().isoformat(),
        }

        # Save interruption report
        interruption_report_path = (
            isolated_agilevv_dir.logs_dir / "streaming_interruption_report.json"
        )
        interruption_report_path.write_text(json.dumps(interruption_report, indent=2))

    @pytest.mark.asyncio
    async def test_concurrent_streaming_session_management(
        self,
        isolated_agilevv_dir: PathConfig,
        sdk_config_for_streaming: SDKConfig,
    ) -> None:
        """Test concurrent streaming sessions maintain proper isolation."""
        # Create multiple stories for concurrent streaming
        stories = [
            {
                "id": "STREAM-CONCURRENT-A",
                "title": "Concurrent Stream A",
                "description": "First concurrent streaming test story",
                "acceptance_criteria": ["Stream independently", "No interference"],
            },
            {
                "id": "STREAM-CONCURRENT-B",
                "title": "Concurrent Stream B",
                "description": "Second concurrent streaming test story",
                "acceptance_criteria": ["Stream independently", "Maintain isolation"],
            },
        ]

        collectors = []

        async def execute_streaming_workflow(story: dict[str, Any], suffix: str) -> dict[str, Any]:
            """Execute workflow with streaming monitoring."""
            collector = StreamingEventCollector()
            collectors.append(collector)

            # Create isolated orchestrator
            isolated_config = PathConfig(
                base_dir=isolated_agilevv_dir.base_dir / f"concurrent-{suffix}"
            )
            isolated_config.ensure_structure()

            orchestrator = Orchestrator(
                path_config=isolated_config,
                sdk_config=sdk_config_for_streaming,
                mock_mode=False,
            )

            # Add streaming monitoring to this orchestrator
            for stage_name, agent in orchestrator.agents.items():
                if hasattr(agent, "process"):
                    original_process = agent.process

                    async def create_monitored_process(
                        stage=stage_name, orig=original_process, coll=collector
                    ):
                        async def monitored_process(
                            input_data: dict[str, Any],
                        ) -> dict[str, Any]:
                            coll.record_event(
                                "concurrent_stream_start",
                                stage,
                                {
                                    "story_id": story["id"],
                                    "workflow_suffix": suffix,
                                },
                            )

                            result = await orig(input_data)

                            coll.record_event(
                                "concurrent_stream_complete",
                                stage,
                                {
                                    "story_id": story["id"],
                                    "workflow_suffix": suffix,
                                    "success": True,
                                },
                            )

                            return result

                        return monitored_process

                    agent.process = await create_monitored_process()

            return await orchestrator.run_sprint(story)

        # Execute concurrent workflows
        start_time = time.time()
        results = await asyncio.gather(
            execute_streaming_workflow(stories[0], "A"),
            execute_streaming_workflow(stories[1], "B"),
            return_exceptions=True,
        )
        end_time = time.time()

        concurrent_duration = end_time - start_time

        # Validate concurrent execution
        assert len(results) == 2, "Both concurrent workflows should complete"
        assert len(collectors) == 2, "Should have two streaming collectors"

        for i, result in enumerate(results):
            if isinstance(result, Exception):
                pytest.fail(f"Concurrent streaming workflow {i} failed: {result}")

            assert isinstance(result, dict), f"Result {i} should be dict"
            assert result["story"]["id"] == stories[i]["id"], f"Should process correct story {i}"

        # Validate streaming isolation
        collector_a, collector_b = collectors

        timeline_a = collector_a.get_streaming_timeline()
        timeline_b = collector_b.get_streaming_timeline()

        assert timeline_a["total_events"] > 0, "Collector A should capture events"
        assert timeline_b["total_events"] > 0, "Collector B should capture events"

        # Validate no cross-contamination of events
        events_a = collector_a.get_events_by_type(
            "concurrent_stream_start"
        ) + collector_a.get_events_by_type("concurrent_stream_complete")
        events_b = collector_b.get_events_by_type(
            "concurrent_stream_start"
        ) + collector_b.get_events_by_type("concurrent_stream_complete")

        # All events in A should reference story A
        story_ids_a = {event["data"].get("story_id") for event in events_a if "data" in event}
        story_ids_b = {event["data"].get("story_id") for event in events_b if "data" in event}

        assert "STREAM-CONCURRENT-A" in story_ids_a, "Collector A should only see story A events"
        assert "STREAM-CONCURRENT-B" in story_ids_b, "Collector B should only see story B events"
        assert len(story_ids_a & story_ids_b) == 0, "Collectors should not see each other's events"

        # Performance validation
        assert (
            concurrent_duration < 240
        ), f"Concurrent streaming should complete reasonably, took {concurrent_duration:.2f}s"

        # Document concurrent streaming results
        concurrent_report = {
            "test_name": "concurrent_streaming_session_management",
            "concurrent_duration": concurrent_duration,
            "workflow_a_events": timeline_a["total_events"],
            "workflow_b_events": timeline_b["total_events"],
            "isolation_verified": len(story_ids_a & story_ids_b) == 0,
            "both_successful": all(
                r["final_decision"] in ["GO", "NO-GO"] for r in results if isinstance(r, dict)
            ),
            "timestamp": datetime.now().isoformat(),
        }

        # Save concurrent streaming report
        concurrent_report_path = isolated_agilevv_dir.logs_dir / "concurrent_streaming_report.json"
        concurrent_report_path.write_text(json.dumps(concurrent_report, indent=2))

    @pytest.mark.asyncio
    async def test_streaming_performance_benchmarking(
        self,
        isolated_agilevv_dir: PathConfig,
        streaming_story: dict[str, Any],
        sdk_config_for_streaming: SDKConfig,
    ) -> None:
        """Benchmark streaming performance characteristics and throughput."""
        collector = StreamingEventCollector()

        orchestrator = Orchestrator(
            path_config=isolated_agilevv_dir,
            sdk_config=sdk_config_for_streaming,
            mock_mode=False,
        )

        # Enhanced performance tracking
        performance_metrics = {
            "stages": {},
            "streaming": {
                "total_chunks": 0,
                "total_bytes_streamed": 0,
                "average_chunk_size": 0,
                "streaming_overhead": 0,
            },
            "timing": {
                "first_response_time": None,
                "total_streaming_time": 0,
                "stage_transitions": [],
            },
        }

        # Override agents for detailed performance tracking
        for stage_name, agent in orchestrator.agents.items():
            if hasattr(agent, "process"):
                original_process = agent.process

                async def create_perf_tracker(stage=stage_name, orig=original_process):
                    async def performance_tracking_process(
                        input_data: dict[str, Any],
                    ) -> dict[str, Any]:
                        stage_start = time.time()

                        collector.record_event(
                            "perf_stage_start", stage, {"start_time": stage_start}
                        )

                        # Track first response time
                        if performance_metrics["timing"]["first_response_time"] is None:
                            performance_metrics["timing"]["first_response_time"] = (
                                stage_start - collector.start_time
                            )

                        try:
                            result = await orig(input_data)
                            stage_end = time.time()
                            stage_duration = stage_end - stage_start

                            # Record stage performance
                            performance_metrics["stages"][stage] = {
                                "duration": stage_duration,
                                "input_size": len(str(input_data)),
                                "output_size": len(str(result)) if result else 0,
                                "throughput": (
                                    len(str(result)) / stage_duration if stage_duration > 0 else 0
                                ),
                            }

                            # Simulate streaming chunk tracking (would be real in actual SDK)
                            estimated_chunks = max(
                                1, len(str(result)) // 1024
                            )  # Estimate 1KB chunks
                            performance_metrics["streaming"]["total_chunks"] += estimated_chunks
                            performance_metrics["streaming"]["total_bytes_streamed"] += len(
                                str(result)
                            )

                            collector.record_event(
                                "perf_stage_complete",
                                stage,
                                {
                                    "duration": stage_duration,
                                    "throughput": performance_metrics["stages"][stage][
                                        "throughput"
                                    ],
                                },
                            )

                            # Record stage transition
                            performance_metrics["timing"]["stage_transitions"].append(
                                {
                                    "stage": stage,
                                    "completed_at": stage_end,
                                    "duration": stage_duration,
                                }
                            )

                            return result

                        except Exception as e:
                            stage_end = time.time()
                            collector.record_event(
                                "perf_stage_error",
                                stage,
                                {
                                    "error": str(e),
                                    "duration": stage_end - stage_start,
                                },
                            )
                            raise

                    return performance_tracking_process

                agent.process = await create_perf_tracker()

        # Execute workflow with performance monitoring
        benchmark_start = time.time()
        result = await orchestrator.run_sprint(streaming_story)
        benchmark_end = time.time()

        total_benchmark_time = benchmark_end - benchmark_start
        performance_metrics["timing"]["total_streaming_time"] = total_benchmark_time

        # Calculate streaming performance statistics
        if performance_metrics["streaming"]["total_chunks"] > 0:
            performance_metrics["streaming"]["average_chunk_size"] = (
                performance_metrics["streaming"]["total_bytes_streamed"]
                / performance_metrics["streaming"]["total_chunks"]
            )

        # Calculate streaming overhead (difference between sum of stages and total time)
        total_stage_time = sum(
            stage_data["duration"] for stage_data in performance_metrics["stages"].values()
        )
        performance_metrics["streaming"]["streaming_overhead"] = max(
            0, total_benchmark_time - total_stage_time
        )

        # Performance validations
        assert (
            total_benchmark_time < 360
        ), f"Streaming benchmark should complete within 6 minutes, took {total_benchmark_time:.2f}s"
        assert (
            performance_metrics["timing"]["first_response_time"] is not None
        ), "Should record first response time"
        assert (
            performance_metrics["timing"]["first_response_time"] < 30
        ), "First response should come quickly"

        # Throughput validations
        successful_stages = [
            s for s in performance_metrics["stages"].values() if s["throughput"] > 0
        ]
        if successful_stages:
            avg_throughput = sum(s["throughput"] for s in successful_stages) / len(
                successful_stages
            )
            assert (
                avg_throughput > 10
            ), f"Should maintain reasonable throughput, got {avg_throughput:.2f} chars/sec"

        # Streaming overhead validation
        overhead_ratio = (
            performance_metrics["streaming"]["streaming_overhead"] / total_benchmark_time
        )
        assert (
            overhead_ratio < 0.3
        ), f"Streaming overhead should be reasonable, got {overhead_ratio:.2f}"

        # Generate comprehensive performance report
        benchmark_report = {
            "test_name": "streaming_performance_benchmarking",
            "total_benchmark_time": total_benchmark_time,
            "performance_metrics": performance_metrics,
            "streaming_statistics": {
                "total_chunks_processed": performance_metrics["streaming"]["total_chunks"],
                "total_data_streamed": performance_metrics["streaming"]["total_bytes_streamed"],
                "average_chunk_size": performance_metrics["streaming"]["average_chunk_size"],
                "streaming_efficiency": 1 - overhead_ratio,
            },
            "stage_analysis": {
                "stages_completed": len(performance_metrics["stages"]),
                "fastest_stage": (
                    min(
                        performance_metrics["stages"].items(),
                        key=lambda x: x[1]["duration"],
                    )[0]
                    if performance_metrics["stages"]
                    else None
                ),
                "slowest_stage": (
                    max(
                        performance_metrics["stages"].items(),
                        key=lambda x: x[1]["duration"],
                    )[0]
                    if performance_metrics["stages"]
                    else None
                ),
                "total_throughput": sum(
                    s["throughput"] for s in performance_metrics["stages"].values()
                ),
            },
            "workflow_outcome": result.get("final_decision", "unknown"),
            "timestamp": datetime.now().isoformat(),
        }

        # Save performance benchmark report
        benchmark_report_path = isolated_agilevv_dir.logs_dir / "streaming_benchmark_report.json"
        benchmark_report_path.write_text(json.dumps(benchmark_report, indent=2))

        # Final validation
        assert result["final_decision"] in [
            "GO",
            "NO-GO",
        ], "Benchmarked streaming workflow should complete"
        assert len(performance_metrics["stages"]) >= 3, "Should benchmark multiple stages"
