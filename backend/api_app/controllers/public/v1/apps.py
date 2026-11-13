"""Versioned public app endpoints — requires API key authentication."""

import time
from dataclasses import fields as dataclass_fields
from typing import Self

import pandas as pd
from litestar import Controller, Request, Response, get
from litestar.datastructures import State
from litestar.exceptions import NotFoundException, PermissionDeniedException

from api_app.analytics import PUBLIC_API_HOSTNAME, build_request_page_view_task
from api_app.controllers.public.v1.public_models import (
    PublicAppBasics,
    PublicAppBestRank,
    PublicAppMappedSdks,
    PublicAppSdkDetails,
    PublicAppSdkHistory,
)
from api_app.guards import validate_api_key
from config import get_logger
from dbcon.queries import (
    get_app_mapped_sdks,
    get_app_sdk_details,
    get_app_sdk_history,
    get_app_version_timeline,
    get_ranks_for_app_overview,
    get_single_app,
)
from dbcon.static import get_company_logos_df

logger = get_logger(__name__)

APP_BASICS_FIELD_SOURCES = {
    "installs_weekly": "installs_sum_1w",
    "installs_monthly": "installs_sum_4w",
    "rating_count_weekly": "ratings_sum_1w",
}


def _api_key_guard(request, route_handler) -> None:
    """Guard that validates the Authorization: Bearer header (X-API-Key also accepted)."""
    state = request.app.state
    request.scope["_api_key_context"] = validate_api_key(request, state)


def _b2b_sdk_guard(request: Request, route_handler) -> None:
    """Require the B2B SDK or B2B Premium subscription tier."""
    context = request.scope.get("_api_key_context")
    if context is None:
        context = validate_api_key(request, request.app.state)
    if context.tier not in {"b2b_sdk", "b2b_premium"}:
        raise PermissionDeniedException(
            detail="Requires B2B SDK or B2B Premium paid tier"
        )


def _coerce_tv_supported(value: object) -> bool:
    """Only an explicit TRUE means TV support; NULL and FALSE both resolve to False."""
    return bool(value) if pd.notna(value) else False


def _build_app_basics_payload(state: State, store_id: str) -> PublicAppBasics:
    """Return public app metadata plus estimated growth, usage, and revenue signals."""
    app_df = get_single_app(state, store_id)
    if app_df.empty:
        msg = f"Store ID not found: {store_id!r}"
        raise NotFoundException(msg, status_code=404)

    app_dict = app_df.to_dict(orient="records")[0]
    payload_fields = {
        field.name: app_dict.get(APP_BASICS_FIELD_SOURCES.get(field.name, field.name))
        for field in dataclass_fields(PublicAppBasics)
    }
    payload_fields["tv_supported"] = _coerce_tv_supported(app_dict.get("tv_supported"))
    return PublicAppBasics(**payload_fields)


def _build_app_ranks_payload(state: State, store_id: str) -> list[PublicAppBestRank]:
    """Return best-rank records for a store identifier across countries."""
    overview_df = get_ranks_for_app_overview(state, store_id=store_id, days=90)
    if overview_df.empty:
        return []

    return [
        PublicAppBestRank(
            country=str(row["country"]),
            collection=str(row["collection"]),
            category=str(row["category"]),
            best_rank=int(row["best_rank"]),
        )
        for row in overview_df.to_dict(orient="records")
    ]


def _build_app_mapped_sdks_payload(state: State, store_id: str) -> PublicAppMappedSdks:
    """Return mapped SDK slugs grouped by company domain for an app."""
    mapped_sdks_df = get_app_mapped_sdks(state, store_id)
    mapped_sdks: dict[str, list[str]] = {}
    for row in mapped_sdks_df.to_dict(orient="records"):
        company_domain = row.get("company_domain")
        sdk_slug = row.get("sdk_slug")
        if pd.isna(company_domain) or pd.isna(sdk_slug):
            continue
        mapped_sdks.setdefault(str(company_domain), []).append(str(sdk_slug))

    return PublicAppMappedSdks(store_id=store_id, mapped_sdks=mapped_sdks)


def _build_app_sdk_details_payload(state: State, store_id: str) -> PublicAppSdkDetails:
    """Return the existing app SDK details response shape."""
    sdk_df = get_app_sdk_details(state, store_id)

    if sdk_df.empty or sdk_df.isna().all().all():
        return PublicAppSdkDetails()

    sdk_df.loc[sdk_df["value_name"].isna(), "value_name"] = ""
    sdk_df["short_value_name"] = sdk_df.value_name.apply(
        lambda value: ".".join(value.split(".")[0:2])
    )

    categories = (
        sdk_df.loc[sdk_df["category_slug"].notna(), "category_slug"].unique().tolist()
    )
    company_sdk_dict = {}
    found_sdk_tlds: list[str] = []
    for category_slug in categories:
        category_dict = {
            company_domain: {
                short_value_name: grouped_df.groupby("xml_path")["value_name"]
                .apply(list)
                .to_dict()
                for short_value_name, grouped_df in company_df.groupby(
                    "short_value_name"
                )
            }
            for company_domain, company_df in sdk_df[
                sdk_df["category_slug"] == category_slug
            ].groupby("company_domain")
        }
        company_sdk_dict[category_slug] = category_dict
        found_sdk_tlds.extend(
            key for category in category_dict.values() for key in category
        )

    found_sdk_tlds = list(set(found_sdk_tlds))
    unwanted_value_names = ["smali", *found_sdk_tlds]

    is_permission = sdk_df["xml_path"] == "uses-permission"
    sdk_df.loc[sdk_df["xml_path"].str.contains("key", case=False), "value_name"] = (
        "redacted_key"
    )
    is_matching_store_id = sdk_df["value_name"].str.startswith(
        ".".join(store_id.split(".")[:2])
    )
    is_android_activity = sdk_df["value_name"].str.contains(
        r"^(com\.android|android|kotlin|smali_)", regex=True
    )
    is_package_query = sdk_df["xml_path"].str.contains(
        r"^queries/package|LSApplicationQueriesSchemes"
    )
    is_value_empty = sdk_df["value_name"] == ""
    is_skadnetwork = sdk_df["xml_path"] == "SKAdNetworkItems"

    permissions_df = sdk_df[is_permission]
    unmapped_sdks_df = sdk_df[
        ~is_permission
        & ~is_matching_store_id
        & ~is_android_activity
        & ~is_value_empty
        & ~is_package_query
        & ~is_skadnetwork
        & sdk_df["company_name"].isna()
    ]
    unmapped_sdks_df = unmapped_sdks_df[
        ~unmapped_sdks_df["value_name"].isin(unwanted_value_names)
    ]

    unmapped_sdks = {
        short_value_name: grouped_df.groupby("xml_path")["value_name"]
        .apply(list)
        .to_dict()
        for short_value_name, grouped_df in unmapped_sdks_df.groupby("short_value_name")
    }
    permissions = [
        value.replace("android.permission.", "")
        for value in permissions_df.value_name.tolist()
    ]
    app_queries = sdk_df[is_package_query].value_name.unique().tolist()
    skadnetwork = sdk_df[is_skadnetwork].value_name.unique().tolist()

    return PublicAppSdkDetails(
        company_categories=company_sdk_dict,
        permissions=permissions,
        app_queries=app_queries,
        skadnetwork=skadnetwork,
        unmapped_sdks=unmapped_sdks,
    )


def _build_app_version_timeline_payload(state: State, store_id: str) -> list[dict]:
    """Return the crawled version timeline used by the SDK history UI."""
    app_df = get_single_app(state, store_id)
    if app_df.empty:
        msg = f"Store ID not found: {store_id!r}"
        raise NotFoundException(msg, status_code=404)

    timeline_df = get_app_version_timeline(state, store_id)
    timeline_df = timeline_df[timeline_df["app_version_code"].astype("string") != "-1"]
    timeline_df["sdk_scan_result"] = timeline_df["sdk_scan_result"].map(
        lambda result: (
            None if pd.isna(result) else "success" if result == 1 else "failure"
        )
    )
    return timeline_df.to_dict(orient="records")


def _build_app_sdk_history_payload(state: State, store_id: str) -> PublicAppSdkHistory:
    """Return SDK additions, removals, and scan-status rows for an app."""
    app_df = get_single_app(state, store_id)
    if app_df.empty:
        msg = f"Store ID not found: {store_id!r}"
        raise NotFoundException(msg, status_code=404)

    history_df = get_app_sdk_history(state, store_id)

    if not history_df.empty:
        no_change_rows = (
            history_df["company_name"].isna()
            & history_df["sdk_name"].isna()
            & history_df["status"].isna()
        )
        history_df.loc[no_change_rows, "status"] = "no_change"
        history_df["sdk_scan_result"] = history_df["sdk_scan_result"].map(
            lambda result: (
                None if pd.isna(result) else "success" if result == 1 else "failure"
            )
        )
        company_logos_df = get_company_logos_df(state).drop_duplicates(
            subset=["company_domain"], keep="first"
        )
        history_df = history_df.merge(
            company_logos_df,
            on="company_domain",
            how="left",
            validate="m:1",
        )
        history_df = history_df.replace({pd.NaT: None})
        history_df = history_df.where(pd.notna(history_df), None)

    return PublicAppSdkHistory(history=history_df.to_dict(orient="records"))


class V1AppsController(Controller):
    """Public API v1 — app endpoints (API key required)."""

    path = "/api/v1/"
    guards = [_api_key_guard]

    @get(path="/apps/{store_id:str}", cache=3600)
    async def app_basics(
        self: Self, state: State, request: Request, store_id: str
    ) -> PublicAppBasics:
        """Return basic app metadata for a store identifier."""
        start = time.perf_counter() * 1000
        payload = _build_app_basics_payload(state=state, store_id=store_id)
        duration = round((time.perf_counter() * 1000 - start), 2)
        logger.info(f"GET /api/v1/apps/{store_id} took {duration}ms")
        return Response(
            payload,
            background=build_request_page_view_task(
                request,
                url=f"/api/v1/apps/{store_id}",
                hostname=PUBLIC_API_HOSTNAME,
            ),
        )

    @get(path="/apps/{store_id:str}/ranks", cache=3600)
    async def app_ranks(
        self: Self, state: State, request: Request, store_id: str
    ) -> list[PublicAppBestRank]:
        """Return best-rank records for a store identifier across countries."""
        start = time.perf_counter() * 1000
        payload = _build_app_ranks_payload(state=state, store_id=store_id)
        duration = round((time.perf_counter() * 1000 - start), 2)
        logger.info(f"GET /api/v1/apps/{store_id}/ranks took {duration}ms")
        return Response(
            payload,
            background=build_request_page_view_task(
                request,
                url=f"/api/v1/apps/{store_id}/ranks",
                hostname=PUBLIC_API_HOSTNAME,
            ),
        )

    @get(
        path="/apps/{store_id:str}/mapped-sdks",
        cache=3600,
        guards=[_b2b_sdk_guard],
    )
    async def app_mapped_sdks(
        self: Self, state: State, request: Request, store_id: str
    ) -> PublicAppMappedSdks:
        """Return mapped SDK slugs grouped by company domain for an app."""
        start = time.perf_counter() * 1000
        payload = _build_app_mapped_sdks_payload(state=state, store_id=store_id)
        duration = round((time.perf_counter() * 1000 - start), 2)
        logger.info(f"GET /api/v1/apps/{store_id}/mapped-sdks took {duration}ms")
        return Response(
            payload,
            background=build_request_page_view_task(
                request,
                url=f"/api/v1/apps/{store_id}/mapped-sdks",
                hostname=PUBLIC_API_HOSTNAME,
            ),
        )

    @get(path="/apps/{store_id:str}/sdks", cache=3600)
    async def app_sdk_details(
        self: Self, state: State, request: Request, store_id: str
    ) -> PublicAppSdkDetails:
        """Return SDK details for a store identifier."""
        start = time.perf_counter() * 1000
        payload = _build_app_sdk_details_payload(state=state, store_id=store_id)
        duration = round((time.perf_counter() * 1000 - start), 2)
        logger.info(f"GET /api/v1/apps/{store_id}/sdks took {duration}ms")
        return Response(
            payload,
            background=build_request_page_view_task(
                request,
                url=f"/api/v1/apps/{store_id}/sdks",
                hostname=PUBLIC_API_HOSTNAME,
            ),
        )

    @get(
        path="/apps/{store_id:str}/versions",
        cache=7200,
        guards=[_b2b_sdk_guard],
    )
    async def app_version_timeline(
        self: Self, state: State, request: Request, store_id: str
    ) -> list[dict]:
        """Return crawled app versions and their SDK scan status."""
        start = time.perf_counter() * 1000
        payload = _build_app_version_timeline_payload(state=state, store_id=store_id)
        duration = round((time.perf_counter() * 1000 - start), 2)
        logger.info(f"GET /api/v1/apps/{store_id}/versions took {duration}ms")
        return Response(
            payload,
            background=build_request_page_view_task(
                request,
                url=f"/api/v1/apps/{store_id}/versions",
                hostname=PUBLIC_API_HOSTNAME,
            ),
        )

    @get(
        path="/apps/{store_id:str}/sdks/history",
        cache=3600,
        guards=[_b2b_sdk_guard],
    )
    async def app_sdk_history(
        self: Self, state: State, request: Request, store_id: str
    ) -> PublicAppSdkHistory:
        """Return SDK additions, removals, and scan-status rows for an app."""
        start = time.perf_counter() * 1000
        payload = _build_app_sdk_history_payload(state=state, store_id=store_id)
        duration = round((time.perf_counter() * 1000 - start), 2)
        logger.info(f"GET /api/v1/apps/{store_id}/sdks/history took {duration}ms")
        return Response(
            payload,
            background=build_request_page_view_task(
                request,
                url=f"/api/v1/apps/{store_id}/sdks/history",
                hostname=PUBLIC_API_HOSTNAME,
            ),
        )
