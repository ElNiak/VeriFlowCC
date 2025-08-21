"""Documentation validation tests for API key assumptions removal.

Tests validate that documentation contains proper authentication disclaimers
and does not contain explicit API key setup instructions.
"""

import re
from pathlib import Path

import pytest


class TestDocumentationValidation:
    """Test suite for validating documentation authentication disclaimers."""

    @pytest.fixture
    def project_root(self) -> Path:
        """Get the project root directory."""
        return Path(__file__).parents[2]

    @pytest.fixture
    def expected_disclaimer_pattern(self) -> str:
        """Expected authentication disclaimer pattern."""
        return (
            r"VeriFlowCC requires Claude Code authentication.*"
            r"Users must.*configure.*authentication.*method.*"
            r"through VeriFlow.*guidelines"
        )

    @pytest.fixture
    def forbidden_api_key_patterns(self) -> list[str]:
        """Patterns that should not appear in documentation."""
        return [
            r"ANTHROPIC_API_KEY",
            r"export ANTHROPIC_API_KEY",
            r"set your API key",
            r"API key setup",
            r"configure your API key",
            r"CLAUDE_API_KEY",
            r"--api-key",
            r"api_key.*=.*\"sk-",
            r"anthropic\.api_key",
        ]

    def test_readme_contains_authentication_disclaimer(
        self, project_root: Path, expected_disclaimer_pattern: str
    ):
        """Test that README.md contains the authentication disclaimer."""
        readme_path = project_root / "README.md"
        assert readme_path.exists(), "README.md file should exist"

        content = readme_path.read_text(encoding="utf-8")

        # Check for authentication disclaimer section
        assert (
            "## Authentication Disclaimer" in content
        ), "README.md should have an Authentication Disclaimer section"

        # Check for the expected disclaimer pattern (case insensitive, multiline)
        disclaimer_match = re.search(
            expected_disclaimer_pattern, content, re.IGNORECASE | re.DOTALL
        )
        assert (
            disclaimer_match is not None
        ), "README.md should contain the expected authentication disclaimer pattern"

    def test_readme_no_api_key_instructions(
        self, project_root: Path, forbidden_api_key_patterns: list[str]
    ):
        """Test that README.md does not contain API key setup instructions."""
        readme_path = project_root / "README.md"
        content = readme_path.read_text(encoding="utf-8")

        for pattern in forbidden_api_key_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            assert not matches, (
                f"README.md should not contain API key pattern '{pattern}'. " f"Found: {matches}"
            )

    def test_claude_md_contains_authentication_disclaimer(
        self, project_root: Path, expected_disclaimer_pattern: str
    ):
        """Test that CLAUDE.md contains the authentication disclaimer."""
        claude_md_path = project_root / "CLAUDE.md"
        assert claude_md_path.exists(), "CLAUDE.md file should exist"

        content = claude_md_path.read_text(encoding="utf-8")

        # Check for authentication configuration section
        assert (
            "### Authentication Configuration" in content
        ), "CLAUDE.md should have an Authentication Configuration section"

        # Check for the expected disclaimer pattern (case insensitive, multiline)
        disclaimer_match = re.search(
            expected_disclaimer_pattern, content, re.IGNORECASE | re.DOTALL
        )
        assert (
            disclaimer_match is not None
        ), "CLAUDE.md should contain the expected authentication disclaimer pattern"

    def test_claude_md_no_api_key_instructions(
        self, project_root: Path, forbidden_api_key_patterns: list[str]
    ):
        """Test that CLAUDE.md does not contain explicit API key instructions."""
        claude_md_path = project_root / "CLAUDE.md"
        content = claude_md_path.read_text(encoding="utf-8")

        # Allow generic references to API key as optional configuration
        allowed_patterns = [
            r"api_key: Optional\[str\] = None",  # Code documentation
            r"API key configuration \(if using direct API access\)",  # Generic reference
        ]

        for pattern in forbidden_api_key_patterns:
            # Skip patterns that are in allowed list
            if any(allowed in pattern for allowed in allowed_patterns):
                continue

            matches = re.findall(pattern, content, re.IGNORECASE)
            assert not matches, (
                f"CLAUDE.md should not contain explicit API key pattern '{pattern}'. "
                f"Found: {matches}"
            )

    def test_cli_help_contains_authentication_disclaimer(self, project_root: Path):
        """Test that CLI help text contains authentication disclaimer."""
        cli_path = project_root / "verifflowcc" / "cli.py"
        assert cli_path.exists(), "CLI module should exist"

        content = cli_path.read_text(encoding="utf-8")

        # Check main app help text
        assert (
            "Requires Claude Code authentication" in content
        ), "CLI app help should mention authentication requirement"

        # Check main callback docstring
        auth_patterns = [
            r"AUTHENTICATION REQUIRED.*VeriFlowCC requires Claude Code authentication",
            r"ensure.*environment.*configured.*authentication.*methods",
        ]

        for pattern in auth_patterns:
            assert re.search(
                pattern, content, re.IGNORECASE | re.DOTALL
            ), f"CLI should contain authentication pattern: {pattern}"

    def test_cli_usage_guide_authentication_disclaimer(
        self, project_root: Path, expected_disclaimer_pattern: str
    ):
        """Test that CLI usage guide contains authentication disclaimer."""
        cli_usage_path = project_root / "docs" / "CLI_USAGE.md"
        if not cli_usage_path.exists():
            pytest.skip("CLI_USAGE.md file does not exist")

        content = cli_usage_path.read_text(encoding="utf-8")

        # Should contain authentication section or disclaimer
        auth_sections = ["Authentication", "Setup", "Prerequisites"]
        has_auth_section = any(section in content for section in auth_sections)

        if has_auth_section:
            # Check for proper disclaimer pattern
            disclaimer_match = re.search(
                expected_disclaimer_pattern, content, re.IGNORECASE | re.DOTALL
            )
            assert (
                disclaimer_match is not None
            ), "CLI_USAGE.md should contain the expected authentication disclaimer"

    def test_cli_usage_guide_no_api_key_instructions(
        self, project_root: Path, forbidden_api_key_patterns: list[str]
    ):
        """Test that CLI usage guide does not contain API key instructions."""
        cli_usage_path = project_root / "docs" / "CLI_USAGE.md"
        if not cli_usage_path.exists():
            pytest.skip("CLI_USAGE.md file does not exist")

        content = cli_usage_path.read_text(encoding="utf-8")

        for pattern in forbidden_api_key_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            assert not matches, (
                f"CLI_USAGE.md should not contain API key pattern '{pattern}'. " f"Found: {matches}"
            )

    def test_real_testing_guide_authentication_handling(self, project_root: Path):
        """Test that REAL_TESTING_GUIDE.md has proper authentication handling."""
        testing_guide_path = project_root / "docs" / "REAL_TESTING_GUIDE.md"
        if not testing_guide_path.exists():
            pytest.skip("REAL_TESTING_GUIDE.md file does not exist")

        content = testing_guide_path.read_text(encoding="utf-8")

        # Should mention flexible authentication approaches
        auth_requirements = [
            r"configured.*authentication.*\(subscription or API key\)",
            r"flexible authentication.*approaches",
            r"authentication.*flexibility",
        ]

        for pattern in auth_requirements:
            assert re.search(
                pattern, content, re.IGNORECASE
            ), f"REAL_TESTING_GUIDE.md should contain authentication pattern: {pattern}"

    def test_documentation_consistency(self, project_root: Path):
        """Test that all documentation uses consistent authentication messaging."""
        doc_files = [
            project_root / "README.md",
            project_root / "CLAUDE.md",
            project_root / "docs" / "CLI_USAGE.md",
            project_root / "docs" / "REAL_TESTING_GUIDE.md",
        ]

        consistent_phrases = [
            "Claude Code authentication",
            "authentication method",
            "VeriFlow's guidelines",
        ]

        for doc_file in doc_files:
            if not doc_file.exists():
                continue

            content = doc_file.read_text(encoding="utf-8")

            # Check for at least one consistent phrase
            has_consistent_phrase = any(phrase in content for phrase in consistent_phrases)

            assert (
                has_consistent_phrase
            ), f"{doc_file.name} should use consistent authentication messaging"

    def test_no_hardcoded_credentials_in_docs(self, project_root: Path):
        """Test that no documentation contains hardcoded credentials."""
        doc_files = [
            project_root / "README.md",
            project_root / "CLAUDE.md",
            project_root / "docs" / "CLI_USAGE.md",
            project_root / "docs" / "REAL_TESTING_GUIDE.md",
        ]

        credential_patterns = [
            r"sk-[a-zA-Z0-9]{40,}",  # Anthropic API key format
            r"key[_-]?[a-zA-Z0-9]{20,}",  # Generic key patterns
            r"token[_-]?[a-zA-Z0-9]{20,}",  # Token patterns
            r"secret[_-]?[a-zA-Z0-9]{20,}",  # Secret patterns
        ]

        for doc_file in doc_files:
            if not doc_file.exists():
                continue

            content = doc_file.read_text(encoding="utf-8")

            for pattern in credential_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                # Filter out obvious placeholders and examples
                real_matches = [
                    match
                    for match in matches
                    if not any(
                        placeholder in match.lower()
                        for placeholder in ["example", "placeholder", "your", "test"]
                    )
                ]

                assert not real_matches, (
                    f"{doc_file.name} should not contain hardcoded credentials "
                    f"matching pattern '{pattern}'. Found: {real_matches}"
                )
