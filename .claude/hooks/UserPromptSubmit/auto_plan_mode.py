#!/usr/bin/env python3
"""
Purpose:
- Inject auto-plan-mode.md context when specific Claude commands are detected in prompts.
- Triggers for: /analyze-product.md, /plan-product.md, /create-spec.md, /create-tasks.md

Mechanics:
- For UserPromptSubmit: Check if command patterns are in prompt, if yes, print auto-plan-mode.md to stdout => added to context automatically.
"""
import json
import os
import re
import sys
from pathlib import Path


def read_json_stdin():
    try:
        return json.load(sys.stdin)
    except Exception as e:
        print(f"Hook error: invalid JSON on stdin ({e})", file=sys.stderr)
        sys.exit(1)


def read_file(path):
    try:
        with Path(path).open(encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return ""


def contains_command_patterns(prompt):
    """Check if prompt contains any of the target command patterns."""
    command_patterns = [
        r"/analyze-product\.md",
        r"/plan-product\.md",
        r"/create-spec\.md",
        r"/create-tasks\.md",
    ]

    return any(
        re.search(pattern, prompt, re.IGNORECASE) for pattern in command_patterns
    )


def main():
    data = read_json_stdin()
    event = data.get("hook_event_name", "")

    if event != "UserPromptSubmit":
        # This hook only handles UserPromptSubmit
        sys.exit(0)

    # Get the user prompt from the event data
    prompt = data.get("prompt", "")

    # Check if any commands are detected
    if not contains_command_patterns(prompt):
        sys.exit(0)

    # Get the path to auto-plan-mode.md
    project_dir = os.environ.get("CLAUDE_PROJECT_DIR", str(Path.cwd()))
    auto_plan_path = (
        Path(project_dir) / ".claude" / "instructions" / "meta" / "auto-plan-mode.md"
    )

    # Read and inject the content
    content = read_file(auto_plan_path).strip()
    if content:
        # Add marker for tracking
        marker = "AUTO_PLAN_MODE_MARKER: AgileVerifFlowCC"
        output = f"\n{marker}\n\n# Auto Plan Mode Context\n\n{content}\n"

        # stdout is injected into context for UserPromptSubmit
        print(output)
        sys.exit(0)
    else:
        # Not fatal if file doesn't exist, proceed without injection
        print(
            f"Warning: auto-plan-mode.md not found at {auto_plan_path}", file=sys.stderr
        )
        sys.exit(0)


if __name__ == "__main__":
    main()
