"""Tests for adapter-to-mediation platform relationships."""

from unittest.mock import patch

import pandas as pd
import pytest
from litestar import Litestar
from litestar.testing import TestClient
from sqlalchemy import create_engine, text

from api_app.controllers.companies import CompaniesController
from dbcon.utils import sql


def test_mediation_partner_query_groups_categories_for_exact_adapter_domain():
    engine = create_engine("sqlite://")
    query = str(sql.mediation_partners).replace("frontend.", "")
    with engine.begin() as conn:
        conn.execute(
            text(
                "CREATE TABLE mediation_adapter_app_counts (mediation_domain TEXT, adapter_domain TEXT, app_category TEXT, app_count INT)"
            )
        )
        conn.execute(
            text(
                "INSERT INTO mediation_adapter_app_counts VALUES ('max.com', 'unity.com', 'games', 5), ('max.com', 'unity.com', 'tools', 3), ('other.com', 'unity.com', 'games', 2), ('max.com', 'another.com', 'games', 99), (NULL, 'unity.com', 'games', 10)"
            )
        )
        result = (
            conn.execute(text(query), {"company_domain": "unity.com"}).mappings().all()
        )
        empty = (
            conn.execute(text(query), {"company_domain": "missing.com"})
            .mappings()
            .all()
        )
    assert [dict(row) for row in result] == [
        {"mediation_domain": "max.com", "app_count": 8},
        {"mediation_domain": "other.com", "app_count": 2},
    ]
    assert empty == []


@pytest.mark.parametrize(
    "records", [[], [{"mediation_domain": "max.com", "app_count": 8}]]
)
def test_mediation_partners_endpoint_returns_exact_domain_data(records):
    app = Litestar(route_handlers=[CompaniesController])
    frame = pd.DataFrame(records, columns=["mediation_domain", "app_count"])
    with (
        patch(
            "api_app.controllers.companies.get_mediation_partners", return_value=frame
        ) as lookup,
        TestClient(app=app, raise_server_exceptions=False) as client,
    ):
        response = client.get("/api/companies/unity.com/mediation-partners")
    assert response.status_code == 200
    assert response.json() == records
    assert lookup.call_args.args[1] == "unity.com"
