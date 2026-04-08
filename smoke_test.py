"""Quick smoke-test — exercises the full pipeline without a live HTTP request."""
from __future__ import annotations

from src.dom_parser import parse_html
from src.rule_engine import run_rules
from src.reporter import render_text, render_json, render_html, compute_exit_code
from src.models import AuditResult

# ── Intentionally bad HTML (triggers all four current rules) ─────────────────
BAD_HTML = (
    "<!DOCTYPE html>"
    "<html>"                          # missing lang  → rule 3.1.1
    "<head></head>"                   # missing title → rule 2.4.2
    "<body>"
    '<img src="logo.png">'            # no alt        → rule 1.1.1 critical
    '<img src="hero.png" role="img" alt="">'  # role+empty alt → rule 1.1.1 serious
    "<form>"
    '<input type="text" id="name">'   # no label      → rule 4.1.2
    "<select id=\"country\"><option>US</option></select>"  # no label → rule 4.1.2
    "</form>"
    "</body></html>"
)

# ── Good HTML (should pass all rules) ───────────────────────────────────────
GOOD_HTML = (
    '<!DOCTYPE html>'
    '<html lang="en">'
    '<head><title>Example Page</title></head>'
    '<body>'
    '<img src="logo.png" alt="Company logo">'
    '<img src="decor.png" alt="">'           # decorative — alt="" is fine
    '<form>'
    '<label for="name">Full name</label>'
    '<input type="text" id="name">'
    '<label for="country">Country</label>'
    '<select id="country"><option>US</option></select>'
    '</form>'
    '</body></html>'
)


def audit(label: str, html: str) -> AuditResult:
    soup = parse_html(html)
    violations, passed = run_rules(soup, f"http://test/{label}")
    return AuditResult(
        url=f"http://test/{label}",
        violations=violations,
        passed_rules=passed,
    )


results = [audit("bad.html", BAD_HTML), audit("good.html", GOOD_HTML)]

# ── Terminal text output ─────────────────────────────────────────────────────
print(render_text(results))

# ── JSON output ───────────────────────────────────────────────────────────────
import json
data = json.loads(render_json(results))
bad_result = data[0]
good_result = data[1]
print(f"\n[JSON] bad.html  violations : {len(bad_result['violations'])}")
print(f"[JSON] good.html violations : {len(good_result['violations'])}")

# ── HTML report ───────────────────────────────────────────────────────────────
render_html(results, "smoke_report.html")

# ── Exit code ────────────────────────────────────────────────────────────────
code = compute_exit_code(results)
print(f"\nExit code: {code}  (expected 1 because bad.html has violations)")
assert code == 1, f"Expected exit code 1, got {code}"
print("\n✓ All smoke-test assertions passed.")