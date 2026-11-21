"""Tests for company-scoped response type materialized-view rows."""

from unittest.mock import MagicMock, patch

import pandas as pd
import pytest
from litestar import Litestar
from litestar.testing import TestClient
from sqlalchemy import create_engine

from api_app.controllers.companies import CompaniesController
from dbcon.queries import get_company_api_response_types


@pytest.fixture
def state():
    engine = create_engine("sqlite://")
    with engine.begin() as conn:
        conn.exec_driver_sql("ATTACH DATABASE ':memory:' AS adtech")
        conn.exec_driver_sql("ATTACH DATABASE ':memory:' AS frontend")
        conn.exec_driver_sql("CREATE TABLE domains (id INTEGER, domain_name TEXT)")
        conn.exec_driver_sql(
            "CREATE TABLE adtech.companies (id INTEGER, domain_id INTEGER, parent_company_id INTEGER)"
        )
        conn.exec_driver_sql(
            "CREATE TABLE adtech.company_domain_mapping (company_id INTEGER, domain_id INTEGER)"
        )
        conn.exec_driver_sql("""CREATE TABLE frontend.api_call_response_types (
            company_domain TEXT, tld_url TEXT, response_type TEXT,
            app_count_30d INTEGER, observed_call_count_30d INTEGER,
            app_count_alltime INTEGER, observed_call_count_alltime INTEGER
        )""")
        conn.exec_driver_sql(
            "INSERT INTO domains VALUES (1,'parent.com'),(2,'child.com'),(3,'alias.com'),(4,'other.com'),(5,'shared.com'),(6,'unmapped.com')"
        )
        conn.exec_driver_sql(
            "INSERT INTO adtech.companies VALUES (1,1,NULL),(2,2,1),(3,4,NULL)"
        )
        conn.exec_driver_sql(
            "INSERT INTO adtech.company_domain_mapping VALUES (1,1),(2,2),(2,3),(2,5),(3,4),(3,5),(2,3)"
        )
        conn.exec_driver_sql(
            "INSERT INTO frontend.api_call_response_types VALUES (?, ?, ?, ?, ?, ?, ?)",
            [
                ("parent.com", "parent.com", "json", 2, 4, 3, 7),
                ("child.com", "child.com", "json", 5, 10, 6, 12),
                ("child.com", "alias.com", "json", 5, 11, 7, 13),
                ("(unknown)", None, "unknown", None, None, 3, 8),
                ("child.com", "other.com", "invalid", 90, 90, 90, 90),
                ("other.com", "shared.com", "json", 8, 9, 10, 11),
                ("child.com", "shared.com", "json", 7, 8, 9, 10),
                ("alias.com", "alias.com", "stale-fallback", 99, 99, 99, 99),
                ("unmapped.com", "unmapped.com", "fallback", None, None, 3, 8),
                ("absent.com", "absent.com", "fallback", 1, 2, 3, 4),
            ],
        )
    result = MagicMock()
    result.dbcon.engine = engine
    result.static_data.company_secondary_domains = ["alias.com", "shared.com"]
    result.static_data.parent_companies = ["parent.com"]
    yield result
    engine.dispose()


@pytest.mark.parametrize(
    ("domain", "expected"),
    [
        ("alias.com", [("child.com", "alias.com")]),
        ("shared.com", [("other.com", "shared.com"), ("child.com", "shared.com")]),
        (
            "child.com",
            [
                ("child.com", "shared.com"),
                ("child.com", "alias.com"),
                ("child.com", "child.com"),
            ],
        ),
        (
            "parent.com",
            [
                ("child.com", "shared.com"),
                ("child.com", "alias.com"),
                ("child.com", "child.com"),
                ("parent.com", "parent.com"),
            ],
        ),
        ("missing.com", []),
        ("(unknown)", []),
        ("unmapped.com", [("unmapped.com", "unmapped.com")]),
        ("absent.com", [("absent.com", "absent.com")]),
    ],
)
def test_scope_preserves_overlapping_counts_and_fallback(state, domain, expected):
    rows = get_company_api_response_types(state, domain)
    assert [(row["company_domain"], row["tld_url"]) for row in rows] == expected
    if domain == "child.com":
        assert [row["app_count_30d"] for row in rows] == [7, 5, 5]
    if domain == "unmapped.com":
        assert rows[0]["app_count_30d"] == 0
        assert rows[0]["observed_call_count_30d"] == 0
        assert rows[0]["app_count_alltime"] == 3


def test_limit_ties_and_null_type(state):
    with state.dbcon.engine.begin() as conn:
        conn.exec_driver_sql("DELETE FROM frontend.api_call_response_types")
        conn.exec_driver_sql(
            "INSERT INTO frontend.api_call_response_types VALUES (?, 'alias.com', ?, 1, 2, 3, 4)",
            [("child.com", f"type-{i:02}") for i in reversed(range(21))]
            + [("child.com", None)],
        )
    rows = get_company_api_response_types(state, "alias.com")
    assert len(rows) == 20
    assert [row["response_type"] for row in rows] == [f"type-{i:02}" for i in range(20)]
    with state.dbcon.engine.begin() as conn:
        conn.exec_driver_sql(
            "DELETE FROM frontend.api_call_response_types WHERE response_type IS NOT NULL"
        )
    assert get_company_api_response_types(state, "alias.com")[0]["response_type"] is None


def test_endpoint_serializes_rows(state):
    empty_apps = pd.DataFrame(columns=["store", "store_id", "name"])
    rows = get_company_api_response_types(state, "alias.com")
    with (
        patch(
            "api_app.controllers.companies.get_api_apps_for_company",
            return_value=empty_apps,
        ),
        patch(
            "api_app.controllers.companies.get_company_recent_api_activity",
            return_value=pd.DataFrame(),
        ),
        patch(
            "api_app.controllers.companies.get_company_api_response_types",
            return_value=rows,
        ),
        TestClient(app=Litestar(route_handlers=[CompaniesController])) as client,
    ):
        response = client.get("/api/companies/alias.com/api-apps")
    assert response.status_code == 200
    assert response.json()["response_types"] == [
        {
            "company_domain": "child.com",
            "tld_url": "alias.com",
            "response_type": "json",
            "app_count_30d": 5,
            "observed_call_count_30d": 11,
            "app_count_alltime": 7,
            "observed_call_count_alltime": 13,
        }
    ]
