"""Unit tests for src.dom_parser helper functions."""
import pytest
from bs4 import BeautifulSoup
from src.dom_parser import (
    parse_html,
    get_images,
    get_form_inputs,
    get_links,
    get_headings,
    get_buttons,
    get_page_title,
    get_lang_attr,
    get_frames,
)


def soup(html: str) -> BeautifulSoup:
    return parse_html(html)


# ---------------------------------------------------------------------------
# parse_html
# ---------------------------------------------------------------------------

class TestParseHtml:
    def test_returns_beautifulsoup_instance(self):
        result = parse_html("<html><body></body></html>")
        assert isinstance(result, BeautifulSoup)

    def test_empty_string_does_not_raise(self):
        result = parse_html("")
        assert result is not None

    def test_parses_nested_elements(self):
        result = parse_html("<html><body><p>Hello</p></body></html>")
        assert result.find("p").get_text() == "Hello"


# ---------------------------------------------------------------------------
# get_images
# ---------------------------------------------------------------------------

class TestGetImages:
    def test_finds_multiple_images(self):
        s = soup('<img src="a.png"><img src="b.png">')
        assert len(get_images(s)) == 2

    def test_returns_empty_when_no_images(self):
        s = soup("<p>No images here</p>")
        assert get_images(s) == []

    def test_returns_tags_not_strings(self):
        s = soup('<img src="a.png">')
        imgs = get_images(s)
        from bs4 import Tag
        assert all(isinstance(i, Tag) for i in imgs)


# ---------------------------------------------------------------------------
# get_form_inputs
# ---------------------------------------------------------------------------

class TestGetFormInputs:
    def test_finds_input_select_textarea(self):
        s = soup('<input type="text"><select><option>A</option></select><textarea></textarea>')
        assert len(get_form_inputs(s)) == 3

    def test_returns_empty_when_no_inputs(self):
        s = soup("<p>No form here</p>")
        assert get_form_inputs(s) == []


# ---------------------------------------------------------------------------
# get_links
# ---------------------------------------------------------------------------

class TestGetLinks:
    def test_finds_anchor_elements(self):
        s = soup('<a href="/">Home</a><a href="/about">About</a>')
        assert len(get_links(s)) == 2

    def test_returns_empty_when_no_links(self):
        s = soup("<p>No links</p>")
        assert get_links(s) == []


# ---------------------------------------------------------------------------
# get_headings
# ---------------------------------------------------------------------------

class TestGetHeadings:
    def test_finds_all_heading_levels(self):
        s = soup("<h1>One</h1><h2>Two</h2><h3>Three</h3><h4>Four</h4>")
        assert len(get_headings(s)) == 4

    def test_returns_empty_when_no_headings(self):
        s = soup("<p>No headings</p>")
        assert get_headings(s) == []

    def test_preserves_document_order(self):
        s = soup("<h2>First</h2><h1>Second</h1>")
        headings = get_headings(s)
        assert headings[0].name == "h2"
        assert headings[1].name == "h1"


# ---------------------------------------------------------------------------
# get_page_title
# ---------------------------------------------------------------------------

class TestGetPageTitle:
    def test_returns_title_text(self):
        s = soup("<html><head><title>My Page</title></head></html>")
        assert get_page_title(s) == "My Page"

    def test_strips_whitespace(self):
        s = soup("<html><head><title>  Padded Title  </title></head></html>")
        assert get_page_title(s) == "Padded Title"

    def test_missing_title_returns_none(self):
        s = soup("<html><head></head></html>")
        assert get_page_title(s) is None

    def test_empty_title_returns_none(self):
        s = soup("<html><head><title>   </title></head></html>")
        assert get_page_title(s) is None


# ---------------------------------------------------------------------------
# get_lang_attr
# ---------------------------------------------------------------------------

class TestGetLangAttr:
    def test_returns_lang_value(self):
        s = soup('<html lang="en"><body></body></html>')
        assert get_lang_attr(s) == "en"

    def test_returns_none_when_lang_missing(self):
        s = soup("<html><body></body></html>")
        assert get_lang_attr(s) is None

    def test_returns_none_when_lang_empty(self):
        s = soup('<html lang=""><body></body></html>')
        assert get_lang_attr(s) is None


# ---------------------------------------------------------------------------
# get_frames
# ---------------------------------------------------------------------------

class TestGetFrames:
    def test_finds_iframes(self):
        s = soup('<iframe src="a.html"></iframe><iframe src="b.html"></iframe>')
        assert len(get_frames(s)) == 2

    def test_returns_empty_when_no_frames(self):
        s = soup("<p>No frames</p>")
        assert get_frames(s) == []
