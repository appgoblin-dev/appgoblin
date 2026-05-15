"""Versioned public app endpoints — requires API key authentication."""

import time
from dataclasses import fields as dataclass_fields
from typing import Self

from litestar import Controller, get
from litestar.datastructures import State
from litestar.exceptions import NotFoundException

from api_app.controllers.public.v1.public_models import (
    PublicAppBasics,
    PublicAppBestRank,
    PublicAppSdkDetails,
)
from api_app.guards import validate_api_key
from config import get_logger
from dbcon.queries import (
    get_app_sdk_details,
    get_ranks_for_app_overview,
    get_single_app,
)

logger = get_logger(__name__)

APP_BASICS_FIELD_SOURCES = {
    "installs_weekly": "installs_sum_1w",
    "installs_monthly": "installs_sum_4w",
    "rating_count_weekly": "ratings_sum_1w",
}


def _api_key_guard(request, route_handler) -> None:
    """Guard that validates the X-API-Key header."""
    state = request.app.state
    validate_api_key(request, state)


def _build_app_basics_payload(state: State, store_id: str) -> PublicAppBasics:
    """Return public app metadata plus estimated growth, usage, and revenue signals."""
    app_df = get_single_app(state, store_id)
    if app_df.empty:
        msg = f"Store ID not found: {store_id!r}"
        raise NotFoundException(msg, status_code=404)

    app_dict = app_df.to_dict(orient="records")[0]
    return PublicAppBasics(
        **{
            field.name: app_dict.get(
                APP_BASICS_FIELD_SOURCES.get(field.name, field.name)
            )
            for field in dataclass_fields(PublicAppBasics)
        }
    )


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


class V1AppsController(Controller):
    """Public API v1 — app endpoints (API key required)."""

    path = "/api/v1/"
    guards = [_api_key_guard]

    @get(path="/apps/{store_id:str}", cache=3600)
    async def app_basics(self: Self, state: State, store_id: str) -> PublicAppBasics:
        """Return basic app metadata for a store identifier."""
        start = time.perf_counter() * 1000
        payload = _build_app_basics_payload(state=state, store_id=store_id)
        duration = round((time.perf_counter() * 1000 - start), 2)
        logger.info(f"GET /api/v1/apps/{store_id} took {duration}ms")
        return payload

    @get(path="/apps/{store_id:str}/ranks", cache=3600)
    async def app_ranks(
        self: Self, state: State, store_id: str
    ) -> list[PublicAppBestRank]:
        """Return best-rank records for a store identifier across countries."""
        start = time.perf_counter() * 1000
        payload = _build_app_ranks_payload(state=state, store_id=store_id)
        duration = round((time.perf_counter() * 1000 - start), 2)
        logger.info(f"GET /api/v1/apps/{store_id}/ranks took {duration}ms")
        return payload

    @get(path="/apps/{store_id:str}/sdks", cache=3600)
    async def app_sdk_details(
        self: Self, state: State, store_id: str
    ) -> PublicAppSdkDetails:
        """Return SDK details for a store identifier."""
        start = time.perf_counter() * 1000
        payload = _build_app_sdk_details_payload(state=state, store_id=store_id)
        duration = round((time.perf_counter() * 1000 - start), 2)
        logger.info(f"GET /api/v1/apps/{store_id}/sdks took {duration}ms")
        return payload
