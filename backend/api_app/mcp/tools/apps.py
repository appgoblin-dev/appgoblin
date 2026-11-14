"""MCP tools wrapping the public ``/api/v1/apps/`` endpoints.

Each tool reuses the existing ``dbcon.queries`` functions and
``public_models`` dataclasses so the business logic stays in one place.
"""

from __future__ import annotations

# `Context` must be importable at runtime — the framework
# uses it for dependency injection into tool functions, not just typing.
from mcp.server.mcpserver import Context  # noqa: TC002
from pydantic import Field

from api_app.controllers.public.v1.apps import (
    _build_app_basics_payload,
    _build_app_sdk_details_payload,
    _search_apps_payload,
)
from api_app.controllers.public.v1.public_models import PublicAppBestRank
from api_app.mcp.serialize import to_json
from api_app.mcp.server import mcp_server
from api_app.mcp.state import get_mcp_state
from config import get_logger
from dbcon.queries import get_ranks_for_app_overview

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------


@mcp_server.tool()
async def search_apps(
    q: str,
    ctx: Context,  # noqa: ARG001
    limit: int = Field(default=20, ge=1, le=100),
) -> str:
    """Search app names and identifiers. Limit defaults to 20, maximum 100."""
    return to_json(_search_apps_payload(get_mcp_state(), q, limit))


@mcp_server.tool()
async def search_developer_apps(
    q: str,
    ctx: Context,  # noqa: ARG001
    limit: int = Field(default=20, ge=1, le=100),
) -> str:
    """Search apps by developer name. Limit defaults to 20, maximum 100."""
    return to_json(_search_apps_payload(get_mcp_state(), q, limit, developer=True))


@mcp_server.tool()
async def get_app_basics(  # noqa: D417
    store_id: str,
    ctx: Context,  # noqa: ARG001
) -> str:
    """Return app metadata, growth estimates, and revenue signals for an app.

    Parameters
    ----------
    store_id : str
        The app's store identifier (e.g. 'dev.thirdgate.appgoblin' for Google
        Play, or '1234567890' for the Apple App Store).

    """
    state = get_mcp_state()
    try:
        payload = _build_app_basics_payload(state, store_id)
        return to_json(payload)
    except Exception as exc:
        logger.exception("Error fetching app basics for %r", store_id)
        msg = f"Error fetching app basics for {store_id!r}: {exc}"
        raise RuntimeError(msg) from exc


@mcp_server.tool()
async def get_app_best_ranks(  # noqa: D417
    store_id: str,
    ctx: Context,  # noqa: ARG001
) -> str:
    """Return the best rank achieved by an app across countries and collections.

    Parameters
    ----------
    store_id : str
        The app's store identifier.

    """
    state = get_mcp_state()
    overview_df = get_ranks_for_app_overview(state, store_id=store_id, days=90)
    if overview_df.empty:
        return f"No rank data found for store_id: {store_id!r}"

    ranks = [
        PublicAppBestRank(
            country=str(row["country"]),
            collection=str(row["collection"]),
            category=str(row["category"]),
            best_rank=int(row["best_rank"]),
        )
        for row in overview_df.to_dict(orient="records")
    ]
    return to_json(ranks)


@mcp_server.tool()
async def get_app_sdk_details(  # noqa: D417
    store_id: str,
    ctx: Context,  # noqa: ARG001
) -> str:
    """Return detailed SDK and manifest findings for a single app.

    Includes permissions, SDK companies, and app queries.

    Parameters
    ----------
    store_id : str
        The app's store identifier.

    """
    state = get_mcp_state()
    try:
        payload = _build_app_sdk_details_payload(state, store_id)
        return to_json(payload)
    except Exception as exc:
        logger.exception("Error fetching SDK details for %r", store_id)
        msg = f"Error fetching SDK details for {store_id!r}: {exc}"
        raise RuntimeError(msg) from exc
