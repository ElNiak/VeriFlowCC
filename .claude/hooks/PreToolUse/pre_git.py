# tools/hooks/git_policy_guard.py
# Purpose: Enforce safe git usage from Claude-code's Bash tool:
# - Forbid commits with --no-verify/-n.
# - Forbid 'git push --force' (incl. '+refspec' force).
# - Gate 'git push --force-with-lease' by branch globs (deny on protected branches by default).
# - Emit a compact JSON decision so Claude can self-correct; exit code 2 blocks the tool call.

from __future__ import annotations
import json, os, re, shlex, subprocess, sys, fnmatch
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# ---------------- Config loading ----------------

DEFAULT_POLICY = {
    # Branch globs treated as "protected" (no force(-with-lease) allowed by default)
    "protectedBranches": ["main", "master", "release/*", "hotfix/*", "stable", "prod", "production"],
    # Branch globs where plain --force is explicitly allowed (discouraged; default none)
    "allowForceOn": [],
    # Branch globs where --force-with-lease is allowed (typical: feature/topic branches)
    "allowForceWithLeaseOn": ["feature/*", "bugfix/*", "chore/*", "refactor/*", "wip/*"],
    # Toggle blocking of commit --no-verify/-n
    "blockNoVerify": True,
}

POLICY_FILE = Path(".claude/git_policy.json")

def _read_json(path: Path) -> Dict[str, Any]:
    try:
        if path.is_file():
            return json.loads(path.read_text())
    except Exception:
        pass
    return {}

def load_policy() -> Dict[str, Any]:
    policy = dict(DEFAULT_POLICY)
    # File policy
    file_policy = _read_json(POLICY_FILE)
    policy.update({k: v for k, v in file_policy.items() if v is not None})

    # Env overrides (CSV for lists)
    def env_list(name: str) -> Optional[List[str]]:
        v = os.getenv(name)
        if not v:
            return None
        return [x.strip() for x in v.split(",") if x.strip()]

    env_protected = env_list("CLAUDE_PROTECTED_BRANCHES")
    env_allow_force = env_list("CLAUDE_ALLOW_FORCE_ON")
    env_allow_lease = env_list("CLAUDE_ALLOW_FORCE_WITH_LEASE_ON")
    env_block_noverify = os.getenv("CLAUDE_BLOCK_NO_VERIFY")

    if env_protected is not None:
        policy["protectedBranches"] = env_protected
    if env_allow_force is not None:
        policy["allowForceOn"] = env_allow_force
    if env_allow_lease is not None:
        policy["allowForceWithLeaseOn"] = env_allow_lease
    if env_block_noverify is not None:
        policy["blockNoVerify"] = env_block_noverify not in ("0", "false", "False")

    return policy

# ---------------- Utility ----------------

def shlex_split(s: str) -> List[str]:
    try:
        return shlex.split(s)
    except Exception:
        return s.strip().split()

def run_git(*args: str) -> Optional[str]:
    try:
        out = subprocess.check_output(["git", *args], text=True, stderr=subprocess.DEVNULL)
        return out.strip()
    except Exception:
        return None

def current_branch() -> Optional[str]:
    # returns e.g., "my-feature"; detached head returns "HEAD"
    br = run_git("rev-parse", "--abbrev-ref", "HEAD")
    return br if br and br != "HEAD" else None

def upstream_branch() -> Optional[str]:
    # returns e.g., "origin/main"; we only need the rightmost component for matching
    up = run_git("rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}")
    return up

def target_branches_from_push(tokens: List[str]) -> List[str]:
    """
    Parse 'git push [opts] [<remote>] [<refspec> ...]' and return list of destination branch names.
    Handles:
      - 'git push origin my-branch'
      - 'git push origin HEAD:main'
      - 'git push origin +main' (force via '+')
      - 'git push' (use upstream)
    """
    # strip leading 'git' 'push'
    if len(tokens) < 2 or tokens[0] != "git" or tokens[1] != "push":
        return []
    # Collect non-flag args after 'push'
    nonflags: List[str] = []
    for t in tokens[2:]:
        if t.startswith("-"):
            continue
        nonflags.append(t)
    if not nonflags:
        # No explicit remote/refspecs → use upstream
        up = upstream_branch()
        if up and "/" in up:
            return [up.split("/", 1)[1]]
        # fallback to current branch
        cb = current_branch()
        return [cb] if cb else []

    # If first non-flag looks like remote, skip it; refspecs follow
    refspecs = nonflags[1:] if nonflags else []
    if not refspecs:
        # Only branch given (git push origin my-branch)
        # It may still be a remote if user omitted branch; assume it's branch if no more args
        if len(nonflags) == 1:
            return [nonflags[0]]
        return []

    dests: List[str] = []
    for rs in refspecs:
        # Remove leading '+' if present (force)
        rs_clean = rs[1:] if rs.startswith("+") else rs
        if ":" in rs_clean:
            _, dst = rs_clean.rsplit(":", 1)
            dests.append(dst)
        else:
            # single name maps to same dst on remote
            dests.append(rs_clean)
    return dests

def any_glob_match(name: str, globs: List[str]) -> bool:
    return any(fnmatch.fnmatchcase(name, g) for g in globs)

# ---------------- Policy checks ----------------

NO_VERIFY_PATTERNS = (re.compile(r"--no-verify\b"), re.compile(r"(?<!\S)-n(?!\S)"))

def is_commit_no_verify(tokens: List[str]) -> bool:
    if len(tokens) >= 2 and tokens[0] == "git" and tokens[1] == "commit":
        joined = " ".join(tokens)
        return any(p.search(joined) for p in NO_VERIFY_PATTERNS)
    return False

def contains_force(tokens: List[str]) -> bool:
    return any(t in ("--force", "-f") for t in tokens)

def contains_force_with_lease(tokens: List[str]) -> bool:
    return any(t.startswith("--force-with-lease") for t in tokens)

def contains_plus_refspec(tokens: List[str]) -> bool:
    # e.g., 'git push origin +main' or '+HEAD:main'
    for t in tokens:
        if not t.startswith("-") and t.startswith("+"):
            return True
    return False

def evaluate_push_policy(tokens: List[str], policy: Dict[str, Any]) -> Tuple[bool, str, Dict[str, Any]]:
    """
    Returns (blocked, reason_text, details)
    """
    branches = target_branches_from_push(tokens)
    branches = [b for b in branches if b] or [current_branch() or "UNKNOWN"]

    is_force = contains_force(tokens) or contains_plus_refspec(tokens)
    is_lease = contains_force_with_lease(tokens)

    prot = list(policy.get("protectedBranches", []))
    allow_force = list(policy.get("allowForceOn", []))
    allow_lease = list(policy.get("allowForceWithLeaseOn", []))

    # Block plain --force unless explicitly allowed for *all* targets
    if is_force:
        blocked = any(not any_glob_match(b, allow_force) for b in branches)
        if blocked:
            return True, "plain-force", {
                "branches": branches, "policy": {"allowForceOn": allow_force}
            }
        return False, "plain-force-allowed", {"branches": branches}

    # For --force-with-lease: block on protected branches; allow on allow_lease branches
    if is_lease:
        for b in branches:
            if any_glob_match(b, prot) and not any_glob_match(b, allow_lease):
                return True, "lease-on-protected", {
                    "branch": b, "policy": {"protectedBranches": prot, "allowForceWithLeaseOn": allow_lease}
                }
        # Allowed: either non-protected branch, or explicitly allowlisted
        return False, "lease-allowed", {"branches": branches}

    # Not a force push: allowed
    return False, "no-force", {"branches": branches}

# ---------------- Hook entry ----------------

def deny(decision: str, message: str, data: Dict[str, Any]) -> int:
    payload = {"decision": "deny", "reason": decision, "message": message, "data": data}
    print("BEGIN_HOOK_REPORT")
    print(json.dumps(payload, indent=2))
    print("END_HOOK_REPORT")
    # Exit 2 signals Claude-code to stop this tool call and adapt.
    return 2

def allow(decision: str, data: Dict[str, Any]) -> int:
    payload = {"decision": "allow", "reason": decision, "data": data}
    print("BEGIN_HOOK_REPORT")
    print(json.dumps(payload, indent=2))
    print("END_HOOK_REPORT")
    return 0

def main() -> int:
    # Read hook envelope from stdin (Claude-code sends JSON for PreToolUse Bash)
    try:
        env: Dict[str, Any] = json.load(sys.stdin)
    except Exception:
        return 0

    if env.get("hook_event_name") != "PreToolUse" or env.get("tool_name") != "Bash":
        return 0

    cmd = (env.get("tool_input") or {}).get("command", "")
    if not cmd:
        return 0

    # Emergency bypass for maintainers/CI
    if os.getenv("CLAUDE_ALLOW_GIT_POLICY_BYPASS") == "1":
        return allow("bypass-env", {"command": cmd})

    tokens = shlex_split(cmd)
    policy = load_policy()

    # 1) Block commit --no-verify
    if policy.get("blockNoVerify", True) and is_commit_no_verify(tokens):
        msg = (
            "Commit blocked: `--no-verify` (or `-n`) is not allowed.\n"
            "Do this instead:\n"
            "  • Run repo checks linters/formatters/typers\n"
            "  • Commit without bypass flags.\n"
        )
        return deny("commit-no-verify", msg, {"command": cmd})

    # Only gate pushes for now
    if len(tokens) >= 2 and tokens[0] == "git" and tokens[1] == "push":
        blocked, reason, details = evaluate_push_policy(tokens, policy)
        if blocked:
            if reason == "plain-force":
                msg = (
                    "Push blocked: plain `git push --force` (or '+refspec') is disallowed.\n"
                    "Try: `git push --force-with-lease` on a non-protected branch, "
                    "or push without force and open a PR.\n"
                )
            elif reason == "lease-on-protected":
                b = details.get("branch", "UNKNOWN")
                msg = (
                    f"Push blocked: `--force-with-lease` to protected branch '{b}' is disallowed.\n"
                    "Push without force, or create a new branch and open a PR.\n"
                )
            else:
                msg = "Push blocked by policy."
            return deny(reason, msg, {"command": cmd, **details})
        return allow(reason, {"command": cmd, **details})

    return allow("not-gated", {"command": cmd})

if __name__ == "__main__":
    sys.exit(main())