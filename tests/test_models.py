"""Unit tests for src.models — Violation and AuditResult dataclasses."""
import pytest
from src.models import Violation, AuditResult


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_violation(**kwargs) -> Violation:
    defaults = dict(
        wcag_criterion="1.1.1",
        criterion_name="Non-text Content",
        level="A",
        description="Missing alt text.",
        element="<img src='logo.png'>",
        severity="critical",
        url="https://example.com",
    )
    defaults.update(kwargs)
    return Violation(**defaults)


# ---------------------------------------------------------------------------
# Violation
# ---------------------------------------------------------------------------

class TestViolation:
    def test_fields_are_stored(self):
        v = _make_violation()
        assert v.wcag_criterion == "1.1.1"
        assert v.criterion_name == "Non-text Content"
        assert v.level == "A"
        assert v.description == "Missing alt text."
        assert v.element == "<img src='logo.png'>"
        assert v.severity == "critical"
        assert v.url == "https://example.com"

    def test_all_severity_levels_accepted(self):
        for severity in ("critical", "serious", "moderate", "minor"):
            v = _make_violation(severity=severity)
            assert v.severity == severity

    def test_level_aa_accepted(self):
        v = _make_violation(level="AA")
        assert v.level == "AA"

    def test_different_criteria(self):
        for criterion in ("1.1.1", "2.4.2", "3.1.1", "4.1.2"):
            v = _make_violation(wcag_criterion=criterion)
            assert v.wcag_criterion == criterion


# ---------------------------------------------------------------------------
# AuditResult
# ---------------------------------------------------------------------------

class TestAuditResult:
    def test_passed_true_when_no_violations_and_no_error(self):
        result = AuditResult(url="https://example.com", passed_rules=["1.1.1"])
        assert result.passed is True

    def test_passed_false_when_violations_present(self):
        result = AuditResult(
            url="https://example.com",
            violations=[_make_violation()],
        )
        assert result.passed is False

    def test_passed_false_when_fetch_error_set(self):
        result = AuditResult(url="https://example.com", fetch_error="Connection refused")
        assert result.passed is False

    def test_passed_false_when_both_violations_and_error(self):
        result = AuditResult(
            url="https://example.com",
            violations=[_make_violation()],
            fetch_error="timeout",
        )
        assert result.passed is False

    def test_total_violations_counts_correctly(self):
        result = AuditResult(
            url="https://example.com",
            violations=[_make_violation(), _make_violation()],
        )
        assert result.total_violations == 2

    def test_total_violations_zero_when_empty(self):
        result = AuditResult(url="https://example.com")
        assert result.total_violations == 0

    def test_default_violations_is_empty_list(self):
        result = AuditResult(url="https://example.com")
        assert result.violations == []

    def test_default_passed_rules_is_empty_list(self):
        result = AuditResult(url="https://example.com")
        assert result.passed_rules == []

    def test_default_fetch_error_is_none(self):
        result = AuditResult(url="https://example.com")
        assert result.fetch_error is None

    def test_url_is_stored(self):
        result = AuditResult(url="https://my-site.example.com")
        assert result.url == "https://my-site.example.com"

    def test_passed_rules_list_is_stored(self):
        result = AuditResult(url="https://example.com", passed_rules=["1.1.1", "2.4.2"])
        assert result.passed_rules == ["1.1.1", "2.4.2"]
