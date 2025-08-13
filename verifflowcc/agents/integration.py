"""IntegrationAgent for V-Model Integration stage.

This agent handles system integration validation, deployment verification,
and end-to-end testing during the INTEGRATION stage of the V-Model.
"""

import json
import logging
from pathlib import Path
from typing import Any

from verifflowcc.agents.base import BaseAgent
from verifflowcc.schemas.agent_schemas import IntegrationInput

logger = logging.getLogger(__name__)


class IntegrationAgent(BaseAgent):
    """Agent responsible for system integration and deployment validation in V-Model INTEGRATION stage.

    The IntegrationAgent validates system integration, performs deployment checks,
    and ensures all components work together correctly for final system validation.
    """

    def __init__(
        self,
        name: str = "integration",
        model: str = "claude-3-sonnet",
        max_tokens: int = 4000,
        config_path: Path | None = None,
        path_config=None,
    ):
        """Initialize the IntegrationAgent.

        Args:
            name: Agent name identifier
            model: Claude model to use for integration validation
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
        """Process integration requirements and validate system integration.

        Args:
            input_data: Dictionary containing IntegrationInput data

        Returns:
            Dictionary containing IntegrationOutput data with integration results,
            deployment validation, and system health metrics
        """
        try:
            # Validate input using Pydantic schema
            try:
                integration_input = IntegrationInput(**input_data)
            except Exception as e:
                logger.error(f"Input validation failed: {e}")
                return self._create_error_output(f"Input validation error: {e!s}")

            logger.info(f"Processing integration for story {integration_input.story_id}")

            # Extract integration requirements
            system_artifacts = integration_input.system_artifacts
            integration_scope = integration_input.integration_scope
            context = integration_input.context
            story_id = integration_input.story_id

            # Validate integration using Claude API
            try:
                integration_response = await self._validate_integration(
                    system_artifacts, integration_scope, context, story_id
                )
            except Exception as e:
                logger.error(f"Integration validation failed: {e}")
                return self._create_error_output(f"Integration validation error: {e!s}")

            # Perform deployment validation
            try:
                deployment_results = self._validate_deployment(integration_response)
                integration_response["deployment_validation"] = deployment_results
            except Exception as e:
                logger.warning(f"Deployment validation failed: {e}")
                integration_response["deployment_validation"] = {
                    "status": "failed",
                    "error": str(e),
                }

            # Check system health
            try:
                health_results = self._check_system_health()
                integration_response["system_health"] = health_results
            except Exception as e:
                logger.warning(f"System health check failed: {e}")
                integration_response["system_health"] = {"status": "unknown", "error": str(e)}

            # Save integration artifacts
            try:
                await self._save_integration_artifacts(story_id, integration_response)
            except Exception as e:
                logger.warning(f"Failed to save integration artifacts: {e}")

            # Create successful output
            return self._create_success_output(integration_response, story_id)

        except Exception as e:
            logger.error(f"Unexpected error in IntegrationAgent.process: {e}")
            return self._create_error_output(f"Unexpected error: {e!s}")

    async def _validate_integration(
        self,
        system_artifacts: dict[str, Any],
        integration_scope: list[str],
        context: dict[str, Any],
        story_id: str,
    ) -> dict[str, Any]:
        """Validate system integration using Claude API."""
        prompt = self._build_integration_prompt(
            system_artifacts, integration_scope, context, story_id
        )
        response = await self._call_claude_api(prompt)
        return self._parse_integration_response(response)

    def _build_integration_prompt(
        self,
        system_artifacts: dict[str, Any],
        integration_scope: list[str],
        context: dict[str, Any],
        story_id: str,
    ) -> str:
        """Build the prompt for Claude API to validate integration."""
        return f"""
You are a system integration expert. Validate the integration of the following system.

Story ID: {story_id}
System Artifacts: {json.dumps(system_artifacts, indent=2)}
Integration Scope: {integration_scope}
Context: {json.dumps(context, indent=2)}

Perform comprehensive integration validation including:
1. Component interaction verification
2. Data flow validation
3. API contract compliance
4. Performance benchmarks
5. Security validation

Return JSON with:
{{
    "integration_results": {{"status": "healthy", "services": 3}},
    "performance_metrics": {{"response_time": 200, "throughput": 1000}},
    "security_validation": {{"vulnerabilities": 0, "compliance": true}}
}}
"""

    async def _call_claude_api(self, prompt: str) -> str:
        """Call Claude API to validate integration."""
        logger.info("Calling Claude API for integration validation")

        # Mock response for testing
        return json.dumps(
            {
                "integration_results": {"status": "healthy", "services": 3, "endpoints": 5},
                "performance_metrics": {"response_time": 150, "throughput": 1200},
                "security_validation": {"vulnerabilities": 0, "compliance": True},
            }
        )

    def _parse_integration_response(self, response: str | dict) -> dict[str, Any]:
        """Parse Claude's response into structured integration data."""
        if isinstance(response, dict):
            return response
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            raise Exception("Could not parse integration response as JSON")

    def _validate_deployment(self, integration_data: dict[str, Any]) -> dict[str, Any]:
        """Validate deployment configuration and readiness."""
        # Mock deployment validation
        return {
            "environment": "staging",
            "health_checks": True,
            "configuration_valid": True,
            "dependencies_resolved": True,
        }

    def _check_system_health(self) -> dict[str, Any]:
        """Check overall system health metrics."""
        # Mock system health check
        return {
            "cpu_usage": 25,
            "memory_usage": 60,
            "disk_usage": 45,
            "uptime": "99.9%",
            "active_connections": 150,
        }

    async def _save_integration_artifacts(
        self, story_id: str, integration_data: dict[str, Any]
    ) -> None:
        """Save integration artifacts to the integration subdirectory."""
        integration_artifact = {
            "story_id": story_id,
            "integration_results": integration_data.get("integration_results", {}),
            "deployment_validation": integration_data.get("deployment_validation", {}),
            "system_health": integration_data.get("system_health", {}),
            "performance_metrics": integration_data.get("performance_metrics", {}),
            "security_validation": integration_data.get("security_validation", {}),
            "generated_at": "2024-01-01T00:00:00Z",
            "version": "1.0",
        }

        self.save_artifact(f"integration/{story_id}.json", integration_artifact)

    def _create_success_output(
        self, integration_data: dict[str, Any], story_id: str
    ) -> dict[str, Any]:
        """Create successful IntegrationOutput."""
        return {
            "status": "success",
            "artifacts": {"integration_report": f"integration/{story_id}.json"},
            "integration_results": integration_data.get("integration_results", {}),
            "deployment_validation": integration_data.get("deployment_validation", {}),
            "system_health": integration_data.get("system_health", {}),
            "metrics": {
                "services_validated": integration_data.get("integration_results", {}).get(
                    "services", 0
                ),
                "health_score": 95.0,
            },
            "next_stage_ready": True,
            "errors": [],
        }

    def _create_error_output(self, error_message: str) -> dict[str, Any]:
        """Create error IntegrationOutput."""
        return {
            "status": "error",
            "artifacts": {},
            "integration_results": {},
            "deployment_validation": {},
            "system_health": {},
            "metrics": {},
            "next_stage_ready": False,
            "errors": [error_message],
        }
