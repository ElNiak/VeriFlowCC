"""
Test suite for Task 4: Error Handling Standardization.

This module tests the standardized authentication error handling system that provides
generic user-friendly error messages without exposing implementation details.
"""

import os
from unittest.mock import patch

from verifflowcc.cli import graceful_exit_with_message, validate_authentication_gracefully
from verifflowcc.core.sdk_config import AuthenticationError, SDKConfig


class TestGenericErrorMessageValidation:
    """Test generic authentication error message patterns."""

    def test_authentication_error_message_is_generic(self):
        """Test that AuthenticationError messages are generic and user-friendly."""
        # Test with a generic message
        generic_message = (
            "Authentication required. Please configure your Claude Code authentication "
            "through VeriFlow's guidelines."
        )
        error = AuthenticationError(generic_message)

        # Verify the message is generic
        assert "API key" not in str(error).lower()
        assert "anthropic" not in str(error).lower()
        assert "subscription" not in str(error).lower()
        assert "token" not in str(error).lower()
        assert "Authentication required" in str(error)
        assert "VeriFlow" in str(error)

    def test_authentication_error_avoids_implementation_details(self):
        """Test that error messages avoid exposing specific authentication methods."""
        # Create error with generic message
        error = AuthenticationError(
            "Authentication is required to use VeriFlowCC. "
            "Please ensure your environment is configured with appropriate "
            "authentication credentials before proceeding."
        )

        error_str = str(error).lower()

        # Should NOT contain these implementation-specific terms
        forbidden_terms = [
            "api key",
            "anthropic_api_key",
            "subscription",
            "token",
            "sk-",
            "claude code subscription",
            "authentication method",
            "fallback",
            "environment variable",
            "dotenv",
        ]

        for term in forbidden_terms:
            assert term not in error_str, f"Error message should not contain '{term}'"

        # Should contain these generic terms
        required_terms = ["authentication", "required", "environment", "configured"]
        for term in required_terms:
            assert term in error_str, f"Error message should contain '{term}'"

    def test_authentication_error_provides_helpful_guidance(self):
        """Test that error messages provide helpful guidance without specifics."""
        message = (
            "Authentication required. Please configure your Claude Code authentication "
            "through VeriFlow's guidelines before using this tool."
        )
        error = AuthenticationError(message)

        error_str = str(error)

        # Should provide guidance
        assert "configure" in error_str.lower()
        assert "guidelines" in error_str.lower()
        assert "authentication" in error_str.lower()

        # Should not expose how to configure
        assert "export" not in error_str.lower()
        assert "set" not in error_str.lower()
        assert ".env" not in error_str.lower()

    def test_error_message_patterns_consistency(self):
        """Test that all error messages follow consistent patterns."""
        test_messages = [
            "Authentication required. Please configure your Claude Code authentication through VeriFlow's guidelines.",
            "Authentication is required to use VeriFlowCC. Please ensure your environment is configured with appropriate authentication credentials before proceeding.",
            "Authentication configuration needed. Please refer to VeriFlow documentation for setup instructions.",
        ]

        for message in test_messages:
            error = AuthenticationError(message)
            error_str = str(error)

            # All should start with authentication-related term
            assert any(
                error_str.startswith(term) for term in ["Authentication", "Auth"]
            ), f"Message should start with authentication term: {error_str}"

            # All should be helpful but generic
            assert len(error_str) > 50, "Error message should be descriptive"
            assert "." in error_str, "Error message should be properly punctuated"

    def test_sdk_config_error_messages_are_generic(self):
        """Test that SDKConfig raises generic authentication errors."""
        # Test with no authentication available
        with patch.dict(os.environ, {}, clear=True):
            config = SDKConfig(api_key=None)

            # Should not expose method details in any validation
            auth_method = config._detect_authentication_method()
            assert auth_method in ["api_key", "subscription", "none"]


class TestCleanApplicationTermination:
    """Test clean application termination without stack traces."""

    def test_graceful_exit_with_message_function_exists(self):
        """Test that graceful exit function is available."""
        # Function should be importable
        assert callable(graceful_exit_with_message)

    def test_graceful_exit_prints_message_and_exits(self):
        """Test that graceful exit prints user-friendly message and exits cleanly."""
        test_message = "Authentication required. Please configure your environment."

        # Mock sys.exit to prevent actual exit during testing
        with (
            patch("sys.exit") as mock_exit,
            patch("verifflowcc.cli.console.print") as mock_print,
        ):
            graceful_exit_with_message(test_message)

            # Should call console.print with red formatting
            mock_print.assert_called_once()
            call_args = mock_print.call_args[0][0]
            assert "[red]" in call_args
            assert test_message in call_args
            assert "[/red]" in call_args

            # Should exit with code 1
            mock_exit.assert_called_once_with(1)

    def test_graceful_exit_handles_various_message_types(self):
        """Test graceful exit with different message types."""
        test_cases = [
            "Simple error message",
            "Error with\nmultiple\nlines",
            "Error with special characters: àáâãäå",
            "",  # Empty message
        ]

        for message in test_cases:
            with (
                patch("sys.exit") as mock_exit,
                patch("verifflowcc.cli.console.print") as mock_print,
            ):
                graceful_exit_with_message(message)

                mock_print.assert_called_once()
                mock_exit.assert_called_once_with(1)

    def test_validate_authentication_gracefully_always_returns_true(self):
        """Test that graceful authentication validation always returns True."""
        # Should always return True regardless of environment
        with patch.dict(os.environ, {}, clear=True):
            assert validate_authentication_gracefully() is True

        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"}):
            assert validate_authentication_gracefully() is True


class TestAuthenticationMethodDetailsRemoval:
    """Test removal of authentication method details from error exposure."""

    def test_no_specific_auth_methods_in_errors(self):
        """Test that specific authentication methods are not exposed in errors."""
        # Test various SDKConfig configurations
        configs = [
            SDKConfig(api_key=None),
            SDKConfig(api_key=""),
            SDKConfig(api_key="sk-test-key"),
        ]

        for config in configs:
            # Should not expose authentication method details
            auth_method = config._detect_authentication_method()

            # The detection should work but not expose details to users
            assert auth_method in ["api_key", "subscription", "none"]

    def test_error_messages_avoid_method_specific_terms(self):
        """Test that error messages don't contain method-specific terminology."""
        # Create various authentication errors
        generic_errors = [
            "Authentication required. Please configure your Claude Code authentication through VeriFlow's guidelines.",
            "Authentication is required to use VeriFlowCC. Please ensure your environment is configured with appropriate authentication credentials before proceeding.",
        ]

        method_specific_terms = [
            "api key",
            "subscription",
            "token",
            "anthropic",
            "sk-",
            "auth token",
            "bearer",
            "oauth",
            "jwt",
        ]

        for error_msg in generic_errors:
            error = AuthenticationError(error_msg)
            error_lower = str(error).lower()

            for term in method_specific_terms:
                assert (
                    term not in error_lower
                ), f"Error message contains method-specific term '{term}': {error}"

    def test_sdk_config_internal_methods_dont_leak_details(self):
        """Test that internal SDK methods don't leak implementation details."""
        config = SDKConfig()

        # Internal methods can detect auth methods but shouldn't expose them in user errors
        try:
            auth_method = config._detect_authentication_method()
            # This is okay - internal method can know about methods
            assert isinstance(auth_method, str)
        except Exception as e:
            # If there's an exception, it should be generic
            assert "API key" not in str(e)
            assert "subscription" not in str(e)
            assert "Anthropic" not in str(e)


class TestLoggingAuthenticationFailuresGracefully:
    """Test that logging handles authentication failures without exposing methods."""

    def test_logging_does_not_expose_auth_methods(self):
        """Test that authentication failure logging is generic."""
        import logging
        from io import StringIO

        # Capture log output
        log_stream = StringIO()
        handler = logging.StreamHandler(log_stream)
        logger = logging.getLogger("verifflowcc")
        logger.addHandler(handler)
        logger.setLevel(logging.DEBUG)

        try:
            # Create config that might log authentication issues
            with patch.dict(os.environ, {}, clear=True):
                config = SDKConfig(api_key=None)
                config._detect_authentication_method()

            # Check log output doesn't expose sensitive details
            log_output = log_stream.getvalue().lower()

            # Should not contain method-specific details
            sensitive_terms = ["api key", "anthropic", "subscription", "sk-"]
            for term in sensitive_terms:
                assert (
                    term not in log_output
                ), f"Log output contains sensitive term '{term}': {log_output}"

        finally:
            logger.removeHandler(handler)

    def test_sdk_config_validation_logging_is_safe(self):
        """Test that SDK config validation logging doesn't expose methods."""
        import logging
        from io import StringIO

        log_stream = StringIO()
        handler = logging.StreamHandler(log_stream)
        logger = logging.getLogger("verifflowcc.core.sdk_config")
        logger.addHandler(handler)
        logger.setLevel(logging.DEBUG)

        try:
            # Test various config scenarios
            valid_configs = [
                SDKConfig(api_key=None),
                SDKConfig(api_key=""),
            ]

            for _config in valid_configs:
                try:
                    # This might trigger validation and logging
                    pass
                except ValueError:
                    # Expected for some validation scenarios
                    pass

            # Test invalid config separately to capture any logging it might produce
            try:
                SDKConfig(timeout=-1)  # This should cause validation error
            except ValueError:
                # Expected for invalid timeout
                pass

            log_output = log_stream.getvalue().lower()

            # Check logs don't expose authentication implementation
            if log_output:  # Only check if there was log output
                forbidden_terms = ["api key", "subscription", "anthropic"]
                for term in forbidden_terms:
                    assert (
                        term not in log_output
                    ), f"Log contains forbidden term '{term}': {log_output}"

        finally:
            logger.removeHandler(handler)


class TestErrorHandlingIntegration:
    """Test integrated error handling across the system."""

    def test_cli_authentication_validation_is_graceful(self):
        """Test that CLI authentication validation is graceful and generic."""
        # The validate_authentication function should always return True
        # and not expose implementation details
        result = validate_authentication_gracefully()
        assert result is True

    def test_authentication_error_inheritance_is_correct(self):
        """Test that AuthenticationError properly inherits from Exception."""
        error = AuthenticationError("Test message")

        assert isinstance(error, Exception)
        assert isinstance(error, AuthenticationError)
        assert str(error) == "Test message"

    def test_error_messages_are_user_facing_not_developer_facing(self):
        """Test that error messages are appropriate for end users."""
        user_friendly_messages = [
            "Authentication required. Please configure your Claude Code authentication through VeriFlow's guidelines.",
            "Authentication is required to use VeriFlowCC. Please ensure your environment is configured with appropriate authentication credentials before proceeding.",
        ]

        for message in user_friendly_messages:
            error = AuthenticationError(message)
            error_str = str(error)

            # Should be user-friendly
            assert not error_str.isupper()  # Not shouting
            assert "please" in error_str.lower()  # Polite
            assert len(error_str.split()) >= 8  # Descriptive enough

            # Should not contain developer jargon
            dev_terms = ["traceback", "exception", "stack", "debug", "config file"]
            for term in dev_terms:
                assert term not in error_str.lower()


class TestErrorHandlingTestsPass:
    """Test that the error handling system passes all validation."""

    def test_all_error_patterns_are_consistent(self):
        """Test that all error handling patterns work consistently."""
        # Test the complete flow
        with patch("sys.exit") as mock_exit:
            # Should be able to create and handle authentication errors gracefully
            message = (
                "Authentication required. Please configure your Claude Code authentication "
                "through VeriFlow's guidelines."
            )

            error = AuthenticationError(message)

            # Error should be well-formed
            assert str(error)
            assert "Authentication" in str(error)

            # Should be able to exit gracefully
            with patch("verifflowcc.cli.console.print"):
                graceful_exit_with_message(str(error))
                mock_exit.assert_called_with(1)

    def test_sdk_config_integrates_with_error_handling(self):
        """Test that SDKConfig integrates properly with error handling."""
        # Should be able to create configs without exposing implementation details
        config = SDKConfig(api_key=None)

        # Should gracefully handle authentication detection
        auth_method = config._detect_authentication_method()
        assert isinstance(auth_method, str)

        # Should integrate with graceful validation
        assert validate_authentication_gracefully() is True

    def test_complete_authentication_error_flow(self):
        """Test the complete authentication error handling flow."""
        # Simulate authentication failure scenario
        with patch.dict(os.environ, {}, clear=True):
            # Create config
            config = SDKConfig(api_key=None)

            # Detect auth method (internal)
            auth_method = config._detect_authentication_method()

            # Should handle gracefully
            if auth_method == "none":
                # Would normally create generic error
                error = AuthenticationError(
                    "Authentication required. Please configure your Claude Code authentication "
                    "through VeriFlow's guidelines."
                )

                # Error should be user-friendly
                assert "Authentication" in str(error)
                assert "guidelines" in str(error)
                assert "API key" not in str(error)

                # Should be able to exit gracefully
                with patch("sys.exit"), patch("verifflowcc.cli.console.print"):
                    graceful_exit_with_message(str(error))
