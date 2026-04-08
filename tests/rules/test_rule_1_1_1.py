"""Tests for WCAG 1.1.1 — Non-text Content (alt text)."""
from src.dom_parser import parse_html
from src.rules.rule_1_1_1_alt_text import check

URL = "https://example.com"


def soup(html):
    return parse_html(html)


class TestAltText:
    def test_no_images_produces_no_violations(self):
        s = soup("<html><body><p>No images here</p></body></html>")
        assert check(s, URL) == []

    def test_image_with_descriptive_alt_passes(self):
        s = soup('<html><body><img src="logo.png" alt="Company logo"></body></html>')
        assert check(s, URL) == []

    def test_decorative_image_with_empty_alt_passes(self):
        s = soup('<html><body><img src="decor.png" alt=""></body></html>')
        assert check(s, URL) == []

    def test_image_missing_alt_is_critical_violation(self):
        s = soup('<html><body><img src="logo.png"></body></html>')
        violations = check(s, URL)
        assert len(violations) == 1
        assert violations[0].severity == "critical"

    def test_missing_alt_violation_has_correct_criterion(self):
        s = soup('<html><body><img src="logo.png"></body></html>')
        violations = check(s, URL)
        assert violations[0].wcag_criterion == "1.1.1"

    def test_role_img_with_empty_alt_is_serious_violation(self):
        s = soup('<html><body><img src="chart.png" role="img" alt=""></body></html>')
        violations = check(s, URL)
        assert len(violations) == 1
        assert violations[0].severity == "serious"

    def test_role_img_with_descriptive_alt_passes(self):
        s = soup('<html><body><img src="chart.png" role="img" alt="Q1 sales chart"></body></html>')
        assert check(s, URL) == []

    def test_multiple_images_without_alt_produce_multiple_violations(self):
        s = soup('<html><body><img src="a.png"><img src="b.png"></body></html>')
        violations = check(s, URL)
        assert len(violations) == 2

    def test_violation_url_matches_audited_url(self):
        s = soup('<html><body><img src="logo.png"></body></html>')
        violations = check(s, URL)
        assert violations[0].url == URL

    def test_violation_element_contains_img_tag(self):
        s = soup('<html><body><img src="logo.png"></body></html>')
        violations = check(s, URL)
        assert "img" in violations[0].element

    def test_mixed_images_only_flags_non_compliant(self):
        s = soup(
            '<html><body>'
            '<img src="good.png" alt="Good image">'
            '<img src="bad.png">'
            '</body></html>'
        )
        violations = check(s, URL)
        assert len(violations) == 1
        assert violations[0].severity == "critical"
