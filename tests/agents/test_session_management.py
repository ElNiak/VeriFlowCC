"""Tests for session state initialization, persistence, and restoration.

This module tests the SDK session management functionality including
session lifecycle, state persistence, context preservation, and
session restoration capabilities.
"""

import json
from pathlib import Path
from typing import Any

import pytest
from verifflowcc.agents.base import BaseAgent
from verifflowcc.core.sdk_config import SDKConfig

pytestmark = [pytest.mark.unit, pytest.mark.session]


class MockSessionAwareAgent(BaseAgent):
    """Mock agent with session management capabilities."""

    def __init__(self, sdk_config: SDKConfig):
        super().__init__(
            name="test_session_agent",
            agent_type="session_test",
            sdk_config=sdk_config,
        )
        self.session_data: dict[str, Any] = {}
        self.session_active = False
        self.session_id: str | None = None
        self.conversation_history: list[dict[str, Any]] = []

    async def process(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """Process input with session context."""
        if not self.session_active or self.session_id is None:
            await self.start_session()

        self.conversation_history.append(
            {"type": "input", "data": input_data, "timestamp": "2024-01-01T00:00:00Z"}
        )

        return {
            "agent": self.name,
            "session_id": self.session_id,
            "processed": True,
            "history_count": len(self.conversation_history),
        }

    async def start_session(self) -> str:
        """Initialize a new session."""
        import secrets
        import time

        self.session_id = f"session_{int(time.time())}_{secrets.randbelow(9000) + 1000}"
        self.session_active = True
        self.session_data = {
            "created_at": "2024-01-01T00:00:00Z",
            "agent_name": self.name,
            "context": {},
        }
        self.conversation_history = []
        return self.session_id

    async def end_session(self) -> None:
        """End the current session."""
        self.session_active = False
        self.session_id = None
        self.session_data = {}
        self.conversation_history = []

    async def save_session_state_to_file(self, file_path: Path) -> None:
        """Save session state to file."""
        state = {
            "session_id": self.session_id,
            "session_active": self.session_active,
            "session_data": self.session_data,
            "conversation_history": self.conversation_history,
        }

        with file_path.open("w") as f:
            json.dump(state, f, indent=2)

    async def restore_session_state(self, file_path: Path) -> None:
        """Restore session state from file."""
        if not file_path.exists():
            raise FileNotFoundError(f"Session file not found: {file_path}")

        with file_path.open() as f:
            state = json.load(f)

        self.session_id = state["session_id"]
        self.session_active = state["session_active"]
        self.session_data = state["session_data"]
        self.conversation_history = state["conversation_history"]


class TestSessionInitialization:
    """Test session initialization functionality."""

    @pytest.fixture
    def session_agent(self) -> MockSessionAwareAgent:
        """Provide mock session-aware agent."""
        config = SDKConfig(api_key="test-session-key")
        return MockSessionAwareAgent(config)

    @pytest.mark.asyncio
    async def test_session_initialization(self, session_agent: MockSessionAwareAgent) -> None:
        """Test basic session initialization."""
        assert session_agent.session_active is False
        assert session_agent.session_id is None

        session_id = await session_agent.start_session()

        assert session_agent.session_active is True
        assert session_agent.session_id == session_id
        assert session_id.startswith("session_")
        assert session_agent.session_data["agent_name"] == "test_session_agent"

    @pytest.mark.asyncio
    async def test_session_data_initialization(self, session_agent: MockSessionAwareAgent) -> None:
        """Test session data is properly initialized."""
        await session_agent.start_session()

        assert "created_at" in session_agent.session_data
        assert "agent_name" in session_agent.session_data
        assert "context" in session_agent.session_data
        assert session_agent.session_data["agent_name"] == "test_session_agent"

    @pytest.mark.asyncio
    async def test_conversation_history_initialization(
        self, session_agent: MockSessionAwareAgent
    ) -> None:
        """Test conversation history is properly initialized."""
        await session_agent.start_session()

        assert session_agent.conversation_history == []

        # Process some input to populate history
        await session_agent.process({"test": "input"})

        assert len(session_agent.conversation_history) == 1
        assert session_agent.conversation_history[0]["type"] == "input"
        assert session_agent.conversation_history[0]["data"] == {"test": "input"}

    @pytest.mark.asyncio
    async def test_automatic_session_start(self, session_agent: MockSessionAwareAgent) -> None:
        """Test automatic session initialization on first process call."""
        assert session_agent.session_active is False

        result = await session_agent.process({"auto_start": True})

        assert session_agent.session_active is True
        assert result["session_id"] is not None
        assert result["history_count"] == 1


class TestSessionPersistence:
    """Test session state persistence functionality."""

    @pytest.fixture
    def session_agent(self) -> MockSessionAwareAgent:
        """Provide mock session-aware agent."""
        config = SDKConfig(api_key="test-persistence-key")
        return MockSessionAwareAgent(config)

    @pytest.mark.asyncio
    async def test_session_state_saving(
        self, session_agent: MockSessionAwareAgent, tmp_path: Path
    ) -> None:
        """Test saving session state to file."""
        await session_agent.start_session()
        await session_agent.process({"message": "Hello world"})

        session_file = tmp_path / "session_state.json"
        await session_agent.save_session_state_to_file(session_file)

        assert session_file.exists()

        # Verify file contents
        with session_file.open() as f:
            saved_state = json.load(f)

        assert saved_state["session_active"] is True
        assert saved_state["session_id"] == session_agent.session_id
        assert len(saved_state["conversation_history"]) == 1
        assert saved_state["conversation_history"][0]["data"]["message"] == "Hello world"

    @pytest.mark.asyncio
    async def test_session_state_restoration(
        self, session_agent: MockSessionAwareAgent, tmp_path: Path
    ) -> None:
        """Test restoring session state from file."""
        # Create and save session state
        await session_agent.start_session()
        original_session_id = session_agent.session_id
        await session_agent.process({"message": "Test message"})

        session_file = tmp_path / "session_restore.json"
        await session_agent.save_session_state_to_file(session_file)

        # Clear session
        await session_agent.end_session()
        assert session_agent.session_active is False

        # Restore session
        await session_agent.restore_session_state(session_file)

        assert session_agent.session_active is True
        assert session_agent.session_id == original_session_id
        assert len(session_agent.conversation_history) == 1
        assert session_agent.conversation_history[0]["data"]["message"] == "Test message"

    @pytest.mark.asyncio
    async def test_session_restoration_file_not_found(
        self, session_agent: MockSessionAwareAgent, tmp_path: Path
    ) -> None:
        """Test handling of missing session file during restoration."""
        missing_file = tmp_path / "nonexistent.json"

        with pytest.raises(FileNotFoundError):
            await session_agent.restore_session_state(missing_file)

    @pytest.mark.asyncio
    async def test_session_persistence_with_complex_data(
        self, session_agent: MockSessionAwareAgent, tmp_path: Path
    ) -> None:
        """Test persistence of complex session data."""
        await session_agent.start_session()

        # Add complex data to session
        session_agent.session_data["context"]["user_preferences"] = {
            "language": "en",
            "theme": "dark",
            "notifications": True,
        }
        session_agent.session_data["workflow_state"] = {
            "current_stage": "requirements",
            "completed_stages": ["planning"],
            "artifacts": ["backlog.md", "requirements.json"],
        }

        # Process multiple interactions
        await session_agent.process({"action": "create_requirement"})
        await session_agent.process({"action": "validate_requirement"})

        session_file = tmp_path / "complex_session.json"
        await session_agent.save_session_state_to_file(session_file)

        # Create new agent and restore
        new_agent = MockSessionAwareAgent(SDKConfig(api_key="test-restore-key"))
        await new_agent.restore_session_state(session_file)

        # Verify complex data restoration
        assert new_agent.session_data["context"]["user_preferences"]["theme"] == "dark"
        assert new_agent.session_data["workflow_state"]["current_stage"] == "requirements"
        assert len(new_agent.conversation_history) == 2
        assert new_agent.conversation_history[1]["data"]["action"] == "validate_requirement"


class TestSessionContextPreservation:
    """Test session context preservation across operations."""

    @pytest.fixture
    def session_agent(self) -> MockSessionAwareAgent:
        """Provide mock session-aware agent."""
        config = SDKConfig(api_key="test-context-key")
        return MockSessionAwareAgent(config)

    @pytest.mark.asyncio
    async def test_context_preservation_across_calls(
        self, session_agent: MockSessionAwareAgent
    ) -> None:
        """Test context preservation across multiple process calls."""
        await session_agent.start_session()

        # Set initial context
        session_agent.session_data["context"]["user_id"] = "user123"
        session_agent.session_data["context"]["project_id"] = "proj456"

        # Process multiple calls
        result1 = await session_agent.process({"step": 1, "data": "first"})
        result2 = await session_agent.process({"step": 2, "data": "second"})
        result3 = await session_agent.process({"step": 3, "data": "third"})

        # Verify session context maintained
        assert result1["session_id"] == result2["session_id"] == result3["session_id"]
        assert result3["history_count"] == 3
        assert session_agent.session_data["context"]["user_id"] == "user123"
        assert session_agent.session_data["context"]["project_id"] == "proj456"

    @pytest.mark.asyncio
    async def test_conversation_history_accumulation(
        self, session_agent: MockSessionAwareAgent
    ) -> None:
        """Test conversation history accumulates correctly."""
        await session_agent.start_session()

        messages = [
            {"type": "greeting", "message": "Hello"},
            {"type": "question", "message": "How are you?"},
            {"type": "request", "message": "Please help me"},
        ]

        for i, message in enumerate(messages):
            result = await session_agent.process(message)
            assert result["history_count"] == i + 1

        # Verify complete history
        assert len(session_agent.conversation_history) == 3
        assert session_agent.conversation_history[0]["data"]["message"] == "Hello"
        assert session_agent.conversation_history[2]["data"]["message"] == "Please help me"

    @pytest.mark.asyncio
    async def test_context_modification_during_session(
        self, session_agent: MockSessionAwareAgent
    ) -> None:
        """Test context can be modified during active session."""
        await session_agent.start_session()

        # Initial context
        session_agent.session_data["context"]["stage"] = "requirements"
        await session_agent.process({"action": "analyze_requirements"})

        # Modify context mid-session
        session_agent.session_data["context"]["stage"] = "design"
        session_agent.session_data["context"]["artifacts"] = ["requirements.json"]
        await session_agent.process({"action": "create_design"})

        # Verify context changes persisted
        assert session_agent.session_data["context"]["stage"] == "design"
        assert "artifacts" in session_agent.session_data["context"]
        assert len(session_agent.conversation_history) == 2

    @pytest.mark.asyncio
    async def test_session_isolation_between_agents(
        self, session_agent: MockSessionAwareAgent
    ) -> None:
        """Test session isolation between different agent instances."""
        # Create second agent
        config2 = SDKConfig(api_key="test-isolation-key")
        agent2 = MockSessionAwareAgent(config2)

        # Start sessions on both agents
        session1_id = await session_agent.start_session()
        session2_id = await agent2.start_session()

        # Process different data on each agent
        result1 = await session_agent.process({"agent": "first", "data": "A"})
        result2 = await agent2.process({"agent": "second", "data": "B"})

        # Verify isolation
        assert session1_id != session2_id
        assert result1["session_id"] != result2["session_id"]
        assert session_agent.conversation_history[0]["data"]["agent"] == "first"
        assert agent2.conversation_history[0]["data"]["agent"] == "second"


class TestSessionCleanup:
    """Test session cleanup and resource management."""

    @pytest.fixture
    def session_agent(self) -> MockSessionAwareAgent:
        """Provide mock session-aware agent."""
        config = SDKConfig(api_key="test-cleanup-key")
        return MockSessionAwareAgent(config)

    @pytest.mark.asyncio
    async def test_session_cleanup_on_end(self, session_agent: MockSessionAwareAgent) -> None:
        """Test proper cleanup when session ends."""
        await session_agent.start_session()
        await session_agent.process({"test": "data"})

        # Verify session is active with data
        assert session_agent.session_active is True
        assert session_agent.session_id is not None
        assert len(session_agent.conversation_history) == 1
        assert len(session_agent.session_data) > 0

        # End session
        await session_agent.end_session()

        # Verify cleanup
        assert session_agent.session_active is False
        assert session_agent.session_id is None
        assert len(session_agent.conversation_history) == 0
        assert len(session_agent.session_data) == 0

    @pytest.mark.asyncio
    async def test_session_restart_after_cleanup(
        self, session_agent: MockSessionAwareAgent
    ) -> None:
        """Test starting new session after cleanup."""
        # First session
        session1_id = await session_agent.start_session()
        await session_agent.process({"session": 1})
        await session_agent.end_session()

        # Second session
        session2_id = await session_agent.start_session()
        await session_agent.process({"session": 2})

        # Verify new session
        assert session2_id != session1_id
        assert session_agent.session_active is True
        assert len(session_agent.conversation_history) == 1
        assert session_agent.conversation_history[0]["data"]["session"] == 2

    @pytest.mark.asyncio
    async def test_multiple_session_cleanup(self, session_agent: MockSessionAwareAgent) -> None:
        """Test cleanup behavior with multiple session start/end cycles."""
        session_ids = []

        for i in range(3):
            session_id = await session_agent.start_session()
            session_ids.append(session_id)
            await session_agent.process({"cycle": i})
            await session_agent.end_session()

        # Verify all sessions were unique and properly cleaned up
        assert len(set(session_ids)) == 3  # All unique
        assert session_agent.session_active is False
        assert session_agent.session_id is None
        assert len(session_agent.conversation_history) == 0


class TestSessionErrorHandling:
    """Test session error handling and recovery."""

    @pytest.fixture
    def session_agent(self) -> MockSessionAwareAgent:
        """Provide mock session-aware agent."""
        config = SDKConfig(api_key="test-error-key")
        return MockSessionAwareAgent(config)

    @pytest.mark.asyncio
    async def test_session_error_recovery(self, session_agent: MockSessionAwareAgent) -> None:
        """Test recovery from session errors."""
        await session_agent.start_session()

        # Simulate session error by corrupting state
        original_session_id = session_agent.session_id
        session_agent.session_id = None  # Simulate corruption

        # Process should handle error gracefully
        await session_agent.process({"recovery": "test"})

        # Session should be restored
        assert session_agent.session_active is True
        assert session_agent.session_id is not None
        assert session_agent.session_id != original_session_id  # New session

    @pytest.mark.asyncio
    async def test_corrupted_session_file_handling(
        self, session_agent: MockSessionAwareAgent, tmp_path: Path
    ) -> None:
        """Test handling of corrupted session files."""
        corrupted_file = tmp_path / "corrupted.json"

        # Create corrupted JSON file
        with corrupted_file.open("w") as f:
            f.write('{"invalid": json content}')

        with pytest.raises(json.JSONDecodeError):
            await session_agent.restore_session_state(corrupted_file)

    @pytest.mark.asyncio
    async def test_session_state_validation(
        self, session_agent: MockSessionAwareAgent, tmp_path: Path
    ) -> None:
        """Test validation of restored session state."""
        invalid_state_file = tmp_path / "invalid_state.json"

        # Create file with invalid state structure
        invalid_state = {
            "session_id": "test_session",
            # Missing required fields: session_active, session_data, conversation_history
        }

        with invalid_state_file.open("w") as f:
            json.dump(invalid_state, f)

        with pytest.raises(KeyError):
            await session_agent.restore_session_state(invalid_state_file)
