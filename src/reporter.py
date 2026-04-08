"""Report rendering and exit-code logic.

Supports three output formats:

* **text** – coloured terminal output (ANSI escape codes; degrades gracefully).
* **json** – machine-readable JSON array, one object per audited URL.
* **html** – self-contained styled HTML file rendered via a Jinja2 template.
"""

from __future__ import annotations

import json
import sys

from pathlib import Path
from dataclasses import asdict
from .models import AuditResult
from jinja2 import Environment, FileSystemLoader, select_autoescape

_TEMPLATES_DIR = Path(__file__).parent / "templates"

# ---------------------------------------------------------------------------
# ANSI colour helpers (auto-disabled when stdout is not a TTY)
# ---------------------------------------------------------------------------

_USE_COLOR = sys.stdout.isatty()

_SEVERITY_COLORS: dict[str, str] = {
    "critical": "\033[91m",  # bright red
    "serious":  "\033[93m",  # bright yellow
    "moderate": "\033[94m",  # bright blue
    "minor":    "\033[96m",  # bright cyan
}
_GREEN  = "\033[92m"
_BOLD   = "\033[1m"
_RESET  = "\033[0m"

def _c(text: str, code: str) -> str:
    """Wrap *text* in *code* + reset, but only when colour is enabled."""
    return f"{code}{text}{_RESET}" if _USE_COLOR else text

# ---------------------------------------------------------------------------
# JSON
# ---------------------------------------------------------------------------

def render_json(results: list[AuditResult]) -> str:
    """Serialize *results* to a JSON string (pretty-printed, UTF-8 safe)."""
    return json.dumps([asdict(r) for r in results], indent=2, ensure_ascii=False)

# ---------------------------------------------------------------------------
# Terminal text
# ---------------------------------------------------------------------------

def render_text(results: list[AuditResult]) -> str:
    """Render *results* as human-readable, ANSI-coloured terminal text."""
    lines: list[str] = []

    for result in results:
        sep = "─" * 62
        lines.append(f"\n{sep}")
        lines.append(_c(f"  URL: {result.url}", _BOLD))
        lines.append(sep)

        if result.fetch_error:
            lines.append(f"  {_c('✗ FETCH ERROR:', _SEVERITY_COLORS['critical'])} {result.fetch_error}")
            continue

        if not result.violations:
            lines.append(f"  {_c('✓ Passed', _GREEN)} — no violations found " f"({len(result.passed_rules)} rule(s) checked).")
        else:
            lines.append(_c(f"  ✗ {len(result.violations)} violation(s) found " f"| {len(result.passed_rules)} rule(s) passed\n", _SEVERITY_COLORS["critical"]))
            for v in result.violations:
                color = _SEVERITY_COLORS.get(v.severity, "")
                lines.append(f"  [{_c(v.severity.upper(), color)}] " f"WCAG {v.wcag_criterion} — {v.criterion_name} (Level {v.level})")
                lines.append(f"    {v.description}")
                snippet = v.element[:120] + ("…" if len(v.element) > 120 else "")
                lines.append(f"    {_c('Element:', _BOLD)} {snippet}")
                lines.append("")

    return "\n".join(lines)

# ---------------------------------------------------------------------------
# HTML
# ---------------------------------------------------------------------------

def render_html(results: list[AuditResult], output_path: str) -> None:
    """Render *results* to a self-contained HTML file at *output_path*."""
    env = Environment(
        loader=FileSystemLoader(str(_TEMPLATES_DIR)),
        autoescape=select_autoescape(["html", "xml", "j2"]),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    template = env.get_template("report.html.j2")
    total_violations = sum(r.total_violations for r in results)
    total_passed = sum(len(r.passed_rules) for r in results)
    html = template.render(
        results=results,
        total_violations=total_violations,
        total_passed=total_passed,
        version="0.1.0",
    )
    Path(output_path).write_text(html, encoding="utf-8")
    print(f"  HTML report written → {output_path}", file=sys.stderr)

# ---------------------------------------------------------------------------
# Exit code
# ---------------------------------------------------------------------------

def compute_exit_code(results: list[AuditResult]) -> int:
    """Return ``1`` if any URL has violations or a fetch error; ``0`` otherwise."""
    for result in results:
        if result.fetch_error or result.violations:
            return 1
    return 0