"""MCP tools wrapping the public ``/api/v1/keywords/`` endpoints."""

from __future__ import annotations

# `Context` must be importable at runtime — the framework
# uses it for dependency injection into tool functions, not just typing.
from mcp.server.mcpserver import Context  # noqa: TC002

from api_app.controllers.public.v1.keywords import (
    _build_keyword_metrics_payload,
    _build_keyword_ranks_payload,
)
from api_app.mcp.serialize import to_json
from api_app.mcp.server import mcp_server
from api_app.mcp.state import get_mcp_state
from config import get_logger

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------


@mcp_server.tool()
async def get_keyword_metrics(  # noqa: D417
    keyword: str,
    ctx: Context,  # noqa: ARG001
) -> str:
    """Return keyword difficulty, competition, and opportunity scores.

    Parameters
    ----------
    keyword : str
        The exact search term (e.g. 'app privacy', 'fitness tracker').

    """
    state = get_mcp_state()
    try:
        payload = _build_keyword_metrics_payload(state=state, keyword=keyword)
        return to_json(payload)
    except Exception as exc:
        logger.exception("Error fetching keyword metrics for %r", keyword)
        msg = f"Error fetching keyword metrics for {keyword!r}: {exc}"
        raise RuntimeError(msg) from exc


@mcp_server.tool()
async def get_keyword_ranks(  # noqa: D417
    keyword: str,
    ctx: Context,  # noqa: ARG001
    limit: int = 20,
) -> str:
    """Return the top-ranked apps for an exact keyword lookup, grouped by platform.

    Parameters
    ----------
    keyword : str
        The exact search term (e.g. 'app privacy').
    limit : int
        Maximum number of ranked apps to return per platform (default 20).

    """
    state = get_mcp_state()
    try:
        payload = _build_keyword_ranks_payload(
            state=state, keyword=keyword, limit=limit
        )
        return to_json(payload)
    except Exception as exc:
        logger.exception("Error fetching keyword ranks for %r", keyword)
        msg = f"Error fetching keyword ranks for {keyword!r}: {exc}"
        raise RuntimeError(msg) from exc
