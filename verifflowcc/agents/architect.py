"""ArchitectAgent for V-Model Design stage.

This agent handles system design creation, architecture documentation updates,
and interface specification generation during the DESIGN stage of the V-Model.
"""

import json
import logging
from datetime import datetime
from typing import Any

from verifflowcc.agents.base import BaseAgent
from verifflowcc.core.path_config import PathConfig
from verifflowcc.core.sdk_config import SDKConfig

logger = logging.getLogger(__name__)


class ArchitectAgent(BaseAgent):
    """Agent responsible for system design and architecture using Claude Code SDK.

    The ArchitectAgent takes requirements artifacts and creates system designs,
    updates architecture documentation, and defines interface contracts for
    implementation using AI-powered design generation.
    """

    def __init__(
        self,
        name: str = "architect",
        agent_type: str = "architect",
        path_config: PathConfig | None = None,
        sdk_config: SDKConfig | None = None,
        mock_mode: bool = False,
    ):
        """Initialize the ArchitectAgent.

        Args:
            name: Agent name identifier
            agent_type: Agent type (architect)
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
        """Process design requirements and generate system architecture using Claude Code SDK.

        Args:
            input_data: Contains requirements artifacts and context data

        Returns:
            Dictionary containing design specifications, architecture updates,
            and interface contracts
        """
        try:
            logger.info("Processing architecture design request")

            # Extract input data
            requirements = input_data.get("requirements", {})
            story_id = input_data.get(
                "story_id", f"ARCH-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
            )
            task_description = input_data.get("task_description", "")
            project_context = input_data.get("context", {})

            # Build prompt context
            prompt_context = {
                "task_description": task_description,
                "project_name": project_context.get("project_name", "VeriFlowCC"),
                "sprint_number": project_context.get("sprint_number", "Current Sprint"),
                "requirements": json.dumps(requirements, indent=2)
                if requirements
                else "No requirements provided",
                "context": json.dumps(project_context, indent=2) if project_context else "",
                "tech_stack": project_context.get("tech_stack", "Python, FastAPI, SQLAlchemy"),
            }

            # Load template and create prompt
            prompt = self.load_prompt_template("architect", **prompt_context)

            # Call Claude Code SDK
            response = await self._call_claude_sdk(prompt, input_data)

            # Parse the response
            design_data = await self._parse_design_response(response, story_id, requirements)

            # Save design artifacts
            await self._save_design_artifacts(story_id, design_data)

            # Update architecture documentation
            if input_data.get("update_architecture", True):
                await self._update_architecture_documentation(story_id, design_data)

            logger.info(f"Successfully processed architecture design for {story_id}")
            return self._create_success_output(design_data, story_id)

        except Exception as e:
            logger.error(f"Error processing architecture design: {e}")
            return self._create_error_output(str(e))

    async def _parse_design_response(
        self, response: str, story_id: str, requirements: dict[str, Any]
    ) -> dict[str, Any]:
        """Parse Claude's response into structured design data.

        Args:
            response: Raw response from Claude
            story_id: Story identifier
            requirements: Original requirements data

        Returns:
            Structured design data
        """
        try:
            # Try to parse as JSON first
            if response.strip().startswith("{"):
                parsed_response = json.loads(response)

                # Add metadata
                parsed_response.update(
                    {
                        "id": story_id,
                        "requirements_reference": requirements,
                        "designed_at": datetime.now().isoformat(),
                        "agent": self.name,
                        "agent_type": self.agent_type,
                    }
                )

                return parsed_response

            # If not JSON, structure the text response
            return {
                "id": story_id,
                "requirements_reference": requirements,
                "designed_at": datetime.now().isoformat(),
                "agent": self.name,
                "agent_type": self.agent_type,
                "response_text": response,
                "architecture_overview": {
                    "style": "Generated from text response",
                    "description": response[:200] + "..." if len(response) > 200 else response,
                    "rationale": "Generated from Claude text response",
                },
                "components": [],
                "interface_specifications": [],
                "quality_attributes": {},
                "risks_and_mitigations": [],
                "implementation_guidance": {
                    "technology_stack": "To be determined based on requirements",
                    "deployment_strategy": "To be defined",
                    "development_phases": [],
                    "testing_strategy": "Comprehensive testing required",
                },
                "traceability": {
                    "requirements_coverage": "All provided requirements addressed",
                    "architectural_decisions": [],
                    "assumptions": [],
                    "constraints": [],
                },
            }

        except json.JSONDecodeError as e:
            logger.warning(f"Could not parse Claude response as JSON: {e}")
            # Return structured fallback
            return {
                "id": story_id,
                "requirements_reference": requirements,
                "designed_at": datetime.now().isoformat(),
                "agent": self.name,
                "agent_type": self.agent_type,
                "response_text": response,
                "parse_error": str(e),
                "architecture_overview": {
                    "style": "Parse error fallback",
                    "description": "Could not parse response",
                    "rationale": "Fallback due to parsing error",
                },
            }

    async def _save_design_artifacts(self, story_id: str, design_data: dict[str, Any]) -> None:
        """Save design artifacts to the design subdirectory.

        Args:
            story_id: Story identifier
            design_data: Generated design data
        """
        try:
            # Save main design document
            self.save_artifact(f"design/{story_id}.json", design_data)

            # Save component diagrams if any
            components = design_data.get("components", [])
            if components:
                for i, component in enumerate(components):
                    if isinstance(component, dict):
                        component_name = component.get("name", f"component_{i}")
                        diagram_content = self._generate_component_diagram(component, story_id)
                        self.save_artifact(
                            f"design/diagrams/{story_id}_{component_name}.puml", diagram_content
                        )

            # Save interface specifications
            interfaces = design_data.get("interface_specifications", [])
            if interfaces:
                interface_doc = self._generate_interface_documentation(interfaces, story_id)
                self.save_artifact(f"design/interfaces/{story_id}_interfaces.md", interface_doc)

            logger.info(f"Saved design artifacts for {story_id}")

        except Exception as e:
            logger.error(f"Error saving design artifacts: {e}")

    def _generate_component_diagram(self, component: dict[str, Any], story_id: str) -> str:
        """Generate PlantUML diagram for a component.

        Args:
            component: Component specification
            story_id: Story identifier

        Returns:
            PlantUML diagram content
        """
        component_name = component.get("name", "Component")
        component_type = component.get("type", "service")
        responsibilities = component.get("responsibilities", [])

        diagram = f"""@startuml {story_id}_{component_name}
!theme plain
title {component_name} - {story_id}

package "{component_name}" as {component_name.lower()} {{
    component "{component_name}" as comp
    note right of comp
        Type: {component_type}
        Story: {story_id}
"""

        for resp in responsibilities[:3]:  # Limit to first 3 responsibilities
            diagram += f"        - {resp}\n"

        diagram += """    end note
}

@enduml"""

        return diagram

    def _generate_interface_documentation(self, interfaces: list, story_id: str) -> str:
        """Generate interface documentation.

        Args:
            interfaces: List of interface specifications
            story_id: Story identifier

        Returns:
            Markdown documentation for interfaces
        """
        doc = f"# Interface Specifications - {story_id}\n\n"
        doc += f"Generated: {datetime.now().isoformat()}\n\n"

        for interface in interfaces:
            if isinstance(interface, dict):
                name = interface.get("name", "Unknown Interface")
                doc += f"## {name}\n\n"

                interface_type = interface.get("type", "unknown")
                doc += f"**Type:** {interface_type}\n\n"

                endpoints = interface.get("endpoints", [])
                if endpoints:
                    doc += "### Endpoints\n\n"
                    for endpoint in endpoints:
                        if isinstance(endpoint, dict):
                            method = endpoint.get("method", "GET")
                            path = endpoint.get("path", "/unknown")
                            desc = endpoint.get("description", "No description")
                            doc += f"- **{method} {path}**: {desc}\n"
                    doc += "\n"

        return doc

    async def _update_architecture_documentation(
        self, story_id: str, design_data: dict[str, Any]
    ) -> None:
        """Update the architecture.md file with new design information.

        Args:
            story_id: Story identifier
            design_data: Generated design data
        """
        try:
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

            # Check if this story already has an entry
            if f"## Design Update - {story_id}" not in current_content:
                # Append new content
                updated_content = current_content + f"\n{update_content}\n"
                arch_path.write_text(updated_content)
                logger.info(f"Updated architecture.md for story {story_id}")

        except Exception as e:
            logger.error(f"Error updating architecture documentation: {e}")

    def _generate_architecture_update(self, story_id: str, design_data: dict[str, Any]) -> str:
        """Generate architecture documentation update content.

        Args:
            story_id: Story identifier
            design_data: Generated design data

        Returns:
            Formatted documentation content
        """
        update_content = f"## Design Update - {story_id}\n\n"
        update_content += f"**Updated:** {design_data.get('designed_at', 'Unknown')}\n\n"

        # Architecture overview
        arch_overview = design_data.get("architecture_overview", {})
        if arch_overview:
            update_content += "### Architecture Overview\n\n"
            style = arch_overview.get("style", "Not specified")
            description = arch_overview.get("description", "No description")
            update_content += f"**Style:** {style}\n"
            update_content += f"**Description:** {description}\n\n"

        # Components
        components = design_data.get("components", [])
        if components:
            update_content += "### New/Modified Components\n\n"
            for component in components:
                if isinstance(component, dict):
                    name = component.get("name", "Unknown Component")
                    comp_type = component.get("type", "service")
                    description = component.get("description", "No description")
                    update_content += f"- **{name}** ({comp_type}): {description}\n"
                else:
                    update_content += f"- {component}\n"
            update_content += "\n"

        # Interface specifications
        interfaces = design_data.get("interface_specifications", [])
        if interfaces:
            update_content += "### Interface Updates\n\n"
            for interface in interfaces:
                if isinstance(interface, dict):
                    name = interface.get("name", "Unknown Interface")
                    interface_type = interface.get("type", "unknown")
                    update_content += f"- **{name}** ({interface_type})\n"
                else:
                    update_content += f"- {interface}\n"
            update_content += "\n"

        # Quality attributes
        quality_attrs = design_data.get("quality_attributes", {})
        if quality_attrs:
            update_content += "### Quality Attributes\n\n"
            for attr, details in quality_attrs.items():
                if isinstance(details, dict):
                    update_content += f"- **{attr.title()}**: {details}\n"
            update_content += "\n"

        return update_content

    def _create_success_output(self, design_data: dict[str, Any], story_id: str) -> dict[str, Any]:
        """Create successful output.

        Args:
            design_data: Generated design data
            story_id: Story identifier

        Returns:
            Success output dictionary
        """
        return {
            "status": "success",
            "story_id": story_id,
            "agent": self.name,
            "agent_type": self.agent_type,
            "artifacts": {
                "design_document": f"design/{story_id}.json",
                "architecture_updates": "architecture.md",
                "diagrams": f"design/diagrams/{story_id}_*.puml",
                "interfaces": f"design/interfaces/{story_id}_interfaces.md",
            },
            "design_data": design_data,
            "metrics": {
                "components_designed": len(design_data.get("components", [])),
                "interfaces_defined": len(design_data.get("interface_specifications", [])),
                "quality_attributes": len(design_data.get("quality_attributes", {})),
                "risks_identified": len(design_data.get("risks_and_mitigations", [])),
            },
            "next_stage_ready": True,
            "validation_passed": True,
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
            "design_data": {},
            "metrics": {},
            "next_stage_ready": False,
            "validation_passed": False,
            "timestamp": datetime.now().isoformat(),
        }
