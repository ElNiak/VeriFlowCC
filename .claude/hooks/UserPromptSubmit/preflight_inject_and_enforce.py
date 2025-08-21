# .claude/hooks/preflight_inject_and_enforce.py
#!/usr/bin/env python3
"""
Purpose:
- Inject AgileVerifFlowCC Pre-Flight Rules into Claude Code's context (UserPromptSubmit).
- Block TodoWrite if the rules were not injected yet (PreToolUse with matcher TodoWrite).

Mechanics:
- For UserPromptSubmit: print the preflight file to stdout => added to context automatically.
- For PreToolUse(TodoWrite): scan transcript for the PRE_FLIGHT_MARKER; if missing, block with exit 2 and instruct Claude to add the rules, then retry.
"""
import json
import os
import sys


def read_json_stdin():
    try:
        return json.load(sys.stdin)
    except Exception as e:
        print(f"Hook error: invalid JSON on stdin ({e})", file=sys.stderr)
        sys.exit(1)


def read_file(path):
    try:
        with open(path, encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return ""


def transcript_contains_marker(transcript_path, marker):
    if not transcript_path or not os.path.exists(transcript_path):
        return False
    found = False
    try:
        with open(transcript_path, encoding="utf-8") as f:
            for line in f:
                if marker in line:
                    found = True
                    break
    except Exception:
        return False
    return found


def main():
    data = read_json_stdin()
    event = data.get("hook_event_name", "")
    tool_name = data.get("tool_name", "")
    project_dir = os.environ.get("CLAUDE_PROJECT_DIR", os.getcwd())
    preflight_path = os.path.join(
        project_dir, ".claude", "instructions", "meta", "pre-flight.md"
    )
    marker = "PRE_FLIGHT_MARKER: AgileVerifFlowCC v1.0"

    if event == "UserPromptSubmit":
        content = read_file(preflight_path).strip()
        if content:
            # stdout is injected into context for UserPromptSubmit
            print(content)
            sys.exit(0)
        else:
            # Not fatal, proceed without injection
            sys.exit(0)

    if event == "PreToolUse" and tool_name == "TodoWrite":
        transcript_path = data.get("transcript_path", "")
        if transcript_contains_marker(transcript_path, marker):
            sys.exit(0)
        else:
            # Exit code 2 blocks tool call; stderr is fed back to Claude to fix automatically
            err = (
                "❌ Pre-Flight not loaded. Before using TodoWrite, add the AgileVerifFlowCC "
                "Pre-Flight Rules to context by echoing the exact contents of "
                "`.claude/instructions/meta/pre-flight.md`, then retry TodoWrite."
            )
            print(err, file=sys.stderr)
            sys.exit(2)

    # Default: do nothing
    sys.exit(0)


if __name__ == "__main__":
    main()
