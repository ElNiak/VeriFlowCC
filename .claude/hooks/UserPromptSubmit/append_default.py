# tools/hooks/prompt_gate.py
# Purpose: Validate/shape user prompts before Claude processes them; inject guardrails & helpful context.

from __future__ import annotations

import json
import os
import re
import sys

BYPASS_ENV = "CLAUDE_PROMPT_GATE_BYPASS"

# Examples: add your own org rules
BANNED_PATTERNS = [
    r"\brm\s+-rf\s+/\b",
    r"--no-verify\b",
    r"\bskip tests\b",
]
REQUIRE_TOKENS = [r"\bV\s*=\s*[1-3]\b"]  # your “verbosity” convention

GUIDELINES = """\
ALWAYS ULTRA THINK BEFORE AND THINK STEP BY STEP.
"""


def deny(msg: str) -> int:
    sys.stderr.write(f"❌ Prompt blocked by policy:\n{msg}\n")
    return 2  # blocks and clears the prompt


def main() -> int:
    try:
        env = json.load(sys.stdin)
    except Exception:
        return 0  # fail-open: do not block if envelope missing

    if os.getenv(BYPASS_ENV) == "1":
        print(GUIDELINES)
        return 0

    prompt = (env or {}).get("prompt", "") or ""

    # Block obviously dangerous or disallowed instructions
    for rx in BANNED_PATTERNS:
        if re.search(rx, prompt, flags=re.IGNORECASE):
            return deny(f"Matched forbidden pattern: {rx}")

    # Nudge: enforce your house style (e.g., V= level)
    missing = [rx for rx in REQUIRE_TOKENS if not re.search(rx, prompt)]
    if missing:
        # Do not block—just inject guidance to context so Claude adapts.
        print(f"{GUIDELINES}\nNote: Consider adding V=1..3 for this prompt.")
        return 0

    # Happy path: inject helpful context anyway
    print(GUIDELINES)
    return 0


if __name__ == "__main__":
    sys.exit(main())
