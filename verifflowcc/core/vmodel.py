"""V-Model stage definitions.

This module contains the VModelStage enum to avoid circular imports.
"""

from enum import Enum


class VModelStage(Enum):
    """V-Model stages enumeration."""

    PLANNING = "planning"
    REQUIREMENTS = "requirements"
    DESIGN = "design"
    CODING = "coding"
    UNIT_TESTING = "unit_testing"
    INTEGRATION_TESTING = "integration_testing"
    SYSTEM_TESTING = "system_testing"
    VALIDATION = "validation"


class GatingMode(Enum):
    """Gating control modes."""

    HARD = "hard"  # Must pass to proceed
    SOFT = "soft"  # Warning but can proceed
    OFF = "off"  # No gating
