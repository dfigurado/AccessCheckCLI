"""WCAG 2.1 — Success Criterion 4.1.2: Name, Role, Value (Level A).

For all UI components (form inputs, selects, text areas) that are not purely
presentational, the accessible *name* must be programmatically determinable.

Without an accessible name, screen readers announce the control type only
(e.g. "edit, blank") with no context, making forms unusable for non-sighted
users.

An accessible name can be provided by:

1. An associated ``<label for="id">`` element.
2. An ``aria-label`` attribute on the element itself.
3. An ``aria-labelledby`` attribute referencing another element's id.
4. An implicit label — the control is nested directly inside a ``<label>``.
"""

from __future__ import annotations

from bs4 import BeautifulSoup, Tag

from src.models import Violation

# ---------------------------------------------------------------------------
# Rule metadata
# ---------------------------------------------------------------------------

RULE_ID = "4.1.2"
CRITERION_NAME = "Name, Role, Value"
LEVEL = "A"
SEVERITY = "critical"

# Input types that are self-labelling or hidden — skip them.
_SKIP_INPUT_TYPES = frozenset(
    {"hidden", "submit", "button", "reset", "image"}
)

# Tags that require an accessible name.
_LABELABLE_TAGS = frozenset({"input", "select", "textarea"})


# ---------------------------------------------------------------------------
# Rule implementation
# ---------------------------------------------------------------------------


def check(soup: BeautifulSoup, url: str) -> list[Violation]:
    """Return violations for form controls that have no accessible name."""
    violations: list[Violation] = []

    for el in soup.find_all(list(_LABELABLE_TAGS)):
        if not isinstance(el, Tag):
            continue

        # Skip input types that are self-labelling or decorative.
        if el.name == "input":
            input_type = str(el.get("type", "text")).lower()
            if input_type in _SKIP_INPUT_TYPES:
                continue

        if not _has_accessible_name(soup, el):
            violations.append(
                Violation(
                    wcag_criterion=RULE_ID,
                    criterion_name=CRITERION_NAME,
                    level=LEVEL,
                    description=(
                        f"Form control <{el.name}> has no accessible name. "
                        "Add a <label for=\"…\">, aria-label, or aria-labelledby attribute "
                        "so assistive technologies can identify the field."
                    ),
                    element=str(el)[:300],
                    severity=SEVERITY,
                    url=url,
                )
            )

    return violations


# ---------------------------------------------------------------------------
# Accessibility-name resolution helpers
# ---------------------------------------------------------------------------


def _has_accessible_name(soup: BeautifulSoup, el: Tag) -> bool:
    """Return ``True`` if *el* has any form of programmatic accessible name."""

    # 1. aria-label attribute
    if str(el.get("aria-label", "")).strip():
        return True

    # 2. aria-labelledby referencing at least one non-empty element
    labelledby = str(el.get("aria-labelledby", "")).strip()
    if labelledby:
        for ref_id in labelledby.split():
            ref = soup.find(id=ref_id)
            if ref and ref.get_text(strip=True):
                return True

    # 3. Explicit <label for="id">
    el_id = str(el.get("id", "")).strip()
    if el_id:
        label = soup.find("label", attrs={"for": el_id})
        if label and isinstance(label, Tag):
            # A label is valid if it has text content OR contains an image with alt.
            if label.get_text(strip=True):
                return True
            if label.find("img", alt=True):
                return True

    # 4. Implicit label — el is a descendant of a <label> element
    parent = el.parent
    while parent and isinstance(parent, Tag):
        if parent.name == "label":
            return True
        parent = parent.parent

    # 5. title attribute (acceptable fallback per WCAG technique H65)
    if str(el.get("title", "")).strip():
        return True

    return False

