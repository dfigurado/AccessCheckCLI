"""Tests for WCAG 3.1.1 — Language of Page."""
from src.dom_parser import parse_html
from src.rules.rule_3_1_1_language import check

URL = "https://example.com"


def soup(html):
    return parse_html(html)


class TestLanguageOfPage:
    def test_html_with_lang_en_passes(self):
        s = soup('<html lang="en"><head></head><body></body></html>')
        assert check(s, URL) == []

    def test_html_with_lang_fr_passes(self):
        s = soup('<html lang="fr"><head></head><body></body></html>')
        assert check(s, URL) == []

    def test_html_with_lang_zh_passes(self):
        s = soup('<html lang="zh-Hans"><head></head><body></body></html>')
        assert check(s, URL) == []

    def test_html_without_lang_has_violation(self):
        s = soup("<html><head></head><body></body></html>")
        violations = check(s, URL)
        assert len(violations) == 1

    def test_html_with_empty_lang_has_violation(self):
        s = soup('<html lang=""><head></head><body></body></html>')
        violations = check(s, URL)
        assert len(violations) == 1

    def test_violation_severity_is_serious(self):
        s = soup("<html><head></head><body></body></html>")
        violations = check(s, URL)
        assert violations[0].severity == "serious"

    def test_violation_criterion_is_3_1_1(self):
        s = soup("<html><head></head><body></body></html>")
        violations = check(s, URL)
        assert violations[0].wcag_criterion == "3.1.1"

    def test_violation_level_is_A(self):
        s = soup("<html><head></head><body></body></html>")
        violations = check(s, URL)
        assert violations[0].level == "A"

    def test_violation_url_matches_audited_url(self):
        s = soup("<html><head></head><body></body></html>")
        violations = check(s, URL)
        assert violations[0].url == URL

    def test_violation_description_mentions_lang(self):
        s = soup("<html><head></head><body></body></html>")
        violations = check(s, URL)
        assert "lang" in violations[0].description.lower()
