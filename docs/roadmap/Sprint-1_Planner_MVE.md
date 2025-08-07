# docs/roadmap/Sprint-1_Planner_MVE.md
## Sprint 1 - “Brains Online”  (Weeks 3-4)

### Goal  
Ship a minimal-viable Planner module (Claude Opus 4.1) that outputs a validated `Plan` object on demand.

### V-Model slice  
`Detailed Design ⇢ Architectural Specification`

### Deliverables  
- `planner_agent.py` (Opus 4.1 integration)  
- `context_manager.py` (loads `CLAUDE.md`)  
- Git checkpoint service (`file_manager.py`)  
- Unit tests (pytest-async) with 80 % coverage  
- Demo command: `verifflowcc plan "feature name"` ➜ YAML plan

### Key Tasks  
| # | Task | Owner | Exit / Gate Criteria |
|---|------|-------|----------------------|
| S1-1 | Implement Opus prompt template | AI Eng | Plan parsed by Pydantic |
| S1-2 | Context loader (memory packs) | Platform | Context unit test passes |
| S1-3 | CLI “plan” command | Platform | Demo runs E2E |
| S1-4 | Git checkpoint helper | Platform | `git commit` auto-created |
| S1-5 | PRD update & living docs | PO | Docs merged |

### Definition of Done  
`verifflowcc plan` returns a valid plan, tests pass, checkpoint commit created.