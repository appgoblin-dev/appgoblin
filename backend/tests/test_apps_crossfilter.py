from unittest.mock import MagicMock

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
