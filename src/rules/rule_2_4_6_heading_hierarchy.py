"""WCAG 2.1 — Success Criterion 2.4.6: Headings and Labels (Level AA).

Headings and labels must describe their topic or purpose, and heading levels
must reflect a logical document structure.

Screen reader users navigate pages predominantly by headings — pressing H to
jump to the next heading, or 1–6 to jump to a specific level.  A broken
heading hierarchy (skipped levels, no h1, empty headings) destroys this
navigation model and forces users to read the entire page linearly.

Checks:
* Page has no <h1> element                                 → serious
* Page has more than one <h1> element                      → moderateDom
* Heading level jumps by more than one step downward
  (e.g. <h2> directly followed by <h4>)                    → serious
* Heading element has no text content (empty heading)      → serious
"""

from __future__ import annotations

from bs4 import BeautifulSoup, Tag
from src.models import Violation

# ---------------------------------------------------------------------------
# Rule metadata
# ---------------------------------------------------------------------------

RULE_ID = "2.4.6"
CRITERION_NAME = "Headings and Labels"
LEVEL = "AA"
SEVERITY = "serious"

_HEADING_TAGS = ("h1", "h2", "h3", "h4", "h5", "h6")

# ---------------------------------------------------------------------------
# Rule implementation
# ---------------------------------------------------------------------------

def check(soup: BeautifulSoup, url: str) -> list[Violation]:
    """Return violations for broken heading structure and empty headings."""
    violations: list[Violation] = []

    headings = [t for t in soup.find_all(_HEADING_TAGS) if isinstance(t, Tag)]

    if not headings:
        # No headings at all - page has no navigation structure.
        violations.append(
            Violation(
                wcag_criterion=RULE_ID,
                criterion_name=CRITERION_NAME,
                level=LEVEL,
                description=(
                    "Page contains no heading elements (<h1>–<h6>). "
                    "Screen reader users navigate pages by jumping between headings. "
                    "Structure your content with a logical heading hierarchy "
                    "starting with a single <h1> for the main page topic."
                ),
                element="(no headings found in document)",
                severity=SEVERITY,
                url=url,
            )
        )
        return violations

    violations.extend(_check_h1_presence(headings, url))
    violations.extend(_check_empty_headings(headings, url))
    violations.extend(_check_heading_hierarchy(headings, url))

    return violations

# ---------------------------------------------------------------------------
# Sub-checks
# ---------------------------------------------------------------------------

def _heading_level(tag: Tag) -> int:
    """Return the numeric level of a heading tag (h1 → 1, h6 → 6)."""
    return int(tag.name[1])

def _check_h1_presence(headings: list[Tag], url: str) -> list[Violation]:
    """Flag pages with no h1 or with more than one h1."""
    h1_tags = [h for h in headings if h.name == "h1"]
    violations: list[Violation] = []

    if not h1_tags:
        violations.append(
            Violation(
                wcag_criterion=RULE_ID,
                criterion_name=CRITERION_NAME,
                level=LEVEL,
                description=(
                    "Page has no <h1> element. Every page should have exactly one "
                    "<h1> that identifies the main content topic — equivalent to the "
                    "title of a document. Screen reader users expect this as the "
                    "primary entry point when jumping to the top-level heading."
                ),
                element="(no <h1> found in document)",
                severity=SEVERITY,
                url=url,
            )
        )
    elif len(h1_tags) > 1:
        # Report each extra h1 (keep first one as valid, flag the rest)
        for extra_h1 in h1_tags[1:]:
            violations.append(
                Violation(
                    wcag_criterion=RULE_ID,
                    criterion_name=CRITERION_NAME,
                    level=LEVEL,
                    description=(
                        f"Page has {len(h1_tags)} <h1> elements. Best practice is "
                        "one <h1> per page to clearly identify the single main topic. "
                        "Multiple <h1> elements confuse the document outline and make "
                        "it harder for screen reader users to identify the page purpose."
                    ),
                    element=str(extra_h1)[:300],
                    severity="moderate",
                    url=url,
                )
            )

    return violations

def _check_empty_headings(headings: list[Tag], url: str) -> list[Violation]:
    """Flag heading elements that have no accessible text content."""
    violations: list[Violation] = []

    for heading in headings:
        text = heading.get_text(strip=True)
        aria_label = str(heading.get("aria-label", "")).strip()
        aria_labelledby = str(heading.get("aria-labelledby", "")).strip()

        if not text and not aria_label and not aria_labelledby:
            violations.append(
                Violation(
                    wcag_criterion=RULE_ID,
                    criterion_name=CRITERION_NAME,
                    level=LEVEL,
                    description=(
                        f"<{heading.name}> heading element is empty. "
                        "Screen readers announce the heading level (e.g. \"heading level 2\") "
                        "but no text follows, leaving users with no section context. "
                        "Add descriptive text or remove the element if it is decorative."
                    ),
                    element=str(heading)[:300],
                    severity="serious",
                    url=url,
                )
            )

    return violations

def _check_heading_hierarchy(headings: list[Tag], url: str) -> list[Violation]:
    """Flag heading levels that skip one or more steps downward.

    Rule: each heading may only increase its level by 1 relative to the
    previous heading.  Decreasing by any amount (closing a section) is
    always valid.

    Example violations:
        h1 → h3  (skips h2)
        h2 → h5  (skips h3 and h4)

    Example valid sequences:
        h1 → h2 → h3 → h2 → h3   (re-opens a level — fine)
        h3 → h1                  (large jump back up — fine)
    """
    violations: list[Violation] = []
    prev_level: int = 0

    for heading in headings:
        current_level = _heading_level(heading)

        if prev_level > 0 and current_level > prev_level + 1:
            skipped = list(range(prev_level + 1, current_level))
            skipped_str = ", ".join(f"<h{s}" for s in skipped)
            violations.append(
                Violation(
                    wcag_criterion=RULE_ID,
                    criterion_name=CRITERION_NAME,
                    level=LEVEL,
                    description=(
                        f"Heading level jumps from <h{prev_level}> to "
                        f"<h{current_level}>, skipping {skipped_str}. "
                        "Screen reader users depend on a consistent heading hierarchy "
                        "to understand document structure and navigate between sections. "
                        f"Insert the missing {skipped_str} level(s) or promote this "
                        f"heading to <h{prev_level + 1}>."
                    ),
                    element=str(heading)[:300],
                    severity="serious",
                    url=url,
                )
            )

        prev_level = current_level

    return violations