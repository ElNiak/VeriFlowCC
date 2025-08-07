# docs/roadmap/Sprint-2_Coding_Agent_MVE.md
## Sprint 2 - “Hands at Work”  (Weeks 5-6)

### Goal  
Introduce Sonnet 4 Coding agent and achieve Plan ⇢ Code path on a toy repo.

### V-Model slice  
`Module Design ⇢ Coding ⇢ Unit Test Skeleton`

### Deliverables  
- `coding_agent.py` with file-diff output  
- Diff applier in `file_manager.py`  
- Hook-gated pipeline for **Plan → Code**  
- Demo feature: generate “Hello, World” module in sample project  
- Unit tests for diff logic + coding prompt compliance

### Key Tasks  
| # | Task | Owner | Exit / Gate Criteria |
|---|------|-------|----------------------|
| S2-1 | Sonnet coding prompt template | AI Eng | Generates correct diff |
| S2-2 | Diff parser & applier | Platform | File modified & tests green |
| S2-3 | Pipeline integration | Platform | Plan → Code auto-executes |
| S2-4 | Demo repo + README gif | DevRel | Demo reproducible |

### Definition of Done  
Running `verifflowcc implement demo.yml` produces code, commits checkpoint, CI green.