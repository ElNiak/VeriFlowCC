"""Validation report schema for acceptance criteria verification."""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class ValidationStatus(str, Enum):
    """Status of validation."""

    PASSED = "passed"
    FAILED = "failed"
    PARTIAL = "partial"
    SKIPPED = "skipped"


class CriterionValidation(BaseModel):
    """Validation result for a single acceptance criterion."""

    criterion: str = Field(..., description="The acceptance criterion being validated")
    status: ValidationStatus = Field(..., description="Validation status")
    evidence: str | None = Field(None, description="Evidence supporting the validation")
    notes: str | None = Field(None, description="Additional notes or concerns")
    validated_by: str = Field(default="ai_agent", description="Who performed the validation")


class ValidationReport(BaseModel):
    """Complete validation report for a feature implementation."""

    feature_name: str = Field(..., description="Name of the feature being validated")
    plan_id: str | None = Field(None, description="Reference to the original plan")
    validation_timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="When validation was performed"
    )
    overall_status: ValidationStatus = Field(..., description="Overall validation status")
    criteria_validations: list[CriterionValidation] = Field(
        ..., description="Individual criterion validations"
    )
    code_quality_score: float | None = Field(None, description="Code quality score (0-100)")
    test_coverage: float | None = Field(None, description="Test coverage percentage")
    performance_metrics: dict | None = Field(None, description="Performance metrics if measured")
    security_checks: dict | None = Field(None, description="Security validation results")
    recommendations: list[str] = Field(
        default_factory=list, description="Recommendations for improvement"
    )
    blockers: list[str] = Field(default_factory=list, description="Issues blocking approval")
    validator_notes: str | None = Field(None, description="Additional notes from validator")

    @property
    def is_approved(self) -> bool:
        """Check if the feature is approved (all criteria passed)."""
        return self.overall_status == ValidationStatus.PASSED and len(self.blockers) == 0

    @property
    def criteria_pass_rate(self) -> float:
        """Calculate the percentage of criteria that passed."""
        if not self.criteria_validations:
            return 0.0
        passed = sum(1 for cv in self.criteria_validations if cv.status == ValidationStatus.PASSED)
        return (passed / len(self.criteria_validations)) * 100

    def get_failed_criteria(self) -> list[CriterionValidation]:
        """Get list of failed criteria."""
        return [cv for cv in self.criteria_validations if cv.status == ValidationStatus.FAILED]

    def generate_summary(self) -> str:
        """Generate a human-readable validation summary."""
        summary_lines = [
            f"Validation Report: {self.feature_name}",
            f"{'=' * 60}",
            f"Timestamp: {self.validation_timestamp.isoformat()}",
            f"Overall Status: {self.overall_status.value.upper()}",
            "",
            f"Acceptance Criteria ({self.criteria_pass_rate:.1f}% passed):",
        ]

        for cv in self.criteria_validations:
            status_icon = {
                ValidationStatus.PASSED: "✅",
                ValidationStatus.FAILED: "❌",
                ValidationStatus.PARTIAL: "⚠️",
                ValidationStatus.SKIPPED: "⏭️",
            }.get(cv.status, "❓")

            summary_lines.append(f"  {status_icon} {cv.criterion}")
            if cv.evidence:
                summary_lines.append(f"     Evidence: {cv.evidence[:100]}...")
            if cv.notes:
                summary_lines.append(f"     Note: {cv.notes}")

        if self.code_quality_score is not None:
            summary_lines.extend(["", f"Code Quality Score: {self.code_quality_score:.1f}/100"])

        if self.test_coverage is not None:
            summary_lines.append(f"Test Coverage: {self.test_coverage:.1f}%")

        if self.blockers:
            summary_lines.extend(["", "🚫 Blockers:"])
            for blocker in self.blockers:
                summary_lines.append(f"  - {blocker}")

        if self.recommendations:
            summary_lines.extend(["", "💡 Recommendations:"])
            for rec in self.recommendations:
                summary_lines.append(f"  - {rec}")

        if self.validator_notes:
            summary_lines.extend(["", "Notes:", self.validator_notes])

        summary_lines.extend(["", f"{'✅ APPROVED' if self.is_approved else '❌ NOT APPROVED'}"])

        return "\n".join(summary_lines)

    def to_markdown(self) -> str:
        """Generate a markdown report."""
        md_lines = [
            f"# Validation Report: {self.feature_name}",
            "",
            f"**Date:** {self.validation_timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}  ",
            f"**Status:** {self.overall_status.value.upper()}  ",
            f"**Approval:** {'✅ Approved' if self.is_approved else '❌ Not Approved'}  ",
            "",
            "## Acceptance Criteria",
            "",
            "| Criterion | Status | Evidence |",
            "|-----------|---------|----------|",
        ]

        for cv in self.criteria_validations:
            status_badge = {
                ValidationStatus.PASSED: "✅ Passed",
                ValidationStatus.FAILED: "❌ Failed",
                ValidationStatus.PARTIAL: "⚠️ Partial",
                ValidationStatus.SKIPPED: "⏭️ Skipped",
            }.get(cv.status, "Unknown")

            evidence = (
                cv.evidence[:50] + "..."
                if cv.evidence and len(cv.evidence) > 50
                else cv.evidence or "-"
            )
            md_lines.append(f"| {cv.criterion} | {status_badge} | {evidence} |")

        if self.code_quality_score is not None or self.test_coverage is not None:
            md_lines.extend(["", "## Metrics", ""])
            if self.code_quality_score is not None:
                md_lines.append(f"- **Code Quality:** {self.code_quality_score:.1f}/100")
            if self.test_coverage is not None:
                md_lines.append(f"- **Test Coverage:** {self.test_coverage:.1f}%")

        if self.blockers:
            md_lines.extend(["", "## ⚠️ Blockers", ""])
            for blocker in self.blockers:
                md_lines.append(f"- {blocker}")

        if self.recommendations:
            md_lines.extend(["", "## 💡 Recommendations", ""])
            for rec in self.recommendations:
                md_lines.append(f"- {rec}")

        return "\n".join(md_lines)
