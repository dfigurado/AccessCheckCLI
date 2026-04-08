"""WCAG 2.1 — Success Criterion 2.4.4: Link Purpose (In Context) (Level A).

The purpose of each link must be determinable from the link text alone, or
from the link text together with its programmatically determined context.

Links are the primary navigation mechanism for screen reader users.  When a
user invokes the "list all links" mode (a very common pattern), the links are
read out of context — so "click here" or "read more" is completely meaningless.

Checks:
* Link has no accessible name at all                        → critical
  (no text, no aria-label, no aria-labelledby, no title,
   no child image with alt)
* Link text is a known generic/ambiguous phrase             → serious
  ("click here", "read more", "here", "more", "link" …)
* Link points only to "#" with no accessible context        → moderate
"""

from __future__ import annotations

import re
from bs4 import BeautifulSoup, Tag
from src.models import Violation

# ---------------------------------------------------------------------------
# Rule metadata
# ---------------------------------------------------------------------------

RULE_ID = "2.4.4"
CRITERION_NAME = "Link Purpose (In Context)"
LEVEL = "A"
SEVERITY = "serious"

# Phrases that are ambiguous out of context.
# Kept intentionally conservative to minimise false positives.
_AMBIGUOUS_TEXT: frozenset[str] = frozenset({
    "click here", "click", "here", "read more", "more", "link",
    "lean more", "details", "info", "information", "this",
    "continue", "go", "start", "open", "download", "see more",
    "view more", "show more", "more info", "more details", "page",
    "next", "previous", "top", "bottom", "back", "home", "exit"
})

# Normalise whitespace when comparing link text.
_WHITESPACE = re.compile(r"\s+")

# ---------------------------------------------------------------------------
# Rule implementation
# ---------------------------------------------------------------------------

def check(soup: BeautifulSoup, url: str) -> list[Violation]:
    """Return violations for links whose purpose cannot be determined."""
    violations: list[Violation] = []

    for a in soup.find_all("a"):
        if not isinstance(a, Tag):
            continue

        if not a.has_attr("href"):
            continue

        name = _get_accessible_name(soup, a)

        if not name:
            violations.append(
                Violation(
                    wcag_criterion=RULE_ID,
                    criterion_name=CRITERION_NAME,
                    level=LEVEL,
                    description=(
                        "Link has no accessible name. Add descriptive text content, "
                        "an aria-label, or an aria-labelledby attribute so screen "
                        "reader users know where the link leads."
                    ),
                    element=str(a)[:300],
                    severity="critical",
                    url=url,
                )
            )

        elif name in _AMBIGUOUS_TEXT:
            violations.append(
                Violation(
                    wcag_criterion=RULE_ID,
                    criterion_name=CRITERION_NAME,
                    level=LEVEL,
                    description=(
                        f'Link text "{name}" is ambiguous out of context. '
                        "When screen reader users list all links on a page, "
                        "generic phrases give no indication of the link destination. "
                        "Use descriptive text such as \"Read our accessibility guide\"."
                    ),
                    element=str(a)[:300],
                    severity="serious",
                    url=url
                )
            )

        elif a.get("href", "").strip() in ("#", "javascript:void(0)", "javascript:"):
            violations.append(
                Violation(
                    wcag_criterion=RULE_ID,
                    criterion_name=CRITERION_NAME,
                    level=LEVEL,
                    description=(
                        "Link points to a fragment identifier (\"#\"), "
                        "which is not useful for screen reader users. "
                        "Use a descriptive text such as \"Read our accessibility guide\"."
                    ),
                    element=str(a)[:300],
                    severity="moderate",
                    url=url
                )
            )

    return violations

# ---------------------------------------------------------------------------
# Accessible name computation (links)
# ---------------------------------------------------------------------------

def _get_accessible_name(soup: BeautifulSoup, a: Tag) -> str:
    """Return the normalised accessible name for a link, empty string if none.

    Resolution order follows the Accessible Name and Description Computation
    (ACCNAME) spec (simplified for static HTML analysis):

    1. aria-labelledby  → text of all referenced elements, space-joined
    2. aria-label       → attribute value
    3. Element contents → text nodes + alt text of child <img> elements
    4. title            → attribute value (last-resort fallback)
    """
    # 1. aria-labellby
    labelledby = str(a.get("aria-labelledby", "")).strip()
    if labelledby:
        parts: list[str] = []
        for ref_id in labelledby.split():
            ref = soup.find(id=ref_id)
            if ref:
                parts.append(ref.get_text(separator=" ", strip=True))
        name = " ".join(parts).strip()
        if name:
            return _normalise(name)

    # 2. aria-label
    aria_label = str(a.get("aria-label", "")).strip()
    if aria_label:
        return _normalise(aria_label)

    # 3. Text content of the link (includes alt text of child images via get_text)
    # We reconstruct manually so that img[alt] contributes its alt value.
    parts = []
    for child in a.descendants:
        if isinstance(child, Tag):
            if child.name == "img":
                alt = str(child.get("alt", "")).strip()
                if alt:
                    parts.append(alt)
        elif hasattr(child, "strip") and child.string:
            text = child.strip()
            if text:
                parts.append(text)
    content = " ".join(parts).strip()
    if content:
        return _normalise(content)

    # 4. title fallback
    title = str(a.get("title", "")).strip()
    if title:
        return _normalise(title)

    return ""

def _normalise(text: str) -> str:
    """Collapse whitespace and lowercase for consistent comparison."""
    return _WHITESPACE.sub(" ", text).strip().lower()