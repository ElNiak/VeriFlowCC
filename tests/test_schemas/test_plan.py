"""Tests for Plan schema and related models."""

from verifflowcc.schemas.plan import AgentType, Plan, Task, TaskStatus


def test_task_creation():
    """Test Task model creation."""
    task = Task(
        id="task-001",
        name="Create database schema",
        description="Design and implement the database schema",
        agent_type=AgentType.DESIGN,
        status=TaskStatus.PENDING,
        dependencies=["task-000"],
    )

    assert task.id == "task-001"
    assert task.name == "Create database schema"
    assert task.agent_type == "design"
    assert task.status == "pending"
    assert task.dependencies == ["task-000"]
    assert task.output is None
    assert task.error is None


def test_plan_creation():
    """Test Plan model creation."""
    tasks = [
        Task(
            id="task-001",
            name="Design API",
            description="Design RESTful API endpoints",
            agent_type=AgentType.DESIGN,
        ),
        Task(
            id="task-002",
            name="Implement API",
            description="Code the API endpoints",
            agent_type=AgentType.CODING,
            dependencies=["task-001"],
        ),
    ]

    plan = Plan(
        user_story="As a user, I want to access the API",
        requirements=["RESTful endpoints", "JSON responses"],
        tasks=tasks,
        acceptance_criteria=["All endpoints return valid JSON", "Status codes are correct"],
    )

    assert plan.user_story == "As a user, I want to access the API"
    assert len(plan.requirements) == 2
    assert len(plan.tasks) == 2
    assert len(plan.acceptance_criteria) == 2


def test_get_task_by_id():
    """Test getting a task by ID."""
    tasks = [
        Task(id="task-001", name="Task 1", description="First task", agent_type=AgentType.DESIGN),
        Task(id="task-002", name="Task 2", description="Second task", agent_type=AgentType.CODING),
    ]

    plan = Plan(
        user_story="Test story",
        requirements=["Req 1"],
        tasks=tasks,
        acceptance_criteria=["AC 1"],
    )

    task = plan.get_task_by_id("task-001")
    assert task is not None
    assert task.name == "Task 1"

    task = plan.get_task_by_id("task-999")
    assert task is None


def test_get_next_task():
    """Test getting the next pending task with resolved dependencies."""
    tasks = [
        Task(
            id="task-001",
            name="Task 1",
            description="First task",
            agent_type=AgentType.DESIGN,
            status=TaskStatus.COMPLETED,
        ),
        Task(
            id="task-002",
            name="Task 2",
            description="Second task",
            agent_type=AgentType.CODING,
            status=TaskStatus.PENDING,
            dependencies=["task-001"],
        ),
        Task(
            id="task-003",
            name="Task 3",
            description="Third task",
            agent_type=AgentType.TESTING,
            status=TaskStatus.PENDING,
            dependencies=["task-002"],
        ),
    ]

    plan = Plan(
        user_story="Test story",
        requirements=["Req 1"],
        tasks=tasks,
        acceptance_criteria=["AC 1"],
    )

    # Task 2 should be next (task 1 is completed, task 2's dependencies are met)
    next_task = plan.get_next_task()
    assert next_task is not None
    assert next_task.id == "task-002"


def test_update_task_status():
    """Test updating task status."""
    tasks = [
        Task(id="task-001", name="Task 1", description="First task", agent_type=AgentType.DESIGN),
    ]

    plan = Plan(
        user_story="Test story",
        requirements=["Req 1"],
        tasks=tasks,
        acceptance_criteria=["AC 1"],
    )

    # Update with output
    success = plan.update_task_status(
        "task-001", TaskStatus.COMPLETED, output="Task completed successfully"
    )
    assert success is True

    task = plan.get_task_by_id("task-001")
    assert task.status == "completed"
    assert task.output == "Task completed successfully"

    # Update with error
    success = plan.update_task_status("task-001", TaskStatus.FAILED, error="Task failed")
    assert success is True

    task = plan.get_task_by_id("task-001")
    assert task.status == "failed"
    assert task.error == "Task failed"

    # Update non-existent task
    success = plan.update_task_status("task-999", TaskStatus.COMPLETED)
    assert success is False


def test_is_complete():
    """Test checking if plan is complete."""
    tasks = [
        Task(
            id="task-001",
            name="Task 1",
            description="First task",
            agent_type=AgentType.DESIGN,
            status=TaskStatus.COMPLETED,
        ),
        Task(
            id="task-002",
            name="Task 2",
            description="Second task",
            agent_type=AgentType.CODING,
            status=TaskStatus.PENDING,
        ),
    ]

    plan = Plan(
        user_story="Test story",
        requirements=["Req 1"],
        tasks=tasks,
        acceptance_criteria=["AC 1"],
    )

    assert plan.is_complete() is False

    # Complete all tasks
    plan.update_task_status("task-002", TaskStatus.COMPLETED)
    assert plan.is_complete() is True


def test_get_progress():
    """Test getting progress statistics."""
    tasks = [
        Task(
            id="task-001",
            name="Task 1",
            description="First task",
            agent_type=AgentType.DESIGN,
            status=TaskStatus.COMPLETED,
        ),
        Task(
            id="task-002",
            name="Task 2",
            description="Second task",
            agent_type=AgentType.CODING,
            status=TaskStatus.IN_PROGRESS,
        ),
        Task(
            id="task-003",
            name="Task 3",
            description="Third task",
            agent_type=AgentType.TESTING,
            status=TaskStatus.FAILED,
        ),
        Task(
            id="task-004",
            name="Task 4",
            description="Fourth task",
            agent_type=AgentType.VALIDATION,
            status=TaskStatus.PENDING,
        ),
    ]

    plan = Plan(
        user_story="Test story",
        requirements=["Req 1"],
        tasks=tasks,
        acceptance_criteria=["AC 1"],
    )

    progress = plan.get_progress()
    assert progress["total"] == 4
    assert progress["completed"] == 1
    assert progress["in_progress"] == 1
    assert progress["failed"] == 1
    assert progress["pending"] == 1
    assert progress["percentage"] == 25.0
