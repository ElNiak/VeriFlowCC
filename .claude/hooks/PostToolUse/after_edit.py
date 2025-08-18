# .claude/hooks/PostToolUse/after_edit.py
# Purpose: Format & lint only updated files; emit actionable diagnostics for Claude-code.
# Behavior:
#   - Exit 0: clean (or only auto-fixes applied)
#   - Exit 2: action required (lint errors, missing tools, or other fixable issues)
#   - Always prints a JSON report between BEGIN_HOOK_REPORT/END_HOOK_REPORT

from __future__ import annotations
import argparse
import json
import shlex
import subprocess
import sys
from pathlib import Path
from shutil import which
from typing import Iterable, List, Dict, Tuple, Callable, Set, Any, Optional

# ---------- helpers ----------

def _cmd_exists(cmd: str) -> bool:
    return which(cmd) is not None

def _python_module_cmd(module: str, args: List[str]) -> Optional[List[str]]:
    py = which("python3") or which("python")
    if not py:
        return None
    return [py, "-m", module, *args]

def _node_tool_cmd(bin_name: str, args: List[str]) -> Optional[List[str]]:
    # Prefer local binary; otherwise fall back to npx if available
    if _cmd_exists(bin_name):
        return [bin_name, *args]
    if _cmd_exists("npx"):
        return ["npx", "--yes", bin_name, *args]
    return None

def _batch(files: List[str], base: List[str], max_args: int = 200) -> List[List[str]]:
    chunks: List[List[str]] = []
    cur: List[str] = []
    for f in files:
        cur.append(f)
        if len(cur) >= max_args:
            chunks.append(base + cur)
            cur = []
    if cur:
        chunks.append(base + cur)
    return chunks

def _ext(p: Path) -> str:
    return p.suffix.lstrip(".").lower()

def _capture_run(cmd: List[str]) -> Tuple[int, str, str]:
    try:
        proc = subprocess.run(cmd, text=True, capture_output=True)
        return proc.returncode, (proc.stdout or "").strip(), (proc.stderr or "").strip()
    except FileNotFoundError:
        # Standardize "not found" so detection is reliable
        return 127, "", f"Command not found: {cmd[0]}"
    except Exception as e:
        return 1, "", f"{type(e).__name__}: {e}"

# ---------- discovery ----------

def git_staged_files() -> List[str]:
    try:
        out = subprocess.check_output(
            ["git", "diff", "--cached", "--name-only", "--diff-filter=ACM"],
            text=True,
        )
        return [ln for ln in out.splitlines() if ln.strip()]
    except subprocess.CalledProcessError:
        return []

def git_updated_vs_head() -> List[str]:
    try:
        out = subprocess.check_output(
            ["git", "diff", "HEAD", "--name-only", "--diff-filter=ACM"],
            text=True,
        )
        return [ln for ln in out.splitlines() if ln.strip()]
    except subprocess.CalledProcessError:
        return []

def filter_supported(files: Iterable[str], tracked_exts: Set[str]) -> List[str]:
    res: List[str] = []
    for f in files:
        p = Path(f)
        if p.is_file() and _ext(p) in tracked_exts:
            res.append(str(p))
    return res

def group_by_ext(files: List[str]) -> Dict[str, List[str]]:
    g: Dict[str, List[str]] = {}
    for f in files:
        g.setdefault(_ext(Path(f)), []).append(f)
    return g

# ---------- command maps ----------

def make_formatters() -> Dict[str, Callable[[List[str]], List[List[str]]]]:
    def py_fmt(fs: List[str]) -> List[List[str]]:
        batches: List[List[str]] = []
        black = _node_or_py(None)  # placeholder to satisfy linter (see helper below)
        # black
        cmd = (["black", "--quiet"] if _cmd_exists("black")
               else (_python_module_cmd("black", ["--quiet"]) or []))
        if cmd:
            batches += _batch(fs, cmd)
        # isort
        cmd = (["isort", "--quiet"] if _cmd_exists("isort")
               else (_python_module_cmd("isort", ["--quiet"]) or []))
        if cmd:
            batches += _batch(fs, cmd)
        return batches

    def js_like_fmt(fs: List[str]) -> List[List[str]]:
        cmd = _node_tool_cmd("prettier", ["--loglevel", "warn", "--write"])
        return _batch(fs, cmd) if cmd else []

    def c_like_fmt(fs: List[str]) -> List[List[str]]:
        return _batch(fs, ["clang-format", "-i"]) if _cmd_exists("clang-format") else []

    def sh_fmt(fs: List[str]) -> List[List[str]]:
        return _batch(fs, ["shfmt", "-w"]) if _cmd_exists("shfmt") else []

    def rs_fmt(fs: List[str]) -> List[List[str]]:
        return _batch(fs, ["rustfmt"]) if _cmd_exists("rustfmt") else []

    def go_fmt(fs: List[str]) -> List[List[str]]:
        return _batch(fs, ["gofmt", "-w"]) if _cmd_exists("gofmt") else []

    fmts: Dict[str, Callable[[List[str]], List[List[str]]]] = {
        "py": py_fmt,
        "js": js_like_fmt, "jsx": js_like_fmt, "ts": js_like_fmt, "tsx": js_like_fmt,
        "json": js_like_fmt, "css": js_like_fmt, "scss": js_like_fmt,
        "md": js_like_fmt, "html": js_like_fmt, "yml": js_like_fmt, "yaml": js_like_fmt,
        "c": c_like_fmt, "h": c_like_fmt, "cc": c_like_fmt, "cpp": c_like_fmt, "hpp": c_like_fmt,
        "sh": sh_fmt, "bash": sh_fmt, "zsh": sh_fmt,
        "rs": rs_fmt,
        "go": go_fmt,
    }
    return fmts

def make_linters(autofix: bool) -> Dict[str, Callable[[List[str]], List[List[str]]]]:
    def js_lint(fs: List[str]) -> List[List[str]]:
        cmd = _node_tool_cmd("eslint", ["--max-warnings=0"] + (["--fix"] if autofix else []))
        return _batch(fs, cmd) if cmd else []

    def py_lint(fs: List[str]) -> List[List[str]]:
        # Prefer binary; otherwise python -m ruff
        cmd = (["ruff", "check"] + (["--fix"] if autofix else [])
               if _cmd_exists("ruff")
               else (_python_module_cmd("ruff", ["check"] + (["--fix"] if autofix else [])) or []))
        return _batch(fs, cmd) if cmd else []

    def sh_lint(fs: List[str]) -> List[List[str]]:
        return _batch(fs, ["shellcheck", "-x"]) if _cmd_exists("shellcheck") else []

    def yml_lint(fs: List[str]) -> List[List[str]]:
        return _batch(fs, ["yamllint", "-s"]) if _cmd_exists("yamllint") else []

    def md_lint(fs: List[str]) -> List[List[str]]:
        # Try markdownlint-cli2, then markdownlint; prefer --fix if allowed
        if _cmd_exists("markdownlint-cli2"):
            return _batch(fs, ["markdownlint-cli2"] + (["--fix"] if autofix else []))
        if _cmd_exists("markdownlint"):
            return _batch(fs, ["markdownlint"] + (["--fix"] if autofix else []))
        return []

    def rs_lint(_: List[str]) -> List[List[str]]:
        # clippy is repo-wide; keep optional to avoid slowdowns on single-file edits
        return [["cargo", "clippy", "--quiet", "--", "-D", "warnings"]] if _cmd_exists("cargo") else []

    def go_lint(_: List[str]) -> List[List[str]]:
        # golangci-lint typically runs per-module; leave as optional
        return [["golangci-lint", "run", "--out-format=tab"]] if _cmd_exists("golangci-lint") else []

    lints: Dict[str, Callable[[List[str]], List[List[str]]]] = {
        "py": py_lint,
        "js": js_lint, "jsx": js_lint, "ts": js_lint, "tsx": js_lint,
        "sh": sh_lint, "bash": sh_lint, "zsh": sh_lint,
        "yml": yml_lint, "yaml": yml_lint,
        "md": md_lint,
        "rs": rs_lint,
        "go": go_lint,
        "c": lambda _fs: [], "h": lambda _fs: [], "cc": lambda _fs: [], "cpp": lambda _fs: [], "hpp": lambda _fs: [],
    }
    return lints

# ---------- orchestration ----------

def run_batches(batches: List[List[str]], verbose: bool) -> Tuple[int, List[Dict[str, Any]]]:
    results: List[Dict[str, Any]] = []
    worst_rc = 0
    for cmd in batches:
        if not cmd:
            continue
        rc, out, err = _capture_run(cmd)
        if verbose:
            print("$ " + " ".join(shlex.quote(x) for x in cmd))
            if out:
                print(out)
            if err:
                print(err, file=sys.stderr)
        results.append({"cmd": cmd, "rc": rc, "stdout": out, "stderr": err})
        if rc != 0 and worst_rc == 0:
            worst_rc = rc
    return worst_rc, results

def do_format(files: List[str], verbose: bool) -> Tuple[int, List[Dict[str, Any]]]:
    fmts = make_formatters()
    grouped = group_by_ext(files)
    batches: List[List[str]] = []
    covered: Set[str] = set()
    for ext, fs in grouped.items():
        if ext in fmts:
            batches += fmts[ext](fs)
            covered.update(fs)
    # Fallback: for remaining text-like files, use dprint if present
    remaining = [f for f in files if f not in covered]
    if remaining and _cmd_exists("dprint"):
        batches += _batch(remaining, ["dprint", "fmt"])
    return run_batches(batches, verbose)

def do_lint(files: List[str], verbose: bool, autofix: bool) -> Tuple[int, List[Dict[str, Any]]]:
    lints = make_linters(autofix=autofix)
    grouped = group_by_ext(files)
    batches: List[List[str]] = []
    for ext, fs in grouped.items():
        if ext in lints:
            batches += lints[ext](fs)
    return run_batches(batches, verbose)

def print_report(status: str, files: List[str], fmt_res: List[Dict[str, Any]], lint_res: List[Dict[str, Any]], note: str = "") -> None:
    report = {
        "status": status,                   # "ok" | "tool_error" | "lint_errors"
        "files": files,
        "formatting": fmt_res,
        "linting": lint_res,
        "note": note,
        "suggestion": (
            "Non-auto-fixable diagnostics remain. Ask Claude to reason about the errors, propose a patch, and re-run the hook."
            if status == "lint_errors" else
            ("Some tools are missing. Install/pin them or adjust settings; Claude can also add them to the toolchain."
             if status == "tool_error" else "")
        ),
    }
    print("BEGIN_HOOK_REPORT")
    print(json.dumps(report, indent=2))
    print("END_HOOK_REPORT")

# ---------- entrypoint ----------

def main(argv: List[str]) -> int:
    ap = argparse.ArgumentParser(description="Format/lint only updated files; emit diagnostics for Claude.")
    ap.add_argument("--mode", choices=["staged", "updated"], default="staged",
                    help="If no files are passed, choose discovery mode.")
    ap.add_argument("--action", choices=["format", "lint", "fix"], default="fix",
                    help="'fix' = format then lint (default).")
    ap.add_argument("--no-autofix-lint", dest="autofix_lint", action="store_false",
                    help="Do not attempt automatic lint fixes.")
    ap.add_argument("-v", "--verbose", action="store_true")
    ap.add_argument("files", nargs="*")
    args = ap.parse_args(argv)

    # Discover files
    files = args.files or (git_staged_files() if args.mode == "staged" else git_updated_vs_head())
    tracked_exts = set(make_formatters().keys()) | set(make_linters(True).keys())
    files = filter_supported(files, tracked_exts)

    if not files:
        if args.verbose:
            print("No supported updated files.")
        print_report(status="ok", files=[], fmt_res=[], lint_res=[], note="No files")
        return 0

    fmt_rc = 0
    fmt_res: List[Dict[str, Any]] = []
    lint_rc = 0
    lint_res: List[Dict[str, Any]] = []

    if args.action in ("format", "fix"):
        fmt_rc, fmt_res = do_format(files, args.verbose)

    if args.action in ("lint", "fix"):
        lint_rc, lint_res = do_lint(files, args.verbose, autofix=args.autofix_lint)

    # Determine outcome.
    # Treat missing tools or invocation failures as action-required (exit 2) so Claude can fix dependencies.
    def _is_tool_missing(r: Dict[str, Any]) -> bool:
        s = (r.get("stderr") or "").lower()
        return r.get("rc") in (127, 126) or "command not found" in s or "not found:" in s

    any_tool_fail = any(_is_tool_missing(r) for r in (fmt_res + lint_res))
    if any_tool_fail:
        print_report("tool_error", files, fmt_res, lint_res, note="Some tools are missing or failed to invoke.")
        # Also print a short stderr line so the runner never shows an empty message
        print("after_edit.py: tool error — see BEGIN_HOOK_REPORT for details.", file=sys.stderr)
        return 2

    if lint_rc != 0:
        print_report("lint_errors", files, fmt_res, lint_res)
        return 2

    print_report("ok", files, fmt_res, lint_res)
    return 0

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))