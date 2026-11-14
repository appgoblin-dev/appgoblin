"""MCP tools wrapping the public ``/api/v1/companies/`` endpoints.

Company tools are **paid-tier only** — unauthenticated or free-tier callers
receive a descriptive access-denied message rather than data.
"""

from __future__ import annotations

# `Context` must be importable at runtime — the framework
# uses it for dependency injection into tool functions, not just typing.
from mcp.server.mcpserver import Context  # noqa: TC002
from pydantic import Field

from api_app.controllers.companies import get_overviews
from api_app.controllers.public.v1.companies import (
    _build_public_company_app_change_payload,
    _build_public_company_overview_payload,
    _search_companies_payload,
    _to_public_company_list_item,
)
from api_app.mcp.serialize import to_json
from api_app.mcp.server import mcp_server
from api_app.mcp.state import assert_paid_tier, get_mcp_state
from config import get_logger

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------


@mcp_server.tool()
async def search_companies(
    q: str, ctx: Context, limit: int = Field(default=20, ge=1, le=100)
) -> str:
    """Search company names and domains. Paid-tier only; maximum limit 100."""
    assert_paid_tier(ctx, "search_companies")
    return to_json(_search_companies_payload(get_mcp_state(), q, limit))


@mcp_server.tool()
async def list_companies(ctx: Context) -> str:
    """Return all queryable company domains with latest overview trend snapshots.

    .. warning::
       This tool is restricted to paid-tier subscribers.
    """
    assert_paid_tier(ctx, "list_companies")

    state = get_mcp_state()
    overview = get_overviews(state=state)
    items = [_to_public_company_list_item(c) for c in overview.companies_overview]
    # Serialise as a JSON array of dicts
    return to_json(items)


@mcp_server.tool()
async def get_company_overview(company_domain: str, ctx: Context) -> str:  # noqa: D417
    """Fetch comprehensive market metrics, trends, and data for a company domain.

    Parameters
    ----------
    company_domain : str
        The domain of the target company (e.g. 'unity.com').

    """
    assert_paid_tier(ctx, "get_company_overview")

    state = get_mcp_state()
    try:
        payload = _build_public_company_overview_payload(
            state=state, company_domain=company_domain
        )
        return to_json(payload)
    except Exception as exc:
        logger.exception("Error fetching overview for %r", company_domain)
        msg = f"Error fetching overview for {company_domain!r}: {exc}"
        raise RuntimeError(msg) from exc


@mcp_server.tool()
async def get_company_app_changes(  # noqa: D417, PLR0913
    company_domain: str,
    tag_source: str,
    year: int,
    quarter: int,
    status: str,
    ctx: Context,
) -> str:
    """Return store IDs for apps a company added or lost in a given quarter.

    Parameters
    ----------
    company_domain : str
        The domain of the target company (e.g. 'unity.com').
    tag_source : str
        Signal source — one of ``sdk``, ``api_call``, ``app_ads_direct``.
    year : int
        Calendar year (e.g. 2026).
    quarter : int
        Quarter number (1, 2, 3, or 4).
    status : str
        Change direction — ``added`` or ``lost``.

    """
    assert_paid_tier(ctx, "get_company_app_changes")

    state = get_mcp_state()
    try:
        payload = _build_public_company_app_change_payload(
            state=state,
            company_domain=company_domain,
            tag_source=tag_source,
            year=year,
            quarter=quarter,
            status=status,
        )
        return to_json(payload)
    except Exception as exc:
        logger.exception(
            "Error fetching app changes for %r (%s, %dQ%d, %s)",
            company_domain,
            tag_source,
            year,
            quarter,
            status,
        )
        msg = (
            f"Error fetching app changes for {company_domain!r} "
            f"({tag_source=}, {year}Q{quarter}, {status=}): {exc}"
        )
        raise RuntimeError(msg) from exc
