"""QATesterAgent for V-Model Testing stages.

This agent handles test generation, test execution, and quality validation
during the TESTING stages of the V-Model.
"""

import json
import logging
from pathlib import Path
from typing import Any

from verifflowcc.agents.base import BaseAgent
from verifflowcc.schemas.agent_schemas import TestingInput

logger = logging.getLogger(__name__)


class QATesterAgent(BaseAgent):
    """Agent responsible for test generation and quality assurance in V-Model TESTING stages.

    The QATesterAgent handles multiple testing stages (unit, integration, system)
    and creates comprehensive test suites, executes tests, and validates
    acceptance criteria for the next stage.
    """

    def __init__(
        self,
        name: str = "qa_tester",
        model: str = "claude-3-sonnet",
        max_tokens: int = 4000,
        config_path: Path | None = None,
        path_config=None,
    ):
        """Initialize the QATesterAgent.

        Args:
            name: Agent name identifier
            model: Claude model to use for test generation
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
        """Process testing requirements and generate/execute tests.

        Args:
            input_data: Dictionary containing TestingInput data

        Returns:
            Dictionary containing TestingOutput data with test files,
            test results, coverage reports, and quality metrics
        """
        try:
            # Validate input using Pydantic schema
            try:
                testing_input = TestingInput(**input_data)
            except Exception as e:
                logger.error(f"Input validation failed: {e}")
                return self._create_error_output(f"Input validation error: {e!s}")

            logger.info(f"Processing testing for story {testing_input.story_id}")

            # Extract testing requirements
            test_scope = testing_input.test_scope
            acceptance_criteria = testing_input.acceptance_criteria
            context = testing_input.context
            story_id = testing_input.story_id

            # Generate tests using Claude API
            try:
                testing_response = await self._generate_tests(
                    test_scope, acceptance_criteria, context, story_id
                )
            except Exception as e:
                logger.error(f"Test generation failed: {e}")
                return self._create_error_output(f"Test generation error: {e!s}")

            # Execute tests (mock implementation)
            try:
                test_results = self._execute_tests(testing_response.get("test_files", []))
                testing_response["test_results"] = test_results
            except Exception as e:
                logger.warning(f"Test execution failed: {e}")
                testing_response["test_results"] = {"passed": 0, "failed": 1, "total": 1}

            # Save testing artifacts
            try:
                await self._save_testing_artifacts(story_id, testing_response)
            except Exception as e:
                logger.warning(f"Failed to save testing artifacts: {e}")

            # Create successful output
            return self._create_success_output(testing_response, story_id)

        except Exception as e:
            logger.error(f"Unexpected error in QATesterAgent.process: {e}")
            return self._create_error_output(f"Unexpected error: {e!s}")

    async def _generate_tests(
        self,
        test_scope: list[str],
        acceptance_criteria: list[str],
        context: dict[str, Any],
        story_id: str,
    ) -> dict[str, Any]:
        """Generate tests using Claude API.

        Args:
            test_scope: Types of tests to generate
            acceptance_criteria: Acceptance criteria to validate
            context: Additional context information
            story_id: Story identifier

        Returns:
            Dictionary containing test files, coverage info, and quality metrics
        """
        # Prepare prompt for Claude
        prompt = self._build_testing_prompt(test_scope, acceptance_criteria, context, story_id)

        # Call Claude API
        response = await self._call_claude_api(prompt)
        return self._parse_testing_response(response)

    def _build_testing_prompt(
        self,
        test_scope: list[str],
        acceptance_criteria: list[str],
        context: dict[str, Any],
        story_id: str,
    ) -> str:
        """Build the prompt for Claude API to generate tests."""
        return f"""
You are an experienced QA engineer. Generate comprehensive tests for the following requirements.

Story ID: {story_id}
Test Scope: {test_scope}
Acceptance Criteria: {acceptance_criteria}
Context: {json.dumps(context, indent=2)}

Generate tests that include:
1. Unit tests for individual components
2. Integration tests for component interactions
3. Acceptance tests for user stories
4. Test coverage and quality metrics

Return JSON with:
{{
    "test_files": [...],
    "coverage_report": {{"percentage": 95.0, "missing_lines": []}},
    "quality_metrics": {{"test_count": 10, "assertions": 25}}
}}
"""

    async def _call_claude_api(self, prompt: str) -> str:
        """Call Claude API to generate test content."""
        logger.info("Calling Claude API for test generation")

        # Mock response for testing
        return json.dumps(
            {
                "test_files": ["tests/test_user_service.py", "tests/test_auth_service.py"],
                "coverage_report": {"percentage": 95.5, "missing_lines": []},
                "quality_metrics": {"test_count": 15, "assertions": 40},
            }
        )

    def _parse_testing_response(self, response: str | dict) -> dict[str, Any]:
        """Parse Claude's response into structured testing data."""
        if isinstance(response, dict):
            return response
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            raise Exception("Could not parse testing response as JSON")

    def _execute_tests(self, test_files: list[str]) -> dict[str, Any]:
        """Execute tests and return results."""
        # Mock test execution
        return {"passed": len(test_files) * 5, "failed": 0, "total": len(test_files) * 5}

    async def _save_testing_artifacts(self, story_id: str, testing_data: dict[str, Any]) -> None:
        """Save testing artifacts to the testing subdirectory."""
        testing_artifact = {
            "story_id": story_id,
            "test_files": testing_data.get("test_files", []),
            "test_results": testing_data.get("test_results", {}),
            "coverage_report": testing_data.get("coverage_report", {}),
            "quality_metrics": testing_data.get("quality_metrics", {}),
            "generated_at": "2024-01-01T00:00:00Z",
            "version": "1.0",
        }

        self.save_artifact(f"testing/{story_id}.json", testing_artifact)

    def _create_success_output(self, testing_data: dict[str, Any], story_id: str) -> dict[str, Any]:
        """Create successful TestingOutput."""
        return {
            "status": "success",
            "artifacts": {"test_report": f"testing/{story_id}.json"},
            "test_files": testing_data.get("test_files", []),
            "test_results": testing_data.get("test_results", {}),
            "coverage_report": testing_data.get("coverage_report", {}),
            "quality_metrics": testing_data.get("quality_metrics", {}),
            "metrics": {
                "tests_generated": len(testing_data.get("test_files", [])),
                "coverage_percentage": testing_data.get("coverage_report", {}).get("percentage", 0),
            },
            "next_stage_ready": True,
            "errors": [],
        }

    def _create_error_output(self, error_message: str) -> dict[str, Any]:
        """Create error TestingOutput."""
        return {
            "status": "error",
            "artifacts": {},
            "test_files": [],
            "test_results": {},
            "coverage_report": {},
            "quality_metrics": {},
            "metrics": {},
            "next_stage_ready": False,
            "errors": [error_message],
        }
