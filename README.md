# AgileVerifFlowCC — Agent‑Driven Agile V&V with Claude Code + MCP

> **Purpose.** Automate an [Agile V-Model](https://aiotplaybook.org/index.php?title=Agile_V-Model) (planning → requirements → design → coding → testing → integration → validation) with specialized Claude Code instances wrapped in VeriFlow CLI and its sub‑agents, **Model Context Protocol (MCP)** tools, and **client‑side verification** (tests/linters run locally).

The goal is to **reduce hallucinations & context drift** using **context template injection**, persistent project memory, and gated verification at every step.

We focus on implementation of cheap context oriented engineering, agent orchestration, and a **plan-then-act** workflow that ensures each feature is developed with clear requirements, design, coding, testing, and validation steps.

Focusing on sequential execution of subagents and tools since, context engineering consider:

- context windows size (around 200k in total)
- agents have their own context
- action carry implicit and explicit decision on context
- context carry implicit and explicit decisions on actions
- the shared context between agents and the non-shared context between agents

______________________________________________________________________

## Why this project?

Modern coding agents are powerful but drift without structure. AgileVerifFlowCC enforces a **documented, test‑first flow** where each V‑phase is handled by a focused sub‑agent with a **scoped context window**. We externalize long‑lived state into files/memory so agents can **read/write “ground truth”** rather than relying on chat history. MCP adds a **standard tool bus** for agents to call linters, run tests, access Git, and query knowledge sources—**without bespoke glue code per tool**.

______________________________________________________________________

## Key Ideas (TL;DR)

- **V‑Model, per sprint:** every story goes from planning → … → validation, and only progresses when gates pass.
- **Specialized sub‑agents:** requirements analyst, architect, developer, tester, reviewer—each with **its own prompt + context**.
- **Context engineering:** Jinja2 templates + project memory (**`CLAUDE.md`**, `/docs`, `/state`) feed only relevant inputs to each agent.
- **Client‑side verification:** tests, linters, type checkers, and formatters run **locally via MCP tools**; failing gates trigger fix loops.
- **MCP integration:** standardized tool access (filesystems, Git, CI, web search, knowledge) + discovery via **`.mcp.json`**.
- **Long‑context strategy:** don’t just “stuff more tokens.” Persist and select **grounded** context, summarize aggressively, and use tools.

______________________________________________________________________

## Tech Stack

- **Python CLI** (Typer) orchestrator with **uv** for packaging/running
- **Claude Code**: CLI & **SDK (Python/TS)** for sub‑agents and tool use

> *Authentication Disclaimer*: VeriFlowCC requires Claude Code authentication to function properly. Users must ensure their environment is configured with appropriate authentication methods through VeriFlow's guidelines before using this tool. The system supports flexible authentication approaches without requiring specific setup steps in this documentation.

- **Jinja2** for prompt/context templates
- **Pydantic** for validating agent IO (JSON contracts)
- **Git** for checkpoints; optional **pre‑commit** with **Ruff/Mypy/Black**
- **MCP** servers for filesystem, Git/GitHub, lint/test execution, web/research

> *Works cross‑project*: use this orchestrator and templates **inside any repo** to turn its backlog into verified code changes.

______________________________________________________________________

## Installation (with `uv`)

```bash
# 1) Create env
uv venv
source .venv/bin/activate

# 2) Install CLI + dev tooling (adjust extras as needed)
uv pip install -e ".[dev]"

# Or minimal runtime:
# uv pip install -e .

# 3) Install Claude Code (required for sub‑agents & tools)
npm install -g @anthropic-ai/claude-code

# 4) Verify Claude Code + SDK availability
claude --help
python -c "import claude_code_sdk; print('ok')"
```

**Prereqs:** Python ≥3.10, Node.js ≥18, Git. Set API keys for MCP servers you enable.

______________________________________________________________________

## Quick Start

```bash
# Initialize Agile V&V scaffolding in the current repo (Sprint 0)
uv run veriflowcc init

# Plan the sprint
uv run veriflowcc plan

# Run one sprint (next story in backlog)
uv run veriflowcc sprint

# Optional: interactive REPL session (pause/inspect/fix between gates)
uv run veriflowcc repl
```

```bash
VeriFlowCC on  context-subagent-standardization [$✘!?] via 🐍 v3.8.0
❯ uv run verifflowcc
╭─────────────────────────────────────────────── Authentication Notice ───────────────────────────────────────────────╮
│ Authentication Required: VeriFlowCC requires Claude Code authentication.                                            │
│ Please configure through VeriFlow's guidelines before using this tool.                                              │
╰─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯

 Usage: verifflowcc [OPTIONS] COMMAND [ARGS]...

 VeriFlowCC - Agile V-Model development pipeline command center. Requires Claude Code authentication.


╭─ Options ───────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ --version  -v        Show version information                                                                       │
│ --help               Show this message and exit.                                                                    │
╰─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Commands ──────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ init         Initialize a new VeriFlowCC project.                                                                   │
│ plan         Plan a new sprint with story selection and refinement.                                                 │
│ sprint       Execute a sprint with the Agile V-Model workflow.                                                      │
│ status       Show project status and current V-Model stage.                                                         │
│ validate     Validate the current sprint against acceptance criteria.                                               │
│ checkpoint   Create or manage checkpoints                                                                           │
╰─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
```

______________________________________________________________________

## Why this exists

- **Agentic Agile V&V**: Each V‑Model stage is driven by a dedicated Claude **sub‑agent** with scoped, template‑built context. Outputs are structured (docs, code, tests) and verified in‑loop.
- **Dynamic context**: Prompts are composed at runtime from **Jinja2** templates + project memory (e.g., `CLAUDE.md`, run artifacts). The orchestrator injects only the relevant slices.
- **Client‑side verification**: Generated code is linted, type‑checked, and tested locally (shell tools, test runners) before being accepted.
- **Long‑context via MCP**: The **Model Context Protocol** exposes file systems, linters, search, planners, etc., as tools—letting agents read/write files, run checks, and persist plans **outside** the token window.

______________________________________________________________________

## Architecture (Orchestrator + Sub‑Agents)

```
User/CLI ──▶ Orchestrator
               ├─ Requirements Agent
               ├─ Architect Agent
               ├─ Coder Agent
               ├─ Lint/Fix Agent
               ├─ Test Agent
               └─ Validation Agent

Persistence & Context:
- Git history & checkpoints
- Memory files (CLAUDE.md, plan.json, run logs)
- Artifacts: {requirements.md, architecture.md, src/, tests/, reports/}

Tooling layer:
- MCP servers (files, planners, search, code exec, external APIs)
- Local runners (pytest, ruff, mypy, pre-commit)
```

**Key ideas**

- **Scoped prompts**: Each sub‑agent gets only the relevant inputs (requirements ⇒ design ⇒ code ⇒ tests).
- **Write context, don’t just chat**: Persist decisions and artifacts; inject them on demand.
- **Gating**: Advance to the next stage only when verification passes (configurable “soft/hard”).

______________________________________________________________________

## Project Structure

```text
.agilevv/                       # State & artifacts per sprint (requirements, test reports, summaries) generated by veriflowcc and its agents
   ├─ README.md
   ├─ catalog.yaml              # single source of truth: activities/steps/stories/releases
   ├─ vision.md
   ├─ story-map/
   │  └─ story_map.md           # overview (table + Mermaid)
   ├─ backlog/
   │  └─ backlog.csv            # flattened view, easy to sort/filter
   ├─ stories/                  # one file per story with acceptance criteria
   │  └─ ACT-01/
   │     └─ STEP-01/
   │        └─ STO-0001.md
   ├─ releases/
   │  ├─ R1.yaml
   │  └─ R2.yaml
   ├─ roadmap/
   │  └─ gantt.md
   ├─ traceability.md           # story ↔ code ↔ test ↔ docs
   └─ _generated/               # auto-indexes, don’t edit by hand
.claude/                 # Agent instructions & Jinja2 prompt templates (role‑scoped)
   ├─  settings.local.json  # Local overrides (MCP servers, verbosity, dry-run, etc.)
   ├─ memory/              # durable notes (summaries, decisions) referenced across sprints
   ├─ hooks/                 # pre/post user prompt hooks
   ├─ commands/              # simple commands (create-spec, review-spec, etc.)
   ├─ instructions/          # core instructions (V‑Model steps, pre-flight, spec review, etc.)
   ├─ agents/                # role‑specific instructions + schemas
   │  └─ generic/             # shared sub‑agents (file-creator, context-fetcher, etc.)
   │  └─ teams/               # role-specific sub-agents (implementer, test-runner, etc.)
.mcp.json                # MCP servers & tool discovery
CLAUDE.md                # Project rules, coding conventions, FAQs (auto‑included by Claude Code)
docs/                    # Human‑readable docs
src/                      # Your source code (created/edited by agents within gated flow)
   ├─ __init__.py
   ├─ cli.py                  # Your main application entrypoint
   ├─ templates/              # Jinja templates (if applicable)
    ├─ contexts/            # Context templates (e.g., CLAUDE.md snippets, agent input/output, file excerpts)
    ├─ instructions/        # Instruction templates (e.g., create-spec, test-plan, create-task, etc.). Dynamic version of .claude/instructions/core/
    ├─ personas/            # Persona templates (e.g., requirements, architect, developer, tester, reviewer, etc.)
    ├─ hooks/               # Hook templates (e.g., pre/post user prompt, etc.)
    ├─ policies/            # Policy templates (e.g., security, compliance, etc.)
    ├─ requirements/        # Requirement templates (e.g., functional, non-functional, etc.)
    └─ agents/              # Agent templates
         ├─ helpers/         # Shared partials (e.g., file creator, context fetcher, etc.)
         └─ teams/           # Team‑specific templates (e.g., implementer, test-runner, code-reviewer, etc.)
    ├─ standards/           # Project-wide standards (e.g., coding conventions, best practices)
      ├─ <language>/         # Language-specific standards (e.g., python.md, js.md)
      ├─ <domain>/           # Domain-specific standards (e.g., web.md, cli.md, api.md)
      └─ <...>/              # Other categorizations as needed
    ├─ tools/                # Tool usage templates (e.g., read, write, grep, glob, bash, etc.)
   ├─ core/                   # Core logic for orchestration, V‑flow, and agent management
    ├─ sessions/             # Claude Code session management
    ├─ memory/               # Project memory management (summaries, decisions)
    ├─ vmodel/               # V‑Model flow logic
    └─ <...>/                # Other categorizations as needed
    └─ orchestrator.py       # Main orchestrator logic for V‑Model flow
   ├─ utils/                  # Utility functions
   ├─ schemas/                # Pydantic models for agent IO validation
   ├─ agents/                 # Custom agent logic (if any)
   ├─ commands/               # CLI commands
   ├─ validation/             # Validation logic
    ├─ code/                 # Code validation (linting, type checking)
    ├─ tests/                # Test validation (test discovery, execution)
    ├─ vmodel/               # V‑Model specific validation
    └─ project/              # Project‑specific validation (e.g., spec completeness)
tests/                    # tests
```

______________________________________________________________________

## Template Source of Truth → `.claude/` Generation

**Canonical templates live in the *main project*** and define the **inputs/outputs**, **persona instructions**, **standards**, and **context‑preserving sub‑agent** prompts. The **CLI uses the Claude Code SDK** to instantiate a Claude session and **render concrete documents into `.claude/`** for the current repository.

### Why this split?

- Keep **authoritative templates** versioned centrally (reuse across projects).
- Render **project‑specific instances** (with Jinja2 variables + memory) locally per repo.
- Allow upgrades: bump templates in the main project → re‑render here with no manual editing.

### How it works (at a glance)

1. Orchestrator loads a **template manifest** from the main project (packaged path or `AGILEVV_TEMPLATE_ROOT`).
1. Context is assembled (repo facts, backlog slice, memory summaries, file excerpts, failing traces).
1. The **Claude Code SDK** session is created; prompts are built from Jinja2 templates.
1. Outputs are **materialized under `.claude/`** (role folders + rendered instructions) and referenced by sub‑agents during the V‑flow.

> **Override the template root:** set `AGILEVV_TEMPLATE_ROOT=/path/to/main-project/templates`
> If unset, the packaged templates shipped with AgileVerifFlowCC are used.

### Contract guarantees

- **Idempotent:** safe to re‑run; only updates changed outputs.
- **Deterministic:** same inputs → same output files.
- **Validated:** rendered docs pass a schema check (Pydantic) before writing.

## MCP: How we use it (and why)

**What it gives us.** A **unified protocol** to connect agents to tools and data (filesystems, Git, linters, CI, web, DBs). Agents don’t need ad‑hoc integrations; they **discover** tools via `.mcp.json` and call them with a standard schema. This **solves the NxM “tool × model” problem**, keeps actions auditable, and lets us **externalize context** (read files, write memory, run tests) beyond the model’s token window.

**Your `.mcp.json` example (drop‑in):**

```jsonc
{
  "mcpServers": {
    "sequential-thinking": {
      "command": "npx",
      "args": ["-y", "mcp-sequentialthinking-tools"],
      "env": { "MAX_HISTORY_SIZE": "1000" }
    },
    "perplexity-ask": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "-e", "PERPLEXITY_API_KEY", "mcp/perplexity-ask"],
      "env": { "PERPLEXITY_API_KEY": "TODO-API-KEY" }
    },
    "context7": {
      "command": "npx",
      "args": ["-y", "@upstash/context7-mcp"],
      "type": "stdio"
    },
    "serena": {
      "command": "uvx",
      "args": [
        "--from", "git+https://github.com/oraios/serena",
        "serena-mcp-server",
        "--context", "ide-assistant",
        "--project", "${PWD}",
        "--tool-timeout", "20",
        "--mode", "planning",
        "--mode", "one-shot",
        "--enable-web-dashboard", "false"
      ],
      "type": "stdio"
    },
    "consult7": {
      "command": "uvx",
      "args": ["consult7", "google", "TODO-API-KEY"],
      "type": "stdio"
    }
  }
}
```

**Typical calls inside the flow:**

- *Filesystem:* read/write source files, inject file fragments into prompts, persist “memory” summaries.
- *Linters/formatters:* run Ruff/Black/pylint; return diagnostics + suggested fixes.
- *Type checks/tests:* run mypy/pytest and capture exit codes, failing traces.
- *Git:* `git diff` for review; checkpoint commits on green; branch per story.
- *Web/research:* controlled lookups (Perplexity/Context7); unify notes into `docs/` for auditability.

> **Design note:** Tools act as **ground truth**. The orchestrator trusts files, tests, and VCS state over model text. MCP makes those checks first‑class actions.

______________________________________________________________________

## Long‑Context Strategy

1. **Write, don’t remember:** persist decisions into `CLAUDE.md` and `.agilevv/memory/`.
1. **Select, don’t dump:** each sub‑agent’s prompt templates (Jinja2) inject only **relevant excerpts** (file slices, signatures, failing traces).
1. **Summarize aggressively:** after each gate, compress outputs into step summaries for future sprints.
1. **Verify continuously:** immediately run tests/linters on the client; sub‑agents fix until green.
1. **Parallelize safely:** orchestrator can spawn independent sub‑agents (code‑gen, lint‑fix) and then merge diffs under Git discipline.

> Even with very large model windows, **externalized state + selective injection** remains more reliable and cheaper than dumping entire codebases into prompts.

______________________________________________________________________

## CLI Commands

```bash
uv run veriflowcc init         # scaffold .agilevv/, .claude/, docs, example templates
uv run veriflowcc plan         # make an executable plan for the next story (saved to state + memory)
uv run veriflowcc sprint       # execute V‑Model gates for the current story
uv run veriflowcc repl         # interactive, confirm actions between gates
uv run veriflowcc status       # show artifacts, failing gates, next fixes
uv run veriflowcc agent lint   # run lint/format sub‑agent via MCP + auto‑fix loop
uv run veriflowcc agent test   # run test sub‑agent (pytest/mypy) with fix cycles
uv run veriflowcc agent gen    # code generation sub‑agent for a specific file/pattern
```

All commands honor `--dry-run`, `--verbose`, and `--hard-gates` (block on failures).

______________________________________________________________________

## Templates & Contracts

- **Prompt templates (`src/templates/*.j2`):** per role (requirements/design/dev/test/review). Keep **short, explicit** outputs (JSON/Pydantic models, diffs).
- **Schemas (Pydantic):** define structures for requirements, design notes, test results, and diffs; the orchestrator validates every agent response.
- **Memory rules:** what to persist (decisions, APIs, constants), where to read it, how to refresh summaries.

```jinja2
{# src/templates/dev_impl.j2 #}
## Task: Implement {{ story.title }}
### Acceptance criteria
{% for c in story.criteria -%}
- {{ c }}
{%- endfor %}

### Relevant code context
{% for f in files -%}
- {{ f.path }} — {{ f.summary }}
{%- endfor %}

### Output
Return ONLY a unified diff (udiff) against the working tree.
```

______________________________________________________________________

## Client‑Side Verification & Drift Guards

In order to ensure code quality and consistency throughout the development process using hooks and VeriflowCC,
Here is an example for a project using python, the following verification and drift guard measures are implemented:

- **Lint & format**: `ruff`, `black`, **auto‑fix** via Lint/Fix agent, commit only on clean tree.
- **Types**: `mypy` baseline enforced for changed files.
- **Tests**: Run focused `pytest -k <story>` after Coder; full suite on `integration` stage.
- **Token discipline**: cap context; summarize; prefer **file fetch via MCP** over raw text injection.
- **Traceability**: Every tool run emits artifacts (logs, junit XML, coverage) into `reports/` and links in the run summary.

______________________________________________________________________

## Security & Safety

- **Allowlist tools** only; prompt templates must never invoke arbitrary exec without user confirmation.
- **Sandbox execution** (Docker/uvx) for risky tools.
- **Git hygiene:** branch per story; checkpoint only on green; review diffs before merge.

______________________________________________________________________

## Roadmap

- Full template library per role + domain‑specific variants
- Rich **memory subsystem** (summaries, embeddings) with freshness policies
- **Hard/soft gating** modes + policy file (per project)
- Deeper MCP coverage (GitHub PRs, code search, LSIF/LSP hints)
- **Interactive TUI/REPL** for explain/fix‑then‑continue workflows
- Metrics dashboard (gate times, first‑pass success rate, rework cycles)
- CI that replays a sprint on sample projects (self‑test)
