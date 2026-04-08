# PROEJCT-01: AccessCheck CLI
## WCAG 2.1 Website Accessibility Auditor | Python/Node.js | CLI Tool

## Requirement Specification
|  |  |
|--|--|
| Project ID   | OSS-001 |
| Language     | Python 3.11+ (primary) with optional Node.js wrapper |
| Lincence     | MIT |
| Target Users | Front-end developers, QA engineers, accessibility consultants |
| Repository   | github.com/dilrukshanfigurado/accessibility-cli |

### 1.1. Purpose & Problem Statement
Visual impaired users rely on web content meeting WCAG 2.1 standars. Existing tools (axe, Lighthouse) require browser GUIs or CI integration overhead.
AccessCheck CLI provides a zero-config, scriptable audit tool that any developer can run from a terminal aginst any URL, producing structured, human-redable reports.

### 1.2. Functional Requirement

| ID | Priority | Requirement | Acceptance Criteria |
|----|----------|-------------|---------------------|
| FR-01 | Must | Accept one or more URLs as command-line arguments | Tools exits with usage error of no URL is provided |
| FR-02 | Must | Audit agaist WCAG 2.1 Level A and AA Criteria | Report maps each violations to a specific WCAG criterion code |
| FR-03 | Must | Output results as JSON and human-readable terminal text | --format json and --format text flags both produce valid output |
| FR-04 | Must | Return non-zero exit code on violations (CI-friendly) | Exit code 1 on violations, 0 on pass — verified in CI pipeline |
| FR-05 | Should | Export results to HTML report with visual summary | --output report.html generates a styled, self-contained HTML file |
| FR-06 | Should | Support batch auditing via a file of URLs | --file urls.txt processes each line as a URL sequentially |
| FR-07 | Should | Flag contrast ratio failures with computed values | Report shows foreground/background hex values and computed ratio |
| FR-08 | Could | Provide severity scoring (critical/serious/moderate/minor | Each violation tagged with WCAG-aligned severity level |
| FR-09 | Could | Support authenticated pages via cookie/session injection | --cookie flag accepts a cookie string for session-based pages |

### 1.3 Non-Functional Requirements
| Category | Requirement |
|----------|-------------|
| Performance | Single URL audit must complete within 10 seconds on standard broadband |
| Usability | pip install accesscheck-cli && accesscheck https://example.com should work out-of-the-box |
| Reliability | Network errors and timeouts handled gracefully with clear error messages |
| Portability | Works on Windows, macOS, Linux without additional dependencies |
| Documentation | README covers installation, usage, all flags, and CI integration examples |

## Software Design Document
### 2.1. Architecture
AccessCheck CLI follows a pipeline architecture: Input Parsing → Page Fetching → DOM Analysis → Rule Engine → Report Rendering. Each stage is a discrete module, making it easy for contributors to add new WCAG rules.

| Module | Responsibility |
|--------|----------------|
| cli.py | Entry point. Parses arguments using argparse. Orchestrates the pipeline. |
| fetcher.py | Fetches page HTML using httpx + Playwright for JS-rendered pages. Handles auth cookies. |
| dom_parser.py | Parses HTML into a DOM tree using BeautifulSoup. Extracts elements for rule evaluation. |
| rule_engine.py | Loads and runs WCAG rule modules. Collects violations and passes results downstream. |
| rules/ | One Python file per WCAG criterion (e.g., rule_1_1_1_alt_text.py). Pluggable pattern. |
| reporter.py | Formats results as terminal text, JSON, or HTML. Handles exit code logic. |
| templates/ | Jinja2 HTML templates for the --output HTML report option. |

### 2.2. Technology Stack
- Language: Python 3.11+
- HTTP fetching: httpx (sync) + Playwright (JS-rendered page support)
- DOM parsing: BeautifulSoup4 + lxml
- CLI framework: argparse (stdlib)
- HTML templating: Jinja2
- Testing: pytest + pytest-cov (>80% coverage target)
- Packaging: pyproject.toml/PyPl distribution via twine

### 2.3. Key Design Decisions
- Plugin-style rule module: each WCAG rule is standalone file, lowering the barrier for external contributors
- Playwrite optional dependency: basic audits work with alone; Playwright activates for JS-heavy sites
- CI-first codes: non-zero on any violations, enabling GitHub Actions / Jenkins integration without extra tooling
- JSON-first output: All internal data passed as typed dataclasses, serialised to JSON, then transformed for other formats.
