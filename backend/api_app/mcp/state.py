"""Lightweight Litestar ``State`` surrogate + auth helpers for MCP tools.

Shared query helpers use the Litestar application state, including its read
and write connections and preloaded static data. The application lifespan
injects that same state for MCP tools.

Usage::

    from api_app.mcp.state import get_mcp_state, assert_paid_tier
    from dbcon.queries import get_single_app

    df = get_single_app(get_mcp_state(), store_id="...")
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from litestar.datastructures import State
    from mcp.server.mcpserver import Context


_mcp_state: State | None = None


def set_mcp_state(state: State | None) -> None:
    """Set or clear the application state used by MCP tools."""
    global _mcp_state  # noqa: PLW0603
    _mcp_state = state


def get_mcp_state() -> State:
    """Return the application state injected during lifespan startup."""
    if _mcp_state is None:
        msg = "MCP application state not initialised - start the application lifespan"
        raise RuntimeError(msg)
    return _mcp_state


# ---------------------------------------------------------------------------
# Tier-gated auth helper
# ---------------------------------------------------------------------------


class MCPAuthError(RuntimeError):
    """Raised when a tool's tier requirement is not met.

    MCPServer catches raised exceptions and returns a proper ``isError=true``
    MCP response, which clients display as tool execution failures rather
    than successful results.
    """


_UNAUTHENTICATED_MSG = "Access Denied: Unauthenticated agent request."


def _paid_tier_required_msg(tool_name: str) -> str:
    """Build the paid-tier-required error message."""
    return (
        f"Access Denied: The '{tool_name}' tool requires an active AppGoblin "
        "Paid Tier subscription. Please upgrade your account to continue."
    )


def assert_paid_tier(ctx: Context, tool_name: str) -> None:
    """Raise ``MCPAuthError`` if the caller is on the free tier.

    The authenticated user is read from ``scope["user"]`` (injected by
    ``AuthenticatedMCPMiddleware`` in ``controller.py``).
    """
    user = ctx.request_context.request.scope.get("user")
    if not user:
        raise MCPAuthError(_UNAUTHENTICATED_MSG)
    if user.tier == "free":
        raise MCPAuthError(_paid_tier_required_msg(tool_name))
