"""WCAG 2.1 — Success Criterion 1.1.1: Non-text Content (Level A).

Every non-decorative image must have an ``alt`` attribute that conveys the
same information as the image for users who cannot see it.

Checks:
* ``<img>`` missing the ``alt`` attribute entirely  →  **critical**
* ``<img role="img">`` with an empty ``alt=""``      →  **serious**
  (An empty alt is valid for decorative images, but role="img" signals
   the image conveys meaning, making an empty alt contradictory.)
"""

from __future__ import annotations

from bs4 import BeautifulSoup, Tag

from src.models import Violation

# ---------------------------------------------------------------------------
# Rule metadata (consumed by rule_engine and reporter)
# ---------------------------------------------------------------------------

RULE_ID = "1.1.1"
CRITERION_NAME = "Non-text Content"
LEVEL = "A"
SEVERITY = "critical"


# ---------------------------------------------------------------------------
# Rule implementation
# ---------------------------------------------------------------------------


def check(soup: BeautifulSoup, url: str) -> list[Violation]:
    """Return violations for images that lack a meaningful alternative text."""
    violations: list[Violation] = []

    for img in soup.find_all("img"):
        if not isinstance(img, Tag):
            continue

        if not img.has_attr("alt"):
            # Missing alt entirely — most impactful violation.
            violations.append(
                Violation(
                    wcag_criterion=RULE_ID,
                    criterion_name=CRITERION_NAME,
                    level=LEVEL,
                    description=(
                        "Image is missing an alt attribute. "
                        "Screen readers cannot describe this image to non-sighted users."
                    ),
                    element=str(img)[:300],
                    severity="critical",
                    url=url,
                )
            )

        elif img.get("alt", "").strip() == "" and img.get("role") == "img":
            # role="img" signals the image carries meaning; empty alt is contradictory.
            violations.append(
                Violation(
                    wcag_criterion=RULE_ID,
                    criterion_name=CRITERION_NAME,
                    level=LEVEL,
                    description=(
                        'Image has role="img" but an empty alt attribute. '
                        "An accessible name is required when the image conveys meaning."
                    ),
                    element=str(img)[:300],
                    severity="serious",
                    url=url,
                )
            )

    return violations

