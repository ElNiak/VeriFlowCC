# Spec Requirements Document

> Spec: Real Testing Migration
> Created: 2025-08-19

## Overview

Eliminate all mock testing infrastructure from VeriFlowCC and implement comprehensive real testing using live Claude Code SDK integration for V-Model orchestration validation. This migration ensures all tests validate actual agent behavior, artifact generation, and workflow orchestration rather than mocked responses.

## User Stories

### Real Agent Orchestration Testing

As a VeriFlowCC developer, I want all agent tests to use real Claude Code SDK calls, so that I can validate true V-Model orchestration behavior and catch integration issues that mocks would miss.

The developer creates a test that spawns a real Requirements Analyst agent, feeds it a user story, and validates that the generated requirements artifact contains proper INVEST criteria formatting and traceability fields that subsequent Design agents can consume.

### Mock-Free Testing Infrastructure

As a maintainer, I want to completely remove all unittest.mock infrastructure from the test suite, so that tests reflect production behavior and prevent mock-reality drift that leads to production failures.

The maintainer runs the full test suite without any @patch decorators or MagicMock instances, ensuring every test validates real agent-to-agent communication patterns and file-based state persistence.

### V-Model Workflow Validation

As a QA engineer, I want end-to-end V-Model cycle tests with real agents, so that I can verify complete Requirements→Design→Code→Test→Validation→Integration workflows produce the expected artifacts and state transitions.

The QA engineer executes a test that creates a simple feature request, runs it through all 5 agent personas using real Claude calls, and validates that each stage produces properly formatted artifacts that the next stage can successfully consume.

## Spec Scope

1. **Mock Infrastructure Removal** - Eliminate all unittest.mock imports, @patch decorators, and MagicMock usage from agent and core tests
1. **Real Agent Integration** - Convert all agent tests to use live Claude Code SDK calls with proper authentication and session management
1. **V-Model Workflow Testing** - Implement sequential end-to-end tests that validate complete Requirements→Design→Code→Test→Validation→Integration cycles
1. **Artifact Validation Framework** - Focus on validating file format, structure, presence, and consumability of agent-generated artifacts rather than content specifics
1. **Sequential Test Execution** - Ensure all tests run one-by-one to capture proper agent handoff patterns and error scenarios

## Out of Scope

- Performance testing and execution time optimization
- Backwards compatibility with existing mock infrastructure
- Detailed Claude response content validation (focus on artifacts)
- Parallel or concurrent test execution patterns
- Test response caching or API call reduction mechanisms
- Custom authentication beyond assumed Claude Code SDK setup

## Expected Deliverable

1. Complete test suite passes with zero mock dependencies and 100% real Claude agent integration
1. End-to-end V-Model workflows execute successfully from user story to validated deliverable with real agent handoffs
1. All agent-generated artifacts validated for proper format, structure, and consumability by subsequent V-Model stages

## Spec Documentation

- Tasks: @.agilevv/specs/2025-08-19-real-testing-migration/tasks.md
- Technical Specification: @.agilevv/specs/2025-08-19-real-testing-migration/sub-specs/technical-spec.md
