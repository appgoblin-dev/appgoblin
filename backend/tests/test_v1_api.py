"""Integration tests for /api/v1 endpoints."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from dataclasses import dataclass, fields
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest
from litestar import Litestar
from litestar.middleware import DefineMiddleware
from litestar.openapi.config import OpenAPIConfig
from litestar.testing import TestClient

from api_app.analytics import PUBLIC_API_HOSTNAME
from api_app.controllers.health import HealthController
from api_app.controllers.public.v1.apps import V1AppsController
from api_app.controllers.public.v1 import companies as v1_companies
from api_app.controllers.public.v1 import public_models as v1_public_models
from api_app.controllers.public.v1.companies import (
    UNMAPPED_COMPANY_NOTICE,
    V1CompaniesController,
)
from api_app.controllers.public.v1.keywords import V1KeywordsController
from api_app.controllers.public.v1.rankings import V1RankingsController
from api_app.controllers.public.v1.public_models import (
    CompanyDatasets,
    CompanyDatasetTarget,
    PublicCompanyAppChangeStoreIds,
    PublicCategoryCompanyStats,
    PublicCompanyOverview,
    PublicCompanyTrends,
)
from api_app.controllers.public.v1.docs import V1DocsController
from api_app.guards import _CachedKey
from api_app.models import CategoryCompanyStats
from app import RateLimitMiddleware


@dataclass
class FakeCompaniesOverview:
    companies_overview: list
    top: object = None
    categories: object = None


@dataclass
class FakeCompanyCategoryOverview:
    categories: dict
    company_types: list | None = None
    trends_summary: object | None = None
    adstxt_ad_domain_overview: dict | None = None
    adstxt_publishers_overview: dict | None = None
    mediation_adapters: dict | None = None


@asynccontextmanager
async def _mock_lifespan(app: Litestar) -> AsyncGenerator[None]:
    """Set up mock dbconwrite on the app state for all requests."""
    app.state.dbconwrite = MagicMock()
    yield


def _make_test_app():
    return Litestar(
        route_handlers=[
            V1CompaniesController,
            V1AppsController,
            V1KeywordsController,
            V1RankingsController,
        ],
        lifespan=[_mock_lifespan],
        middleware=[DefineMiddleware(RateLimitMiddleware)],
    )


def _make_docs_test_app():
    return Litestar(
        route_handlers=[
            HealthController,
            V1CompaniesController,
            V1AppsController,
            V1KeywordsController,
            V1RankingsController,
            V1DocsController,
        ],
        lifespan=[_mock_lifespan],
        middleware=[DefineMiddleware(RateLimitMiddleware)],
        openapi_config=OpenAPIConfig(
            title="Test AppGoblin Public API v1", version="0.0.1"
        ),
    )


@pytest.fixture(autouse=True)
def _reset_caches(isolated_guards):
    """Use disposable Redis-backed guard state for each test."""


def _patch_key_found(tier="free"):
    return patch(
        "api_app.guards._query_key",
        return_value=_CachedKey(user_id=1, tier=tier, expires_at=9e9),
    )


def _patch_key_not_found():
    return patch("api_app.guards._query_key", return_value=None)


FAKE_OVERVIEW = FakeCompaniesOverview(
    companies_overview=[
        {
            "company_name": "Google",
            "company_domain": "google.com",
            "parent_company_domain": "alphabet.com",
            "parent_company_name": "Alphabet",
            "api_ip_resolved_country": "US",
            "total_app_count": 50000,
            "installs_d30": 123456789,
            "google_sdk_app_count": 30000,
            "apple_sdk_app_count": 12000,
            "google_api_call_app_count": 4000,
            "apple_api_call_app_count": 1000,
            "google_app_ads_direct_app_count": 2000,
            "apple_app_ads_direct_app_count": 500,
            "google_app_ads_reseller_app_count": 300,
            "apple_app_ads_reseller_app_count": 200,
            "trends_latest_period": "2026Q1",
            "google_sdk_latest_pct_market_share": 18.5,
            "apple_sdk_latest_pct_market_share": 4.25,
            "google_app_ads_direct_latest_pct_market_share": 2.75,
            "apple_app_ads_direct_latest_pct_market_share": None,
            "google_sdk_latest_pct_market_share_change": 20.0,
            "apple_sdk_latest_pct_market_share_change": 100.0,
            "google_app_ads_direct_latest_pct_market_share_change": 75.0,
            "apple_app_ads_direct_latest_pct_market_share_change": None,
            "google_sdk_latest_total_apps": 240,
            "apple_sdk_latest_total_apps": 40,
            "google_app_ads_direct_latest_total_apps": 35,
            "apple_app_ads_direct_latest_total_apps": None,
            "google_sdk_latest_apps_added": 40,
            "apple_sdk_latest_apps_added": 10,
            "google_app_ads_direct_latest_apps_added": 20,
            "apple_app_ads_direct_latest_apps_added": None,
            "google_sdk_latest_apps_lost": 10,
            "apple_sdk_latest_apps_lost": 0,
            "google_app_ads_direct_latest_apps_lost": 5,
            "apple_app_ads_direct_latest_apps_lost": None,
        },
        {
            "company_name": float("nan"),
            "company_domain": "blasto.ai",
            "parent_company_domain": None,
            "parent_company_name": None,
            "api_ip_resolved_country": None,
            "total_app_count": 30000,
            "installs_d30": 450000,
            "google_sdk_app_count": None,
        },
    ]
)


def _patch_overview(overview=FAKE_OVERVIEW):
    return patch(
        "api_app.controllers.public.v1.companies.get_overviews", return_value=overview
    )


def _patch_company_detail(payload: dict):
    return patch(
        "api_app.controllers.public.v1.companies._build_public_company_overview_payload",
        return_value=payload,
    )


def _patch_raw_company_detail(overview: FakeCompanyCategoryOverview):
    return patch(
        "api_app.controllers.public.v1.companies.build_company_overview_base",
        return_value=overview,
    )


def _patch_company_app_change_store_ids_by_platform(
    store_ids_by_platform: dict[str, list[str]],
):
    return patch(
        "api_app.controllers.public.v1.companies.get_company_app_change_store_ids_by_platform",
        return_value=store_ids_by_platform,
    )


def _patch_single_app(row: dict | None):
    app_df = pd.DataFrame([row]) if row is not None else pd.DataFrame()
    return patch(
        "api_app.controllers.public.v1.apps.get_single_app", return_value=app_df
    )


def _patch_ranks(rows: list[dict]):
    ranks_df = pd.DataFrame(rows)
    return patch(
        "api_app.controllers.public.v1.apps.get_ranks_for_app_overview",
        return_value=ranks_df,
    )


def _patch_mapped_sdks(rows: list[dict]):
    mapped_sdks_df = pd.DataFrame(rows)
    return patch(
        "api_app.controllers.public.v1.apps.get_app_mapped_sdks",
        return_value=mapped_sdks_df,
    )


def _patch_sdk_details(rows: list[dict]):
    details_df = pd.DataFrame(rows)
    return patch(
        "api_app.controllers.public.v1.apps.get_app_sdk_details",
        return_value=details_df,
    )


def _patch_sdk_companies(rows: list[dict]):
    companies_df = pd.DataFrame(rows)
    return patch(
        "api_app.controllers.public.v1.companies.get_sdk_companies",
        return_value=companies_df,
    )


def _patch_company_sdks(rows: list[dict]):
    sdks_df = pd.DataFrame(rows)
    return patch(
        "api_app.controllers.public.v1.companies.get_company_sdks",
        return_value=sdks_df,
    )


def _patch_version_timeline(rows: list[dict]):
    timeline_df = pd.DataFrame(rows)
    return patch(
        "api_app.controllers.public.v1.apps.get_app_version_timeline",
        return_value=timeline_df,
    )


def _patch_sdk_history(rows: list[dict]):
    history_df = pd.DataFrame(rows)
    return patch(
        "api_app.controllers.public.v1.apps.get_app_sdk_history",
        return_value=history_df,
    )


def _patch_ctv_app_ranks(rows: list[dict]):
    ranks_df = pd.DataFrame(rows)
    return patch(
        "api_app.controllers.public.v1.rankings.get_ctv_app_ranks",
        return_value=ranks_df,
    )


def _patch_keyword_details(rows: list[dict]):
    keyword_df = pd.DataFrame(rows)
    return patch(
        "api_app.controllers.public.v1.keywords.get_keyword_details",
        return_value=keyword_df,
    )


def _patch_keyword_apps(rows: list[dict]):
    keyword_apps_df = pd.DataFrame(rows)
    return patch(
        "api_app.controllers.public.v1.keywords.get_keyword_apps",
        return_value=keyword_apps_df,
    )


class TestV1Search:
    @pytest.mark.parametrize(
        "path",
        [
            "/api/v1/apps/search",
            "/api/v1/apps/search/developers",
            "/api/v1/companies/search",
        ],
    )
    def test_search_requires_api_key(self, path):
        with TestClient(app=_make_test_app(), raise_server_exceptions=False) as client:
            assert client.get(path, params={"q": "example"}).status_code == 401

    @pytest.mark.parametrize(
        ("path", "query"),
        [
            ("/api/v1/apps/search", "search_v1_apps"),
            ("/api/v1/apps/search/developers", "search_v1_developer_apps"),
        ],
    )
    def test_app_searches_use_separate_queries(self, path, query):
        rows = pd.DataFrame(
            [
                {
                    "store": 1,
                    "store_id": "com.example",
                    "name": "Example",
                    "icon_128": "icon.png",
                    "installs": 100,
                    "rating": 4.5,
                    "rating_count": 10,
                }
            ]
        )
        with (
            _patch_key_found(),
            patch(
                f"api_app.controllers.public.v1.apps.{query}", return_value=rows
            ) as search,
            TestClient(app=_make_test_app(), raise_server_exceptions=False) as client,
        ):
            resp = client.get(
                path,
                params={"q": " Example+App ", "limit": 5},
                headers={"X-API-Key": "ag_test"},
            )
        assert resp.status_code == 200, resp.text
        search.assert_called_once()
        assert search.call_args.args[1:] == ("Example+App", 5)
        assert resp.json()[0]["store_id"] == "com.example"
        assert resp.json()[0]["store"] == "Google Play"
        assert "app_icon_url" not in resp.json()[0]

    def test_company_search_and_paid_guard(self):
        rows = pd.DataFrame(
            [
                {
                    "company_domain": "example.com",
                    "company_name": "Example",
                    "has_sdk_signal": True,
                }
            ]
        )
        with (
            _patch_key_found("b2b_premium"),
            patch(
                "api_app.controllers.public.v1.companies.search_v1_companies",
                return_value=rows,
            ) as search,
            TestClient(app=_make_test_app(), raise_server_exceptions=False) as client,
        ):
            resp = client.get(
                "/api/v1/companies/search",
                params={"q": "example"},
                headers={"X-API-Key": "ag_test"},
            )
        assert resp.status_code == 200, resp.text
        assert resp.json()[0]["company_domain"] == "example.com"
        assert search.call_args.args[1:] == ("example", 20)
        with (
            _patch_key_found(),
            TestClient(app=_make_test_app(), raise_server_exceptions=False) as client,
        ):
            assert (
                client.get(
                    "/api/v1/companies/search",
                    params={"q": "example"},
                    headers={"X-API-Key": "ag_free"},
                ).status_code
                == 403
            )

    @pytest.mark.parametrize(
        "path",
        [
            "/api/v1/apps/search",
            "/api/v1/apps/search/developers",
            "/api/v1/companies/search",
        ],
    )
    @pytest.mark.parametrize(
        "params", [{"q": " "}, {"q": "abc", "limit": 0}, {"q": "abc", "limit": 101}]
    )
    def test_search_rejects_invalid_parameters(self, path, params):
        with (
            _patch_key_found("b2b_premium"),
            TestClient(app=_make_test_app(), raise_server_exceptions=False) as client,
        ):
            assert (
                client.get(
                    path, params=params, headers={"X-API-Key": "ag_test"}
                ).status_code
                == 400
            )


def test_v1_search_queries_are_independent_and_parameterized():
    from dbcon import queries
    from dbcon.utils import sql

    state = MagicMock()
    with patch("dbcon.queries.pd.read_sql", return_value=pd.DataFrame()) as read_sql:
        queries.search_v1_apps(state, "rock & roll", 4)
        queries.search_v1_developer_apps(state, "rock & roll", 4)
        queries.search_v1_companies(state, "rock & roll", 4)
    assert [call.args[0] for call in read_sql.call_args_list] == [
        sql.v1_search_apps,
        sql.v1_search_devs,
        sql.v1_search_companies,
    ]
    assert all(
        call.kwargs["params"] == {"searchinput": "rock & roll", "mylimit": 4}
        for call in read_sql.call_args_list
    )
    assert "plainto_tsquery" in str(sql.v1_search_apps)
    assert "plainto_tsquery" in str(sql.v1_search_devs)


class TestV1CompaniesAuth:
    def test_no_api_key_returns_401(self):
        app = _make_test_app()
        with TestClient(app=app, raise_server_exceptions=False) as client:
            resp = client.get("/api/v1/companies")
        assert resp.status_code == 401

    def test_company_detail_requires_api_key(self):
        app = _make_test_app()
        with TestClient(app=app, raise_server_exceptions=False) as client:
            resp = client.get("/api/v1/companies/google.com")
        assert resp.status_code == 401
        assert "Missing API key" in resp.json()["detail"]

    def test_app_requires_api_key(self):
        app = _make_test_app()
        with TestClient(app=app, raise_server_exceptions=False) as client:
            resp = client.get("/api/v1/apps/com.example.app")
        assert resp.status_code == 401
        assert "Missing API key" in resp.json()["detail"]

    def test_app_ranks_requires_api_key(self):
        app = _make_test_app()
        with TestClient(app=app, raise_server_exceptions=False) as client:
            resp = client.get("/api/v1/apps/com.example.app/ranks")
        assert resp.status_code == 401
        assert "Missing API key" in resp.json()["detail"]

    def test_app_sdks_requires_api_key(self):
        app = _make_test_app()
        with TestClient(app=app, raise_server_exceptions=False) as client:
            resp = client.get("/api/v1/apps/com.example.app/sdks")
        assert resp.status_code == 401
        assert "Missing API key" in resp.json()["detail"]

    def test_keyword_overview_requires_api_key(self):
        app = _make_test_app()
        with TestClient(app=app, raise_server_exceptions=False) as client:
            resp = client.get("/api/v1/keywords/app privacy")
        assert resp.status_code == 401
        assert "Missing API key" in resp.json()["detail"]

    def test_keyword_ranks_requires_api_key(self):
        app = _make_test_app()
        with TestClient(app=app, raise_server_exceptions=False) as client:
            resp = client.get("/api/v1/keywords/app privacy/ranks")
        assert resp.status_code == 401
        assert "Missing API key" in resp.json()["detail"]

    def test_invalid_api_key_returns_401(self):
        app = _make_test_app()
        with (
            _patch_key_not_found(),
            TestClient(app=app, raise_server_exceptions=False) as client,
        ):
            resp = client.get(
                "/api/v1/companies",
                headers={"X-API-Key": "ag_totallyfake"},
            )
        assert resp.status_code == 401

    def test_free_tier_returns_403_for_companies(self):
        app = _make_test_app()
        with (
            _patch_key_found("free"),
            _patch_overview(),
            TestClient(app=app, raise_server_exceptions=False) as client,
        ):
            resp = client.get(
                "/api/v1/companies",
                headers={"X-API-Key": "ag_goodkey"},
            )

        assert resp.status_code == 403
        assert "paid subscription tier" in resp.json()["detail"]

    def test_free_tier_returns_403_for_company_detail(self):
        app = _make_test_app()
        with (
            _patch_key_found("free"),
            TestClient(app=app, raise_server_exceptions=False) as client,
        ):
            resp = client.get(
                "/api/v1/companies/google.com",
                headers={"X-API-Key": "ag_goodkey"},
            )

        assert resp.status_code == 403
        assert "paid subscription tier" in resp.json()["detail"]

    def test_company_sdks_returns_public_mapping(self):
        app = _make_test_app()
        with (
            _patch_key_found("premium_access"),
            _patch_company_sdks(
                [
                    {"sdk_slug": "unity-ads", "sdk_name": "Unity Ads", "app_count": 30},
                    {"sdk_slug": "unity-ads", "sdk_name": "Unity Ads", "app_count": 30},
                    {"sdk_slug": "unity-mediation", "sdk_name": "Unity Mediation", "app_count": 12},
                ]
            ),
            TestClient(app=app, raise_server_exceptions=False) as client,
        ):
            resp = client.get(
                "/api/v1/companies/unity.com/sdks",
                headers={"X-API-Key": "ag_company_sdks"},
            )

        assert resp.status_code == 200
        assert resp.json() == {
            "company_domain": "unity.com",
            "sdks": [
                {"sdk_slug": "unity-ads", "sdk_name": "Unity Ads", "app_count": 30},
                {
                    "sdk_slug": "unity-mediation",
                    "sdk_name": "Unity Mediation",
                    "app_count": 12,
                },
            ],
        }

    def test_sdk_company_overview_returns_public_shape(self):
        app = _make_test_app()
        company_payload = PublicCompanyOverview(
            domain_is_mapped=True,
            company_types=["ad-networks"],
        )
        with (
            _patch_key_found("premium_access"),
            _patch_sdk_companies(
                [
                    {
                        "sdk_id": 42,
                        "sdk_slug": "example-sdk",
                        "company_name": "Example Co",
                        "company_domain": "example.com",
                    }
                ]
            ),
            patch(
                "api_app.controllers.public.v1.companies._build_public_company_overview_payload",
                return_value=company_payload,
            ),
            TestClient(app=app, raise_server_exceptions=False) as client,
        ):
            resp = client.get(
                "/api/v1/sdks/example-sdk",
                headers={"X-API-Key": "ag_goodkey"},
            )

        assert resp.status_code == 200
        assert resp.json() == {
            "sdk_slug": "example-sdk",
            "company_domain": "example.com",
            "company_name": "Example Co",
            "company": {
                "domain_is_mapped": True,
                "company_types": ["ad-networks"],
                "metrics": {
                    "total_apps": 0,
                    "adstxt_direct_android_total_apps": 0,
                    "adstxt_direct_ios_total_apps": 0,
                    "adstxt_reseller_android_total_apps": 0,
                    "adstxt_reseller_ios_total_apps": 0,
                    "sdk_android_total_apps": 0,
                    "sdk_ios_total_apps": 0,
                    "sdk_total_apps": 0,
                    "api_android_total_apps": 0,
                    "api_total_apps": 0,
                    "sdk_android_installs_d30": 0,
                    "sdk_ios_installs_d30": 0,
                    "adstxt_direct_android_installs_d30": 0,
                    "adstxt_reseller_android_installs_d30": 0,
                },
                "trends": None,
                "mapping_notice": None,
                "datasets": None,
            },
        }
        assert "sdk_id" not in resp.json()

    def test_paid_key_returns_200(self):
        app = _make_test_app()
        with (
            _patch_key_found("premium_access"),
            _patch_overview(),
            TestClient(app=app, raise_server_exceptions=False) as client,
        ):
            resp = client.get(
                "/api/v1/companies",
                headers={"X-API-Key": "ag_goodkey"},
            )

        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) == 2
        assert data[0]["name"] == "Google"
        assert data[0]["company_domain"] == "google.com"
        assert data[0]["parent_company_domain"] == "alphabet.com"
        assert data[0]["parent_company_name"] == "Alphabet"
        assert data[0]["api_ip_resolved_country"] == "US"
        assert data[0]["total_app_count"] == 50000
        assert data[0]["installs_d30"] == 123456789
        assert data[0]["google_sdk_app_count"] == 30000
        assert data[0]["apple_sdk_app_count"] == 12000
        assert data[0]["google_api_call_app_count"] == 4000
        assert data[0]["apple_api_call_app_count"] == 1000
        assert data[0]["google_app_ads_direct_app_count"] == 2000
        assert data[0]["apple_app_ads_direct_app_count"] == 500
        assert data[0]["google_app_ads_reseller_app_count"] == 300
        assert data[0]["apple_app_ads_reseller_app_count"] == 200
        assert data[0]["trends_latest_period"] == "2026Q1"
        assert data[0]["google_sdk_latest_pct_market_share"] == 18.5
        assert data[0]["apple_sdk_latest_pct_market_share"] == 4.25
        assert data[0]["google_app_ads_direct_latest_pct_market_share"] == 2.75
        assert data[0]["apple_app_ads_direct_latest_pct_market_share"] is None
        assert data[0]["google_sdk_latest_pct_market_share_change"] == 20.0
        assert data[0]["apple_sdk_latest_pct_market_share_change"] == 100.0
        assert data[0]["google_app_ads_direct_latest_pct_market_share_change"] == 75.0
        assert data[0]["apple_app_ads_direct_latest_pct_market_share_change"] is None
        assert data[0]["google_sdk_latest_total_apps"] == 240
        assert data[0]["apple_sdk_latest_total_apps"] == 40
        assert data[0]["google_app_ads_direct_latest_total_apps"] == 35
        assert data[0]["apple_app_ads_direct_latest_total_apps"] is None
        assert "google_sdk_latest_total_apps_change_pct" not in data[0]
        assert "apple_sdk_latest_total_apps_change_pct" not in data[0]
        assert "google_app_ads_direct_latest_total_apps_change_pct" not in data[0]
        assert "apple_app_ads_direct_latest_total_apps_change_pct" not in data[0]
        assert data[0]["google_sdk_latest_apps_added"] == 40
        assert data[0]["apple_sdk_latest_apps_added"] == 10
        assert data[0]["google_app_ads_direct_latest_apps_added"] == 20
        assert data[0]["apple_app_ads_direct_latest_apps_added"] is None
        assert data[0]["google_sdk_latest_apps_lost"] == 10
        assert data[0]["apple_sdk_latest_apps_lost"] == 0
        assert data[0]["google_app_ads_direct_latest_apps_lost"] == 5
        assert data[0]["apple_app_ads_direct_latest_apps_lost"] is None
        assert data[1]["name"] is None
        assert data[1]["company_domain"] == "blasto.ai"
        assert data[1]["parent_company_domain"] is None
        assert data[1]["parent_company_name"] is None
        assert data[1]["api_ip_resolved_country"] is None
        assert data[1]["total_app_count"] == 30000
        assert data[1]["installs_d30"] == 450000
        assert data[1]["google_sdk_app_count"] is None
        assert data[1]["apple_sdk_app_count"] is None
        assert data[1]["google_api_call_app_count"] is None
        assert data[1]["apple_api_call_app_count"] is None
        assert data[1]["google_app_ads_direct_app_count"] is None
        assert data[1]["apple_app_ads_direct_app_count"] is None
        assert data[1]["google_app_ads_reseller_app_count"] is None
        assert data[1]["apple_app_ads_reseller_app_count"] is None
        assert data[1]["trends_latest_period"] is None
        assert data[1]["google_sdk_latest_pct_market_share"] is None
        assert data[1]["apple_sdk_latest_pct_market_share"] is None
        assert data[1]["google_app_ads_direct_latest_pct_market_share"] is None
        assert data[1]["apple_app_ads_direct_latest_pct_market_share"] is None
        assert data[1]["google_sdk_latest_pct_market_share_change"] is None
        assert data[1]["apple_sdk_latest_pct_market_share_change"] is None
        assert data[1]["google_app_ads_direct_latest_pct_market_share_change"] is None
        assert data[1]["apple_app_ads_direct_latest_pct_market_share_change"] is None
        assert data[1]["google_sdk_latest_total_apps"] is None
        assert data[1]["apple_sdk_latest_total_apps"] is None
        assert data[1]["google_app_ads_direct_latest_total_apps"] is None
        assert data[1]["apple_app_ads_direct_latest_total_apps"] is None
        assert "google_sdk_latest_total_apps_change_pct" not in data[1]
        assert "apple_sdk_latest_total_apps_change_pct" not in data[1]
        assert "google_app_ads_direct_latest_total_apps_change_pct" not in data[1]
        assert "apple_app_ads_direct_latest_total_apps_change_pct" not in data[1]
        assert data[1]["google_sdk_latest_apps_added"] is None
        assert data[1]["apple_sdk_latest_apps_added"] is None
        assert data[1]["google_app_ads_direct_latest_apps_added"] is None
        assert data[1]["apple_app_ads_direct_latest_apps_added"] is None
        assert data[1]["google_sdk_latest_apps_lost"] is None
        assert data[1]["apple_sdk_latest_apps_lost"] is None
        assert data[1]["google_app_ads_direct_latest_apps_lost"] is None
        assert data[1]["apple_app_ads_direct_latest_apps_lost"] is None


class TestV1CompaniesRateLimitHeaders:
    def test_response_has_ratelimit_headers(self):
        app = _make_test_app()
        with (
            _patch_key_found("premium_access"),
            _patch_overview(),
            TestClient(app=app) as client,
        ):
            resp = client.get(
                "/api/v1/companies",
                headers={"X-API-Key": "ag_headercheck"},
            )

        assert resp.status_code == 200
        assert resp.headers["x-ratelimit-limit"] == "200"
        assert resp.headers["x-ratelimit-remaining"] == "199"

    def test_daily_quota_headers_present(self):
        app = _make_test_app()
        with (
            _patch_key_found("premium_access"),
            _patch_overview(),
            TestClient(app=app) as client,
        ):
            resp = client.get(
                "/api/v1/companies",
                headers={"X-API-Key": "ag_dailyheader"},
            )

        assert resp.headers["x-ratelimit-policy"] == "10000;w=86400"
        assert resp.headers["x-ratelimit-quota-remaining"] == "9999"


class TestV1CompaniesRateLimit:
    def test_per_minute_429(self):
        from api_app import guards as g

        app = _make_test_app()
        with (
            _patch_key_found("premium_access"),
            _patch_overview(),
            patch.dict(g.TIER_LIMITS, {"premium_access": g.TierLimits(2, 100)}),
            TestClient(app=app, raise_server_exceptions=False) as client,
        ):
            key = "ag_ratelimit429"
            headers = {"X-API-Key": key}

            for _ in range(2):
                resp = client.get("/api/v1/companies", headers=headers)
                assert resp.status_code == 200

            resp = client.get("/api/v1/companies", headers=headers)
            assert resp.status_code == 429
            assert "Rate limit exceeded" in resp.json()["detail"]
            assert "retry-after" in resp.headers

    def test_daily_quota_429(self):
        app = _make_test_app()
        from api_app import guards as g

        with (
            _patch_key_found("b2b_premium"),
            _patch_overview(),
            patch.dict(g.TIER_LIMITS, {"b2b_premium": g.TierLimits(100, 2)}),
            TestClient(app=app, raise_server_exceptions=False) as client,
        ):
            headers = {"X-API-Key": "ag_daily429"}
            for _ in range(2):
                g._daily_quota.check("user:1", 2)

            resp = client.get("/api/v1/companies", headers=headers)
            assert resp.status_code == 429
            assert "Daily request quota" in resp.json()["detail"]


class TestRedisGuardIntegration:
    @pytest.mark.parametrize("tracker_name", ["_daily_quota", "_rate_limiter"])
    def test_rest_redis_outage_returns_503(self, tracker_name):
        import redis
        from api_app import guards

        app = _make_test_app()
        tracker = getattr(guards, tracker_name)
        with (
            _patch_key_found(),
            _patch_overview(),
            patch.object(tracker, "check", side_effect=redis.exceptions.ConnectionError("offline")),
            TestClient(app=app, raise_server_exceptions=False) as client,
        ):
            response = client.get("/api/v1/companies", headers={"X-API-Key": "ag_rest"})
        assert response.status_code == 503

    @pytest.mark.parametrize("tracker_name", ["_daily_quota", "_rate_limiter"])
    def test_mcp_redis_outage_returns_503(self, tracker_name, monkeypatch):
        import asyncio
        import redis
        from api_app import guards
        from api_app.mcp import controller

        monkeypatch.setattr(controller, "get_engine", lambda: MagicMock())
        monkeypatch.setattr(controller, "_query_key", lambda *_: _CachedKey(1, "free", 9e9))
        monkeypatch.setattr(
            getattr(guards, tracker_name), "check",
            MagicMock(side_effect=redis.exceptions.ConnectionError("offline")),
        )
        messages = []

        async def send(message):
            messages.append(message)

        async def downstream(scope, receive, send):
            raise AssertionError("MCP request reached downstream during Redis outage")

        scope = {"type": "http", "headers": [(b"x-api-key", b"ag_mcp")]}
        asyncio.run(controller.AuthenticatedMCPMiddleware(downstream)(scope, None, send))
        assert messages[0]["status"] == 503

    def test_mcp_organization_shares_and_user_fallback_is_isolated(self, monkeypatch):
        import hashlib
        from api_app import guards
        from api_app.mcp import controller

        monkeypatch.setitem(guards.TIER_LIMITS, "free", guards.TierLimits(100, 1))
        keys = {
            hashlib.sha256(raw.encode()).hexdigest(): _CachedKey(user, "free", 9e9, org)
            for raw, user, org in (
                ("org-first", 1, 7),
                ("org-second", 2, 7),
                ("user-first", 1, None),
                ("user-second", 2, None),
            )
        }
        monkeypatch.setattr(controller, "get_engine", lambda: MagicMock())
        monkeypatch.setattr(controller, "_query_key", lambda _engine, key: keys[key])

        def authenticate(key):
            return controller._authenticate({"headers": [(b"x-api-key", key.encode())]})

        assert authenticate("org-first").user_id == 1
        with pytest.raises(controller._RateLimitError):
            authenticate("org-second")
        assert authenticate("user-first").user_id == 1
        assert authenticate("user-second").user_id == 2
        with pytest.raises(controller._RateLimitError):
            authenticate("user-first")

    def test_rest_and_mcp_share_organization_quota(self, monkeypatch):
        import asyncio
        from api_app import guards
        from api_app.mcp import controller

        monkeypatch.setitem(guards.TIER_LIMITS, "premium_access", guards.TierLimits(100, 1))
        monkeypatch.setattr(controller, "get_engine", lambda: MagicMock())
        monkeypatch.setattr(
            controller, "_query_key",
            lambda *_: _CachedKey(2, "premium_access", 9e9, organization_id=7),
        )
        app = _make_test_app()
        with (
            patch("api_app.guards._query_key", return_value=_CachedKey(1, "premium_access", 9e9, organization_id=7)),
            _patch_overview(),
            TestClient(app=app) as client,
        ):
            assert client.get("/api/v1/companies", headers={"X-API-Key": "ag_rest"}).status_code == 200

        messages = []

        async def send(message):
            messages.append(message)

        async def downstream(scope, receive, send):
            raise AssertionError("MCP request exceeded the shared daily quota")

        scope = {"type": "http", "headers": [(b"x-api-key", b"ag_mcp")]}
        asyncio.run(controller.AuthenticatedMCPMiddleware(downstream)(scope, None, send))
        assert messages[0]["status"] == 429


class TestV1CompaniesTierRateLimits:
    @pytest.mark.parametrize(
        "tier,expected_minute",
        [
            ("premium_access", "200"),
            ("b2b_sdk", "2000"),
            ("b2b_premium", "10000"),
        ],
    )
    def test_tier_minute_limit_in_header(self, tier, expected_minute):
        app = _make_test_app()
        with (
            _patch_key_found(tier),
            _patch_overview(),
            TestClient(app=app) as client,
        ):
            resp = client.get(
                "/api/v1/companies",
                headers={"X-API-Key": f"ag_{tier}key"},
            )

        assert resp.status_code == 200
        assert resp.headers["x-ratelimit-limit"] == expected_minute


class TestV1CompanyDetail:
    def test_company_detail_returns_expected_payload(self):
        app = _make_test_app()
        payload = PublicCompanyOverview(
            metrics=PublicCategoryCompanyStats(
                sdk_android_total_apps=123,
                sdk_ios_total_apps=45,
                sdk_total_apps=168,
                sdk_ios_installs_d30=456,
            ),
            trends=PublicCompanyTrends(
                latest_period="2026Q1",
                ios_sdk_api_market_share_change_pct=1.82,
                ios_sdk_api_apps_lost=18,
            ),
            company_types=["ad-network"],
            domain_is_mapped=True,
            datasets=CompanyDatasets(
                sdk_api_android=CompanyDatasetTarget(
                    available=True,
                    estimated_rows=123,
                    url=(
                        "https://media.appgoblin.info/"
                        "downloads/company-verified-apps/domains/domain=google.com/"
                        "source=all/appgoblin_google.com_android_verified_apps.csv"
                    ),
                ),
                sdk_api_ios=CompanyDatasetTarget(
                    available=True,
                    estimated_rows=45,
                    url=(
                        "https://media.appgoblin.info/"
                        "downloads/company-verified-apps/domains/domain=google.com/"
                        "source=all/appgoblin_google.com_ios_verified_apps.csv"
                    ),
                ),
                parent_company_android=CompanyDatasetTarget(
                    available=False, estimated_rows=0, url=None
                ),
                parent_company_ios=CompanyDatasetTarget(
                    available=False, estimated_rows=0, url=None
                ),
            ),
            mapping_notice=None,
        )
        with (
            _patch_key_found("b2b_sdk"),
            _patch_company_detail(payload),
            TestClient(app=app, raise_server_exceptions=False) as client,
        ):
            resp = client.get(
                "/api/v1/companies/google.com",
                headers={"X-API-Key": "ag_companydetail"},
            )

        assert resp.status_code == 200
        assert resp.json() == {
            "metrics": {
                "total_apps": 0,
                "adstxt_direct_android_total_apps": 0,
                "adstxt_direct_ios_total_apps": 0,
                "adstxt_reseller_android_total_apps": 0,
                "adstxt_reseller_ios_total_apps": 0,
                "sdk_android_total_apps": 123,
                "sdk_ios_total_apps": 45,
                "sdk_total_apps": 168,
                "api_android_total_apps": 0,
                "api_total_apps": 0,
                "sdk_android_installs_d30": 0,
                "sdk_ios_installs_d30": 456,
                "adstxt_direct_android_installs_d30": 0,
                "adstxt_reseller_android_installs_d30": 0,
            },
            "trends": {
                "latest_period": "2026Q1",
                "android_app_ads_direct_market_share_change_pct": None,
                "android_app_ads_direct_apps_lost": None,
                "android_sdk_api_market_share_change_pct": None,
                "android_sdk_api_apps_lost": None,
                "ios_app_ads_direct_market_share_change_pct": None,
                "ios_app_ads_direct_apps_lost": None,
                "ios_sdk_api_market_share_change_pct": 1.82,
                "ios_sdk_api_apps_lost": 18,
            },
            "company_types": ["ad-network"],
            "domain_is_mapped": True,
            "datasets": {
                "sdk_api_android": {
                    "available": True,
                    "estimated_rows": 123,
                    "url": (
                        "https://media.appgoblin.info/"
                        "downloads/company-verified-apps/domains/domain=google.com/"
                        "source=all/appgoblin_google.com_android_verified_apps.csv"
                    ),
                },
                "sdk_api_ios": {
                    "available": True,
                    "estimated_rows": 45,
                    "url": (
                        "https://media.appgoblin.info/"
                        "downloads/company-verified-apps/domains/domain=google.com/"
                        "source=all/appgoblin_google.com_ios_verified_apps.csv"
                    ),
                },
                "parent_company_android": {
                    "available": False,
                    "estimated_rows": 0,
                    "url": None,
                },
                "parent_company_ios": {
                    "available": False,
                    "estimated_rows": 0,
                    "url": None,
                },
            },
            "mapping_notice": None,
        }

    def test_company_detail_projects_trends_summary(self):
        app = _make_test_app()
        trend_summary = MagicMock()
        trend_summary.latest_period = "2026Q1"
        trend_summary.sources = {
            "android_sdk_api": MagicMock(
                platform="android",
                tag_source="sdk_api",
                latest_period="2026Q1",
                latest_pct_market_share_change_pct=20.0,
                latest_apps_lost=10,
            )
        }
        overview = FakeCompanyCategoryOverview(
            categories={
                "all": PublicCategoryCompanyStats(
                    sdk_android_total_apps=123,
                    sdk_ios_installs_d30=45,
                )
            },
            company_types=["ad-network"],
            trends_summary=trend_summary,
        )

        with (
            _patch_key_found("b2b_sdk"),
            _patch_raw_company_detail(overview),
            TestClient(app=app, raise_server_exceptions=False) as client,
        ):
            resp = client.get(
                "/api/v1/companies/google.com",
                headers={"X-API-Key": "ag_companydetail"},
            )

        assert resp.status_code == 200
        assert resp.json()["trends"] == {
            "latest_period": "2026Q1",
            "android_app_ads_direct_market_share_change_pct": None,
            "android_app_ads_direct_apps_lost": None,
            "android_sdk_api_market_share_change_pct": 20.0,
            "android_sdk_api_apps_lost": 10,
            "ios_app_ads_direct_market_share_change_pct": None,
            "ios_app_ads_direct_apps_lost": None,
            "ios_sdk_api_market_share_change_pct": None,
            "ios_sdk_api_apps_lost": None,
        }

    def test_company_detail_projects_sdk_ios_installs_from_private_overview(self):
        app = _make_test_app()
        overview = FakeCompanyCategoryOverview(
            categories={
                "all": CategoryCompanyStats(
                    sdk_android_total_apps=123,
                    sdk_ios_total_apps=45,
                    sdk_ios_installs_d30=456,
                )
            },
            company_types=["ad-network"],
        )

        with (
            _patch_key_found("b2b_sdk"),
            _patch_raw_company_detail(overview),
            TestClient(app=app, raise_server_exceptions=False) as client,
        ):
            resp = client.get(
                "/api/v1/companies/google.com",
                headers={"X-API-Key": "ag_companydetail"},
            )

        assert resp.status_code == 200
        assert resp.json()["metrics"]["sdk_ios_installs_d30"] == 456

    def test_company_detail_returns_mapping_notice_for_unmapped_company(self):
        app = _make_test_app()
        overview = FakeCompanyCategoryOverview(
            categories={
                "all": PublicCategoryCompanyStats(
                    total_apps=1,
                    adstxt_direct_android_total_apps=1,
                )
            },
            company_types=[],
            adstxt_ad_domain_overview=None,
            adstxt_publishers_overview=None,
            mediation_adapters=None,
        )

        with (
            _patch_key_found("b2b_sdk"),
            _patch_raw_company_detail(overview),
            TestClient(app=app, raise_server_exceptions=False) as client,
        ):
            resp = client.get(
                "/api/v1/companies/google.com",
                headers={"X-API-Key": "ag_companydetail"},
            )

        assert resp.status_code == 200
        assert resp.json()["company_types"] == []
        assert resp.json()["domain_is_mapped"] is False
        assert resp.json()["mapping_notice"] == UNMAPPED_COMPANY_NOTICE

    def test_company_detail_returns_404_for_empty_company_payload(self):
        app = _make_test_app()
        overview = FakeCompanyCategoryOverview(
            categories={"all": PublicCategoryCompanyStats()},
            company_types=[],
            adstxt_ad_domain_overview=None,
            adstxt_publishers_overview=None,
            mediation_adapters=None,
        )

        with (
            _patch_key_found("b2b_sdk"),
            _patch_raw_company_detail(overview),
            TestClient(app=app, raise_server_exceptions=False) as client,
        ):
            resp = client.get(
                "/api/v1/companies/missing.example",
                headers={"X-API-Key": "ag_missingcompany"},
            )

        assert resp.status_code == 404
        assert "Company domain not found" in resp.json()["detail"]


class TestV1CompanyAppChanges:
    def test_apps_added_returns_platform_app_lists(self):
        app = _make_test_app()
        payload = PublicCompanyAppChangeStoreIds(
            company_domain="google.com",
            tag_source="sdk",
            year=2026,
            quarter=1,
            status="added",
            android_apps=["com.example.first"],
            ios_apps=["id123456"],
        )

        with (
            _patch_key_found("b2b_sdk"),
            patch(
                "api_app.controllers.public.v1.companies._build_public_company_app_change_payload",
                return_value=payload,
            ),
            TestClient(app=app, raise_server_exceptions=False) as client,
        ):
            resp = client.get(
                "/api/v1/companies/google.com/app-changes",
                headers={"X-API-Key": "ag_companychanges"},
                params={
                    "status": "added",
                    "tag_source": "sdk",
                    "year": 2026,
                    "quarter": 1,
                },
            )

        assert resp.status_code == 200
        assert resp.json() == {
            "company_domain": "google.com",
            "tag_source": "sdk",
            "year": 2026,
            "quarter": 1,
            "status": "added",
            "android_apps": ["com.example.first"],
            "ios_apps": ["id123456"],
        }

    def test_apps_lost_rejects_invalid_tag_source(self):
        app = _make_test_app()
        with (
            _patch_key_found("b2b_sdk"),
            TestClient(app=app, raise_server_exceptions=False) as client,
        ):
            resp = client.get(
                "/api/v1/companies/google.com/app-changes",
                headers={"X-API-Key": "ag_companychanges"},
                params={
                    "status": "removed",
                    "tag_source": "invalid",
                    "year": 2026,
                    "quarter": 1,
                },
            )

        assert resp.status_code == 400
        assert "tag_source must be one of" in resp.json()["detail"]

    def test_build_public_company_app_change_payload_uses_shared_platform_lists(self):
        with _patch_company_app_change_store_ids_by_platform(
            {
                "android_apps": ["com.example.first"],
                "ios_apps": ["id123456"],
            }
        ):
            payload = v1_companies._build_public_company_app_change_payload(
                state=MagicMock(),
                company_domain="google.com",
                tag_source="sdk",
                year=2026,
                quarter=1,
                status="removed",
            )

        assert payload == PublicCompanyAppChangeStoreIds(
            company_domain="google.com",
            tag_source="sdk",
            year=2026,
            quarter=1,
            status="removed",
            android_apps=["com.example.first"],
            ios_apps=["id123456"],
        )

    def test_build_public_company_app_change_payload_maps_lost_to_removed(self):
        with patch(
            "api_app.controllers.public.v1.companies.get_company_app_change_store_ids_by_platform",
            return_value={"android_apps": [], "ios_apps": []},
        ) as get_store_ids:
            v1_companies._build_public_company_app_change_payload(
                state=MagicMock(),
                company_domain="adcolony.com",
                tag_source="sdk",
                year=2026,
                quarter=3,
                status="lost",
            )

        assert get_store_ids.call_args.kwargs["status"] == "removed"


class TestV1Apps:
    def test_mapped_sdks_requires_b2b_sdk_tier(self):
        app = _make_test_app()
        with (
            _patch_key_found("free"),
            TestClient(app=app, raise_server_exceptions=False) as client,
        ):
            resp = client.get(
                "/api/v1/apps/com.example.app/mapped-sdks",
                headers={"X-API-Key": "ag_mapped_sdks_free"},
            )

        assert resp.status_code == 403
        assert "B2B SDK" in resp.json()["detail"]

    def test_mapped_sdks_returns_company_grouped_slugs(self):
        app = _make_test_app()
        with (
            _patch_key_found("b2b_sdk"),
            _patch_mapped_sdks(
                [
                    {"company_domain": "adjust.com", "sdk_slug": "adjust"},
                    {"company_domain": "unity.com", "sdk_slug": "unity-ads"},
                    {"company_domain": "adjust.com", "sdk_slug": "adjust-signals"},
                ]
            ),
            TestClient(app=app, raise_server_exceptions=False) as client,
        ):
            resp = client.get(
                "/api/v1/apps/com.example.app/mapped-sdks",
                headers={"X-API-Key": "ag_mapped_sdks"},
            )

        assert resp.status_code == 200
        assert resp.json() == {
            "store_id": "com.example.app",
            "mapped_sdks": {
                "adjust.com": ["adjust", "adjust-signals"],
                "unity.com": ["unity-ads"],
            },
        }

    def test_app_version_timeline_requires_b2b_sdk_tier(self):
        app = _make_test_app()
        with (
            _patch_key_found("free"),
            TestClient(app=app, raise_server_exceptions=False) as client,
        ):
            resp = client.get(
                "/api/v1/apps/com.example.app/versions",
                headers={"X-API-Key": "ag_versions_free"},
            )

        assert resp.status_code == 403
        assert "B2B SDK" in resp.json()["detail"]

    def test_app_version_timeline_returns_expected_rows(self):
        app = _make_test_app()
        timeline_rows = [
            {
                "app_version_code": "-1",
                "sdk_scan_result": 0,
                "sdks_last_scanned_at": None,
                "downloaded_at": "2026-04-01T12:00:00",
            },
            {
                "app_version_code": "42",
                "sdk_scan_result": 1,
                "sdks_last_scanned_at": "2026-05-02T12:00:00",
                "downloaded_at": "2026-05-01T12:00:00",
            },
            {
                "app_version_code": "41",
                "sdk_scan_result": 0,
                "sdks_last_scanned_at": None,
                "downloaded_at": "2026-04-01T12:00:00",
            },
        ]
        with (
            _patch_key_found("b2b_sdk"),
            _patch_single_app({"store_id": "com.example.app"}),
            _patch_version_timeline(timeline_rows),
            TestClient(app=app, raise_server_exceptions=False) as client,
        ):
            resp = client.get(
                "/api/v1/apps/com.example.app/versions",
                headers={"X-API-Key": "ag_versions"},
            )

        assert resp.status_code == 200
        assert resp.json() == [
            {
                **timeline_rows[1],
                "sdk_scan_result": "success",
            },
            {
                **timeline_rows[2],
                "sdk_scan_result": "failure",
            },
        ]

    @pytest.mark.parametrize(
        "path",
        [
            "/api/v1/apps/com.unknown.app/versions",
            "/api/v1/apps/com.unknown.app/sdks/history",
        ],
    )
    def test_app_version_endpoints_return_404_for_unknown_apps(self, path):
        app = _make_test_app()
        with (
            _patch_key_found("b2b_sdk"),
            _patch_single_app(None),
            TestClient(app=app, raise_server_exceptions=False) as client,
        ):
            resp = client.get(
                path,
                headers={"X-API-Key": "ag_versions"},
            )

        assert resp.status_code == 404

    def test_app_sdk_history_returns_expected_shape(self):
        app = _make_test_app()
        history_rows = [
            {
                "company_name": "Adjust",
                "company_domain": "adjust.com",
                "sdk_name": "Adjust SDK",
                "version_code": "42",
                "version_code_created_at": "2026-05-01T12:00:00",
                "sdk_scan_result": 1,
                "status": "added",
            },
            {
                "company_name": None,
                "company_domain": None,
                "sdk_name": None,
                "version_code": "41",
                "version_code_created_at": "2026-04-01T12:00:00",
                "sdk_scan_result": 0,
                "status": None,
            },
        ]
        with (
            _patch_key_found("b2b_premium"),
            _patch_single_app({"store_id": "com.example.app"}),
            _patch_sdk_history(history_rows),
            patch(
                "api_app.controllers.public.v1.apps.get_company_logos_df",
                return_value=pd.DataFrame(
                    [{"company_domain": "adjust.com", "company_logo_url": "adjust.png"}]
                ),
            ),
            TestClient(app=app, raise_server_exceptions=False) as client,
        ):
            resp = client.get(
                "/api/v1/apps/com.example.app/sdks/history",
                headers={"X-API-Key": "ag_sdk_history"},
            )

        assert resp.status_code == 200
        assert resp.json() == {
            "history": [
                {
                    **history_rows[0],
                    "sdk_scan_result": "success",
                    "company_logo_url": "adjust.png",
                },
                {
                    **history_rows[1],
                    "sdk_scan_result": "failure",
                    "status": "no_change",
                    "company_logo_url": None,
                },
            ]
        }

    def test_app_basics_logs_umami_page_view_with_user_id(self):
        app = _make_test_app()
        app_row = {
            "name": "Example App",
            "store_id": "com.example.app",
            "store": "Google Play",
            "category": "tools",
            "rating": 4.5,
            "rating_count": 100,
            "installs": 50000,
            "weekly_active_users": 3200,
            "monthly_active_users": 12800,
            "monthly_ad_revenue": 1200.5,
            "monthly_iap_revenue": 875.25,
            "installs_sum_1w": 1400,
            "installs_sum_4w": 5300,
            "ratings_sum_1w": 43,
            "store_last_updated": "2026-05-01",
            "developer_id": "dev123",
            "developer_name": "Example Dev",
            "developer_url": "https://example.com/dev",
            "release_date": "2024-01-01",
            "ad_supported": True,
            "in_app_purchases": False,
            "store_link": "https://play.google.com/store/apps/details?id=com.example.app",
        }

        with (
            _patch_key_found("free"),
            _patch_single_app(app_row),
            patch("api_app.analytics.log_umami_page") as log_umami_page,
            TestClient(app=app, raise_server_exceptions=False) as client,
        ):
            resp = client.get(
                "/api/v1/apps/com.example.app",
                headers={
                    "X-API-Key": "ag_appkey",
                    "X-Forwarded-For": "203.0.113.10",
                },
            )

        assert resp.status_code == 200
        log_umami_page.assert_called_once_with(
            url="/api/v1/apps/com.example.app",
            ip="203.0.113.10",
            user_id=1,
            page_title=None,
            hostname=PUBLIC_API_HOSTNAME,
            referrer=None,
        )

    def test_app_basics_returns_expected_fields(self):
        app = _make_test_app()
        app_row = {
            "id": 1,
            "name": "Example App",
            "store_id": "com.example.app",
            "store": "Google Play",
            "category": "tools",
            "rating": 4.5,
            "rating_count": 100,
            "installs": 50000,
            "weekly_active_users": 3200,
            "monthly_active_users": 12800,
            "monthly_ad_revenue": 1200.5,
            "monthly_iap_revenue": 875.25,
            "installs_sum_1w": 1400,
            "installs_sum_4w": 5300,
            "ratings_sum_1w": 43,
            "store_last_updated": "2026-05-01",
            "developer_id": "dev123",
            "developer_name": "Example Dev",
            "developer_url": "https://example.com/dev",
            "release_date": "2024-01-01",
            "ad_supported": True,
            "in_app_purchases": False,
            "tv_supported": True,
            "app_icon_url": "https://media.appgoblin.info/icon.png",
            "store_link": "https://play.google.com/store/apps/details?id=com.example.app",
            "ad_creative_count": 12,
            "ad_monetized_creative_count": 4,
            "description": "ignored",
        }
        with (
            _patch_key_found("free"),
            _patch_single_app(app_row),
            TestClient(app=app, raise_server_exceptions=False) as client,
        ):
            resp = client.get(
                "/api/v1/apps/com.example.app",
                headers={"X-API-Key": "ag_appkey"},
            )

        assert resp.status_code == 200
        assert resp.json() == {
            "name": "Example App",
            "store_id": "com.example.app",
            "store": "Google Play",
            "category": "tools",
            "rating": 4.5,
            "rating_count": 100,
            "installs": 50000,
            "weekly_active_users": 3200,
            "monthly_active_users": 12800,
            "monthly_ad_revenue": 1200.5,
            "monthly_iap_revenue": 875.25,
            "installs_weekly": 1400,
            "installs_monthly": 5300,
            "rating_count_weekly": 43,
            "store_last_updated": "2026-05-01",
            "developer_id": "dev123",
            "developer_name": "Example Dev",
            "developer_url": "https://example.com/dev",
            "release_date": "2024-01-01",
            "ad_supported": True,
            "in_app_purchases": False,
            "tv_supported": True,
            "store_link": "https://play.google.com/store/apps/details?id=com.example.app",
        }
        assert "id" not in resp.json()
        assert "app_icon_url" not in resp.json()
        assert "ad_creative_count" not in resp.json()
        assert "ad_monetized_creative_count" not in resp.json()

    def test_app_basics_returns_404_for_unknown_store_id(self):
        app = _make_test_app()
        with (
            _patch_key_found("free"),
            _patch_single_app(None),
            TestClient(app=app, raise_server_exceptions=False) as client,
        ):
            resp = client.get(
                "/api/v1/apps/com.missing.app",
                headers={"X-API-Key": "ag_missingapp"},
            )

        assert resp.status_code == 404
        assert "Store ID not found" in resp.json()["detail"]

    @pytest.mark.parametrize(
        ("tv_supported", "expected"),
        [
            (True, True),
            (False, False),
            (None, False),
            (float("nan"), False),
        ],
    )
    def test_app_basics_tv_supported_only_true_is_true(self, tv_supported, expected):
        app = _make_test_app()
        app_row = {
            "store_id": "com.example.app",
            "name": "Example App",
            "tv_supported": tv_supported,
        }
        with (
            _patch_key_found("free"),
            _patch_single_app(app_row),
            TestClient(app=app, raise_server_exceptions=False) as client,
        ):
            resp = client.get(
                "/api/v1/apps/com.example.app",
                headers={"X-API-Key": "ag_appkey"},
            )

        assert resp.status_code == 200
        assert resp.json()["tv_supported"] is expected

    def test_app_ranks_returns_expected_shape(self):
        app = _make_test_app()
        rank_rows = [
            {
                "country": "US",
                "collection": "GROSSING",
                "category": "GAME_STRATEGY",
                "best_rank": 26,
            },
            {
                "country": "BD",
                "collection": "GROSSING",
                "category": "GAME_STRATEGY",
                "best_rank": 169,
            },
        ]
        with (
            _patch_key_found("free"),
            _patch_ranks(rank_rows),
            TestClient(app=app, raise_server_exceptions=False) as client,
        ):
            resp = client.get(
                "/api/v1/apps/com.example.app/ranks",
                headers={"X-API-Key": "ag_rankhistory"},
            )

        assert resp.status_code == 200
        assert resp.json() == rank_rows

    def test_app_ranks_returns_empty_shape_when_missing(self):
        app = _make_test_app()
        with (
            _patch_key_found("free"),
            _patch_ranks([]),
            TestClient(app=app, raise_server_exceptions=False) as client,
        ):
            resp = client.get(
                "/api/v1/apps/com.example.app/ranks",
                headers={"X-API-Key": "ag_rankhistoryempty"},
            )

        assert resp.status_code == 200
        assert resp.json() == []

    def test_company_list_logs_umami_page_view_with_user_id(self):
        app = _make_test_app()

        with (
            _patch_key_found("b2b_sdk"),
            _patch_overview(),
            patch("api_app.analytics.log_umami_page") as log_umami_page,
            TestClient(app=app, raise_server_exceptions=False) as client,
        ):
            resp = client.get(
                "/api/v1/companies",
                headers={
                    "X-API-Key": "ag_companylist",
                    "X-Forwarded-For": "198.51.100.7",
                },
            )

        assert resp.status_code == 200
        log_umami_page.assert_called_once_with(
            url="/api/v1/companies",
            ip="198.51.100.7",
            user_id=1,
            page_title=None,
            hostname=PUBLIC_API_HOSTNAME,
            referrer=None,
        )

    def test_app_sdks_returns_expected_shape(self):
        app = _make_test_app()
        sdk_rows = [
            {
                "xml_path": "uses-permission",
                "value_name": "android.permission.INTERNET",
                "category_slug": None,
                "company_domain": None,
                "company_name": None,
            },
            {
                "xml_path": "queries/package",
                "value_name": "com.adjust.sdk",
                "category_slug": "measurement",
                "company_domain": "adjust.com",
                "company_name": "Adjust",
            },
            {
                "xml_path": "application/activity",
                "value_name": "com.adjust.sdk.Adjust",
                "category_slug": "measurement",
                "company_domain": "adjust.com",
                "company_name": "Adjust",
            },
            {
                "xml_path": "SKAdNetworkItems",
                "value_name": "cstr6suwn9.skadnetwork",
                "category_slug": None,
                "company_domain": None,
                "company_name": None,
            },
            {
                "xml_path": "application/meta-data",
                "value_name": "mystery.vendor.sdk",
                "category_slug": None,
                "company_domain": None,
                "company_name": None,
            },
        ]
        with (
            _patch_key_found("free"),
            _patch_sdk_details(sdk_rows),
            TestClient(app=app, raise_server_exceptions=False) as client,
        ):
            resp = client.get(
                "/api/v1/apps/com.example.app/sdks",
                headers={"X-API-Key": "ag_sdkdetails"},
            )

        assert resp.status_code == 200
        assert resp.json() == {
            "company_categories": {
                "measurement": {
                    "adjust.com": {
                        "com.adjust": {
                            "application/activity": ["com.adjust.sdk.Adjust"],
                            "queries/package": ["com.adjust.sdk"],
                        }
                    }
                }
            },
            "permissions": ["INTERNET"],
            "app_queries": ["com.adjust.sdk"],
            "skadnetwork": ["cstr6suwn9.skadnetwork"],
            "unmapped_sdks": {
                "mystery.vendor": {"application/meta-data": ["mystery.vendor.sdk"]}
            },
        }

    def test_company_detail_builds_signed_dataset_urls(self):
        app = _make_test_app()
        overview = FakeCompanyCategoryOverview(
            categories={
                "all": CategoryCompanyStats(
                    sdk_android_total_apps=123,
                    sdk_ios_total_apps=45,
                )
            },
            company_types=["ad-network"],
        )

        with (
            _patch_key_found("b2b_sdk"),
            _patch_raw_company_detail(overview),
            patch(
                "api_app.controllers.public.v1.companies.get_signed_download_url",
                side_effect=lambda key: f"signed://{key}",
            ),
            TestClient(app=app, raise_server_exceptions=False) as client,
        ):
            resp = client.get(
                "/api/v1/companies/google.com",
                headers={"X-API-Key": "ag_companydetail"},
            )

        assert resp.status_code == 200
        assert resp.json()["datasets"] == {
            "sdk_api_android": {
                "available": True,
                "estimated_rows": 123,
                "url": (
                    "signed://downloads/company-verified-apps/domains/"
                    "domain=google.com/source=all/"
                    "appgoblin_google.com_android_verified_apps.csv"
                ),
            },
            "sdk_api_ios": {
                "available": True,
                "estimated_rows": 45,
                "url": (
                    "signed://downloads/company-verified-apps/domains/"
                    "domain=google.com/source=all/"
                    "appgoblin_google.com_ios_verified_apps.csv"
                ),
            },
            "parent_company_android": {
                "available": False,
                "estimated_rows": 0,
                "url": None,
            },
            "parent_company_ios": {
                "available": False,
                "estimated_rows": 0,
                "url": None,
            },
        }

    def test_app_sdks_returns_empty_shape_when_missing(self):
        app = _make_test_app()
        with (
            _patch_key_found("free"),
            _patch_sdk_details([]),
            TestClient(app=app, raise_server_exceptions=False) as client,
        ):
            resp = client.get(
                "/api/v1/apps/com.example.app/sdks",
                headers={"X-API-Key": "ag_sdkdetailsempty"},
            )

        assert resp.status_code == 200
        assert resp.json() == {
            "company_categories": {},
            "permissions": [],
            "app_queries": [],
            "skadnetwork": [],
            "unmapped_sdks": {},
        }


class TestV1CtvAppRanks:
    def test_ctv_app_ranks_requires_api_key(self):
        app = _make_test_app()
        with TestClient(app=app, raise_server_exceptions=False) as client:
            resp = client.get("/api/v1/rankings/ctv/1")

        assert resp.status_code == 401

    def test_ctv_app_ranks_returns_expected_shape(self):
        app = _make_test_app()
        rank_rows = [
            {
                "rank_num": 1,
                "app_name": "Example TV App",
                "store_id": "com.example.tv",
                "store": 1,
                "icon_64": "icon.png",
                "app_category": "video_players",
                "developer_name": "Example Dev",
                "developer_id": "dev123",
                "rating": 4.5,
                "rating_count": 1000,
                "installs": 500000,
                "monthly_installs": 25000.0,
                "monthly_revenue": 1200.5,
                "installs_z_score_2w": 812.44,
                "country_code": "US",
            }
        ]
        with (
            _patch_key_found("free"),
            _patch_ctv_app_ranks(rank_rows),
            TestClient(app=app, raise_server_exceptions=False) as client,
        ):
            resp = client.get(
                "/api/v1/rankings/ctv/1",
                headers={"X-API-Key": "ag_ctvranks"},
            )

        assert resp.status_code == 200
        payload = resp.json()
        assert payload["store"] == "Google Play"
        assert payload["country"] == "US"
        assert payload["apps"] == [
            {
                "rank": 1,
                "name": "Example TV App",
                "store_id": "com.example.tv",
                "store": "Google Play",
                "category": "video_players",
                "developer_name": "Example Dev",
                "rating": 4.5,
                "rating_count": 1000,
                "installs": 500000,
                "monthly_installs": 25000.0,
                "monthly_revenue": 1200.5,
                "installs_z_score_2w": 812.44,
                "country": "US",
                "app_icon_url": (
                    "https://media.appgoblin.info/app-icons/com.example.tv/icon.png"
                ),
            }
        ]

    def test_ctv_app_ranks_returns_empty_shape_when_missing(self):
        app = _make_test_app()
        with (
            _patch_key_found("free"),
            _patch_ctv_app_ranks([]),
            TestClient(app=app, raise_server_exceptions=False) as client,
        ):
            resp = client.get(
                "/api/v1/rankings/ctv/2",
                headers={"X-API-Key": "ag_ctvranksempty"},
            )

        assert resp.status_code == 200
        assert resp.json() == {
            "store": "Apple App Store",
            "country": "US",
            "apps": [],
        }

    def test_ctv_app_ranks_rejects_unknown_store(self):
        app = _make_test_app()
        with (
            _patch_key_found("free"),
            TestClient(app=app, raise_server_exceptions=False) as client,
        ):
            resp = client.get(
                "/api/v1/rankings/ctv/9",
                headers={"X-API-Key": "ag_ctvranksbadstore"},
            )

        assert resp.status_code == 404
        assert "Unknown store" in resp.json()["detail"]

    def test_ctv_app_ranks_logs_umami_page_view_with_user_id(self):
        app = _make_test_app()
        with (
            _patch_key_found("free"),
            _patch_ctv_app_ranks([]),
            patch("api_app.analytics.log_umami_page") as log_umami_page,
            TestClient(app=app, raise_server_exceptions=False) as client,
        ):
            resp = client.get(
                "/api/v1/rankings/ctv/1",
                headers={
                    "X-API-Key": "ag_ctvranksumami",
                    "X-Forwarded-For": "203.0.113.10",
                },
            )

        assert resp.status_code == 200
        log_umami_page.assert_called_once_with(
            url="/api/v1/rankings/ctv/1",
            ip="203.0.113.10",
            user_id=1,
            page_title=None,
            hostname=PUBLIC_API_HOSTNAME,
            referrer=None,
        )


class TestV1Keywords:
    def test_keyword_metrics_logs_umami_page_view_with_user_id(self):
        app = _make_test_app()
        keyword_rows = [
            {
                "store": 1,
                "app_count": 420,
                "total_apps": 1960,
                "median_competitor_installs": 250000,
                "avg_competitor_rating": 4.3,
                "major_competitors": 18,
                "volume_competition_score": 73.1,
                "keyword_difficulty": 61.2,
                "opportunity_score": 69.8,
                "competitiveness_score": 64.5,
            }
        ]

        with (
            _patch_key_found("free"),
            _patch_keyword_details(keyword_rows),
            patch("api_app.analytics.log_umami_page") as log_umami_page,
            TestClient(app=app, raise_server_exceptions=False) as client,
        ):
            resp = client.get(
                "/api/v1/keywords/app privacy",
                headers={
                    "X-API-Key": "ag_keywordkey",
                    "X-Forwarded-For": "203.0.113.11",
                },
            )

        assert resp.status_code == 200
        log_umami_page.assert_called_once_with(
            url="/api/v1/keywords/app privacy",
            ip="203.0.113.11",
            user_id=1,
            page_title=None,
            hostname=PUBLIC_API_HOSTNAME,
            referrer=None,
        )

    def test_keyword_metrics_returns_expected_fields(self):
        app = _make_test_app()
        keyword_rows = [
            {
                "store": 1,
                "app_count": 420,
                "total_apps": 1960,
                "median_competitor_installs": 250000,
                "avg_competitor_rating": 4.3,
                "major_competitors": 18,
                "volume_competition_score": 73.1,
                "keyword_difficulty": 61.2,
                "opportunity_score": 69.8,
                "competitiveness_score": 64.5,
                "keyword_id": 101,
            },
            {
                "store": 2,
                "app_count": 215,
                "total_apps": 910,
                "median_competitor_installs": 175000,
                "avg_competitor_rating": 4.6,
                "major_competitors": 11,
                "volume_competition_score": 68.4,
                "keyword_difficulty": 57.9,
                "opportunity_score": 71.3,
                "competitiveness_score": 59.4,
                "keyword_text": "app privacy",
            },
        ]
        with (
            _patch_key_found("free"),
            _patch_keyword_details(keyword_rows),
            TestClient(app=app, raise_server_exceptions=False) as client,
        ):
            resp = client.get(
                "/api/v1/keywords/app privacy",
                headers={"X-API-Key": "ag_keywordkey"},
            )

        assert resp.status_code == 200
        assert resp.json() == {
            "keyword": "app privacy",
            "country": "US",
            "android": {
                "app_count": 420,
                "total_apps": 1960,
                "median_competitor_installs": 250000,
                "avg_competitor_rating": 4.3,
                "major_competitors": 18,
                "volume_competition_score": 73.1,
                "keyword_difficulty": 61.2,
                "opportunity_score": 69.8,
                "competitiveness_score": 64.5,
            },
            "ios": {
                "app_count": 215,
                "total_apps": 910,
                "median_competitor_installs": 175000,
                "avg_competitor_rating": 4.6,
                "major_competitors": 11,
                "volume_competition_score": 68.4,
                "keyword_difficulty": 57.9,
                "opportunity_score": 71.3,
                "competitiveness_score": 59.4,
            },
        }
        assert "keyword_id" not in resp.text

    def test_keyword_metrics_returns_404_for_unknown_keyword(self):
        app = _make_test_app()
        with (
            _patch_key_found("free"),
            _patch_keyword_details([]),
            TestClient(app=app, raise_server_exceptions=False) as client,
        ):
            resp = client.get(
                "/api/v1/keywords/missing keyword",
                headers={"X-API-Key": "ag_missingkeyword"},
            )

        assert resp.status_code == 404
        assert "Keyword not found" in resp.json()["detail"]

    def test_keyword_ranks_logs_umami_page_view_with_user_id(self):
        app = _make_test_app()
        rank_rows = [
            {
                "name": "Example App",
                "store": 1,
                "store_id": "com.example.app",
                "installs": 50000,
                "rating_count": 100,
                "icon_url_100": "icon.png",
                "category": "tools",
                "latest_app_rank": 4,
                "d30_best_rank": 2,
            }
        ]

        with (
            _patch_key_found("free"),
            _patch_keyword_apps(rank_rows),
            patch("api_app.analytics.log_umami_page") as log_umami_page,
            TestClient(app=app, raise_server_exceptions=False) as client,
        ):
            resp = client.get(
                "/api/v1/keywords/app privacy/ranks",
                headers={
                    "X-API-Key": "ag_keywordkey",
                    "X-Forwarded-For": "203.0.113.11",
                },
            )

        assert resp.status_code == 200
        log_umami_page.assert_called_once_with(
            url="/api/v1/keywords/app privacy/ranks",
            ip="203.0.113.11",
            user_id=1,
            page_title=None,
            hostname=PUBLIC_API_HOSTNAME,
            referrer=None,
        )

    @pytest.mark.parametrize("limit, expected_status", [(200, 200), (201, 400)])
    def test_keyword_ranks_limit_maximum(self, limit, expected_status):
        app = _make_test_app()
        rows = [{"name": "Example", "store": 1, "latest_app_rank": 1}]
        with (
            _patch_key_found("free"),
            _patch_keyword_apps(rows) as get_apps,
            TestClient(app=app, raise_server_exceptions=False) as client,
        ):
            resp = client.get(
                f"/api/v1/keywords/app privacy/ranks?limit={limit}",
                headers={"X-API-Key": "ag_keywordkey"},
            )

        assert resp.status_code == expected_status
        if limit == 200:
            assert get_apps.call_args.kwargs["rank"] == 201
        else:
            get_apps.assert_not_called()

    def test_keyword_ranks_returns_expected_fields(self):
        app = _make_test_app()
        rank_rows = [
            {
                "name": "Example Android App",
                "store": 1,
                "store_id": "com.example.app",
                "installs": 50000,
                "rating_count": 100,
                "icon_url_100": "icon.png",
                "category": "tools",
                "latest_app_rank": 4,
                "d30_best_rank": 2,
            },
            {
                "name": "Example iPhone App",
                "store": 2,
                "store_id": "id123456",
                "installs": 1200,
                "rating_count": 94,
                "icon_url_100": "ios-icon.png",
                "category": "utilities",
                "latest_app_rank": 6,
                "d30_best_rank": 3,
            },
        ]
        with (
            _patch_key_found("free"),
            _patch_keyword_apps(rank_rows),
            TestClient(app=app, raise_server_exceptions=False) as client,
        ):
            resp = client.get(
                "/api/v1/keywords/app privacy/ranks",
                headers={"X-API-Key": "ag_keywordkey"},
            )

        assert resp.status_code == 200
        assert resp.json() == {
            "keyword": "app privacy",
            "country": "US",
            "android": [
                {
                    "name": "Example Android App",
                    "store_id": "com.example.app",
                    "category": "tools",
                    "installs": 50000,
                    "rating_count": 100,
                    "app_icon_url": (
                        "https://media.appgoblin.info/app-icons/"
                        "com.example.app/icon.png"
                    ),
                    "latest_rank": 4,
                    "best_rank_d30": 2,
                }
            ],
            "ios": [
                {
                    "name": "Example iPhone App",
                    "store_id": "id123456",
                    "category": "utilities",
                    "installs": 1200,
                    "rating_count": 94,
                    "app_icon_url": (
                        "https://media.appgoblin.info/app-icons/"
                        "id123456/ios-icon.png"
                    ),
                    "latest_rank": 6,
                    "best_rank_d30": 3,
                }
            ],
        }

    def test_keyword_ranks_returns_empty_lists_for_known_keyword_without_ranks(self):
        app = _make_test_app()
        keyword_rows = [
            {
                "store": 1,
                "app_count": 420,
                "total_apps": 1960,
                "median_competitor_installs": 250000,
                "avg_competitor_rating": 4.3,
                "major_competitors": 18,
                "volume_competition_score": 73.1,
                "keyword_difficulty": 61.2,
                "opportunity_score": 69.8,
                "competitiveness_score": 64.5,
            }
        ]
        with (
            _patch_key_found("free"),
            _patch_keyword_details(keyword_rows),
            _patch_keyword_apps([]),
            TestClient(app=app, raise_server_exceptions=False) as client,
        ):
            resp = client.get(
                "/api/v1/keywords/app privacy/ranks",
                headers={"X-API-Key": "ag_keywordemptyranks"},
            )

        assert resp.status_code == 200
        assert resp.json() == {
            "keyword": "app privacy",
            "country": "US",
            "android": [],
            "ios": [],
        }

    def test_keyword_ranks_returns_404_for_unknown_keyword(self):
        app = _make_test_app()
        with (
            _patch_key_found("free"),
            _patch_keyword_details([]),
            _patch_keyword_apps([]),
            TestClient(app=app, raise_server_exceptions=False) as client,
        ):
            resp = client.get(
                "/api/v1/keywords/missing keyword/ranks",
                headers={"X-API-Key": "ag_missingkeywordranks"},
            )

        assert resp.status_code == 404
        assert "Keyword not found" in resp.json()["detail"]


class TestV1Docs:
    def test_openapi_json_matches_public_v1_paths_and_schema_properties(self):
        app = _make_docs_test_app()
        with TestClient(app=app, raise_server_exceptions=False) as client:
            resp = client.get("/api/v1/docs/openapi.json")

        assert resp.status_code == 200
        data = resp.json()

        assert set(data["paths"]) == {
            "/api/v1/apps/search",
            "/api/v1/apps/search/developers",
            "/api/v1/companies/search",
            "/api/v1/apps/{store_id}",
            "/api/v1/apps/{store_id}/ranks",
            "/api/v1/apps/{store_id}/mapped-sdks",
            "/api/v1/apps/{store_id}/sdks",
            "/api/v1/apps/{store_id}/versions",
            "/api/v1/apps/{store_id}/sdks/history",
            "/api/v1/apps/{store_id}/sdks/history",
            "/api/v1/companies",
            "/api/v1/companies/{company_domain}/sdks",
            "/api/v1/sdks/{sdk_slug}",
            "/api/v1/companies/{company_domain}",
            "/api/v1/companies/{company_domain}/app-changes",
            "/api/v1/keywords/{keyword}",
            "/api/v1/keywords/{keyword}/ranks",
            "/api/v1/rankings/ctv/{store}",
        }

        expected_schema_fields = {
            model.__name__: sorted(field.name for field in fields(model))
            for model in (
                v1_public_models.CompanyDatasetTarget,
                v1_public_models.CompanyDatasets,
                v1_public_models.PublicAppBasics,
                v1_public_models.PublicAppBestRank,
                v1_public_models.PublicAppSdkDetails,
                v1_public_models.PublicAppSdkHistory,
                v1_public_models.PublicCategoryCompanyStats,
                v1_public_models.PublicCompanyAppChangeStoreIds,
                v1_public_models.PublicCompanyListItem,
                v1_public_models.PublicCompanyOverview,
                v1_public_models.PublicCompanyTrends,
                v1_public_models.PublicCtvAppRank,
                v1_public_models.PublicCtvAppRanks,
                v1_public_models.PublicKeywordMetrics,
                v1_public_models.PublicKeywordPlatformMetrics,
                v1_public_models.PublicKeywordRankedApp,
                v1_public_models.PublicKeywordRanks,
            )
        }
        actual_schema_fields = {
            schema_name: sorted(schema.get("properties", {}))
            for schema_name, schema in data["components"]["schemas"].items()
            if schema_name in expected_schema_fields
        }

        assert actual_schema_fields == expected_schema_fields

    def test_openapi_json_only_lists_public_v1_paths(self):
        app = _make_docs_test_app()
        with TestClient(app=app, raise_server_exceptions=False) as client:
            resp = client.get("/api/v1/docs/openapi.json")

        assert resp.status_code == 200
        data = resp.json()
        assert data["info"]["title"] == "AppGoblin Public API v1"
        assert data["info"]["version"] == "0.1.0"
        assert "Bearer" in data["info"]["description"]
        assert "## Rate Limits" in data["info"]["description"]
        assert "## Plans & Access" in data["info"]["description"]
        assert "https://appgoblin.info/pricing" in data["info"]["description"]
        assert "vary by subscription tier" in data["info"]["description"]
        assert "30 requests per minute" not in data["info"]["description"]
        assert "1,000 requests per day" not in data["info"]["description"]
        assert "X-RateLimit-Limit" in data["info"]["description"]
        assert "429 Too Many Requests" in data["info"]["description"]
        assert "## AI & Raw Spec" in data["info"]["description"]
        assert "/api/v1/docs/openapi.json" in data["info"]["description"]
        assert data["servers"] == [{"url": "https://appgoblin.info"}]
        assert data["components"]["securitySchemes"]["BearerAuth"]["scheme"] == "bearer"
        assert data["security"] == [{"BearerAuth": []}]
        assert "/health" not in data["paths"]
        assert "/api/v1/apps/{store_id}/sdksoverview" not in data["paths"]
        assert "/api/v1/keywords/{keyword}" in data["paths"]
        assert data["paths"]
        assert all(path.startswith("/api/v1/") for path in data["paths"])
        assert "PublicAppSdkOverview" not in data["components"]["schemas"]
        versions_operation = data["paths"]["/api/v1/apps/{store_id}/versions"]["get"]
        assert versions_operation["summary"] == "[Paid] /apps/{store_id}/versions"
        assert "B2B SDK and B2B Premium tiers only" in versions_operation["description"]
        assert versions_operation["responses"]["200"]["content"]["application/json"][
            "examples"
        ]
        history_operation = data["paths"]["/api/v1/apps/{store_id}/sdks/history"]["get"]
        assert history_operation["summary"] == "[Paid] /apps/{store_id}/sdks/history"
        assert "B2B SDK and B2B Premium tiers only" in history_operation["description"]
        app_basics_operation = data["paths"]["/api/v1/apps/{store_id}"]["get"]
        store_id_parameter = next(
            parameter
            for parameter in app_basics_operation["parameters"]
            if parameter["name"] == "store_id"
        )
        assert store_id_parameter["example"] == "dev.thirdgate.appgoblin"
        examples = app_basics_operation["responses"]["200"]["content"][
            "application/json"
        ]["examples"]
        assert examples["appgoblin_android_app"]["value"]["store_id"] == (
            "dev.thirdgate.appgoblin"
        )
        assert examples["appgoblin_android_app"]["value"]["name"] == (
            "AppGoblin: Scan Trackers & SDK"
        )
        assert "id" not in examples["appgoblin_android_app"]["value"]
        assert "app_icon_url" not in examples["appgoblin_android_app"]["value"]
        assert "ad_creative_count" not in examples["appgoblin_android_app"]["value"]
        assert (
            "ad_monetized_creative_count"
            not in examples["appgoblin_android_app"]["value"]
        )
        assert app_basics_operation["summary"] == "/apps/{store_id}"
        assert (
            app_basics_operation["description"]
            == "Endpoint: `GET /api/v1/apps/{store_id}`\n\n"
            "Returns stable public app metadata plus MAU, recent install, and "
            "estimated revenue signals for a single app."
        )
        app_ranks_operation = data["paths"]["/api/v1/apps/{store_id}/ranks"]["get"]
        assert [
            parameter["name"] for parameter in app_ranks_operation["parameters"]
        ] == ["store_id"]
        assert app_ranks_operation["summary"] == "/apps/{store_id}/ranks"
        assert (
            app_ranks_operation["description"]
            == "Endpoint: `GET /api/v1/apps/{store_id}/ranks`\n\n"
            "Returns flat best-rank records by country, collection, and category "
            "for the last 90 days."
        )
        assert "/api/v1/apps/{store_id}/ranks/overview" not in data["paths"]
        company_overview_operation = data["paths"][
            "/api/v1/companies/{company_domain}"
        ]["get"]
        companies_operation = data["paths"]["/api/v1/companies"]["get"]
        company_app_changes_operation = data["paths"][
            "/api/v1/companies/{company_domain}/app-changes"
        ]["get"]
        assert companies_operation["summary"] == "[Paid] /companies"
        assert (
            companies_operation["description"]
            == "Endpoint: `GET /api/v1/companies`\n\n"
            "Access: Paid tiers only.\n\n"
            "Returns the public company index with queryable company domains, "
            "display names, parent mappings, installs, and the latest trend "
            "snapshot fields for market share, market-share change, total apps, "
            "apps added, and apps lost."
        )
        companies_examples = companies_operation["responses"]["200"]["content"][
            "application/json"
        ]["examples"]
        assert companies_examples["companies_index"]["value"][0]["company_domain"] == (
            "unity.com"
        )
        assert (
            companies_examples["companies_index"]["value"][0]["trends_latest_period"]
            == "2026Q1"
        )
        assert (
            companies_examples["companies_index"]["value"][0][
                "google_sdk_latest_pct_market_share"
            ]
            == 18.34
        )
        assert (
            companies_examples["companies_index"]["value"][0][
                "google_sdk_latest_total_apps"
            ]
            == 51_202
        )
        assert (
            "google_sdk_latest_total_apps_change_pct"
            not in companies_examples["companies_index"]["value"][0]
        )
        company_domain_parameter = next(
            parameter
            for parameter in company_overview_operation["parameters"]
            if parameter["name"] == "company_domain"
        )
        assert company_domain_parameter["example"] == "unity.com"
        assert (
            company_overview_operation["summary"]
            == "[Paid] /companies/{company_domain}"
        )
        assert (
            company_overview_operation["description"]
            == "Endpoint: `GET /api/v1/companies/{company_domain}`\n\n"
            "Access: Paid tiers only.\n\n"
            "Returns the public company overview for a single domain, including "
            "mapping status, company types, key metrics, a latest-trends summary, "
            "and dataset availability."
        )
        company_examples = company_overview_operation["responses"]["200"]["content"][
            "application/json"
        ]["examples"]
        assert (
            company_examples["unity_company_overview"]["value"]["domain_is_mapped"]
            is True
        )
        assert company_examples["unity_company_overview"]["value"]["company_types"] == [
            "ad-networks",
            "development-tools",
            "mediation",
        ]
        assert (
            company_examples["unity_company_overview"]["value"]["metrics"][
                "sdk_android_total_apps"
            ]
            == 39452
        )
        assert [
            parameter["name"]
            for parameter in company_app_changes_operation["parameters"]
        ] == ["company_domain", "status", "tag_source", "year", "quarter"]
        assert company_app_changes_operation["summary"] == (
            "[Paid] /companies/{company_domain}/app-changes"
        )
        assert (
            company_app_changes_operation["description"]
            == "Endpoint: `GET /api/v1/companies/{company_domain}/app-changes`\n\n"
            "Access: Paid tiers only.\n\n"
            "Returns ordered Android and iOS app store IDs for a known company's "
            "quarterly churn and adoption slice. Use `status=lost` to review apps "
            "that removed the company in that year/quarter window, or `status=added` "
            "to review apps that newly added it, filtered by a single tag source. "
            "This is useful for prospecting, competitor monitoring, and compliance "
            "review when you already know the company domain you want to inspect. "
            "The response is scoped to one company's quarterly delta and does not "
            "directly correlate that company's removal with another company's "
            "addition in the same payload."
        )
        company_app_changes_examples = company_app_changes_operation["responses"][
            "200"
        ]["content"]["application/json"]["examples"]
        assert company_app_changes_examples["unity_company_app_changes_added"][
            "value"
        ] == {
            "company_domain": "unity.com",
            "tag_source": "sdk",
            "year": 2026,
            "quarter": 1,
            "status": "added",
            "android_apps": ["com.example.first"],
            "ios_apps": ["id1234567890"],
        }
        app_sdks_operation = data["paths"]["/api/v1/apps/{store_id}/sdks"]["get"]
        assert app_sdks_operation["summary"] == "/apps/{store_id}/sdks"
        assert (
            app_sdks_operation["description"]
            == "Endpoint: `GET /api/v1/apps/{store_id}/sdks`\n\n"
            "Returns public SDK findings, permissions, package queries, SKAdNetwork "
            "entries, and unmapped evidence for a single app."
        )
        keyword_operation = data["paths"]["/api/v1/keywords/{keyword}"]["get"]
        keyword_parameter = next(
            parameter
            for parameter in keyword_operation["parameters"]
            if parameter["name"] == "keyword"
        )
        assert keyword_parameter["example"] == "app privacy"
        assert keyword_operation["summary"] == "/keywords/{keyword}"
        assert (
            keyword_operation["description"]
            == "Endpoint: `GET /api/v1/keywords/{keyword}`\n\n"
            "Returns per-platform keyword difficulty, competition, and "
            "opportunity metrics for an exact keyword lookup in the US storefront dataset."
        )
        keyword_examples = keyword_operation["responses"]["200"]["content"][
            "application/json"
        ]["examples"]
        assert keyword_examples["keyword_metrics"]["value"]["keyword"] == (
            "app privacy"
        )
        assert (
            keyword_examples["keyword_metrics"]["value"]["android"]["opportunity_score"]
            == 69.8
        )
        keyword_ranks_operation = data["paths"]["/api/v1/keywords/{keyword}/ranks"][
            "get"
        ]
        assert [
            parameter["name"] for parameter in keyword_ranks_operation["parameters"]
        ] == ["keyword", "limit"]
        limit_parameter = keyword_ranks_operation["parameters"][1]
        assert limit_parameter["schema"]["maximum"] == 200
        assert keyword_ranks_operation["summary"] == "/keywords/{keyword}/ranks"
        assert (
            keyword_ranks_operation["description"]
            == "Endpoint: `GET /api/v1/keywords/{keyword}/ranks`\n\n"
            "Returns grouped latest top-ranked Android and iOS apps for an exact "
            "keyword lookup in the US storefront dataset."
        )
        keyword_ranks_examples = keyword_ranks_operation["responses"]["200"]["content"][
            "application/json"
        ]["examples"]
        assert (
            keyword_ranks_examples["keyword_ranks"]["value"]["android"][0][
                "latest_rank"
            ]
            == 4
        )

    def test_openapi_page_renders_scalar(self):
        app = _make_docs_test_app()
        with TestClient(app=app, raise_server_exceptions=False) as client:
            resp = client.get("/api/v1/docs/openapi")

        assert resp.status_code == 200
        assert 'id="api-reference"' in resp.text
        assert '"hideModels":true' in resp.text
        assert '"showDeveloperTools":"never"' in resp.text
        assert '"showToolbar":"localhost"' in resp.text
        assert '"agent":{"disabled":true}' in resp.text
        assert '"mcp":' not in resp.text
        assert 'href="data:text/css,"' in resp.text
        assert "/api/v1/docs/openapi.json" in resp.text
