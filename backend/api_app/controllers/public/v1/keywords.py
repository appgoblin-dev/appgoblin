"""Versioned public keyword endpoints — requires API key authentication."""

import time
from typing import Self, SupportsFloat, SupportsIndex, SupportsInt

from litestar import Controller, Request, Response, get
from litestar.datastructures import State
from litestar.exceptions import NotFoundException
from litestar.params import Parameter

from api_app.analytics import PUBLIC_API_HOSTNAME, build_request_page_view_task
from api_app.controllers.public.v1.apps import _api_key_guard
from api_app.controllers.public.v1.public_models import (
    PublicKeywordMetrics,
    PublicKeywordPlatformMetrics,
    PublicKeywordRankedApp,
    PublicKeywordRanks,
)
from api_app.utils import extend_app_icon_url
from config import get_logger
from dbcon.queries import get_keyword_apps, get_keyword_details

logger = get_logger(__name__)

_STORE_TO_PLATFORM = {1: "android", 2: "ios"}
_PLATFORM_ORDER = ("android", "ios")


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


def _build_keyword_metrics_by_platform(
    state: State, keyword: str
) -> dict[str, PublicKeywordPlatformMetrics | None]:
    """Return keyword metric records split by public platform key."""
    keyword_df = get_keyword_details(state, keyword)
    if keyword_df.empty:
        msg = f"Keyword not found: {keyword!r}"
        raise NotFoundException(msg, status_code=404)

    metrics_by_platform: dict[str, PublicKeywordPlatformMetrics | None] = dict.fromkeys(
        _PLATFORM_ORDER
    )  # type: ignore[assignment]
    for row in keyword_df.to_dict(orient="records"):
        store_val = _optional_int(row.get("store"))
        platform = _STORE_TO_PLATFORM.get(store_val)  # type: ignore[arg-type]
        if platform is None:
            continue

        metrics_by_platform[platform] = PublicKeywordPlatformMetrics(
            app_count=_optional_int(row.get("app_count")),
            total_apps=_optional_int(row.get("total_apps")),
            median_competitor_installs=_optional_int(
                row.get("median_competitor_installs")
            ),
            avg_competitor_rating=_optional_float(row.get("avg_competitor_rating")),
            major_competitors=_optional_int(row.get("major_competitors")),
            volume_competition_score=_optional_float(
                row.get("volume_competition_score")
            ),
            keyword_difficulty=_optional_float(row.get("keyword_difficulty")),
            opportunity_score=_optional_float(row.get("opportunity_score")),
            competitiveness_score=_optional_float(row.get("competitiveness_score")),
        )

    return metrics_by_platform


def _assert_keyword_exists(state: State, keyword: str) -> None:
    """Raise a 404 when the keyword is missing from the metrics dataset."""
    keyword_df = get_keyword_details(state, keyword)
    if keyword_df.empty:
        msg = f"Keyword not found: {keyword!r}"
        raise NotFoundException(msg, status_code=404)


def _build_keyword_top_apps_by_platform(
    state: State, keyword: str, limit: int
) -> dict[str, list[PublicKeywordRankedApp]]:
    """Return top ranked apps for a keyword split by public platform key."""
    apps_df = get_keyword_apps(state, keyword, rank=limit + 1)
    if apps_df.empty:
        _assert_keyword_exists(state, keyword)

    apps_df = extend_app_icon_url(apps_df)

    apps_by_platform: dict[str, list[PublicKeywordRankedApp]] = {
        platform: [] for platform in _PLATFORM_ORDER
    }
    for row in apps_df.to_dict(orient="records"):
        store_val = _optional_int(row.get("store"))
        platform = _STORE_TO_PLATFORM.get(store_val)  # type: ignore[arg-type]
        if platform is None:
            continue

        apps_by_platform[platform].append(
            PublicKeywordRankedApp(
                name=_optional_string(row.get("name")),
                store_id=_optional_string(row.get("store_id")),
                category=_optional_string(row.get("category")),
                installs=_optional_int(row.get("installs")),
                rating_count=_optional_int(row.get("rating_count")),
                app_icon_url=_optional_string(row.get("app_icon_url")),
                latest_rank=_optional_int(row.get("latest_app_rank")),
                best_rank_d30=_optional_int(row.get("d30_best_rank")),
            )
        )

    return apps_by_platform


def _build_keyword_metrics_payload(state: State, keyword: str) -> PublicKeywordMetrics:
    """Return the public keyword metrics payload."""
    metrics_by_platform = _build_keyword_metrics_by_platform(
        state=state, keyword=keyword
    )

    return PublicKeywordMetrics(
        keyword=keyword,
        country="US",
        android=metrics_by_platform["android"],
        ios=metrics_by_platform["ios"],
    )


def _build_keyword_ranks_payload(
    state: State, keyword: str, limit: int
) -> PublicKeywordRanks:
    """Return the public keyword latest-ranks payload."""
    apps_by_platform = _build_keyword_top_apps_by_platform(
        state=state, keyword=keyword, limit=limit
    )

    return PublicKeywordRanks(
        keyword=keyword,
        country="US",
        android=apps_by_platform["android"],
        ios=apps_by_platform["ios"],
    )


class V1KeywordsController(Controller):
    """Public API v1 — keyword endpoints (API key required)."""

    path = "/api/v1/"
    guards = [_api_key_guard]

    @get(path="/keywords/{keyword:str}", cache=3600)
    async def keyword_metrics(
        self: Self,
        state: State,
        request: Request,
        keyword: str,
    ) -> PublicKeywordMetrics:
        """Return keyword difficulty and competition metrics for an exact keyword lookup."""
        start = time.perf_counter() * 1000
        payload = _build_keyword_metrics_payload(state=state, keyword=keyword)
        duration = round((time.perf_counter() * 1000 - start), 2)
        logger.info(f"GET /api/v1/keywords/{keyword} took {duration}ms")
        return Response(
            payload,
            background=build_request_page_view_task(
                request,
                url=f"/api/v1/keywords/{keyword}",
                hostname=PUBLIC_API_HOSTNAME,
            ),
        )

    @get(path="/keywords/{keyword:str}/ranks", cache=3600)
    async def keyword_ranks(
        self: Self,
        state: State,
        request: Request,
        keyword: str,
        limit: int = Parameter(default=20, le=200),
    ) -> PublicKeywordRanks:
        """Return grouped latest top-ranked apps for an exact keyword lookup."""
        start = time.perf_counter() * 1000
        payload = _build_keyword_ranks_payload(
            state=state,
            keyword=keyword,
            limit=limit,
        )
        duration = round((time.perf_counter() * 1000 - start), 2)
        logger.info(f"GET /api/v1/keywords/{keyword}/ranks took {duration}ms")
        return Response(
            payload,
            background=build_request_page_view_task(
                request,
                url=f"/api/v1/keywords/{keyword}/ranks",
                hostname=PUBLIC_API_HOSTNAME,
            ),
        )
