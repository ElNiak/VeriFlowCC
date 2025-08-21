# .claude/hooks/PostToolUse/after_edit.py
# Purpose: Format & lint only files actually touched by this tool call, falling back to git-detected changes.
# Behavior: Exit 0 (clean or only auto-fixes), Exit 2 (action needed: lint/tool issues). Always prints BEGIN/END report.

from __future__ import annotations

import argparse
import fnmatch
import json
import shlex
import subprocess
import sys
from pathlib import Path
from shutil import which
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable

# ---------- envelope parsing (so we see freshly Written files) ----------


def _read_envelope() -> dict[str, Any]:
    try:
        data = sys.stdin.read()
        if not data.strip():
            return {}
        return json.loads(data)
    except Exception:
        return {}


def _walk_paths(x: Any, out: list[str]) -> None:
    if isinstance(x, dict):
        # common Write/Edit shapes: {"path": "...", "content": "..."} or nested lists
        if "path" in x and isinstance(x["path"], str):
            out.append(x["path"])
        for v in x.values():
            _walk_paths(v, out)
    elif isinstance(x, list):
        for it in x:
            _walk_paths(it, out)


def extract_paths_from_envelope(env: dict[str, Any]) -> list[str]:
    tool = env.get("tool_name")
    if tool not in ("Write", "Edit", "MultiEdit"):
        return []
    ti = env.get("tool_input")
    paths: list[str] = []
    _walk_paths(ti, paths)
    # Preserve order but dedupe
    seen = set()
    dedup = []
    for p in paths:
        if p not in seen:
            dedup.append(p)
            seen.add(p)
    return dedup


# ---------- helpers ----------


def _cmd_exists(cmd: str) -> bool:
    return which(cmd) is not None


def _python_module_cmd(module: str, args: list[str]) -> list[str] | None:
    py = which("python3") or which("python")
    return [py, "-m", module, *args] if py else None


def _node_tool_cmd(bin_name: str, args: list[str]) -> list[str] | None:
    if _cmd_exists(bin_name):
        return [bin_name, *args]
    if _cmd_exists("npx"):
        return ["npx", "--yes", bin_name, *args]
    return None


def _batch(
    files: list[str], base: list[str] | None, max_args: int = 200
) -> list[list[str]]:
    if not base:
        return []
    chunks: list[list[str]] = []
    cur: list[str] = []
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


def _capture_run(cmd: list[str]) -> tuple[int, str, str]:
    try:
        proc = subprocess.run(cmd, text=True, capture_output=True)  # noqa: S603
        return proc.returncode, (proc.stdout or "").strip(), (proc.stderr or "").strip()
    except FileNotFoundError:
        return 127, "", f"Command not found: {cmd[0]}"
    except Exception as e:
        return 1, "", f"{type(e).__name__}: {e}"


# ---------- discovery (git + untracked) ----------


def git_staged_files() -> list[str]:
    try:
        out = subprocess.check_output(
            [  # noqa: S607
                "git",
                "diff",
                "--cached",
                "--name-only",
                "--diff-filter=ACM",
            ],
            text=True,
        )
        return [ln for ln in out.splitlines() if ln.strip()]
    except subprocess.CalledProcessError:
        return []


def git_updated_vs_head() -> list[str]:
    try:
        out = subprocess.check_output(
            ["git", "diff", "HEAD", "--name-only", "--diff-filter=ACM"],  # noqa: S607
            text=True,
        )
        return [ln for ln in out.splitlines() if ln.strip()]
    except subprocess.CalledProcessError:
        return []


def git_untracked() -> list[str]:
    # freshly Written files will appear here
    try:
        out = subprocess.check_output(
            ["git", "ls-files", "--others", "--exclude-standard"],  # noqa: S607
            text=True,
        )
        return [ln for ln in out.splitlines() if ln.strip()]
    except subprocess.CalledProcessError:
        return []


def filter_supported(
    files: Iterable[str], exts: set[str], exclude_globs: list[str]
) -> list[str]:
    res: list[str] = []
    for f in files:
        p = Path(f)
        if not p.is_file():
            continue
        if any(fnmatch.fnmatchcase(str(p), g) for g in exclude_globs):
            continue
        if _ext(p) in exts:
            res.append(str(p))
    return res


def group_by_ext(files: list[str]) -> dict[str, list[str]]:
    g: dict[str, list[str]] = {}
    for f in files:
        g.setdefault(_ext(Path(f)), []).append(f)
    return g


# ---------- command maps ----------


def make_formatters() -> dict[str, Callable[[list[str]], list[list[str]]]]:
    def py_fmt(fs: list[str]) -> list[list[str]]:
        batches: list[list[str]] = []
        cmd = (
            ["black", "--quiet"]
            if _cmd_exists("black")
            else _python_module_cmd("black", ["--quiet"])
        )
        batches += _batch(fs, cmd)
        cmd = (
            ["isort", "--quiet"]
            if _cmd_exists("isort")
            else _python_module_cmd("isort", ["--quiet"])
        )
        batches += _batch(fs, cmd)
        return batches

    def js_like_fmt(fs: list[str]) -> list[list[str]]:
        # fix flag name: --log-level
        cmd = _node_tool_cmd("prettier", ["--log-level", "warn", "--write"])
        return _batch(fs, cmd)

    def c_like_fmt(fs: list[str]) -> list[list[str]]:
        return _batch(fs, ["clang-format", "-i"]) if _cmd_exists("clang-format") else []

    def sh_fmt(fs: list[str]) -> list[list[str]]:
        return _batch(fs, ["shfmt", "-w"]) if _cmd_exists("shfmt") else []

    def rs_fmt(fs: list[str]) -> list[list[str]]:
        return _batch(fs, ["rustfmt"]) if _cmd_exists("rustfmt") else []

    def go_fmt(fs: list[str]) -> list[list[str]]:
        return _batch(fs, ["gofmt", "-w"]) if _cmd_exists("gofmt") else []

    return {
        "py": py_fmt,
        "js": js_like_fmt,
        "jsx": js_like_fmt,
        "ts": js_like_fmt,
        "tsx": js_like_fmt,
        "json": js_like_fmt,
        "css": js_like_fmt,
        "scss": js_like_fmt,
        "md": js_like_fmt,
        "html": js_like_fmt,
        "yml": js_like_fmt,
        "yaml": js_like_fmt,
        "c": c_like_fmt,
        "h": c_like_fmt,
        "cc": c_like_fmt,
        "cpp": c_like_fmt,
        "hpp": c_like_fmt,
        "sh": sh_fmt,
        "bash": sh_fmt,
        "zsh": sh_fmt,
        "rs": rs_fmt,
        "go": go_fmt,
    }


def make_linters(autofix: bool) -> dict[str, Callable[[list[str]], list[list[str]]]]:
    def js_lint(fs: list[str]) -> list[list[str]]:
        cmd = _node_tool_cmd(
            "eslint", ["--max-warnings=0"] + (["--fix"] if autofix else [])
        )
        return _batch(fs, cmd)

    def py_lint(fs: list[str]) -> list[list[str]]:
        cmd = (
            ["ruff", "check"] + (["--fix"] if autofix else [])
            if _cmd_exists("ruff")
            else _python_module_cmd("ruff", ["check"] + (["--fix"] if autofix else []))
        )
        return _batch(fs, cmd)

    def sh_lint(fs: list[str]) -> list[list[str]]:
        return _batch(fs, ["shellcheck", "-x"]) if _cmd_exists("shellcheck") else []

    def yml_lint(fs: list[str]) -> list[list[str]]:
        return _batch(fs, ["yamllint", "-s"]) if _cmd_exists("yamllint") else []

    def md_lint(fs: list[str]) -> list[list[str]]:
        if _cmd_exists("markdownlint-cli2"):
            return _batch(fs, ["markdownlint-cli2"] + (["--fix"] if autofix else []))
        if _cmd_exists("markdownlint"):
            return _batch(fs, ["markdownlint"] + (["--fix"] if autofix else []))
        return []

    def rs_lint(_: list[str]) -> list[list[str]]:
        return (
            [["cargo", "clippy", "--quiet", "--", "-D", "warnings"]]
            if _cmd_exists("cargo")
            else []
        )

    def go_lint(_: list[str]) -> list[list[str]]:
        return (
            [["golangci-lint", "run", "--out-format=tab"]]
            if _cmd_exists("golangci-lint")
            else []
        )

    return {
        "py": py_lint,
        "js": js_lint,
        "jsx": js_lint,
        "ts": js_lint,
        "tsx": js_lint,
        "sh": sh_lint,
        "bash": sh_lint,
        "zsh": sh_lint,
        "yml": yml_lint,
        "yaml": yml_lint,
        "md": md_lint,
        "rs": rs_lint,
        "go": go_lint,
        "c": lambda _fs: [],
        "h": lambda _fs: [],
        "cc": lambda _fs: [],
        "cpp": lambda _fs: [],
        "hpp": lambda _fs: [],
    }


# ---------- orchestration ----------


def run_batches(
    batches: list[list[str]], verbose: bool
) -> tuple[int, list[dict[str, Any]]]:
    results: list[dict[str, Any]] = []
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


def do_format(files: list[str], verbose: bool) -> tuple[int, list[dict[str, Any]]]:
    fmts = make_formatters()
    grouped = group_by_ext(files)
    batches: list[list[str]] = []
    covered: set[str] = set()
    for ext, fs in grouped.items():
        if ext in fmts:
            batches += fmts[ext](fs)
            covered.update(fs)
    remaining = [f for f in files if f not in covered]
    if remaining and _cmd_exists("dprint"):
        batches += _batch(remaining, ["dprint", "fmt"])
    return run_batches(batches, verbose)


def do_lint(
    files: list[str], verbose: bool, autofix: bool
) -> tuple[int, list[dict[str, Any]]]:
    lints = make_linters(autofix=autofix)
    grouped = group_by_ext(files)
    batches: list[list[str]] = []
    for ext, fs in grouped.items():
        if ext in lints:
            batches += lints[ext](fs)
    return run_batches(batches, verbose)


def print_report(
    status: str,
    files: list[str],
    fmt_res: list[dict[str, Any]],
    lint_res: list[dict[str, Any]],
    note: str = "",
) -> None:
    report = {
        "status": status,  # "ok" | "tool_error" | "lint_errors"
        "files": files,
        "formatting": fmt_res,
        "linting": lint_res,
        "note": note,
        "suggestion": (
            "Non-auto-fixable linting diagnostics remain. Apply immediately command @.claude/commands/pre-commit.md."
            if status == "lint_errors"
            else (
                "Some tools are missing. Install/pin them or adjust settings."
                if status == "tool_error"
                else ""
            )
        ),
    }
    print("BEGIN_HOOK_REPORT", file=sys.stderr if status != "ok" else sys.stdout)
    print(
        json.dumps(report, indent=2), file=sys.stderr if status != "ok" else sys.stdout
    )
    print("END_HOOK_REPORT", file=sys.stderr if status != "ok" else sys.stdout)


# ---------- entrypoint ----------


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(
        description="Format/lint updated files; envelope-aware."
    )
    ap.add_argument("--mode", choices=["staged", "updated"], default="updated")
    ap.add_argument("--action", choices=["format", "lint", "fix"], default="fix")
    ap.add_argument("--no-autofix-lint", dest="autofix_lint", action="store_false")
    ap.add_argument("-v", "--verbose", action="store_true")
    ap.add_argument("files", nargs="*")
    args = ap.parse_args(argv)

    env = _read_envelope()
    env_paths = extract_paths_from_envelope(env)

    # Fallback discovery
    discovered = args.files or (
        git_staged_files() if args.mode == "staged" else git_updated_vs_head()
    )
    # Include untracked so new Writes are seen
    discovered += git_untracked()

    # Merge (preserve order, dedupe)
    merged: list[str] = []
    seen: set[str] = set()
    for p in env_paths + discovered:
        if p and p not in seen:
            merged.append(p)
            seen.add(p)

    # Exclude internal hook logs/noisy paths
    exclude = [
        ".claude/hooks/*.json",
        ".claude/hooks/**/*.json",
    ]

    tracked_exts = set(make_formatters().keys()) | set(make_linters(True).keys())
    files = filter_supported(merged, tracked_exts, exclude)

    if not files:
        if args.verbose:
            print("No supported files to process.")
        print_report("ok", [], [], [], note="No files")
        return 0

    fmt_rc, fmt_res = (0, [])
    lint_rc, lint_res = (0, [])

    if args.action in ("format", "fix"):
        fmt_rc, fmt_res = do_format(files, args.verbose)

    if args.action in ("lint", "fix"):
        lint_rc, lint_res = do_lint(files, args.verbose, autofix=args.autofix_lint)

    # Outcome: treat missing tools as action required → exit 2 (agent can install them)
    def _tool_missing(r: dict[str, Any]) -> bool:
        s = (r.get("stderr") or "").lower()
        return (
            r.get("rc") in (127, 126) or "command not found" in s or "not found:" in s
        )

    any_tool_fail = any(_tool_missing(r) for r in (fmt_res + lint_res))
    if any_tool_fail:
        print_report(
            "tool_error",
            files,
            fmt_res,
            lint_res,
            note="Some tools are missing or failed.",
        )
        print("after_edit.py: tool error — see BEGIN_HOOK_REPORT.", file=sys.stderr)
        return 2

    if lint_rc != 0:
        print_report("lint_errors", files, fmt_res, lint_res)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
