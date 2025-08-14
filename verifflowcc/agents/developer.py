"""DeveloperAgent for V-Model Coding stage.

This agent handles feature implementation, code generation, and source code
creation during the CODING stage of the V-Model.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from verifflowcc.agents.base import BaseAgent
from verifflowcc.core.path_config import PathConfig
from verifflowcc.core.sdk_config import SDKConfig

logger = logging.getLogger(__name__)


class DeveloperAgent(BaseAgent):
    """Agent responsible for feature implementation and code generation using Claude Code SDK.

    The DeveloperAgent takes design specifications and creates source code
    implementations, generates tests, and produces implementation artifacts
    with comprehensive documentation.
    """

    def __init__(
        self,
        name: str = "developer",
        agent_type: str = "developer",
        path_config: PathConfig | None = None,
        sdk_config: SDKConfig | None = None,
        mock_mode: bool = False,
    ):
        """Initialize the DeveloperAgent.

        Args:
            name: Agent name identifier
            agent_type: Agent type (developer)
            path_config: PathConfig instance for managing project paths
            sdk_config: SDK configuration instance
            mock_mode: Whether to use mock responses
        """
        super().__init__(
            name=name,
            agent_type=agent_type,
            path_config=path_config,
            sdk_config=sdk_config,
            mock_mode=mock_mode,
        )

    async def process(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """Process design specifications and generate implementation using Claude Code SDK.

        Args:
            input_data: Contains design artifacts and context data

        Returns:
            Dictionary containing implementation files, tests, documentation, and metrics
        """
        try:
            logger.info("Processing development implementation request")

            # Extract input data
            design_spec = input_data.get("design_spec", {})
            story_id = input_data.get("story_id", f"DEV-{datetime.now().strftime('%Y%m%d-%H%M%S')}")
            task_description = input_data.get("task_description", "")
            project_context = input_data.get("context", {})

            # Build prompt context
            prompt_context = {
                "task_description": task_description,
                "project_name": project_context.get("project_name", "VeriFlowCC"),
                "sprint_number": project_context.get("sprint_number", "Current Sprint"),
                "tech_stack": project_context.get("tech_stack", "Python, FastAPI, SQLAlchemy"),
                "design_spec": json.dumps(design_spec, indent=2)
                if design_spec
                else "No design specification provided",
                "context": json.dumps(project_context, indent=2) if project_context else "",
            }

            # Load template and create prompt
            prompt = self.load_prompt_template("developer", **prompt_context)

            # Call Claude Code SDK
            response = await self._call_claude_sdk(prompt, input_data)

            # Parse the response
            implementation_data = await self._parse_implementation_response(
                response, story_id, design_spec
            )

            # Create source files from implementation
            created_files = await self._create_source_files(
                implementation_data.get("implementation", {})
            )

            # Validate code quality
            quality_metrics = await self._validate_implementation_quality(implementation_data)

            # Save implementation artifacts
            await self._save_implementation_artifacts(story_id, implementation_data, created_files)

            logger.info(f"Successfully processed implementation for {story_id}")
            return self._create_success_output(
                implementation_data, created_files, story_id, quality_metrics
            )

        except Exception as e:
            logger.error(f"Error processing implementation: {e}")
            return self._create_error_output(str(e))

    async def _parse_implementation_response(
        self, response: str, story_id: str, design_spec: dict[str, Any]
    ) -> dict[str, Any]:
        """Parse Claude's response into structured implementation data.

        Args:
            response: Raw response from Claude
            story_id: Story identifier
            design_spec: Original design specification

        Returns:
            Structured implementation data
        """
        try:
            # Try to parse as JSON first
            if response.strip().startswith("{"):
                parsed_response: dict[str, Any] = json.loads(response)

                # Add metadata
                parsed_response.update(
                    {
                        "id": story_id,
                        "design_reference": design_spec,
                        "implemented_at": datetime.now().isoformat(),
                        "agent": self.name,
                        "agent_type": self.agent_type,
                    }
                )

                return parsed_response

            # If not JSON, structure the text response
            return {
                "id": story_id,
                "design_reference": design_spec,
                "implemented_at": datetime.now().isoformat(),
                "agent": self.name,
                "agent_type": self.agent_type,
                "response_text": response,
                "implementation": {
                    "language": "python",
                    "framework": "fastapi",
                    "version": "Python 3.10+",
                    "files": [],
                },
                "tests": {"framework": "pytest", "coverage_target": "90%", "test_files": []},
                "documentation": {
                    "api_docs": {"format": "markdown", "content": "", "examples": ""},
                    "code_documentation": [],
                },
            }

        except json.JSONDecodeError as e:
            logger.warning(f"Could not parse Claude response as JSON: {e}")
            # Return structured fallback
            return {
                "id": story_id,
                "design_reference": design_spec,
                "implemented_at": datetime.now().isoformat(),
                "agent": self.name,
                "agent_type": self.agent_type,
                "response_text": response,
                "parse_error": str(e),
                "implementation": {"files": []},
                "tests": {"test_files": []},
                "documentation": {"code_documentation": []},
            }

    async def _create_source_files(self, implementation: dict[str, Any]) -> list[str]:
        """Create source files from implementation data.

        Args:
            implementation: Implementation data containing file specifications

        Returns:
            List of created file paths
        """
        created_files = []

        try:
            files = implementation.get("files", [])

            for file_spec in files:
                if isinstance(file_spec, dict):
                    file_path = file_spec.get("path", "")
                    content = file_spec.get("content", "")
                    purpose = file_spec.get("purpose", "Generated file")

                    if file_path and content:
                        # Create directory structure if needed
                        full_path = Path.cwd() / file_path
                        full_path.parent.mkdir(parents=True, exist_ok=True)

                        # Add file header comment
                        file_header = f'"""{purpose}\n\nGenerated by VeriFlowCC Developer Agent\nTimestamp: {datetime.now().isoformat()}\n"""\n\n'

                        # Write file
                        full_path.write_text(file_header + content)
                        created_files.append(file_path)
                        logger.info(f"Created source file: {file_path}")

        except Exception as e:
            logger.error(f"Error creating source files: {e}")

        return created_files

    async def _validate_implementation_quality(
        self, implementation_data: dict[str, Any]
    ) -> dict[str, Any]:
        """Validate the quality of the implementation.

        Args:
            implementation_data: Implementation data to validate

        Returns:
            Quality metrics and validation results
        """
        try:
            quality_metrics: dict[str, Any] = {
                "overall_score": 0.0,
                "code_quality": {"score": 0.0, "issues": []},
                "test_coverage": {"score": 0.0, "issues": []},
                "documentation": {"score": 0.0, "issues": []},
                "security": {"score": 0.0, "issues": []},
                "performance": {"score": 0.0, "issues": []},
                "maintainability": {"score": 0.0, "issues": []},
            }

            implementation: dict[str, Any] = implementation_data.get("implementation", {})
            tests: dict[str, Any] = implementation_data.get("tests", {})
            documentation: dict[str, Any] = implementation_data.get("documentation", {})

            # Code quality assessment
            files = implementation.get("files", [])
            if files:
                quality_metrics["code_quality"]["score"] = 0.8  # Base score

                # Check for proper structure
                has_classes = any(
                    "class " in str(f.get("content", "")) for f in files if isinstance(f, dict)
                )
                has_functions = any(
                    "def " in str(f.get("content", "")) for f in files if isinstance(f, dict)
                )

                if has_classes and has_functions:
                    quality_metrics["code_quality"]["score"] += 0.1

                # Check for error handling
                has_try_catch = any(
                    "try:" in str(f.get("content", "")) for f in files if isinstance(f, dict)
                )
                if has_try_catch:
                    quality_metrics["code_quality"]["score"] += 0.1
                else:
                    quality_metrics["code_quality"]["issues"].append("Missing error handling")
            else:
                quality_metrics["code_quality"]["issues"].append("No implementation files provided")

            # Test coverage assessment
            test_files = tests.get("test_files", [])
            if test_files:
                quality_metrics["test_coverage"]["score"] = 0.7

                # Check for comprehensive test types
                test_content = " ".join(
                    str(tf.get("content", "")) for tf in test_files if isinstance(tf, dict)
                )
                if "test_" in test_content:
                    quality_metrics["test_coverage"]["score"] += 0.2
                if "mock" in test_content.lower():
                    quality_metrics["test_coverage"]["score"] += 0.1
            else:
                quality_metrics["test_coverage"]["issues"].append("No test files provided")

            # Documentation assessment
            docs = documentation.get("code_documentation", [])
            api_docs = documentation.get("api_docs", {})

            if docs or api_docs.get("content"):
                quality_metrics["documentation"]["score"] = 0.8
            else:
                quality_metrics["documentation"]["issues"].append("Insufficient documentation")

            # Security assessment (basic checks)
            quality_metrics["security"]["score"] = 0.7  # Base score

            # Check for common security issues
            all_content = " ".join(str(f.get("content", "")) for f in files if isinstance(f, dict))
            if "password" in all_content.lower() and "hash" not in all_content.lower():
                quality_metrics["security"]["issues"].append("Potential password security issue")
                quality_metrics["security"]["score"] -= 0.2

            # Performance assessment (basic)
            quality_metrics["performance"]["score"] = 0.7  # Assume good until proven otherwise

            # Maintainability assessment
            if files and test_files and docs:
                quality_metrics["maintainability"]["score"] = 0.8
            else:
                quality_metrics["maintainability"]["score"] = 0.5
                quality_metrics["maintainability"]["issues"].append(
                    "Incomplete implementation package"
                )

            # Calculate overall score
            scores = [
                metrics["score"]
                for metrics in quality_metrics.values()
                if isinstance(metrics, dict) and "score" in metrics
            ]
            quality_metrics["overall_score"] = sum(scores) / len(scores) if scores else 0.0

            return quality_metrics

        except Exception as e:
            logger.error(f"Error validating implementation quality: {e}")
            return {
                "overall_score": 0.0,
                "validation_error": str(e),
                "code_quality": {"score": 0.0, "issues": ["Validation failed"]},
                "test_coverage": {"score": 0.0, "issues": ["Validation failed"]},
                "documentation": {"score": 0.0, "issues": ["Validation failed"]},
            }

    async def _save_implementation_artifacts(
        self, story_id: str, implementation_data: dict[str, Any], created_files: list[str]
    ) -> None:
        """Save implementation artifacts.

        Args:
            story_id: Story identifier
            implementation_data: Implementation data
            created_files: List of created file paths
        """
        try:
            # Save main implementation document
            artifact_data = {
                **implementation_data,
                "created_files": created_files,
                "artifact_type": "implementation",
            }
            self.save_artifact(f"implementation/{story_id}.json", artifact_data)

            # Save test reports
            tests = implementation_data.get("tests", {})
            if tests:
                self.save_artifact(f"implementation/{story_id}_tests.json", tests)

            # Save documentation
            documentation = implementation_data.get("documentation", {})
            if documentation:
                api_docs = documentation.get("api_docs", {})
                if api_docs.get("content"):
                    self.save_artifact(
                        f"implementation/{story_id}_api_docs.md", api_docs["content"]
                    )

            logger.info(f"Saved implementation artifacts for {story_id}")

        except Exception as e:
            logger.error(f"Error saving implementation artifacts: {e}")

    def _create_success_output(
        self,
        implementation_data: dict[str, Any],
        created_files: list[str],
        story_id: str,
        quality_metrics: dict[str, Any],
    ) -> dict[str, Any]:
        """Create successful output.

        Args:
            implementation_data: Generated implementation data
            created_files: List of created files
            story_id: Story identifier
            quality_metrics: Quality assessment results

        Returns:
            Success output dictionary
        """
        return {
            "status": "success",
            "story_id": story_id,
            "agent": self.name,
            "agent_type": self.agent_type,
            "artifacts": {
                "implementation_document": f"implementation/{story_id}.json",
                "test_report": f"implementation/{story_id}_tests.json",
                "api_documentation": f"implementation/{story_id}_api_docs.md",
                "source_files": created_files,
            },
            "implementation_data": implementation_data,
            "quality_metrics": quality_metrics,
            "metrics": {
                "files_created": len(created_files),
                "test_files": len(implementation_data.get("tests", {}).get("test_files", [])),
                "documentation_sections": len(
                    implementation_data.get("documentation", {}).get("code_documentation", [])
                ),
                "overall_quality_score": quality_metrics.get("overall_score", 0.0),
            },
            "next_stage_ready": quality_metrics.get("overall_score", 0.0) > 0.6,
            "validation_passed": quality_metrics.get("overall_score", 0.0) > 0.7,
            "timestamp": datetime.now().isoformat(),
        }

    def _create_error_output(self, error_message: str) -> dict[str, Any]:
        """Create error output.

        Args:
            error_message: Error description

        Returns:
            Error output dictionary
        """
        return {
            "status": "error",
            "agent": self.name,
            "agent_type": self.agent_type,
            "error": error_message,
            "artifacts": {},
            "implementation_data": {},
            "quality_metrics": {},
            "metrics": {},
            "next_stage_ready": False,
            "validation_passed": False,
            "timestamp": datetime.now().isoformat(),
        }
