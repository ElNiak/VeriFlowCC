"""Test report schema for test execution results."""

from pydantic import BaseModel, Field


class TestResult(BaseModel):
    """Individual test result."""

    test_name: str = Field(..., description="Name of the test")
    test_path: str | None = Field(None, description="File path of the test")
    passed: bool = Field(..., description="Whether the test passed")
    error_message: str | None = Field(None, description="Error message if test failed")
    execution_time: float = Field(..., description="Test execution time in seconds")
    stdout: str | None = Field(None, description="Standard output from test")
    stderr: str | None = Field(None, description="Standard error from test")


class TestReport(BaseModel):
    """Complete test execution report."""

    total_tests: int = Field(..., description="Total number of tests")
    passed_tests: int = Field(..., description="Number of passed tests")
    failed_tests: int = Field(..., description="Number of failed tests")
    skipped_tests: int = Field(default=0, description="Number of skipped tests")
    test_results: list[TestResult] = Field(..., description="Individual test results")
    coverage_percentage: float | None = Field(None, description="Code coverage percentage")
    total_execution_time: float = Field(..., description="Total execution time in seconds")
    recommendation: str | None = Field(None, description="AI-generated recommendation")
    test_command: str | None = Field(None, description="Command used to run tests")

    @property
    def success_rate(self) -> float:
        """Calculate test success rate."""
        if self.total_tests == 0:
            return 0.0
        return (self.passed_tests / self.total_tests) * 100

    @property
    def all_passed(self) -> bool:
        """Check if all tests passed."""
        return self.failed_tests == 0 and self.total_tests > 0

    def get_failed_tests(self) -> list[TestResult]:
        """Get list of failed tests."""
        return [test for test in self.test_results if not test.passed]

    def generate_summary(self) -> str:
        """Generate a human-readable summary."""
        summary_lines = [
            "Test Execution Summary:",
            f"{'=' * 50}",
            f"Total Tests: {self.total_tests}",
            f"Passed: {self.passed_tests} ({self.success_rate:.1f}%)",
            f"Failed: {self.failed_tests}",
        ]

        if self.skipped_tests > 0:
            summary_lines.append(f"Skipped: {self.skipped_tests}")

        if self.coverage_percentage is not None:
            summary_lines.append(f"Coverage: {self.coverage_percentage:.1f}%")

        summary_lines.append(f"Execution Time: {self.total_execution_time:.2f}s")

        if self.failed_tests > 0:
            summary_lines.extend(["", "Failed Tests:"])
            for test in self.get_failed_tests():
                summary_lines.append(f"  ❌ {test.test_name}")
                if test.error_message:
                    # Truncate long error messages
                    error_msg = test.error_message[:200]
                    if len(test.error_message) > 200:
                        error_msg += "..."
                    summary_lines.append(f"     Error: {error_msg}")

        if self.recommendation:
            summary_lines.extend(["", "Recommendation:", self.recommendation])

        return "\n".join(summary_lines)
