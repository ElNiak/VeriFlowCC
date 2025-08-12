"""Requirements Analyst Agent for VeriFlowCC."""

from datetime import datetime
from pathlib import Path
from typing import Any

from verifflowcc.core.path_config import PathConfig

from .base import BaseAgent


class RequirementsAnalystAgent(BaseAgent):
    """Agent responsible for requirements analysis and elaboration."""

    def __init__(self, config_path: Path | None = None, path_config: PathConfig | None = None):
        """Initialize the Requirements Analyst agent.

        Args:
            config_path: Path to configuration file (deprecated, use path_config)
            path_config: PathConfig instance for managing project paths
        """
        super().__init__(
            name="requirements_analyst",
            model="claude-3-sonnet",
            max_tokens=4000,
            config_path=config_path,
            path_config=path_config,
        )

    async def process(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """Process requirements and elaborate them.

        Args:
            input_data: Contains 'story' and optional 'backlog_path'

        Returns:
            Elaborated requirements with acceptance criteria
        """
        story = input_data.get("story", {})
        backlog_path = input_data.get("backlog_path", str(self.path_config.backlog_path))

        # Simulate Claude-Code API call for requirements analysis
        # In production, this would make actual API calls to Claude
        elaborated_requirements = await self._analyze_requirements(story)

        # Save the elaborated requirements
        self.save_artifact(
            f"requirements/{story.get('id', 'unknown')}.json", elaborated_requirements
        )

        # Update the backlog with elaborated requirements
        await self._update_backlog(backlog_path, elaborated_requirements)

        return elaborated_requirements

    async def _analyze_requirements(self, story: dict[str, Any]) -> dict[str, Any]:
        """Analyze and elaborate requirements using Claude.

        Args:
            story: User story to analyze

        Returns:
            Elaborated requirements
        """
        # This is a placeholder for Claude-Code integration
        # In production, this would:
        # 1. Format the prompt using Jinja2 template
        # 2. Call Claude API with the story context
        # 3. Parse and structure the response

        elaborated = {
            "id": story.get("id", "STORY-001"),
            "title": story.get("title", ""),
            "description": story.get("description", ""),
            "elaborated_at": datetime.now().isoformat(),
            "functional_requirements": [],
            "non_functional_requirements": [],
            "acceptance_criteria": [],
            "test_scenarios": [],
            "dependencies": [],
            "risks": [],
            "effort_estimate": "TBD",
            "priority": story.get("priority", "Medium"),
        }

        # Simulate requirements elaboration
        if "authentication" in story.get("title", "").lower():
            elaborated["functional_requirements"] = [
                "System SHALL provide user login functionality",
                "System SHALL validate user credentials",
                "System SHALL maintain user sessions",
                "System SHALL provide logout functionality",
            ]
            elaborated["non_functional_requirements"] = [
                "Authentication SHALL complete within 2 seconds",
                "System SHALL support concurrent user sessions",
                "Passwords SHALL be encrypted using bcrypt",
            ]
            elaborated["acceptance_criteria"] = [
                "GIVEN valid credentials WHEN user logs in THEN access is granted",
                "GIVEN invalid credentials WHEN user logs in THEN access is denied",
                "GIVEN active session WHEN user logs out THEN session is terminated",
            ]

        return elaborated

    async def _update_backlog(self, backlog_path: str, requirements: dict[str, Any]) -> None:
        """Update the backlog with elaborated requirements.

        Args:
            backlog_path: Path to backlog file
            requirements: Elaborated requirements
        """
        backlog = Path(backlog_path)
        if not backlog.exists():
            backlog.parent.mkdir(parents=True, exist_ok=True)
            backlog.write_text("# Product Backlog\n\n")

        # Append elaborated requirements to backlog
        content = backlog.read_text()

        # Add a section for this story if not exists
        story_section = f"\n## {requirements['id']}: {requirements['title']}\n\n"

        if requirements["id"] not in content:
            content += story_section
            content += f"**Priority:** {requirements['priority']}\n"
            content += f"**Elaborated:** {requirements['elaborated_at']}\n\n"

            if requirements["functional_requirements"]:
                content += "### Functional Requirements\n"
                for req in requirements["functional_requirements"]:
                    content += f"- {req}\n"
                content += "\n"

            if requirements["acceptance_criteria"]:
                content += "### Acceptance Criteria\n"
                for criteria in requirements["acceptance_criteria"]:
                    content += f"- {criteria}\n"
                content += "\n"

            backlog.write_text(content)

    async def validate_requirements(self, requirements: dict[str, Any]) -> dict[str, Any]:
        """Validate requirements against INVEST criteria.

        Args:
            requirements: Requirements to validate

        Returns:
            Validation results
        """
        validation: dict[str, Any] = {
            "is_valid": True,
            "criteria": {
                "independent": True,
                "negotiable": True,
                "valuable": True,
                "estimable": True,
                "small": True,
                "testable": True,
            },
            "issues": [],
        }

        # Check for acceptance criteria (testable)
        if not requirements.get("acceptance_criteria"):
            validation["criteria"]["testable"] = False
            validation["issues"].append("Missing acceptance criteria")
            validation["is_valid"] = False

        # Check for effort estimate (estimable)
        if requirements.get("effort_estimate") == "TBD":
            validation["criteria"]["estimable"] = False
            validation["issues"].append("Missing effort estimate")

        # Check for dependencies (independent)
        if len(requirements.get("dependencies", [])) > 2:
            validation["criteria"]["independent"] = False
            validation["issues"].append("Too many dependencies")

        return validation
