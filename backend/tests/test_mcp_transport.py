"""Regression tests for the mounted MCP transport (no database or Redis)."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import pytest
from litestar import Litestar
from litestar.testing import TestClient

from api_app.guards import _CachedKey
from api_app.mcp import controller
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
        assert client.get(MCP_PATH, headers=HEADERS).status_code == 405
