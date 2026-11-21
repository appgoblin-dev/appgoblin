"""Tests for company API-using app rankings and endpoint."""

from unittest.mock import MagicMock, patch

import pandas as pd
import pytest
from litestar import Litestar
from litestar.testing import TestClient
from sqlalchemy import create_engine

from api_app.controllers.companies import CompaniesController
from dbcon.queries import get_api_apps_for_company


@pytest.mark.parametrize(
    ("secondary", "parent", "table"),
    [
        (True, True, "company_domains_top_apps"),
        (False, True, "company_parent_top_apps"),
        (False, False, "company_top_apps"),
    ],
)
def test_api_apps_filter_before_per_store_ranking(secondary, parent, table):
    engine = create_engine("sqlite://")
    with engine.begin() as conn:
        conn.exec_driver_sql("ATTACH DATABASE ':memory:' AS frontend")
        conn.exec_driver_sql(
            f"""CREATE TABLE frontend.{table} (
                company_domain TEXT, store INTEGER, name TEXT, store_id TEXT,
                developer_name TEXT, icon_64 TEXT, app_company_rank INTEGER,
                installs_d30 INTEGER, sdk BOOLEAN, api_call BOOLEAN,
                publisher BOOLEAN, app_ads_direct BOOLEAN
            )"""
        )
        conn.exec_driver_sql(
            "CREATE TABLE frontend.store_apps_overview "
            "(store_id TEXT, store INTEGER, is_removed BOOLEAN, country_id INTEGER)"
        )
        conn.exec_driver_sql("CREATE TABLE countries (id INTEGER, alpha2 TEXT)")
        rows = []
        for store in (1, 2):
            for rank in range(1, 15):
                rows.append(
                    ("example.com", store, f"App {rank}", f"{store}-{rank}",
                     "Dev", None, rank, 100 - rank, False, rank > 2, False, False)
                )
        rows.append(("other.com", 1, "Other", "other", "Dev", None, 1,
                     99, False, True, False, False))
        conn.exec_driver_sql(
            f"INSERT INTO frontend.{table} VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            rows,
        )
    state = MagicMock()
    state.dbcon.engine = engine
    state.static_data.company_secondary_domains = ["example.com"] if secondary else []
    state.static_data.parent_companies = ["example.com"] if parent else []

    df = get_api_apps_for_company(state, "example.com")

    assert len(df) == 20
    for store, group in df.groupby("store"):
        assert store in ("Google Play", "Apple App Store")
        assert group["rank"].tolist() == list(range(1, 11))
        assert group["name"].tolist() == [f"App {n}" for n in range(3, 13)]
        assert group["api_call"].all()

    empty = get_api_apps_for_company(state, "missing.com") if not (secondary or parent) else None
    if empty is not None:
        assert empty.empty
    engine.dispose()


@pytest.mark.parametrize("empty", [False, True])
def test_company_api_apps_endpoint_shape(empty):
    rows = [] if empty else [
        {"store": "Google Play", "store_id": "android", "name": "Android", "api_call": True},
        {"store": "Apple App Store", "store_id": "ios", "name": "iOS", "api_call": True},
    ]
    frame = pd.DataFrame(rows, columns=["store", "store_id", "name", "api_call"])
    app = Litestar(route_handlers=[CompaniesController])
    with (
        patch("api_app.controllers.companies.get_api_apps_for_company", return_value=frame) as query,
        patch("api_app.controllers.companies.get_company_recent_api_activity", return_value=pd.DataFrame()),
        patch("api_app.controllers.companies.get_company_api_response_types", return_value=[]),
        TestClient(app=app) as client,
    ):
        response = client.get("/api/companies/example.com/api-apps")

    assert response.status_code == 200
    assert response.json() == {
        "android": {"title": "example.com", "apps": [] if empty else [rows[0]]},
        "ios": {"title": "example.com", "apps": [] if empty else [rows[1]]},
        "recent_endpoints": [],
        "recent_requests": [],
        "response_types": [],
    }
    assert query.call_args.kwargs["company_domain"] == "example.com"
