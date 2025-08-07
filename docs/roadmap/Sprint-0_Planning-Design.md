# docs/roadmap/Sprint-0_Planning-Design.md
## Sprint 0 - “Blueprint”  (Weeks 0-2)

### Goal  
Establish vision, requirements, and high-level architecture for VerifFlowCC.

### V-Model slice  
`Requirements ⇢ System Design`

### Deliverables  
- Final Product Requirements Document (PRD)  
- C4 Context & Container diagrams (mermaid)  
- Jinja prompt templates v0 (`planner`, `design`)  
- Pydantic schemas: `Plan`, `Task`, `TestReport`  
- CLI scaffold (`verifflowcc_cli.py` with Typer)  
- ADR-000 “Why VerifFlowCC”  

### Key Tasks  
| # | Task | Owner | Exit / Gate Criteria |
|---|------|-------|----------------------|
| P-1 | Draft & iterate PRD | PO + Arch | Signed-off PRD |
| P-2 | Draw Context + Container diagrams | Arch | Diagrams committed |
| P-3 | Create prompt templates | AI Eng | Rendered sample passes schema |
| P-4 | Build CLI skeleton | Platform | `verifflowcc --help` works |
| P-5 | Set up CI + pre-commit | Platform | All checks green |

### Risks & Mitigations  
- **Scope creep** → time-box PRD review to ≤ 2 iterations.  
- **Template drift** → lock template filenames via pre-commit.

### Definition of Done  
All deliverables in `docs/` or `src/` repo paths, CI green.  