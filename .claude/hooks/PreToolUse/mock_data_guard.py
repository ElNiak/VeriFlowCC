# tools/hooks/mock_data_guard.py
# Purpose: Block creation of "mock data" files from Claude-code tools, prefer updating existing files.
# Triggers on PreToolUse for Write/Edit/MultiEdit and Bash. Allows updates to existing files.

from __future__ import annotations
import json, os, re, shlex, sys, fnmatch, subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

POLICY_FILE = Path(".claude/mock_policy.json")

DEFAULT_POLICY = {
    # Directories considered "mocky" (deny by default unless allowDirs matches)
    "denyDirGlobs": [
        "**/mocks/**", "**/__mocks__/**", "**/mock/**",
        "**/fixtures/**", "**/fixture/**",
        "**/sample/**", "**/samples/**",
        "**/dummy/**", "**/dummies/**",
        "**/seed/**", "**/seeds/**",
        "**/testdata/**", "**/test-data/**", "**/data/mock/**", "**/data/mocks/**"
    ],
    # Filenames indicating mock data creation
    "denyNameGlobs": [
        "*mock*.*", "*fixture*.*", "*sample*.*", "*dummy*.*", "*seed*.*", "*testdata*.*", "*synthetic*.*", "*example*.*"
    ],
    # Data-ish extensions to gate (only when name/dir also looks mocky unless blockAllDataExt is true)
    "dataExtensions": [".json", ".yaml", ".yml", ".csv", ".ndjson", ".tsv", ".toml"],
    # Allow creation inside these dirs (e.g., test fixtures for unit tests)
    "allowDirs": ["tests/**", "test/**", "e2e/**", "cypress/fixtures/**", "playwright/fixtures/**", "docs/**"],
    # Additional explicit allowlist
    "allowNameGlobs": [],
    # If true, *any* new file with a data extension is blocked unless allowlisted
    "blockAllDataExt": False,
    # Emergency bypass (env var name)
    "bypassEnv": "CLAUDE_ALLOW_MOCK_DATA"
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
    p = dict(DEFAULT_POLICY)
    p.update(_read_json(POLICY_FILE))
    # Env overrides
    for key, envn in [
        ("denyDirGlobs", "CLAUDE_MOCK_DENY_DIRS"),
        ("denyNameGlobs", "CLAUDE_MOCK_DENY_NAMES"),
        ("dataExtensions", "CLAUDE_MOCK_DATA_EXTS"),
        ("allowDirs", "CLAUDE_MOCK_ALLOW_DIRS"),
        ("allowNameGlobs", "CLAUDE_MOCK_ALLOW_NAMES"),
    ]:
        lst = _env_list(envn)
        if lst is not None:
            p[key] = lst
    bae = os.getenv("CLAUDE_MOCK_BLOCK_ALL_DATA_EXT")
    if bae is not None:
        p["blockAllDataExt"] = bae not in ("0", "false", "False")
    return p

def project_root() -> Path:
    root = os.getenv("CLAUDE_PROJECT_DIR")
    return Path(root) if root else Path.cwd()

def norm_path(p: str) -> Path:
    root = project_root().resolve()
    abs_p = (root / p).resolve()
    if not str(abs_p).startswith(str(root)):
        raise ValueError(f"path escapes project root: {p}")
    return abs_p

def any_glob_ci(path_posix: str, globs: List[str]) -> bool:
    s = path_posix.lower()
    return any(fnmatch.fnmatchcase(s, g.lower()) for g in globs)

def is_allowed_dir(abs_path: Path, allow_dirs: List[str]) -> bool:
    rel = abs_path.relative_to(project_root()).as_posix()
    rel_dir = abs_path.parent.relative_to(project_root()).as_posix() + "/"
    return any_glob_ci(rel, allow_dirs) or any_glob_ci(rel_dir, allow_dirs)

def ext_of(p: Path) -> str:
    return p.suffix.lower()

def extract_paths_from_write_like(tool_input: Any) -> List[str]:
    paths: List[str] = []
    def walk(x: Any):
        if isinstance(x, dict):
            if "path" in x and isinstance(x["path"], str):
                paths.append(x["path"])
            for v in x.values():
                walk(v)
        elif isinstance(x, list):
            for it in x:
                walk(it)
    walk(tool_input)
    # de-dup
    seen: Set[str] = set(); out: List[str] = []
    for p in paths:
        if p not in seen:
            out.append(p); seen.add(p)
    return out

# -------- Bash command analysis (heuristic but effective) --------

def shlex_split(s: str) -> List[str]:
    try:
        return shlex.split(s)
    except Exception:
        return s.strip().split()

def bash_target_paths(cmd: str) -> List[str]:
    """
    Extract likely created/overwritten file targets from a Bash command.
    Handles: redirections (>, >>), 'tee file', 'touch file', 'cp src dst', 'mv src dst',
             'curl -o file', 'wget -O file', 'dd of=file'.
    Only returns targets that do not currently exist (i.e., creation) or are being written to (redir/tee).
    """
    tokens = shlex_split(cmd)
    if not tokens:
        return []

    targets: List[str] = []
    # redirections: > file, >> file
    for i, t in enumerate(tokens):
        if t in (">", ">>"):
            if i + 1 < len(tokens):
                targets.append(tokens[i + 1])
        elif t.startswith((">", ">>")) and len(t) > 1:
            targets.append(t.lstrip(">"))
    # tee
    if "tee" in tokens:
        idxs = [i for i, t in enumerate(tokens) if t == "tee"]
        for i in idxs:
            # collect following non-flag args until next pipe/command sep
            j = i + 1
            while j < len(tokens) and not tokens[j].startswith("-") and tokens[j] not in ("|", "&&", "||", ";"):
                targets.append(tokens[j]); j += 1
    # touch
    if "touch" in tokens:
        i = tokens.index("touch")
        j = i + 1
        while j < len(tokens) and not tokens[j].startswith("-"):
            targets.append(tokens[j]); j += 1
    # cp/mv/install -> last non-flag is destination
    for cmd0 in ("cp", "mv", "install"):
        if cmd0 in tokens:
            # naive but works: take last non-flag
            nonflags = [t for t in tokens[tokens.index(cmd0) + 1:] if not t.startswith("-")]
            if nonflags:
                targets.append(nonflags[-1])
    # curl -o, wget -O
    for flag, prog in (("-o", "curl"), ("-O", "wget"), ("-o", "wget"), ("--output", "curl")):
        if prog in tokens and flag in tokens:
            i = tokens.index(flag)
            if i + 1 < len(tokens):
                targets.append(tokens[i + 1])
    # dd of=file
    for t in tokens:
        if t.startswith("of="):
            targets.append(t.split("=", 1)[1])

    # Filter to new files (do not block updates), but keep redirection/tee targets (overwrite).
    out: List[str] = []
    root = project_root()
    for p in targets:
        # ignore descriptors like /dev/stdout
        if p.startswith("/dev/"):
            continue
        try:
            abs_p = norm_path(p)
        except Exception:
            continue
        # treat as created if not exists OR if came from redirection/tee/touch
        if not abs_p.exists() or any(sym in cmd for sym in (">", ">>", " tee ")):
            out.append(abs_p.relative_to(root).as_posix())
    # de-dup
    seen: Set[str] = set(); uniq: List[str] = []
    for p in out:
        if p not in seen:
            uniq.append(p); seen.add(p)
    return uniq

# -------- Policy decisions --------
def deny(reason: str, message: str, data: Dict[str, Any]) -> int:
    payload = {"decision": "deny", "reason": reason, "message": message, "data": data}
    print("BEGIN_HOOK_REPORT", file=sys.stderr)
    print(json.dumps(payload, indent=2), file=sys.stderr)
    print("END_HOOK_REPORT", file=sys.stderr)
    return 2

def allow(reason: str, data: Dict[str, Any]) -> int:
    payload = {"decision": "allow", "reason": reason, "data": data}
    print("BEGIN_HOOK_REPORT"); print(json.dumps(payload, indent=2)); print("END_HOOK_REPORT")
    return 0

def looks_mocky(abs_path: Path, policy: Dict[str, Any]) -> Tuple[bool, str]:
    rel = abs_path.relative_to(project_root()).as_posix()
    name = abs_path.name
    ext = ext_of(abs_path)
    # Allowlist checks first
    if is_allowed_dir(abs_path, policy.get("allowDirs", [])) or any_glob_ci(rel, policy.get("allowNameGlobs", [])):
        return (False, "allowlist")
    # Deny dirs/names
    if any_glob_ci(rel, policy.get("denyDirGlobs", [])) or any_glob_ci(name, policy.get("denyNameGlobs", [])):
        return (True, "deny-pattern")
    # Gate by extension if requested
    if policy.get("blockAllDataExt", False) and ext in set(map(str.lower, policy.get("dataExtensions", []))):
        return (True, "deny-data-ext")
    # Otherwise, allow
    return (False, "ok")

def evaluate_creation(paths: List[str], policy: Dict[str, Any]) -> Tuple[List[Dict[str, Any]], List[str]]:
    blocked: List[Dict[str, Any]] = []
    checked: List[str] = []
    root = project_root()
    for rel in paths:
        abs_p = norm_path(rel)
        checked.append(rel)
        # Only act on new files (not existing)
        if abs_p.exists():
            continue
        block, reason = looks_mocky(abs_p, policy)
        if block:
            blocked.append({
                "path": rel,
                "reason": reason,
                "suggest": "Prefer updating existing sources or generate data on-the-fly within tests. "
                           "If persistent fixtures are required, place them under an allowed directory "
                           "(see allowDirs) with minimal size."
            })
    return blocked, checked

# -------- Hook entry --------

def main() -> int:
    # Emergency bypass
    policy = load_policy()
    if os.getenv(policy.get("bypassEnv", "CLAUDE_ALLOW_MOCK_DATA")) == "1":
        return allow("bypass", {"note": "mock data guard bypassed via env"})

    try:
        env = json.load(sys.stdin)
    except Exception:
        return 0

    event = env.get("hook_event_name")
    tool = env.get("tool_name")
    if event != "PreToolUse":
        return 0

    # Write/Edit/MultiEdit path
    if tool in ("Write", "Edit", "MultiEdit"):
        paths = extract_paths_from_write_like(env.get("tool_input"))
        if not paths:
            return allow("no-paths", {"tool": tool})
        blocked, checked = evaluate_creation(paths, policy)
        if blocked:
            msg = (
                "Mock data creation is blocked by policy. Update existing files or use test-time factories/fixtures. "
                "Allowed dirs can be configured in .claude/mock_policy.json."
            )
            return deny("mock-data-new-file", msg, {"blocked": blocked, "checked": checked, "tool": tool})
        return allow("ok", {"checked": checked, "tool": tool})

    # Bash path
    if tool == "Bash":
        cmd = (env.get("tool_input") or {}).get("command", "")
        if not cmd:
            return allow("no-cmd", {"tool": tool})
        targets = bash_target_paths(cmd)
        if not targets:
            return allow("no-targets", {"tool": tool, "command": cmd})
        blocked, checked = evaluate_creation(targets, policy)
        if blocked:
            msg = (
                "Mock data creation via Bash is blocked. Remove file creation or write into allowed test fixtures dirs."
            )
            return deny("mock-data-bash", msg, {"blocked": blocked, "checked": checked, "command": cmd})
        return allow("ok", {"checked": checked, "command": cmd})

    return 0

if __name__ == "__main__":
    sys.exit(main())