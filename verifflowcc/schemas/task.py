"""Task schema for individual task management."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from .plan import AgentType, TaskStatus


class TaskContext(BaseModel):
    """Context information for task execution."""

    user_story: str = Field(..., description="Original user story")
    requirements: list[str] = Field(..., description="Relevant requirements")
    dependencies_output: dict[str, Any] = Field(
        default_factory=dict, description="Outputs from dependency tasks"
    )
    memory: str | None = Field(None, description="Relevant memory/context from CLAUDE.md")
    additional_context: dict[str, Any] = Field(
        default_factory=dict, description="Any additional context"
    )


class TaskExecutionRequest(BaseModel):
    """Request for executing a task."""

    task_id: str = Field(..., description="Task ID to execute")
    task_name: str = Field(..., description="Task name")
    task_description: str = Field(..., description="Task description")
    agent_type: AgentType = Field(..., description="Agent type to use")
    context: TaskContext = Field(..., description="Execution context")
    timeout_seconds: int = Field(default=300, description="Execution timeout in seconds")
    retry_count: int = Field(default=0, description="Current retry count")
    max_retries: int = Field(default=3, description="Maximum retries allowed")


class TaskExecutionResult(BaseModel):
    """Result from task execution."""

    task_id: str = Field(..., description="Task ID that was executed")
    status: TaskStatus = Field(..., description="Final task status")
    output: str | None = Field(None, description="Task output")
    error: str | None = Field(None, description="Error message if failed")
    execution_time: float = Field(..., description="Execution time in seconds")
    tokens_used: int | None = Field(None, description="Tokens consumed")
    artifacts: dict[str, Any] = Field(default_factory=dict, description="Any artifacts produced")
    logs: list[str] = Field(default_factory=list, description="Execution logs")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Execution timestamp")

    def to_summary(self) -> str:
        """Generate a summary of the execution result."""
        status_emoji = {
            TaskStatus.COMPLETED: "✅",
            TaskStatus.FAILED: "❌",
            TaskStatus.BLOCKED: "🚫",
            TaskStatus.IN_PROGRESS: "🔄",
            TaskStatus.PENDING: "⏳",
        }.get(self.status, "❓")

        summary = f"{status_emoji} Task {self.task_id}: {self.status.value}"
        if self.execution_time:
            summary += f" ({self.execution_time:.2f}s)"
        if self.tokens_used:
            summary += f" [{self.tokens_used} tokens]"
        if self.error:
            summary += f"\n   Error: {self.error}"
        return summary
