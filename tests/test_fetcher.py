"""Unit tests for src.fetcher — fetch_page, _build_headers, and FetchError."""
import builtins

import httpx
import pytest

from src.fetcher import FetchError, _DEFAULT_HEADERS, _build_headers, fetch_page


# ---------------------------------------------------------------------------
# _build_headers
# ---------------------------------------------------------------------------

class TestBuildHeaders:
    def test_returns_default_headers_without_cookie(self):
        headers = _build_headers(None)
        assert "User-Agent" in headers
        assert "Accept" in headers
        assert "Cookie" not in headers

    def test_adds_cookie_header_when_provided(self):
        headers = _build_headers("session=abc123")
        assert headers["Cookie"] == "session=abc123"

    def test_does_not_mutate_module_defaults(self):
        _build_headers("session=abc")
        assert "Cookie" not in _DEFAULT_HEADERS

    def test_user_agent_references_project(self):
        headers = _build_headers(None)
        assert "AccessCheck" in headers["User-Agent"]


# ---------------------------------------------------------------------------
# fetch_page — httpx transport (mocked)
# ---------------------------------------------------------------------------

class TestFetchPageHttpx:
    def test_success_returns_html_text(self, httpx_mock):
        httpx_mock.add_response(text="<html><body>Hello</body></html>")
        result = fetch_page("https://example.com")
        assert result == "<html><body>Hello</body></html>"

    def test_timeout_raises_fetch_error(self, httpx_mock):
        httpx_mock.add_exception(httpx.TimeoutException("timed out"))
        with pytest.raises(FetchError, match="timed out"):
            fetch_page("https://example.com")

    def test_http_404_raises_fetch_error(self, httpx_mock):
        httpx_mock.add_response(status_code=404)
        with pytest.raises(FetchError, match="HTTP 404"):
            fetch_page("https://example.com")

    def test_http_500_raises_fetch_error(self, httpx_mock):
        httpx_mock.add_response(status_code=500)
        with pytest.raises(FetchError, match="HTTP 500"):
            fetch_page("https://example.com")

    def test_network_error_raises_fetch_error(self, httpx_mock):
        httpx_mock.add_exception(httpx.ConnectError("connection refused"))
        with pytest.raises(FetchError, match="Network error"):
            fetch_page("https://example.com")

    def test_cookie_is_forwarded_in_request(self, httpx_mock):
        httpx_mock.add_response(text="<html></html>")
        fetch_page("https://example.com", cookie="token=xyz")
        request = httpx_mock.get_requests()[0]
        assert request.headers["Cookie"] == "token=xyz"

    def test_no_cookie_omits_cookie_header(self, httpx_mock):
        httpx_mock.add_response(text="<html></html>")
        fetch_page("https://example.com")
        request = httpx_mock.get_requests()[0]
        assert "cookie" not in {k.lower() for k in request.headers}

    def test_fetch_error_is_runtime_error_subclass(self):
        assert issubclass(FetchError, RuntimeError)


# ---------------------------------------------------------------------------
# fetch_page — Playwright transport (import-mocked)
# ---------------------------------------------------------------------------

class TestFetchPagePlaywright:
    def test_playwright_not_installed_raises_fetch_error(self, monkeypatch):
        real_import = builtins.__import__

        def mock_import(name, *args, **kwargs):
            if name == "playwright.sync_api":
                raise ImportError("No module named 'playwright'")
            return real_import(name, *args, **kwargs)

        monkeypatch.setattr(builtins, "__import__", mock_import)
        with pytest.raises(FetchError, match="Playwright is not installed"):
            fetch_page("https://example.com", use_playwright=True)
