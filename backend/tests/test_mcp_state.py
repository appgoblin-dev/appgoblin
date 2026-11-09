"""Regression tests for MCP application state and database lifecycle."""

import asyncio
from contextlib import asynccontextmanager
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from litestar.datastructures import State

import app as app_module
from api_app.mcp import controller, engine, state
from api_app.mcp.tools import companies
from dbcon.static import get_company_logos_df, get_company_trends_summary


def test_company_tools_use_preloaded_static_data(monkeypatch):
    logos = object()
    trend = object()
    app_state = State(
        {
            "dbcon": SimpleNamespace(engine=object()),
            "dbconwrite": SimpleNamespace(engine=object()),
            "static_data": SimpleNamespace(
                company_logos_df=logos, company_trends_summaries={"example.com": trend}
            ),
        }
    )
    monkeypatch.setattr(state, "_mcp_state", app_state)
    monkeypatch.setattr(companies, "assert_paid_tier", lambda *_: None)

    def get_overviews(*, state):
        assert get_company_logos_df(state) is logos
        return SimpleNamespace(companies_overview=[])

    def get_overview(*, state, company_domain):
        assert get_company_trends_summary(state, company_domain) is trend
        return {"domain": company_domain}

    monkeypatch.setattr(companies, "get_overviews", get_overviews)
    monkeypatch.setattr(
        companies, "_build_public_company_overview_payload", get_overview
    )
    assert asyncio.run(companies.list_companies(None)) == "[]"
    assert "example.com" in asyncio.run(
        companies.get_company_overview("example.com", None)
    )


def test_lifespan_injects_and_clears_distinct_connections(monkeypatch):
    read_engine = MagicMock()
    write_engine = MagicMock()
    static_data = object()
    app_state = State(
        {
            "dbcon": SimpleNamespace(engine=read_engine),
            "dbconwrite": SimpleNamespace(engine=write_engine),
        }
    )
    monkeypatch.setattr(state, "_mcp_state", None)
    monkeypatch.setattr(engine, "_engine", None)
    monkeypatch.setattr(app_module, "load_static_data", lambda db: static_data)

    @asynccontextmanager
    async def session_run():
        yield

    monkeypatch.setattr(app_module.mcp_server.session_manager, "run", session_run)

    async def exercise():
        async with app_module.db_lifespan(SimpleNamespace(state=app_state)):
            assert state.get_mcp_state() is app_state
            assert state.get_mcp_state().dbcon.engine is read_engine
            assert state.get_mcp_state().dbconwrite.engine is write_engine
            assert state.get_mcp_state().static_data is static_data
            assert engine.get_engine() is write_engine
            monkeypatch.setattr("api_app.guards._KEY_CACHE", {})
            query_key = MagicMock(return_value=None)
            monkeypatch.setattr(controller, "_query_key", query_key)
            assert (
                controller._authenticate(
                    {"type": "http", "headers": [(b"authorization", b"Bearer test")]}
                )
                is None
            )
            assert query_key.call_args.args[0] is write_engine
        with pytest.raises(RuntimeError, match="state not initialised"):
            state.get_mcp_state()
        with pytest.raises(engine.MCPDatabaseUnavailableError):
            engine.get_engine()

    asyncio.run(exercise())
    read_engine.dispose.assert_called_once()
    write_engine.dispose.assert_called_once()


def test_missing_write_connection_does_not_reuse_stale_engine(monkeypatch):
    app_state = State({"dbcon": SimpleNamespace(engine=MagicMock())})
    monkeypatch.setattr(state, "_mcp_state", None)
    monkeypatch.setattr(engine, "_engine", MagicMock())
    monkeypatch.setattr(app_module, "load_static_data", lambda _: object())

    def fail_connection(**_kwargs):
        raise OSError("write database unavailable")

    @asynccontextmanager
    async def session_run():
        yield

    monkeypatch.setattr(app_module, "get_db_connection", fail_connection)
    monkeypatch.setattr(app_module.mcp_server.session_manager, "run", session_run)

    async def exercise():
        async with app_module.db_lifespan(SimpleNamespace(state=app_state)):
            assert state.get_mcp_state() is app_state
            assert app_state.dbconwrite is None
            scope = {
                "type": "http",
                "method": "POST",
                "headers": [(b"authorization", b"Bearer test")],
            }
            with pytest.raises(engine.MCPDatabaseUnavailableError):
                controller._authenticate(scope)
            messages = []

            async def send(message):
                messages.append(message)

            async def receive():
                return {"type": "http.request"}

            await controller.AuthenticatedMCPMiddleware(None)(scope, receive, send)
            assert messages[0]["status"] == 503
            assert messages[1]["body"] == b'{"error":"API key validation unavailable"}'

    asyncio.run(exercise())
