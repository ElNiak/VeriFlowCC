"""Tests for ValidationReport schema and related models."""

from verifflowcc.schemas.validation import (
    CriterionValidation,
    ValidationReport,
    ValidationStatus,
)


def test_criterion_validation_creation():
    """Test CriterionValidation model creation."""
    cv = CriterionValidation(
        criterion="API returns valid JSON",
        status=ValidationStatus.PASSED,
        evidence="All endpoints tested successfully",
        notes="Performance is good",
    )

    assert cv.criterion == "API returns valid JSON"
    assert cv.status == ValidationStatus.PASSED
    assert cv.evidence == "All endpoints tested successfully"
    assert cv.notes == "Performance is good"
    assert cv.validated_by == "ai_agent"


def test_validation_report_creation():
    """Test ValidationReport model creation."""
    criteria = [
        CriterionValidation(
            criterion="API returns valid JSON",
            status=ValidationStatus.PASSED,
            evidence="All endpoints tested",
        ),
        CriterionValidation(
            criterion="Authentication works",
            status=ValidationStatus.FAILED,
            evidence="Token validation fails",
        ),
    ]

    report = ValidationReport(
        feature_name="User Authentication API",
        plan_id="plan-001",
        overall_status=ValidationStatus.PARTIAL,
        criteria_validations=criteria,
        code_quality_score=85.5,
        test_coverage=92.3,
        recommendations=["Add more error handling", "Improve logging"],
        blockers=["Token validation must be fixed"],
    )

    assert report.feature_name == "User Authentication API"
    assert report.plan_id == "plan-001"
    assert report.overall_status == ValidationStatus.PARTIAL
    assert len(report.criteria_validations) == 2
    assert report.code_quality_score == 85.5
    assert report.test_coverage == 92.3
    assert len(report.recommendations) == 2
    assert len(report.blockers) == 1


def test_is_approved():
    """Test approval logic."""
    criteria = [
        CriterionValidation(
            criterion="All tests pass",
            status=ValidationStatus.PASSED,
        ),
    ]

    # Not approved - has blockers
    report = ValidationReport(
        feature_name="Feature 1",
        overall_status=ValidationStatus.PASSED,
        criteria_validations=criteria,
        blockers=["Critical bug found"],
    )
    assert report.is_approved is False

    # Not approved - status not passed
    report = ValidationReport(
        feature_name="Feature 2",
        overall_status=ValidationStatus.FAILED,
        criteria_validations=criteria,
        blockers=[],
    )
    assert report.is_approved is False

    # Approved - passed and no blockers
    report = ValidationReport(
        feature_name="Feature 3",
        overall_status=ValidationStatus.PASSED,
        criteria_validations=criteria,
        blockers=[],
    )
    assert report.is_approved is True


def test_criteria_pass_rate():
    """Test calculating pass rate of criteria."""
    criteria = [
        CriterionValidation(criterion="Test 1", status=ValidationStatus.PASSED),
        CriterionValidation(criterion="Test 2", status=ValidationStatus.PASSED),
        CriterionValidation(criterion="Test 3", status=ValidationStatus.FAILED),
        CriterionValidation(criterion="Test 4", status=ValidationStatus.PARTIAL),
    ]

    report = ValidationReport(
        feature_name="Feature",
        overall_status=ValidationStatus.PARTIAL,
        criteria_validations=criteria,
    )

    assert report.criteria_pass_rate == 50.0  # 2 out of 4 passed

    # Test with no criteria
    report = ValidationReport(
        feature_name="Feature",
        overall_status=ValidationStatus.PASSED,
        criteria_validations=[],
    )
    assert report.criteria_pass_rate == 0.0


def test_get_failed_criteria():
    """Test getting list of failed criteria."""
    criteria = [
        CriterionValidation(criterion="Test 1", status=ValidationStatus.PASSED),
        CriterionValidation(criterion="Test 2", status=ValidationStatus.FAILED),
        CriterionValidation(criterion="Test 3", status=ValidationStatus.FAILED),
        CriterionValidation(criterion="Test 4", status=ValidationStatus.PARTIAL),
    ]

    report = ValidationReport(
        feature_name="Feature",
        overall_status=ValidationStatus.PARTIAL,
        criteria_validations=criteria,
    )

    failed = report.get_failed_criteria()
    assert len(failed) == 2
    assert failed[0].criterion == "Test 2"
    assert failed[1].criterion == "Test 3"


def test_generate_summary():
    """Test generating human-readable summary."""
    criteria = [
        CriterionValidation(
            criterion="All tests pass",
            status=ValidationStatus.PASSED,
            evidence="100% test coverage achieved",
        ),
        CriterionValidation(
            criterion="Performance meets requirements",
            status=ValidationStatus.FAILED,
            notes="Response time exceeds 2 seconds",
        ),
    ]

    report = ValidationReport(
        feature_name="API Feature",
        overall_status=ValidationStatus.PARTIAL,
        criteria_validations=criteria,
        code_quality_score=90.0,
        test_coverage=95.5,
        blockers=["Performance issue must be resolved"],
        recommendations=["Consider caching", "Optimize database queries"],
        validator_notes="Overall good implementation, needs performance tuning",
    )

    summary = report.generate_summary()

    # Check key elements are in summary
    assert "Validation Report: API Feature" in summary
    assert "Overall Status: PARTIAL" in summary
    assert "50.0% passed" in summary
    assert "✅ All tests pass" in summary
    assert "❌ Performance meets requirements" in summary
    assert "Code Quality Score: 90.0/100" in summary
    assert "Test Coverage: 95.5%" in summary
    assert "🚫 Blockers:" in summary
    assert "Performance issue must be resolved" in summary
    assert "💡 Recommendations:" in summary
    assert "Consider caching" in summary
    assert "NOT APPROVED" in summary


def test_to_markdown():
    """Test generating markdown report."""
    criteria = [
        CriterionValidation(
            criterion="Security checks pass",
            status=ValidationStatus.PASSED,
            evidence="No vulnerabilities found in security scan",
        ),
    ]

    report = ValidationReport(
        feature_name="Security Feature",
        overall_status=ValidationStatus.PASSED,
        criteria_validations=criteria,
        code_quality_score=95.0,
        test_coverage=98.0,
    )

    markdown = report.to_markdown()

    # Check markdown structure
    assert "# Validation Report: Security Feature" in markdown
    assert "**Status:** PASSED" in markdown
    assert "**Approval:** ✅ Approved" in markdown
    assert "## Acceptance Criteria" in markdown
    assert "| Criterion | Status | Evidence |" in markdown
    assert "| Security checks pass | ✅ Passed |" in markdown
    assert "## Metrics" in markdown
    assert "**Code Quality:** 95.0/100" in markdown
    assert "**Test Coverage:** 98.0%" in markdown
