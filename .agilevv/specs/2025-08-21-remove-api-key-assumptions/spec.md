# Spec Requirements Document

> Spec: Remove API Key Assumptions
> Created: 2025-08-21
> Status: Planning

## Overview

Remove all hardcoded API key assumptions from VeriFlowCC documentation, code, and tests while maintaining Claude Code SDK functionality. Users should be able to operate with flexible authentication methods (subscription or API key) without explicit setup requirements in the codebase.

## User Stories

### Developer Authentication Flexibility

As a VeriFlowCC developer, I want to use the system without hardcoded API key requirements, so that I can authenticate through Claude Code subscription or configured API keys seamlessly.

The system should detect available authentication methods and proceed without requiring explicit API key setup in documentation or code. When authentication fails, the system provides generic error messages and exits gracefully.

### Documentation User Experience

As a VeriFlowCC user reading documentation, I want clear disclaimers about authentication requirements, so that I understand I need to configure authentication beforehand without being forced into specific API key setup patterns.

Documentation should assume users have already configured their preferred authentication method through VeriFlow guidelines.

### Testing Without API Key Dependencies

As a VeriFlowCC contributor, I want to run tests without mandatory API key environment variables, so that the testing framework remains flexible while maintaining the "100% real integration" philosophy.

Tests should use existing patterns like skip_if_no_auth to handle authentication gracefully without breaking the real integration testing approach.

## Spec Scope

1. **Documentation Updates** - Remove API key setup instructions from README.md, CLAUDE.md, and related docs
1. **Code Authentication Logic** - Update SDKConfig and core classes to handle flexible authentication without assumptions
1. **Test Framework Updates** - Modify 70+ test files to remove mandatory ANTHROPIC_API_KEY requirements
1. **Error Handling Enhancement** - Implement generic authentication error messages with graceful exit behavior
1. **CLI Disclaimer Integration** - Add authentication disclaimer to CLI startup and help text

## Out of Scope

- Security configuration changes (.gitleaks.toml patterns remain unchanged)
- Backward compatibility breaking changes for existing API key users
- New authentication method implementations beyond Claude Code SDK capabilities
- Mock or simulated authentication modes that violate real integration philosophy

## Expected Deliverable

1. VeriFlowCC operates with Claude Code subscription authentication without requiring API key setup
1. All documentation contains appropriate disclaimers instead of API key configuration instructions
1. Test suite runs successfully using skip_if_no_auth patterns without mandatory API key environment variables

## Spec Documentation

- Tasks: @.agilevv/specs/2025-08-21-remove-api-key-assumptions/tasks.md
- Technical Specification: @.agilevv/specs/2025-08-21-remove-api-key-assumptions/sub-specs/technical-spec.md
