"""Regression tests for the mounted MCP transport (no database or Redis)."""

import asyncio
import json
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
