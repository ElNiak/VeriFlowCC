"""Tests for TestReport schema and related models."""

import pytest
from verifflowcc.schemas.test_report import TestReport, TestResult


def test_test_result_creation():
    """Test TestResult model creation."""
    test_result = TestResult(
        test_name="test_user_login",
        test_path="tests/test_auth.py",
        passed=True,
        execution_time=0.5,
        error_message=None,
        stdout="Test output",
        stderr=None,
    )

    assert test_result.test_name == "test_user_login"
    assert test_result.test_path == "tests/test_auth.py"
    assert test_result.passed is True
    assert test_result.execution_time == 0.5
    assert test_result.error_message is None
    assert test_result.stdout == "Test output"


def test_test_result_with_error():
    """Test TestResult with error."""
    test_result = TestResult(
        test_name="test_database_connection",
        passed=False,
        execution_time=2.3,
        error_message="Connection timeout",
        stderr="Error: Connection timeout",
    )

    assert test_result.passed is False
    assert test_result.error_message == "Connection timeout"
    assert test_result.stderr == "Error: Connection timeout"


def test_test_report_creation():
    """Test TestReport model creation."""
    test_results = [
        TestResult(
            test_name="test_1",
            passed=True,
            execution_time=0.1,
        ),
        TestResult(
            test_name="test_2",
            passed=False,
            execution_time=0.2,
            error_message="Assertion failed",
        ),
        TestResult(
            test_name="test_3",
            passed=True,
            execution_time=0.3,
        ),
    ]

    report = TestReport(
        total_tests=3,
        passed_tests=2,
        failed_tests=1,
        skipped_tests=0,
        test_results=test_results,
        total_execution_time=0.6,
        coverage_percentage=85.5,
        test_command="pytest tests/",
    )

    assert report.total_tests == 3
    assert report.passed_tests == 2
    assert report.failed_tests == 1
    assert report.skipped_tests == 0
    assert len(report.test_results) == 3
    assert report.total_execution_time == 0.6
    assert report.coverage_percentage == 85.5
    assert report.test_command == "pytest tests/"


def test_success_rate():
    """Test calculating success rate."""
    test_results = [
        TestResult(test_name="test_1", passed=True, execution_time=0.1),
        TestResult(test_name="test_2", passed=True, execution_time=0.1),
        TestResult(test_name="test_3", passed=False, execution_time=0.1),
    ]

    report = TestReport(
        total_tests=3,
        passed_tests=2,
        failed_tests=1,
        test_results=test_results,
        total_execution_time=0.3,
    )

    assert report.success_rate == pytest.approx(66.67, rel=0.01)

    # Test with no tests
    report_empty = TestReport(
        total_tests=0,
        passed_tests=0,
        failed_tests=0,
        test_results=[],
        total_execution_time=0.0,
    )

    assert report_empty.success_rate == 0.0


def test_all_passed():
    """Test checking if all tests passed."""
    # All tests passed
    test_results_all_passed = [
        TestResult(test_name="test_1", passed=True, execution_time=0.1),
        TestResult(test_name="test_2", passed=True, execution_time=0.1),
    ]

    report_all_passed = TestReport(
        total_tests=2,
        passed_tests=2,
        failed_tests=0,
        test_results=test_results_all_passed,
        total_execution_time=0.2,
    )

    assert report_all_passed.all_passed is True

    # Some tests failed
    test_results_with_failure = [
        TestResult(test_name="test_1", passed=True, execution_time=0.1),
        TestResult(test_name="test_2", passed=False, execution_time=0.1),
    ]

    report_with_failure = TestReport(
        total_tests=2,
        passed_tests=1,
        failed_tests=1,
        test_results=test_results_with_failure,
        total_execution_time=0.2,
    )

    assert report_with_failure.all_passed is False


def test_generate_summary():
    """Test generating test summary."""
    test_results = [
        TestResult(
            test_name="test_api_endpoint",
            test_path="tests/test_api.py",
            passed=True,
            execution_time=1.5,
            stdout="All assertions passed",
        ),
        TestResult(
            test_name="test_validation",
            test_path="tests/test_validation.py",
            passed=False,
            execution_time=0.3,
            error_message="Validation failed: expected 200, got 400",
            stderr="AssertionError",
        ),
    ]

    report = TestReport(
        total_tests=2,
        passed_tests=1,
        failed_tests=1,
        skipped_tests=0,
        test_results=test_results,
        total_execution_time=1.8,
        coverage_percentage=75.0,
        test_command="pytest tests/ -v",
        recommendation="Consider adding more edge case tests for validation",
    )

    summary = report.generate_summary()

    # Check key elements
    assert "Test Execution Summary" in summary
    assert "Total Tests: 2" in summary
    assert "Passed: 1 (50.0%)" in summary  # Success rate is shown inline
    assert "Failed: 1" in summary
    assert "Coverage: 75.0%" in summary
    assert "Execution Time: 1.8s" in summary
    assert "Failed Tests:" in summary
    assert "test_validation" in summary
    assert "Validation failed" in summary

    # Check recommendation is included
    assert "Recommendation:" in summary
    assert "Consider adding more edge case tests" in summary


def test_test_report_with_skipped():
    """Test report with skipped tests."""
    test_results = [
        TestResult(test_name="test_1", passed=True, execution_time=0.1),
        TestResult(test_name="test_2", passed=False, execution_time=0.1),
        # Skipped tests would not have results in the list typically
    ]

    report = TestReport(
        total_tests=5,
        passed_tests=2,
        failed_tests=1,
        skipped_tests=2,  # 2 tests were skipped
        test_results=test_results,
        total_execution_time=0.2,
    )

    assert report.total_tests == 5
    assert report.skipped_tests == 2
    assert len(report.test_results) == 2  # Only executed tests have results


def test_test_report_minimal():
    """Test minimal TestReport creation."""
    report = TestReport(
        total_tests=1,
        passed_tests=1,
        failed_tests=0,
        test_results=[TestResult(test_name="test_simple", passed=True, execution_time=0.01)],
        total_execution_time=0.01,
    )

    assert report.skipped_tests == 0  # Default value
    assert report.coverage_percentage is None
    assert report.recommendation is None
    assert report.test_command is None
    assert report.success_rate == 100.0
    assert report.all_passed is True
