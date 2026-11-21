"""Tests for adapter pattern presentation in SDK endpoints."""

from unittest.mock import patch

import pandas as pd
import pytest
from litestar import Litestar
from litestar.testing import TestClient

from api_app.controllers.companies import CompaniesController
from api_app.controllers.sdks import SdksController


@pytest.fixture
def pattern_rows():
    return pd.DataFrame(
        [
            {
                "company_name": "Example",
                "sdk_id": 7,
                "sdk_slug": "example",
                "sdk_name": "Example SDK",
                "pattern_type": "package",
                "pattern_value": "com.example",
                "app_count": 20,
            },
            {
                "company_name": "Example",
                "sdk_id": 7,
                "sdk_slug": "example",
                "sdk_name": "Example SDK",
                "pattern_type": "adapter",
                "pattern_value": "com.example.adapter",
                "app_count": 4,
            },
            {
                "company_name": "Example",
                "sdk_id": 7,
                "sdk_slug": "example",
                "sdk_name": "Example SDK",
                "pattern_type": "ADAPTER",
                "pattern_value": "adapter.unknown",
                "app_count": None,
            },
            {
                "company_name": "Example",
                "sdk_id": 7,
                "sdk_slug": "example",
                "sdk_name": "Example SDK",
                "pattern_type": "adapter",
                "pattern_value": None,
                "app_count": None,
            },
        ]
    )


def test_mapped_sdk_endpoint_returns_adapter_patterns(pattern_rows):
    app = Litestar(route_handlers=[SdksController])
    with (
        patch(
            "api_app.controllers.sdks.get_sdk_companies", return_value=pd.DataFrame()
        ),
        patch("api_app.controllers.sdks.get_sdk_patterns", return_value=pattern_rows),
        TestClient(app=app, raise_server_exceptions=False) as client,
    ):
        response = client.get("/api/sdks/appgoblin/example")
    assert response.status_code == 200
    patterns = response.json()["patterns"]
    assert patterns["package_patterns"] == [{"pattern": "com.example", "app_count": 20}]
    assert patterns["adapter_patterns"] == [
        {"pattern": "com.example.adapter", "app_count": 4},
        {"pattern": "adapter.unknown", "app_count": None},
    ]


def test_mapped_sdk_metadata_can_skip_app_lookup():
    app = Litestar(route_handlers=[SdksController])
    with (
        patch(
            "api_app.controllers.sdks.get_sdk_companies", return_value=pd.DataFrame()
        ),
        patch(
            "api_app.controllers.sdks.get_sdk_patterns",
            return_value=pd.DataFrame(columns=["pattern_type", "pattern_value", "app_count"]),
        ),
        patch("api_app.controllers.sdks.get_sdk") as get_sdk,
        TestClient(app=app, raise_server_exceptions=False) as client,
    ):
        response = client.get("/api/sdks/appgoblin/example/metadata")
    assert response.status_code == 200
    assert response.json()["apps"] == []
    get_sdk.assert_not_called()


def test_company_sdks_endpoint_returns_adapter_patterns(pattern_rows):
    app = Litestar(route_handlers=[CompaniesController])
    with (
        patch(
            "api_app.controllers.companies.get_company_sdks", return_value=pattern_rows
        ),
        TestClient(app=app, raise_server_exceptions=False) as client,
    ):
        response = client.get("/api/companies/example.com/sdks")
    assert response.status_code == 200
    patterns = response.json()["companies"]["Example"]["Example SDK"]
    assert patterns["package_patterns"] == [{"pattern": "com.example", "app_count": 20}]
    assert patterns["adapter_patterns"] == [
        {"pattern": "com.example.adapter", "app_count": 4},
        {"pattern": "adapter.unknown", "app_count": None},
    ]
