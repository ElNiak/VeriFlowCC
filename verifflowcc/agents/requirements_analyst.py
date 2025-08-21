"""Requirements Analyst Agent for VeriFlowCC."""

import json
import logging
from datetime import datetime
from typing import Any

from verifflowcc.core.path_config import PathConfig
from verifflowcc.core.sdk_config import SDKConfig

from .base import BaseAgent

logger = logging.getLogger(__name__)


class RequirementsAnalystAgent(BaseAgent):
    """Agent responsible for requirements analysis and elaboration using Claude Code SDK."""

    def __init__(
        self,
        name: str = "requirements_analyst",
        agent_type: str = "requirements",
        path_config: PathConfig | None = None,
        sdk_config: SDKConfig | None = None,
    ):
        """Initialize the Requirements Analyst agent.

        Args:
            name: Agent name identifier
            agent_type: Agent type (requirements)
            path_config: PathConfig instance for managing project paths
            sdk_config: SDK configuration instance
        """
        super().__init__(
            name=name,
            agent_type=agent_type,
            path_config=path_config,
            sdk_config=sdk_config,
        )

    async def process(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """Process requirements and elaborate them using Claude Code SDK.

        Args:
            input_data: Contains 'story' and optional context data

        Returns:
            Elaborated requirements with acceptance criteria
        """
        try:
            logger.info("Processing requirements analysis request")

            # Extract input data
            story = input_data.get("story", {})
            task_description = input_data.get("task_description", "")
            project_context = input_data.get("context", {})

            # Build prompt context
            prompt_context = {
                "task_description": task_description or story.get("description", ""),
                "project_name": project_context.get("project_name", "VeriFlowCC"),
                "sprint_number": project_context.get("sprint_number", "Current Sprint"),
                "user_story": story.get("title", ""),
                "context": (json.dumps(project_context, indent=2) if project_context else ""),
            }

            # Load template and create prompt
            prompt = self.load_prompt_template("requirements", **prompt_context)

            # Call Claude Code SDK
            response = await self._call_claude_sdk(prompt, input_data)

            # Parse the response
            elaborated_requirements = await self._parse_requirements_response(response, story)

            # Save artifacts
            story_id = story.get("id", f"REQ-{datetime.now().strftime('%Y%m%d-%H%M%S')}")
            self.save_artifact(f"requirements/{story_id}.json", elaborated_requirements)

            # Update backlog if requested
            if input_data.get("update_backlog", True):
                await self._update_backlog(elaborated_requirements)

            logger.info(f"Successfully processed requirements for story {story_id}")
            return elaborated_requirements

        except Exception as e:
            logger.error(f"Error processing requirements: {e}")
            raise

    async def _parse_requirements_response(
        self, response: str, story: dict[str, Any]
    ) -> dict[str, Any]:
        """Parse Claude's response into structured requirements.

        Args:
            response: Raw response from Claude
            story: Original user story data

        Returns:
            Structured requirements data
        """
        try:
            # Try to parse as JSON first
            if response.strip().startswith("{"):
                parsed_response = json.loads(response)

                # Add metadata
                parsed_response.update(
                    {
                        "id": story.get("id", f"REQ-{datetime.now().strftime('%Y%m%d-%H%M%S')}"),
                        "original_story": story,
                        "elaborated_at": datetime.now().isoformat(),
                        "agent": self.name,
                        "agent_type": self.agent_type,
                    }
                )

                return parsed_response  # type: ignore[no-any-return]

            # If not JSON, structure the text response
            return {
                "id": story.get("id", f"REQ-{datetime.now().strftime('%Y%m%d-%H%M%S')}"),
                "original_story": story,
                "elaborated_at": datetime.now().isoformat(),
                "agent": self.name,
                "agent_type": self.agent_type,
                "response_text": response,
                "functional_requirements": [],
                "non_functional_requirements": [],
                "acceptance_criteria": [],
                "dependencies": [],
                "constraints": [],
                "traceability": {
                    "source_document": "User Story",
                    "business_objective": story.get("business_value", ""),
                    "risk_level": "medium",
                },
            }

        except json.JSONDecodeError as e:
            logger.warning(f"Could not parse Claude response as JSON: {e}")
            # Return structured fallback
            return {
                "id": story.get("id", f"REQ-{datetime.now().strftime('%Y%m%d-%H%M%S')}"),
                "original_story": story,
                "elaborated_at": datetime.now().isoformat(),
                "agent": self.name,
                "agent_type": self.agent_type,
                "response_text": response,
                "parse_error": str(e),
                "functional_requirements": [],
                "non_functional_requirements": [],
                "acceptance_criteria": [],
            }

    async def _update_backlog(self, requirements: dict[str, Any]) -> None:
        """Update the backlog with elaborated requirements.

        Args:
            requirements: Elaborated requirements
        """
        try:
            backlog_path = self.path_config.backlog_path

            if not backlog_path.exists():
                backlog_path.parent.mkdir(parents=True, exist_ok=True)
                backlog_path.write_text("# Product Backlog\n\n")

            # Read current content
            content = backlog_path.read_text()

            # Build new section
            req_id = requirements.get("id", "UNKNOWN")
            story = requirements.get("original_story", {})

            story_section = f"\n## {req_id}: {story.get('title', 'Untitled')}\n\n"

            # Only add if not already present
            if req_id not in content:
                story_section += f"**Priority:** {story.get('priority', 'Medium')}\n"
                story_section += f"**Elaborated:** {requirements.get('elaborated_at', 'Unknown')}\n"
                story_section += (
                    f"**Description:** {story.get('description', 'No description')}\n\n"
                )

                # Add functional requirements
                functional_reqs = requirements.get("functional_requirements", [])
                if functional_reqs:
                    story_section += "### Functional Requirements\n"
                    for req in functional_reqs:
                        if isinstance(req, dict):
                            story_section += f"- **{req.get('id', 'REQ-XXX')}**: {req.get('description', 'No description')}\n"
                        else:
                            story_section += f"- {req}\n"
                    story_section += "\n"

                # Add non-functional requirements
                nf_reqs = requirements.get("non_functional_requirements", [])
                if nf_reqs:
                    story_section += "### Non-Functional Requirements\n"
                    for req in nf_reqs:
                        if isinstance(req, dict):
                            story_section += f"- **{req.get('id', 'NFR-XXX')}**: {req.get('description', 'No description')}\n"
                        else:
                            story_section += f"- {req}\n"
                    story_section += "\n"

                # Add acceptance criteria
                acceptance_criteria = requirements.get("acceptance_criteria", [])
                if acceptance_criteria:
                    story_section += "### Acceptance Criteria\n"
                    for criteria in acceptance_criteria:
                        if isinstance(criteria, dict):
                            story_section += f"- **{criteria.get('id', 'AC-XXX')}**: {criteria.get('scenario', 'No scenario')}\n"
                        else:
                            story_section += f"- {criteria}\n"
                    story_section += "\n"

                # Add dependencies
                dependencies = requirements.get("dependencies", [])
                if dependencies:
                    story_section += "### Dependencies\n"
                    for dep in dependencies:
                        if isinstance(dep, dict):
                            story_section += f"- **{dep.get('type', 'unknown')}**: {dep.get('description', 'No description')}\n"
                        else:
                            story_section += f"- {dep}\n"
                    story_section += "\n"

                # Write updated content
                content += story_section
                backlog_path.write_text(content)
                logger.info(f"Updated backlog with requirements for {req_id}")

        except Exception as e:
            logger.error(f"Error updating backlog: {e}")

    async def validate_requirements(self, requirements: dict[str, Any]) -> dict[str, Any]:
        """Validate requirements against INVEST and SMART criteria.

        Args:
            requirements: Requirements to validate

        Returns:
            Validation results with detailed criteria assessment
        """
        try:
            validation: dict[str, Any] = {
                "is_valid": True,
                "invest_criteria": {
                    "independent": {"score": 0.9, "issues": []},
                    "negotiable": {"score": 0.85, "issues": []},
                    "valuable": {"score": 0.9, "issues": []},
                    "estimable": {"score": 0.9, "issues": []},
                    "small": {"score": 0.9, "issues": []},
                    "testable": {"score": 0.9, "issues": []},
                },
                "smart_criteria": {
                    "specific": {"score": 0.9, "issues": []},
                    "measurable": {"score": 0.85, "issues": []},
                    "achievable": {"score": 0.85, "issues": []},
                    "relevant": {"score": 0.85, "issues": []},
                    "time_bound": {"score": 0.85, "issues": []},
                },
                "overall_score": 0.9,
                "recommendations": [],
            }

            # Check INVEST criteria

            # Independent: Check for excessive dependencies
            dependencies = requirements.get("dependencies", [])
            if len(dependencies) > 3:
                validation["invest_criteria"]["independent"]["score"] = 0.5
                validation["invest_criteria"]["independent"]["issues"].append(
                    "Too many dependencies may indicate coupling"
                )
                validation["recommendations"].append(
                    "Consider breaking down into smaller, more independent stories"
                )

            # Valuable: Check for business value indication
            story = requirements.get("original_story", {})
            description = story.get("description", "")
            if not story.get("business_value") and len(description) < 20:
                validation["invest_criteria"]["valuable"]["score"] = 0.3
                validation["invest_criteria"]["valuable"]["issues"].append(
                    "Business value and description both missing or inadequate"
                )
                validation["recommendations"].append(
                    "Add clear business value and detailed user story description"
                )
            elif not story.get("business_value"):
                validation["invest_criteria"]["valuable"]["score"] = 0.5
                validation["invest_criteria"]["valuable"]["issues"].append(
                    "Business value not clearly articulated"
                )
                validation["recommendations"].append(
                    "Add clear business value or user benefit statement"
                )

            # Estimable: Check for sufficient detail
            functional_reqs = requirements.get("functional_requirements", [])
            if len(functional_reqs) == 0:
                validation["invest_criteria"]["estimable"]["score"] = 0.2
                validation["invest_criteria"]["estimable"]["issues"].append(
                    "No functional requirements provided"
                )
                validation["recommendations"].append("Add at least 2-3 functional requirements")
            elif len(functional_reqs) < 2:
                validation["invest_criteria"]["estimable"]["score"] = 0.4
                validation["invest_criteria"]["estimable"]["issues"].append(
                    "Insufficient functional requirements for estimation"
                )

            # Small: Check complexity indicators
            total_reqs = len(functional_reqs) + len(
                requirements.get("non_functional_requirements", [])
            )
            if total_reqs > 10:
                validation["invest_criteria"]["small"]["score"] = 0.4
                validation["invest_criteria"]["small"]["issues"].append(
                    "Story may be too large with many requirements"
                )
                validation["recommendations"].append("Consider splitting into multiple stories")

            # Testable: Check for acceptance criteria
            acceptance_criteria = requirements.get("acceptance_criteria", [])
            if not acceptance_criteria:
                validation["invest_criteria"]["testable"]["score"] = 0.0
                validation["invest_criteria"]["testable"]["issues"].append(
                    "Missing acceptance criteria"
                )
                validation["recommendations"].append("Add specific, testable acceptance criteria")
                validation["is_valid"] = False
            elif len(acceptance_criteria) < 2:
                validation["invest_criteria"]["testable"]["score"] = 0.5
                validation["invest_criteria"]["testable"]["issues"].append(
                    "Limited acceptance criteria coverage"
                )

            # Check SMART criteria

            # Specific: Check for detailed requirements
            if not functional_reqs:
                validation["smart_criteria"]["specific"]["score"] = 0.2
                validation["smart_criteria"]["specific"]["issues"].append(
                    "No functional requirements provided - cannot be specific"
                )
            elif len(str(requirements.get("functional_requirements", ""))) < 100:
                validation["smart_criteria"]["specific"]["score"] = 0.4
                validation["smart_criteria"]["specific"]["issues"].append(
                    "Requirements lack sufficient detail"
                )

            # Measurable: Check for quantifiable criteria
            nf_reqs = requirements.get("non_functional_requirements", [])
            measurable_found = any(
                "%" in str(req) or "seconds" in str(req) or "users" in str(req) for req in nf_reqs
            )
            if not measurable_found and nf_reqs:
                validation["smart_criteria"]["measurable"]["score"] = 0.7
                validation["smart_criteria"]["measurable"]["issues"].append(
                    "Non-functional requirements could be more quantifiable"
                )

            # Apply compound penalty for multiple critical issues
            critical_issues = 0
            if validation["invest_criteria"]["testable"]["score"] <= 0.1:  # No acceptance criteria
                critical_issues += 1
            if (
                validation["invest_criteria"]["estimable"]["score"] <= 0.3
            ):  # No/few functional requirements
                critical_issues += 1
            if validation["smart_criteria"]["specific"]["score"] <= 0.3:  # Not specific enough
                critical_issues += 1
            if validation["invest_criteria"]["valuable"]["score"] <= 0.4:  # Poor business value
                critical_issues += 1

            # Calculate overall score
            invest_scores = [
                criteria["score"] for criteria in validation["invest_criteria"].values()
            ]
            smart_scores = [criteria["score"] for criteria in validation["smart_criteria"].values()]
            base_score = (sum(invest_scores) + sum(smart_scores)) / (
                len(invest_scores) + len(smart_scores)
            )

            # Apply compound penalty: 10% reduction per critical issue beyond the first
            compound_penalty = max(0, (critical_issues - 1) * 0.1)
            validation["overall_score"] = max(0.0, base_score - compound_penalty)

            # Final validation
            if validation["overall_score"] < 0.7:
                validation["is_valid"] = False
                validation["recommendations"].append(
                    "Requirements need significant improvement before implementation"
                )

            return validation

        except Exception as e:
            logger.error(f"Error validating requirements: {e}")
            return {
                "is_valid": False,
                "error": str(e),
                "overall_score": 0.0,
                "recommendations": ["Requirements validation failed - please review and resubmit"],
            }
