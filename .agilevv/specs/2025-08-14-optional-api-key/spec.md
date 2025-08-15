# Spec Requirements Document

> Spec: Optional API Key with Claude Code Subscription
> Created: 2025-08-14

## Overview

Remove the mandatory requirement for ANTHROPIC_API_KEY when users have Claude Code subscription authentication available. This feature will enable Pro/Max subscription users to use VeriFlowCC without needing separate API key setup while maintaining backward compatibility.

## User Stories

### Subscription User Authentication

As a Claude Code Pro/Max subscriber, I want to use VeriFlowCC without setting up an API key, so that I can leverage my existing subscription for V-Model workflow automation.

When a user launches VeriFlowCC without an API key, the system should detect available Claude Code subscription authentication and proceed with the workflow using the subscription credentials. If subscription authentication fails, the system should provide a clear error message explaining the authentication options available.

### Backward Compatibility

As an existing VeriFlowCC user with API key setup, I want my current workflow to remain unchanged, so that I can continue using the tool without disruption.

The system should continue to prioritize API key authentication when available, ensuring existing users experience no changes to their current setup and configuration.

## Spec Scope

1. **Authentication Detection** - Modify SDK configuration to detect and use Claude Code subscription when API key is unavailable
1. **Error Handling** - Implement clear error messages when both authentication methods fail
1. **Backward Compatibility** - Ensure existing API key workflows remain unchanged
1. **Configuration Updates** - Update SDKConfig class to support optional API key scenarios

## Out of Scope

- Model selection based on subscription tier (Sonnet vs Opus)
- CLI flags for explicit authentication method selection
- Configuration storage for authentication preferences
- Usage tracking or billing integration
- Subscription plan validation

## Expected Deliverable

1. VeriFlowCC launches successfully for users with Claude Code Pro/Max subscriptions without requiring ANTHROPIC_API_KEY
1. Clear error messages appear when neither authentication method is available or functional
1. Existing API key users experience no workflow changes

## Spec Documentation

- Tasks: @.agilevv/specs/2025-08-14-optional-api-key/tasks.md
- Technical Specification: @.agilevv/specs/2025-08-14-optional-api-key/sub-specs/technical-spec.md
