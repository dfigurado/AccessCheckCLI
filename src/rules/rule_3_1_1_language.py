"""WCAG 2.1 — Success Criterion 3.1.1: Language of Page (Level A).

The default human language of each web page must be programmatically
determined.  Screen readers use the ``lang`` attribute on the ``<html>``
element to select the correct voice, pronunciation rules, and character
rendering for speech synthesis.

Checks:
* ``<html>`` element missing ``lang`` attribute entirely    →  **serious**
* ``<html lang="">`` — present but blank                    →  **serious**
"""

from __future__ import annotations
from bs4 import BeautifulSoup, Tag
from src.models import Violation

# ---------------------------------------------------------------------------
# Rule metadata
# ---------------------------------------------------------------------------

RULE_ID = "3.1.1"
CRITERION_NAME = "Language of Page"
LEVEL = "A"
SEVERITY = "serious"


# ---------------------------------------------------------------------------
# Rule implementation
# ---------------------------------------------------------------------------


def check(soup: BeautifulSoup, url: str) -> list[Violation]:
    """Return a violation when the ``<html>`` element lacks a valid ``lang`` attribute."""
    html_tag = soup.find("html")

    if not html_tag or not isinstance(html_tag, Tag):
        # Malformed document — no <html> at all.
        return [
            Violation(
                wcag_criterion=RULE_ID,
                criterion_name=CRITERION_NAME,
                level=LEVEL,
                description=(
                    "Document has no <html> element; the page language cannot be determined. "
                    "Assistive technologies need a valid lang attribute for correct speech synthesis."
                ),
                element="(no <html> element found)",
                severity=SEVERITY,
                url=url,
            )
        ]

    lang = str(html_tag.get("lang", "")).strip()

    if not lang:
        # Grab a short snippet of the opening tag for the report.
        tag_str = str(html_tag)[:120]
        return [
            Violation(
                wcag_criterion=RULE_ID,
                criterion_name=CRITERION_NAME,
                level=LEVEL,
                description=(
                    "The <html> element is missing a lang attribute or the value is empty. "
                    "Add lang=\"en\" (or the appropriate BCP 47 language tag) so that "
                    "screen readers can use the correct speech synthesis engine."
                ),
                element=tag_str + ("…" if len(str(html_tag)) > 120 else ""),
                severity=SEVERITY,
                url=url,
            )
        ]

    return []

