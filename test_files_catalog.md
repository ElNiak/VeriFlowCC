# Test Files Catalog for skip_if_no_auth Pattern Implementation

This document catalogs all test files in the VeriFlowCC project that require updates to implement the `skip_if_no_auth` pattern for graceful authentication handling.

## Summary Statistics

- **Total test files**: 55
- **Files requiring authentication updates**: 43
- **Pattern implementation needed**: Remove mandatory ANTHROPIC_API_KEY requirements while maintaining real integration testing philosophy

## Files Requiring skip_if_no_auth Pattern Updates

### Agent Tests (21 files)

1. `tests/agents/test_agent_factory.py`
1. `tests/agents/test_ai_generated_task_validation.py`
1. `tests/agents/test_architect.py`
1. `tests/agents/test_basic_sdk_response_validation.py`
1. `tests/agents/test_developer.py`
1. `tests/agents/test_integration.py`
1. `tests/agents/test_integration_enhanced.py`
1. `tests/agents/test_pydantic_schema_validation.py`
1. `tests/agents/test_qa_tester.py`
1. `tests/agents/test_real_architect_sdk.py`
1. `tests/agents/test_real_developer_sdk.py`
1. `tests/agents/test_real_integration_sdk.py`
1. `tests/agents/test_real_qa_tester_sdk.py`
1. `tests/agents/test_real_requirements_analyst_sdk.py`
1. `tests/agents/test_real_sdk_code_generation.py`
1. `tests/agents/test_requirements_analyst.py`
1. `tests/agents/test_session_management.py`
1. `tests/agents/test_streaming_interruption.py`
1. `tests/agents/test_streaming_response.py`
1. `tests/agents/test_streaming_timeout_retry.py`
1. `tests/agents/test_structured_output_parsing.py`

### Core Tests (3 files)

22. `tests/core/test_path_config.py`
01. `tests/core/test_real_sdk_config_integration.py`
01. `tests/core/test_sdk_config.py`

### Integration Tests (18 files)

25. `tests/integration/test_authentication_error_handling.py`
01. `tests/integration/test_authentication_integration.py`
01. `tests/integration/test_concurrent_session_isolation.py`
01. `tests/integration/test_document_based_session_storage.py`
01. `tests/integration/test_e2e_error_handling.py`
01. `tests/integration/test_e2e_real_sdk_streaming.py`
01. `tests/integration/test_e2e_real_sdk_vmodel_workflow.py`
01. `tests/integration/test_e2e_session_persistence.py`
01. `tests/integration/test_e2e_vmodel_workflow.py`
01. `tests/integration/test_e2e_vmodel_workflow_handoffs.py`
01. `tests/integration/test_e2e_vmodel_workflow_part2.py`
01. `tests/integration/test_e2e_vmodel_workflow_verification.py`
01. `tests/integration/test_mailbuddy_vmodel_integration.py`
01. `tests/integration/test_multi_agent_coordination.py`
01. `tests/integration/test_orchestrator_integration.py`
01. `tests/integration/test_path_config_integration.py`
01. `tests/integration/test_real_authentication_integration.py`
01. `tests/integration/test_real_claude_code_sdk_requirements.py`
01. `tests/integration/test_real_orchestrator_integration.py`
01. `tests/integration/test_sdk_integration.py`
01. `tests/integration/test_vmodel_session_context.py`

### Performance Tests (1 file)

46. `tests/performance/test_sdk_performance.py`

### Schema Tests (1 file)

47. `tests/schemas/test_agent_schemas.py`

### CLI and Main Tests (4 files)

48. `tests/test_cli.py`
01. `tests/test_integration.py`
01. `tests/test_real_cli_integration.py`
01. `tests/test_skip_auth_pattern.py` (our new test file)

### Validation Tests (2 files)

52. `tests/validation/test_documentation_validation.py`
01. `tests/validation/test_mock_removal_validation.py`

### Miscellaneous Tests (2 files)

54. `tests/test_examples.py`
01. `tests/test_isolation_meta.py`

## Files NOT Requiring Updates (Already Handled or No Authentication)

- `tests/conftest.py` - Already updated with skip_if_no_auth pattern
- `tests/test_conftest.py` - Tests conftest functionality, may need minor updates

## Update Strategy by File Type

### High Priority (Real SDK Tests)

Files with "real\_" prefix are high priority as they directly interact with Claude SDK:

- All `tests/agents/test_real_*.py` files (8 files)
- All `tests/integration/test_real_*.py` files (4 files)
- `tests/core/test_real_sdk_config_integration.py`
- `tests/test_real_cli_integration.py`

### Medium Priority (SDK Integration Tests)

Files that use SDKConfig or authentication patterns:

- All other `tests/agents/` files
- Most `tests/integration/` files
- `tests/core/test_sdk_config.py`

### Low Priority (Infrastructure Tests)

Files with minimal authentication dependencies:

- `tests/validation/` files
- `tests/schemas/` files
- Miscellaneous test files

## Implementation Pattern

For each file, implement one of these patterns:

### Pattern 1: Explicit check_auth fixture usage

```python
@pytest.mark.usefixtures("check_auth")
class TestClassRequiringAuth:
    pass
```

### Pattern 2: Manual skip_if_no_auth calls

```python
def test_function_requiring_auth():
    skip_if_no_auth()
    # Test implementation
```

### Pattern 3: Class-level fixture usage

```python
class TestSDKIntegration:
    @pytest.fixture(autouse=True)
    def _check_auth(self, check_auth):
        pass
```

## Expected Benefits

After implementing the skip_if_no_auth pattern across all 43 files:

1. **Graceful Degradation**: Tests skip cleanly when authentication is not available
1. **No Breaking Changes**: Existing test functionality preserved
1. **Real Integration Maintained**: Zero mock dependencies philosophy preserved
1. **Developer Experience**: Clear skip messages help developers understand requirements
1. **CI/CD Flexibility**: Tests can run in environments without API keys

## Implementation Order

1. **Phase 1**: High priority real SDK tests (13 files)
1. **Phase 2**: Agent and core tests (24 files)
1. **Phase 3**: Integration tests (15 files)
1. **Phase 4**: Remaining validation and misc tests (6 files)

Total: 58 files requiring updates across 4 phases.
