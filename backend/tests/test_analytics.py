"""Tests for backend analytics helpers."""

import builtins
import runpy
import types
from unittest.mock import Mock

import pytest

from api_app import analytics


def test_log_umami_page_normalizes_optional_fields(monkeypatch):
    called: dict[str, str] = {}
    fake_umami = types.SimpleNamespace()

    def set_url_base(value: str) -> None:
        called["url_base"] = value

    def set_website_id(value: str) -> None:
        called["website_id"] = value

    def new_page_view(**kwargs) -> None:
        called.update(kwargs)

    fake_umami.set_url_base = set_url_base
    fake_umami.set_website_id = set_website_id
    fake_umami.new_page_view = new_page_view

    monkeypatch.setattr(analytics, "umami", fake_umami)
    analytics.log_umami_page(
        url="/api/v1/companies",
        hostname="appgoblin.info",
        referrer=None,
        ip="203.0.113.1",
        user_id=7,
    )

    assert called["hostname"] == "appgoblin.info"
    assert called["referrer"] == ""
    assert called["ip_address"] == "203.0.113.1"
    assert called["distinct_id"] == "7"


def test_missing_umami_skips_analytics_without_logging(monkeypatch):
    original_import = builtins.__import__
    import_attempts = 0

    def import_without_umami(name, *args, **kwargs):
        nonlocal import_attempts
        if name == "umami":
            import_attempts += 1
            raise ModuleNotFoundError("No module named 'umami'", name="umami")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", import_without_umami)
    module = runpy.run_path(analytics.__file__)
    logger = Mock()
    monkeypatch.setitem(module["log_umami_page"].__globals__, "logger", logger)

    module["log_umami_page"](url="/first")
    module["log_umami_page"](url="/second")

    assert import_attempts == 1
    logger.exception.assert_not_called()


def test_missing_umami_dependency_is_not_suppressed(monkeypatch):
    original_import = builtins.__import__

    def import_with_missing_dependency(name, *args, **kwargs):
        if name == "umami":
            raise ModuleNotFoundError("No module named 'dependency'", name="dependency")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", import_with_missing_dependency)
    with pytest.raises(ModuleNotFoundError, match="dependency"):
        runpy.run_path(analytics.__file__)
