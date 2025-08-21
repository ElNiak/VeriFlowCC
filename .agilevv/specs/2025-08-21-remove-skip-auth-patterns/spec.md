# Spec Requirements Document

> Spec: Remove Skip Auth Patterns
> Created: 2025-08-21
> Status: Planning

## Overview

Remove all skip_if_no_auth patterns from VeriFlowCC test suite and assume end users are already authenticated via API key or subscription. This eliminates conditional authentication testing and simplifies the test framework by assuming authentication is pre-configured.

## User Stories

### Test Developer Experience

As a test developer, I want all tests to run without authentication checks, so that I don't need to implement skip_if_no_auth patterns and can assume authentication is available.

When running tests, the framework assumes authentication is already configured through Claude Code subscription or API key. Tests fail fast if authentication is actually unavailable rather than skipping gracefully.

## Spec Scope

1. **Skip Auth Pattern Removal** - Remove all 84+ skip_if_no_auth patterns from test files
1. **Authentication Assumption** - Modify validation functions to assume authentication is always available
1. **Test Framework Simplification** - Eliminate conditional authentication logic from test infrastructure
1. **Fast Failure Mode** - Tests fail immediately if authentication is actually unavailable instead of skipping

## Out of Scope

- Modifying core authentication mechanisms in SDKConfig
- Changing subscription-first authentication priority logic
- Removing API key fallback capabilities for runtime usage

## Expected Deliverable

1. All tests run assuming authentication is available with no skip_if_no_auth patterns
1. Test suite fails fast if authentication is unavailable rather than gracefully skipping
1. Simplified test framework with no conditional authentication checking logic

## Spec Documentation

- Tasks: @.agilevv/specs/2025-08-21-remove-skip-auth-patterns/tasks.md
- Technical Specification: @.agilevv/specs/2025-08-21-remove-skip-auth-patterns/sub-specs/technical-spec.md
