from unittest.mock import MagicMock

import pandas as pd

from api_app import report_exports
from dbcon import queries


def test_query_apps_crossfilter_defaults_and_optional_flags(monkeypatch):
    query_call = {}

    def fake_read_sql(query, connection, params):
        query_call["query"] = query
        query_call["params"] = params
        return None

    monkeypatch.setattr(queries.pd, "read_sql", fake_read_sql)

    queries.query_apps_crossfilter(
        MagicMock(),
        include_company_ids=[],
        exclude_company_ids=[],
        include_removed_apps=True,
        tv_supported_only=True,
    )

    assert query_call["params"]["include_removed_apps"] is True
    assert query_call["params"]["tv_supported_only"] is True
    assert "sao.is_removed = FALSE" in query_call["query"].text
    assert "sao.tv_supported = TRUE" in query_call["query"].text


def test_query_apps_crossfilter_defaults_to_live_apps_without_tv_filter(monkeypatch):
    query_call = {}

    def fake_read_sql(query, connection, params):
        query_call["query"] = query
        query_call["params"] = params
        return None

    monkeypatch.setattr(queries.pd, "read_sql", fake_read_sql)

    queries.query_apps_crossfilter(
        MagicMock(),
        include_company_ids=[],
        exclude_company_ids=[],
    )

    assert query_call["params"]["include_removed_apps"] is False
    assert query_call["params"]["tv_supported_only"] is False
    for column in (
        "tv_supported",
        "is_removed",
        "developer_name",
        "developer_id",
        "developer_url",
    ):
        assert f"sao.{column}" in query_call["query"].text


def test_crossfilter_export_includes_requested_app_columns(monkeypatch):
    apps = pd.DataFrame(
        [
            {
                "id": 1,
                "name": "Example App",
                "tv_supported": True,
                "is_removed": False,
                "developer_name": "Example Developer",
                "developer_id": "developer-1",
                "developer_url": "https://example.com/developer",
            }
        ]
    )
    monkeypatch.setattr(
        report_exports, "query_apps_crossfilter", lambda *args, **kwargs: apps.copy()
    )

    csv_bytes, row_count = report_exports.create_crossfilter_export_csv(
        MagicMock(), {}
    )

    assert row_count == 1
    header = csv_bytes.decode("utf-8").splitlines()[0].split(",")
    assert {
        "tv_supported",
        "is_removed",
        "developer_name",
        "developer_id",
        "developer_url",
    }.issubset(header)
