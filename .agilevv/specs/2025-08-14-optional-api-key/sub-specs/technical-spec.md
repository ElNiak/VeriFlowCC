# Technical Specification

This is the technical specification for the spec detailed in @.agilevv/specs/2025-08-14-optional-api-key/spec.md

> Created: 2025-08-14
> Version: 1.0.0

## Technical Requirements

- Modify `SDKConfig.__post_init__()` method to remove mandatory API key requirement outside test mode
- Implement authentication detection logic that attempts Claude Code subscription before failing
- Update error messages to clearly indicate when both API key and subscription authentication are unavailable
- Ensure existing API key workflows remain unchanged through backward compatibility checks
- Add graceful fallback handling when Claude Code subscription authentication fails
- Implement proper exception handling with descriptive error messages for authentication failures
- Maintain existing test mode functionality with mock API key generation

## Approach

### 1. Modify SDKConfig Authentication Logic

```python
def __post_init__(self):
    """Initialize SDK configuration with flexible authentication"""
    if self.api_key is None:
        # First try environment variable
        self.api_key = os.getenv("ANTHROPIC_API_KEY")

    # Only require API key in test environments
    if not self.api_key and self._is_test_environment():
        if self.mock_mode:
            self.api_key = "test-mock-key"
        else:
            raise ValueError("API key required in test environments")

    # In production, allow Claude Code subscription authentication
    # No mandatory API key requirement
```

### 2. Authentication Detection Strategy

```python
def _detect_authentication_method(self) -> str:
    """Detect available authentication method"""
    if self.api_key:
        return "api_key"

    # Check for Claude Code subscription
    try:
        # Attempt subscription-based authentication
        if self._verify_claude_subscription():
            return "subscription"
    except Exception as e:
        logger.debug(f"Subscription authentication unavailable: {e}")

    return "none"


def _verify_claude_subscription(self) -> bool:
    """Verify Claude Code subscription availability"""
    # Implementation to check subscription status
    # This would integrate with Claude Code's authentication system
    pass
```

### 3. Error Message Enhancement

```python
def _validate_authentication(self):
    """Validate authentication with descriptive error messages"""
    auth_method = self._detect_authentication_method()

    if auth_method == "none":
        raise AuthenticationError(
            "No authentication method available. Please either:\n"
            "1. Set ANTHROPIC_API_KEY environment variable, or\n"
            "2. Ensure Claude Code subscription is active\n"
            "Run 'claude auth login' to check subscription status."
        )
```

### 4. Backward Compatibility Preservation

```python
# Maintain existing API key priority
def get_client(self):
    """Get Claude client with authentication priority"""
    if self.api_key and not self.api_key.startswith("test-"):
        # Use API key authentication (existing behavior)
        return anthropic.Anthropic(api_key=self.api_key)
    else:
        # Use subscription authentication
        return anthropic.Anthropic()  # Uses default auth
```

## External Dependencies

### Core Dependencies

- `anthropic` SDK - Latest version with subscription auth support
- `os` module - Environment variable access
- `logging` module - Authentication debugging

### Authentication Flow Dependencies

- Claude Code subscription system integration
- Environment variable detection (`ANTHROPIC_API_KEY`)
- Test environment detection utilities

### Error Handling Dependencies

- Custom `AuthenticationError` exception class
- Structured logging for authentication failures
- User-friendly error message formatting

## Implementation Details

### File Modifications Required

1. **`verifflowcc/core/sdk_config.py`**

   - Modify `__post_init__()` method
   - Add authentication detection methods
   - Implement subscription verification
   - Update error handling

1. **Exception Handling**

   - Create `AuthenticationError` class if not exists
   - Add to `verifflowcc/exceptions.py` or similar

1. **Documentation Updates**

   - Update README with new authentication options
   - Modify CLI help text to reflect optional API key
   - Update error message examples

### Testing Requirements

- Unit tests for authentication detection logic
- Integration tests with mock subscription scenarios
- Backward compatibility tests for existing API key workflows
- Error message validation tests
- Test environment detection validation

### Configuration Changes

No changes required to existing configuration files. The modification maintains full backward compatibility while adding flexibility for subscription-based authentication.
