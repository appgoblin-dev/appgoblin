"""Versioned public API endpoints — requires API key authentication."""

import os
import time
from typing import Self
from urllib.parse import quote

from litestar import Controller, get
from litestar.datastructures import State

from api_app.controllers.companies import (
    build_company_overview_payload,
    get_overviews,
)
from api_app.guards import validate_api_key
from api_app.models import (
    CategoryCompanyStats,
    CompanyExports,
    CompanyExportTarget,
    PublicCompanyOverview,
)
from config import get_logger

logger = get_logger(__name__)

DEFAULT_DOWNLOADS_BASE = "https://media.appgoblin.info/"


def _api_key_guard(request, route_handler) -> None:
    """Guard that validates the X-API-Key header."""
    state = request.app.state
    validate_api_key(request, state)


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


def _build_company_exports(
    company_domain: str, categories: dict[str, object]
) -> CompanyExports:
    """Build public SDK/API export metadata for a company domain."""
    totals = categories.get("all")

    android_rows = int(getattr(totals, "sdk_android_total_apps", 0)) if totals else 0
    ios_rows = int(getattr(totals, "sdk_ios_total_apps", 0)) if totals else 0

    return CompanyExports(
        sdk_api_android=CompanyExportTarget(
            available=android_rows > 0,
            estimated_rows=android_rows,
            url=(
                _build_company_verified_apps_url(company_domain, "android")
                if android_rows > 0
                else None
            ),
        ),
        sdk_api_ios=CompanyExportTarget(
            available=ios_rows > 0,
            estimated_rows=ios_rows,
            url=(
                _build_company_verified_apps_url(company_domain, "ios")
                if ios_rows > 0
                else None
            ),
        ),
    )


def _build_public_company_overview_payload(
    state: State, company_domain: str, category: str | None = None
) -> PublicCompanyOverview:
    """Build the public company detail payload for v1 endpoints."""
    overview = build_company_overview_payload(
        state=state, company_domain=company_domain, category=category
    )

    return PublicCompanyOverview(
        metrics_overview=overview.categories.get("all", CategoryCompanyStats()),
        company_types=overview.company_types,
        adstxt_ad_domain_overview=overview.adstxt_ad_domain_overview,
        adstxt_publishers_overview=overview.adstxt_publishers_overview,
        mediation_adapters=overview.mediation_adapters,
        exports=_build_company_exports(company_domain, overview.categories),
    )


class V1CompaniesController(Controller):
    """Public API v1 — companies endpoints (API key required)."""

    path = "/api/v1/"
    guards = [_api_key_guard]

    @get(path="/companies", cache=86400)
    async def companies(self: Self, state: State) -> list[dict]:
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
