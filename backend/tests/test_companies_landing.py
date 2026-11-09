"""Tests for the lightweight companies landing summary."""

from unittest.mock import MagicMock, patch

from litestar import Litestar
from litestar.testing import TestClient

from api_app.controllers.companies import CompaniesController
from dbcon.queries import get_companies_landing


def test_summary_query_returns_mapping():
    state = MagicMock()
    row = {
        "total": 3,
        "api": 2,
        "sdk": 1,
        "app_ads": 1,
        "publishers": 1,
        "listed": 1,
        "countries": [],
        "listed_companies": [],
    }
    connection = state.dbcon.engine.connect.return_value.__enter__.return_value
    connection.execute.return_value.mappings.return_value.one.return_value = row

    assert get_companies_landing(state) == row
    connection.execute.assert_called_once()


def test_summary_endpoint_is_distinct_from_company_detail():
    summary = {
        "total": 2,
        "api": 1,
        "sdk": 0,
        "app_ads": 1,
        "publishers": 0,
        "listed": 1,
        "countries": [{"country": "US", "company_count": 2}],
        "listed_companies": [
            {
                "company_domain": "example.com",
                "company_name": "Example",
                "tickers_direct": ["EX"],
                "company_tickers": None,
            }
        ],
    }
    app = Litestar(route_handlers=[CompaniesController])
    with patch(
        "api_app.controllers.companies.get_companies_landing", return_value=summary
    ) as query:
        with TestClient(app=app) as client:
            response = client.get("/api/companies/summary")
    assert response.status_code == 200
    assert response.json() == summary
    query.assert_called_once()
