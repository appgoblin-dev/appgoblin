"""Tests for company-scoped recent API observations."""

from unittest.mock import MagicMock, patch

from litestar import Litestar
from litestar.testing import TestClient

import pandas as pd
import pytest
from sqlalchemy import create_engine, event

from api_app.controllers.companies import (
    CompaniesController,
    _build_company_recent_api_activity,
)
from dbcon.queries import get_company_recent_api_activity


@pytest.fixture
def state():
    engine = create_engine("sqlite://")
    with engine.begin() as conn:
        conn.exec_driver_sql("ATTACH DATABASE ':memory:' AS adtech")
        for statement in [
            "CREATE TABLE domains (id INTEGER, domain_name TEXT)",
            "CREATE TABLE adtech.companies (id INTEGER, domain_id INTEGER, parent_company_id INTEGER)",
            "CREATE TABLE adtech.company_domain_mapping (company_id INTEGER, domain_id INTEGER)",
            "CREATE TABLE store_apps (id INTEGER, store INTEGER, store_id TEXT, name TEXT, icon_64 TEXT)",
            "CREATE TABLE version_codes (id INTEGER, store_app INTEGER)",
            "CREATE TABLE version_code_api_scan_results (id INTEGER, version_code_id INTEGER, run_at TEXT)",
            "CREATE TABLE api_calls (id INTEGER, tld_url TEXT, url TEXT, called_at TEXT, run_id INTEGER, store_app INTEGER, request_mime_type TEXT, response_mime_type TEXT)",
        ]:
            conn.exec_driver_sql(statement)
        conn.exec_driver_sql("INSERT INTO domains VALUES (1,'parent.com'),(2,'child.com'),(3,'alias.com'),(4,'other.com')")
        conn.exec_driver_sql("INSERT INTO adtech.companies VALUES (1,1,NULL),(2,2,1),(3,4,NULL)")
        conn.exec_driver_sql("INSERT INTO adtech.company_domain_mapping VALUES (1,1),(2,2),(2,3),(3,4)")
        conn.exec_driver_sql("INSERT INTO store_apps VALUES (1,1,'a','A',NULL),(2,1,'b','B',NULL),(3,1,'c','C',NULL),(4,2,'ios','iOS',NULL)")
        conn.exec_driver_sql("INSERT INTO version_codes VALUES (1,1),(2,2),(3,3),(4,4)")
        conn.exec_driver_sql("INSERT INTO version_code_api_scan_results VALUES (1,1,'2026-01-01'),(2,2,'2026-02-01'),(3,3,'2026-03-01'),(4,4,'2026-04-01')")
        conn.exec_driver_sql("INSERT INTO api_calls (id, tld_url, url, called_at, run_id, store_app) VALUES (1,'parent.com','parent.com/api','2026-01-01',1,1),(2,'alias.com','alias.com/api','2026-02-01',2,2),(3,'other.com','other.com/api','2026-03-01',3,3),(4,'child.com','child.com/api','2026-01-02',1,1),(5,'alias.com','alias.com/v2','2026-04-01',4,4),(6,'alias.com','alias.com/v3','2026-05-01',NULL,NULL),(7,'alias.com','alias.com/v4','2026-06-01',NULL,999)")
    result = MagicMock()
    result.dbcon.engine = engine
    result.static_data.company_secondary_domains = ["alias.com"]
    result.static_data.parent_companies = ["parent.com"]
    yield result
    engine.dispose()


@pytest.mark.parametrize(
    ("domain", "call_domains", "app_ids"),
    [
        ("parent.com", ["alias.com", "child.com", "parent.com"], ["b", "a"]),
        ("child.com", ["alias.com", "child.com"], ["b", "a"]),
        ("alias.com", ["alias.com"], ["b"]),
        ("missing.com", [], []),
    ],
)
def test_activity_scope_and_order(state, domain, call_domains, app_ids):
    calls = get_company_recent_api_activity(state, domain)
    assert calls.tld_url.tolist() == call_domains
    endpoints, requests = _build_company_recent_api_activity(calls)
    assert list(dict.fromkeys(request["store_id"] for request in requests)) == app_ids
    assert [endpoint["host"] for endpoint in endpoints] == call_domains


def test_only_calls_query_runs_and_same_app_requests_are_retained(state):
    with state.dbcon.engine.begin() as conn:
        conn.exec_driver_sql(
            "INSERT INTO api_calls (id, tld_url, url, called_at, store_app) VALUES "
            "(8, 'alias.com', 'alias.com/api?order=8', '2026-02-01', 2), "
            "(9, 'alias.com', 'alias.com/api?order=9', '2026-02-01', 2)"
        )
        conn.exec_driver_sql("UPDATE store_apps SET name=NULL WHERE id=2")
    statements = []

    def record_query(conn, cursor, statement, parameters, context, executemany):
        statements.append(statement)

    event.listen(state.dbcon.engine, "before_cursor_execute", record_query)
    try:
        calls = get_company_recent_api_activity(state, "alias.com")
    finally:
        event.remove(state.dbcon.engine, "before_cursor_execute", record_query)
    assert len(statements) == 1
    assert "api_calls" in statements[0]
    assert "version_code_api_scan_results" not in statements[0]
    assert calls.url.tolist() == ["alias.com/api?order=9", "alias.com/api?order=8", "alias.com/api"]
    endpoints, requests = _build_company_recent_api_activity(calls)
    assert len(endpoints) == 1
    assert len(requests) == 3
    assert all(request["store_id"] == "b" and request["name"] is None for request in requests)


def test_missing_store_id_is_excluded_before_limiting(state):
    with state.dbcon.engine.begin() as conn:
        conn.exec_driver_sql("INSERT INTO store_apps VALUES (5, 1, NULL, 'Missing', NULL)")
        conn.exec_driver_sql(
            "INSERT INTO api_calls (id, tld_url, url, called_at, store_app) VALUES "
            "(?, 'alias.com', 'alias.com/missing', '2027-01-01', 5)",
            [(i,) for i in range(100, 1100)],
        )
    calls = get_company_recent_api_activity(state, "alias.com")
    assert calls.store_id.tolist() == ["b"]
    endpoints, requests = _build_company_recent_api_activity(calls)
    assert [request["store_id"] for request in requests] == ["b"]
    assert [endpoint["path"] for endpoint in endpoints] == ["/api"]


def test_only_ios_activity_returns_empty(state):
    with state.dbcon.engine.begin() as conn:
        conn.exec_driver_sql("DELETE FROM api_calls WHERE store_app != 4 OR store_app IS NULL")
    calls = get_company_recent_api_activity(state, "alias.com")
    assert calls.empty


def test_response_exposes_observed_endpoint(state):
    calls = get_company_recent_api_activity(state, "parent.com")
    calls.loc[0, "url"] = "https://user:secret@api.alias.com/api/users?token=private"
    calls.loc[0, "request_mime_type"] = "application/json"
    calls.loc[0, "response_mime_type"] = "text/plain"
    frame = pd.DataFrame(columns=["store", "store_id", "name"])
    with (
        patch("api_app.controllers.companies.get_api_apps_for_company", return_value=frame),
        patch("api_app.controllers.companies.get_company_recent_api_activity", return_value=calls),
        patch("api_app.controllers.companies.get_company_api_response_types", return_value=[]),
        TestClient(app=Litestar(route_handlers=[CompaniesController])) as client,
    ):
        response = client.get("/api/companies/parent.com/api-apps")
    assert response.status_code == 200
    payload = response.json()
    assert payload["recent_endpoints"][0] == {
        "host": "api.alias.com", "path": "/api/users", "last_seen": "2026-02-01T00:00:00"
    }
    assert payload["recent_requests"][0] == {
        "host": "api.alias.com", "path": "/api/users", "called_at": "2026-02-01T00:00:00",
        "store_id": "b", "name": "B", "icon_64": None,
        "request_mime_type": "application/json", "response_mime_type": "text/plain",
    }
    assert "private" not in response.text
    assert "secret" not in response.text


def test_endpoint_host_path_and_deduplication():
    calls = pd.DataFrame([
        {"url": "https://user:password@api.example.com:8443/v1/users?token=x#fragment", "called_at": "2026-02-02"},
        {"url": "https://api.example.com:8443/v1/users?token=y", "called_at": "2026-02-01"},
        {"url": "api.example.com/v1/orders", "called_at": "2026-01-31"},
        {"url": "api.example.com/v1/orders/123/details", "called_at": "2026-01-30"},
        {"url": "api.example.com/" + "x" * 200, "called_at": "2026-01-29"},
        {"url": "api.example.com/" + "y" * 104, "called_at": "2026-01-28"},
        {"url": "api.example.com/v1/orders/", "called_at": "2026-01-27"},
        {"url": "api.example.com/v1/orders/456", "called_at": "2026-01-26"},
        {"url": None, "called_at": "2026-01-25"},
    ])
    calls = calls.assign(store_id=None, name=None, icon_64=None, request_mime_type=None, response_mime_type=None)
    endpoints, requests = _build_company_recent_api_activity(calls)
    assert [(request["host"], request["path"]) for request in requests[:2]] == [
        ("api.example.com:8443", "/v1/users"),
        ("api.example.com:8443", "/v1/users"),
    ]
    assert requests[3]["path"] == "/v1/orders/..."
    assert len(requests[4]["host"] + requests[4]["path"]) == 120
    assert endpoints == [
        {"host": "api.example.com:8443", "path": "/v1/users", "last_seen": "2026-02-02T00:00:00"},
        {"host": "api.example.com", "path": "/v1/orders", "last_seen": "2026-01-31T00:00:00"},
        {"host": "api.example.com", "path": "/v1/orders/...", "last_seen": "2026-01-30T00:00:00"},
        {"host": "api.example.com", "path": "/" + "x" * 101 + "...", "last_seen": "2026-01-29T00:00:00"},
        {"host": "api.example.com", "path": "/" + "y" * 104, "last_seen": "2026-01-28T00:00:00"},
        {"host": "api.example.com", "path": "/v1/orders/", "last_seen": "2026-01-27T00:00:00"},
    ]
    assert all(len(endpoint["host"] + endpoint["path"]) <= 120 for endpoint in endpoints)


def test_query_samples_are_bounded(state):
    with state.dbcon.engine.begin() as conn:
        conn.exec_driver_sql(
            "INSERT INTO api_calls (id, tld_url, url, called_at, run_id, store_app) VALUES (?, 'alias.com', 'alias.com/api', ?, 2, 2)",
            [(i, f"2027-01-01T00:{i // 60:02d}:{i % 60:02d}") for i in range(100, 1101)],
        )
    calls = get_company_recent_api_activity(state, "alias.com")
    assert len(calls) == 1000
    assert calls.called_at.iloc[0] > calls.called_at.iloc[-1]


def test_bounded_deduplicated_activity():
    calls = pd.DataFrame([
        {"url": f"example.com/api/{i}", "tld_url": "example.com", "called_at": f"2026-01-{i + 1:02d}"}
        for i in reversed(range(25))
    ])
    calls = calls.assign(store_id="same-app", name=None, icon_64=None, request_mime_type=None, response_mime_type=None)
    endpoints, requests = _build_company_recent_api_activity(calls)
    assert len(endpoints) == 20
    assert endpoints[0] == {"host": "example.com", "path": "/api/24", "last_seen": "2026-01-25T00:00:00"}
    assert endpoints[-1]["path"] == "/api/5"
    assert len(requests) == 20
    assert all(request["store_id"] == "same-app" for request in requests)
    assert requests[0]["called_at"] == "2026-01-25T00:00:00"
    assert requests[-1]["called_at"] == "2026-01-06T00:00:00"
    assert requests[0]["name"] is None
    assert requests[0]["response_mime_type"] is None

    repeated = pd.concat([calls.iloc[[0]]] * 20 + [calls.iloc[[1]]], ignore_index=True)
    endpoints, requests = _build_company_recent_api_activity(repeated)
    assert len(requests) == 20
    assert [endpoint["path"] for endpoint in endpoints] == ["/api/24", "/api/23"]

    calls["tld_url"] = [f"domain{i}.com" for i in range(25)]
    calls["url"] = calls["tld_url"] + "/api"
    endpoints, _ = _build_company_recent_api_activity(calls)
    assert len(endpoints) == 20
    assert endpoints[0]["last_seen"] == "2026-01-25T00:00:00"
