"""ArchitectAgent for V-Model Design stage.

This agent handles system design creation, architecture documentation updates,
and interface specification generation during the DESIGN stage of the V-Model.
"""

import json
import logging
from pathlib import Path
from typing import Any

from verifflowcc.agents.base import BaseAgent
from verifflowcc.schemas.agent_schemas import DesignInput

logger = logging.getLogger(__name__)


class ArchitectAgent(BaseAgent):
    """Agent responsible for system design and architecture in the V-Model DESIGN stage.

    The ArchitectAgent takes requirements artifacts from the RequirementsAnalyst
    and creates system designs, updates architecture documentation, and defines
    interface contracts for the implementation phase.
    """

    def __init__(
        self,
        name: str = "architect",
        model: str = "claude-3-sonnet",
        max_tokens: int = 4000,
        config_path: Path | None = None,
        path_config=None,
    ):
        """Initialize the ArchitectAgent.

        Args:
            name: Agent name identifier
            model: Claude model to use for design generation
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
        """Process design requirements and generate system architecture.

        Args:
            input_data: Dictionary containing DesignInput data

        Returns:
            Dictionary containing DesignOutput data with design specifications,
            architecture updates, and interface contracts
        """
        try:
            # Validate input using Pydantic schema
            try:
                design_input = DesignInput(**input_data)
            except Exception as e:
                logger.error(f"Input validation failed: {e}")
                return self._create_error_output(f"Input validation error: {e!s}")

            logger.info(f"Processing design for story {design_input.story_id}")

            # Extract requirements for design generation
            requirements = design_input.requirements_artifacts
            context = design_input.context
            story_id = design_input.story_id

            # Generate design using Claude API
            try:
                design_response = await self._generate_design(requirements, context, story_id)
            except Exception as e:
                logger.error(f"Design generation failed: {e}")
                return self._create_error_output(f"Design generation error: {e!s}")

            # Save design artifacts
            try:
                await self._save_design_artifacts(story_id, design_response)
            except Exception as e:
                logger.warning(f"Failed to save design artifacts: {e}")
                # Continue with partial success

            # Update architecture.md
            try:
                await self._update_architecture_documentation(story_id, design_response)
            except Exception as e:
                logger.warning(f"Failed to update architecture.md: {e}")
                # Continue with partial success

            # Create successful output
            return self._create_success_output(design_response, story_id)

        except Exception as e:
            logger.error(f"Unexpected error in ArchitectAgent.process: {e}")
            return self._create_error_output(f"Unexpected error: {e!s}")

    async def _generate_design(
        self, requirements: dict[str, Any], context: dict[str, Any], story_id: str
    ) -> dict[str, Any]:
        """Generate system design using Claude API.

        Args:
            requirements: Requirements artifacts from previous stage
            context: Additional context information
            story_id: Story identifier

        Returns:
            Dictionary containing design specifications, architecture updates,
            and interface contracts
        """
        # Prepare prompt for Claude
        prompt = self._build_design_prompt(requirements, context, story_id)

        # Call Claude API (with retry logic)
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = await self._call_claude_api(prompt)
                return self._parse_design_response(response)
            except Exception as e:
                if attempt == max_retries - 1:
                    raise e
                logger.warning(f"API call attempt {attempt + 1} failed: {e}")
                # Add exponential backoff here if needed

    def _build_design_prompt(
        self, requirements: dict[str, Any], context: dict[str, Any], story_id: str
    ) -> str:
        """Build the prompt for Claude API to generate system design.

        Args:
            requirements: Requirements artifacts
            context: Context information
            story_id: Story identifier

        Returns:
            Formatted prompt string for Claude
        """
        # Load template if available
        template = self.load_prompt_template("design")

        if template:
            # Use Jinja2 template if available
            try:
                from jinja2 import Template

                jinja_template = Template(template)
                return jinja_template.render(
                    requirements=requirements, context=context, story_id=story_id
                )
            except ImportError:
                logger.warning("Jinja2 not available, using simple template replacement")

        # Fallback to simple template
        return f"""
You are an experienced software architect. Create a comprehensive system design for the following user story.

Story ID: {story_id}
Requirements: {json.dumps(requirements, indent=2)}
Context: {json.dumps(context, indent=2)}

Please provide a detailed system design that includes:

1. **Design Specifications**:
   - System components and their responsibilities
   - Data models and entities
   - Service interfaces and APIs
   - Integration points

2. **Architecture Updates**:
   - Component diagrams (PlantUML format)
   - Sequence diagrams for key flows
   - Updated system documentation

3. **Interface Contracts**:
   - API endpoint specifications
   - Data transfer object definitions
   - Service interface contracts
   - Database schema updates

Return your response as a JSON object with the following structure:
{{
    "design_specifications": {{
        "components": [...],
        "data_models": [...],
        "services": [...],
        "integration_points": [...]
    }},
    "architecture_updates": {{
        "diagrams": [...],
        "documentation_updates": [...]
    }},
    "interface_contracts": {{
        "api_endpoints": [...],
        "service_interfaces": [...],
        "data_contracts": [...]
    }}
}}

Focus on creating a design that is:
- Scalable and maintainable
- Follows SOLID principles
- Supports the acceptance criteria
- Integrates well with existing system architecture
"""

    async def _call_claude_api(self, prompt: str) -> str:
        """Call Claude API to generate design content.

        Args:
            prompt: The prompt to send to Claude

        Returns:
            Claude's response as a string

        Raises:
            Exception: If API call fails
        """
        # This is a placeholder for the actual Claude API integration
        # In a real implementation, this would use the Anthropic SDK
        logger.info("Calling Claude API for design generation")

        # Mock response for testing
        return json.dumps(
            {
                "design_specifications": {
                    "components": ["UserService", "AuthenticationService", "DatabaseService"],
                    "data_models": ["User", "Session", "Credentials"],
                    "services": ["IUserRepository", "IAuthenticationProvider"],
                    "integration_points": ["Database", "External Auth Provider"],
                },
                "architecture_updates": {
                    "diagrams": ["user_management_component.puml", "authentication_sequence.puml"],
                    "documentation_updates": [
                        "Updated User Service documentation",
                        "Added authentication flow documentation",
                    ],
                },
                "interface_contracts": {
                    "api_endpoints": ["/api/users", "/api/auth/login", "/api/auth/logout"],
                    "service_interfaces": ["IUserService", "IAuthenticationService"],
                    "data_contracts": [
                        "UserDTO",
                        "AuthenticationRequest",
                        "AuthenticationResponse",
                    ],
                },
            }
        )

    def _parse_design_response(self, response: str | dict) -> dict[str, Any]:
        """Parse Claude's response into structured design data.

        Args:
            response: Raw response from Claude API (string) or already parsed dict

        Returns:
            Parsed design data

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
                raise Exception("Could not parse design response as JSON")

    async def _save_design_artifacts(self, story_id: str, design_data: dict[str, Any]) -> None:
        """Save design artifacts to the design subdirectory.

        Args:
            story_id: Story identifier
            design_data: Generated design data
        """
        # Save main design document
        design_artifact = {
            "story_id": story_id,
            "design_specifications": design_data.get("design_specifications", {}),
            "interface_contracts": design_data.get("interface_contracts", {}),
            "generated_at": "2024-01-01T00:00:00Z",  # Would use datetime.now() in real implementation
            "version": "1.0",
        }

        self.save_artifact(f"design/{story_id}.json", design_artifact)

        # Save individual diagrams if any
        diagrams = design_data.get("architecture_updates", {}).get("diagrams", [])
        for diagram in diagrams:
            if isinstance(diagram, str) and diagram.endswith(".puml"):
                # In real implementation, would generate actual PlantUML content
                diagram_content = f"@startuml\n' Diagram for {story_id}\n@enduml"
                self.save_artifact(f"design/diagrams/{diagram}", diagram_content)

    async def _update_architecture_documentation(
        self, story_id: str, design_data: dict[str, Any]
    ) -> None:
        """Update the architecture.md file with new design information.

        Args:
            story_id: Story identifier
            design_data: Generated design data
        """
        arch_path = self.path_config.architecture_path

        # Ensure parent directory exists
        arch_path.parent.mkdir(parents=True, exist_ok=True)

        # Read existing content or create new
        if arch_path.exists():
            current_content = arch_path.read_text()
        else:
            current_content = "# System Architecture\n\n"

        # Generate update content
        update_content = self._generate_architecture_update(story_id, design_data)

        # Append new content
        updated_content = current_content + f"\n{update_content}\n"

        # Write back to file
        arch_path.write_text(updated_content)

        logger.info(f"Updated architecture.md for story {story_id}")

    def _generate_architecture_update(self, story_id: str, design_data: dict[str, Any]) -> str:
        """Generate architecture documentation update content.

        Args:
            story_id: Story identifier
            design_data: Generated design data

        Returns:
            Formatted documentation content
        """
        specifications = design_data.get("design_specifications", {})
        components = specifications.get("components", [])

        update_content = f"## Update for {story_id}\n\n"

        if components:
            update_content += "### New Components\n\n"
            for component in components:
                update_content += f"- **{component}**: Component added for {story_id}\n"
            update_content += "\n"

        interfaces = design_data.get("interface_contracts", {}).get("service_interfaces", [])
        if interfaces:
            update_content += "### Service Interfaces\n\n"
            for interface in interfaces:
                update_content += f"- `{interface}`: Interface contract for {story_id}\n"
            update_content += "\n"

        return update_content

    def _create_success_output(self, design_data: dict[str, Any], story_id: str) -> dict[str, Any]:
        """Create successful DesignOutput.

        Args:
            design_data: Generated design data
            story_id: Story identifier

        Returns:
            Success output dictionary
        """
        return {
            "status": "success",
            "artifacts": {
                "design_document": f"design/{story_id}.json",
                "architecture_updates": "architecture.md",
            },
            "design_specifications": design_data.get("design_specifications", {}),
            "architecture_updates": design_data.get("architecture_updates", {}),
            "interface_contracts": design_data.get("interface_contracts", {}),
            "metrics": {
                "components_designed": len(
                    design_data.get("design_specifications", {}).get("components", [])
                ),
                "interfaces_defined": len(
                    design_data.get("interface_contracts", {}).get("service_interfaces", [])
                ),
                "diagrams_created": len(
                    design_data.get("architecture_updates", {}).get("diagrams", [])
                ),
            },
            "next_stage_ready": True,
            "errors": [],
        }

    def _create_error_output(self, error_message: str) -> dict[str, Any]:
        """Create error DesignOutput.

        Args:
            error_message: Error description

        Returns:
            Error output dictionary
        """
        return {
            "status": "error",
            "artifacts": {},
            "design_specifications": {},
            "architecture_updates": {},
            "interface_contracts": {},
            "metrics": {},
            "next_stage_ready": False,
            "errors": [error_message],
        }
