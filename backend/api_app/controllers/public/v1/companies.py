"""Versioned public API endpoints — requires API key authentication."""

import os
import time
from collections.abc import Mapping
from typing import Self, cast
from urllib.parse import quote

from litestar import Controller, Request, get
from litestar.connection import ASGIConnection
from litestar.datastructures import State
from litestar.exceptions import NotFoundException, PermissionDeniedException
from litestar.handlers import BaseRouteHandler

from api_app.controllers.companies import (
    build_company_overview_base,
    get_overviews,
)
from api_app.controllers.public.v1.public_models import (
    CompanyDatasets,
    CompanyDatasetTarget,
    PublicCategoryCompanyStats,
    PublicCompanyOverview,
)
from api_app.guards import validate_api_key
from api_app.models import (
    CategoryCompanyStats,
    CompanyDetail,
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


def _api_key_guard(request: ASGIConnection, route_handler: BaseRouteHandler) -> None:
    """Guard that validates the X-API-Key header."""
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
        total_apps=metrics.total_apps,
        adstxt_direct_ios_total_apps=metrics.adstxt_direct_ios_total_apps,
        adstxt_direct_android_total_apps=metrics.adstxt_direct_android_total_apps,
        adstxt_reseller_ios_total_apps=metrics.adstxt_reseller_ios_total_apps,
        adstxt_reseller_android_total_apps=metrics.adstxt_reseller_android_total_apps,
        sdk_ios_total_apps=metrics.sdk_ios_total_apps,
        sdk_android_total_apps=metrics.sdk_android_total_apps,
        sdk_total_apps=metrics.sdk_total_apps,
        api_ios_total_apps=metrics.api_ios_total_apps,
        api_android_total_apps=metrics.api_android_total_apps,
        api_total_apps=metrics.api_total_apps,
        sdk_android_installs_d30=metrics.sdk_android_installs_d30,
        adstxt_direct_android_installs_d30=metrics.adstxt_direct_android_installs_d30,
        adstxt_reseller_android_installs_d30=(
            metrics.adstxt_reseller_android_installs_d30
        ),
    )


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
        company_types=overview.company_types,
        domain_is_mapped=domain_is_mapped,
        mapping_notice=mapping_notice,
        datasets=_build_company_datasets(company_domain, overview.categories),
    )


class V1CompaniesController(Controller):
    """Public API v1 — companies endpoints (API key required)."""

    path = "/api/v1/"
    guards = [_api_key_guard]

    @get(path="/companies", cache=86400)
    async def companies(self: Self, state: State) -> list[CompanyDetail]:
        """Return a list of all mapped companies.

        Each entry contains ``company_id``, ``name``, and ``count``
        (number of apps associated with the company across stores).
        """
        start = time.perf_counter() * 1000
        overview = get_overviews(state=state)
        duration = round((time.perf_counter() * 1000 - start), 2)
        logger.info(f"GET /api/v1/companies took {duration}ms")

        return overview.companies_overview

    @get(path="/companies/{company_domain:str}", cache=86400)
    async def company_overview(
        self: Self,
        state: State,
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
        return payload
