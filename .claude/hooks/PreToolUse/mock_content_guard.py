# Purpose: Prevent committing bulky/mock data content (JSON/YAML/CSV/NDJSON/etc.) created by Claude-code.
# Strategy: Inspect Write/Edit/MultiEdit payloads (and common inline Bash writes) and deny new mocky data;
#           prefer updating existing sources or using runtime factories/fixtures under allowed dirs.

from __future__ import annotations
import json, os, re, sys, fnmatch, shlex, csv, io, subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

POLICY_FILE = Path(".claude/mock_policy.json")

DEFAULT_POLICY: Dict[str, Any] = {
    # Directories where generated/fixture content is allowed
    "allowDirs": [],
    # File extensions we treat as "data"
    "dataExtensions": [".json", ".yaml", ".yml", ".csv", ".ndjson", ".tsv", ".toml", ".xml", ".txt"],
    # Absolute caps (deny if any exceeded)
    "maxBytesPerFile": 64_000,       # 64 KB default
    "maxJsonArrayLen": 200,          # total items in a top-level JSON array
    "maxCsvRows": 200,               # including header
    "maxNdjsonLines": 200,
    # Deny if content matches these markers (case-insensitive)
    "denyContentRegexes": [
        r"\blorem ipsum\b",
        r"\bjohn\s+doe\b",
        r"\bexample\.com\b",
        r"\b123\s+main\s+st\b",
        r"\bfoo\b.*\bbar\b",      # common placeholders
        r"\bdummy\b|\bmock\b|\bsample\b|\bfixture\b|\bsynthetic\b",
    ],
    # If true, *any* new data file is blocked unless under allowDirs
    "blockAllNewDataFiles": False,
    # Allowlist file globs (names) despite rules
    "allowNameGlobs": [],
    # Emergency bypass env var
    "bypassEnv": "CLAUDE_ALLOW_MOCK_DATA",
}

# ---------- utils: config & project ----------

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
    # env overrides
    for key, envn in [
        ("allowDirs", "CLAUDE_MOCK_ALLOW_DIRS"),
        ("dataExtensions", "CLAUDE_MOCK_DATA_EXTS"),
        ("denyContentRegexes", "CLAUDE_MOCK_DENY_REGEXES"),
        ("allowNameGlobs", "CLAUDE_MOCK_ALLOW_NAMES"),
    ]:
        lst = _env_list(envn)
        if lst is not None:
            p[key] = lst
    for key in ("maxBytesPerFile", "maxJsonArrayLen", "maxCsvRows", "maxNdjsonLines"):
        ev = os.getenv(f"CLAUDE_MOCK_{key.upper()}")
        if ev and ev.isdigit():
            p[key] = int(ev)
    b = os.getenv("CLAUDE_MOCK_BLOCK_ALL_DATA_EXT")
    if b is not None:
        p["blockAllNewDataFiles"] = b not in ("0", "false", "False")
    return p

def project_root() -> Path:
    return Path(os.getenv("CLAUDE_PROJECT_DIR") or Path.cwd()).resolve()

def norm_path(p: str) -> Path:
    root = project_root()
    abs_p = (root / p).resolve()
    if not str(abs_p).startswith(str(root)):
        raise ValueError(f"path escapes project root: {p}")
    return abs_p

def relpath(p: Path) -> str:
    return p.relative_to(project_root()).as_posix()

def any_glob_ci(s: str, globs: List[str]) -> bool:
    ss = s.lower()
    return any(fnmatch.fnmatchcase(ss, g.lower()) for g in globs or [])

def is_allowed_dir(abs_path: Path, allow_dirs: List[str]) -> bool:
    rel = relpath(abs_path)
    rel_dir = (abs_path.parent.relative_to(project_root())).as_posix() + "/"
    return any_glob_ci(rel, allow_dirs) or any_glob_ci(rel_dir, allow_dirs)

# ---------- extract (path, content) from Write/Edit/MultiEdit ----------

def extract_write_pairs(payload: Any) -> List[Tuple[str, str]]:
    pairs: List[Tuple[str, str]] = []
    def walk(x: Any):
        if isinstance(x, dict):
            if "path" in x and isinstance(x["path"], str) and "content" in x and isinstance(x["content"], str):
                pairs.append((x["path"], x["content"]))
            for v in x.values():
                walk(v)
        elif isinstance(x, list):
            for it in x:
                walk(it)
    walk(payload)
    # de-dup by path keep last
    seen: Set[str] = set(); out: List[Tuple[str, str]] = []
    for path, content in pairs[::-1]:
        if path not in seen:
            out.append((path, content)); seen.add(path)
    return list(reversed(out))

# ---------- parse inline Bash writes (best-effort) ----------

HEREDOC_RE = re.compile(r"<<-?\s*(['\"]?)(?P<eof>\w+)\1\s*(?P<body>.*?)(?:\n)(?P=eof)\b", re.DOTALL)
ECHO_REDIRECT_RE = re.compile(r"""(?:^|\s)echo\s+(['"])(?P<body>.*?)(?<!\\)\1\s*(?:>>?|>\|)\s*(?P<target>[^;&|]+)""", re.DOTALL)
TEE_RE = re.compile(r"""(?:^|\s)tee\s+(?P<target>[^-\s][^\s;|&]*)""")

def extract_bash_targets_and_bodies(command: str) -> List[Tuple[str, Optional[str]]]:
    res: List[Tuple[str, Optional[str]]] = []
    # echo 'body' > file
    for m in ECHO_REDIRECT_RE.finditer(command):
        tgt = m.group("target").strip()
        body = m.group("body")
        res.append((tgt, body))
    # here-doc: cat > file <<EOF \n body \n EOF
    for m in HEREDOC_RE.finditer(command):
        body = m.group("body")
        # try to locate a preceding redirection target '>' on same or previous line; heuristic:
        # this is hard reliably, so we just mark body with unknown target; another detector below will catch 'tee'
        res.append(("", body))
    # tee file
    for m in TEE_RE.finditer(command):
        tgt = m.group("target").strip()
        res.append((tgt, None))
    # crude 'printf "..." > file'
    if "printf" in command and ">" in command:
        parts = command.split(">")
        if len(parts) >= 2:
            tgt = parts[-1].strip().split()[0]
            res.append((tgt, None))
    # normalize: drop entries without target unless body exists (we can't map body→file)
    return [(t, b) for (t, b) in res if t or b]

# ---------- content heuristics ----------

def is_data_extension(p: Path, exts: List[str]) -> bool:
    return p.suffix.lower() in {e.lower() for e in exts}

def count_json_array_len(s: str) -> Optional[int]:
    try:
        obj = json.loads(s)
        if isinstance(obj, list):
            return len(obj)
    except Exception:
        pass
    return None

def count_ndjson_lines(s: str) -> Optional[int]:
    lines = [ln for ln in s.splitlines() if ln.strip()]
    # treat as NDJSON if most lines look like JSON objects/arrays
    sample = lines[:50]
    if not sample:
        return None
    looks = 0
    for ln in sample:
        ln = ln.strip()
        if (ln.startswith("{") and ln.endswith("}")) or (ln.startswith("[") and ln.endswith("]")):
            looks += 1
    if looks >= max(3, int(0.6 * len(sample))):
        return len(lines)
    return None

def count_csv_rows(s: str) -> Optional[int]:
    try:
        # simple sniff: if commas or tabs and >1 line
        if not ("," in s or "\t" in s) or "\n" not in s:
            return None
        reader = csv.reader(io.StringIO(s))
        return sum(1 for _ in reader)
    except Exception:
        return None

MOCK_PATTERNS = [re.compile(rx, re.IGNORECASE) for rx in DEFAULT_POLICY["denyContentRegexes"]]

def matches_mock_markers(s: str, deny_regexes: List[str]) -> bool:
    pats = [re.compile(rx, re.IGNORECASE) for rx in (deny_regexes or [])]
    for rx in pats:
        if rx.search(s):
            return True
    return False

def low_diversity_rows(s: str, min_rows: int = 20, max_unique_ratio: float = 0.35) -> bool:
    """Very rough: if many repeated identical lines/objects → likely mock dump."""
    lines = [ln.strip() for ln in s.splitlines() if ln.strip()]
    if len(lines) < min_rows:
        return False
    uniq = len(set(lines))
    return (uniq / len(lines)) <= max_unique_ratio

# ---------- decision & reporting ----------

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

def evaluate_pair(path_str: str, content: str, policy: Dict[str, Any]) -> Tuple[bool, str, Dict[str, Any]]:
    abs_p = norm_path(path_str)
    rel = relpath(abs_p)
    exts = policy.get("dataExtensions", [])
    # Skip if allowlist
    if is_allowed_dir(abs_p, policy.get("allowDirs", [])) or any_glob_ci(rel, policy.get("allowNameGlobs", [])):
        return (False, "allowlist", {"path": rel})

    # Only guard "data-like" files or any file if blockAllNewDataFiles=True
    is_data = is_data_extension(abs_p, exts)
    if not is_data and not policy.get("blockAllNewDataFiles", False):
        return (False, "non-data", {"path": rel})

    # Existing file updates: allow unless grossly violating thresholds (optional stricter mode)
    if abs_p.exists() and not policy.get("blockAllNewDataFiles", False):
        # You can tighten by applying thresholds to updates too; by default we allow editing existing.
        return (False, "update-existing", {"path": rel})

    # New data file: enforce
    size = len(content.encode("utf-8", errors="ignore"))
    if size > int(policy.get("maxBytesPerFile", 64000)):
        return (True, "size-cap", {"path": rel, "bytes": size})

    if matches_mock_markers(content, policy.get("denyContentRegexes", [])):
        return (True, "mock-markers", {"path": rel})

    # Structured detectors
    ja = count_json_array_len(content)
    if ja is not None and ja > int(policy.get("maxJsonArrayLen", 200)):
        return (True, "json-array-cap", {"path": rel, "items": ja})

    nd = count_ndjson_lines(content)
    if nd is not None and nd > int(policy.get("maxNdjsonLines", 200)):
        return (True, "ndjson-cap", {"path": rel, "lines": nd})

    cr = count_csv_rows(content)
    if cr is not None and cr > int(policy.get("maxCsvRows", 200)):
        return (True, "csv-rows-cap", {"path": rel, "rows": cr})

    if low_diversity_rows(content):
        return (True, "low-diversity", {"path": rel})

    # All good
    return (False, "ok", {"path": rel})

# ---------- hook entry ----------

def main() -> int:
    policy = load_policy()
    if os.getenv(policy.get("bypassEnv", "CLAUDE_ALLOW_MOCK_DATA")) == "1":
        return allow("bypass", {"note": "mock content guard bypassed via env"})

    try:
        env = json.load(sys.stdin)
    except Exception:
        return 0

    event = env.get("hook_event_name")
    tool = env.get("tool_name")
    if event != "PreToolUse":
        return 0

    blocked: List[Dict[str, Any]] = []
    checked: List[str] = []

    if tool in ("Write", "Edit", "MultiEdit"):
        pairs = extract_write_pairs(env.get("tool_input"))
        for path, content in pairs:
            blocked_flag, reason, details = evaluate_pair(path, content, policy)
            checked.append(path)
            if blocked_flag:
                blocked.append({"reason": reason, **details})

    elif tool == "Bash":
        cmd = (env.get("tool_input") or {}).get("command", "")
        if cmd:
            for target, body in extract_bash_targets_and_bodies(cmd):
                # If body is known, treat as new content; if not, we can't pre-validate reliably.
                if not target:
                    continue
                abs_tgt = norm_path(target)
                # Skip allowed dirs
                if is_allowed_dir(abs_tgt, policy.get("allowDirs", [])):
                    continue
                # Only evaluate when we have inline body (echo/heredoc)
                if body is None:
                    continue
                blocked_flag, reason, details = evaluate_pair(relpath(abs_tgt), body, policy)
                checked.append(relpath(abs_tgt))
                if blocked_flag:
                    blocked.append({"reason": reason, **details})

    if blocked:
        msg = (
            "Mock/bulky data content creation is blocked. Prefer updating existing sources or generating data "
            "at runtime in tests. If persistent fixtures are necessary, place small samples under allowed dirs "
            "and reduce size below thresholds defined in .claude/mock_policy.json."
        )
        return deny("mock-content", msg, {"blocked": blocked, "checked": checked, "tool": tool})

    return allow("ok", {"checked": checked, "tool": tool})

if __name__ == "__main__":
    sys.exit(main())