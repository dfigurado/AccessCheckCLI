"""WCAG rule engine.

Automatically discovers every ``rule_*.py`` module inside :mod:`src.rules`,
imports it, and runs its :func:`check` function against a parsed DOM.

Adding a new WCAG rule is as simple as dropping a new file into ``src/rules/``
that follows the plug-in contract defined in :mod:`src.rules`.
"""

from __future__ import annotations

import pkgutil
import importlib

from pathlib import Path
from types import ModuleType
from bs4 import BeautifulSoup
from .models import Violation

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_RULES_PACKAGE = "src.rules"
_RULES_DIR = Path(__file__).parent / "rules"

# ---------------------------------------------------------------------------
# Rule discovery
# ---------------------------------------------------------------------------

def _discover_rule_modules() -> list[ModuleType]:
    """Return all rule modules, sorted by module name (i.e. by criterion number)."""
    modules: list[ModuleType] = []
    for _finder, module_name, _is_pkg in pkgutil.iter_modules([str(_RULES_DIR)]):
        if module_name.startswith("rule_"):
            full_name = f"{_RULES_PACKAGE}.{module_name}"
            mod = importlib.import_module(full_name)
            modules.append(mod)
    # Sort lexicographically so rules always run in criterion order (1.1.1, 2.4.2 …)
    return sorted(modules, key=lambda m: m.__name__)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def run_rules(soup: BeautifulSoup, url: str) -> tuple[list[Violation], list[str]]:
    """Run all discovered rule modules against *soup* and return results.

    Args:
        soup: Parsed BeautifulSoup document for the page.
        url:  The URL being audited (passed through to each rule for reporting).

    Returns:
        A two-tuple of:

        * ``violations`` – every :class:`~src.models.Violation` found across all rules.
        * ``passed_rule_ids`` – ``RULE_ID`` strings for rules that produced no violations.
    """
    violations: list[Violation] = []
    passed_ids: list[str] = []

    for module in _discover_rule_modules():
        check_fn = getattr(module, "check", None)
        if not callable(check_fn):
            continue  # module does not expose a check() — skip silently

        rule_id: str = getattr(module, "RULE_ID", module.__name__)

        try:
            found: list[Violation] = check_fn(soup, url)
        except Exception as exc:  # noqa: BLE001
            # A broken rule must not abort the whole audit; report it as a warning.
            import warnings  # noqa: PLC0415
            warnings.warn(
                f"Rule {rule_id} raised an unexpected error and was skipped: {exc}",
                RuntimeWarning,
                stacklevel=2,
            )
            continue

        if found:
            violations.extend(found)
        else:
            passed_ids.append(rule_id)

    return violations, passed_ids