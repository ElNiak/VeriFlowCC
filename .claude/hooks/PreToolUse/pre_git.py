# tools/hooks/git_policy_guard.py
# Purpose: Enforce safe git usage from Claude-code's Bash tool:
# - Forbid commits with --no-verify/-n (even inside chained commands).
# - Forbid 'git push --force' (incl. '+refspec' force).
# - Gate 'git push --force-with-lease' by branch globs (deny on protected branches by default).
# - Emit a compact JSON decision so Claude can self-correct; exit code 2 blocks the tool call.

from __future__ import annotations

import fnmatch
import json
import os
import re
import shlex
import subprocess
import sys
from pathlib import Path
from typing import Any

# ---------------- Config loading ----------------

DEFAULT_POLICY = {
    "protectedBranches": ["main", "master", "release/*", "hotfix/*", "stable", "prod", "production"],
    "allowForceOn": [],
    "allowForceWithLeaseOn": ["feature/*", "bugfix/*", "chore/*", "refactor/*", "wip/*"],
    "blockNoVerify": True,
}

POLICY_FILE = Path(".claude/git_policy.json")

def _read_json(path: Path) -> dict[str, Any]:
    try:
        if path.is_file():
            return json.loads(path.read_text())
    except Exception:
        pass
    return {}

def load_policy() -> dict[str, Any]:
    policy = dict(DEFAULT_POLICY)
    policy.update(_read_json(POLICY_FILE))

    def env_list(name: str) -> list[str] | None:
        v = os.getenv(name)
        if not v:
            return None
        return [x.strip() for x in v.split(",") if x.strip()]

    if (v := env_list("CLAUDE_PROTECTED_BRANCHES")) is not None:
        policy["protectedBranches"] = v
    if (v := env_list("CLAUDE_ALLOW_FORCE_ON")) is not None:
        policy["allowForceOn"] = v
    if (v := env_list("CLAUDE_ALLOW_FORCE_WITH_LEASE_ON")) is not None:
        policy["allowForceWithLeaseOn"] = v
    if (v := os.getenv("CLAUDE_BLOCK_NO_VERIFY")) is not None:
        policy["blockNoVerify"] = v not in ("0", "false", "False")
    return policy

# ---------------- Utilities ----------------

SEP_TOKENS = {"&&", "||", ";", "|"}

def shlex_split(s: str) -> list[str]:
    try:
        return shlex.split(s)
    except Exception:
        return s.strip().split()

def split_segments(tokens: list[str]) -> list[list[str]]:
    """Split a token list on shell control operators (&&, ||, ;, |)."""
    segs: list[list[str]] = []
    cur: list[str] = []
    for t in tokens:
        if t in SEP_TOKENS:
            if cur:
                segs.append(cur); cur = []
        else:
            cur.append(t)
    if cur:
        segs.append(cur)
    return segs

def run_git(*args: str) -> str | None:
    try:
        out = subprocess.check_output(["git", *args], text=True, stderr=subprocess.DEVNULL)
        return out.strip()
    except Exception:
        return None

def current_branch() -> str | None:
    br = run_git("rev-parse", "--abbrev-ref", "HEAD")
    return br if br and br != "HEAD" else None

def upstream_branch() -> str | None:
    up = run_git("rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}")
    return up

def any_glob_match(name: str, globs: list[str]) -> bool:
    return any(fnmatch.fnmatchcase(name, g) for g in globs)

# ---------------- Detectors ----------------

NO_VERIFY_PATTERNS = (re.compile(r"--no-verify\b"), re.compile(r"(?<!\S)-n(?!\S)"))

def is_git_commit_segment(seg: list[str]) -> bool:
    """Return True if segment looks like a 'git commit ...' invocation (options before/after allowed)."""
    if "git" not in seg or "commit" not in seg:
        return False
    # Ensure 'commit' appears after 'git' (allow options like '-c key=val')
    git_idx = seg.index("git")
    try:
        commit_idx = seg.index("commit", git_idx + 1)
    except ValueError:
        return False
    return commit_idx > git_idx

def commit_has_no_verify(seg: list[str]) -> bool:
    if not is_git_commit_segment(seg):
        return False
    joined = " ".join(seg)
    return any(p.search(joined) for p in NO_VERIFY_PATTERNS)

def is_git_push_segment(seg: list[str]) -> bool:
    if "git" not in seg or "push" not in seg:
        return False
    git_idx = seg.index("git")
    try:
        push_idx = seg.index("push", git_idx + 1)
    except ValueError:
        return False
    return push_idx > git_idx

def contains_force(tokens: list[str]) -> bool:
    return any(t in ("--force", "-f") for t in tokens)

def contains_force_with_lease(tokens: list[str]) -> bool:
    return any(t.startswith("--force-with-lease") for t in tokens)

def contains_plus_refspec(tokens: list[str]) -> bool:
    # e.g., '+main' or '+HEAD:main' among non-flag args
    for t in tokens:
        if t and (not t.startswith("-")) and t.startswith("+"):
            return True
    return False

def target_branches_from_push(seg: list[str]) -> list[str]:
    """
    Parse 'git [opts] push [opts] [<remote>] [<refspec> ...]' for the given segment.
    Return destination branch names.
    """
    try:
        push_idx = seg.index("push")
    except ValueError:
        return []
    tail = seg[push_idx + 1:]

    # Collect non-flag args
    nonflags: list[str] = []
    i = 0
    while i < len(tail):
        t = tail[i]
        if t.startswith("-"):
            # Skip option + optional value for options like "-o val" or "--option=val"
            if i + 1 < len(tail) and not tail[i + 1].startswith("-") and "=" not in t:
                i += 2
            else:
                i += 1
            continue
        nonflags.append(t)
        i += 1

    if not nonflags:
        up = upstream_branch()
        if up and "/" in up:
            return [up.split("/", 1)[1]]
        cb = current_branch()
        return [cb] if cb else []

    # If first looks like remote, skip it; refspecs follow
    refspecs = nonflags[1:] if nonflags else []
    if not refspecs:
        # 'git push origin my-branch' OR 'git push my-branch' (no remote)
        if len(nonflags) == 1:
            return [nonflags[0]]
        return []

    dests: list[str] = []
    for rs in refspecs:
        rs_clean = rs[1:] if rs.startswith("+") else rs
        if ":" in rs_clean:
            _, dst = rs_clean.rsplit(":", 1)
            dests.append(dst)
        else:
            dests.append(rs_clean)
    return dests

# ---------------- Reporting ----------------

def deny(reason: str, message: str, data: dict[str, Any]) -> int:
    payload = {"decision": "deny", "reason": reason, "message": message, "data": data}
    print("BEGIN_HOOK_REPORT")
    print(json.dumps(payload, indent=2))
    print("END_HOOK_REPORT")
    return 2

def allow(reason: str, data: dict[str, Any]) -> int:
    payload = {"decision": "allow", "reason": reason, "data": data}
    print("BEGIN_HOOK_REPORT")
    print(json.dumps(payload, indent=2))
    print("END_HOOK_REPORT")
    return 0

# ---------------- Hook entry ----------------

def main() -> int:
    try:
        env: dict[str, Any] = json.load(sys.stdin)
    except Exception:
        return 0

    if env.get("hook_event_name") != "PreToolUse" or env.get("tool_name") != "Bash":
        return 0

    cmd = (env.get("tool_input") or {}).get("command", "")
    if not cmd:
        return 0

    if os.getenv("CLAUDE_ALLOW_GIT_POLICY_BYPASS") == "1":
        return allow("bypass-env", {"command": cmd})

    tokens = shlex_split(cmd)
    segs = split_segments(tokens)
    policy = load_policy()

    # 1) Block 'git commit --no-verify/-n' in ANY segment
    if policy.get("blockNoVerify", True):
        for seg in segs:
            if commit_has_no_verify(seg):
                msg = (
                    "Commit blocked: `--no-verify` (or `-n`) is not allowed.\n"
                    "Suggested fix:\n"
                    "  • Run format/lint/type checks and address issues\n"
                    "  • Commit without bypass flags\n"
                )
                return deny("commit-no-verify", msg, {"command": cmd, "segment": " ".join(seg)})

    # 2) Gate pushes (force / lease) in ANY segment
    prot = list(policy.get("protectedBranches", []))
    allow_force = list(policy.get("allowForceOn", []))
    allow_lease = list(policy.get("allowForceWithLeaseOn", []))

    for seg in segs:
        if not is_git_push_segment(seg):
            continue

        branches = target_branches_from_push(seg) or [current_branch() or "UNKNOWN"]
        is_force = contains_force(seg) or contains_plus_refspec(seg)
        is_lease = contains_force_with_lease(seg)

        if is_force:
            blocked = any(not any_glob_match(b, allow_force) for b in branches)
            if blocked:
                msg = (
                    "Push blocked: plain `git push --force` (or '+refspec') is disallowed.\n"
                    "Try: `git push --force-with-lease` on a non-protected branch, "
                    "or push without force and open a PR."
                )
                return deny("plain-force", msg, {"command": cmd, "branches": branches, "segment": " ".join(seg),
                                                 "policy": {"allowForceOn": allow_force}})
            # allowed force (rare)
            return allow("plain-force-allowed", {"command": cmd, "branches": branches, "segment": " ".join(seg)})

        if is_lease:
            for b in branches:
                if any_glob_match(b, prot) and not any_glob_match(b, allow_lease):
                    msg = (
                        f"Push blocked: `--force-with-lease` to protected branch '{b}' is disallowed.\n"
                        "Push without force, or create a new branch and open a PR."
                    )
                    return deny("lease-on-protected", msg, {"command": cmd, "branch": b, "segment": " ".join(seg),
                                                            "policy": {"protectedBranches": prot,
                                                                       "allowForceWithLeaseOn": allow_lease}})
            return allow("lease-allowed", {"command": cmd, "branches": branches, "segment": " ".join(seg)})

    # Not a gated git op
    return allow("not-gated", {"command": cmd})

if __name__ == "__main__":
    sys.exit(main())
