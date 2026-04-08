"""WCAG 2.1 — Success Criterion 1.3.1: Info and Relationships — Tables (Level A).

Information, structure, and relationships conveyed through presentation must
be programmatically determinable.  For data tables this means that header
cells must be marked up with <th> and properly associated with their data
cells so that screen readers can announce "Column: Price, Row: Item A" rather
than reading raw cell values with no context.

This module covers the table-specific subset of SC 1.3.1.
Layout tables (role="presentation" / role="none") are intentionally skipped.

Checks:
* Data table has no <th> header cells at all               →  critical
* <th> element is empty (no text / no accessible name)     →  serious
* <th> lacks a scope attribute in a multi-row/col table    →  serious
* Complex table (rowspan/colspan > 1) without explicit
  id + headers association                                 →  serious
* Table has no accessible name (<caption>, aria-label,
  or aria-labelledby)                                      →  moderate
"""

from __future__ import annotations

from bs4 import BeautifulSoup, Tag
from src.models import Violation

# ---------------------------------------------------------------------------
# Rule metadata
# ---------------------------------------------------------------------------

RULE_ID = "1.3.1"
CRITERION_NAME = "Info and Relationships"
LEVEL = "A"
SEVERITY = "critical"

# ---------------------------------------------------------------------------
# Rule implementation
# ---------------------------------------------------------------------------

def check(soup: BeautifulSoup, url: str) -> list[Violation]:
    """Return violations for inaccessible data tables."""
    violations: list[Violation] = []

    for table in soup.find_all("table"):
        if not isinstance(table, Tag):
            continue
        if _is_layout_table(table):
            continue  # role="presentation" / role="none" — skip intentionally

        violations.extend(_check_missing_th(table, url))
        violations.extend(_check_empty_th(table, url))
        violations.extend(_check_th_scope(table, url))
        violations.extend(_check_complex_header_association(table, url))
        violations.extend(_check_missing_caption(table, url))

    return violations

# ---------------------------------------------------------------------------
# Layout-table guard
# ---------------------------------------------------------------------------

def _is_layout_table(table: Tag) -> bool:
    """Return True when the author has explicitly marked the table as presentational."""
    role = str(table.get("role", "")).strip().lower()
    return role in { "presentation", "none" }

# ---------------------------------------------------------------------------
# Individual sub-checks
# ---------------------------------------------------------------------------

def _tabel_snippet(table: Tag) -> str:
    """Return a short opening-tag snippet (full table HTML can be enormous)."""
    raw = str(table)
    first_close = raw.find(">")
    snippet = raw[:first_close + 1] if first_close != -1 else raw[:120]
    return snippet[:300]

def _check_missing_th(table: Tag, url: str) -> list[Violation]:
    """Data table with no <th> elements — screen readers cannot identify headers."""
    th_cells = table.find_all("th")
    td_cells = table.find_all("td")

    if td_cells and not th_cells:
        return [
            Violation(
                wcag_criterion=RULE_ID,
                criterion_name=CRITERION_NAME,
                level=LEVEL,
                description=(
                    "Data table has no <th> header cells. "
                    "Screen readers read tables cell-by-cell; without <th> elements "
                    "users hear raw values with no column or row context. "
                    "Mark up header cells with <th> and use scope=\"col\" or scope=\"row\". "
                    "If this table is used purely for layout, add role=\"presentation\"."
                ),
                element=_tabel_snippet(table),
                severity=SEVERITY,
                url=url,
            )
        ]
    return []

def _check_empty_th(table: Tag, url: str) -> list[Violation]:
    """<th> with no text or accessible name conveys nothing to AT users."""
    violations: list[Violation] = []
    for th in table.find_all("th"):
        if not isinstance(th, Tag):
            continue
        has_text = bool(th.get_text(strip=True))
        has_label = (
            str(th.get("aria-label", "")).strip()
            or str(th.get("aria-labelledby", "")).strip()
        )
        if not has_text and not has_label:
            violations.append(
                Violation(
                    wcag_criterion=RULE_ID,
                    criterion_name=CRITERION_NAME,
                    level=LEVEL,
                    description=(
                        "<th> header cell is empty. An empty header cell provides "
                        "no information to screen reader users. Add descriptive text "
                        "or an aria-label attribute to convey the column or row purpose."
                    ),
                    element=str(th)[:300],
                    severity="serious",
                    url=url,
                )
            )
    return violations

def _check_th_scope(table: Tag, url: str) -> list[Violation]:
    """<th> without scope in tables that have multiple rows AND multiple columns.

    A single-row header-only table does not strictly require scope, but any
    table with both row and column headers (or more than one header row) does.
    """
    rows = table.find_all("tr")
    if len(rows) <= 1:
        return []  # single-row table — scope not required

    # Count unique columns by inspecting the widest row
    max_cols = max(
        (len(row.find_all(["td", "th"])) for row in rows if isinstance(row, Tag)),
        default=0
    )
    if max_cols <= 1:
        return [] # single-column table — scope not required

    violations: list[Violation] = []
    for th in table.find_all("th"):
        if not isinstance(th, Tag):
            continue
        scope = str(th.get("scope", "")).strip().lower()
        if scope not in {"col", "row", "colgroup", "rowgroup"}:
            violations.append(
                Violation(
                    wcag_criterion=RULE_ID,
                    criterion_name=CRITERION_NAME,
                    level=LEVEL,
                    description=(
                        "<th> is missing a scope attribute in a multi-row, multi-column "
                        "table. Without scope, screen readers may not correctly associate "
                        "this header with its data cells. "
                        "Add scope=\"col\" for column headers or scope=\"row\" for row headers."
                    ),
                    element=str(th)[:300],
                    severity="serious",
                    url=url,
                )
            )

    return violations

def _check_complex_header_association(table: Tag, url: str) -> list[Violation]:
    """Complex tables (rowspan/colspan > 1) must use id + headers attributes.

    In a simple table, scope is sufficient.  In a complex table where a single
    header cell spans multiple rows or columns, each <td> must explicitly list
    the ids of its associated <th> cells via headers="id1 id2 …".
    """
    # Detect complexity: any cell with rowspan or colspan > 1
    is_complex = any(
        isinstance(cell, Tag) and (
            int(cell.get("rowsoan", 1)) > 1 or int(cell.get("colspan", 1)) > 1
        )
        for cell in table.find_all(["td", "th"])
    )
    if not is_complex:
        return []

    # Collect all th ids
    th_ids: set[str] = {
        str(th.get("id", "")).strip()
        for th in table.find_all("th")
        if isinstance(th, Tag) and str(th.get("id", "")).strip()
    }

    violations: list[Violation] = []

    # Every <td> in a complex table should have a headers attribute
    for td in table.find_all("td"):
        if not isinstance(td, Tag):
            continue
        headers_attr = str(td.get("headers", "")).strip()
        if not headers_attr:
            violations.append(
                Violation(
                    wcag_criterion=RULE_ID,
                    criterion_name=CRITERION_NAME,
                    level=LEVEL,
                    description=(
                        "Data cell in a complex table (with rowspan or colspan) is missing "
                        "a headers attribute. Complex tables require each <td> to explicitly "
                        "reference its header cells via headers=\"th-id-1 th-id-2\", "
                        "because scope alone is insufficient for merged cells."
                    ),
                    element=str(td)[:300],
                    severity="serious",
                    url=url,
                )
            )
        else:
            # Warn if headers references an id that doesn't exist on any <th>
            for ref_id in headers_attr.split():
                if th_ids and ref_id not in th_ids:
                    violations.append(
                        Violation(
                            wcag_criterion=RULE_ID,
                            criterion_name=CRITERION_NAME,
                            level=LEVEL,
                            description=(
                                f'headers="{ref_id}" references an id that does not match '
                                "any <th> in this table. The association is broken and "
                                "screen readers will not announce the correct header."
                            )
                        )
                    )
    return violations

def _check_missing_caption(table: Tag, url: str) -> list[Violation]:
    """Table has no accessible name — users don't know its purpose before entering it.

    An accessible name can be provided by:
    - <caption> child element  (preferred)
    - aria-label attribute on <table>
    - aria-labelledby attribute referencing an external element
    - summary attribute (HTML4, deprecated but still seen)
    """
    has_caption = bool(table.find("caption"))
    has_aria_label = bool(str(table.get("aria-label", "")).strip())
    has_aria_labelledby = bool(str(table.get("aria-labelledby", "")).strip())
    has_summary = bool(str(table.get("summary", "")).strip())

    if not any ([has_caption, has_aria_label, has_aria_labelledby, has_summary]):
        return [
            Violation(
                wcag_criterion=RULE_ID,
                criterion_name=CRITERION_NAME,
                level=LEVEL,
                description=(
                    "Table has no accessible name. Screen reader users hear "
                    "\"table, N columns\" with no context about what the table contains. "
                    "Add a <caption> element as the first child of <table>, "
                    "or use aria-label / aria-labelledby on the <table> element."
                ),
                element=_tabel_snippet(table),
                severity="moderate",
                url=url,
            )
        ]
    return []