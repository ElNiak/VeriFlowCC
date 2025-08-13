"""DeveloperAgent for V-Model Coding stage.

This agent handles feature implementation, code generation, and source code
creation during the CODING stage of the V-Model.
"""

import json
import logging
from pathlib import Path
from typing import Any

from verifflowcc.agents.base import BaseAgent
from verifflowcc.schemas.agent_schemas import ImplementationInput

logger = logging.getLogger(__name__)


class DeveloperAgent(BaseAgent):
    """Agent responsible for feature implementation and code generation in the V-Model CODING stage.

    The DeveloperAgent takes design artifacts from the ArchitectAgent and creates
    source code implementations, generates implementation reports, and produces
    code quality metrics for the testing phase.
    """

    def __init__(
        self,
        name: str = "developer",
        model: str = "claude-3-sonnet",
        max_tokens: int = 4000,
        config_path: Path | None = None,
        path_config=None,
    ):
        """Initialize the DeveloperAgent.

        Args:
            name: Agent name identifier
            model: Claude model to use for code generation
            max_tokens: Maximum tokens for Claude responses
            config_path: Path to configuration file (deprecated)
            path_config: PathConfig instance for managing project paths
        """
        super().__init__(
            name=name,
            model=model,
            max_tokens=max_tokens,
            config_path=config_path,
            path_config=path_config,
        )

    async def process(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """Process design specifications and generate implementation.

        Args:
            input_data: Dictionary containing ImplementationInput data

        Returns:
            Dictionary containing ImplementationOutput data with source files,
            code metrics, and implementation reports
        """
        try:
            # Validate input using Pydantic schema
            try:
                impl_input = ImplementationInput(**input_data)
            except Exception as e:
                logger.error(f"Input validation failed: {e}")
                return self._create_error_output(f"Input validation error: {e!s}")

            logger.info(f"Processing implementation for story {impl_input.story_id}")

            # Extract design artifacts for implementation
            design_artifacts = impl_input.design_artifacts
            architecture_context = impl_input.architecture_context
            context = impl_input.context
            story_id = impl_input.story_id

            # Generate implementation using Claude API
            try:
                implementation_response = await self._generate_implementation(
                    design_artifacts, architecture_context, context, story_id
                )
            except Exception as e:
                logger.error(f"Implementation generation failed: {e}")
                return self._create_error_output(f"Implementation generation error: {e!s}")

            # Create source files
            try:
                created_files = self._create_source_files(
                    implementation_response.get("source_files", [])
                )
            except Exception as e:
                logger.warning(f"Failed to create some source files: {e}")
                created_files = []  # Continue with partial success

            # Validate code quality
            code_metrics = implementation_response.get("code_metrics", {})
            quality_passed = self._validate_code_quality(code_metrics)

            if not quality_passed:
                logger.warning("Generated code did not meet quality standards")

            # Save implementation artifacts
            try:
                await self._save_implementation_artifacts(
                    story_id, implementation_response, created_files
                )
            except Exception as e:
                logger.warning(f"Failed to save implementation artifacts: {e}")
                # Continue with partial success

            # Create successful output
            return self._create_success_output(
                implementation_response, created_files, story_id, quality_passed
            )

        except Exception as e:
            logger.error(f"Unexpected error in DeveloperAgent.process: {e}")
            return self._create_error_output(f"Unexpected error: {e!s}")

    async def _generate_implementation(
        self,
        design_artifacts: dict[str, Any],
        architecture_context: dict[str, Any],
        context: dict[str, Any],
        story_id: str,
    ) -> dict[str, Any]:
        """Generate implementation using Claude API.

        Args:
            design_artifacts: Design specifications from ArchitectAgent
            architecture_context: Current architecture information
            context: Additional context information
            story_id: Story identifier

        Returns:
            Dictionary containing source files, code metrics, and implementation report
        """
        # Prepare prompt for Claude
        prompt = self._build_implementation_prompt(
            design_artifacts, architecture_context, context, story_id
        )

        # Call Claude API (with retry logic)
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = await self._call_claude_api(prompt)
                return self._parse_implementation_response(response)
            except Exception as e:
                if attempt == max_retries - 1:
                    raise e
                logger.warning(f"API call attempt {attempt + 1} failed: {e}")
                # Add exponential backoff here if needed

    def _build_implementation_prompt(
        self,
        design_artifacts: dict[str, Any],
        architecture_context: dict[str, Any],
        context: dict[str, Any],
        story_id: str,
    ) -> str:
        """Build the prompt for Claude API to generate implementation.

        Args:
            design_artifacts: Design specifications
            architecture_context: Architecture information
            context: Context information
            story_id: Story identifier

        Returns:
            Formatted prompt string for Claude
        """
        # Load template if available
        template = self.load_prompt_template("implementation")

        if template:
            # Use Jinja2 template if available
            try:
                from jinja2 import Template

                jinja_template = Template(template)
                return jinja_template.render(
                    design_artifacts=design_artifacts,
                    architecture_context=architecture_context,
                    context=context,
                    story_id=story_id,
                )
            except ImportError:
                logger.warning("Jinja2 not available, using simple template replacement")

        # Fallback to simple template
        return f"""
You are an experienced software developer. Implement the following design specification as clean, maintainable, and well-documented code.

Story ID: {story_id}
Design Artifacts: {json.dumps(design_artifacts, indent=2)}
Architecture Context: {json.dumps(architecture_context, indent=2)}
Context: {json.dumps(context, indent=2)}

Please provide a complete implementation that includes:

1. **Source Files**:
   - Complete implementations of all components
   - Proper class structures and method implementations
   - Type hints and documentation
   - Error handling and logging

2. **Code Quality**:
   - Follow SOLID principles and clean code practices
   - Implement proper separation of concerns
   - Include comprehensive error handling
   - Add appropriate logging and monitoring

3. **Implementation Report**:
   - Summary of features implemented
   - Design patterns used
   - Dependencies and libraries added
   - Performance considerations

Return your response as a JSON object with the following structure:
{{
    "source_files": [
        {{
            "path": "relative/path/to/file.py",
            "content": "complete file content here"
        }}
    ],
    "code_metrics": {{
        "total_lines": 150,
        "complexity_score": 5,
        "test_coverage": 85,
        "maintainability_index": 90
    }},
    "implementation_report": {{
        "features_implemented": [...],
        "design_patterns_used": [...],
        "dependencies_added": [...],
        "performance_notes": "..."
    }}
}}

Focus on creating production-ready code that is:
- Scalable and performant
- Well-tested and maintainable
- Properly documented
- Follows established coding standards
- Integrates seamlessly with existing architecture
"""

    async def _call_claude_api(self, prompt: str) -> str:
        """Call Claude API to generate implementation content.

        Args:
            prompt: The prompt to send to Claude

        Returns:
            Claude's response as a string

        Raises:
            Exception: If API call fails
        """
        # This is a placeholder for the actual Claude API integration
        # In a real implementation, this would use the Anthropic SDK
        logger.info("Calling Claude API for implementation generation")

        # Mock response for testing
        return json.dumps(
            {
                "source_files": [
                    {
                        "path": "src/services/user_service.py",
                        "content": """from typing import List, Optional
from models.user import User
from repositories.user_repository import IUserRepository

class UserService:
    def __init__(self, user_repository: IUserRepository):
        self.user_repository = user_repository

    def create_user(self, name: str, email: str) -> User:
        if not name or not email:
            raise ValueError("Name and email are required")

        user = User(name=name, email=email)
        return self.user_repository.save(user)

    def find_user_by_id(self, user_id: str) -> Optional[User]:
        return self.user_repository.find_by_id(user_id)

    def list_users(self) -> List[User]:
        return self.user_repository.find_all()
""",
                    },
                    {
                        "path": "src/models/user.py",
                        "content": """from dataclasses import dataclass
from typing import Optional

@dataclass
class User:
    name: str
    email: str
    id: Optional[str] = None

    def __post_init__(self):
        if not self.name:
            raise ValueError("Name cannot be empty")
        if not self.email or "@" not in self.email:
            raise ValueError("Valid email is required")
""",
                    },
                ],
                "code_metrics": {
                    "total_lines": 45,
                    "complexity_score": 3,
                    "test_coverage": 90,
                    "maintainability_index": 85,
                },
                "implementation_report": {
                    "features_implemented": ["user_creation", "user_retrieval", "user_listing"],
                    "design_patterns_used": ["Repository", "Dependency Injection"],
                    "dependencies_added": ["typing", "dataclasses"],
                    "performance_notes": "Simple in-memory operations, suitable for small to medium datasets",
                },
            }
        )

    def _parse_implementation_response(self, response: str | dict) -> dict[str, Any]:
        """Parse Claude's response into structured implementation data.

        Args:
            response: Raw response from Claude API (string) or already parsed dict

        Returns:
            Parsed implementation data

        Raises:
            Exception: If response cannot be parsed
        """
        # If response is already a dict (from mocking), return it directly
        if isinstance(response, dict):
            return response

        try:
            # Try to parse as JSON
            return json.loads(response)
        except json.JSONDecodeError:
            # If not JSON, try to extract JSON from text
            import re

            json_match = re.search(r"\{.*\}", response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            else:
                raise Exception("Could not parse implementation response as JSON")

    def _create_source_files(self, source_files_data: list[dict[str, Any]]) -> list[str]:
        """Create source files from the implementation data.

        Args:
            source_files_data: List of source file definitions

        Returns:
            List of created file paths
        """
        created_files = []

        # Note: In a real implementation, this would create actual files
        # For testing, we just track what would be created
        for file_data in source_files_data:
            file_path = file_data.get("path", "")
            file_content = file_data.get("content", "")

            if file_path and file_content:
                # In real implementation:
                # full_path = Path(file_path)
                # full_path.parent.mkdir(parents=True, exist_ok=True)
                # full_path.write_text(file_content)

                created_files.append(file_path)
                logger.info(f"Would create source file: {file_path}")

        return created_files

    def _validate_code_quality(self, code_metrics: dict[str, Any]) -> bool:
        """Validate that generated code meets quality standards.

        Args:
            code_metrics: Code quality metrics

        Returns:
            True if code meets quality standards, False otherwise
        """
        if not code_metrics:
            return False

        # Define quality thresholds
        thresholds = {
            "complexity_score": 10,  # Max complexity
            "test_coverage": 80,  # Min test coverage
            "maintainability_index": 70,  # Min maintainability
        }

        # Check complexity (lower is better)
        complexity = code_metrics.get("complexity_score", 0)
        if complexity > thresholds["complexity_score"]:
            logger.warning(f"Code complexity too high: {complexity}")
            return False

        # Check test coverage (higher is better)
        coverage = code_metrics.get("test_coverage", 0)
        if coverage < thresholds["test_coverage"]:
            logger.warning(f"Test coverage too low: {coverage}%")
            return False

        # Check maintainability (higher is better)
        maintainability = code_metrics.get("maintainability_index", 0)
        if maintainability < thresholds["maintainability_index"]:
            logger.warning(f"Maintainability index too low: {maintainability}")
            return False

        return True

    async def _save_implementation_artifacts(
        self, story_id: str, implementation_data: dict[str, Any], created_files: list[str]
    ) -> None:
        """Save implementation artifacts to the implementation subdirectory.

        Args:
            story_id: Story identifier
            implementation_data: Generated implementation data
            created_files: List of created source file paths
        """
        # Save main implementation report
        impl_artifact = {
            "story_id": story_id,
            "source_files": created_files,
            "code_metrics": implementation_data.get("code_metrics", {}),
            "implementation_report": implementation_data.get("implementation_report", {}),
            "generated_at": "2024-01-01T00:00:00Z",  # Would use datetime.now() in real implementation
            "version": "1.0",
        }

        self.save_artifact(f"implementation/{story_id}.json", impl_artifact)

        # Save code metrics separately for tracking
        metrics_artifact = {
            "story_id": story_id,
            "metrics": implementation_data.get("code_metrics", {}),
            "quality_passed": self._validate_code_quality(
                implementation_data.get("code_metrics", {})
            ),
            "timestamp": "2024-01-01T00:00:00Z",
        }

        self.save_artifact(f"implementation/metrics/{story_id}_metrics.json", metrics_artifact)

    def _create_success_output(
        self,
        implementation_data: dict[str, Any],
        created_files: list[str],
        story_id: str,
        quality_passed: bool,
    ) -> dict[str, Any]:
        """Create successful ImplementationOutput.

        Args:
            implementation_data: Generated implementation data
            created_files: List of created source files
            story_id: Story identifier
            quality_passed: Whether code quality validation passed

        Returns:
            Success output dictionary
        """
        status = "success" if quality_passed else "partial"

        return {
            "status": status,
            "artifacts": {
                "implementation_report": f"implementation/{story_id}.json",
                "source_files": created_files,
                "metrics_report": f"implementation/metrics/{story_id}_metrics.json",
            },
            "source_files": created_files,
            "code_metrics": implementation_data.get("code_metrics", {}),
            "implementation_report": implementation_data.get("implementation_report", {}),
            "metrics": {
                "files_created": len(created_files),
                "total_lines": implementation_data.get("code_metrics", {}).get("total_lines", 0),
                "complexity_score": implementation_data.get("code_metrics", {}).get(
                    "complexity_score", 0
                ),
                "quality_passed": quality_passed,
            },
            "next_stage_ready": quality_passed,
            "errors": [] if quality_passed else ["Code quality validation failed"],
        }

    def _create_error_output(self, error_message: str) -> dict[str, Any]:
        """Create error ImplementationOutput.

        Args:
            error_message: Error description

        Returns:
            Error output dictionary
        """
        return {
            "status": "error",
            "artifacts": {},
            "source_files": [],
            "code_metrics": {},
            "implementation_report": {},
            "metrics": {},
            "next_stage_ready": False,
            "errors": [error_message],
        }
