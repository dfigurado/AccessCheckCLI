"""Unit tests for src.rule_engine — auto-discovery and run_rules pipeline."""
from src.dom_parser import parse_html
from src.rule_engine import run_rules

URL = "https://example.com"

# Deliberately well-formed HTML that should satisfy all current rules.
_GOOD_HTML = (
    '<!DOCTYPE html>'
    '<html lang="en">'
    '<head><title>Accessible Page</title></head>'
    '<body>'
    '<a href="#main-content">Skip to main content</a>'
    '<nav aria-label="Main navigation"><a href="/">Main navigation</a></nav>'
    '<main id="main-content">'
    '<h1>Main Heading</h1>'
    '<h2>Sub Heading</h2>'
    '<img src="logo.png" alt="Company logo">'
    '<a href="/about">Read our accessibility guide</a>'
    '<table>'
    '<caption>Sales Data</caption>'
    '<tr><th scope="col">Product</th><th scope="col">Revenue</th></tr>'
    '<tr><td>Widget A</td><td>$500</td></tr>'
    '</table>'
    '<form>'
    '<label for="name">Full name</label>'
    '<input type="text" id="name" autocomplete="name">'
    '<label for="email">Email</label>'
    '<input type="email" id="email" autocomplete="email">'
    '</form>'
    '</main>'
    '</body></html>'
)

# HTML with multiple intentional WCAG violations.
_BAD_HTML = (
    '<!DOCTYPE html>'
    '<html>'                        # missing lang  → 3.1.1
    '<head></head>'                 # missing title → 2.4.2
    '<body>'
    '<img src="logo.png">'          # missing alt   → 1.1.1
    '<form>'
    '<input type="text" id="q">'   # no label       → 4.1.2
    '</form>'
    '</body></html>'
)


class TestRunRules:
    def test_returns_two_tuple(self):
        soup = parse_html(_GOOD_HTML)
        result = run_rules(soup, URL)
        assert isinstance(result, tuple)
        assert len(result) == 2

    def test_good_html_produces_no_violations(self):
        soup = parse_html(_GOOD_HTML)
        violations, _ = run_rules(soup, URL)
        assert violations == []

    def test_good_html_has_passed_rules(self):
        soup = parse_html(_GOOD_HTML)
        _, passed = run_rules(soup, URL)
        assert len(passed) > 0

    def test_bad_html_produces_violations(self):
        soup = parse_html(_BAD_HTML)
        violations, _ = run_rules(soup, URL)
        assert len(violations) > 0

    def test_violations_carry_correct_url(self):
        target = "https://target.example.com"
        soup = parse_html(_BAD_HTML)
        violations, _ = run_rules(soup, target)
        for v in violations:
            assert v.url == target

    def test_passed_rules_are_strings(self):
        soup = parse_html(_GOOD_HTML)
        _, passed = run_rules(soup, URL)
        assert all(isinstance(r, str) for r in passed)

    def test_violation_fields_are_populated(self):
        soup = parse_html(_BAD_HTML)
        violations, _ = run_rules(soup, URL)
        for v in violations:
            assert v.wcag_criterion
            assert v.criterion_name
            assert v.level in ("A", "AA")
            assert v.severity in ("critical", "serious", "moderate", "minor")
            assert v.description
            assert v.url == URL

    def test_rules_run_in_criterion_order(self):
        """Passed rule IDs should be lexicographically ordered (rule engine sorts them)."""
        soup = parse_html(_GOOD_HTML)
        _, passed = run_rules(soup, URL)
        assert passed == sorted(passed)

    def test_broken_rule_does_not_abort_audit(self, monkeypatch):
        """A rule whose check() raises must not crash the whole pipeline."""
        import src.rule_engine as engine
        original_discover = engine._discover_rule_modules

        class _BrokenModule:
            __name__ = "src.rules.rule_broken"
            RULE_ID = "0.0.0"

            @staticmethod
            def check(soup, url):
                raise RuntimeError("simulated rule crash")

        def patched_discover():
            return [_BrokenModule()] + original_discover()

        monkeypatch.setattr(engine, "_discover_rule_modules", patched_discover)

        import warnings
        soup = parse_html(_GOOD_HTML)
        with warnings.catch_warnings(record=True):
            violations, passed = run_rules(soup, URL)
        # Pipeline must still return results from the working rules.
        assert isinstance(violations, list)
        assert isinstance(passed, list)
