"""Versioned public API endpoints — requires API key authentication."""

import os
import time
from collections.abc import Mapping
from typing import Self, SupportsFloat, SupportsIndex, SupportsInt, cast
from urllib.parse import quote

from litestar import Controller, Request, Response, get
from litestar.connection import ASGIConnection
from litestar.datastructures import State
from litestar.exceptions import NotFoundException, PermissionDeniedException
from litestar.handlers import BaseRouteHandler

from api_app.analytics import PUBLIC_API_HOSTNAME, build_request_page_view_task
from api_app.controllers.companies import (
    build_company_overview_base,
    get_company_app_change_store_ids_by_platform,
    get_overviews,
)
from api_app.controllers.public.v1.public_models import (
    CompanyDatasets,
    CompanyDatasetTarget,
    PublicCategoryCompanyStats,
    PublicCompanyAppChangeStoreIds,
    PublicCompanyListItem,
    PublicCompanyOverview,
    PublicCompanyTrends,
)
from api_app.guards import validate_api_key
from api_app.models import (
    CategoryCompanyStats,
    CompanyTrendsSummary,
)
from api_app.models import (
    CompanyCategoryOverview as PrivateCompanyCategoryOverview,
)
from config import get_logger

logger = get_logger(__name__)

DEFAULT_DOWNLOADS_BASE = "https://media.appgoblin.info/"
UNMAPPED_COMPANY_NOTICE = (
    "This domain has not yet been manually mapped to a company in the AppGoblin "
    "database. Current results may include incidental matches from ads.txt or "
    "recorded API calls. Contact contact@appgoblin.info to request mapping; "
    "additions are usually completed within 1-2 business days."
)
VALID_COMPANY_APP_CHANGE_TAG_SOURCES = {"sdk", "api_call", "app_ads_direct"}
VALID_COMPANY_APP_CHANGE_STATUSES = {"added", "lost", "removed"}


def _validate_company_app_changes_query(
    *, tag_source: str, quarter: int, status: str
) -> None:
    """Validate public app-change request filters."""
    if tag_source not in VALID_COMPANY_APP_CHANGE_TAG_SOURCES:
        msg = "tag_source must be one of: sdk, api_call, app_ads_direct"
        raise NotFoundException(msg, status_code=400)
    if status not in VALID_COMPANY_APP_CHANGE_STATUSES:
        msg = "status must be one of: added, lost, removed"
        raise NotFoundException(msg, status_code=400)
    if quarter not in {1, 2, 3, 4}:
        msg = "quarter must be one of: 1, 2, 3, 4"
        raise NotFoundException(msg, status_code=400)


def _is_missing_value(value: object) -> bool:
    """Return whether a value is missing after dataframe serialization."""
    if value is None:
        return True

    try:
        return bool(value != value)
    except TypeError:
        return False


def _optional_string(value: object) -> str | None:
    """Normalize optional strings from serialized pandas rows."""
    if _is_missing_value(value):
        return None

    normalized = str(value).strip()
    if not normalized or normalized.lower() == "nan":
        return None
    return normalized


def _optional_int(value: object) -> int | None:
    """Normalize optional integers from serialized pandas rows."""
    if _is_missing_value(value):
        return None
    if isinstance(value, (str, bytes, bytearray, SupportsInt, SupportsIndex)):
        return int(value)
    raise TypeError(f"Expected integer-compatible scalar, got {type(value).__name__}")


def _optional_float(value: object) -> float | None:
    """Normalize optional floats from serialized pandas rows."""
    if _is_missing_value(value):
        return None
    if isinstance(value, (str, bytes, bytearray, SupportsFloat, SupportsIndex)):
        return float(value)
    raise TypeError(f"Expected float-compatible scalar, got {type(value).__name__}")


def _api_key_guard(request: ASGIConnection, route_handler: BaseRouteHandler) -> None:
    """Guard that validates the Authorization: Bearer header (X-API-Key also accepted)."""
    state = request.app.state
    context = validate_api_key(cast("Request", request), state)
    if context.tier == "free":
        raise PermissionDeniedException(
            detail="Companies API v1 requires a paid subscription tier"
        )


def _get_downloads_base_url() -> str:
    """Return the configured public downloads base URL."""
    base = os.getenv("APPGOBLIN_DOWNLOADS_BASE", "").strip()
    if not base:
        return DEFAULT_DOWNLOADS_BASE
    return base if base.endswith("/") else f"{base}/"


def _build_company_verified_apps_url(company_domain: str, platform: str) -> str | None:
    """Build the public S3 URL for a company verified apps export."""
    if not company_domain:
        return None

    encoded_domain = quote(company_domain, safe="")
    base = _get_downloads_base_url()
    return (
        f"{base}downloads/company-verified-apps/"
        f"domains/domain={encoded_domain}/source=all/"
        f"appgoblin_{encoded_domain}_{platform}_verified_apps.csv"
    )


def _build_company_datasets(
    company_domain: str, categories: Mapping[str, CategoryCompanyStats]
) -> CompanyDatasets:
    """Build public SDK/API dataset metadata for a company domain."""
    totals = categories.get("all")

    android_rows = int(getattr(totals, "sdk_android_total_apps", 0)) if totals else 0
    ios_rows = int(getattr(totals, "sdk_ios_total_apps", 0)) if totals else 0

    return CompanyDatasets(
        sdk_api_android=CompanyDatasetTarget(
            available=android_rows > 0,
            estimated_rows=android_rows,
            url=(
                _build_company_verified_apps_url(company_domain, "android")
                if android_rows > 0
                else None
            ),
        ),
        sdk_api_ios=CompanyDatasetTarget(
            available=ios_rows > 0,
            estimated_rows=ios_rows,
            url=(
                _build_company_verified_apps_url(company_domain, "ios")
                if ios_rows > 0
                else None
            ),
        ),
    )


def _to_public_company_list_item(
    company: Mapping[str, object],
) -> PublicCompanyListItem:
    """Project an internal company summary into the public contract type."""
    return PublicCompanyListItem(
        company_domain=_optional_string(company.get("company_domain")),
        name=_optional_string(company.get("name") or company.get("company_name")),
        parent_company_domain=_optional_string(company.get("parent_company_domain")),
        parent_company_name=_optional_string(company.get("parent_company_name")),
        api_ip_resolved_country=_optional_string(
            company.get("api_ip_resolved_country")
        ),
        total_app_count=_optional_int(company.get("total_app_count")),
        installs_d30=_optional_int(company.get("installs_d30")),
        google_sdk_app_count=_optional_int(company.get("google_sdk_app_count")),
        apple_sdk_app_count=_optional_int(company.get("apple_sdk_app_count")),
        google_api_call_app_count=_optional_int(
            company.get("google_api_call_app_count")
        ),
        apple_api_call_app_count=_optional_int(company.get("apple_api_call_app_count")),
        google_app_ads_direct_app_count=_optional_int(
            company.get("google_app_ads_direct_app_count")
        ),
        apple_app_ads_direct_app_count=_optional_int(
            company.get("apple_app_ads_direct_app_count")
        ),
        google_app_ads_reseller_app_count=_optional_int(
            company.get("google_app_ads_reseller_app_count")
        ),
        apple_app_ads_reseller_app_count=_optional_int(
            company.get("apple_app_ads_reseller_app_count")
        ),
        trends_latest_period=_optional_string(company.get("trends_latest_period")),
        google_sdk_latest_pct_market_share=_optional_float(
            company.get("google_sdk_latest_pct_market_share")
        ),
        apple_sdk_latest_pct_market_share=_optional_float(
            company.get("apple_sdk_latest_pct_market_share")
        ),
        google_app_ads_direct_latest_pct_market_share=_optional_float(
            company.get("google_app_ads_direct_latest_pct_market_share")
        ),
        apple_app_ads_direct_latest_pct_market_share=_optional_float(
            company.get("apple_app_ads_direct_latest_pct_market_share")
        ),
        google_sdk_latest_pct_market_share_change=_optional_float(
            company.get("google_sdk_latest_pct_market_share_change")
        ),
        apple_sdk_latest_pct_market_share_change=_optional_float(
            company.get("apple_sdk_latest_pct_market_share_change")
        ),
        google_app_ads_direct_latest_pct_market_share_change=_optional_float(
            company.get("google_app_ads_direct_latest_pct_market_share_change")
        ),
        apple_app_ads_direct_latest_pct_market_share_change=_optional_float(
            company.get("apple_app_ads_direct_latest_pct_market_share_change")
        ),
        google_sdk_latest_total_apps=_optional_int(
            company.get("google_sdk_latest_total_apps")
        ),
        apple_sdk_latest_total_apps=_optional_int(
            company.get("apple_sdk_latest_total_apps")
        ),
        google_app_ads_direct_latest_total_apps=_optional_int(
            company.get("google_app_ads_direct_latest_total_apps")
        ),
        apple_app_ads_direct_latest_total_apps=_optional_int(
            company.get("apple_app_ads_direct_latest_total_apps")
        ),
        google_sdk_latest_apps_added=_optional_int(
            company.get("google_sdk_latest_apps_added")
        ),
        apple_sdk_latest_apps_added=_optional_int(
            company.get("apple_sdk_latest_apps_added")
        ),
        google_app_ads_direct_latest_apps_added=_optional_int(
            company.get("google_app_ads_direct_latest_apps_added")
        ),
        apple_app_ads_direct_latest_apps_added=_optional_int(
            company.get("apple_app_ads_direct_latest_apps_added")
        ),
        google_sdk_latest_apps_lost=_optional_int(
            company.get("google_sdk_latest_apps_lost")
        ),
        apple_sdk_latest_apps_lost=_optional_int(
            company.get("apple_sdk_latest_apps_lost")
        ),
        google_app_ads_direct_latest_apps_lost=_optional_int(
            company.get("google_app_ads_direct_latest_apps_lost")
        ),
        apple_app_ads_direct_latest_apps_lost=_optional_int(
            company.get("apple_app_ads_direct_latest_apps_lost")
        ),
    )


def _has_company_overview_data(
    metrics: PublicCategoryCompanyStats, overview: PrivateCompanyCategoryOverview
) -> bool:
    """Return whether the computed company overview contains any material data."""
    if any(bool(value) for value in vars(metrics).values()):
        return True

    return bool(overview.company_types)


def _to_public_category_company_stats(
    metrics: CategoryCompanyStats | None,
) -> PublicCategoryCompanyStats:
    """Project private company metrics into the public contract type."""
    if metrics is None:
        return PublicCategoryCompanyStats()

    return PublicCategoryCompanyStats(
        adstxt_direct_android_total_apps=metrics.adstxt_direct_android_total_apps,
        adstxt_direct_ios_total_apps=metrics.adstxt_direct_ios_total_apps,
        adstxt_reseller_android_total_apps=metrics.adstxt_reseller_android_total_apps,
        adstxt_reseller_ios_total_apps=metrics.adstxt_reseller_ios_total_apps,
        sdk_android_total_apps=metrics.sdk_android_total_apps,
        sdk_ios_total_apps=metrics.sdk_ios_total_apps,
        sdk_total_apps=metrics.sdk_total_apps,
        api_android_total_apps=metrics.api_android_total_apps,
        api_total_apps=metrics.api_total_apps,
        sdk_android_installs_d30=metrics.sdk_android_installs_d30,
        sdk_ios_installs_d30=metrics.sdk_ios_installs_d30,
        adstxt_direct_android_installs_d30=metrics.adstxt_direct_android_installs_d30,
        adstxt_reseller_android_installs_d30=(
            metrics.adstxt_reseller_android_installs_d30
        ),
    )


def _to_public_company_trends(
    trends: CompanyTrendsSummary | None,
) -> PublicCompanyTrends | None:
    """Project private company trend summaries into the public contract."""
    if trends is None:
        return None

    public_trends = PublicCompanyTrends(latest_period=trends.latest_period)
    for source_key, source_summary in trends.sources.items():
        market_share_field = f"{source_key}_market_share_change_pct"
        apps_lost_field = f"{source_key}_apps_lost"

        if hasattr(public_trends, market_share_field):
            setattr(
                public_trends,
                market_share_field,
                source_summary.latest_pct_market_share_change_pct,
            )
        if hasattr(public_trends, apps_lost_field):
            setattr(public_trends, apps_lost_field, source_summary.latest_apps_lost)

    return public_trends


def _build_public_company_overview_payload(
    state: State, company_domain: str, category: str | None = None
) -> PublicCompanyOverview:
    """Project shared company overview data into the public v1 response shape."""
    overview = build_company_overview_base(
        state=state, company_domain=company_domain, category=category
    )
    metrics_overview = _to_public_category_company_stats(overview.categories.get("all"))
    if not _has_company_overview_data(metrics_overview, overview):
        msg = f"Company domain not found: {company_domain!r}"
        raise NotFoundException(msg, status_code=404)

    domain_is_mapped = len(overview.company_types) > 0
    mapping_notice = None
    if not domain_is_mapped:
        mapping_notice = UNMAPPED_COMPANY_NOTICE

    return PublicCompanyOverview(
        metrics=metrics_overview,
        trends=_to_public_company_trends(overview.trends_summary),
        company_types=overview.company_types,
        domain_is_mapped=domain_is_mapped,
        mapping_notice=mapping_notice,
        datasets=_build_company_datasets(company_domain, overview.categories),
    )


def _build_public_company_app_change_payload(
    state: State,
    *,
    company_domain: str,
    tag_source: str,
    year: int,
    quarter: int,
    status: str,
) -> PublicCompanyAppChangeStoreIds:
    """Project a single public company app-change slice into the v1 response."""
    _validate_company_app_changes_query(
        tag_source=tag_source,
        quarter=quarter,
        status=status,
    )
    return PublicCompanyAppChangeStoreIds(
        company_domain=company_domain,
        tag_source=tag_source,
        year=year,
        quarter=quarter,
        status=status,
        **get_company_app_change_store_ids_by_platform(
            state=state,
            company_domain=company_domain,
            tag_source=tag_source,
            year=year,
            quarter=quarter,
            status="removed" if status == "lost" else status,
        ),
    )


class V1CompaniesController(Controller):
    """Public API v1 — companies endpoints (API key required)."""

    path = "/api/v1/"
    guards = [_api_key_guard]

    @get(path="/companies", cache=86400)
    async def companies(
        self: Self, state: State, request: Request
    ) -> list[PublicCompanyListItem]:
        """Return a list of all queryable company domains.

        Each entry contains the exact ``company_domain``, display ``name``,
        parent company mapping fields, and the latest overview trend snapshot
        fields already present in the shared companies index.
        """
        start = time.perf_counter() * 1000
        overview = get_overviews(state=state)
        duration = round((time.perf_counter() * 1000 - start), 2)
        logger.info(f"GET /api/v1/companies took {duration}ms")

        return Response(
            [
                _to_public_company_list_item(company)
                for company in overview.companies_overview
            ],
            background=build_request_page_view_task(
                request,
                url="/api/v1/companies",
                hostname=PUBLIC_API_HOSTNAME,
            ),
        )

    @get(path="/companies/{company_domain:str}", cache=86400)
    async def company_overview(
        self: Self,
        state: State,
        request: Request,
        company_domain: str,
        category: str | None = None,
    ) -> PublicCompanyOverview:
        """Return overview details for a single company domain."""
        start = time.perf_counter() * 1000
        payload = _build_public_company_overview_payload(
            state=state, company_domain=company_domain, category=category
        )
        duration = round((time.perf_counter() * 1000 - start), 2)
        logger.info(f"GET /api/v1/companies/{company_domain} took {duration}ms")
        return Response(
            payload,
            background=build_request_page_view_task(
                request,
                url=f"/api/v1/companies/{company_domain}",
                hostname=PUBLIC_API_HOSTNAME,
            ),
        )

    @get(path="/companies/{company_domain:str}/app-changes", cache=86400)
    async def company_app_changes(
        self: Self,
        state: State,
        request: Request,
        company_domain: str,
        status: str,
        tag_source: str,
        year: int,
        quarter: int,
    ) -> PublicCompanyAppChangeStoreIds:
        """Return store IDs for a company's app-change slice in a quarter."""
        start = time.perf_counter() * 1000
        payload = _build_public_company_app_change_payload(
            state=state,
            company_domain=company_domain,
            tag_source=tag_source,
            year=year,
            quarter=quarter,
            status=status,
        )
        duration = round((time.perf_counter() * 1000 - start), 2)
        logger.info(
            f"GET /api/v1/companies/{company_domain}/app-changes took {duration}ms"
        )
        return Response(
            payload,
            background=build_request_page_view_task(
                request,
                url=(
                    f"/api/v1/companies/{quote(company_domain)}/app-changes"
                    f"?status={quote(status)}"
                    f"&tag_source={quote(tag_source)}"
                    f"&year={year}&quarter={quarter}"
                ),
                hostname=PUBLIC_API_HOSTNAME,
            ),
        )
