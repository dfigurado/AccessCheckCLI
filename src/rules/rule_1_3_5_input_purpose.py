"""WCAG 2.1 — Success Criterion 1.3.5: Identify Input Purpose (Level AA).

The purpose of each input field that collects information *about the user*
must be programmatically determinable.

The primary technique (WCAG H98) is the HTML ``autocomplete`` attribute with
one of the recognised autofill token values from the WHATWG HTML specification.
When set correctly, browsers, password managers, and assistive technologies
(e.g. Switch Access, AAC devices) can auto-populate fields — dramatically
reducing the cognitive and motor load for users with disabilities.

Scope: this rule only applies to inputs that plausibly collect personal user
information.  It uses a two-stage detection strategy:
  1. ``type``-based  — ``type=" email "``, ``type=" tel "``, ``type=" password "``
                       always collect personal data.
  2. Heuristic match — ``name``, ``id``, and ``placeholder`` attributes are
                       matched against keyword patterns for common personal
                       data fields (name, address, phone, DOB, etc.)

Checks:
* Personal-info input has no ``autocomplete`` attribute        →  serious
* Personal-info input has ``autocomplete=" off "``             →  moderate
  (disables browser/AT autofill; may be a legitimate security
   choice for OTP / security-answer fields, so lower severity)
"""
from __future__ import annotations

import re
from bs4 import BeautifulSoup, Tag
from src.models import Violation 

# ---------------------------------------------------------------------------
# Rule metadata
# ---------------------------------------------------------------------------

RULE_ID = "1.3.5" 
CRITERION_NAME = "Input Purpose" 
LEVEL = "AA" 
SEVERITY = "serious" # Input types that are never about user personal data - skip entirely

_SKIP_INPUT_TYPES = frozenset({ 
        "hidden",
        "submit",
        "button",
        "reset",
        "image",
        "checkbox",
        "radio",
        "range",
        "color",
        "file",
        "search", # search boxes collect queries, not personal info
}) 

# ---------------------------------------------------------------------------
# Detection tables
# ---------------------------------------------------------------------------
# Inputs whose TYPE alone tells us they collect personal user information.
# Maps input type → (recommended autocomplete token, human-readable label).

_PERSONAL_INFO_TYPES = { 
        "email": ("email", "Email address"),
        "tel": ("tel", "Phone number"),
        "password": ("current-password or new-password", "password"),
        "url": ("url", "URL / website"),
} 

# Patterns matched (case-insensitively) against name / id / placeholder.
# Each entry: (compiled regex, recommended autocomplete token, field label)
_PERSONAL_BY_NAME: list [tuple[re.Pattern[str],
    str,
    str ] ] = [
        (re.compile(r"e[_-] ? mail "), " email ", " email address "),
        (re.compile(r" phone | mobile | cell | telephone | tel "), " tel ", " phone number "),
        (re.compile(r" first [_-] ? name | fname | given [_-] ? name | forename "), " given - name ", " first / given name "),
        (re.compile(r" last [_-] ? name | lname | family [_-] ? name | surname "), " family - name ", " last / family name "),
        (re.compile(r" ^ name $ | full [_-] ? name | your [_-] ? name "), " name ",  " full name "),
        (re.compile(r" user [_-] ? name | login | userid "), " username ", " username "),
        (re.compile(r" new [_-] ? pass "), " new - password ", " new password "),
        (re.compile(r" pass(word | wd) ?| passwd "), " current - password ", " password "),
        (re.compile(r" street | address [_-] ? line | addr [_-] ?1 "), " street - address ",  " street address "),
        (re.compile(r" city | town | locality | suburb "), " address - level2 ", " city / town "),
        (re.compile(r" \ bstate \ b | province | region "), " address - level1 ", " state / region "),
        (re.compile(r" zip | postal [_-] ? code | post [_-] ? code "), " postal - code ",  " postal / ZIP code "),
        (re.compile(r" \ bcountry \ b "), " country ", " country "),
        (re.compile(r" org(anization | anisation) ?| company | employer "), " organization ", " organisation "),
        (re.compile(r" birthday | birth [_-] ? date | date [_-] ? of [_-] ? birth | dob \ b | bday "), " bday ", " date of birth "),
        (re.compile(r" card [_-] ? num | cc [_-] ? num | credit [_-] ? card [_-] ? num "), " cc - number ", " credit card number "),
        (re.compile(r" card [_-] ? name | cc [_-] ? name | name [_-] ? on [_-] ? card "), " cc - name ", " name on card "),
        (re.compile(r" cc [_-] ? exp | card [_-] ? exp | expir "), " cc - exp ", " card expiry "),
        (re.compile(r" \ bcvv \ b | \ bcvc \ b | \ bcsc \ b | security [_-] ? code "), " cc - csc ", " card security code "),
        (re.compile(r" otp \ b | one [_-] ? time "), " one - time - code ", " one - time code "),
]

# All Recognised WHATWG autofill tokens that satisfy WCAG 1.3.5,
# autocomplete=" on " is intentionally included - it is valid and browser
# infers the pupose; not ideal but not a WCAG 1.3.5 violation.
_VALID_AUTOCOMPLETE_TOKENS = frozenset({
        " on ", " name ", " honorific - prefix ", " given - name ", " additional - name ",
        " family - name ", " honorific - suffix ", " nickname ", " username ", " new - password ",
        " current - password ", " one - time - code ", " organization - title ", " organization ",
        " street - address ", " address - line1 ", " address - line2 ", " address - line3 ",
        " address - level1 ", " address - level2 ", " address - level3 ", " address - level4 ",
        " country ", " country - name ", " postal - code ",
        " cc - name ", " cc - given - name ", " cc - additional - name ", " cc - family - name ",
        " cc - number ", " cc - exp ", " cc - exp - month ", " cc - exp - year ", " cc - csc ", " cc - type ",
        " transaction - currency ", " transaction - amount ", " language ",
        " bday ", " bday - day ", " bday - month ", " bday - year ", " sex ", " url ", " photo ",
        " tel ", " tel - country - code ", " tel - national ", " tel - area - code ",
        " tel - local ", " tel - extension ", " email ", " impp ",
        # Section and contact-type prefixes are valid modifiers (e.g. " shipping email ")
        " shipping ", " billing ", " home ", " work ", " mobile ", " fax ", " pager ",
})

# ---------------------------------------------------------------------------
# Rule implementation
# ---------------------------------------------------------------------------

def check(soup: BeautifulSoup, url: str) -> list[Violation]:
        """Return violations for personal-info inputs missing a valid autocomplete."""
        violations: list[Violation] = []

        for el in soup.find_all("input"):
            if not isinstance(el, Tag):
                continue

            input_type = str(el.get("type", "text")).lower()
            if input_type in _SKIP_INPUT_TYPES:
                continue

            # Determine if this input collects personal user information.
            hint = _detect_personal_field(el, input_type)
            if hint is None:
                continue # not a personal-info field - skip

            expected_token, field_label = hint
            autocomplete = str(el.get("autocomplete", "")).strip().lower()

            if not autocomplete:
                violations.append(
                        Violation(
                            wcag_criterion=RULE_ID,
                            criterion_name=CRITERION_NAME,
                            level=LEVEL,
                            description=(
                                f"Input collecting {field_label} has no autocomplete attribute. "
                                "Without autocomplete, browsers and assistive technologies "
                                "(e.g. Switch Access, AAC devices) cannot auto-populate the field. "
                                f"Add autocomplete=\"{expected_token}\" to this input."
                            ),
                            element=str(el)[:300],
                            severity=SEVERITY,
                            url=url,
                        )
                )
            elif autocomplete == "off":
                violations.append(
                    Violation(
                        wcag_criterion=RULE_ID,
                        criterion_name=CRITERION_NAME,
                        level=LEVEL,
                        description=(
                            f"Input collecting {field_label} has autocomplete=\"off\", "
                            "which prevents browsers and assistive technologies from "
                            "auto-populating the field. This creates a significant barrier "
                            "for users with motor or cognitive disabilities. "
                            f"Replace with autocomplete=\"{expected_token}\" unless this "
                            "field has specific security requirements (e.g. OTP, CAPTCHA)."
                        ),
                        element=str(el)[:300],
                        severity="moderate",
                        url=url,
                    )
                )
            elif not _is_valid_autocomplete(autocomplete):
                violations.append(
                    Violation(
                        wcag_criterion=RULE_ID,
                        criterion_name=CRITERION_NAME,
                        level=LEVEL,
                        description=(
                            f"Input collecting {field_label} has an invalid autocomplete value "
                            f"\"{autocomplete}\". Valid values are: "
                            f"{', '.join(_VALID_AUTOCOMPLETE_TOKENS)}."
                        ),
                    )
                )

        return violations

# ---------------------------------------------------------------------------
# Detection helpers
# ---------------------------------------------------------------------------

def _detect_personal_field(el: Tag, input_type: str) -> tuple[str, str] | None:
        """ 
        Return (expected_autocomplete_token, field_label) if the input appears to collect personal user information,
        otherwise None.
        """
        # Stage 1: type-based detection
        if input_type in _PERSONAL_INFO_TYPES:
                return _PERSONAL_INFO_TYPES[input_type]
        
        # Stage 2: heuristic name/id/placeholder-based detection
        candidates = " ".join(filter(None, [
            str(el.get(" name ", "")).lower(),
            str(el.get(" id ", "")).lower(),
            str(el.get(" placeholder ", "")).lower(),
        ]))
        
        for pattern, token, label in _PERSONAL_BY_NAME:
                if pattern.search(candidates):
                        return token, label
        
        return None # not a personal-info field

def _is_valid_autocomplete(value: str) -> bool:
        """Return True if *value* is a recognized WHATWG autofill token or
        a valid compound value (e.g. "shipping email", "billing postal-code").
        """
        # A compounded value is space-separated tokens; all must be recognized.
        parts = value.strip().split()
        return bool(parts) and all(p in _VALID_AUTOCOMPLETE_TOKENS for p in parts)