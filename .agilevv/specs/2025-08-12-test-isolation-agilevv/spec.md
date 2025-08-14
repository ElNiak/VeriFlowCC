# Spec Requirements Document

> Spec: Test Isolation for .agilevv Directory
> Created: 2025-08-12

## Overview

Implement a configurable base directory system for the .agilevv/ folder to enable complete test isolation and prevent test pollution of production configuration. This feature will allow tests to use separate .agilevv-test/ directories while maintaining backward compatibility with the default .agilevv/ folder for production use.

## User Stories

### Test Developer Experience

As a test developer, I want to run tests without affecting the production .agilevv/ directory, so that I can safely execute tests in parallel and maintain a clean development environment.

The workflow involves running pytest with automatic isolation where each test suite or individual test gets its own isolated .agilevv/ directory in a temporary location. Tests can share common fixtures when appropriate, and the framework automatically cleans up test directories based on the test's isolation requirements.

### CI/CD Pipeline Integration

As a DevOps engineer, I want the test suite to run in complete isolation from any existing .agilevv/ directories, so that CI/CD pipelines can execute tests reliably without side effects.

The CI environment will automatically use test-specific directories, preventing any modifications to the repository's .agilevv/ folder during automated testing. This ensures reproducible test results across different environments and prevents test artifacts from being accidentally committed.

### Developer Workflow Protection

As a developer, I want my local .agilevv/ configuration to remain untouched during test execution, so that my development workflow state is preserved.

When running tests locally, the framework will use temporary test directories by default, protecting the developer's working configuration. Developers can optionally share test data between related tests for efficiency while maintaining isolation from production data.

## Spec Scope

1. **Configurable Base Directory** - Refactor all hard-coded .agilevv/ paths to use a configurable base directory throughout the codebase
1. **Test Isolation Framework** - Implement pytest fixtures and utilities for creating isolated test environments with .agilevv-test/ directories
1. **Environment Variable Support** - Add AGILEVV_BASE_DIR environment variable support for overriding the default directory
1. **Test Data Management** - Create a flexible system for sharing common test data between related tests with configurable cleanup strategies
1. **Backward Compatibility** - Maintain .agilevv/ as the default directory for production use without breaking existing workflows

## Out of Scope

- Migration tools for existing .agilevv/ data structures
- Changes to the .agilevv/ directory structure itself
- Modifications to production behavior (only test isolation)
- Cross-platform path handling improvements beyond test isolation needs
- Performance optimizations unrelated to test isolation

## Expected Deliverable

1. All tests run in complete isolation using temporary .agilevv-test/ directories without affecting production .agilevv/ folder
1. Tests can be executed in parallel without conflicts or race conditions
1. Existing production code continues to use .agilevv/ by default with no breaking changes
