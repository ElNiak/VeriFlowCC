# Artifact and Memory Management Strategy

A robust artifact management approach underpins AgileVerifFlowCC, ensuring that all outputs of each phase are saved, organized, and fed back into the AI’s context when needed. We design the artifact storage to be local, per-project, human-readable (mostly Markdown or code files), and under version control (if the user opts to use git). This not only provides traceability but also prevents loss of information between AI sessions.

Project Directory Structure: When a project is initialized, a structured layout is created. For example:

```text
/<project_name>/
    .agilevv/          # AgileVerifFlowCC configuration and metadata
        backlog.md          # Agile story map and backlog of user stories (requirements)
        architecture.md     # System and design documentation (living design doc)
        agilevv.yaml     # Config file for gating and settings (if any)

   CLAUDE.md           # Project memory for Claude (ingested on start)
   .claude/agents/     # Subagent definitions (Markdown files with persona configs)
   src/                # Source code directory (could have subfolders per component)
   tests/              # Test code directory mirroring src/ structure
   .mcp.json           # (optional) MCP server config (e.g., for GitHub integration)
   ... (other aux files like README, etc.)
```

The backlog.md and architecture.md files are the core living artifacts that correspond to the left side of the V-model (requirements and design, respectively). They are continuously updated:

- backlog.md lists each user story (with an ID or number, description, and acceptance criteria). It can also encode status (e.g., a checkbox or tag for Done vs. TODO) and possibly a link or reference to tests (for traceability, we might include for each story a reference to test file names or sections that verify it). This becomes a simple requirements traceability matrix: by reading backlog.md you can see what has tests or not.

- architecture.md contains the evolving design: high-level system context, and sections per component/feature. We might include UML-like descriptions in Markdown, or bullet lists of design decisions. It should also capture any non-functional requirements and how they are addressed (for compliance, etc.).

These artifacts are supplemented by code and test files in src/ and tests/, which are the outputs of the implementation and verification phases (the right side of the V). The CLI ensures that for each story, there is at least one corresponding test file or test case in tests/. We could even enforce naming conventions (e.g. story “Share To-Do” is requirement R5, then test file test_R5_share_todo.py is generated). This consistent naming aids in mapping tests to requirements, both for humans and if we implement any automated coverage checks.

Persistent Memory (CLAUDE.md): Claude-Code provides a mechanism for persistent project memory via CLAUDE.md in the repo ￼ ￼. We leverage this heavily. On project load, Claude automatically reads this file (and any imported files) into its system context.

Our strategy:

- Use CLAUDE.md as a hub that imports the key artifact files. For example, CLAUDE.md might contain:

```markdown
Project: Agile To-Do List app
Domain: Web application for task management.

@backlog.md  <!-- import the backlog so Claude always “knows” current requirements -->
@architecture.md  <!-- import architecture for system context -->

# Coding Standards
- Follow PEP8 (for Python) or Airbnb style (for JS) as relevant.
- Use descriptive variable and function names.

# Definition of Done
- All acceptance criteria met and tests passed for each story.
- Documentation updated (backlog & architecture).
```

By using the import syntax, we ensure the entire content of backlog.md and architecture.md can be pulled into context on demand ￼. (We must be cautious: if those files grow, importing everything could hit context limits. Alternatively, we might place only summaries in CLAUDE.md and manually inject details as needed. More on that below.)

- Hierarchy of Memories: Claude-Code actually supports multiple memory scopes (user-level, project-level, etc.) ￼. We focus on project memory to keep things self-contained. If an organization had common policies, an enterprise CLAUDE.md could be present (but that’s beyond our current scope). The tool might also utilize the user’s ~/.claude/CLAUDE.md to store personal preferences (like always use a certain testing library) so that all projects by that user share some consistent settings. However, project-specific is our main concern.

- Automatic Memory Updates: Whenever a major change occurs (requirement added/changed, design updated, new important decision, etc.), AgileVerifFlowCC will update the relevant files and possibly a summary in CLAUDE.md. For example, after each sprint, it might append a short summary of what was done to CLAUDE.md (or a separate changelog that is imported). This allows new sessions or subagents to quickly catch up on project history without reading the entire backlog. By keeping CLAUDE.md curated, we give Claude a high-level awareness (“We have completed 3 out of 10 planned features; current architecture includes modules A, B, C…”) that guides its reasoning. This mitigates context loss when the conversation history is cleared or if Claude’s short-term memory gets full ￼ ￼. Essentially, long-term info goes to files, short-term working info stays in conversation.

Selective Context Injection: As projects grow, even persistent files can become large. We adopt a strategy of selective injection to manage context window limits. Instead of always dumping the entire backlog and architecture into Claude’s prompt, the CLI will:

- Identify which parts of the backlog are relevant for the current task. E.g., if working on story #5, we only feed story #5’s details (plus maybe any globally relevant requirements). We can parse backlog.md (it’s structured text) and extract that section to include in the prompt to the Developer or QA agent.

- Similarly, for architecture, use mapping or search. Since during Sprint 0 we established a mapping of features to components, the CLI can know that “Share To-Do” feature mostly concerns (say) the ShareController and EmailService. We then only inject the part of architecture.md describing those, rather than the whole file. We could maintain an index at the top of architecture.md linking story IDs to sections, to make retrieval easier. In future, a semantic search (vector database) could be employed to fetch relevant design pieces by similarity, but a simpler mapping suffices given we proactively link them.

- The CLAUDE.md import mechanism is flexible: we can organize memory files hierarchically. For instance, instead of one giant architecture.md, we could have multiple files (like one per component) and include only needed ones. The memory import system allows relative paths, so we could do conditional imports if needed. However, a simpler route is the orchestrator reading from files and putting text into the prompt directly, which it can certainly do with the Claude SDK.

Artifact Versioning and Completeness Checks: AgileVerifFlowCC can embed self-checksums or tags in artifacts to mark completeness. For example, when a story is done, mark it [Done] in backlog.md along with a reference like (Verified by tests: test_share.py). A simple script or the tool itself can scan backlog.md to ensure every story marked Done has a corresponding test reference, and vice versa. This is an additional guard so nothing is marked finished without evidence of verification. These checks can be run as part of a agileverif status command or at end of sprint, giving a sanity report to the user.

All artifacts are plain files which the user can edit if needed – the tool will detect changes and incorporate them. For instance, if the user manually adds a story to backlog.md, the next time agileverif status or agileverif sprint start runs, the orchestrator will notice a new story and might ask the Requirements agent to flesh it out further. This bidirectional flexibility means the human can still steer high-level requirements and let the AI handle the heavy lifting of elaboration and enforcement.

Maintaining Traceability: One principle of V&V is traceability from requirements to tests. Our strategy ensures this in multiple ways:

- By design, we generate tests immediately after implementing each requirement (story). So the temporal proximity ensures the link.

- We explicitly label tests to map to requirements (in names or comments). The QA agent could insert a comment in each test file like # Test for User Story 5: Share To-Do List.

- The documentation (backlog.md) can be updated with a reference to the test or simply an annotation that it’s done and tested. In regulated contexts, one might generate a requirements trace matrix; our tool could potentially output such a matrix by reading the files. This is something to consider as an extra feature (export a CSV of Story vs Test status).

Context Memory Safety: We also guard against prompt corruption or loss of state by employing context engineering techniques:

- Frequent summarization: If a conversation (Claude session) is getting long, the CLI can command Claude to summarize what has been done so far and what remains, then start a new session carrying that summary. This prevents the model from losing earlier details due to context limit ￼. For example, after coding and some testing in a single session, we might pause and say, “Summarize the current implementation status and remaining tasks”, save that, then re-init Claude with that summary plus the failing test scenario to continue. This summary-checkpoint approach is akin to compressing history so important facts remain accessible ￼.

- Using Claude’s /save and /open slash commands if available, or the SDK to maintain a conversation log that can be reloaded. We can also store the conversation history in a file per sprint (for audit and possibly to fine-tune future runs).

- Ensuring deterministic behavior via hooks and schema: For instance, when the Planner (or orchestrator) asks Claude to output a plan or an artifact, we might use a structured format (like instruct it to output YAML or JSON for certain data). This can then be parsed by the CLI to verify completeness. Anthropic’s docs suggest using e.g. Pydantic schemas to validate AI outputs ￼ ￼. We can apply this to things like test results or checklist outputs to reduce miscommunication between the AI and the orchestrator.

In summary, artifact and memory management in AgileVerifFlowCC is designed so that the AI never starts a task from scratch or from a blank slate in later sprints – it always has the accumulated knowledge of past work available in a structured form. This persistent knowledge base (backlog, design, CLAUDE.md memory) ensures consistency across sprints (global consistency of requirements/design is maintained despite iterative development ￼ ￼). It also means if one stops working and returns later, the tool and Claude can pick up right where they left off, with full context restored from files.
