# AccessCheck CLI

> **WCAG 2.1 Website Accessibility Auditor** — zero-config, scriptable CLI for front-end developers, QA engineers, and accessibility consultants.

[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-0.1.0-green.svg)]()

---

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [WCAG Rules Covered](#wcag-rules-covered)
- [Requirements](#requirements)
- [Installation](#installation)
- [Usage](#usage)
- [CI / CD Integration](#ci--cd-integration)
- [Exit Codes](#exit-codes)
- [Architecture](#architecture)
- [Adding a New WCAG Rule](#adding-a-new-wcag-rule)
- [Development Setup](#development-setup)
- [Running Tests](#running-tests)
- [License](#license)

---

## Overview

Visually impaired users rely on web content that meets WCAG 2.1 standards. Existing tools (axe, Lighthouse) require browser GUIs or heavy CI integration overhead. **AccessCheck CLI** provides a zero-config, terminal-native audit tool that any developer can run against any URL and get structured, human-readable results instantly.

```bash
pip install accesscheck-cli
accesscheck https://example.com
```

---

## Features

| Feature | Details |
|---|---|
| **WCAG 2.1 Level A & AA** | Checks against 10 criteria out of the box |
| **Three output formats** | Coloured terminal text, JSON, and styled HTML report |
| **CI-friendly exit codes** | Exit `0` on pass, `1` on any violation |
| **Batch auditing** | Pass a plain-text file of URLs |
| **Authenticated pages** | Inject cookies with `--cookie` |
| **JS-rendered pages** | Optional Playwright backend with `--js` |
| **Pluggable rule engine** | Drop a new `rule_*.py` into `src/rules/` to add a check |
| **Severity tagging** | Every violation is tagged `critical / serious / moderate / minor` |

---

## WCAG Rules Covered

| Rule File | WCAG Criterion | Name | Level |
|---|---|---|---|
| `rule_1_1_1_alt_text` | 1.1.1 | Non-text Content | A |
| `rule_1_3_1_tables` | 1.3.1 | Info and Relationships | A |
| `rule_1_3_5_input_purpose` | 1.3.5 | Identify Input Purpose | AA |
| `rule_2_4_1_bypass_blocks` | 2.4.1 | Bypass Blocks | A |
| `rule_2_4_2_page_titled` | 2.4.2 | Page Titled | A |
| `rule_2_4_4_link_purpose` | 2.4.4 | Link Purpose (In Context) | A |
| `rule_2_4_6_heading_hierarchy` | 2.4.6 | Headings and Labels | AA |
| `rule_3_1_1_language` | 3.1.1 | Language of Page | A |
| `rule_4_1_1_1_parsing` | 4.1.1 | Parsing | A |
| `rule_4_1_2_form_labels` | 4.1.2 | Name, Role, Value | A |

---

## Requirements

- Python **3.11** or later
- *(Optional)* [Playwright](https://playwright.dev/python/) for JS-rendered pages

---

## Installation

### Standard (static HTML pages)

```bash
pip install accesscheck-cli
```

### With JavaScript rendering support

```bash
pip install "accesscheck-cli[js]"
playwright install chromium
```

---

## Usage

### Audit a Single URL

```bash
accesscheck https://example.com
```

### Multiple URLs

```bash
accesscheck https://example.com https://example.com/about
```

### Batch Auditing from a File

Create a `urls.txt` file — lines starting with `#` are ignored:

```text
# Production pages
https://example.com
https://example.com/about
https://example.com/contact
```

```bash
accesscheck --file urls.txt
```

### Output Formats

```bash
# Default: coloured terminal text
accesscheck https://example.com

# Machine-readable JSON
accesscheck https://example.com --format json
```

### HTML Report

```bash
accesscheck https://example.com --output report.html
```

### Authenticated Pages

```bash
accesscheck https://app.example.com/dashboard --cookie "session=abc123; token=xyz"
```

### JavaScript-Rendered Pages

Requires the `[js]` optional dependency (see [Installation](#installation)):

```bash
accesscheck https://spa.example.com --js
```

### All Flags at a Glance

| Flag | Description |
|---|---|
| `URL [URL …]` | One or more URLs to audit |
| `--file FILE` | Read URLs from `FILE`, one per line |
| `--format text\|json` | Output format (default: `text`) |
| `--output FILE` | Write an HTML report to `FILE` |
| `--cookie COOKIE` | Raw `Cookie` header string for authenticated pages |
| `--js` | Use Playwright for JS-rendered pages |

---

## CI / CD Integration

AccessCheck CLI exits with code `1` if **any** violation or fetch error is found, making it a drop-in CI gate.

### GitHub Actions

```yaml
- name: Accessibility audit
  run: |
    pip install accesscheck-cli
    accesscheck https://staging.example.com --format json --output a11y-report.html

- name: Upload accessibility report
  uses: actions/upload-artifact@v4
  with:
    name: accessibility-report
    path: a11y-report.html
```

### Pre-commit / Pre-push Hook

```bash
#!/usr/bin/env bash
accesscheck https://localhost:3000 || exit 1
```

---

## Exit Codes

| Code | Meaning |
|---|---|
| `0` | All audited URLs passed — no violations found |
| `1` | One or more violations (or fetch errors) detected |
| `2` | Usage error (no URLs provided, missing file, etc.) |

---

## Architecture

AccessCheck CLI follows a **pipeline architecture**:

```
CLI args → Fetcher → DOM Parser → Rule Engine → Reporter → stdout / file
```

| Module | Responsibility |
|---|---|
| `src/cli.py` | Entry point. Parses arguments, orchestrates the pipeline. |
| `src/fetcher.py` | Fetches HTML via `httpx`; optionally uses Playwright for SPAs. Handles auth cookies. |
| `src/dom_parser.py` | Parses raw HTML into a BeautifulSoup DOM tree. |
| `src/rule_engine.py` | Auto-discovers `rule_*.py` modules in `src/rules/` and runs each `check()` function. |
| `src/rules/` | One Python file per WCAG criterion — pluggable and isolated. |
| `src/reporter.py` | Renders results as terminal text, JSON, or HTML; computes exit code. |
| `src/templates/` | Jinja2 HTML templates for the `--output` report. |

---

## Adding a New WCAG Rule

1. Create `src/rules/rule_X_Y_Z_short_name.py`
2. Expose these module-level constants and one function:

```python
from bs4 import BeautifulSoup
from src.models import Violation

RULE_ID        = "X.Y.Z"
CRITERION_NAME = "Your Criterion Name"
LEVEL          = "A"          # or "AA"
SEVERITY       = "serious"    # critical | serious | moderate | minor

def check(soup: BeautifulSoup, url: str) -> list[Violation]:
    violations = []
    # ... your logic here ...
    return violations
```

The rule engine discovers and runs your file **automatically** — no registration required.

---

## Development Setup

```bash
git clone https://github.com/dfigurado/AccessCheckCLI.git
cd AccessCheckCLI

python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate

pip install -e ".[dev]"
```

---

## Running Tests

```bash
# Full test suite with coverage
pytest

# Quick smoke test (no live HTTP requests needed)
python smoke_test.py
```

Coverage target: **≥ 80 %**

---

## License

This project is licensed under the **MIT License**. See [LICENSE](LICENSE) for details.
