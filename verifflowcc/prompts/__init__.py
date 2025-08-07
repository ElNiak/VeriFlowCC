"""Jinja2 prompt templates for AI agents."""

from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, Template

# Set up Jinja2 environment
PROMPTS_DIR = Path(__file__).parent
env = Environment(
    loader=FileSystemLoader(PROMPTS_DIR),
    trim_blocks=True,
    lstrip_blocks=True,
    keep_trailing_newline=True,
)


def render_template(template_name: str, context: dict[str, Any]) -> str:
    """Render a Jinja2 template with the given context.

    Args:
        template_name: Name of the template file (e.g., 'planner.jinja2')
        context: Dictionary of variables to pass to the template

    Returns:
        Rendered template as a string
    """
    template = env.get_template(template_name)
    return template.render(**context)


def get_template(template_name: str) -> Template:
    """Get a Jinja2 template object.

    Args:
        template_name: Name of the template file

    Returns:
        Jinja2 Template object
    """
    return env.get_template(template_name)


# Convenience functions for specific templates
def render_planner_prompt(user_story: str, context: str = "", **kwargs) -> str:
    """Render the planner agent prompt."""
    return render_template(
        "planner.jinja2", {"user_story": user_story, "context": context, **kwargs}
    )


def render_design_prompt(requirements: list, design_outline: str = "", **kwargs) -> str:
    """Render the design agent prompt."""
    return render_template(
        "design.jinja2",
        {"requirements": requirements, "design_outline": design_outline, **kwargs},
    )


def render_coding_prompt(task: dict, design: str, file_context: str = "", **kwargs) -> str:
    """Render the coding agent prompt."""
    return render_template(
        "coding.jinja2", {"task": task, "design": design, "file_context": file_context, **kwargs}
    )


def render_testing_prompt(code: str, requirements: list, test_output: str = "", **kwargs) -> str:
    """Render the testing agent prompt."""
    return render_template(
        "testing.jinja2",
        {"code": code, "requirements": requirements, "test_output": test_output, **kwargs},
    )


def render_validation_prompt(
    feature_name: str, acceptance_criteria: list, implementation_summary: str, **kwargs
) -> str:
    """Render the validation agent prompt."""
    return render_template(
        "validation.jinja2",
        {
            "feature_name": feature_name,
            "acceptance_criteria": acceptance_criteria,
            "implementation_summary": implementation_summary,
            **kwargs,
        },
    )
