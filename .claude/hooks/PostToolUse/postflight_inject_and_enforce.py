# .claude/hooks/postflight_inject_and_enforce.py
#!/usr/bin/env python3
# Purpose: PostToolUse hook that, when a process/todo appears complete, triggers a Post-Flight self-audit per AgileVerifFlowCC rules and surfaces a concise checklist to Claude.

import json
import os
import re
import sys
from typing import Any

DONE_HINTS = (
    "all tasks completed",
    "todos complete",
    "process_flow completed",
    "process flow completed",
    '"completed"',
)

SUBAGENT_PATTERN = re.compile(r'subagent\s*=\s*"([^"]+)"', re.IGNORECASE)
STEP_HDR = re.compile(r"\b(step|étape)\s*(\d+)\b", re.IGNORECASE)


def _read_json() -> dict[str, Any]:
    try:
        return json.load(sys.stdin)
    except Exception as e:
        print(f"[postflight] Invalid JSON: {e}", file=sys.stderr)
        sys.exit(1)


def _stringify(obj: Any) -> str:
    try:
        return json.dumps(obj, ensure_ascii=False).lower()
    except Exception:
        return str(obj).lower()


def response_looks_done(tool_resp: Any) -> bool:
    s = _stringify(tool_resp)
    # Heuristic: absence of pending/in_progress + presence of “completed”/phrases
    if any(k in s for k in ('"pending"', '"in_progress"')):
        return False
    return any(h in s for h in DONE_HINTS)


def load_file(path: str) -> str:
    try:
        with open(path, encoding="utf-8") as f:
            return f.read()
    except Exception:
        return ""


def grep_subagents(text: str) -> list[str]:
    return list({m.group(1).strip() for m in SUBAGENT_PATTERN.finditer(text)})


def grep_steps(text: str) -> list[str]:
    steps = []
    for m in STEP_HDR.finditer(text):
        steps.append(m.group(2))
    # Keep order while deduping
    seen, out = set(), []
    for x in steps:
        if x not in seen:
            seen.add(x)
            out.append(x)
    return out


def transcript_paths(payload: dict[str, Any]) -> list[str]:
    # Claude Code usually passes transcript_path; keep extensible
    paths = []
    tp = payload.get("transcript_path")
    if tp and os.path.exists(tp):
        paths.append(tp)
    # Fallback: known session logs (optional)
    for env_key in ("CLAUDE_TRANSCRIPT", "SESSION_LOG"):
        p = os.environ.get(env_key)
        if p and os.path.exists(p):
            paths.append(p)
    return paths


def slurp(paths: list[str]) -> str:
    buf = []
    for p in paths:
        try:
            with open(p, encoding="utf-8", errors="ignore") as f:
                buf.append(f.read())
        except Exception:
            continue
    return "\n".join(buf)


def precheck_findings(instructions_text: str, transcript_text: str) -> dict[str, Any]:
    req_subagents = grep_subagents(instructions_text)
    seen_subagents = []
    for name in req_subagents:
        # crude evidence of delegation; adapt to your logs if you have stable markers
        pat = re.compile(
            rf"\b(subagent|using subagent|delegate[d]?)\b.*\b{name}\b", re.IGNORECASE
        )
        if pat.search(transcript_text):
            seen_subagents.append(name)
    missing_subagents = [s for s in req_subagents if s not in seen_subagents]

    instr_steps = grep_steps(instructions_text)
    # simple delivered/evidence heuristic
    delivered = []
    for step in instr_steps:
        # look for a section marking output for that step
        pat = re.compile(
            rf"(step\s*{step}\b.*?)(delivered|output|result|commit)\b",
            re.IGNORECASE | re.DOTALL,
        )
        if pat.search(transcript_text):
            delivered.append(step)
    missing_steps = [s for s in instr_steps if s not in delivered]

    return {
        "required_subagents": req_subagents,
        "missing_subagents_evidence": missing_subagents,
        "instruction_steps": instr_steps,
        "steps_without_delivery_evidence": missing_steps,
    }


def main():
    data = _read_json()
    if data.get("hook_event_name") != "PostToolUse":
        sys.exit(0)

    tool_name = data.get("tool_name", "")
    tool_resp = data.get("tool_response", {})
    cwd = data.get("cwd", os.getcwd())

    # Only run when it *looks* complete after tools likely to end a flow
    likely_finish_tools = {"TodoWrite", "Task", "Write", "Edit", "MultiEdit"}
    if tool_name not in likely_finish_tools or not response_looks_done(tool_resp):
        sys.exit(0)

    # Load rules + transcript for a light pre-audit
    rules_path = os.path.join(cwd, "instructions", "agentos-postflight.md")
    rules_text = load_file(rules_path)
    transcript_text = slurp(transcript_paths(data))

    findings = precheck_findings(rules_text, transcript_text)

    # Emit a compact pre-audit hint to stderr (shown to Claude if needed)
    print(
        "[postflight] Candidate completion detected → prompting audit.", file=sys.stderr
    )
    if findings.get("missing_subagents_evidence") or findings.get(
        "steps_without_delivery_evidence"
    ):
        print(
            f"[postflight] Precheck: {json.dumps(findings, ensure_ascii=False)}",
            file=sys.stderr,
        )

    # Ask Claude to perform the human-grade audit per your rules (block to show prompt)
    audit_prompt = f"""
📋 AgileVerifFlowCC Post-Flight Audit

Use the following rules to self-audit the just-completed flow, then report succinctly:

{rules_text}

If you find deviations, explain *which instruction* was misread/skipped, why it likely happened, and the corrective action.
If a step had subagent="…", verify the subagent was actually used; if not, investigate and report the reason.

(Precheck hints — optional to use): {json.dumps(findings, ensure_ascii=False)}
""".strip()

    print(json.dumps({"decision": "block", "reason": audit_prompt}))
    sys.exit(0)


if __name__ == "__main__":
    main()
