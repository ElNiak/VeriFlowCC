# Purpose: Block creation of duplicate-ish "enhanced/unified/final/copy/v2" files from Claude's Write/Edit tools to prefer updating existing files.

from __future__ import annotations
import json, os, re, sys, fnmatch, shlex, subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

# ---------------- Configuration ----------------

POLICY_FILE = Path(".claude/file_policy.json")

DEFAULT_POLICY = {
    # Deny when filename (path) matches any of these globs (case-insensitive)
    "denyNameGlobs": [
        "*enhanced*",
        "*unified*",
        "*final*",
        "*copy*",
        "*duplicate*",
        "*new*",
        "*tmp*",
        "*draft*",
        "*alt*",
        "*alternative*",
        "*rewrite*",
        "*refactor*",
        "*v[0-9]*",      # interpreted as glob; see regex below for version suffixes
        "*_v[0-9]*",
    ],
    # Extra deny regexes (applied case-insensitive to POSIX-style path)
    "denyNameRegexes": [
        r"(^|/).*(?:enhanced|unified|final|copy|duplicate|new|tmp|draft|alt|alternative|rewrite|refactor)(?:[-_ ]?\d+)?\.",
        r"(^|/).*[._-]v\d+\.",  # e.g., foo_v2.py, foo-v3.ts
    ],
    # Allow creation inside these dirs (globs), e.g., migrations or tests
    "allowDirs": ["migrations/**", "docs/**", "tests/**", "test/**", "generated/**"],
    # Allow names even if they match deny (higher priority than deny)
    "allowNameGlobs": [],
    # Block all new files by default? (we keep it False per your ask)
    "blockAllNewFiles": False,
    # Candidate suffix tokens to strip when suggesting existing file to update
    "duplicateSuffixTokens": ["enhanced", "unified", "final", "copy", "duplicate", "new", "tmp", "draft", "alt", "alternative", "rewrite", "refactor"],
}

def _read_json(path: Path) -> Dict[str, Any]:
    try:
        if path.is_file():
            return json.loads(path.read_text())
    except Exception:
        pass
    return {}

def _env_list(name: str) -> Optional[List[str]]:
    v = os.getenv(name)
    if not v:
        return None
    return [x.strip() for x in v.split(",") if x.strip()]

def load_policy() -> Dict[str, Any]:
    policy = dict(DEFAULT_POLICY)
    file_cfg = _read_json(POLICY_FILE)
    policy.update({k: v for k, v in file_cfg.items() if v is not None})

    # Optional env overrides (CSV for list fields)
    for key, env_name in [
        ("denyNameGlobs", "CLAUDE_FILE_DENY_GLOBS"),
        ("denyNameRegexes", "CLAUDE_FILE_DENY_REGEXES"),
        ("allowDirs", "CLAUDE_FILE_ALLOW_DIRS"),
        ("allowNameGlobs", "CLAUDE_FILE_ALLOW_GLOBS"),
        ("duplicateSuffixTokens", "CLAUDE_FILE_SUFFIX_TOKENS"),
    ]:
        v = _env_list(env_name)
        if v is not None:
            policy[key] = v

    env_block_all = os.getenv("CLAUDE_FILE_BLOCK_ALL_NEW")
    if env_block_all is not None:
        policy["blockAllNewFiles"] = env_block_all not in ("0", "false", "False")
    return policy

# ---------------- Utilities ----------------

def project_root() -> Path:
    root = os.getenv("CLAUDE_PROJECT_DIR")
    return Path(root) if root else Path.cwd()

def norm_path(p: str) -> Path:
    """Resolve a tool path safely inside project root."""
    root = project_root().resolve()
    abs_p = (root / p).resolve()
    # Keep writes within the project
    if not str(abs_p).startswith(str(root)):
        raise ValueError(f"path escapes project root: {p}")
    return abs_p

def is_allowed_dir(p: Path, allow_dirs: List[str]) -> bool:
    rel = p.relative_to(project_root()).as_posix()
    rel_dir = (p.parent.relative_to(project_root())).as_posix() + "/"
    patterns = allow_dirs or []
    return any(fnmatch.fnmatchcase(rel, pat) or fnmatch.fnmatchcase(rel_dir, pat) for pat in patterns)

def any_glob(name: str, globs: List[str]) -> bool:
    name_ci = name.lower()
    return any(fnmatch.fnmatchcase(name_ci, g.lower()) for g in globs)

def any_regex(name: str, regexes: List[str]) -> bool:
    name_posix = name.replace("\\", "/")
    return any(re.compile(rx, re.IGNORECASE).search(name_posix) for rx in regexes or [])

def extract_paths_from_input(tool_name: str, tool_input: Any) -> List[str]:
    """Support Write/Edit/MultiEdit envelopes by walking for 'path' keys."""
    paths: List[str] = []
    def walk(x: Any):
        if isinstance(x, dict):
            # common: {"path": "...", "content": "..."}
            if "path" in x and isinstance(x["path"], str):
                paths.append(x["path"])
            for v in x.values():
                walk(v)
        elif isinstance(x, list):
            for it in x:
                walk(it)
    walk(tool_input)
    # De-dup while preserving order
    seen: Set[str] = set()
    uniq: List[str] = []
    for p in paths:
        if p not in seen:
            uniq.append(p); seen.add(p)
    return uniq

def strip_suffix_tokens(stem: str, tokens: List[str]) -> str:
    s = stem
    # remove common version suffixes: _v2, -v3, v4
    s = re.sub(r"(?i)[._-]?v\d+$", "", s)
    # remove trailing tokens with separators
    for t in tokens:
        s = re.sub(rf"(?i)([._-]?{re.escape(t)})+$", "", s)
    return s

def suggest_existing_candidates(new_path: Path, tokens: List[str]) -> List[str]:
    """Heuristic: suggest siblings with same extension whose stem matches stripped base."""
    base = strip_suffix_tokens(new_path.stem, tokens)
    ext = new_path.suffix
    parent = new_path.parent
    if not parent.exists():
        return []
    candidates: List[str] = []
    try:
        for p in parent.glob(f"{base}*{ext}"):
            if p.is_file() and p.name != new_path.name:
                candidates.append(p.relative_to(project_root()).as_posix())
    except Exception:
        pass
    return candidates[:5]

# ---------------- Decisions ----------------

def deny(reason: str, message: str, data: Dict[str, Any]) -> int:
    payload = {"decision": "deny", "reason": reason, "message": message, "data": data}
    print("BEGIN_HOOK_REPORT")
    print(json.dumps(payload, indent=2))
    print("END_HOOK_REPORT")
    # Exit 2: ask Claude to adapt (don’t execute the Write/Edit)
    return 2

def allow(reason: str, data: Dict[str, Any]) -> int:
    payload = {"decision": "allow", "reason": reason, "data": data}
    print("BEGIN_HOOK_REPORT")
    print(json.dumps(payload, indent=2))
    print("END_HOOK_REPORT")
    return 0

def evaluate_new_file(path_str: str, policy: Dict[str, Any]) -> Tuple[bool, str, Dict[str, Any]]:
    """Return (blocked, reason, details)."""
    p_abs = norm_path(path_str)
    rel = p_abs.relative_to(project_root()).as_posix()

    # existing file is always allowed (this guard is for creations)
    if p_abs.exists():
        return (False, "exists", {"path": rel})

    # allow certain directories
    if is_allowed_dir(p_abs, policy.get("allowDirs", [])):
        return (False, "allowed-dir", {"path": rel})

    if policy.get("blockAllNewFiles", False):
        return (True, "block-all-new", {"path": rel})

    # allowlist names override any denies
    if any_glob(rel, policy.get("allowNameGlobs", [])):
        return (False, "allowed-name", {"path": rel})

    # deny patterns
    deny_globs = policy.get("denyNameGlobs", [])
    deny_regex = policy.get("denyNameRegexes", [])
    if any_glob(rel, deny_globs) or any_regex(rel, deny_regex):
        # suggest existing likely targets
        cands = suggest_existing_candidates(p_abs, policy.get("duplicateSuffixTokens", []))
        details = {"path": rel, "suggest": cands}
        return (True, "deny-name-pattern", details)

    # heuristic duplicate detection: base without suffix tokens matches a sibling
    tokens = policy.get("duplicateSuffixTokens", [])
    base = strip_suffix_tokens(p_abs.stem, tokens) + p_abs.suffix
    sib = (p_abs.parent / base)
    if sib.exists():
        details = {"path": rel, "suspected_original": sib.relative_to(project_root()).as_posix()}
        return (True, "duplication-suspected", details)

    return (False, "new-file-ok", {"path": rel})

# ---------------- Hook entry ----------------

def main() -> int:
    try:
        env = json.load(sys.stdin)  # Claude-code passes hook envelope JSON
    except Exception:
        return 0

    if env.get("hook_event_name") != "PreToolUse":
        return 0

    tool = env.get("tool_name")
    if tool not in ("Write", "Edit", "MultiEdit"):
        return 0

    policy = load_policy()

    tool_input = env.get("tool_input")
    paths = extract_paths_from_input(tool, tool_input)
    if not paths:
        return allow("no-paths", {"tool": tool})

    blocked_paths: List[Dict[str, Any]] = []
    for p in paths:
        blocked, reason, details = evaluate_new_file(p, policy)
        if blocked:
            blocked_paths.append({"reason": reason, **details})

    if blocked_paths:
        msg = (
            "Creation of new files that look like 'enhanced/unified/final/copy/vN' duplicates is blocked.\n"
            "Prefer updating the original file instead. If truly needed, rename to a canonical filename "
            "or place it under an allowed directory (see .claude/file_policy.json).\n"
            "Next steps for Claude:\n"
            "  • Identify the original file(s) from 'suggest' or 'suspected_original'.\n"
            "  • Apply edits there and retry.\n"
        )
        return deny("new-file-denied", msg, {"blocked": blocked_paths, "tool": tool})

    return allow("no-new-files-or-ok", {"checked": [str(p) for p in paths], "tool": tool})

if __name__ == "__main__":
    sys.exit(main())