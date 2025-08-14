"""Tests for multi-agent session coordination.

This module tests the coordination between multiple agents within
shared sessions, including agent communication, resource sharing,
conflict resolution, and collaborative workflows.
"""

import asyncio
import json
import time
from pathlib import Path
from typing import Any

import pytest
from verifflowcc.agents.base import BaseAgent
from verifflowcc.core.path_config import PathConfig
from verifflowcc.core.sdk_config import SDKConfig

# Import will use fixture directly

pytestmark = [pytest.mark.integration, pytest.mark.multiagent, pytest.mark.coordination]


class MockCollaborativeAgent(BaseAgent):
    """Mock agent designed for collaborative multi-agent scenarios."""

    def __init__(
        self, agent_id: str, specialization: str, sdk_config: SDKConfig, mock_mode: bool = True
    ):
        super().__init__(
            name=f"{specialization}_agent_{agent_id}",
            agent_type=specialization,
            sdk_config=sdk_config,
            mock_mode=mock_mode,
        )
        self.agent_id = agent_id
        self.specialization = specialization
        self.shared_session_id: str | None = None
        self.collaboration_data: dict[str, Any] = {}
        self.message_queue: list[dict[str, Any]] = []
        self.peer_agents: set[str] = set()
        self.coordination_state = "idle"
        self.tasks_assigned: list[str] = []
        self.tasks_completed: list[str] = []

    async def process(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """Process with multi-agent coordination."""
        # Update coordination state
        self.coordination_state = "processing"

        # Check for collaboration requests
        if "collaborate_with" in input_data:
            await self._handle_collaboration_request(input_data["collaborate_with"])

        # Process assigned tasks
        for task_id in self.tasks_assigned:
            if task_id not in self.tasks_completed:
                # Simulate task processing
                task_result = await self._process_specialization(input_data)
                self.complete_task(task_id, task_result)

        # Process specialization-specific tasks
        result = await self._process_specialization(input_data)

        # Share results with peer agents if needed
        if input_data.get("share_results"):
            await self._share_results_with_peers(result)

        self.coordination_state = "completed"

        return {
            "agent": self.name,
            "agent_id": self.agent_id,
            "specialization": self.specialization,
            "result": result,
            "collaboration_data": self.collaboration_data,
            "coordination_state": self.coordination_state,
            "tasks_completed": len(self.tasks_completed),
        }

    async def _process_specialization(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """Process based on agent specialization."""
        if self.specialization == "requirements":
            return {
                "requirements_analyzed": 5,
                "quality_score": 88,
                "stakeholder_feedback": "positive",
            }
        elif self.specialization == "architecture":
            return {
                "components_designed": 3,
                "interfaces_defined": 7,
                "design_patterns": ["factory", "observer", "strategy"],
            }
        elif self.specialization == "testing":
            return {
                "test_cases_created": 25,
                "coverage_target": 90,
                "test_types": ["unit", "integration", "e2e"],
            }
        elif self.specialization == "security":
            return {
                "vulnerabilities_assessed": 12,
                "security_controls": ["authentication", "authorization", "encryption"],
                "risk_level": "medium",
            }
        else:
            return {"processed": True}

    async def _handle_collaboration_request(self, peer_agent_ids: list[str]) -> None:
        """Handle collaboration request from peer agents."""
        for peer_id in peer_agent_ids:
            self.peer_agents.add(peer_id)
            self.collaboration_data[f"collaboration_with_{peer_id}"] = {
                "status": "active",
                "started_at": time.time(),
                "shared_tasks": [],
            }

    async def _share_results_with_peers(self, result: dict[str, Any]) -> None:
        """Share processing results with peer agents."""
        for peer_id in self.peer_agents:
            message = {
                "from_agent": self.agent_id,
                "to_agent": peer_id,
                "message_type": "result_sharing",
                "timestamp": time.time(),
                "data": result,
            }
            # In real implementation, this would use a message broker
            self.message_queue.append(message)

    def join_shared_session(self, session_id: str) -> None:
        """Join a shared session for multi-agent coordination."""
        self.shared_session_id = session_id
        self.coordination_state = "in_session"

    def leave_shared_session(self) -> None:
        """Leave the shared session."""
        self.shared_session_id = None
        self.coordination_state = "idle"
        self.collaboration_data.clear()
        self.peer_agents.clear()

    def assign_task(self, task_id: str, task_description: str) -> None:
        """Assign a task to this agent."""
        self.tasks_assigned.append(task_id)
        self.collaboration_data[f"task_{task_id}"] = {
            "description": task_description,
            "status": "assigned",
            "assigned_at": time.time(),
        }

    def complete_task(self, task_id: str, result: dict[str, Any]) -> None:
        """Mark a task as completed."""
        if task_id in self.tasks_assigned and task_id not in self.tasks_completed:
            self.tasks_completed.append(task_id)
            if f"task_{task_id}" in self.collaboration_data:
                self.collaboration_data[f"task_{task_id}"].update(
                    {"status": "completed", "completed_at": time.time(), "result": result}
                )


class MockSessionCoordinator:
    """Mock coordinator for managing multi-agent sessions."""

    def __init__(self, sdk_config: SDKConfig):
        self.sdk_config = sdk_config
        self.active_sessions: dict[str, dict[str, Any]] = {}
        self.agent_registry: dict[str, MockCollaborativeAgent] = {}
        self.message_bus: list[dict[str, Any]] = []
        self.coordination_strategies = {
            "parallel": self._coordinate_parallel,
            "sequential": self._coordinate_sequential,
            "collaborative": self._coordinate_collaborative,
        }

    def register_agent(self, agent: MockCollaborativeAgent) -> None:
        """Register an agent with the coordinator."""
        self.agent_registry[agent.agent_id] = agent

    def create_shared_session(
        self, session_id: str, participant_agents: list[str]
    ) -> dict[str, Any]:
        """Create a shared session for multi-agent coordination."""
        session_data = {
            "session_id": session_id,
            "participants": participant_agents,
            "created_at": time.time(),
            "status": "active",
            "shared_context": {},
            "coordination_log": [],
        }

        self.active_sessions[session_id] = session_data

        # Add agents to session
        for agent_id in participant_agents:
            if agent_id in self.agent_registry:
                self.agent_registry[agent_id].join_shared_session(session_id)

        return session_data

    async def coordinate_agents(
        self, session_id: str, coordination_strategy: str, tasks: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """Coordinate agents within a session using specified strategy."""
        if session_id not in self.active_sessions:
            raise ValueError(f"Session {session_id} not found")

        if coordination_strategy not in self.coordination_strategies:
            raise ValueError(f"Unknown coordination strategy: {coordination_strategy}")

        session = self.active_sessions[session_id]
        strategy_func = self.coordination_strategies[coordination_strategy]

        # Execute coordination strategy
        result = await strategy_func(session, tasks)

        # Update session with coordination results
        session["coordination_log"].append(
            {
                "timestamp": time.time(),
                "strategy": coordination_strategy,
                "tasks": len(tasks),
                "result": result,
            }
        )

        return result

    async def _coordinate_parallel(
        self, session: dict[str, Any], tasks: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """Coordinate agents to work in parallel."""
        participant_agents = [
            self.agent_registry[agent_id]
            for agent_id in session["participants"]
            if agent_id in self.agent_registry
        ]

        # Assign tasks to agents
        for i, task in enumerate(tasks):
            agent = participant_agents[i % len(participant_agents)]
            agent.assign_task(task["id"], task["description"])

        # Execute tasks in parallel
        agent_tasks = []
        for agent in participant_agents:
            agent_input = {
                "coordination_mode": "parallel",
                "session_id": session["session_id"],
                "share_results": True,
            }
            agent_tasks.append(agent.process(agent_input))

        results = await asyncio.gather(*agent_tasks)

        return {
            "coordination_type": "parallel",
            "agents_coordinated": len(participant_agents),
            "tasks_processed": len(tasks),
            "results": results,
            "execution_time": time.time(),
        }

    async def _coordinate_sequential(
        self, session: dict[str, Any], tasks: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """Coordinate agents to work sequentially."""
        participant_agents = [
            self.agent_registry[agent_id]
            for agent_id in session["participants"]
            if agent_id in self.agent_registry
        ]
        results: list[Any] = []

        # Process tasks sequentially
        for i, task in enumerate(tasks):
            agent = participant_agents[i % len(participant_agents)]
            agent.assign_task(task["id"], task["description"])

            agent_input = {
                "coordination_mode": "sequential",
                "session_id": session["session_id"],
                "task_order": i,
                "previous_results": results[-1] if results else None,
            }

            result = await agent.process(agent_input)
            results.append(result)

        return {
            "coordination_type": "sequential",
            "agents_coordinated": len(participant_agents),
            "tasks_processed": len(tasks),
            "results": results,
            "execution_time": time.time(),
        }

    async def _coordinate_collaborative(
        self, session: dict[str, Any], tasks: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """Coordinate agents to work collaboratively."""
        participant_agents = [
            self.agent_registry[agent_id]
            for agent_id in session["participants"]
            if agent_id in self.agent_registry
        ]

        # Setup collaboration between agents
        agent_ids = [agent.agent_id for agent in participant_agents]
        for agent in participant_agents:
            peer_ids = [aid for aid in agent_ids if aid != agent.agent_id]
            await agent._handle_collaboration_request(peer_ids)

        # Assign overlapping tasks for collaboration
        for task in tasks:
            for agent in participant_agents:
                agent.assign_task(task["id"], task["description"])

        # Execute collaborative processing
        agent_tasks = []
        for agent in participant_agents:
            agent_input = {
                "coordination_mode": "collaborative",
                "session_id": session["session_id"],
                "collaborate_with": peer_ids,
                "share_results": True,
            }
            agent_tasks.append(agent.process(agent_input))

        results = await asyncio.gather(*agent_tasks)

        return {
            "coordination_type": "collaborative",
            "agents_coordinated": len(participant_agents),
            "collaboration_pairs": len(participant_agents) * (len(participant_agents) - 1),
            "tasks_processed": len(tasks),
            "results": results,
            "execution_time": time.time(),
        }

    def end_session(self, session_id: str) -> dict[str, Any]:
        """End a shared session and cleanup."""
        if session_id not in self.active_sessions:
            return {"error": "Session not found"}

        session = self.active_sessions[session_id]

        # Remove agents from session
        for agent_id in session["participants"]:
            if agent_id in self.agent_registry:
                self.agent_registry[agent_id].leave_shared_session()

        # Archive session data
        session["status"] = "ended"
        session["ended_at"] = time.time()

        archived_session = self.active_sessions.pop(session_id)

        return {
            "session_ended": True,
            "session_id": session_id,
            "duration": archived_session["ended_at"] - archived_session["created_at"],
            "coordination_events": len(archived_session["coordination_log"]),
        }


class TestMultiAgentCoordination:
    """Test multi-agent session coordination."""

    @pytest.fixture
    def session_coordinator(self) -> MockSessionCoordinator:
        """Provide mock session coordinator."""
        config = SDKConfig(api_key="test-coordination-key")
        return MockSessionCoordinator(config)

    @pytest.fixture
    def collaborative_agents(
        self, session_coordinator: MockSessionCoordinator
    ) -> list[MockCollaborativeAgent]:
        """Provide collaborative agents."""
        agents = [
            MockCollaborativeAgent("agent_001", "requirements", session_coordinator.sdk_config),
            MockCollaborativeAgent("agent_002", "architecture", session_coordinator.sdk_config),
            MockCollaborativeAgent("agent_003", "testing", session_coordinator.sdk_config),
            MockCollaborativeAgent("agent_004", "security", session_coordinator.sdk_config),
        ]

        for agent in agents:
            session_coordinator.register_agent(agent)

        return agents

    @pytest.mark.asyncio
    async def test_parallel_agent_coordination(
        self,
        session_coordinator: MockSessionCoordinator,
        collaborative_agents: list[MockCollaborativeAgent],
    ) -> None:
        """Test parallel coordination of multiple agents."""
        session_id = "parallel_session_001"
        agent_ids = [agent.agent_id for agent in collaborative_agents]

        # Create shared session
        session = session_coordinator.create_shared_session(session_id, agent_ids)
        assert session["session_id"] == session_id
        assert len(session["participants"]) == 4

        # Define parallel tasks
        tasks = [
            {"id": "task_001", "description": "Analyze user requirements"},
            {"id": "task_002", "description": "Design system architecture"},
            {"id": "task_003", "description": "Create test strategy"},
            {"id": "task_004", "description": "Security assessment"},
        ]

        # Coordinate agents in parallel
        start_time = time.time()
        result = await session_coordinator.coordinate_agents(session_id, "parallel", tasks)
        end_time = time.time()

        # Verify coordination results
        assert result["coordination_type"] == "parallel"
        assert result["agents_coordinated"] == 4
        assert result["tasks_processed"] == 4
        assert len(result["results"]) == 4

        # Verify each agent processed their assigned tasks
        for _i, agent_result in enumerate(result["results"]):
            assert agent_result["coordination_state"] == "completed"
            assert agent_result["tasks_completed"] == 1  # Each agent got one task

        # Verify parallel execution was faster than sequential would be
        execution_time = end_time - start_time
        assert execution_time < 0.5  # Should be much faster than sequential

    @pytest.mark.asyncio
    async def test_sequential_agent_coordination(
        self,
        session_coordinator: MockSessionCoordinator,
        collaborative_agents: list[MockCollaborativeAgent],
    ) -> None:
        """Test sequential coordination of multiple agents."""
        session_id = "sequential_session_001"
        agent_ids = [agent.agent_id for agent in collaborative_agents]

        session_coordinator.create_shared_session(session_id, agent_ids)

        tasks = [
            {"id": "seq_001", "description": "Requirements gathering"},
            {"id": "seq_002", "description": "Architecture design"},
            {"id": "seq_003", "description": "Test planning"},
            {"id": "seq_004", "description": "Security review"},
        ]

        result = await session_coordinator.coordinate_agents(session_id, "sequential", tasks)

        # Verify sequential execution
        assert result["coordination_type"] == "sequential"
        assert len(result["results"]) == 4

        # Verify results build on each other (sequential characteristic)
        for _i, agent_result in enumerate(result["results"]):
            assert "coordination_mode" in str(agent_result)  # Should have coordination metadata

        # Check session coordination log
        session = session_coordinator.active_sessions[session_id]
        assert len(session["coordination_log"]) == 1
        assert session["coordination_log"][0]["strategy"] == "sequential"

    @pytest.mark.asyncio
    async def test_collaborative_agent_coordination(
        self,
        session_coordinator: MockSessionCoordinator,
        collaborative_agents: list[MockCollaborativeAgent],
    ) -> None:
        """Test collaborative coordination where agents work together."""
        session_id = "collaborative_session_001"
        agent_ids = [agent.agent_id for agent in collaborative_agents]

        session_coordinator.create_shared_session(session_id, agent_ids)

        # Collaborative tasks that benefit from multiple perspectives
        tasks = [
            {"id": "collab_001", "description": "Cross-functional system design"},
            {"id": "collab_002", "description": "Integrated security architecture"},
        ]

        result = await session_coordinator.coordinate_agents(session_id, "collaborative", tasks)

        # Verify collaborative execution
        assert result["coordination_type"] == "collaborative"
        assert result["collaboration_pairs"] == 12  # 4 agents * 3 peers each
        assert len(result["results"]) == 4

        # Verify agents established collaboration
        for agent in collaborative_agents:
            assert len(agent.peer_agents) == 3  # Each agent should have 3 peers
            assert len(agent.collaboration_data) > 0  # Should have collaboration metadata

        # Verify task sharing
        for agent in collaborative_agents:
            assert len(agent.tasks_assigned) == 2  # Each task assigned to all agents

    @pytest.mark.asyncio
    async def test_agent_communication_during_coordination(
        self,
        session_coordinator: MockSessionCoordinator,
        collaborative_agents: list[MockCollaborativeAgent],
    ) -> None:
        """Test inter-agent communication during coordination."""
        session_id = "communication_session_001"
        agent_ids = [
            agent.agent_id for agent in collaborative_agents[:2]
        ]  # Use just 2 agents for clarity

        session_coordinator.create_shared_session(session_id, agent_ids)

        tasks = [{"id": "comm_001", "description": "Communication test task"}]

        # Execute with result sharing enabled
        await session_coordinator.coordinate_agents(session_id, "collaborative", tasks)

        # Verify communication occurred
        messages_sent = 0
        for agent in collaborative_agents[:2]:
            messages_sent += len(agent.message_queue)

            # Each agent should have messages in queue for peer communication
            if len(agent.message_queue) > 0:
                message = agent.message_queue[0]
                assert message["message_type"] == "result_sharing"
                assert "timestamp" in message
                assert "data" in message

        assert messages_sent > 0  # Some inter-agent communication should occur

    @pytest.mark.asyncio
    async def test_session_lifecycle_management(
        self,
        session_coordinator: MockSessionCoordinator,
        collaborative_agents: list[MockCollaborativeAgent],
    ) -> None:
        """Test complete session lifecycle management."""
        session_id = "lifecycle_session_001"
        agent_ids = [agent.agent_id for agent in collaborative_agents]

        # Create session
        session_coordinator.create_shared_session(session_id, agent_ids)
        assert session_id in session_coordinator.active_sessions

        # Verify agents joined session
        for agent in collaborative_agents:
            assert agent.shared_session_id == session_id
            assert agent.coordination_state == "in_session"

        # Execute some coordination
        tasks = [{"id": "lifecycle_001", "description": "Lifecycle test"}]
        await session_coordinator.coordinate_agents(session_id, "parallel", tasks)

        # End session
        end_result = session_coordinator.end_session(session_id)

        # Verify session cleanup
        assert end_result["session_ended"] is True
        assert session_id not in session_coordinator.active_sessions
        assert "duration" in end_result

        # Verify agents left session
        for agent in collaborative_agents:
            assert agent.shared_session_id is None
            assert agent.coordination_state == "idle"
            assert len(agent.collaboration_data) == 0
            assert len(agent.peer_agents) == 0


class TestAgentResourceSharing:
    """Test resource sharing between agents in coordinated sessions."""

    @pytest.fixture
    def session_coordinator(self) -> MockSessionCoordinator:
        """Provide mock session coordinator."""
        config = SDKConfig(api_key="test-resource-key")
        return MockSessionCoordinator(config)

    @pytest.mark.asyncio
    async def test_shared_resource_access(
        self, session_coordinator: MockSessionCoordinator, isolated_agilevv_dir: PathConfig
    ) -> None:
        """Test shared resource access between coordinated agents."""
        # Create agents with shared resource needs
        agents = [
            MockCollaborativeAgent("resource_001", "requirements", session_coordinator.sdk_config),
            MockCollaborativeAgent("resource_002", "architecture", session_coordinator.sdk_config),
        ]

        for agent in agents:
            session_coordinator.register_agent(agent)

        session_id = "resource_session_001"
        session_coordinator.create_shared_session(session_id, [agent.agent_id for agent in agents])

        # Create shared resource
        shared_resource_file = isolated_agilevv_dir.base_dir / "shared_resource.json"
        shared_data = {
            "project_context": {"name": "test_project", "version": "1.0"},
            "shared_artifacts": ["requirements.md", "architecture.puml"],
        }

        with shared_resource_file.open("w") as f:
            json.dump(shared_data, f)

        # Both agents process with access to shared resource
        tasks = [{"id": "resource_task", "description": "Use shared resources"}]
        result = await session_coordinator.coordinate_agents(session_id, "parallel", tasks)

        # Verify both agents can access shared resource
        assert result["agents_coordinated"] == 2
        for agent_result in result["results"]:
            assert agent_result["coordination_state"] == "completed"

        # Verify resource file still exists and unchanged
        assert shared_resource_file.exists()
        with shared_resource_file.open() as f:
            final_data = json.load(f)
        assert final_data == shared_data

    @pytest.mark.asyncio
    async def test_resource_conflict_resolution(
        self, session_coordinator: MockSessionCoordinator, isolated_agilevv_dir: PathConfig
    ) -> None:
        """Test resolution of resource conflicts between agents."""

        class ConflictingAgent(MockCollaborativeAgent):
            """Agent that simulates resource conflicts."""

            def __init__(self, agent_id: str, resource_file: Path, sdk_config: SDKConfig):
                super().__init__(agent_id, "conflicting", sdk_config)
                self.resource_file = resource_file
                self.write_attempts = 0
                self.successful_writes = 0

            async def process(self, input_data: dict[str, Any]) -> dict[str, Any]:
                """Process with potential resource conflict."""
                self.write_attempts += 1

                # Simulate resource modification
                try:
                    # Read current resource
                    current_data = {}
                    if self.resource_file.exists():
                        with self.resource_file.open() as f:
                            current_data = json.load(f)

                    # Add agent-specific data
                    current_data[f"agent_{self.agent_id}_data"] = {
                        "modification_time": time.time(),
                        "agent_id": self.agent_id,
                    }

                    # Small delay to increase chance of conflict
                    await asyncio.sleep(0.01)

                    # Write back to resource
                    with self.resource_file.open("w") as f:
                        json.dump(current_data, f)

                    self.successful_writes += 1

                    return await super().process(input_data)

                except Exception as e:
                    return {
                        "agent": self.name,
                        "error": str(e),
                        "write_attempts": self.write_attempts,
                        "successful_writes": self.successful_writes,
                    }

        # Create conflicting agents
        resource_file = isolated_agilevv_dir.base_dir / "conflicted_resource.json"
        agents = [
            ConflictingAgent("conflict_001", resource_file, session_coordinator.sdk_config),
            ConflictingAgent("conflict_002", resource_file, session_coordinator.sdk_config),
            ConflictingAgent("conflict_003", resource_file, session_coordinator.sdk_config),
        ]

        for agent in agents:
            session_coordinator.register_agent(agent)

        session_id = "conflict_session_001"
        session_coordinator.create_shared_session(session_id, [agent.agent_id for agent in agents])

        # Execute conflicting operations
        tasks = [{"id": "conflict_task", "description": "Modify shared resource"}]
        await session_coordinator.coordinate_agents(session_id, "parallel", tasks)

        # Verify conflict resolution
        assert resource_file.exists()

        with resource_file.open() as f:
            final_data = json.load(f)

        # All agents should have contributed data (conflict resolved)
        agent_data_count = sum(1 for key in final_data.keys() if key.startswith("agent_"))
        assert agent_data_count == 3  # All agents wrote successfully

        # Verify all agents attempted and succeeded
        total_attempts = sum(agent.write_attempts for agent in agents)
        total_successes = sum(agent.successful_writes for agent in agents)

        assert total_attempts == 3  # Each agent made one attempt
        assert total_successes == 3  # All attempts succeeded (no conflicts)


class TestConcurrentSessionHandling:
    """Test concurrent handling of multiple agent sessions."""

    @pytest.fixture
    def session_coordinator(self) -> MockSessionCoordinator:
        """Provide mock session coordinator."""
        config = SDKConfig(api_key="test-concurrent-key")
        return MockSessionCoordinator(config)

    @pytest.mark.asyncio
    async def test_multiple_concurrent_sessions(
        self, session_coordinator: MockSessionCoordinator
    ) -> None:
        """Test handling of multiple concurrent coordination sessions."""
        # Create agents for multiple sessions
        all_agents = []
        for session_num in range(3):
            session_agents = [
                MockCollaborativeAgent(
                    f"s{session_num}_agent_{i}", f"type_{i}", session_coordinator.sdk_config
                )
                for i in range(2)
            ]
            all_agents.extend(session_agents)

            for agent in session_agents:
                session_coordinator.register_agent(agent)

        # Create multiple concurrent sessions
        sessions = []
        for session_num in range(3):
            session_id = f"concurrent_session_{session_num}"
            agent_ids = [f"s{session_num}_agent_{i}" for i in range(2)]
            session_coordinator.create_shared_session(session_id, agent_ids)
            sessions.append((session_id, agent_ids))

        # Execute concurrent coordination
        async def _coordinate_session(session_id: str) -> dict[str, Any]:
            tasks = [{"id": f"task_{session_id}", "description": f"Task for {session_id}"}]
            return await session_coordinator.coordinate_agents(session_id, "parallel", tasks)

        # Run all sessions concurrently
        coordination_tasks = [_coordinate_session(session_id) for session_id, _ in sessions]
        results = await asyncio.gather(*coordination_tasks)

        # Verify all sessions executed successfully
        assert len(results) == 3
        for _i, result in enumerate(results):
            assert result["coordination_type"] == "parallel"
            assert result["agents_coordinated"] == 2
            assert result["tasks_processed"] == 1

        # Verify session isolation
        for session_id, agent_ids in sessions:
            for agent_id in agent_ids:
                agent = session_coordinator.agent_registry[agent_id]
                assert agent.shared_session_id == session_id
                # Agent should only collaborate with peers from same session
                assert len(agent.peer_agents) == 1

    @pytest.mark.asyncio
    async def test_session_scalability(self, session_coordinator: MockSessionCoordinator) -> None:
        """Test coordination scalability with many agents."""
        # Create large number of agents
        num_agents = 10
        agents = [
            MockCollaborativeAgent(
                f"scale_agent_{i}", f"type_{i % 5}", session_coordinator.sdk_config
            )
            for i in range(num_agents)
        ]

        for agent in agents:
            session_coordinator.register_agent(agent)

        session_id = "scalability_session"
        agent_ids = [agent.agent_id for agent in agents]
        session_coordinator.create_shared_session(session_id, agent_ids)

        # Execute with many tasks
        tasks = [
            {"id": f"scale_task_{i}", "description": f"Scalability test task {i}"}
            for i in range(20)  # More tasks than agents
        ]

        start_time = time.time()
        result = await session_coordinator.coordinate_agents(session_id, "parallel", tasks)
        end_time = time.time()

        # Verify scalability
        assert result["agents_coordinated"] == num_agents
        assert result["tasks_processed"] == 20

        # Should complete in reasonable time even with many agents/tasks
        execution_time = end_time - start_time
        assert execution_time < 1.0  # Should scale well

        # Verify task distribution
        total_tasks_completed = sum(len(agent.tasks_completed) for agent in agents)
        assert total_tasks_completed == 20  # All tasks distributed and completed

    @pytest.mark.asyncio
    async def test_session_error_isolation(
        self, session_coordinator: MockSessionCoordinator
    ) -> None:
        """Test that errors in one session don't affect others."""

        class FailingAgent(MockCollaborativeAgent):
            """Agent that fails during processing."""

            async def process(self, input_data: dict[str, Any]) -> dict[str, Any]:
                if input_data.get("should_fail"):
                    raise RuntimeError("Simulated agent failure")
                return await super().process(input_data)

        # Create normal and failing agents
        normal_agents = [
            MockCollaborativeAgent("normal_001", "normal", session_coordinator.sdk_config),
            MockCollaborativeAgent("normal_002", "normal", session_coordinator.sdk_config),
        ]

        failing_agents = [
            FailingAgent("failing_001", "failing", session_coordinator.sdk_config),
            FailingAgent("failing_002", "failing", session_coordinator.sdk_config),
        ]

        all_agents = normal_agents + failing_agents
        for agent in all_agents:
            session_coordinator.register_agent(agent)

        # Create separate sessions
        normal_session_id = "normal_session"
        failing_session_id = "failing_session"

        session_coordinator.create_shared_session(
            normal_session_id, [agent.agent_id for agent in normal_agents]
        )
        session_coordinator.create_shared_session(
            failing_session_id, [agent.agent_id for agent in failing_agents]
        )

        # Execute sessions concurrently - one will fail
        async def _normal_coordination() -> dict[str, Any]:
            tasks = [{"id": "normal_task", "description": "Normal task"}]
            return await session_coordinator.coordinate_agents(normal_session_id, "parallel", tasks)

        async def _failing_coordination() -> dict[str, Any]:
            tasks = [{"id": "failing_task", "description": "Failing task", "should_fail": True}]
            return await session_coordinator.coordinate_agents(
                failing_session_id, "parallel", tasks
            )

        # Run both sessions
        normal_task = asyncio.create_task(_normal_coordination())
        failing_task = asyncio.create_task(_failing_coordination())

        # Normal session should succeed
        normal_result = await normal_task
        assert normal_result["coordination_type"] == "parallel"
        assert normal_result["agents_coordinated"] == 2

        # Failing session should fail but not affect normal session
        with pytest.raises(RuntimeError):
            await failing_task

        # Verify normal session is still operational
        assert normal_session_id in session_coordinator.active_sessions
        for agent in normal_agents:
            assert agent.coordination_state == "completed"
            assert agent.shared_session_id == normal_session_id
