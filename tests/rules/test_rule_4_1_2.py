"""Tests for WCAG 4.1.2 — Name, Role, Value (form labels)."""
from src.dom_parser import parse_html
from src.rules.rule_4_1_2_form_labels import check

URL = "https://example.com"


def soup(html):
    return parse_html(html)


class TestFormLabels:
    def test_input_with_explicit_label_passes(self):
        s = soup(
            '<html><body><form>'
            '<label for="name">Full name</label>'
            '<input type="text" id="name">'
            '</form></body></html>'
        )
        assert check(s, URL) == []

    def test_input_with_aria_label_passes(self):
        s = soup('<html><body><input type="text" aria-label="Search query"></body></html>')
        assert check(s, URL) == []

    def test_input_with_aria_labelledby_passes(self):
        s = soup(
            '<html><body>'
            '<span id="lbl">Full name</span>'
            '<input type="text" aria-labelledby="lbl">'
            '</body></html>'
        )
        assert check(s, URL) == []

    def test_input_nested_in_implicit_label_passes(self):
        s = soup('<html><body><label>Name <input type="text"></label></body></html>')
        assert check(s, URL) == []

    def test_input_with_title_passes(self):
        s = soup('<html><body><input type="text" title="Your full name"></body></html>')
        assert check(s, URL) == []

    def test_unlabelled_text_input_has_violation(self):
        s = soup('<html><body><input type="text" id="q"></body></html>')
        violations = check(s, URL)
        assert len(violations) == 1

    def test_violation_criterion_is_4_1_2(self):
        s = soup('<html><body><input type="text" id="q"></body></html>')
        violations = check(s, URL)
        assert violations[0].wcag_criterion == "4.1.2"

    def test_violation_severity_is_critical(self):
        s = soup('<html><body><input type="text" id="q"></body></html>')
        violations = check(s, URL)
        assert violations[0].severity == "critical"

    def test_hidden_input_is_skipped(self):
        s = soup('<html><body><input type="hidden" name="csrf"></body></html>')
        assert check(s, URL) == []

    def test_submit_input_is_skipped(self):
        s = soup('<html><body><input type="submit" value="Send"></body></html>')
        assert check(s, URL) == []

    def test_button_input_is_skipped(self):
        s = soup('<html><body><input type="button" value="Click me"></body></html>')
        assert check(s, URL) == []

    def test_unlabelled_select_has_violation(self):
        s = soup(
            '<html><body><select id="country">'
            '<option>US</option>'
            '</select></body></html>'
        )
        violations = check(s, URL)
        assert len(violations) == 1

    def test_unlabelled_textarea_has_violation(self):
        s = soup('<html><body><textarea id="bio"></textarea></body></html>')
        violations = check(s, URL)
        assert len(violations) == 1

    def test_violation_url_matches_audited_url(self):
        s = soup('<html><body><input type="text" id="q"></body></html>')
        violations = check(s, URL)
        assert violations[0].url == URL
