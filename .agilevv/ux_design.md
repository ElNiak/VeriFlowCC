# CLI User Experience (UX) Design

The CLI is designed for both interactive use (a guided REPL-like workflow for a human user) and non-interactive use (automating the pipeline via single commands or scripts). Only one project is active at a time, simplifying context management. The UX is organized around project initialization and sprint execution:

- Project Initialization (New Project): The user creates a new project with a command like agileverif init \<project_name>. This sets up a project directory (named after the project) with the necessary files and templates: an empty (or templated) backlog.md for user stories, architecture.md for design notes, a fresh CLAUDE.md with project context placeholders, and configuration defaults. The CLI may prompt the user for initial info (project domain, goals) or read an input file, then seed the backlog and architecture by invoking Claude. For example, after init, the CLI could call Claude to generate a Story Map and initial requirements for “Sprint 0” (foundational sprint)

  - In interactive mode, it might ask the user to confirm or refine these AI-generated artifacts. The result is a populated backlog and high-level design ready for iteration.

- Opening an Existing Project: To continue work, the user enters the project directory (or uses agileverif open \<project_name>). The CLI loads the persistent memory (CLAUDE.md and imports) and connects to Claude-Code with that context. In interactive mode, this could drop the user into a REPL where Claude (aware of the project’s context) is ready to take commands. The prompt might show the current sprint or backlog status in the greeting. Only one project can be open at once, and the CLI ensures Claude’s context is cleared of any previous project data to avoid leakage.

- Interactive Workflow (Single-sprint REPL): Once a project is open, a user can use commands to step through the V-model pipeline interactively. For example:

  - next-story (or the CLI automatically selects the next highest-priority story from the backlog that isn’t done). The CLI then prompts Claude (in the persona of a Requirements subagent) to elaborate the user story, confirm acceptance criteria, and plan V&V for this story.
    - design to trigger the Design subagent for creating or updating the design/architecture related to the story.
    - implement to have the Development subagent write or modify code for the feature.
    - test to invoke the Testing subagent, which generates test cases and runs them.
    - review or validate for final verification/validation steps (e.g. a summary of results or stakeholder review simulation).
      These can be run step-by-step with user confirmation at each, or the CLI can offer a one-shot command (e.g. agileverif run-sprint) to execute the full cycle automatically. In interactive mode, after each phase the CLI prints results (e.g. list of requirements generated, diff of code changes, test outcomes) and waits for user input to proceed, if soft gating is configured. The user can intervene – e.g. editing a requirement or code manually – and then resume the pipeline. This design keeps the user “in the loop” for oversight, aligning with agile principles of continuous feedback.

- Non-Interactive (Batch) Mode: The CLI supports running a full sprint or specific phases without manual intervention. For instance, agileverif run --story "User logs in" could accept a user story description and then internally carry it through requirements→design→code→test, producing artifacts and a report at the end. Or agileverif run-sprint with no arguments would automatically pick the next story from the backlog and do the same. In batch mode, the CLI uses hard gating by default – if any phase fails (e.g. tests do not pass), the process stops with an error status, ensuring CI/CD pipelines detect the issue. This is useful for automation (for example, integrating AgileVerifFlowCC into a CI system to verify that each proposed change has all V-model artifacts complete).

- Command Structure & Help: The CLI has a hierarchical command structure for clarity. For example:

  - agileverif init – create new project.
    - agileverif status – show current sprint, backlog summary, and which phase is in progress or any gating issues.
    - agileverif sprint start \<story_id> – (optionally) begin a new sprint with a specific story or let the tool choose the next.
    - agileverif sprint run – run through all phases of the current sprint story (if one is in progress).
    - Or, break it down:
      - agileverif req – run requirements analysis phase,
      - agileverif design – run design phase,
      - agileverif dev – run implementation (development) phase,
      - agileverif test – run testing/verification phase
      - agileverif validate – run validation (e.g. stakeholder review simulation).
    - agileverif sprint close – mark sprint complete and do end-of-sprint documentation updates.
    - agileverif backlog add "new story description" – add a new item to backlog (which the requirements agent could then flesh out).

The CLI provides --strict or --no-strict flags to toggle hard gating. In help messages and documentation, we will emphasize that skipping phases is discouraged unless in an exploratory mode. By default, the UX nudges the user to follow the sequence: for instance, if they try agileverif dev (development) before requirements, the tool can warn or automatically trigger the missing prior phases (or enforce via a hook that development actions are blocked until requirements exist ￼). This approach makes the right way (V-model) the path of least resistance.

Overall, the UX is designed to be convenient but opinionated: it automates the heavy lifting of artifact generation and consistency checks while giving the user easy commands to oversee or adjust as needed. The interactive mode feels like pair-programming with an AI that guides you through an Agile V&V checklist, whereas the batch mode can serve in continuous integration or for power users who want one-shot generation of all outputs.
