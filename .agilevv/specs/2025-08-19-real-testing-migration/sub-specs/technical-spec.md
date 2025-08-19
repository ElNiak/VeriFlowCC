# Technical Specification

This is the technical specification for the spec detailed in @.agilevv/specs/2025-08-19-real-testing-migration/spec.md

> Created: 2025-08-19
> Version: 1.0.0

## Technical Requirements

- **Mock Infrastructure Removal**: Complete elimination of unittest.mock imports, @patch decorators, AsyncMock, and MagicMock instances from all test files
- **BaseAgent SDK Integration**: Remove mock_mode parameters and MockSDKClient/MockSDKOptions classes, ensuring all agents use real Claude Code SDK instances
- **Sequential Test Execution**: Implement pytest execution strategies that prevent parallel test runs to capture proper agent handoff patterns and error scenarios
- **Real Authentication Flow**: Leverage existing Claude Code SDK authentication without custom test authentication - assume proper SDK setup
- **Artifact Structure Validation**: Implement Pydantic schemas and validation logic focusing on file format, presence, and structure rather than AI-generated content specifics
- **V-Model State Management**: Ensure tests validate proper .agilevv directory state transitions and file-based memory persistence between agent handoffs
- **Error Handling Integration**: Test real network failures, API rate limits, and Claude SDK exceptions rather than mock error simulation
- **Agent Factory Real Instances**: Update AgentFactory to only create real agent instances, removing factory patterns for mock agent creation

## Integration Requirements

- **Agent-to-Agent Communication**: Validate real artifact consumption patterns where Design agents can parse Requirements agent outputs, Developer agents consume Design specifications, etc.
- **File-Based Memory Persistence**: Test actual .agilevv file creation, modification, and reading across agent boundaries in isolated test directories
- **SDK Session Management**: Integrate with Claude Code SDK session handling for context preservation across multi-agent workflows
- **V-Model Orchestrator Integration**: Ensure Orchestrator class properly manages real agent lifecycles and state transitions without mock dependencies

## Performance Criteria

- **Sequential Execution Only**: All tests must execute one-by-one to prevent race conditions and ensure proper error capture
- **Test Isolation**: Each test must use isolated .agilevv-test directories to prevent cross-test contamination
- **Network Resilience**: Tests should handle real network latency and API response variations without brittle timing assumptions
- **Resource Management**: Proper cleanup of real agent instances and file system artifacts after test completion
