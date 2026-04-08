"""Shared data-transfer objects used across the AccessCheck pipeline."""

from __future__ import annotations
from dataclasses import dataclass, field

@dataclass
class Violation:
    """A single WCAG rule violation detected on a page.

    Attributes:
        wcag_criterion:  WCAG 2.1 criterion code, e.g. ``"1.1.1"``.
        criterion_name:  Human-readable criterion title, e.g. ``"Non-text Content"``.
        level:           Conformance level – ``"A"`` or ``"AA"``.
        description:     Plain-English explanation of the violation.
        element:         Serialised HTML snippet of the offending element (may be truncated).
        severity:        One of ``"critical" | "serious" | "moderate" | "minor"``.
        url:             The URL on which the violation was detected.
    """

    wcag_criterion: str
    criterion_name: str
    level: str
    description: str
    element: str
    severity: str
    url: str

@dataclass
class AuditResult:
    """Aggregated accessibility audit results for a single URL.

    Attributes:
        url:          The audited URL.
        violations:   All violations found; empty list means the page passed every checked rule.
        passed_rules: RULE_IDs of rules that produced no violations.
        fetch_error:  Non-``None`` when the page could not be retrieved; other fields are empty.
    """

    url: str
    violations: list[Violation] = field(default_factory=list)
    passed_rules: list[str] = field(default_factory=list)
    fetch_error: str | None = None

    # ------------------------------------------------------------------
    # Convenience helpers
    # ------------------------------------------------------------------

    @property
    def passed(self) -> bool:
        """``True`` when no violations were found and the page was fetched successfully."""
        return not self.fetch_error and not self.violations

    @property
    def total_violations(self) -> int:
        return len(self.violations)

