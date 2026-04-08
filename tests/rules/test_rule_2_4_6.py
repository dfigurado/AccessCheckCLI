"""Tests for WCAG 2.4.6 — Headings and Labels (heading hierarchy)."""
from src.dom_parser import parse_html
from src.rules.rule_2_4_6_heading_hierarchy import check

URL = "https://example.com"


def soup(html):
    return parse_html(html)


class TestHeadingHierarchy:
    def test_no_headings_produces_violation(self):
        s = soup("<html><body><p>No headings at all</p></body></html>")
        violations = check(s, URL)
        assert len(violations) >= 1

    def test_proper_sequential_hierarchy_passes(self):
        s = soup("<html><body><h1>Title</h1><h2>Section</h2><h3>Sub-section</h3></body></html>")
        assert check(s, URL) == []

    def test_no_h1_produces_violation(self):
        s = soup("<html><body><h2>Subtitle</h2><h3>Sub</h3></body></html>")
        violations = check(s, URL)
        assert any(v.wcag_criterion == "2.4.6" for v in violations)

    def test_multiple_h1_produces_violation_for_extras(self):
        s = soup("<html><body><h1>First</h1><h2>Mid</h2><h1>Second</h1></body></html>")
        violations = check(s, URL)
        assert len(violations) >= 1

    def test_skipped_heading_level_h1_to_h3_has_violation(self):
        s = soup("<html><body><h1>Title</h1><h3>Skipped h2</h3></body></html>")
        violations = check(s, URL)
        assert any("jumps" in v.description.lower() or "skipping" in v.description.lower()
                   for v in violations)

    def test_skipped_heading_level_h2_to_h5_has_violation(self):
        s = soup("<html><body><h1>Title</h1><h2>Section</h2><h5>Deep skip</h5></body></html>")
        violations = check(s, URL)
        assert any("jumps" in v.description.lower() or "skipping" in v.description.lower()
                   for v in violations)

    def test_closing_heading_level_is_valid(self):
        # h1 → h2 → h3 → h2  (closing back to h2 is fine)
        s = soup("<html><body><h1>A</h1><h2>B</h2><h3>C</h3><h2>D</h2></body></html>")
        assert check(s, URL) == []

    def test_empty_heading_produces_violation(self):
        s = soup("<html><body><h1></h1></body></html>")
        violations = check(s, URL)
        assert len(violations) >= 1

    def test_empty_heading_violation_mentions_empty(self):
        s = soup("<html><body><h1></h1></body></html>")
        violations = check(s, URL)
        assert any("empty" in v.description.lower() for v in violations)

    def test_all_violations_have_correct_criterion(self):
        s = soup("<html><body><h2>No h1</h2><h5>Skipped levels</h5></body></html>")
        violations = check(s, URL)
        assert all(v.wcag_criterion == "2.4.6" for v in violations)

    def test_violation_url_matches_audited_url(self):
        s = soup("<html><body><p>No headings</p></body></html>")
        violations = check(s, URL)
        assert all(v.url == URL for v in violations)

    def test_heading_with_aria_label_is_not_empty(self):
        s = soup('<html><body><h1 aria-label="Page title"></h1></body></html>')
        violations = check(s, URL)
        # aria-label provides accessible name so it should not flag as empty
        empty_violations = [v for v in violations if "empty" in v.description.lower()]
        assert empty_violations == []
