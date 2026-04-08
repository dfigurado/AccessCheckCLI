"""AccessCheck CLI — entry point.

Parses command-line arguments, orchestrates the fetch → parse → rule-engine →
report pipeline, and exits with an appropriate status code.

Usage examples::
    accesscheck https://example.com
    accesscheck https://example.com --format json
    accesscheck https://example.com --output report.html
    accesscheck --file urls.txt --format json
    accesscheck https://example.com --cookie "session=abc123" --js
"""

from __future__ import annotations

import sys
import argparse

from pathlib import Path
from .fetcher import fetch_page, FetchError
from .dom_parser import parse_html
from .rule_engine import run_rules
from .reporter import render_text, render_json, render_html, compute_exit_code
from .models import AuditResult


# ---------------------------------------------------------------------------
# Argument parser
# ---------------------------------------------------------------------------

def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="accesscheck",
        description=(
            "AccessCheck CLI — WCAG 2.1 Website Accessibility Auditor.\n"
            "Exits with code 0 when no violations are found, 1 otherwise (CI-friendly)."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  accesscheck https://example.com\n"
            "  accesscheck https://example.com --format json\n"
            "  accesscheck --file urls.txt --output report.html\n"
        ),
    )
    parser.add_argument(
        "urls",
        nargs="*",
        metavar="URL",
        help="One or more URLs to audit.",
    )
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        dest="fmt",
        metavar="FORMAT",
        help="Output format: 'text' (default) or 'json'.",
    )
    parser.add_argument(
        "--output",
        metavar="FILE",
        help="Write an HTML report to FILE (e.g. report.html).",
    )
    parser.add_argument(
        "--file",
        metavar="FILE",
        help="Read URLs from FILE, one per line (lines starting with '#' are ignored).",
    )
    parser.add_argument(
        "--cookie",
        metavar="COOKIE",
        help="Raw Cookie header string for authenticated pages (e.g. 'session=abc; token=xyz').",
    )
    parser.add_argument(
        "--js",
        action="store_true",
        default=False,
        help=("Use Playwright for JS-rendered pages (requires: pip install accesscheck-cli[js])."),
    )
    return parser

# ---------------------------------------------------------------------------
# URL collection
# ---------------------------------------------------------------------------

def _collect_urls(args: argparse.Namespace) -> list[str]:
    urls: list[str] = list(args.urls)

    if args.file:
        path = Path(args.file)
        if not path.exists():
            print(f"Error: URL file not found: {args.file}", file=sys.stderr)
            sys.exit(2)
        for line in path.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if stripped and not stripped.startswith("#"):
                urls.append(stripped)

    if not urls:
        print("Error: no URLs provided. Pass a URL as an argument or use --file.", file=sys.stderr)
        sys.exit(2)

    return urls

# ---------------------------------------------------------------------------
# Single-URL audit
# ---------------------------------------------------------------------------

def _audit_url(url: str, *, cookie: str | None, use_js: bool) -> AuditResult:
    """Fetch, parse, and evaluate WCAG rules for a single *url*."""
    try:
        html = fetch_page(url, cookie=cookie, use_playwright=use_js)
    except FetchError as exc:
        return AuditResult(url=url, fetch_error=str(exc))

    soup = parse_html(html)
    violations, passed = run_rules(soup, url)
    return AuditResult(url=url, violations=violations, passed_rules=passed)


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------


def main() -> None:
    """CLI entry point registered in ``pyproject.toml`` as ``accesscheck``."""
    parser = _build_parser()
    args = parser.parse_args()
    urls = _collect_urls(args)

    results: list[AuditResult] = []
    for url in urls:
        print(f"  Auditing: {url} …", file=sys.stderr)
        results.append(_audit_url(url, cookie=args.cookie, use_js=args.js))

    # Optional HTML report
    if args.output:
        render_html(results, args.output)

    # Primary output to stdout
    if args.fmt == "json":
        print(render_json(results))
    else:
        print(render_text(results))

    sys.exit(compute_exit_code(results))


if __name__ == "__main__":
    main()