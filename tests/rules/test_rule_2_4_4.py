"""Tests for WCAG 2.4.4 — Link Purpose (In Context)."""
from src.dom_parser import parse_html
from src.rules.rule_2_4_4_link_purpose import check

URL = "https://example.com"


def soup(html):
    return parse_html(html)


class TestLinkPurpose:
    def test_descriptive_link_text_passes(self):
        s = soup('<html><body><a href="/guide">Read our accessibility guide</a></body></html>')
        assert check(s, URL) == []

    def test_link_without_href_is_skipped(self):
        s = soup('<html><body><a>No destination</a></body></html>')
        assert check(s, URL) == []

    def test_empty_link_text_is_critical_violation(self):
        s = soup('<html><body><a href="/page"></a></body></html>')
        violations = check(s, URL)
        assert len(violations) == 1
        assert violations[0].severity == "critical"

    def test_click_here_is_serious_violation(self):
        s = soup('<html><body><a href="/page">click here</a></body></html>')
        violations = check(s, URL)
        assert len(violations) == 1
        assert violations[0].severity == "serious"

    def test_read_more_is_serious_violation(self):
        s = soup('<html><body><a href="/page">read more</a></body></html>')
        violations = check(s, URL)
        assert len(violations) == 1
        assert violations[0].severity == "serious"

    def test_here_is_serious_violation(self):
        s = soup('<html><body><a href="/page">here</a></body></html>')
        violations = check(s, URL)
        assert len(violations) == 1
        assert violations[0].severity == "serious"

    def test_hash_only_href_is_moderate_violation(self):
        s = soup('<html><body><a href="#">Go somewhere</a></body></html>')
        violations = check(s, URL)
        assert len(violations) == 1
        assert violations[0].severity == "moderate"

    def test_aria_label_resolves_empty_text(self):
        s = soup('<html><body><a href="/page" aria-label="Download our annual report"></a></body></html>')
        assert check(s, URL) == []

    def test_image_link_with_alt_passes(self):
        # "Home" is in _AMBIGUOUS_TEXT; use a descriptive alt instead.
        s = soup('<html><body><a href="/home"><img src="logo.png" alt="Return to homepage"></a></body></html>')
        assert check(s, URL) == []

    def test_image_link_without_alt_is_critical(self):
        s = soup('<html><body><a href="/home"><img src="logo.png" alt=""></a></body></html>')
        violations = check(s, URL)
        assert any(v.severity == "critical" for v in violations)

    def test_violation_criterion_is_2_4_4(self):
        s = soup('<html><body><a href="/page"></a></body></html>')
        violations = check(s, URL)
        assert violations[0].wcag_criterion == "2.4.4"

    def test_violation_url_matches_audited_url(self):
        s = soup('<html><body><a href="/page"></a></body></html>')
        violations = check(s, URL)
        assert violations[0].url == URL
