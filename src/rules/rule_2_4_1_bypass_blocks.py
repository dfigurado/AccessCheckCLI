"""WCAG 2.1 — Success Criterion 2.4.1: Bypass Blocks (Level A).

A mechanism must exist to bypass blocks of content that are repeated across
multiple pages — primarily site-wide navigation menus.

Without a bypass mechanism, keyboard-only users must Tab through every
navigation link on every page load to reach the main content.  A screen reader
user may Tab through 40+ links just to get to the first paragraph.

WCAG accepts any ONE of these techniques as sufficient:

1. Skip navigation link  — a visible (or focusable) <a href="#main"> near the
   top of the page that jumps directly to the main content.
2. ARIA landmarks        — <main> (or role="main") lets screen reader users
   jump regions with a single keystroke (e.g. F6 / landmark shortcut).
3. Heading structure     — properly nested headings allow "jump to heading"
   navigation (checked separately by rule 2.4.6).

This rule raises a violation only when NONE of the two static-detectable
mechanisms (skip link + landmark) are present.

Checks:
* No <main> landmark (and no role="main")              →  serious
* No skip navigation link near the top of the page     →  moderate
  (only raised when <main> is also absent — belt-and-braces)
* Multiple <nav> elements with no accessible names     →  minor
  (users can't distinguish "main nav" from "footer nav" etc.)
"""

from __future__ import annotations
from bs4 import BeautifulSoup, Tag
from src.models import Violation

# ---------------------------------------------------------------------------
# Rule metadata
# ---------------------------------------------------------------------------

RULE_ID = "2.4.1"
CRITERION_NAME = "Bypass Blocks"
LEVEL = "A"
SEVERITY = "serious"

# How many <a> elements from the top of <body> to scan for a skip link.
_SKIP_LINK_SCAN_DEPTH = 10

# Words that identify a skip_navigation link by its text context.
_SKIP_LINK_KEYWORDS = frozenset({
    "skip", "bypass", "jump to", "go to main", "main content",
    "skip navigation", "skip to content", "skip to main",
})

# ---------------------------------------------------------------------------
# Rule implementation
# ---------------------------------------------------------------------------

def check(soup: BeautifulSoup, url: str) -> list[Violation]:
    """Return violations for pages that lack a static-detectable bypass mechanism."""
    violations: list[Violation] = []

    has_main = _has_main_landmark(soup)
    has_skip_nav = _has_skip_nav_link(soup)

    # ── Check 1: No main landmark
    if not _has_main_landmark(soup):
        violations.append(
            Violation(
                wcag_criterion=RULE_ID,
                criterion_name=CRITERION_NAME,
                level=LEVEL,
                description=(
                    "Page has no <main> landmark element (or role=\"main\"). "
                    "Screen reader and keyboard users have no programmatic way to "
                    "jump directly to the primary content, forcing them to Tab "
                    "through every navigation link on every page load. "
                    "Wrap your main content in <main> or add role=\"main\"."
                ),
                element="(no <main> or role=\"main\" found in document)",
                severity=SEVERITY,
                url=url,
            )
        )

    # ── Check 2: No skip navigation link (only when <main> also absent) ─────
    # If <main> exists, landmark navigation satisfies the criterion on its own.
    # If <main> is absent, flag missing skip nav as an additional gap.
    if not has_main and not has_skip_nav:
        violations.append(
            Violation(
                wcag_criterion=RULE_ID,
                criterion_name=CRITERION_NAME,
                level=LEVEL,
                description=(
                    "Page has no skip navigation link near the top of the page. "
                    "Add a link as the first focusable element: "
                    "<a href=\"#main-content\">Skip to main content</a>, "
                    "and ensure an element with id=\"main-content\" exists. "
                    "This gives sighted keyboard users a visible bypass mechanism."
                ),
                element="(no skip-navigation <a href=\"#…\"> found in first links)",
                severity="moderate",
                url=url,
            )
        )

    # ── Check 3: Multiple <nav> elements with no accessible names ───────────
    violations.extend(_check_unlabelled_navs(soup, url))

    return violations

# ---------------------------------------------------------------------------
# Detection helpers
# ---------------------------------------------------------------------------

def _has_main_landmark(soup: BeautifulSoup) -> bool:
    """Return True if the page has a <main> element or role="main"."""
    if soup.find("main") or soup.find("main", role="main"):
        return True
    if soup.find(attrs={"role": "main"}):
        return True
    return False

def _has_skip_nav_link(soup: BeautifulSoup) -> bool:
    """Return True if a skip navigation link exists near the top of the page.

    Strategy:
    - Scan the first ``_SKIP_LINK_SCAN_DEPTH`` <a> elements in the document.
    - A qualifying link must have an href starting with "#" whose target ID
      exists in the document AND whose visible text contains a skip keyword.
    - OR: any <a> anywhere whose text contains a skip keyword and points to an
      existing internal anchor (covers hidden / CSS-positioned skip links).
    """
    all_links = [t for t in soup.find_all("a") if isinstance(t, Tag)]

    # Pass 1 - scan the first N links (most skip-nav links appear at the top)
    for a in all_links[:_SKIP_LINK_SCAN_DEPTH]:
        if _is_skip_link(soup, a):
            return True

    # Pass 2 - full document scan for hidden skip links (e.g. Off-screen via CSS)
    for a in all_links:
        text = a.get_text(separator=" ", strip=True).lower()
        if any(kw in text for kw in _SKIP_LINK_KEYWORDS):
            href = str(a.get("href", "")).strip()
            if href.startswith("#") and _target_exists(soup, href[1:]):
                return True

    return False

def _is_skip_link(soup: BeautifulSoup, a: Tag) -> bool:
    """Return True if *a* looks like a skip navigation link."""
    href = str(a.get("href", "")).strip()
    if not href.startswith("#"):
        return False
    target_id = href[1:]
    if not target_id or not _target_exists(soup, target_id):
        return False
    text = a.get_text(separator=" ", strip=True).lower()
    return any(kw in text for kw in _SKIP_LINK_KEYWORDS)


def _target_exists(soup: BeautifulSoup, element_id: str) -> bool:
    """Return True if an element with *element_id* exists in the document."""
    return bool(element_id and soup.find(id=element_id))

def _check_unlabelled_navs(soup: BeautifulSoup, url: str) -> list[Violation]:
    """Flag pages with multiple <nav> elements that share no accessible name.

    When a page has two or more <nav> blocks (e.g. site nav + breadcrumb +
    footer nav), each must carry an aria-label or aria-labelledby so that
    screen reader users can distinguish them in the landmark menu.
    """
    nav_tags = [t for t in soup.find_all("nav") if isinstance(t, Tag)]

    # Also count role="navigation" elements
    role_navs = [
        t for t in soup.find_all(attrs={"role": "navigation"})
        if isinstance(t, Tag) and t.name != "nav"
    ]
    all_navs = nav_tags + role_navs

    if len(all_navs) <= 2:
        return [] # Only one nav - no ambiguity, no violation.

    violations: list[Violation] = []
    for nav in all_navs:
        has_label = (
            str(nav.get("aria-label", "")).strip()
            or str(nav.get("aria-labelledby", "")).strip()
            or str(nav.get("title", "")).strip()
        )
        if not has_label:
            violations.append(
                Violation(
                    wcag_criterion=RULE_ID,
                    criterion_name=CRITERION_NAME,
                    level=LEVEL,
                    description=(
                        f"Page has {len(all_navs)} navigation landmarks but this "
                        "<nav> has no accessible name. Screen reader users cannot "
                        "distinguish navigation regions in the landmark menu. "
                        "Add aria-label=\"Main navigation\" (or similar) to each <nav>."
                    ),
                    element=str(nav)[:300],
                    severity="minor",
                    url=url,
                )
            )
    return violations