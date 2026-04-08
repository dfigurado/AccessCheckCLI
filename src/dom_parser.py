"""DOM parsing utilities.

Wraps BeautifulSoup4 (with the ``lxml`` back-end for speed) and provides
element-extraction helpers consumed by individual WCAG rule modules.

Rule authors should import helpers from here rather than calling BeautifulSoup
directly, so that the underlying parser can be changed in one place if needed.
"""

from __future__ import annotations
from bs4 import BeautifulSoup, Tag

# ---------------------------------------------------------------------------
# Core parser
# ---------------------------------------------------------------------------


def parse_html(html: str) -> BeautifulSoup:
    """Parse *html* into a :class:`~bs4.BeautifulSoup` document.

    Uses the ``lxml`` parser for performance.  Falls back to ``html.parser``
    (Python stdlib) if ``lxml`` is not installed, so the tool degrades
    gracefully rather than crashing.
    """
    try:
        return BeautifulSoup(html, "lxml")
    except Exception:  # noqa: BLE001
        return BeautifulSoup(html, "html.parser")


# ---------------------------------------------------------------------------
# Element extraction helpers
# ---------------------------------------------------------------------------


def get_images(soup: BeautifulSoup) -> list[Tag]:
    """Return all ``<img>`` elements."""
    return [t for t in soup.find_all("img") if isinstance(t, Tag)]


def get_form_inputs(soup: BeautifulSoup) -> list[Tag]:
    """Return all labelable form controls: ``<input>``, ``<select>``, ``<textarea>``."""
    return [
        t
        for t in soup.find_all(["input", "select", "textarea"])
        if isinstance(t, Tag)
    ]


def get_links(soup: BeautifulSoup) -> list[Tag]:
    """Return all ``<a>`` elements."""
    return [t for t in soup.find_all("a") if isinstance(t, Tag)]


def get_headings(soup: BeautifulSoup) -> list[Tag]:
    """Return all heading elements h1–h6 in document order."""
    return [
        t
        for t in soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6"])
        if isinstance(t, Tag)
    ]


def get_buttons(soup: BeautifulSoup) -> list[Tag]:
    """Return all ``<button>`` elements and ``<input type='button|submit|reset'>``."""
    buttons: list[Tag] = [t for t in soup.find_all("button") if isinstance(t, Tag)]
    for inp in get_form_inputs(soup):
        if inp.get("type", "").lower() in {"button", "submit", "reset", "image"}:
            buttons.append(inp)
    return buttons


def get_page_title(soup: BeautifulSoup) -> str | None:
    """Return the stripped text of the ``<title>`` element, or ``None`` if absent/empty."""
    title_tag = soup.find("title")
    if title_tag and title_tag.string:
        text = title_tag.string.strip()
        return text if text else None
    return None


def get_lang_attr(soup: BeautifulSoup) -> str | None:
    """Return the ``lang`` attribute of the ``<html>`` element, or ``None``."""
    html_tag = soup.find("html")
    if html_tag and isinstance(html_tag, Tag):
        lang = html_tag.get("lang", "")
        return str(lang).strip() if lang else None
    return None


def get_frames(soup: BeautifulSoup) -> list[Tag]:
    """Return all ``<iframe>`` and ``<frame>`` elements."""
    return [
        t for t in soup.find_all(["iframe", "frame"]) if isinstance(t, Tag)
    ]