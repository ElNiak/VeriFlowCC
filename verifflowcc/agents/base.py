"""Base Agent class for VeriFlowCC subagents."""

import json
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from verifflowcc.core.path_config import PathConfig


class BaseAgent(ABC):
    """Base class for all VeriFlowCC subagents."""

    def __init__(
        self,
        name: str,
        model: str = "claude-3-sonnet",
        max_tokens: int = 4000,
        config_path: Path | None = None,
        path_config: PathConfig | None = None,
    ):
        """Initialize the base agent.

        Args:
            name: Agent name identifier
            model: Claude model to use
            max_tokens: Maximum tokens for responses
            config_path: Path to configuration file (deprecated, use path_config)
            path_config: PathConfig instance for managing project paths
        """
        self.name = name
        self.model = model
        self.max_tokens = max_tokens
        self.path_config = path_config or PathConfig()
        self.config_path = config_path or self.path_config.config_path
        self.context: dict[str, Any] = {}

    @abstractmethod
    async def process(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """Process input and return structured output.

        Args:
            input_data: Input data for the agent

        Returns:
            Structured output from the agent
        """
        pass

    def load_prompt_template(self, template_name: str) -> str:
        """Load a Jinja2 template from the prompts directory.

        Args:
            template_name: Name of the template file

        Returns:
            Template content as string
        """
        template_path = Path("verifflowcc/prompts") / f"{template_name}.j2"
        if template_path.exists():
            return template_path.read_text()
        return ""

    def save_artifact(self, artifact_name: str, content: Any) -> None:
        """Save an artifact to the .agilevv directory.

        Args:
            artifact_name: Name of the artifact
            content: Content to save
        """
        artifact_path = self.path_config.base_dir / artifact_name
        artifact_path.parent.mkdir(parents=True, exist_ok=True)

        if isinstance(content, dict):
            artifact_path.write_text(json.dumps(content, indent=2))
        else:
            artifact_path.write_text(str(content))

    def load_artifact(self, artifact_name: str) -> Any:
        """Load an artifact from the .agilevv directory.

        Args:
            artifact_name: Name of the artifact

        Returns:
            Artifact content
        """
        artifact_path = self.path_config.base_dir / artifact_name
        if artifact_path.exists():
            content = artifact_path.read_text()
            if artifact_name.endswith(".json"):
                return json.loads(content)
            return content
        return None

    async def execute(self, **kwargs: Any) -> dict[str, Any]:
        """Execute the agent with given parameters.

        Args:
            **kwargs: Parameters for agent execution

        Returns:
            Agent execution results
        """
        try:
            result = await self.process(kwargs)
            return {"status": "success", "agent": self.name, "result": result}
        except Exception as e:
            return {"status": "error", "agent": self.name, "error": str(e)}
