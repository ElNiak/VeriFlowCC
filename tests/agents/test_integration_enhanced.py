"""Enhanced tests for IntegrationAgent with comprehensive real Claude Code SDK integration.

This module provides comprehensive testing for the IntegrationAgent including
GO/NO-GO decision making, deployment validation, and complete V-Model integration.

NOTE: The comprehensive real SDK integration tests for the Integration agent
have been moved to test_real_integration_sdk.py to maintain consistency with
other agent testing patterns.

This file now serves as a redirect/alias to ensure test discovery works properly.
"""

import pytest

# Import all test classes from the real SDK integration test module
from .test_real_integration_sdk import (
    TestRealIntegrationArtifactGeneration,
    TestRealIntegrationErrorHandling,
    TestRealIntegrationGONOGODecisionMaking,
    TestRealIntegrationPerformance,
    TestRealIntegrationSDKInitialization,
    TestRealIntegrationSessionManagement,
    TestRealIntegrationSystemHealthValidation,
)

# Mark all tests with enhanced integration markers
pytestmark = [
    pytest.mark.integration,
    pytest.mark.real_sdk,
    pytest.mark.asyncio,
    pytest.mark.enhanced,
]

# Re-export all test classes for backward compatibility
__all__ = [
    "TestRealIntegrationArtifactGeneration",
    "TestRealIntegrationErrorHandling",
    "TestRealIntegrationGONOGODecisionMaking",
    "TestRealIntegrationPerformance",
    "TestRealIntegrationSDKInitialization",
    "TestRealIntegrationSessionManagement",
    "TestRealIntegrationSystemHealthValidation",
]
