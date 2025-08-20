"""
Mock Removal Validation Tests

These tests validate the complete elimination of unittest.mock infrastructure from the codebase.
They follow the TDD approach - failing initially, then passing after mock removal.

Test Categories:
1. Import validation - No unittest.mock imports remain
2. Decorator validation - No @patch decorators remain
3. Instance validation - No MagicMock/AsyncMock instances remain
4. SDK class validation - No MockSDKClient/MockSDKOptions classes remain
5. Parameter validation - No mock_mode parameters remain
"""

import re
from pathlib import Path

import pytest


class MockRemovalValidator:
    """Validates complete removal of mock infrastructure."""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.source_dirs = [
            project_root / "verifflowcc",
            project_root / "tests",
        ]

    def get_python_files(self) -> list[Path]:
        """Get all Python files in source directories."""
        python_files = []
        for source_dir in self.source_dirs:
            if source_dir.exists():
                python_files.extend(source_dir.rglob("*.py"))
        return python_files

    def check_unittest_mock_imports(self) -> list[tuple[Path, int, str]]:
        """Check for any unittest.mock imports."""
        violations = []
        pattern = re.compile(r"from unittest\.mock import|import unittest\.mock")

        for py_file in self.get_python_files():
            try:
                with py_file.open(encoding="utf-8") as f:
                    for line_num, line in enumerate(f, 1):
                        if pattern.search(line):
                            violations.append((py_file, line_num, line.strip()))
            except (UnicodeDecodeError, PermissionError):
                continue  # Skip problematic files

        return violations

    def check_patch_decorators(self) -> list[tuple[Path, int, str]]:
        """Check for @patch decorators."""
        violations = []
        pattern = re.compile(r"@patch\(")

        for py_file in self.get_python_files():
            try:
                with py_file.open(encoding="utf-8") as f:
                    for line_num, line in enumerate(f, 1):
                        if pattern.search(line):
                            violations.append((py_file, line_num, line.strip()))
            except (UnicodeDecodeError, PermissionError):
                continue

        return violations

    def check_mock_instances(self) -> list[tuple[Path, int, str]]:
        """Check for MagicMock/AsyncMock instances."""
        violations = []
        pattern = re.compile(r"(MagicMock|AsyncMock)\(")

        for py_file in self.get_python_files():
            try:
                with py_file.open(encoding="utf-8") as f:
                    for line_num, line in enumerate(f, 1):
                        if pattern.search(line):
                            violations.append((py_file, line_num, line.strip()))
            except (UnicodeDecodeError, PermissionError):
                continue

        return violations

    def check_mock_sdk_classes(self) -> list[tuple[Path, int, str]]:
        """Check for MockSDKClient/MockSDKOptions classes."""
        violations = []
        pattern = re.compile(r"class (MockSDKClient|MockSDKOptions)")

        for py_file in self.get_python_files():
            try:
                with py_file.open(encoding="utf-8") as f:
                    for line_num, line in enumerate(f, 1):
                        if pattern.search(line):
                            violations.append((py_file, line_num, line.strip()))
            except (UnicodeDecodeError, PermissionError):
                continue

        return violations

    def check_mock_mode_parameters(self) -> list[tuple[Path, int, str]]:
        """Check for mock_mode parameters in function/class signatures."""
        violations = []
        # Look for mock_mode in function definitions and class constructors
        pattern = re.compile(r"(def __init__|def \w+).*mock_mode")

        for py_file in self.get_python_files():
            # Skip test files that may legitimately reference mock_mode in comments
            if "test_" in py_file.name:
                continue

            try:
                with py_file.open(encoding="utf-8") as f:
                    for line_num, line in enumerate(f, 1):
                        if pattern.search(line):
                            violations.append((py_file, line_num, line.strip()))
            except (UnicodeDecodeError, PermissionError):
                continue

        return violations

    def check_mock_mode_usages(self) -> list[tuple[Path, int, str]]:
        """Check for mock_mode attribute usages and assignments."""
        violations = []
        # Look for self.mock_mode assignments and usages
        pattern = re.compile(r"(self\.mock_mode|mock_mode=)")

        for py_file in self.get_python_files():
            # Skip test files that may legitimately use mock_mode
            if "test_" in py_file.name:
                continue

            try:
                with py_file.open(encoding="utf-8") as f:
                    for line_num, line in enumerate(f, 1):
                        if pattern.search(line):
                            violations.append((py_file, line_num, line.strip()))
            except (UnicodeDecodeError, PermissionError):
                continue

        return violations


@pytest.fixture
def mock_validator() -> MockRemovalValidator:
    """Fixture providing mock removal validator."""
    project_root = Path(__file__).parent.parent.parent
    return MockRemovalValidator(project_root)


class TestMockInfrastructureRemoval:
    """Test suite validating complete mock infrastructure removal."""

    def test_no_unittest_mock_imports(self, mock_validator: MockRemovalValidator) -> None:
        """Validate no unittest.mock imports remain in codebase."""
        violations = mock_validator.check_unittest_mock_imports()

        if violations:
            error_msg = "Found unittest.mock imports that should be removed:\n"
            for file_path, line_num, line in violations:
                relative_path = file_path.relative_to(mock_validator.project_root)
                error_msg += f"  {relative_path}:{line_num}: {line}\n"
            pytest.fail(error_msg)

    def test_no_patch_decorators(self, mock_validator: MockRemovalValidator) -> None:
        """Validate no @patch decorators remain in codebase."""
        violations = mock_validator.check_patch_decorators()

        if violations:
            error_msg = "Found @patch decorators that should be removed:\n"
            for file_path, line_num, line in violations:
                relative_path = file_path.relative_to(mock_validator.project_root)
                error_msg += f"  {relative_path}:{line_num}: {line}\n"
            pytest.fail(error_msg)

    def test_no_magic_mock_instances(self, mock_validator: MockRemovalValidator) -> None:
        """Validate no MagicMock/AsyncMock instances remain in codebase."""
        violations = mock_validator.check_mock_instances()

        if violations:
            error_msg = "Found MagicMock/AsyncMock instances that should be removed:\n"
            for file_path, line_num, line in violations:
                relative_path = file_path.relative_to(mock_validator.project_root)
                error_msg += f"  {relative_path}:{line_num}: {line}\n"
            pytest.fail(error_msg)

    def test_no_mock_sdk_classes(self, mock_validator: MockRemovalValidator) -> None:
        """Validate MockSDKClient/MockSDKOptions classes are removed."""
        violations = mock_validator.check_mock_sdk_classes()

        if violations:
            error_msg = "Found MockSDK classes that should be removed:\n"
            for file_path, line_num, line in violations:
                relative_path = file_path.relative_to(mock_validator.project_root)
                error_msg += f"  {relative_path}:{line_num}: {line}\n"
            pytest.fail(error_msg)

    def test_no_mock_mode_parameters(self, mock_validator: MockRemovalValidator) -> None:
        """Validate mock_mode parameters are removed from function signatures."""
        violations = mock_validator.check_mock_mode_parameters()

        if violations:
            error_msg = "Found mock_mode parameters that should be removed:\n"
            for file_path, line_num, line in violations:
                relative_path = file_path.relative_to(mock_validator.project_root)
                error_msg += f"  {relative_path}:{line_num}: {line}\n"
            pytest.fail(error_msg)

    def test_no_mock_mode_usages(self, mock_validator: MockRemovalValidator) -> None:
        """Validate mock_mode attribute usages are removed."""
        violations = mock_validator.check_mock_mode_usages()

        if violations:
            error_msg = "Found mock_mode usages that should be removed:\n"
            for file_path, line_num, line in violations:
                relative_path = file_path.relative_to(mock_validator.project_root)
                error_msg += f"  {relative_path}:{line_num}: {line}\n"
            pytest.fail(error_msg)


class TestRealSDKIntegrity:
    """Test suite validating real SDK integration remains intact."""

    def test_real_sdk_imports_preserved(self, mock_validator: MockRemovalValidator) -> None:
        """Validate real SDK imports are preserved."""
        base_agent_file = mock_validator.project_root / "verifflowcc" / "agents" / "base.py"

        if not base_agent_file.exists():
            pytest.skip("BaseAgent file not found")

        with base_agent_file.open() as f:
            content = f.read()

        # Should have real Claude Code SDK imports
        expected_patterns = [
            r"from claude_code_sdk import",
            r"try:\s*from claude_code_sdk",
        ]

        found_real_imports = False
        for pattern in expected_patterns:
            if re.search(pattern, content):
                found_real_imports = True
                break

        if not found_real_imports:
            pytest.fail("Real Claude Code SDK imports not found in BaseAgent")

    def test_isolated_test_directories(self, mock_validator: MockRemovalValidator) -> None:
        """Validate test isolation framework remains intact."""
        conftest_file = mock_validator.project_root / "tests" / "conftest.py"

        if not conftest_file.exists():
            pytest.skip("conftest.py not found")

        with conftest_file.open() as f:
            content = f.read()

        # Should have isolation fixtures
        isolation_patterns = [
            r"isolated_agilevv_dir",
            r"\.agilevv-test",
        ]

        for pattern in isolation_patterns:
            if not re.search(pattern, content):
                pytest.fail(f"Test isolation pattern '{pattern}' not found in conftest.py")


class TestValidationMetrics:
    """Test suite providing metrics on mock removal progress."""

    def test_mock_removal_progress(self, mock_validator: MockRemovalValidator) -> None:
        """Report progress metrics on mock removal."""

        # Gather all violations
        mock_imports = mock_validator.check_unittest_mock_imports()
        patch_decorators = mock_validator.check_patch_decorators()
        mock_instances = mock_validator.check_mock_instances()
        mock_sdk_classes = mock_validator.check_mock_sdk_classes()
        mock_mode_params = mock_validator.check_mock_mode_parameters()
        mock_mode_usages = mock_validator.check_mock_mode_usages()

        # Create summary
        total_violations = (
            len(mock_imports)
            + len(patch_decorators)
            + len(mock_instances)
            + len(mock_sdk_classes)
            + len(mock_mode_params)
            + len(mock_mode_usages)
        )

        summary = f"""
        Mock Removal Progress Summary:
        ============================
        unittest.mock imports: {len(mock_imports)}
        @patch decorators: {len(patch_decorators)}
        Mock instances: {len(mock_instances)}
        MockSDK classes: {len(mock_sdk_classes)}
        mock_mode parameters: {len(mock_mode_params)}
        mock_mode usages: {len(mock_mode_usages)}

        Total violations: {total_violations}
        """

        # This test always passes but provides metrics
        print(summary)

        # Optionally fail if violations found (uncomment for strict validation)
        # if total_violations > 0:
        #     pytest.fail(f"Mock infrastructure removal incomplete: {total_violations} violations found")
