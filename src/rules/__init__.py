"""WCAG rule plug-ins.

Each module in this package named ``rule_<criterion_id>_<short_name>.py`` is
auto-discovered by :mod:`src.rule_engine` and must expose:

* ``RULE_ID``        – WCAG criterion code, e.g. ``"1.1.1"``
* ``CRITERION_NAME`` – human-readable name, e.g. ``"Non-text Content"``
* ``LEVEL``          – ``"A"`` or ``"AA"``
* ``SEVERITY``       – default severity: ``"critical" | "serious" | "moderate" | "minor"``
* ``check(soup, url) -> list[Violation]`` – the rule implementation
"""
