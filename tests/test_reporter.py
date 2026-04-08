"""Unit tests for src.reporter — render_json, render_text, render_html, compute_exit_code."""
import json

import pytest

from src.models import AuditResult, Violation
from src.reporter import compute_exit_code, render_html, render_json, render_text

URL = "https://example.com"


# ---------------------------------------------------------------------------
# Fixtures / helpers
# ---------------------------------------------------------------------------

def _violation(**kwargs) -> Violation:
    defaults = dict(
        wcag_criterion="1.1.1",
        criterion_name="Non-text Content",
        level="A",
        description="Missing alt attribute.",
        element="<img src='logo.png'>",
        severity="critical",
        url=URL,
    )
    defaults.update(kwargs)
    return Violation(**defaults)


def _passed() -> AuditResult:
    return AuditResult(url=URL, passed_rules=["1.1.1", "2.4.2"])


def _failed() -> AuditResult:
    return AuditResult(url=URL, violations=[_violation()], passed_rules=["2.4.2"])


def _error() -> AuditResult:
    return AuditResult(url=URL, fetch_error="Connection refused")


# ---------------------------------------------------------------------------
# render_json
# ---------------------------------------------------------------------------

class TestRenderJson:
    def test_returns_valid_json_string(self):
        data = json.loads(render_json([_passed()]))
        assert isinstance(data, list)

    def test_passed_result_has_empty_violations(self):
        data = json.loads(render_json([_passed()]))
        assert data[0]["violations"] == []

    def test_failed_result_contains_violation_fields(self):
        data = json.loads(render_json([_failed()]))
        v = data[0]["violations"][0]
        assert v["wcag_criterion"] == "1.1.1"
        assert v["severity"] == "critical"
        assert v["url"] == URL

    def test_multiple_results_are_serialised(self):
        data = json.loads(render_json([_passed(), _failed()]))
        assert len(data) == 2

    def test_fetch_error_is_included(self):
        data = json.loads(render_json([_error()]))
        assert data[0]["fetch_error"] == "Connection refused"


# ---------------------------------------------------------------------------
# render_text
# ---------------------------------------------------------------------------

class TestRenderText:
    def test_contains_audited_url(self):
        assert URL in render_text([_passed()])

    def test_passed_page_contains_passed_keyword(self):
        text = render_text([_passed()])
        assert "Passed" in text or "passed" in text

    def test_failed_page_contains_violation_count(self):
        assert "1 violation" in render_text([_failed()])

    def test_failed_page_contains_wcag_criterion(self):
        assert "1.1.1" in render_text([_failed()])

    def test_fetch_error_page_contains_error_keyword(self):
        text = render_text([_error()])
        assert "FETCH ERROR" in text or "Connection refused" in text

    def test_multiple_results_all_urls_present(self):
        url2 = "https://other.example.com"
        r2 = AuditResult(url=url2, passed_rules=["1.1.1"])
        text = render_text([_passed(), r2])
        assert URL in text
        assert url2 in text


# ---------------------------------------------------------------------------
# compute_exit_code
# ---------------------------------------------------------------------------

class TestComputeExitCode:
    def test_returns_zero_when_all_pass(self):
        assert compute_exit_code([_passed()]) == 0

    def test_returns_one_when_violations_found(self):
        assert compute_exit_code([_failed()]) == 1

    def test_returns_one_when_fetch_error(self):
        assert compute_exit_code([_error()]) == 1

    def test_returns_one_when_mixed_results(self):
        assert compute_exit_code([_passed(), _failed()]) == 1

    def test_empty_list_returns_zero(self):
        assert compute_exit_code([]) == 0


# ---------------------------------------------------------------------------
# render_html
# ---------------------------------------------------------------------------

class TestRenderHtml:
    def test_creates_output_file(self, tmp_path):
        out = str(tmp_path / "report.html")
        render_html([_passed()], out)
        assert (tmp_path / "report.html").exists()

    def test_output_contains_audited_url(self, tmp_path):
        out = str(tmp_path / "report.html")
        render_html([_passed()], out)
        assert URL in (tmp_path / "report.html").read_text(encoding="utf-8")

    def test_output_is_html_document(self, tmp_path):
        out = str(tmp_path / "report.html")
        render_html([_passed()], out)
        content = (tmp_path / "report.html").read_text(encoding="utf-8")
        assert "<html" in content.lower()

    def test_violation_details_in_html(self, tmp_path):
        out = str(tmp_path / "report.html")
        render_html([_failed()], out)
        content = (tmp_path / "report.html").read_text(encoding="utf-8")
        assert "1.1.1" in content
