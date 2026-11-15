"""Versioned public ranking endpoints — requires API key authentication."""

import time
from typing import Self

import pandas as pd
from litestar import Controller, Request, Response, get
from litestar.datastructures import State
from litestar.exceptions import NotFoundException

from api_app.analytics import PUBLIC_API_HOSTNAME, build_request_page_view_task
from api_app.controllers.public.v1.apps import _api_key_guard
from api_app.controllers.public.v1.public_models import (
    PublicCtvAppRank,
    PublicCtvAppRanks,
    PublicRankCategory,
    PublicRankCollection,
)
from api_app.utils import extend_app_icon_url
from config import get_logger
from dbcon.queries import get_ctv_app_ranks, get_most_recent_top_ranks
from dbcon.static import get_store_collection_category_map

logger = get_logger(__name__)

STORE_NAMES = {1: "Google Play", 2: "Apple App Store"}
STORE_SLUGS = {1: "google-play", 2: "apple-app-store"}
STORE_IDS = {slug: store_id for store_id, slug in STORE_SLUGS.items()}
CTV_RANKS_LIMIT = 50


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
    return int(value)


def _optional_float(value: object) -> float | None:
    """Normalize optional floats from serialized pandas rows."""
    if _is_missing_value(value):
        return None
    return float(value)


def _to_public_ctv_app_rank(row: dict) -> PublicCtvAppRank:
    """Project a CTV rank dataframe row onto the public response model."""
    store_id = _optional_int(row.get("store"))
    return PublicCtvAppRank(
        rank=_optional_int(row.get("rank_num")),
        name=_optional_string(row.get("app_name")),
        store_id=_optional_string(row.get("store_id")),
        store=STORE_NAMES.get(store_id) if store_id is not None else None,
        category=_optional_string(row.get("app_category")),
        developer_name=_optional_string(row.get("developer_name")),
        rating=_optional_float(row.get("rating")),
        rating_count=_optional_int(row.get("rating_count")),
        installs=_optional_int(row.get("installs")),
        monthly_installs=_optional_float(row.get("monthly_installs")),
        monthly_revenue=_optional_float(row.get("monthly_revenue")),
        installs_z_score_2w=_optional_float(row.get("installs_z_score_2w")),
        country=_optional_string(row.get("country_code")),
        app_icon_url=_optional_string(row.get("app_icon_url")),
    )


def _build_ctv_app_ranks_payload(state: State, store: str) -> PublicCtvAppRanks:
    """Return the public top CTV app ranks payload for a store."""
    store_id = STORE_IDS.get(store)
    if store_id is None:
        msg = f"Unknown store: {store!r}. Use 'google-play' or 'apple-app-store'."
        raise NotFoundException(msg, status_code=404)

    store_name = STORE_NAMES[store_id]
    df = get_ctv_app_ranks(state, store=store_id, limit=CTV_RANKS_LIMIT)
    if df.empty:
        return PublicCtvAppRanks(store=store_name, country="US", apps=[])

    df = extend_app_icon_url(df)
    apps = [_to_public_ctv_app_rank(row) for row in df.to_dict(orient="records")]
    country = next((app.country for app in apps if app.country), "US")
    return PublicCtvAppRanks(store=store_name, country=country, apps=apps)


def _build_ranking_collections_payload(state: State) -> list[PublicRankCollection]:
    """Return unique ranking collections grouped by store."""
    collection_df = get_store_collection_category_map(state)
    if collection_df.empty:
        return []

    collection_df = (
        collection_df.loc[collection_df["store_id"].isin(STORE_SLUGS)]
        .dropna(subset=["store_id", "store_name", "collection_id", "collection_name"])
        .drop_duplicates(subset=["store_id", "collection_id"])
        .sort_values(["store_id", "collection_name"])
    )
    return [
        PublicRankCollection(
            store=STORE_SLUGS[int(row["store_id"])],
            store_name=str(row["store_name"]),
            collection=str(row["collection_name"]),
        )
        for row in collection_df.to_dict(orient="records")
    ]


def _build_ranking_categories_payload(state: State) -> list[PublicRankCategory]:
    """Return unique ranking categories grouped by store."""
    category_df = get_store_collection_category_map(state)
    if category_df.empty:
        return []

    category_df = (
        category_df.loc[category_df["store_id"].isin(STORE_SLUGS)]
        .dropna(subset=["store_id", "store_name", "category_id", "category_name"])
        .drop_duplicates(subset=["store_id", "category_id"])
        .sort_values(["store_id", "category_name"])
    )
    return [
        PublicRankCategory(
            store=STORE_SLUGS[int(row["store_id"])],
            store_name=str(row["store_name"]),
            category=str(row["category_name"]),
        )
        for row in category_df.to_dict(orient="records")
    ]


def _resolve_ranking_ids(
    state: State, store: str, collection: str, category: str
) -> tuple[int, int]:
    """Resolve public ranking names to internal IDs for the database query."""
    store_id = STORE_IDS.get(store)
    if store_id is None:
        raise NotFoundException(
            f"Unknown store: {store!r}. Use 'google-play' or 'apple-app-store'.",
            status_code=404,
        )

    rank_map = get_store_collection_category_map(state)
    if rank_map.empty:
        raise NotFoundException(
            f"Unknown ranking collection/category: {collection!r}/{category!r} "
            f"for store {store!r}.",
            status_code=404,
        )
    matches = rank_map.loc[
        (rank_map["store_id"] == store_id)
        & (rank_map["collection_name"] == collection)
        & (rank_map["category_name"] == category)
    ].dropna(subset=["collection_id", "category_id"])
    ids = matches[["collection_id", "category_id"]].drop_duplicates()
    if len(ids) != 1:
        raise NotFoundException(
            f"Unknown ranking collection/category: {collection!r}/{category!r} "
            f"for store {store!r}.",
            status_code=404,
        )

    row = ids.iloc[0]
    return int(row["collection_id"]), int(row["category_id"])


class V1RankingsController(Controller):
    """Public API v1 — ranking endpoints (API key required)."""

    path = "/api/v1/"
    guards = [_api_key_guard]

    @get(path="/rankings/collections", cache=3600)
    async def ranking_collections(
        self: Self, state: State, request: Request
    ) -> list[PublicRankCollection]:
        """List ranking collections for each app store."""
        payload = _build_ranking_collections_payload(state)
        return Response(
            payload,
            background=build_request_page_view_task(
                request,
                url="/api/v1/rankings/collections",
                hostname=PUBLIC_API_HOSTNAME,
            ),
        )

    @get(path="/rankings/categories", cache=3600)
    async def ranking_categories(
        self: Self, state: State, request: Request
    ) -> list[PublicRankCategory]:
        """List ranking categories for each app store."""
        payload = _build_ranking_categories_payload(state)
        return Response(
            payload,
            background=build_request_page_view_task(
                request,
                url="/api/v1/rankings/categories",
                hostname=PUBLIC_API_HOSTNAME,
            ),
        )

    @get(path="/rankings/{store:str}/{collection:str}/{category:str}", cache=86400)
    async def ranks_for_category(
        self: Self,
        state: State,
        request: Request,
        store: str,
        collection: str,
        category: str,
        country: str = "US",
    ) -> dict:
        """Return the latest ranked apps for a collection and category."""
        start = time.perf_counter() * 1000
        collection_id, category_id = _resolve_ranking_ids(
            state, store, collection, category
        )
        ranks_df = get_most_recent_top_ranks(
            state,
            collection_id=collection_id,
            category_id=category_id,
            country=country,
            limit=200,
        )
        ranks_df = ranks_df.drop(
            columns=["developer_name", "app_icon_url", "ratings_sum_1w"],
            errors="ignore",
        )
        best_rank_columns = [
            column
            for column in ranks_df.columns
            if isinstance(column, str) and column.startswith("best_rank_")
        ]
        ranks_df = ranks_df.drop(columns=best_rank_columns).rename(
            columns={
                "installs_sum_1w": "installs_week",
                "installs_sum_4w": "installs_month",
            }
        )
        if "crawled_date" in ranks_df:
            ranks_df["crawled_date"] = pd.to_datetime(
                ranks_df["crawled_date"]
            ).dt.strftime("%Y-%m-%d")
        payload = {"ranks": ranks_df.to_dict(orient="records")}
        duration = round((time.perf_counter() * 1000 - start), 2)
        logger.info(
            f"GET /api/v1/rankings/{store}/{collection}/{category} took {duration}ms"
        )
        return Response(
            payload,
            background=build_request_page_view_task(
                request,
                url=f"/api/v1/rankings/{store}/{collection}/{category}",
                hostname=PUBLIC_API_HOSTNAME,
            ),
        )

    @get(path="/rankings/ctv/{store:str}", cache=86400)
    async def ctv_app_ranks(
        self: Self, state: State, request: Request, store: str
    ) -> PublicCtvAppRanks:
        """Return the top CTV-supported apps for a store by monthly installs."""
        start = time.perf_counter() * 1000
        payload = _build_ctv_app_ranks_payload(state=state, store=store)
        duration = round((time.perf_counter() * 1000 - start), 2)
        logger.info(f"GET /api/v1/rankings/ctv/{store} took {duration}ms")
        return Response(
            payload,
            background=build_request_page_view_task(
                request,
                url=f"/api/v1/rankings/ctv/{store}",
                hostname=PUBLIC_API_HOSTNAME,
            ),
        )
