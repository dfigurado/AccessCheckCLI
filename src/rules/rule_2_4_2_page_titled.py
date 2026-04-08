"""WCAG 2.1 — Success Criterion 2.4.2: Page Titled (Level A).

Web pages must have titles that describe their topic or purpose.  Screen
readers announce the page title when a user navigates to a new tab or window,
and it is the first piece of orientation information a non-sighted user
receives.

Checks:
* ``<title>`` element is absent                        →  **serious**
* ``<title>`` element is present but empty/whitespace  →  **serious**
"""

from __future__ import annotations

from bs4 import BeautifulSoup
from src.models import Violation

# ---------------------------------------------------------------------------
# Rule metadata
# ---------------------------------------------------------------------------

RULE_ID = "2.4.2"
CRITERION_NAME = "Page Titled"
LEVEL = "A"
SEVERITY = "serious"


# ---------------------------------------------------------------------------
# Rule implementation
# ---------------------------------------------------------------------------


def check(soup: BeautifulSoup, url: str) -> list[Violation]:
    """Return a violation when the page ``<title>`` is absent or empty."""
    title_tag = soup.find("title")
    title_text = (title_tag.get_text() if title_tag else "").strip()

    if not title_text:
        element_repr = str(title_tag) if title_tag else "<title> (missing)"
        return [
            Violation(
                wcag_criterion=RULE_ID,
                criterion_name=CRITERION_NAME,
                level=LEVEL,
                description=(
                    "Page is missing a descriptive <title> element or the title is empty. "
                    "Screen readers announce the title when users navigate between tabs, "
                    "providing essential orientation context."
                ),
                element=element_repr[:300],
                severity=SEVERITY,
                url=url,
            )
        ]

    return []

