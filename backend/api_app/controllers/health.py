"""Health check API controllers."""

from datetime import UTC, date, datetime, time, timedelta
from typing import Self

from litestar import Controller, Response, get
from litestar.datastructures import State
from sqlalchemy import text

from config import get_logger

logger = get_logger(__name__)

NO_CACHE_HEADERS = {
    "Cache-Control": "no-store,no-cache,must-revalidate",
    "Pragma": "no-cache",
    "Expires": "0",
}


def _utc_now_iso() -> str:
    """Return the current UTC timestamp in ISO-8601 format with Z suffix."""
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def _normalize_to_utc(value: object) -> datetime | None:
    """Normalize DB timestamp/date values to timezone-aware UTC datetime."""
    if value is None:
        return None

    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=UTC)
        return value.astimezone(UTC)

    if isinstance(value, date):
        return datetime.combine(value, time.min, tzinfo=UTC)

    if isinstance(value, str):
        parsed = value.strip()
        if parsed.endswith("Z"):
            parsed = parsed[:-1] + "+00:00"
        try:
            parsed_dt = datetime.fromisoformat(parsed)
        except ValueError:
            logger.warning(
                "Failed to parse datetime string for health check: %s", value
            )
            return None

        if parsed_dt.tzinfo is None:
            return parsed_dt.replace(tzinfo=UTC)
        return parsed_dt.astimezone(UTC)

    logger.warning(
        "Unsupported datetime type for health check: %s", type(value).__name__
    )
    return None


def _build_health_response(
    check_name: str,
    check_payload: dict[str, object],
    failed_checks: list[str],
) -> Response:
    """Build a standard health response for a single check."""
    status = "ok" if not failed_checks else "degraded"
    status_code = 200 if not failed_checks else 503
    payload = {
        "status": status,
        "service": "backend",
        "timestamp_utc": _utc_now_iso(),
        "checks": {check_name: check_payload},
        "failed_checks": failed_checks,
    }
    return Response(payload, status_code=status_code, headers=NO_CACHE_HEADERS)


def _check_db_connection(state: State) -> tuple[dict[str, object], list[str]]:
    """Check DB connectivity with a lightweight query."""
    failed_checks: list[str] = []
    check_payload: dict[str, object] = {"ok": False}

    try:
        with state.dbcon.engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        check_payload = {"ok": True}
    except Exception:
        logger.exception("Health check DB connectivity probe failed")
        failed_checks.append("db_connection")

    return check_payload, failed_checks


def _check_ranks_freshness(
    state: State, now_utc: datetime
) -> tuple[dict[str, object], list[str]]:
    """Check freshness of rank data."""
    failed_checks: list[str] = []
    check_payload: dict[str, object] = {
        "ok": False,
        "last_ranks_crawled_at": None,
        "threshold": "1 day",
    }

    try:
        with state.dbcon.engine.connect() as conn:
            ranks_row = (
                conn.execute(
                    text(
                        "SELECT max(crawled_date) AS last_ranks_crawled_at "
                        "FROM frontend.store_app_ranks_weekly"
                    )
                )
                .mappings()
                .one()
            )
        last_ranks_raw = ranks_row.get("last_ranks_crawled_at")
        last_ranks_utc = _normalize_to_utc(last_ranks_raw)
        ranks_ok = last_ranks_utc is not None and now_utc - last_ranks_utc <= timedelta(
            days=1
        )
        check_payload = {
            "ok": ranks_ok,
            "last_ranks_crawled_at": (
                last_ranks_utc.isoformat().replace("+00:00", "Z")
                if last_ranks_utc
                else None
            ),
            "threshold": "1 day",
        }
        if not ranks_ok:
            failed_checks.append("ranks_freshness")
    except Exception:
        logger.exception("Health check ranks freshness probe failed")
        failed_checks.append("ranks_freshness")

    return check_payload, failed_checks


def _check_apps_freshness(
    state: State, now_utc: datetime
) -> tuple[dict[str, object], list[str]]:
    """Check freshness of app overview data."""
    failed_checks: list[str] = []
    check_payload: dict[str, object] = {
        "ok": False,
        "last_apps_updated_at": None,
        "threshold": "5 hours",
    }

    try:
        with state.dbcon.engine.connect() as conn:
            apps_row = (
                conn.execute(
                    text(
                        "SELECT max(updated_at) AS last_apps_updated_at "
                        "FROM frontend.store_apps_overview"
                    )
                )
                .mappings()
                .one()
            )
        last_apps_raw = apps_row.get("last_apps_updated_at")
        last_apps_utc = _normalize_to_utc(last_apps_raw)
        apps_ok = last_apps_utc is not None and now_utc - last_apps_utc <= timedelta(
            hours=5
        )
        check_payload = {
            "ok": apps_ok,
            "last_apps_updated_at": (
                last_apps_utc.isoformat().replace("+00:00", "Z")
                if last_apps_utc
                else None
            ),
            "threshold": "5 hours",
        }
        if not apps_ok:
            failed_checks.append("apps_freshness")
    except Exception:
        logger.exception("Health check apps freshness probe failed")
        failed_checks.append("apps_freshness")

    return check_payload, failed_checks


class HealthController(Controller):
    """Health endpoints for backend service and DB freshness checks."""

    path = "/api/public/"

    @get(path="health/check")
    async def check(self: Self) -> Response:
        """Check basic backend liveness endpoint."""
        payload = {
            "status": "ok",
            "service": "backend",
            "timestamp_utc": _utc_now_iso(),
            "checks": {
                "app_lifecycle": {
                    "ok": True,
                }
            },
        }
        return Response(payload, status_code=200, headers=NO_CACHE_HEADERS)

    @get(path="health/db")
    async def checkdb_connection(self: Self, state: State) -> Response:
        """Check basic database connectivity."""
        check_payload, failed_checks = _check_db_connection(state)
        return _build_health_response("db_connection", check_payload, failed_checks)

    @get(path="health/ranks")
    async def checkdb_ranks(self: Self, state: State) -> Response:
        """Check freshness of rank data."""
        check_payload, failed_checks = _check_ranks_freshness(state, datetime.now(UTC))
        return _build_health_response("ranks_freshness", check_payload, failed_checks)

    @get(path="health/apps")
    async def checkdb_apps(self: Self, state: State) -> Response:
        """Check freshness of app overview data."""
        check_payload, failed_checks = _check_apps_freshness(state, datetime.now(UTC))
        return _build_health_response("apps_freshness", check_payload, failed_checks)
