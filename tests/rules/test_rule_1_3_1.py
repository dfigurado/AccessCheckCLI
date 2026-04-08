"""Tests for WCAG 1.3.1 — Info and Relationships (data tables)."""
from src.dom_parser import parse_html
from src.rules.rule_1_3_1_tables import check

URL = "https://example.com"


def soup(html):
    return parse_html(html)


def _table(inner: str, attrs: str = "") -> str:
    return f"<html><body><table {attrs}>{inner}</table></body></html>"


class TestTables:
    def test_no_tables_produces_no_violations(self):
        s = soup("<html><body><p>No tables here</p></body></html>")
        assert check(s, URL) == []

    def test_layout_table_with_role_presentation_is_skipped(self):
        s = soup('<html><body><table role="presentation"><tr><td>Cell</td></tr></table></body></html>')
        assert check(s, URL) == []

    def test_layout_table_with_role_none_is_skipped(self):
        s = soup('<html><body><table role="none"><tr><td>Cell</td></tr></table></body></html>')
        assert check(s, URL) == []

    def test_well_formed_table_with_th_caption_passes(self):
        html = (
            "<html><body><table>"
            "<caption>Sales Data</caption>"
            "<tr><th scope='col'>Product</th><th scope='col'>Revenue</th></tr>"
            "<tr><td>Widget A</td><td>$500</td></tr>"
            "</table></body></html>"
        )
        s = soup(html)
        assert check(s, URL) == []

    def test_table_without_th_has_critical_violation(self):
        html = (
            "<html><body><table>"
            "<caption>Data</caption>"
            "<tr><td>Name</td><td>Value</td></tr>"
            "<tr><td>Item A</td><td>10</td></tr>"
            "</table></body></html>"
        )
        s = soup(html)
        violations = check(s, URL)
        severities = [v.severity for v in violations]
        assert "critical" in severities

    def test_table_without_th_criterion_is_1_3_1(self):
        html = (
            "<html><body><table><caption>D</caption>"
            "<tr><td>A</td><td>B</td></tr></table></body></html>"
        )
        s = soup(html)
        violations = check(s, URL)
        assert all(v.wcag_criterion == "1.3.1" for v in violations)

    def test_empty_th_has_serious_violation(self):
        html = (
            "<html><body><table>"
            "<caption>Data</caption>"
            "<tr><th scope='col'></th><th scope='col'>Value</th></tr>"
            "<tr><td>Item A</td><td>10</td></tr>"
            "</table></body></html>"
        )
        s = soup(html)
        violations = check(s, URL)
        assert any(v.severity == "serious" for v in violations)

    def test_table_without_caption_has_moderate_violation(self):
        html = (
            "<html><body><table>"
            "<tr><th scope='col'>Name</th><th scope='col'>Value</th></tr>"
            "<tr><td>Item A</td><td>10</td></tr>"
            "</table></body></html>"
        )
        s = soup(html)
        violations = check(s, URL)
        assert any(v.severity == "moderate" for v in violations)

    def test_table_with_aria_label_instead_of_caption_passes_caption_check(self):
        html = (
            "<html><body>"
            '<table aria-label="Revenue summary">'
            "<tr><th scope='col'>Name</th><th scope='col'>Value</th></tr>"
            "<tr><td>Item A</td><td>10</td></tr>"
            "</table></body></html>"
        )
        s = soup(html)
        violations = check(s, URL)
        assert not any(v.severity == "moderate" for v in violations)

    def test_violation_url_matches_audited_url(self):
        html = (
            "<html><body><table>"
            "<tr><td>Cell</td></tr>"
            "</table></body></html>"
        )
        s = soup(html)
        violations = check(s, URL)
        assert all(v.url == URL for v in violations)
