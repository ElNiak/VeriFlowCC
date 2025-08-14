"""Tests for concurrent session handling and workflow isolation.

This module tests the isolation between concurrent sessions, ensuring
that multiple workflows can run simultaneously without interference,
resource conflicts, or state contamination.
"""

import asyncio
import json
import time
from pathlib import Path
from typing import Any

import pytest
from verifflowcc.core.path_config import PathConfig
from verifflowcc.core.sdk_config import SDKConfig

# Import will use fixture directly

pytestmark = [pytest.mark.integration, pytest.mark.concurrent, pytest.mark.isolation]


class IsolatedWorkflowAgent:
    """Agent designed to test workflow isolation."""

    def __init__(self, agent_id: str, workflow_id: str, sdk_config: SDKConfig):
        self.agent_id = agent_id
        self.workflow_id = workflow_id
        self.sdk_config = sdk_config
        self.session_state: dict[str, Any] = {}
        self.processing_count = 0
        self.concurrent_processes: set[str] = set()
        self.resource_access_log: list[dict[str, Any]] = []
        self.isolation_violations: list[str] = []
        self._lock = asyncio.Lock()

    async def process_workflow_step(
        self, step_data: dict[str, Any], shared_resources: dict[str, Path] | None = None
    ) -> dict[str, Any]:
        """Process a workflow step with isolation tracking."""
        process_id = f"{self.workflow_id}_{step_data.get('step_id', 'unknown')}"

        async with self._lock:
            self.concurrent_processes.add(process_id)
            self.processing_count += 1

        start_time = time.time()

        try:
            # Simulate processing with resource access
            if shared_resources:
                await self._access_shared_resources(shared_resources, process_id)

            # Process step-specific logic
            result = await self._process_step_logic(step_data, process_id)

            # Update session state
            self.session_state[f"step_{step_data.get('step_id', 'unknown')}"] = {
                "result": result,
                "timestamp": time.time(),
                "process_id": process_id,
            }

            return {
                "agent_id": self.agent_id,
                "workflow_id": self.workflow_id,
                "process_id": process_id,
                "result": result,
                "processing_time": time.time() - start_time,
                "session_state_size": len(self.session_state),
            }

        finally:
            async with self._lock:
                self.concurrent_processes.discard(process_id)

    async def _process_step_logic(
        self, step_data: dict[str, Any], process_id: str
    ) -> dict[str, Any]:
        """Process step-specific logic."""
        step_type = step_data.get("type", "generic")

        # Simulate different processing times for different step types
        processing_delays = {
            "requirements": 0.1,
            "design": 0.15,
            "coding": 0.2,
            "testing": 0.12,
            "integration": 0.08,
        }

        await asyncio.sleep(processing_delays.get(step_type, 0.05))

        return {
            "step_type": step_type,
            "workflow_specific_data": f"data_for_{self.workflow_id}",
            "processing_metadata": {
                "agent": self.agent_id,
                "concurrent_processes": len(self.concurrent_processes),
                "total_processed": self.processing_count,
            },
        }

    async def _access_shared_resources(
        self, shared_resources: dict[str, Path], process_id: str
    ) -> None:
        """Access shared resources and log access patterns."""
        for resource_name, resource_path in shared_resources.items():
            access_log = {
                "resource": resource_name,
                "path": str(resource_path),
                "process_id": process_id,
                "workflow_id": self.workflow_id,
                "timestamp": time.time(),
                "action": "read",
            }

            # Simulate resource access
            if resource_path.exists():
                try:
                    with resource_path.open() as f:
                        content = f.read()

                    # Check for isolation violations
                    if self.workflow_id not in content and content.strip():
                        self.isolation_violations.append(
                            f"Resource {resource_name} contains data from other workflows"
                        )

                    access_log["action"] = "read_success"
                    access_log["content_size"] = len(content)

                except Exception as e:
                    access_log["action"] = "read_error"
                    access_log["error"] = str(e)

            self.resource_access_log.append(access_log)

    def get_isolation_report(self) -> dict[str, Any]:
        """Generate isolation report for this agent."""
        return {
            "agent_id": self.agent_id,
            "workflow_id": self.workflow_id,
            "total_processes": self.processing_count,
            "session_state_entries": len(self.session_state),
            "resource_accesses": len(self.resource_access_log),
            "isolation_violations": len(self.isolation_violations),
            "violation_details": self.isolation_violations,
        }


class ConcurrentWorkflowManager:
    """Manager for handling concurrent workflow sessions."""

    def __init__(self, base_path_config: PathConfig):
        self.base_path_config = base_path_config
        self.active_workflows: dict[str, dict[str, Any]] = {}
        self.workflow_agents: dict[str, IsolatedWorkflowAgent] = {}
        self.resource_manager = ConcurrentResourceManager(base_path_config)
        self.session_isolation_metrics: dict[str, Any] = {}

    def create_isolated_workflow(
        self, workflow_id: str, agent_count: int = 2, isolation_level: str = "strong"
    ) -> dict[str, Any]:
        """Create an isolated workflow session."""
        workflow_path = self.base_path_config.base_dir / f"workflow_{workflow_id}"
        workflow_path.mkdir(exist_ok=True)

        # Create workflow-specific configuration
        workflow_config = SDKConfig(api_key=f"workflow_{workflow_id}_key")

        # Create agents for this workflow
        agents = []
        for i in range(agent_count):
            agent_id = f"{workflow_id}_agent_{i}"
            agent = IsolatedWorkflowAgent(agent_id, workflow_id, workflow_config)
            agents.append(agent)
            self.workflow_agents[agent_id] = agent

        # Setup isolated resources
        isolated_resources = self.resource_manager.create_workflow_resources(workflow_id)

        workflow_data = {
            "workflow_id": workflow_id,
            "created_at": time.time(),
            "agents": [agent.agent_id for agent in agents],
            "isolation_level": isolation_level,
            "resource_paths": isolated_resources,
            "workflow_path": str(workflow_path),
        }

        self.active_workflows[workflow_id] = workflow_data
        return workflow_data

    async def execute_concurrent_workflows(
        self, workflow_configs: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """Execute multiple workflows concurrently."""
        execution_start = time.time()

        # Create workflows
        workflows = []
        for config in workflow_configs:
            workflow_id: str = config["workflow_id"]
            agent_count: int = config.get("agent_count", 2)
            isolation_level: str = config.get("isolation_level", "strong")
            workflow = self.create_isolated_workflow(
                workflow_id,
                agent_count,
                isolation_level,
            )
            workflows.append(workflow)

        # Execute workflows concurrently
        async def _execute_workflow(
            workflow: dict[str, Any], steps: list[dict[str, Any]]
        ) -> dict[str, Any]:
            workflow_id = workflow["workflow_id"]
            agents = [self.workflow_agents[aid] for aid in workflow["agents"]]

            # Execute steps across agents
            step_results = []
            for step in steps:
                # Distribute steps across agents
                agent_tasks = []
                for i, agent in enumerate(agents):
                    step_data = {**step, "agent_index": i, "step_id": f"{step['id']}_{i}"}
                    shared_resources = self.resource_manager.get_workflow_resources(workflow_id)

                    task = agent.process_workflow_step(step_data, shared_resources)
                    agent_tasks.append(task)

                # Wait for all agents to complete step
                agent_results = await asyncio.gather(*agent_tasks)
                step_results.append(agent_results)

            return {
                "workflow_id": workflow_id,
                "steps_completed": len(step_results),
                "agent_results": step_results,
            }

        # Create execution tasks
        execution_tasks = []
        for _i, workflow in enumerate(workflows):
            # Define steps for each workflow
            steps = [
                {
                    "id": "req",
                    "type": "requirements",
                    "data": f"requirements_for_{workflow['workflow_id']}",
                },
                {"id": "des", "type": "design", "data": f"design_for_{workflow['workflow_id']}"},
                {"id": "cod", "type": "coding", "data": f"coding_for_{workflow['workflow_id']}"},
            ]
            execution_tasks.append(_execute_workflow(workflow, steps))

        # Execute all workflows concurrently
        workflow_results = await asyncio.gather(*execution_tasks)

        execution_time = time.time() - execution_start

        # Generate isolation metrics
        isolation_metrics = self._generate_isolation_metrics(workflows)

        return {
            "execution_time": execution_time,
            "workflows_executed": len(workflows),
            "results": workflow_results,
            "isolation_metrics": isolation_metrics,
        }

    def _generate_isolation_metrics(self, workflows: list[dict[str, Any]]) -> dict[str, Any]:
        """Generate metrics about workflow isolation."""
        metrics: dict[str, Any] = {
            "total_workflows": len(workflows),
            "total_agents": sum(len(w["agents"]) for w in workflows),
            "isolation_violations": 0,
            "resource_conflicts": 0,
            "workflow_reports": {},
        }

        for workflow in workflows:
            workflow_id = workflow["workflow_id"]
            workflow_agents = [self.workflow_agents[aid] for aid in workflow["agents"]]

            # Collect reports from agents
            agent_reports = [agent.get_isolation_report() for agent in workflow_agents]

            workflow_violations = sum(report["isolation_violations"] for report in agent_reports)
            metrics["isolation_violations"] += workflow_violations

            workflow_report: dict[str, Any] = {
                "agents": len(workflow_agents),
                "isolation_violations": workflow_violations,
                "agent_reports": agent_reports,
            }
            metrics["workflow_reports"][workflow_id] = workflow_report

        return metrics


class ConcurrentResourceManager:
    """Manager for handling concurrent resource access."""

    def __init__(self, base_path_config: PathConfig):
        self.base_path_config = base_path_config
        self.workflow_resources: dict[str, dict[str, Path]] = {}
        self.resource_locks: dict[str, asyncio.Lock] = {}
        self.access_patterns: dict[str, list[dict[str, Any]]] = {}

    def create_workflow_resources(self, workflow_id: str) -> dict[str, Path]:
        """Create isolated resources for a workflow."""
        workflow_dir = self.base_path_config.base_dir / f"resources_{workflow_id}"
        workflow_dir.mkdir(exist_ok=True)

        resources = {
            "config": workflow_dir / f"{workflow_id}_config.json",
            "state": workflow_dir / f"{workflow_id}_state.json",
            "artifacts": workflow_dir / f"{workflow_id}_artifacts.json",
            "logs": workflow_dir / f"{workflow_id}_logs.txt",
        }

        # Initialize resources with workflow-specific data
        for resource_name, resource_path in resources.items():
            initial_data = {
                "workflow_id": workflow_id,
                "resource_type": resource_name,
                "created_at": time.time(),
                "data": f"{resource_name}_data_for_{workflow_id}",
            }

            if resource_name == "logs":
                with resource_path.open("w") as f:
                    f.write(f"Log file for workflow {workflow_id}\n")
            else:
                with resource_path.open("w") as f:
                    json.dump(initial_data, f)

        self.workflow_resources[workflow_id] = resources
        return resources

    def get_workflow_resources(self, workflow_id: str) -> dict[str, Path]:
        """Get resources for a specific workflow."""
        return self.workflow_resources.get(workflow_id, {})

    async def concurrent_resource_access_test(
        self, workflows: list[str], access_pattern: str = "read_heavy"
    ) -> dict[str, Any]:
        """Test concurrent resource access patterns."""
        access_results = {
            "pattern": access_pattern,
            "workflows": workflows,
            "access_log": [],
            "conflicts_detected": 0,
            "performance_metrics": {},
        }

        async def _access_resources(workflow_id: str) -> dict[str, Any]:
            """Access resources for a specific workflow."""
            resources = self.get_workflow_resources(workflow_id)
            workflow_access_log = []

            for resource_name, resource_path in resources.items():
                start_time = time.time()

                try:
                    if access_pattern == "read_heavy":
                        # Multiple reads
                        for _i in range(5):
                            with resource_path.open() as f:
                                content = f.read()
                            workflow_access_log.append(
                                {
                                    "operation": "read",
                                    "resource": resource_name,
                                    "timestamp": time.time(),
                                    "content_size": len(content),
                                }
                            )

                    elif access_pattern == "write_heavy":
                        # Multiple writes
                        for i in range(3):
                            if resource_name != "logs":
                                with resource_path.open() as f:
                                    current_data = json.load(f)

                                current_data[f"write_{i}"] = {
                                    "timestamp": time.time(),
                                    "workflow": workflow_id,
                                }

                                with resource_path.open("w") as f:
                                    json.dump(current_data, f)
                            else:
                                with resource_path.open("a") as f:
                                    f.write(f"Write {i} from {workflow_id} at {time.time()}\n")

                            workflow_access_log.append(
                                {
                                    "operation": "write",
                                    "resource": resource_name,
                                    "timestamp": time.time(),
                                    "write_index": i,
                                }
                            )

                    elif access_pattern == "mixed":
                        # Mix of reads and writes
                        operations = ["read", "write", "read", "write", "read"]
                        for op in operations:
                            if op == "read":
                                with resource_path.open() as f:
                                    content = f.read()
                            else:
                                if resource_name != "logs":
                                    with resource_path.open() as f:
                                        current_data = json.load(f)
                                    current_data["mixed_op"] = time.time()
                                    with resource_path.open("w") as f:
                                        json.dump(current_data, f)
                                else:
                                    with resource_path.open("a") as f:
                                        f.write(f"Mixed operation from {workflow_id}\n")

                            workflow_access_log.append(
                                {
                                    "operation": op,
                                    "resource": resource_name,
                                    "timestamp": time.time(),
                                }
                            )

                except Exception as e:
                    workflow_access_log.append(
                        {
                            "operation": "error",
                            "resource": resource_name,
                            "error": str(e),
                            "timestamp": time.time(),
                        }
                    )

                access_time = time.time() - start_time
                workflow_access_log[-1]["access_time"] = access_time

            return {
                "workflow_id": workflow_id,
                "access_log": workflow_access_log,
                "total_operations": len(workflow_access_log),
            }

        # Execute concurrent access
        access_tasks = [_access_resources(wid) for wid in workflows]
        workflow_results = await asyncio.gather(*access_tasks)

        # Analyze results for conflicts
        all_accesses = []
        for result in workflow_results:
            all_accesses.extend(result["access_log"])

        # Sort by timestamp to detect potential conflicts
        all_accesses.sort(key=lambda x: x["timestamp"])

        # Simple conflict detection: overlapping write operations on same resource
        conflicts = 0
        for i in range(1, len(all_accesses)):
            curr = all_accesses[i]
            prev = all_accesses[i - 1]

            if (
                curr["resource"] == prev["resource"]
                and curr["operation"] == "write"
                and prev["operation"] == "write"
                and curr["timestamp"] - prev["timestamp"] < 0.01
            ):  # Within 10ms
                conflicts += 1

        access_results.update(
            {
                "workflow_results": workflow_results,
                "total_operations": len(all_accesses),
                "conflicts_detected": conflicts,
                "average_access_time": sum(access.get("access_time", 0) for access in all_accesses)
                / len(all_accesses)
                if all_accesses
                else 0,
            }
        )

        return access_results


class TestConcurrentSessionIsolation:
    """Test concurrent session handling and workflow isolation."""

    @pytest.fixture
    def workflow_manager(self, isolated_agilevv_dir: PathConfig) -> ConcurrentWorkflowManager:
        """Provide concurrent workflow manager."""
        return ConcurrentWorkflowManager(isolated_agilevv_dir)

    @pytest.mark.asyncio
    async def test_basic_workflow_isolation(
        self, workflow_manager: ConcurrentWorkflowManager
    ) -> None:
        """Test basic isolation between concurrent workflows."""
        workflow_configs = [
            {"workflow_id": "workflow_A", "agent_count": 2},
            {"workflow_id": "workflow_B", "agent_count": 2},
            {"workflow_id": "workflow_C", "agent_count": 2},
        ]

        result = await workflow_manager.execute_concurrent_workflows(workflow_configs)

        # Verify execution completed
        assert result["workflows_executed"] == 3
        assert result["execution_time"] < 2.0  # Should complete reasonably fast

        # Verify isolation
        isolation_metrics = result["isolation_metrics"]
        assert isolation_metrics["total_workflows"] == 3
        assert isolation_metrics["total_agents"] == 6
        assert isolation_metrics["isolation_violations"] == 0  # No violations expected

        # Check individual workflow results
        for workflow_result in result["results"]:
            assert workflow_result["steps_completed"] == 3
            assert len(workflow_result["agent_results"]) == 3  # 3 steps

            # Each step should have results from 2 agents
            for step_results in workflow_result["agent_results"]:
                assert len(step_results) == 2

    @pytest.mark.asyncio
    async def test_resource_isolation_between_workflows(
        self, workflow_manager: ConcurrentWorkflowManager
    ) -> None:
        """Test that workflows cannot access each other's resources."""
        # Create workflows with different resource requirements
        workflow_configs: list[dict[str, Any]] = [
            {"workflow_id": "isolated_A", "agent_count": 1},
            {"workflow_id": "isolated_B", "agent_count": 1},
        ]

        # Create workflows
        workflows = []
        for config in workflow_configs:
            workflow = workflow_manager.create_isolated_workflow(
                str(config["workflow_id"]), int(config["agent_count"])
            )
            workflows.append(workflow)

        # Verify resource isolation
        workflow_a_resources = workflow_manager.resource_manager.get_workflow_resources(
            "isolated_A"
        )
        workflow_b_resources = workflow_manager.resource_manager.get_workflow_resources(
            "isolated_B"
        )

        # Resources should be completely separate
        a_paths = {str(path) for path in workflow_a_resources.values()}
        b_paths = {str(path) for path in workflow_b_resources.values()}

        assert len(a_paths.intersection(b_paths)) == 0  # No shared paths

        # Verify each workflow's resources exist and contain correct data
        for resource_name, resource_path in workflow_a_resources.items():
            assert resource_path.exists()
            if resource_name != "logs":
                with resource_path.open() as f:
                    data = json.load(f)
                assert data["workflow_id"] == "isolated_A"

        for resource_name, resource_path in workflow_b_resources.items():
            assert resource_path.exists()
            if resource_name != "logs":
                with resource_path.open() as f:
                    data = json.load(f)
                assert data["workflow_id"] == "isolated_B"

    @pytest.mark.asyncio
    async def test_concurrent_resource_access_patterns(
        self, workflow_manager: ConcurrentWorkflowManager
    ) -> None:
        """Test different concurrent resource access patterns."""
        workflows = ["access_test_1", "access_test_2", "access_test_3"]

        # Create workflows and resources
        for workflow_id in workflows:
            workflow_manager.create_isolated_workflow(workflow_id, agent_count=1)

        # Test different access patterns
        access_patterns = ["read_heavy", "write_heavy", "mixed"]

        for pattern in access_patterns:
            result = await workflow_manager.resource_manager.concurrent_resource_access_test(
                workflows, pattern
            )

            # Verify no conflicts in isolated resources
            assert result["conflicts_detected"] == 0  # Isolated resources should not conflict
            assert result["total_operations"] > 0
            assert result["average_access_time"] < 0.1  # Should be fast

            # Each workflow should have completed operations
            for workflow_result in result["workflow_results"]:
                assert workflow_result["total_operations"] > 0
                assert workflow_result["workflow_id"] in workflows

    @pytest.mark.asyncio
    async def test_session_state_isolation(
        self, workflow_manager: ConcurrentWorkflowManager
    ) -> None:
        """Test that session states remain isolated between workflows."""
        workflow_configs = [
            {"workflow_id": "state_A", "agent_count": 2},
            {"workflow_id": "state_B", "agent_count": 2},
        ]

        await workflow_manager.execute_concurrent_workflows(workflow_configs)

        # Check session state isolation
        workflow_a_agents = [
            workflow_manager.workflow_agents[f"state_A_agent_{i}"] for i in range(2)
        ]
        workflow_b_agents = [
            workflow_manager.workflow_agents[f"state_B_agent_{i}"] for i in range(2)
        ]

        # Each agent should have session state for their workflow only
        for agent in workflow_a_agents:
            for _state_key, state_value in agent.session_state.items():
                assert "state_A" in str(state_value.get("process_id", ""))
                assert "state_B" not in str(state_value)

        for agent in workflow_b_agents:
            for _state_key, state_value in agent.session_state.items():
                assert "state_B" in str(state_value.get("process_id", ""))
                assert "state_A" not in str(state_value)

    @pytest.mark.asyncio
    async def test_scalability_with_many_concurrent_workflows(
        self, workflow_manager: ConcurrentWorkflowManager
    ) -> None:
        """Test scalability with many concurrent workflows."""
        # Create many workflows
        num_workflows = 8
        workflow_configs = [
            {"workflow_id": f"scale_{i}", "agent_count": 1} for i in range(num_workflows)
        ]

        start_time = time.time()
        result = await workflow_manager.execute_concurrent_workflows(workflow_configs)
        end_time = time.time()

        # Verify scalability
        assert result["workflows_executed"] == num_workflows

        # Should complete in reasonable time even with many workflows
        total_time = end_time - start_time
        assert total_time < 3.0  # Should scale reasonably

        # Average time per workflow should be reasonable
        avg_time_per_workflow = total_time / num_workflows
        assert avg_time_per_workflow < 1.0

        # Isolation should be maintained
        isolation_metrics = result["isolation_metrics"]
        assert isolation_metrics["isolation_violations"] == 0

    @pytest.mark.asyncio
    async def test_workflow_cleanup_and_resource_release(
        self, workflow_manager: ConcurrentWorkflowManager
    ) -> None:
        """Test proper cleanup and resource release after workflows complete."""
        workflow_configs = [
            {"workflow_id": "cleanup_A", "agent_count": 2},
            {"workflow_id": "cleanup_B", "agent_count": 2},
        ]

        # Execute workflows
        await workflow_manager.execute_concurrent_workflows(workflow_configs)

        # Verify resources were created
        assert len(workflow_manager.resource_manager.workflow_resources) == 2
        assert len(workflow_manager.workflow_agents) == 4

        # Simulate cleanup
        for workflow_id in ["cleanup_A", "cleanup_B"]:
            # Remove workflow agents
            agents_to_remove = [
                aid for aid in workflow_manager.workflow_agents.keys() if workflow_id in aid
            ]
            for agent_id in agents_to_remove:
                del workflow_manager.workflow_agents[agent_id]

            # Remove workflow from active list
            if workflow_id in workflow_manager.active_workflows:
                del workflow_manager.active_workflows[workflow_id]

        # Verify cleanup
        assert len(workflow_manager.workflow_agents) == 0
        assert len(workflow_manager.active_workflows) == 0

        # Resources should still exist for persistence
        assert len(workflow_manager.resource_manager.workflow_resources) == 2


class TestWorkflowErrorIsolation:
    """Test error isolation between concurrent workflows."""

    @pytest.fixture
    def workflow_manager(self, isolated_agilevv_dir: PathConfig) -> ConcurrentWorkflowManager:
        """Provide concurrent workflow manager."""
        return ConcurrentWorkflowManager(isolated_agilevv_dir)

    @pytest.mark.asyncio
    async def test_error_isolation_between_workflows(
        self, workflow_manager: ConcurrentWorkflowManager
    ) -> None:
        """Test that errors in one workflow don't affect others."""

        class FailingWorkflowAgent(IsolatedWorkflowAgent):
            """Agent that fails during processing."""

            async def _process_step_logic(
                self, step_data: dict[str, Any], process_id: str
            ) -> dict[str, Any]:
                if step_data.get("fail"):
                    raise RuntimeError(f"Simulated failure in {self.workflow_id}")
                return await super()._process_step_logic(step_data, process_id)

        # Create normal and failing workflows
        workflow_manager.create_isolated_workflow("normal_work", 2)
        workflow_manager.create_isolated_workflow("failing_work", 2)

        # Replace agents in failing workflow with failing agents
        for i in range(2):
            agent_id = f"failing_work_agent_{i}"
            failing_agent = FailingWorkflowAgent(
                agent_id, "failing_work", SDKConfig(api_key="failing_key")
            )
            workflow_manager.workflow_agents[agent_id] = failing_agent

        # Define steps - one workflow will fail
        async def _execute_normal_workflow() -> dict[str, Any]:
            agents = [workflow_manager.workflow_agents[f"normal_work_agent_{i}"] for i in range(2)]
            steps = [
                {"id": "norm_1", "type": "requirements", "data": "normal_data"},
                {"id": "norm_2", "type": "design", "data": "normal_data"},
            ]

            results = []
            for step in steps:
                agent_tasks = []
                for i, agent in enumerate(agents):
                    step_data: dict[str, Any] = {**step, "agent_index": i}
                    agent_tasks.append(agent.process_workflow_step(step_data))

                step_results = await asyncio.gather(*agent_tasks)
                results.append(step_results)

            return {"workflow": "normal", "success": True, "results": results}

        async def _execute_failing_workflow() -> dict[str, Any]:
            agents = [workflow_manager.workflow_agents[f"failing_work_agent_{i}"] for i in range(2)]
            steps: list[dict[str, Any]] = [
                {"id": "fail_1", "type": "requirements", "data": "normal_data"},
                {
                    "id": "fail_2",
                    "type": "design",
                    "data": "normal_data",
                    "fail": True,
                },  # This will fail
            ]

            results = []
            for step in steps:
                agent_tasks = []
                for i, agent in enumerate(agents):
                    step_data: dict[str, Any] = {**step, "agent_index": i}
                    agent_tasks.append(agent.process_workflow_step(step_data))

                try:
                    step_results = await asyncio.gather(*agent_tasks)
                    results.append(step_results)
                except RuntimeError as e:
                    raise RuntimeError(f"Workflow failed: {e}")

            return {"workflow": "failing", "success": True, "results": results}

        # Execute both workflows concurrently
        normal_task = asyncio.create_task(_execute_normal_workflow())
        failing_task = asyncio.create_task(_execute_failing_workflow())

        # Normal workflow should succeed
        normal_result = await normal_task
        assert normal_result["success"] is True
        assert normal_result["workflow"] == "normal"

        # Failing workflow should fail
        with pytest.raises(RuntimeError, match="Workflow failed"):
            await failing_task

        # Verify normal workflow agents are unaffected
        normal_agents = [
            workflow_manager.workflow_agents[f"normal_work_agent_{i}"] for i in range(2)
        ]
        for agent in normal_agents:
            assert len(agent.session_state) == 2  # Should have processed 2 steps
            assert len(agent.isolation_violations) == 0  # No contamination from failing workflow

    @pytest.mark.asyncio
    async def test_resource_corruption_isolation(
        self, workflow_manager: ConcurrentWorkflowManager
    ) -> None:
        """Test isolation when one workflow corrupts its resources."""

        class ResourceCorruptingAgent(IsolatedWorkflowAgent):
            """Agent that corrupts its own resources."""

            async def _access_shared_resources(
                self, shared_resources: dict[str, Path], process_id: str
            ) -> None:
                # Corrupt own resources
                for resource_name, resource_path in shared_resources.items():
                    if resource_name == "config" and "corrupt" in process_id:
                        with resource_path.open("w") as f:
                            f.write("CORRUPTED RESOURCE DATA!!!")

                await super()._access_shared_resources(shared_resources, process_id)

        # Create normal and corrupting workflows
        workflow_manager.create_isolated_workflow("clean_work", 1)
        workflow_manager.create_isolated_workflow("corrupt_work", 1)

        # Replace agent in corrupting workflow
        corrupting_agent = ResourceCorruptingAgent(
            "corrupt_work_agent_0", "corrupt_work", SDKConfig(api_key="corrupt_key")
        )
        workflow_manager.workflow_agents["corrupt_work_agent_0"] = corrupting_agent

        # Execute both workflows
        normal_agent = workflow_manager.workflow_agents["clean_work_agent_0"]

        # Execute normal workflow
        normal_resources = workflow_manager.resource_manager.get_workflow_resources("clean_work")
        normal_result = await normal_agent.process_workflow_step(
            {"id": "clean", "type": "requirements"}, normal_resources
        )

        # Execute corrupting workflow
        corrupt_resources = workflow_manager.resource_manager.get_workflow_resources("corrupt_work")
        await corrupting_agent.process_workflow_step(
            {"id": "corrupt", "type": "requirements"}, corrupt_resources
        )

        # Verify corruption isolation
        assert normal_result["result"]["step_type"] == "requirements"
        assert len(normal_agent.isolation_violations) == 0  # Normal workflow unaffected

        # Corrupting workflow should have affected only its own resources
        clean_config_path = normal_resources["config"]
        corrupt_config_path = corrupt_resources["config"]

        # Clean workflow's config should be intact
        with clean_config_path.open() as f:
            clean_data = json.load(f)
        assert clean_data["workflow_id"] == "clean_work"

        # Corrupting workflow's config should be corrupted
        with corrupt_config_path.open() as f:
            corrupt_content = f.read()
        assert "CORRUPTED" in corrupt_content


class TestPerformanceUnderConcurrency:
    """Test performance characteristics under concurrent workflow execution."""

    @pytest.fixture
    def workflow_manager(self, isolated_agilevv_dir: PathConfig) -> ConcurrentWorkflowManager:
        """Provide concurrent workflow manager."""
        return ConcurrentWorkflowManager(isolated_agilevv_dir)

    @pytest.mark.asyncio
    async def test_throughput_with_increasing_concurrency(
        self, workflow_manager: ConcurrentWorkflowManager
    ) -> None:
        """Test throughput as concurrency increases."""
        concurrency_levels = [1, 2, 4, 6]
        performance_results = {}

        for concurrency in concurrency_levels:
            workflow_configs = [
                {"workflow_id": f"perf_{concurrency}_{i}", "agent_count": 1}
                for i in range(concurrency)
            ]

            start_time = time.time()
            result = await workflow_manager.execute_concurrent_workflows(workflow_configs)
            end_time = time.time()

            total_time = end_time - start_time
            throughput = concurrency / total_time  # workflows per second

            performance_results[concurrency] = {
                "total_time": total_time,
                "throughput": throughput,
                "isolation_violations": result["isolation_metrics"]["isolation_violations"],
            }

        # Verify throughput scaling
        for concurrency in concurrency_levels:
            perf_data = performance_results[concurrency]

            # Should complete within reasonable time
            assert perf_data["total_time"] < 2.0

            # Throughput should increase with concurrency (up to a point)
            assert perf_data["throughput"] > 0.5

            # Isolation should be maintained regardless of concurrency
            assert perf_data["isolation_violations"] == 0

        # Higher concurrency should generally have higher throughput
        # (though may plateau due to resource constraints)
        throughput_1 = performance_results[1]["throughput"]
        throughput_4 = performance_results[4]["throughput"]
        assert throughput_4 >= throughput_1 * 2  # At least 2x improvement with 4x concurrency

    @pytest.mark.asyncio
    async def test_memory_isolation_under_load(
        self, workflow_manager: ConcurrentWorkflowManager
    ) -> None:
        """Test memory isolation under concurrent load."""
        # Create workflows with different memory patterns
        workflow_configs = []
        for i in range(4):
            workflow_configs.append({"workflow_id": f"memory_{i}", "agent_count": 2})

        # Execute with memory tracking
        result = await workflow_manager.execute_concurrent_workflows(workflow_configs)

        # Verify each workflow's agents maintain separate state
        for i in range(4):
            workflow_agents = [
                workflow_manager.workflow_agents[f"memory_{i}_agent_0"],
                workflow_manager.workflow_agents[f"memory_{i}_agent_1"],
            ]

            for agent in workflow_agents:
                # Each agent should have its own session state
                assert len(agent.session_state) > 0

                # Session state should be specific to this workflow
                for _state_key, state_value in agent.session_state.items():
                    assert f"memory_{i}" in str(
                        state_value.get("result", {}).get("workflow_specific_data", "")
                    )

                # No cross-contamination from other workflows
                for other_i in range(4):
                    if other_i != i:
                        workflow_data_str = str(agent.session_state)
                        assert f"memory_{other_i}" not in workflow_data_str

        # Overall isolation metrics should be clean
        assert result["isolation_metrics"]["isolation_violations"] == 0
