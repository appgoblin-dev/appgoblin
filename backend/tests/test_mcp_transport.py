"""Regression tests for the mounted MCP transport (no database or Redis)."""

import asyncio
import json
import sys
import threading
import types
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import pytest
from litestar import Litestar
from litestar.testing import TestClient

from api_app.guards import _CachedKey
from api_app.mcp import controller
from api_app.mcp.docs import _build_tools_docs, _render_tool_row
from app import mcp_asgi_handler

MCP_PATH = "/api/v1/mcp"
HEADERS = {
    "accept": "application/json, text/event-stream",
    "authorization": "Bearer ag_test",
}
INITIALIZE = {
    "jsonrpc": "2.0",
    "id": 1,
    "method": "initialize",
    "params": {
        "protocolVersion": "2025-06-18",
        "capabilities": {},
        "clientInfo": {"name": "pytest", "version": "0"},
    },
}
LIST_TOOLS = {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}


@asynccontextmanager
async def _mcp_lifespan(_app: Litestar) -> AsyncGenerator[None]:
    # session_manager.run() can only be entered once per process.
    async with controller.mcp_server.session_manager.run():
        yield


@pytest.mark.parametrize(
    ("daily_ok", "minute_ok", "expected_status"),
    [(True, True, 200), (False, True, 429), (True, False, 429)],
)
def test_quota_checked_requests_schedule_umami_page_view(
    monkeypatch, daily_ok, minute_ok, expected_status
) -> None:
    monkeypatch.setattr("api_app.guards._KEY_CACHE", {})
    monkeypatch.setattr(controller, "get_engine", lambda: None)
    monkeypatch.setattr(controller, "_query_key", lambda *_: _CachedKey(7, "free", 9e12))
    monkeypatch.setattr(
        controller, "_check_daily_quota", lambda _key, limit: (daily_ok, limit, 0)
    )
    monkeypatch.setattr(
        controller,
        "_check_minute_limit",
        lambda _key, limit: (minute_ok, limit, 0, 1),
    )
    views = []
    completed = threading.Event()

    def capture_page_view(**kwargs):
        views.append(kwargs)
        completed.set()

    monkeypatch.setattr(controller, "log_umami_page", capture_page_view)

    async def exercise():
        messages = []

        async def send(message):
            messages.append(message)

        async def downstream(scope, receive, send):
            await send({"type": "http.response.start", "status": 200, "headers": []})

        scope = {
            "type": "http",
            "method": "POST",
            "headers": [
                (b"x-api-key", b"ag_analytics"),
                (b"x-forwarded-for", b"203.0.113.1, 10.0.0.1"),
            ],
            "client": ("127.0.0.1", 1234),
        }
        await controller.AuthenticatedMCPMiddleware(downstream)(scope, None, send)
        return messages[0]["status"]

    assert asyncio.run(exercise()) == expected_status
    assert completed.wait(2)
    assert views == [{
        "url": "/api/v1/mcp",
        "hostname": "appgoblin.info",
        "ip": "203.0.113.1",
        "user_id": 7,
    }]


def test_invalid_key_does_not_schedule_umami(monkeypatch) -> None:
    monkeypatch.setattr("api_app.guards._KEY_CACHE", {})
    monkeypatch.setattr(controller, "get_engine", lambda: None)
    monkeypatch.setattr(controller, "_query_key", lambda *_: None)
    views = []
    monkeypatch.setattr(controller, "_track_mcp_request", lambda *args: views.append(args))
    assert controller._authenticate({"headers": [(b"x-api-key", b"bad")]}) is None
    assert views == []


def test_redis_failure_does_not_schedule_umami(monkeypatch) -> None:
    from litestar.exceptions import ServiceUnavailableException

    monkeypatch.setattr("api_app.guards._KEY_CACHE", {})
    monkeypatch.setattr(controller, "get_engine", lambda: None)
    monkeypatch.setattr(controller, "_query_key", lambda *_: _CachedKey(7, "free", 9e12))
    views = []
    monkeypatch.setattr(controller, "_track_mcp_request", lambda *args: views.append(args))

    def fail_daily_quota(*args):
        raise ServiceUnavailableException(detail="Rate limiting unavailable")

    monkeypatch.setattr(controller, "_check_daily_quota", fail_daily_quota)
    with pytest.raises(ServiceUnavailableException):
        controller._authenticate({"headers": [(b"x-api-key", b"ag_redis")]})
    assert views == []


def test_umami_failure_does_not_block_mcp_response(monkeypatch) -> None:
    monkeypatch.setattr("api_app.guards._KEY_CACHE", {})
    monkeypatch.setattr(controller, "get_engine", lambda: None)
    monkeypatch.setattr(controller, "_query_key", lambda *_: _CachedKey(7, "free", 9e12))
    monkeypatch.setattr(controller, "_check_daily_quota", lambda _key, limit: (True, limit, 1))
    monkeypatch.setattr(controller, "_check_minute_limit", lambda _key, limit: (True, limit, 1, 0))
    started = threading.Event()
    release = threading.Event()
    semaphore = threading.BoundedSemaphore(1)
    monkeypatch.setattr(controller, "_ANALYTICS_SLOTS", semaphore)
    from api_app import analytics

    monkeypatch.setitem(analytics.CONFIG, "umami", {"base_url": "test", "site_id": "test"})

    def failing_page_view(**kwargs):
        started.set()
        if not release.wait(5):
            raise TimeoutError("test did not release analytics")
        raise OSError("Umami unavailable")

    monkeypatch.setitem(
        sys.modules,
        "umami",
        types.SimpleNamespace(
            set_url_base=lambda _: None,
            set_website_id=lambda _: None,
            new_page_view=failing_page_view,
        ),
    )

    async def exercise():
        messages = []

        async def send(message):
            messages.append(message)

        async def downstream(scope, receive, send):
            await send({"type": "http.response.start", "status": 200, "headers": []})

        await controller.AuthenticatedMCPMiddleware(downstream)(
            {"type": "http", "method": "POST", "headers": [(b"x-api-key", b"ag_slow")]},
            None,
            send,
        )
        return messages[0]["status"]

    try:
        assert asyncio.run(exercise()) == 200
        assert started.wait(2)
        assert not semaphore.acquire(blocking=False)
        controller._track_mcp_request({}, 7)
    finally:
        release.set()
        assert semaphore.acquire(timeout=2)
        semaphore.release()


def test_analytics_scheduling_failure_does_not_break_authentication(monkeypatch):
    monkeypatch.setattr("api_app.guards._KEY_CACHE", {})
    monkeypatch.setattr(controller, "get_engine", lambda: None)
    monkeypatch.setattr(controller, "_query_key", lambda *_: _CachedKey(7, "free", 9e12))
    monkeypatch.setattr(controller, "_check_daily_quota", lambda _key, limit: (True, limit, 1))
    monkeypatch.setattr(controller, "_check_minute_limit", lambda _key, limit: (True, limit, 1, 0))

    semaphore = threading.BoundedSemaphore(1)
    monkeypatch.setattr(controller, "_ANALYTICS_SLOTS", semaphore)

    def fail(*args, **kwargs):
        raise RuntimeError("scheduling failure")

    monkeypatch.setattr(controller.threading.Thread, "start", fail)
    assert controller._authenticate({"headers": [(b"x-api-key", b"ag_fail")]}).user_id == 7
    assert semaphore.acquire(blocking=False)
    semaphore.release()


def test_keyword_tool_docs_show_free_tier() -> None:
    docs = asyncio.run(_build_tools_docs())
    assert docs["tier_access"]["keywords"] == "All tiers (free and paid)."
    tools = {tool["name"]: tool for tool in docs["tools"]}
    for name in ("get_keyword_metrics", "get_keyword_ranks"):
        assert "paid-tier" not in tools[name]["description"]
        assert '<span class="badge badge-free">free</span>' in _render_tool_row(
            tools[name]
        )
    assert '<span class="badge badge-paid">paid</span>' in _render_tool_row(
        tools["get_company_overview"]
    )


def test_search_tools_are_registered_with_access_and_limits() -> None:
    docs = asyncio.run(_build_tools_docs())
    tools = {tool["name"]: tool for tool in docs["tools"]}
    for name in ("search_apps", "search_developer_apps", "search_companies"):
        assert tools[name]["parameters"]["q"]["required"]
        assert tools[name]["parameters"]["limit"]["default"] == 20
    assert '<span class="badge badge-paid">paid</span>' in _render_tool_row(
        tools["search_companies"]
    )


def test_app_metrics_history_tools_are_registered_for_all_tiers() -> None:
    docs = asyncio.run(_build_tools_docs())
    tools = {tool["name"]: tool for tool in docs["tools"]}
    assert docs["tier_access"]["apps"] == "All tiers (free and paid)."
    for name in (
        "get_app_global_metrics_history",
        "get_app_country_metrics_history",
        "get_app_rank_history",
    ):
        assert tools[name]["parameters"]["store_id"]["required"]
        assert "paid-tier" not in tools[name]["description"]
    assert tools["get_app_rank_history"]["parameters"]["country"]["default"] == "US"


def test_app_metrics_history_tools_return_shared_payloads(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from api_app.mcp.tools import apps

    monkeypatch.setattr(apps, "get_mcp_state", lambda: None)
    monkeypatch.setattr(
        apps,
        "_build_app_global_metrics_history_payload",
        lambda state, store_id: [{"store_id": store_id, "scope": "global"}],
    )
    monkeypatch.setattr(
        apps,
        "_build_app_country_metrics_history_payload",
        lambda state, store_id: [{"store_id": store_id, "scope": "country"}],
    )
    monkeypatch.setattr(
        apps,
        "_build_app_rank_history_payload",
        lambda state, store_id, country="US": {
            "history": [{"store_id": store_id, "country": country}]
        },
    )

    global_result = asyncio.run(
        apps.get_app_global_metrics_history("com.example.app", object())
    )
    country_result = asyncio.run(
        apps.get_app_country_metrics_history("com.example.app", object())
    )
    rank_result = asyncio.run(
        apps.get_app_rank_history("com.example.app", object(), country="GB")
    )

    assert json.loads(global_result) == [
        {"store_id": "com.example.app", "scope": "global"}
    ]
    assert json.loads(country_result) == [
        {"store_id": "com.example.app", "scope": "country"}
    ]
    assert json.loads(rank_result) == {
        "history": [{"store_id": "com.example.app", "country": "GB"}]
    }


def test_company_search_tool_paid_access(monkeypatch: pytest.MonkeyPatch) -> None:
    from api_app.mcp.tools import companies

    seen = []
    monkeypatch.setattr(companies, "assert_paid_tier", lambda ctx, name: seen.append(name))
    monkeypatch.setattr(companies, "get_mcp_state", lambda: None)
    monkeypatch.setattr(
        companies, "_search_companies_payload",
        lambda state, term, limit: [{"term": term, "limit": limit}],
    )
    payload = asyncio.run(companies.search_companies("example", object(), 7))
    assert seen == ["search_companies"]
    assert json.loads(payload) == [{"term": "example", "limit": 7}]


def test_mcp_serves_any_host_without_a_session(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Proxied hosts connect, and requests work on any worker with no session."""
    monkeypatch.setattr(controller, "get_engine", lambda: None)
    monkeypatch.setattr(
        controller, "_query_key", lambda *_: _CachedKey(1, "free", 9e12)
    )
    monkeypatch.setattr(
        controller, "_check_daily_quota", lambda _k, limit: (True, limit, limit)
    )
    monkeypatch.setattr(
        controller, "_check_minute_limit", lambda _k, limit: (True, limit, limit, 0)
    )
    monkeypatch.setattr("api_app.guards._KEY_CACHE", {})
    tracked_users = []
    monkeypatch.setattr(
        controller, "_track_mcp_request", lambda _scope, user: tracked_users.append(user)
    )

    monkeypatch.setattr("api_app.mcp.tools.keywords.get_mcp_state", lambda: None)
    monkeypatch.setattr(
        "api_app.mcp.tools.keywords._build_keyword_metrics_payload",
        lambda **_: {"keyword": "test"},
    )
    monkeypatch.setattr(
        "api_app.mcp.tools.keywords._build_keyword_ranks_payload",
        lambda **_: {"keyword": "test", "android": [], "ios": []},
    )

    monkeypatch.setattr("api_app.mcp.tools.apps.get_mcp_state", lambda: None)
    monkeypatch.setattr(
        "api_app.mcp.tools.apps._search_apps_payload",
        lambda state, term, limit, **kwargs: [
            {"term": term, "developer": kwargs.get("developer", False)}
        ],
    )
    monkeypatch.setattr("api_app.mcp.tools.companies.get_mcp_state", lambda: None)
    monkeypatch.setattr(
        "api_app.mcp.tools.companies._search_companies_payload",
        lambda state, term, limit: [{"term": term}],
    )

    app = Litestar(route_handlers=[mcp_asgi_handler], lifespan=[_mcp_lifespan])
    with TestClient(app=app) as client:
        for host in ("appgoblin.info", "appgoblin_api", "127.0.0.1:8000"):
            response = client.post(
                MCP_PATH, json=INITIALIZE, headers={**HEADERS, "host": host}
            )
            assert response.status_code == 200, host
        assert (
            client.post(MCP_PATH, json=LIST_TOOLS, headers=HEADERS).status_code == 200
        )
        for name in ("get_keyword_metrics", "get_keyword_ranks"):
            response = client.post(
                MCP_PATH,
                headers=HEADERS,
                json={
                    "jsonrpc": "2.0",
                    "id": 3,
                    "method": "tools/call",
                    "params": {"name": name, "arguments": {"keyword": "test"}},
                },
            )
            assert response.status_code == 200
            data = next(
                line[6:]
                for line in response.text.splitlines()
                if line.startswith("data: ")
            )
            result = json.loads(data)["result"]
            assert not result.get("isError", False)
            assert json.loads(result["content"][0]["text"])["keyword"] == "test"
        for name in ("search_apps", "search_developer_apps", "search_companies"):
            response = client.post(
                MCP_PATH,
                headers=HEADERS,
                json={
                    "jsonrpc": "2.0",
                    "id": 4,
                    "method": "tools/call",
                    "params": {"name": name, "arguments": {"q": "example"}},
                },
            )
            data = next(
                line[6:]
                for line in response.text.splitlines()
                if line.startswith("data: ")
            )
            result = json.loads(data)["result"]
            if name == "search_companies":
                assert result.get("isError") is True
            else:
                assert not result.get("isError", False)
                assert json.loads(result["content"][0]["text"])[0] == {
                    "term": "example",
                    "developer": name == "search_developer_apps",
                }
        assert client.get(MCP_PATH, headers=HEADERS).status_code == 405
    assert tracked_users == [1] * 10
