# Technical Specification

This is the technical specification for the spec detailed in @.agilevv/specs/2025-08-21-remove-api-key-assumptions/spec.md

> Created: 2025-08-21
> Version: 1.0.0

## Technical Requirements

- **SDKConfig Class Modification**: Update authentication detection logic to prioritize Claude Code subscription over API key requirements
- **Documentation Template Updates**: Replace explicit API key setup instructions with generic authentication disclaimers in README.md and CLAUDE.md
- **Test Framework Enhancement**: Implement skip_if_no_auth pattern consistently across 70+ test files to maintain real integration testing without mandatory API keys
- **Error Handling Standardization**: Create generic authentication error messages that exit gracefully without exposing authentication method details
- **CLI Integration**: Add authentication disclaimer to CLI help text and startup messages
- **Graceful Exit Behavior**: Implement clean application termination when authentication fails without stack traces or detailed error exposure
- **Authentication Method Detection**: Enhance existing subscription verification logic to handle both authentication approaches seamlessly
- **Backward Compatibility**: Ensure existing API key workflows continue functioning without breaking changes for current users

## Approach

The implementation will follow a phased approach to maintain system stability while removing API key assumptions:

1. **Authentication Layer Enhancement**: Modify `verifflowcc/core/sdk_config.py` to implement intelligent authentication detection that checks for Claude Code subscription first, then falls back to API key validation without exposing implementation details

1. **Documentation Sanitization**: Update all user-facing documentation to remove explicit API key setup instructions while maintaining clear authentication requirements through generic disclaimers

1. **Test Infrastructure Updates**: Systematically apply the `skip_if_no_auth` decorator pattern across the test suite to ensure real integration testing continues without forcing API key configuration

1. **Error Message Standardization**: Implement consistent, user-friendly authentication error messages that guide users to proper authentication without revealing internal authentication mechanisms

1. **CLI User Experience**: Enhance command-line interface with helpful authentication disclaimers in help text and startup messages to set proper user expectations

1. **Graceful Degradation**: Ensure the application exits cleanly when authentication fails, providing helpful guidance without technical stack traces

## External Dependencies

No new external dependencies are required. This specification leverages the existing Claude Code SDK integration and authentication infrastructure.
