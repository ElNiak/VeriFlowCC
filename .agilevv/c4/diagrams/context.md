### 1. Context Model

At the highest level, VerifFlowCC sits between the **developer** and several external services. The developer interacts with VerifFlowCC through a CLI in the terminal (issuing commands and providing input like feature descriptions). The CLI tool in turn communicates with Anthropic’s Claude API to leverage the Opus 4.1 and Sonnet 4 models as needed. All AI reasoning and code generation happen via these model API calls. The CLI also interfaces with the **local development environment** – reading and writing files in the project’s repository, running test suites, and using system tools (like version control, compilers, etc.). The figure below conceptualizes this context:

- **Developer (User):** Uses the VerifFlowCC CLI on their machine to develop software with AI assistance. They initiate workflows (e.g. “implement feature X”) and supervise the results at each stage.

- **VerifFlowCC CLI:** The tool itself, running locally. It orchestrates the multi-agent workflow and serves as the bridge between the AI models and the developer’s local system. It sends prompts to Anthropic’s Claude service and receives code/plan outputs, applying them to the local codebase or presenting them to the user.

- **Anthropic Claude API:** Cloud service providing access to Claude Opus 4.1 and Sonnet 4 models. VerifFlowCC sends structured prompts and tool-use commands to this API (using the Claude Code SDK), and obtains the model’s responses (plans, code, test analysis, etc.). The API can also handle tool calls (via MCP) by pausing the model’s output and awaiting the tool results.

- **Local Environment (Code Repository & Tools):** This includes the project’s source code, test files, and any relevant data on the developer’s machine. VerifFlowCC reads from and writes to these files as directed by the AI (with permission). It also includes system tools like the shell, compilers, test runners, and git. The CLI may invoke these directly or via Claude’s tool-use interface. Checkpoints (such as git commits) are stored here, and any persistent memory files (e.g. `CLAUDE.md` log) reside in the repo.

In summary, the context diagram shows the developer driving VerifFlowCC, which in turn orchestrates cloud AI models and local tools to produce software artifacts. This central position of the CLI means it must carefully manage inputs/outputs between the human, AI, and system – which is exactly what the following design details ensure.
