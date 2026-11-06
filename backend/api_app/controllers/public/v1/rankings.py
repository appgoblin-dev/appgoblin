"""Versioned public ranking endpoints — requires API key authentication."""

import time
from typing import Self

from litestar import Controller, Request, Response, get
from litestar.datastructures import State
from litestar.exceptions import NotFoundException

from api_app.analytics import PUBLIC_API_HOSTNAME, build_request_page_view_task
from api_app.controllers.public.v1.apps import _api_key_guard
from api_app.controllers.public.v1.public_models import (
    PublicCtvAppRank,
    PublicCtvAppRanks,
)
from api_app.utils import extend_app_icon_url
from config import get_logger
from dbcon.queries import get_ctv_app_ranks

logger = get_logger(__name__)

STORE_NAMES = {1: "Google Play", 2: "Apple App Store"}
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


def _build_ctv_app_ranks_payload(state: State, store: int) -> PublicCtvAppRanks:
    """Return the public top CTV app ranks payload for a store."""
    store_name = STORE_NAMES.get(store)
    if store_name is None:
        msg = (
            f"Unknown store: {store!r}. "
            "Use 1 for Google Play or 2 for Apple App Store."
        )
        raise NotFoundException(msg, status_code=404)

    df = get_ctv_app_ranks(state, store=store, limit=CTV_RANKS_LIMIT)
    if df.empty:
        return PublicCtvAppRanks(store=store_name, country="US", apps=[])

    df = extend_app_icon_url(df)
    apps = [_to_public_ctv_app_rank(row) for row in df.to_dict(orient="records")]
    country = next((app.country for app in apps if app.country), "US")
    return PublicCtvAppRanks(store=store_name, country=country, apps=apps)


class V1RankingsController(Controller):
    """Public API v1 — ranking endpoints (API key required)."""

    path = "/api/v1/"
    guards = [_api_key_guard]

    @get(path="/rankings/ctv/{store:int}", cache=86400)
    async def ctv_app_ranks(
        self: Self, state: State, request: Request, store: int
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
