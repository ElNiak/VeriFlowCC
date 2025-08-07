"""Plan schema for V-Model workflow planning."""

from enum import Enum

from pydantic import BaseModel, Field


class TaskStatus(str, Enum):
    """Status of a task in the pipeline."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"


class AgentType(str, Enum):
    """Types of agents available for task execution."""

    PLANNER = "planner"
    DESIGN = "design"
    CODING = "coding"
    TESTING = "testing"
    VALIDATION = "validation"


class Task(BaseModel):
    """Individual task within a plan."""

    id: str = Field(..., description="Unique task identifier")
    name: str = Field(..., description="Task name")
    description: str = Field(..., description="Detailed task description")
    agent_type: AgentType = Field(..., description="Agent responsible for this task")
    status: TaskStatus = Field(default=TaskStatus.PENDING, description="Current task status")
    dependencies: list[str] = Field(
        default_factory=list, description="List of task IDs this task depends on"
    )
    context: dict | None = Field(default=None, description="Additional context for the task")
    output: str | None = Field(default=None, description="Task output when completed")
    error: str | None = Field(default=None, description="Error message if task failed")

    class Config:
        """Pydantic configuration."""

        use_enum_values = True


class Plan(BaseModel):
    """Complete plan for a feature implementation following V-Model."""

    user_story: str = Field(..., description="Original user story or feature request")
    requirements: list[str] = Field(..., description="Extracted requirements")
    design_outline: str | None = Field(None, description="High-level design description")
    tasks: list[Task] = Field(..., description="Ordered list of tasks to execute")
    acceptance_criteria: list[str] = Field(..., description="Criteria for successful completion")
    metadata: dict | None = Field(default=None, description="Additional plan metadata")

    def get_task_by_id(self, task_id: str) -> Task | None:
        """Get a task by its ID."""
        for task in self.tasks:
            if task.id == task_id:
                return task
        return None

    def get_next_task(self) -> Task | None:
        """Get the next pending task that has no pending dependencies."""
        for task in self.tasks:
            if task.status == TaskStatus.PENDING:
                # Check if all dependencies are completed
                deps_completed = all(
                    self.get_task_by_id(dep_id).status == TaskStatus.COMPLETED
                    for dep_id in task.dependencies
                    if self.get_task_by_id(dep_id)
                )
                if deps_completed:
                    return task
        return None

    def update_task_status(
        self, task_id: str, status: TaskStatus, output: str | None = None, error: str | None = None
    ) -> bool:
        """Update the status of a task."""
        task = self.get_task_by_id(task_id)
        if task:
            task.status = status
            if output:
                task.output = output
            if error:
                task.error = error
            return True
        return False

    def is_complete(self) -> bool:
        """Check if all tasks are completed."""
        return all(task.status == TaskStatus.COMPLETED for task in self.tasks)

    def get_progress(self) -> dict:
        """Get progress statistics."""
        total = len(self.tasks)
        completed = sum(1 for task in self.tasks if task.status == TaskStatus.COMPLETED)
        failed = sum(1 for task in self.tasks if task.status == TaskStatus.FAILED)
        in_progress = sum(1 for task in self.tasks if task.status == TaskStatus.IN_PROGRESS)
        pending = sum(1 for task in self.tasks if task.status == TaskStatus.PENDING)

        return {
            "total": total,
            "completed": completed,
            "failed": failed,
            "in_progress": in_progress,
            "pending": pending,
            "percentage": (completed / total * 100) if total > 0 else 0,
        }
