"""Tests for WCAG 2.4.1 — Bypass Blocks."""
from src.dom_parser import parse_html
from src.rules.rule_2_4_1_bypass_blocks import (
    _has_main_landmark,
    _has_skip_nav_link,
    check,
)

URL = "https://example.com"


def soup(html):
    return parse_html(html)


class TestHasMainLandmark:
    def test_main_element_detected(self):
        s = soup("<html><body><main><p>Content</p></main></body></html>")
        assert _has_main_landmark(s) is True

    def test_role_main_detected(self):
        s = soup('<html><body><div role="main"><p>Content</p></div></body></html>')
        assert _has_main_landmark(s) is True

    def test_no_main_returns_false(self):
        s = soup("<html><body><p>No main landmark</p></body></html>")
        assert _has_main_landmark(s) is False


class TestHasSkipNavLink:
    def test_skip_link_with_valid_target_detected(self):
        s = soup(
            '<html><body>'
            '<a href="#main-content">Skip to main content</a>'
            '<div id="main-content"><p>Content</p></div>'
            '</body></html>'
        )
        assert _has_skip_nav_link(s) is True

    def test_skip_link_without_matching_target_not_detected(self):
        s = soup(
            '<html><body>'
            '<a href="#missing-id">Skip to main content</a>'
            '</body></html>'
        )
        assert _has_skip_nav_link(s) is False

    def test_no_skip_link_returns_false(self):
        s = soup('<html><body><a href="/about">About</a></body></html>')
        assert _has_skip_nav_link(s) is False


class TestBypassBlocks:
    def test_page_with_main_has_no_serious_violation(self):
        s = soup(
            '<html><body>'
            '<main><h1>Content</h1></main>'
            '</body></html>'
        )
        violations = check(s, URL)
        serious = [v for v in violations if v.severity == "serious"]
        assert serious == []

    def test_page_without_main_has_serious_violation(self):
        s = soup("<html><body><p>No landmark here</p></body></html>")
        violations = check(s, URL)
        assert any(v.severity == "serious" for v in violations)

    def test_page_without_main_and_skip_nav_has_moderate_violation(self):
        s = soup("<html><body><p>No bypass mechanism</p></body></html>")
        violations = check(s, URL)
        assert any(v.severity == "moderate" for v in violations)

    def test_page_without_main_but_with_skip_nav_has_no_moderate_violation(self):
        s = soup(
            '<html><body>'
            '<a href="#content">Skip to main content</a>'
            '<p id="content">Content here</p>'
            '</body></html>'
        )
        violations = check(s, URL)
        assert not any(v.severity == "moderate" for v in violations)

    def test_three_unlabelled_navs_produce_minor_violations(self):
        s = soup(
            '<html><body><main>'
            '<nav><a href="/">Home</a></nav>'
            '<nav><a href="/about">About</a></nav>'
            '<nav><a href="/contact">Contact</a></nav>'
            '</main></body></html>'
        )
        violations = check(s, URL)
        assert any(v.severity == "minor" for v in violations)

    def test_three_labelled_navs_have_no_minor_violations(self):
        s = soup(
            '<html><body><main>'
            '<nav aria-label="Primary"><a href="/">Home</a></nav>'
            '<nav aria-label="Secondary"><a href="/about">About</a></nav>'
            '<nav aria-label="Footer"><a href="/contact">Contact</a></nav>'
            '</main></body></html>'
        )
        violations = check(s, URL)
        assert not any(v.severity == "minor" for v in violations)

    def test_all_violations_have_correct_criterion(self):
        s = soup("<html><body><p>No bypass</p></body></html>")
        violations = check(s, URL)
        assert all(v.wcag_criterion == "2.4.1" for v in violations)

    def test_violation_url_matches_audited_url(self):
        s = soup("<html><body><p>No bypass</p></body></html>")
        violations = check(s, URL)
        assert all(v.url == URL for v in violations)
