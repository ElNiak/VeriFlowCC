# Plan

Below is a 🗺 **12-week roadmap** (≈ 3 × 4-week V-Sprints) that gets VerifFlowCC from zero → GA:

| Wk        | Sprint Goal (V-Model slice)             | Key Deliverables                                                                                                                                                                               | Owner(s)    |
| --------- | --------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------- |
| **0**     | *Project bootstrap*                     | • Git repo + CI skeleton<br>• `pyproject.toml` with Poetry<br>• Pre-commit hooks (ruff, black)<br>• ADR-000 “Why VerifFlowCC”                                                                  | Tech Lead   |
| **1 – 2** | **Sprint 0 – Planning & Design**        | • Finalised PRD<br>• C4 Context & Container diagrams *(mermaid)*<br>• Jinja prompt templates v0<br>• Pydantic schemas: `Plan`, `TestReport`<br>• CLI scaffolding (`verifflowcc_cli.py`, Typer) | Arch + UX   |
| **3 – 4** | **Sprint 1 – Planner MVE**              | • Opus 4.1 Planner module<br>• Context manager (loads `CLAUDE.md`)<br>• Unit tests (pytest-async)<br>• Git checkpoint service                                                                  | AI Eng      |
| **5 – 6** | **Sprint 2 – Coding Agent MVE**         | • Sonnet 4 coding agent<br>• File-edit diff applier<br>• Basic hook-gated pipeline (Plan→Code)<br>• Demo: generate “Hello, World” feature                                                      | AI Eng      |
| **7**     | **Hardening Sprint**                    | • Error/timeout handling<br>• Structured logging (JSON)                                                                                                                                        | Platform    |
| **8 – 9** | **Sprint 3 – Testing Agent + Fix Loop** | • Sonnet 4 testing agent<br>• Shell tool wrapper (`pytest` runner)<br>• Fix-loop orchestration (failed-test → code-fix cycle)                                                                  | AI Eng      |
| **10**    | **Validation Gate**                     | • Opus validation prompts<br>• Acceptance-criteria checklist output                                                                                                                            | QA          |
| **11**    | **Beta Readiness**                      | • CLI UX polish (rich progress bars)<br>• Installer (`pipx`) & README<br>• Usage telemetry opt-in                                                                                              | DevRel      |
| **12**    | **GA Cut-over**                         | • Version 1.0 tag<br>• Release notes<br>• Publish to PyPI                                                                                                                                      | Release Mgr |

### Parallel (continuous) tracks

* **Security & Compliance** – optional, re-introduce post-GA.
* **Documentation** – keep `/docs` up-to-date every sprint.
* **Observability Dashboards** – start Week 7; Grafana or plain JSON log viewer.

---

### Milestone Checklist ✓

1. **M0** – Repo ready, CI green
2. **M1** – Planner returns valid `Plan` object on CLI command
3. **M2** – End-to-end Plan → Code path runs on toy repo
4. **M3** – Tests generated & pass; rollback works
5. **M4** – Validation report produced; Beta tag
6. **M5** – GA release on PyPI, docs live

---

### Agile V-Model Enforcement

Each sprint still contains the micro-V:

> *Specify → Design → Code → Unit-Test → Integration-Test → User-Validation*

Hook gates in `orchestrator.py` must be satisfied before “Done”. Example gate logic:

```python
def gate_passed(stage: Stage, artifact: Path) -> bool:
    return artifact.exists() and validate_schema(artifact)
```

---