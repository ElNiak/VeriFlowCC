# Purpose: Format & lint only updated files; emit actionable diagnostics for Claude-code.
# Notes:
# - Returns 0 when clean (or only auto-fixes applied), 2 if lint errors remain, 1 on tool failure.
# - Prints a JSON summary between BEGIN_HOOK_REPORT/END_HOOK_REPORT for programmatic use.

from __future__ import annotations
import argparse
import json
import shlex
import subprocess
import sys
from pathlib import Path
from shutil import which
from typing import Iterable, List, Dict, Tuple, Callable, Set, Any

# ---------- helpers ----------

def _cmd_exists(cmd: str) -> bool:
    return which(cmd) is not None

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
        return proc.returncode, proc.stdout.strip(), proc.stderr.strip()
    except FileNotFoundError:
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
    fmts: Dict[str, Callable[[List[str]], List[List[str]]]] = {
        "py": lambda fs: (
            ([] if not _cmd_exists("black") else _batch(fs, ["black", "--quiet"])) +
            ([] if not _cmd_exists("isort") else _batch(fs, ["isort", "--quiet"]))
        ),
        "js": lambda fs: ([] if not _cmd_exists("prettier") else _batch(fs, ["prettier", "--loglevel", "warn", "--write"])),
        "jsx": lambda fs: fmts["js"](fs),
        "ts": lambda fs: fmts["js"](fs),
        "tsx": lambda fs: fmts["js"](fs),
        "json": lambda fs: fmts["js"](fs),
        "css": lambda fs: fmts["js"](fs),
        "scss": lambda fs: fmts["js"](fs),
        "md": lambda fs: fmts["js"](fs),
        "html": lambda fs: fmts["js"](fs),
        "yml": lambda fs: fmts["js"](fs),
        "yaml": lambda fs: fmts["js"](fs),
        "c": lambda fs: ([] if not _cmd_exists("clang-format") else _batch(fs, ["clang-format", "-i"])),
        "h": lambda fs: fmts["c"](fs),
        "cc": lambda fs: fmts["c"](fs),
        "cpp": lambda fs: fmts["c"](fs),
        "hpp": lambda fs: fmts["c"](fs),
        "sh": lambda fs: ([] if not _cmd_exists("shfmt") else _batch(fs, ["shfmt", "-w"])),
        "bash": lambda fs: fmts["sh"](fs),
        "zsh": lambda fs: fmts["sh"](fs),
        "rs": lambda fs: ([] if not _cmd_exists("rustfmt") else _batch(fs, ["rustfmt"])),
        "go": lambda fs: ([] if not _cmd_exists("gofmt") else _batch(fs, ["gofmt", "-w"])),
    }
    return fmts

def make_linters(autofix: bool) -> Dict[str, Callable[[List[str]], List[List[str]]]]:
    def js_lint(fs: List[str]) -> List[List[str]]:
        if not _cmd_exists("eslint"):
            return []
        base = ["eslint"]
        if autofix:
            base.append("--fix")
        return _batch(fs, base)

    def py_lint(fs: List[str]) -> List[List[str]]:
        if not _cmd_exists("ruff"):
            return []
        base = ["ruff", "check"]
        if autofix:
            base.append("--fix")
        return _batch(fs, base)

    lints: Dict[str, Callable[[List[str]], List[List[str]]]] = {
        "py": py_lint,
        "js": js_lint,
        "jsx": js_lint,
        "ts": js_lint,
        "tsx": js_lint,
        "sh": lambda fs: ([] if not _cmd_exists("shellcheck") else _batch(fs, ["shellcheck", "-x"])),
        "bash": lambda fs: lints["sh"](fs),
        "zsh": lambda fs: lints["sh"](fs),
        "yml": lambda fs: ([] if not _cmd_exists("yamllint") else _batch(fs, ["yamllint", "-s"])),
        "yaml": lambda fs: lints["yml"](fs),
        "md": lambda fs: (
            _batch(fs, ["markdownlint-cli2", "--fix"]) if _cmd_exists("markdownlint-cli2") and autofix
            else (_batch(fs, ["markdownlint-cli2"]) if _cmd_exists("markdownlint-cli2")
                  else (_batch(fs, ["markdownlint", "--fix"]) if _cmd_exists("markdownlint") and autofix
                        else (_batch(fs, ["markdownlint"]) if _cmd_exists("markdownlint") else [])))
        ),
        "rs": lambda fs: ([] if not _cmd_exists("cargo") else [["cargo", "clippy", "--quiet", "--", "-D", "warnings"]]),
        "go": lambda fs: ([] if not _cmd_exists("golangci-lint") else _batch(fs, ["golangci-lint", "run", "--out-format=tab"])),
        "c": lambda fs: [],
        "h": lambda fs: [],
        "cc": lambda fs: [],
        "cpp": lambda fs: [],
        "hpp": lambda fs: [],
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
        elif rc != 0:
            # keep first nonzero as representative; still record each
            pass
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
    # Fallback to dprint for remaining texty files
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
            if status == "lint_errors" else ""
        ),
    }
    # Machine-readable block for Claude-code or scripts
    print("BEGIN_HOOK_REPORT")
    print(json.dumps(report, indent=2))
    print("END_HOOK_REPORT")

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

    # discover files
    files = args.files or (git_staged_files() if args.mode == "staged" else git_updated_vs_head())
    tracked_exts = set(make_formatters()) | set(make_linters(True))
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

    # Decide outcome:
    # - tool failure (rc >= 126 typical for missing tool) → exit 1
    # - lint errors (nonzero) → exit 2
    # - ok → exit 0
    any_tool_fail = any(r["rc"] in (127, 126, 1) and ("not found" in (r["stderr"] or "").lower()) for r in (fmt_res + lint_res))
    if any_tool_fail:
        print_report("tool_error", files, fmt_res, lint_res, note="Some tools are missing or failed.")
        return 1

    if lint_rc != 0:
        print_report("lint_errors", files, fmt_res, lint_res)
        return 2

    print_report("ok", files, fmt_res, lint_res)
    return 0

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))