"""Page fetching module.

Provides :func:`fetch_page` which retrieves raw HTML from a URL using either:

* **httpx** (default) – fast, synchronous, zero extra runtime dependencies.
* **Playwright** (opt-in via ``use_playwright=True``) – full browser rendering for
  JavaScript-heavy SPAs.  Requires the optional ``[js]`` extras:
  ``pip install accesscheck-cli[js]``
"""

from __future__ import annotations
import httpx

# ---------------------------------------------------------------------------
# Public exception
# ---------------------------------------------------------------------------

class FetchError(RuntimeError):
    """Raised whenever a page cannot be fetched, regardless of the transport used."""


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_TIMEOUT: float = 10.0
_DEFAULT_HEADERS: dict[str, str] = {
    "User-Agent": (
        "AccessCheck-CLI/0.1 (+https://github.com/dfigurado/accessibility-cli)"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}

# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def fetch_page(
    url: str,
    *,
    cookie: str | None = None,
    use_playwright: bool = False,
    timeout: float = _TIMEOUT,
) -> str:
    """Fetch the HTML of *url* and return it as a string.

    Args:
        url:            The target URL (must include scheme, e.g. ``https://``).
        cookie:         Raw ``Cookie`` header string for authenticated sessions.
        use_playwright: When ``True``, launch a headless Chromium browser via
                        Playwright and wait for ``networkidle`` before capturing HTML.
        timeout:        Request / navigation timeout in seconds.

    Returns:
        The full HTML source of the page.

    Raises:
        :class:`FetchError`: On any network, HTTP, or browser error.
    """
    if use_playwright:
        return _fetch_with_playwright(url, cookie=cookie, timeout=timeout)
    return _fetch_with_httpx(url, cookie=cookie, timeout=timeout)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _build_headers(cookie: str | None) -> dict[str, str]:
    headers = dict(_DEFAULT_HEADERS)
    if cookie:
        headers["Cookie"] = cookie
    return headers


def _fetch_with_httpx(url: str, *, cookie: str | None, timeout: float) -> str:
    """Fetch *url* using httpx (no browser)."""
    headers = _build_headers(cookie)
    try:
        with httpx.Client(follow_redirects=True, timeout=timeout) as client:
            response = client.get(url, headers=headers)
            response.raise_for_status()
            return response.text
    except httpx.TimeoutException as exc:
        raise FetchError(f"Request timed out after {timeout}s: {url}") from exc
    except httpx.HTTPStatusError as exc:
        raise FetchError(
            f"HTTP {exc.response.status_code} error for URL: {url}"
        ) from exc
    except httpx.RequestError as exc:
        raise FetchError(f"Network error fetching {url}: {exc}") from exc


def _fetch_with_playwright(url: str, *, cookie: str | None, timeout: float) -> str:
    """Fetch *url* by launching a headless Chromium browser via Playwright."""
    try:
        from playwright.sync_api import (  # type: ignore[import]
            sync_playwright,
            TimeoutError as PWTimeout,
        )
    except ImportError as exc:
        raise FetchError(
            "Playwright is not installed. "
            "Enable JS rendering with: pip install accesscheck-cli[js]"
        ) from exc

    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            context = browser.new_context()

            if cookie:
                # Playwright requires cookies as a list of dicts; parse raw header string.
                cookies_list = []
                for part in cookie.split(";"):
                    part = part.strip()
                    if "=" in part:
                        name, _, value = part.partition("=")
                        cookies_list.append(
                            {"name": name.strip(), "value": value.strip(), "url": url}
                        )
                if cookies_list:
                    context.add_cookies(cookies_list)

            page = context.new_page()
            page.goto(url, timeout=int(timeout * 1000), wait_until="networkidle")
            html = page.content()
            browser.close()
            return html
    except PWTimeout as exc:
        raise FetchError(f"Playwright timed out loading: {url}") from exc
    except Exception as exc:  # noqa: BLE001
        raise FetchError(f"Playwright error for {url}: {exc}") from exc