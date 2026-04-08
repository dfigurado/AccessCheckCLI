"""Tests for WCAG 2.4.2 — Page Titled."""
from src.dom_parser import parse_html
from src.rules.rule_2_4_2_page_titled import check

URL = "https://example.com"


def soup(html):
    return parse_html(html)


class TestPageTitled:
    def test_page_with_descriptive_title_passes(self):
        s = soup("<html><head><title>Accessibility Guide</title></head><body></body></html>")
        assert check(s, URL) == []

    def test_page_without_title_element_has_violation(self):
        s = soup("<html><head></head><body></body></html>")
        violations = check(s, URL)
        assert len(violations) == 1

    def test_page_with_empty_title_has_violation(self):
        s = soup("<html><head><title></title></head><body></body></html>")
        violations = check(s, URL)
        assert len(violations) == 1

    def test_page_with_whitespace_only_title_has_violation(self):
        s = soup("<html><head><title>    </title></head><body></body></html>")
        violations = check(s, URL)
        assert len(violations) == 1

    def test_violation_severity_is_serious(self):
        s = soup("<html><head></head><body></body></html>")
        violations = check(s, URL)
        assert violations[0].severity == "serious"

    def test_violation_criterion_is_2_4_2(self):
        s = soup("<html><head></head><body></body></html>")
        violations = check(s, URL)
        assert violations[0].wcag_criterion == "2.4.2"

    def test_violation_level_is_A(self):
        s = soup("<html><head></head><body></body></html>")
        violations = check(s, URL)
        assert violations[0].level == "A"

    def test_violation_url_matches_audited_url(self):
        s = soup("<html><head></head><body></body></html>")
        violations = check(s, URL)
        assert violations[0].url == URL

    def test_violation_description_mentions_title(self):
        s = soup("<html><head></head><body></body></html>")
        violations = check(s, URL)
        assert "title" in violations[0].description.lower()
