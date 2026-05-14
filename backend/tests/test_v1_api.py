"""Integration tests for /api/v1 endpoints."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager, contextmanager
from dataclasses import dataclass
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest
from litestar import Litestar
from litestar.middleware import DefineMiddleware
from litestar.openapi.config import OpenAPIConfig
from litestar.testing import TestClient

from api_app.controllers.health import HealthController
from api_app.controllers.public.v1.apps import V1AppsController
from api_app.controllers.public.v1.companies import (
    UNMAPPED_COMPANY_NOTICE,
    V1CompaniesController,
)
from api_app.controllers.public.v1.public_models import PublicCategoryCompanyStats
from api_app.controllers.public.v1.docs import V1DocsController
from api_app.guards import _CachedKey
from app import RateLimitMiddleware


@dataclass
class FakeCompanyDetail:
    company_id: int
    name: str
    count: int


@dataclass
class FakeCompaniesOverview:
    companies_overview: list
    top: object = None
    categories: object = None


@dataclass
class FakeCompanyCategoryOverview:
    categories: dict
    company_types: list | None = None
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
        route_handlers=[V1CompaniesController, V1AppsController],
        lifespan=[_mock_lifespan],
        middleware=[DefineMiddleware(RateLimitMiddleware)],
    )


def _make_docs_test_app():
    return Litestar(
        route_handlers=[
            HealthController,
            V1CompaniesController,
            V1AppsController,
            V1DocsController,
        ],
        lifespan=[_mock_lifespan],
        middleware=[DefineMiddleware(RateLimitMiddleware)],
        openapi_config=OpenAPIConfig(
            title="Test AppGoblin Public API v1", version="0.0.1"
        ),
    )


@pytest.fixture(autouse=True)
def _reset_caches():
    from api_app import guards as g

    g._KEY_CACHE.clear()
    g._LAST_USED_UPDATES.clear()
    g._rate_limiter._buckets.clear()
    g._daily_quota._counters.clear()
    yield


def _patch_key_found(tier="free"):
    return patch(
        "api_app.guards._query_key",
        return_value=_CachedKey(user_id=1, tier=tier, expires_at=9e9),
    )


def _patch_key_not_found():
    return patch("api_app.guards._query_key", return_value=None)


FAKE_OVERVIEW = FakeCompaniesOverview(
    companies_overview=[
        FakeCompanyDetail(company_id=1, name="Google", count=50000),
        FakeCompanyDetail(company_id=2, name="Meta", count=30000),
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


def _patch_single_app(row: dict | None):
    app_df = pd.DataFrame([row]) if row is not None else pd.DataFrame()
    return patch(
        "api_app.controllers.public.v1.apps.get_single_app", return_value=app_df
    )


def _patch_ranks_overview(rows: list[dict]):
    ranks_df = pd.DataFrame(rows)
    return patch(
        "api_app.controllers.public.v1.apps.get_ranks_for_app_overview",
        return_value=ranks_df,
    )


def _patch_ranks(rows: list[dict]):
    ranks_df = pd.DataFrame(rows)
    return patch(
        "api_app.controllers.public.v1.apps.get_ranks_for_app", return_value=ranks_df
    )


@contextmanager
def _patch_sdk_overview(rows: list[dict], logos: list[dict] | None = None):
    overview_df = pd.DataFrame(rows)
    logos_df = pd.DataFrame(logos or [])
    with (
        patch(
            "api_app.controllers.public.v1.apps.get_app_sdk_overview",
            return_value=overview_df,
        ),
        patch(
            "api_app.controllers.public.v1.apps.get_company_logos_df",
            return_value=logos_df,
        ),
    ):
        yield


def _patch_sdk_details(rows: list[dict]):
    details_df = pd.DataFrame(rows)
    return patch(
        "api_app.controllers.public.v1.apps.get_app_sdk_details",
        return_value=details_df,
    )


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
        assert "Missing X-API-Key" in resp.json()["detail"]

    def test_app_requires_api_key(self):
        app = _make_test_app()
        with TestClient(app=app, raise_server_exceptions=False) as client:
            resp = client.get("/api/v1/apps/com.example.app")
        assert resp.status_code == 401
        assert "Missing X-API-Key" in resp.json()["detail"]

    def test_app_ranks_overview_requires_api_key(self):
        app = _make_test_app()
        with TestClient(app=app, raise_server_exceptions=False) as client:
            resp = client.get("/api/v1/apps/com.example.app/ranks/overview")
        assert resp.status_code == 401
        assert "Missing X-API-Key" in resp.json()["detail"]

    def test_app_sdk_overview_requires_api_key(self):
        app = _make_test_app()
        with TestClient(app=app, raise_server_exceptions=False) as client:
            resp = client.get("/api/v1/apps/com.example.app/sdksoverview")
        assert resp.status_code == 401
        assert "Missing X-API-Key" in resp.json()["detail"]

    def test_app_ranks_requires_api_key(self):
        app = _make_test_app()
        with TestClient(app=app, raise_server_exceptions=False) as client:
            resp = client.get("/api/v1/apps/com.example.app/ranks")
        assert resp.status_code == 401
        assert "Missing X-API-Key" in resp.json()["detail"]

    def test_app_sdks_requires_api_key(self):
        app = _make_test_app()
        with TestClient(app=app, raise_server_exceptions=False) as client:
            resp = client.get("/api/v1/apps/com.example.app/sdks")
        assert resp.status_code == 401
        assert "Missing X-API-Key" in resp.json()["detail"]

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
        assert data[1]["count"] == 30000


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
        app = _make_test_app()
        with (
            _patch_key_found("premium_access"),
            _patch_overview(),
            TestClient(app=app, raise_server_exceptions=False) as client,
        ):
            key = "ag_ratelimit429"
            headers = {"X-API-Key": key}

            for _ in range(200):
                resp = client.get("/api/v1/companies", headers=headers)
                assert resp.status_code == 200

            resp = client.get("/api/v1/companies", headers=headers)
            assert resp.status_code == 429
            assert "Rate limit exceeded" in resp.json()["detail"]
            assert "retry-after" in resp.headers

    def test_daily_quota_429(self):
        app = _make_test_app()
        with (
            _patch_key_found("b2b_premium"),
            _patch_overview(),
            TestClient(app=app, raise_server_exceptions=False) as client,
        ):
            from api_app import guards as g
            import hashlib

            raw_key = "ag_daily429"
            key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
            headers = {"X-API-Key": raw_key}

            # Exhaust daily quota using the hash
            for _ in range(500_000):
                g._daily_quota.check(key_hash, 500_000)

            resp = client.get("/api/v1/companies", headers=headers)
            assert resp.status_code == 429
            assert "Daily request quota" in resp.json()["detail"]


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
        payload = {
            "metrics_overview": {
                "sdk_android_total_apps": 123,
                "sdk_ios_total_apps": 45,
                "sdk_total_apps": 168,
            },
            "company_types": ["ad-network"],
            "domain_is_mapped": True,
            "adstxt_ad_domain_overview": {"google": {"direct": {"count": 10}}},
            "adstxt_publishers_overview": None,
            "mediation_adapters": None,
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
            },
            "mapping_notice": None,
        }
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
        assert resp.json() == payload

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


class TestV1Apps:
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
            "developer_id": "dev123",
            "developer_name": "Example Dev",
            "developer_url": "https://example.com/dev",
            "release_date": "2024-01-01",
            "ad_supported": True,
            "in_app_purchases": False,
            "app_icon_url": "https://media.appgoblin.info/icon.png",
            "store_link": "https://play.google.com/store/apps/details?id=com.example.app",
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
            "id": 1,
            "name": "Example App",
            "store_id": "com.example.app",
            "store": "Google Play",
            "category": "tools",
            "rating": 4.5,
            "rating_count": 100,
            "installs": 50000,
            "developer_id": "dev123",
            "developer_name": "Example Dev",
            "developer_url": "https://example.com/dev",
            "release_date": "2024-01-01",
            "ad_supported": True,
            "in_app_purchases": False,
            "app_icon_url": "https://media.appgoblin.info/icon.png",
            "store_link": "https://play.google.com/store/apps/details?id=com.example.app",
        }

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

    def test_app_ranks_overview_returns_expected_shape(self):
        app = _make_test_app()
        rank_rows = [
            {
                "country": "US",
                "collection": "topfreeapplications",
                "category": "overall",
                "best_rank": 7,
            },
            {
                "country": "CA",
                "collection": "topfreeapplications",
                "category": "overall",
                "best_rank": 11,
            },
        ]
        with (
            _patch_key_found("free"),
            _patch_ranks_overview(rank_rows),
            TestClient(app=app, raise_server_exceptions=False) as client,
        ):
            resp = client.get(
                "/api/v1/apps/com.example.app/ranks/overview",
                headers={"X-API-Key": "ag_rankkey"},
            )

        assert resp.status_code == 200
        assert resp.json() == {
            "countries": ["CA", "US"],
            "best_ranks": rank_rows,
        }

    def test_app_ranks_overview_returns_empty_shape_when_missing(self):
        app = _make_test_app()
        with (
            _patch_key_found("free"),
            _patch_ranks_overview([]),
            TestClient(app=app, raise_server_exceptions=False) as client,
        ):
            resp = client.get(
                "/api/v1/apps/com.example.app/ranks/overview",
                headers={"X-API-Key": "ag_rankempty"},
            )

        assert resp.status_code == 200
        assert resp.json() == {"countries": [], "best_ranks": []}

    def test_app_sdk_overview_returns_expected_shape(self):
        app = _make_test_app()
        sdk_rows = [
            {
                "category_slug": "ad_network",
                "company_name": "Google",
                "company_domain": "google.com",
            },
            {
                "category_slug": "measurement",
                "company_name": "Adjust",
                "company_domain": "adjust.com",
            },
        ]
        logos = [
            {
                "company_domain": "google.com",
                "company_logo_url": "https://cdn.example/google.png",
            },
            {
                "company_domain": "adjust.com",
                "company_logo_url": "https://cdn.example/adjust.png",
            },
        ]
        with (
            _patch_key_found("free"),
            _patch_sdk_overview(sdk_rows, logos),
            TestClient(app=app, raise_server_exceptions=False) as client,
        ):
            resp = client.get(
                "/api/v1/apps/com.example.app/sdksoverview",
                headers={"X-API-Key": "ag_sdkkey"},
            )

        assert resp.status_code == 200
        assert resp.json() == {
            "company_categories": {
                "ad_network": [
                    {
                        "company_name": "Google",
                        "company_domain": "google.com",
                        "company_logo_url": "https://cdn.example/google.png",
                    }
                ],
                "measurement": [
                    {
                        "company_name": "Adjust",
                        "company_domain": "adjust.com",
                        "company_logo_url": "https://cdn.example/adjust.png",
                    }
                ],
            }
        }

    def test_app_sdk_overview_returns_empty_shape_when_missing(self):
        app = _make_test_app()
        with (
            _patch_key_found("free"),
            _patch_sdk_overview([]),
            TestClient(app=app, raise_server_exceptions=False) as client,
        ):
            resp = client.get(
                "/api/v1/apps/com.example.app/sdksoverview",
                headers={"X-API-Key": "ag_sdkempty"},
            )

        assert resp.status_code == 200
        assert resp.json() == {"company_categories": {}}

    def test_app_ranks_returns_expected_shape(self):
        app = _make_test_app()
        rank_rows = [
            {
                "country": "US",
                "collection": "topfreeapplications",
                "category": "overall",
                "crawled_date": "2026-04-01",
                "rank": 5,
            },
            {
                "country": "US",
                "collection": "topfreeapplications",
                "category": "overall",
                "crawled_date": "2026-04-02",
                "rank": 3,
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
        assert resp.json() == {
            "history": [
                {
                    "crawled_date": "2026-04-01",
                    "topfreeapplications: overall": 5,
                },
                {
                    "crawled_date": "2026-04-02",
                    "topfreeapplications: overall": 3,
                },
            ]
        }

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
        assert resp.json() == {"history": {}}

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
            "leftovers": {
                "mystery.vendor": {"application/meta-data": ["mystery.vendor.sdk"]}
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
            "leftovers": {},
        }


class TestV1Docs:
    def test_openapi_json_only_lists_public_v1_paths(self):
        app = _make_docs_test_app()
        with TestClient(app=app, raise_server_exceptions=False) as client:
            resp = client.get("/api/v1/docs/openapi.json")

        assert resp.status_code == 200
        data = resp.json()
        assert data["info"]["title"] == "AppGoblin Public API v1"
        assert data["info"]["version"] == "0.1.0"
        assert "X-API-Key" in data["info"]["description"]
        assert data["servers"] == [{"url": "https://appgoblin.info"}]
        assert (
            data["components"]["securitySchemes"]["ApiKeyAuth"]["name"] == "X-API-Key"
        )
        assert data["security"] == [{"ApiKeyAuth": []}]
        assert "/health" not in data["paths"]
        assert data["paths"]
        assert all(path.startswith("/api/v1/") for path in data["paths"])

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
