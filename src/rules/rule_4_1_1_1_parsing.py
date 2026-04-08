""" 
WCAG 2.1 — Success Criterion 4.1.1: Parsing (Level A).

In content implemented using markup languages, elements must have complete
start and end tags, elements must be nested according to their specifications,
elements must not contain duplicate attributes, and any IDs must be unique.

The most impactful statically-detectable violation is **duplicate id attributes**.
Many WCAG techniques depend on unique IDs:
  - <label for="id"> (SC 1.3.1, 4.1.2)
  - aria-labelledby="id" (SC 4.1.2)
  - aria-describedby="id"
  - aria-controls="id"
A duplicate id causes all of the above to silently fail or target the wrong element.

Checks:
* Duplicate ``id`` attribute values anywhere on the page  →  **critical**
* ARIA attributes (aria-labelledby, aria-describedby,
  aria-controls) referencing a non-existent id           →  **serious**
"""

from __future__ import annotations

from collections import Counter
from bs4 import BeautifulSoup, Tag
from src.models import Violation

# ---------------------------------------------------------------------------
# Rule metadata
# ---------------------------------------------------------------------------

RULE_ID = "4.1.1"
CRITERION_NAME = "Parsing"
LEVEL = "A"
SEVERITY = "critical"

# ARIA attributes whose values are id references
_ARIA_IDREF_ATTRS = ("aria-labelledby", "aria-describedby", "aria-controls", "aria-owns", "aria-flowto", "aria-activedescendant")

# ---------------------------------------------------------------------------
# Rule implementation
# ---------------------------------------------------------------------------

def check(soup: BeautifulSoup, url: str) -> list[Violation]:
    """Return violations for duplicate IDs and broken ARIA id references."""
    violations: list[Violation] = []
    violations.extend(_check_duplicate_ids(soup, url))
    violations.extend(_check_broken_aria_references(soup, url))
    return violations
    
# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _check_duplicate_ids(soup: BeautifulSoup, url: str) -> list[Violation]:
    """Flag every id value that appears more than once in the document."""
    violations: list[Violation] = []
    all_ids: list[str] = []
    
    for tag in soup.find_all(True):      # True = every element
        if not isinstance(tag, Tag):
            continue
        id_attr = str(tag.get("id", "")).strip()
        if id_attr:
            all_ids.append(id_attr)
            
    counts = Counter(all_ids)
    reported: set[str] = set()
    
    for tag in soup.find_all(True):
        if not isinstance(tag, Tag):
            continue
        id_attr = str(tag.get("id", "")).strip()
        if id_attr and counts[id_attr] > 1 and id_attr not in reported:
            reported.add(id_attr)
            violations.append(
                Violation(
                   wcag_criterion=RULE_ID,
                   criterion_name=CRITERION_NAME,
                   level=LEVEL,
                   description=(
                       f'Duplicate id="{id_attr}" found {counts[id_attr]} times. '
                       "Duplicate IDs break aria-labelledby, aria-describedby, "
                       "and <label for> associations, silently disabling "
                       "accessibility features for screen readers users."
                   ),
                   element=str(tag)[:300],
                   severity="critical",
                   url=url,
                )
            )

    return violations

def _check_broken_aria_references(soup: BeautifulSoup, url: str) -> list[Violation]:
    """Flag ARIA id-reference attributes that point to non-existent elements."""
    violations: list[Violation] = []

    # Build the set of all ids present in the document (only once)
    existing_ids: set[str] = {
        str(tag.get("id", "")).strip()
        for tag in soup.find_all(True)
        if isinstance(tag, Tag) and tag.get("id", "").strip()
    }

    for tag in soup.find_all(True):
        if not isinstance(tag, Tag):
            continue
        for attr in _ARIA_IDREF_ATTRS:
            ref_val = str(tag.get(attr, "")).strip()
            if not ref_val:
                continue
            for ref_id in ref_val.split():
                if ref_id not in existing_ids:
                    violations.append(
                        Violation(
                            wcag_criterion=RULE_ID,
                            criterion_name=CRITERION_NAME,
                            level=LEVEL,
                            description=(
                                f'{attr}="{ref_id}" references an id that does not '
                                "exist in the document. Assistive technologies cannot "
                                "resolve this reference, leaving the element unnamed."
                            ),
                            element=str(tag)[:300],
                            severity="serious",
                            url=url,
                        )
                    )

    return violations