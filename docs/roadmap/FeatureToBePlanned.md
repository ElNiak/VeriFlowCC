# VerifFlowCC – Agile V-&-V feature to be integrated

## 📐 VerifFlowCC – Agile V-&-V Session Orchestration

This feature adds **pause-and-resume workflow enforcement** to VerifFlowCC.
It guarantees that every Claude-Code session respects the Agile V-Model gates, even when you close your terminal, switch branches, or hand the task to a teammate.

---

### ✨ What’s inside

| Path / File | Purpose |
|-------------|---------|
| `.vv/state.json` | **Finite-state machine** – remembers current sprint & gate (`RequirementsVerifier`, `UnitVerifier`, …). |
| `sprints/<SPRINT_ID>/VV_DECISIONS.md` | Append-only **decision log** for that sprint. |
| `sprints/<SPRINT_ID>/artefacts/*` | Raw JSON evidence from each sub-agent (reqs, test reports, logs). |
| `~/.claude/hooks/before_*d/10-vv-gate.sh` | Claude-Code **hooks** that block tool calls not allowed by the current gate. |
| `orchestrator/validators.py` | **Pydantic** schemas – refuse malformed sub-agent JSON. |
| `vv resume` CLI cmd | Loads `state.json`, injects sprint memory, launches the next gate’s sub-agent. |

---

### 🚀 Quick-start

```bash
# 1 ·  launch a sprint
vv sprint-init S01

# 2 ·  let the planner create the roadmap
vv resume      # runs agile-vv-planner, sets stage → RequirementsVerifier

# 3 ·  approve requirements in GUI or CLI
vv resume      # triggers RequirementsVerifier agent

# … work through gates …
vv resume      # continues where you left off, every time
```

If you accidentally kill the session, just run `vv resume` again—state is persisted.

---

### 🔐 Gate logic (TL;DR)

* **Hooks** abort any `edit`, `write_code`, or `bash` call if `state.stage` doesn’t permit it.
* **Pydantic** stops hallucinated JSON from poisoning the next stage.
* **Git tags** mark every PASS: `git tag sprint-S01-Stage3_PASS`.

  * Roll back with: `git reset --hard sprint-S01-Stage2_PASS`.

---

### 🧩 Extending

* Add a new gate? Append its name to `stage_order` in `orchestrator/main.py`.
* Need CCID integration? Drop artefacts under `artefacts/`; they’ll be auto-summarised into context.

---

### 📚 References

* Anthropic Sub-Agent Hooks – June 2025 release notes
* AIoT Playbook – Agile V-Model ([https://aiotplaybook.org/index.php?title=Agile\_V-Model](https://aiotplaybook.org/index.php?title=Agile_V-Model))
* VerifFlowCC Architecture docs (`/docs/architecture.md`)

## Agent-OS - Integration Blueprint
**Bringing Agent-OS Utilities into VerifFlow CC’s Agile V-&-V Pipeline**

> **Repository** [Agent-OS](https://github.com/buildermethods/agent-os)
> **Status** DRAFT – for Sprint S02 planning meeting
> **Target release** v0.6.0 (end of Q3-2025)

---

### 1 Why integrate?

| Benefit | Agent-OS asset | Where it slots into VerifFlow CC |
|---------|---------------|----------------------------------|
| *Spec-first discipline* | `specs/*`, `tasks.md`, `SRD.md` | Front-load context for **RequirementsVerifier** agent |
| *Reusable helper agents* | `context-fetcher`, `git-workflow`, `test-runner` | Replace our ad-hoc shell wrappers and cut tokens |
| *Hook & banner UX* | `setup-claude-code.sh`, colourful progress UI | Unify developer experience across all gates |
| *Auto CHANGELOG* | `git-workflow` CHANGELOG update ⬆️ | Triggered by **AcceptanceValidator** “GO” decision |
| *Standard metadata format* | Front-matter in `/claude-code/agents/*.md` | Align with Claude sub-agent router 2025-07 spec |

---

### 2 High-level work plan

1. **Vendor in Agent-OS** as a Git subtree (`vendor/agent-os/`).
2. **Convert** Agent-OS agent MD → our YAML schema via `scripts/convert_agentos_to_yaml.py`.
3. **Adopt** style guides & tech stack docs as memory packs (`docs/standards/*`).
4. **Merge hooks**: keep our *gate-block* logic, add their UX banners.
5. **Swap** old bash wrappers for Agent-OS helper agents (context-fetcher, git-workflow, test-runner).
6. **Update FSM** (`stage_order` list) to insert helper steps at proper gates.
7. **Document** new commands in CLI help & README.
8. **Ship** v0.6.0 after green E2E run on demo repo.

---

### 3 File-tree additions

```text
vendor/agent-os/               # subtree
docs/standards/
 ├── tech-stack.md             # imported
 └── code-style-python.md
claude-code/
 └── agents/
     ├── context-fetcher.yaml  # converted
     ├── git-workflow.yaml
     └── test-runner.yaml
scripts/
 └── convert_agentos_to_yaml.py
~/.claude/hooks/
 └── before_edit.d/
     └── 05-agentos-banner.sh  # new
```

---

### 4 Sprint-sized tasks

| ID      | Task                                                      | Owner  | Est. hrs |
| ------- | --------------------------------------------------------- | ------ | -------- |
| **A-1** | Pull Agent-OS subtree & run conversion script             | @chris | 3        |
| **A-2** | Copy style/tech docs → memory hierarchy                   | @alex  | 2        |
| **A-3** | Hook merger: UX banner + gate-block coexist               | @marie | 4        |
| **A-4** | Replace bash `run_tests` wrapper with `test-runner` agent | @david | 5        |
| **A-5** | Insert `context-fetcher` before each Verify/Validate call | @david | 3        |
| **A-6** | Wire `git-workflow` into AcceptanceValidator success hook | @marie | 3        |
| **A-7** | Update CLI docs & `vv --help`                             | @alex  | 1        |
| **A-8** | Demo E2E on sample repo, record asciinema                 | @chris | 2        |

*Total ≈ 23 hrs – fits a 1-week hardening sprint.*

---

### 5 Open questions / parking lot

* **Licensing** – Agent-OS is MIT; confirm no copyleft issues for commercial plugin.
* **Colour banner collisions** – ensure hooks don’t double-print.
* **Token impact** – measure if `context-fetcher` actually reduces cost vs Serena search.
* **CI image size** – vendor subtree may bloat repo; consider shallow clone in pipeline.

---

### 6 Definition of Done ✅

* `vv resume` completes full V-&-V flow **using only** Agent-OS helper agents.
* `CHANGELOG.md` auto-updates on GO decision.
* New memory packs appear in generated prompt logs (verify via `vv debug-context`).
* All unit + integration tests green; pipeline cost ≤ +10 % tokens vs prior baseline.
* README + CLI help show new commands & folder layout.
