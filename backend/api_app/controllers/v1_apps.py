"""Versioned public app endpoints — requires API key authentication."""

import time
from typing import Self

import pandas as pd
from litestar import Controller, get
from litestar.datastructures import State
from litestar.exceptions import NotFoundException

from api_app.guards import validate_api_key
from config import get_logger
from dbcon.queries import (
    get_app_sdk_details,
    get_app_sdk_overview,
    get_ranks_for_app,
    get_ranks_for_app_overview,
    get_single_app,
)
from dbcon.static import get_company_logos_df

logger = get_logger(__name__)


def _api_key_guard(request, route_handler) -> None:
    """Guard that validates the X-API-Key header."""
    state = request.app.state
    validate_api_key(request, state)


def _build_app_basics_payload(state: State, store_id: str) -> dict:
    """Return a stable subset of basic app metadata for a store_id."""
    app_df = get_single_app(state, store_id)
    if app_df.empty:
        msg = f"Store ID not found: {store_id!r}"
        raise NotFoundException(msg, status_code=404)

    app_dict = app_df.to_dict(orient="records")[0]
    fields = [
        "id",
        "name",
        "store_id",
        "store",
        "category",
        "rating",
        "rating_count",
        "installs",
        "developer_id",
        "developer_name",
        "developer_url",
        "release_date",
        "ad_supported",
        "in_app_purchases",
        "app_icon_url",
        "store_link",
    ]
    return {field: app_dict.get(field) for field in fields}


def _build_app_ranks_overview_payload(state: State, store_id: str) -> dict:
    """Return the existing app ranks overview response shape."""
    overview_df = get_ranks_for_app_overview(state, store_id=store_id, days=90)
    if overview_df.empty:
        return {"countries": [], "best_ranks": []}

    countries = sorted(overview_df["country"].unique().tolist())
    return {
        "countries": countries,
        "best_ranks": overview_df.to_dict(orient="records"),
    }


def _build_app_sdk_overview_payload(state: State, store_id: str) -> dict:
    """Return the existing app SDK overview response shape."""
    overview_df = get_app_sdk_overview(state, store_id)
    if overview_df.empty:
        return {"company_categories": {}}

    overview_df = overview_df.merge(
        get_company_logos_df(state),
        left_on="company_domain",
        right_on="company_domain",
        how="left",
        validate="m:1",
    )

    company_categories: dict[str, list[dict]] = {}
    categories = (
        overview_df.loc[overview_df["category_slug"].notna(), "category_slug"]
        .unique()
        .tolist()
    )
    for category_slug in categories:
        company_categories[category_slug] = overview_df[
            overview_df["category_slug"] == category_slug
        ][["company_name", "company_domain", "company_logo_url"]].to_dict(
            orient="records"
        )

    return {"company_categories": company_categories}


def _build_app_ranks_payload(state: State, store_id: str, country: str = "US") -> dict:
    """Return the existing app rank history response shape."""
    ranks_df = get_ranks_for_app(state, store_id=store_id, country=country, days=90)
    if ranks_df.empty:
        return {"history": {}}

    ranks_df["rank_group"] = ranks_df["collection"] + ": " + ranks_df["category"]
    ranks_df["crawled_date"] = pd.to_datetime(ranks_df["crawled_date"]).dt.strftime(
        "%Y-%m-%d"
    )
    pivot_source = ranks_df[ranks_df["country"] == country][
        ["crawled_date", "rank", "rank_group"]
    ].sort_values("crawled_date")
    history = (
        pivot_source.pivot_table(
            columns=["rank_group"], index=["crawled_date"], values="rank"
        )
        .reset_index()
        .to_dict(orient="records")
    )
    return {"history": history}


def _build_app_sdk_details_payload(state: State, store_id: str) -> dict:
    """Return the existing app SDK details response shape."""
    sdk_df = get_app_sdk_details(state, store_id)

    if sdk_df.empty or sdk_df.isna().all().all():
        return {
            "company_categories": {},
            "permissions": [],
            "app_queries": [],
            "skadnetwork": [],
            "leftovers": {},
        }

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
    leftovers_df = sdk_df[
        ~is_permission
        & ~is_matching_store_id
        & ~is_android_activity
        & ~is_value_empty
        & ~is_package_query
        & ~is_skadnetwork
        & sdk_df["company_name"].isna()
    ]
    leftovers_df = leftovers_df[~leftovers_df["value_name"].isin(unwanted_value_names)]

    leftovers = {
        short_value_name: grouped_df.groupby("xml_path")["value_name"]
        .apply(list)
        .to_dict()
        for short_value_name, grouped_df in leftovers_df.groupby("short_value_name")
    }
    permissions = [
        value.replace("android.permission.", "")
        for value in permissions_df.value_name.tolist()
    ]
    app_queries = sdk_df[is_package_query].value_name.unique().tolist()
    skadnetwork = sdk_df[is_skadnetwork].value_name.unique().tolist()

    return {
        "company_categories": company_sdk_dict,
        "permissions": permissions,
        "app_queries": app_queries,
        "skadnetwork": skadnetwork,
        "leftovers": leftovers,
    }


class V1AppsController(Controller):
    """Public API v1 — app endpoints (API key required)."""

    path = "/api/v1/"
    guards = [_api_key_guard]

    @get(path="/apps/{store_id:str}", cache=3600)
    async def app_basics(self: Self, state: State, store_id: str) -> dict:
        """Return basic app metadata for a store identifier."""
        start = time.perf_counter() * 1000
        payload = _build_app_basics_payload(state=state, store_id=store_id)
        duration = round((time.perf_counter() * 1000 - start), 2)
        logger.info(f"GET /api/v1/apps/{store_id} took {duration}ms")
        return payload

    @get(path="/apps/{store_id:str}/ranks/overview", cache=3600)
    async def app_ranks_overview(self: Self, state: State, store_id: str) -> dict:
        """Return ranking overview data for a store identifier."""
        start = time.perf_counter() * 1000
        payload = _build_app_ranks_overview_payload(state=state, store_id=store_id)
        duration = round((time.perf_counter() * 1000 - start), 2)
        logger.info(f"GET /api/v1/apps/{store_id}/ranks/overview took {duration}ms")
        return payload

    @get(path="/apps/{store_id:str}/ranks", cache=3600)
    async def app_ranks(
        self: Self, state: State, store_id: str, country: str = "US"
    ) -> dict:
        """Return app rank history for a store identifier and country."""
        start = time.perf_counter() * 1000
        payload = _build_app_ranks_payload(
            state=state, store_id=store_id, country=country
        )
        duration = round((time.perf_counter() * 1000 - start), 2)
        logger.info(f"GET /api/v1/apps/{store_id}/ranks took {duration}ms")
        return payload

    @get(path="/apps/{store_id:str}/sdksoverview", cache=3600)
    async def app_sdk_overview(self: Self, state: State, store_id: str) -> dict:
        """Return SDK overview data grouped by company category."""
        start = time.perf_counter() * 1000
        payload = _build_app_sdk_overview_payload(state=state, store_id=store_id)
        duration = round((time.perf_counter() * 1000 - start), 2)
        logger.info(f"GET /api/v1/apps/{store_id}/sdksoverview took {duration}ms")
        return payload

    @get(path="/apps/{store_id:str}/sdks", cache=3600)
    async def app_sdk_details(self: Self, state: State, store_id: str) -> dict:
        """Return SDK details for a store identifier."""
        start = time.perf_counter() * 1000
        payload = _build_app_sdk_details_payload(state=state, store_id=store_id)
        duration = round((time.perf_counter() * 1000 - start), 2)
        logger.info(f"GET /api/v1/apps/{store_id}/sdks took {duration}ms")
        return payload
