# docs/roadmap/Sprint-3_Testing_Agent_and_Fix_Loop.md
## Sprint 3 - “Trust but Verify”  (Weeks 8-9)

### Goal  
Complete Testing agent, automated test execution, and fix-loop until tests pass (Milestone M3).

### V-Model slice  
`Unit Test ⭢ Integration Test ⭢ Validation Report`

### Deliverables  
- `testing_agent.py` (Sonnet 4) with shell MCP wrapper  
- Orchestrator fix-loop: failed-test → code-fix cycle  
- Validation prompt for Planner (Opus)  
- End-to-end demo: Plan → Code → Test → Pass  
- Documentation update + Changelog `v0.5.0`

### Key Tasks  
| # | Task | Owner | Exit / Gate Criteria |
|---|------|-------|----------------------|
| S3-1 | Shell execute tool wrapper | Platform | Captures `pytest` output |
| S3-2 | Testing prompt & schema | AI Eng | TestReport validated |
| S3-3 | Fix-loop orchestration | AI Eng | Failing tests auto-fixed |
| S3-4 | Validation checklist prompt | Arch | All acceptance criteria satisfied |
| S3-5 | M3 demo recording | DevRel | Video or asciinema merged |

### Risks & Mitigations  
- **Flaky tests** → use seeded data + deterministic flags.  
- **Excess token cost** → batch failures into single prompt.

### Definition of Done  
`verifflowcc run` on demo repo cycles until **all tests pass** and outputs validation summary.  
Base project functionality complete (Milestone M3).  