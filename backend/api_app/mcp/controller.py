"""ASGI middleware + lifecycle wiring for the MCP server inside Litestar.

Architecture
------------
MCPServer generates a Starlette-compatible ASGI app
(``mcp_server.streamable_http_app()``).
Because Litestar uses its own ASGI lifecycle, we wrap the MCP app in a thin
middleware that handles **authentication** and **rate limiting** at the ASGI
layer *before* requests reach any tool handler.

Engine injection
----------------
The Litestar ``db_lifespan`` callback calls ``set_mcp_engine()`` after
creating database connections, so the MCP middleware and tools can query the
same connection pool without depending on ``app.state``.
"""

from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass
from typing import TYPE_CHECKING

# Import the MCP package first — the __init__.py registers all tools.
# Then pull the server instance and shared authentication primitives.
import api_app.mcp  # noqa: F401  # triggers tool registration
from api_app.guards import (
    _daily_quota,
    _query_key,
    _rate_limiter,
    get_tier_limits,
)
from api_app.mcp.engine import get_engine, set_mcp_engine  # noqa: F401
from api_app.mcp.server import mcp_server
from config import get_logger

if TYPE_CHECKING:
    from litestar.types import ASGIApp, Receive, Scope, Send

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Authentication helpers (stand-alone; no Litestar Request dependency)
# ---------------------------------------------------------------------------


@dataclass
class MCPAuthContext:
    """Authenticated user context injected into the ASGI scope."""

    user_id: int
    tier: str
    key_hash: str
    minute_limit: int
    minute_remaining: int
    daily_limit: int
    daily_remaining: int
    retry_after: int


def _normalise_header(scope: Scope, name: bytes) -> str | None:
    """Extract a single header value from the raw ASGI scope header tuple."""
    for key, value in scope.get("headers", []):
        if key.lower() == name:
            return value.decode("utf-8", errors="replace")
    return None


def _authenticate(scope: Scope) -> MCPAuthContext | None:
    """Validate API key and enforce rate limits.

    Returns an ``MCPAuthContext`` when the request is authorised, or ``None``
    when the key is missing / invalid.  The caller should emit a 401 response
    in the latter case.

    Rate-limit violations raise ``_RateLimitError`` so the middleware can emit
    429 responses.
    """
    raw_key = _normalise_header(scope, b"authorization")
    if raw_key:
        for prefix in ("bearer ", "token "):
            if raw_key.lower().startswith(prefix):
                raw_key = raw_key[len(prefix) :]
                break
        else:
            raw_key = _normalise_header(scope, b"x-api-key")
    else:
        raw_key = _normalise_header(scope, b"x-api-key")
    if not raw_key:
        return None

    key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
    engine = get_engine()

    # Resolve tier (cache-aware, same as guards.validate_api_key)
    from api_app.guards import _KEY_CACHE  # noqa: PLC0415

    cached = _KEY_CACHE.get(key_hash)
    if cached is not None and time.monotonic() < cached.expires_at:
        tier = cached.tier
        user_id = cached.user_id
    else:
        result = _query_key(engine, key_hash)
        if result is None:
            return None
        _KEY_CACHE[key_hash] = result
        tier = result.tier
        user_id = result.user_id

    limits = get_tier_limits(tier)

    # --- Daily quota ---
    daily_ok, daily_limit, daily_remaining = _daily_quota.check(
        str(user_id), limits.requests_per_day
    )
    if not daily_ok:
        logger.warning(
            "MCP daily quota exceeded",
            extra={"user_id": user_id, "tier": tier, "daily_limit": daily_limit},
        )
        raise _RateLimitError(
            detail="Daily request quota exceeded",
            retry_after=86400,
            limit=daily_limit,
            remaining=0,
        )

    # --- Per-minute burst ---
    minute_ok, minute_limit, minute_remaining, retry_after = _rate_limiter.check(
        str(user_id), limits.requests_per_minute
    )
    if not minute_ok:
        logger.warning(
            "MCP per-minute rate limit exceeded",
            extra={
                "user_id": user_id,
                "tier": tier,
                "minute_limit": minute_limit,
            },
        )
        raise _RateLimitError(
            detail="Rate limit exceeded",
            retry_after=retry_after,
            limit=minute_limit,
            remaining=0,
        )

    return MCPAuthContext(
        user_id=user_id,
        tier=tier,
        key_hash=key_hash,
        minute_limit=minute_limit,
        minute_remaining=minute_remaining,
        daily_limit=daily_limit,
        daily_remaining=daily_remaining,
        retry_after=retry_after,
    )


# ---------------------------------------------------------------------------
# ASGI middleware
# ---------------------------------------------------------------------------


class _RateLimitError(Exception):
    """Raised inside the middleware when a rate limit is hit."""

    def __init__(
        self,
        detail: str,
        retry_after: int,
        limit: int,
        remaining: int,
    ) -> None:
        self.detail = detail
        self.retry_after = retry_after
        self.limit = limit
        self.remaining = remaining
        super().__init__(detail)


class AuthenticatedMCPMiddleware:
    """ASGI middleware that authenticates + rate-limits every MCP request.

    Wraps the MCP HTTP app.  On success the authenticated user context
    is injected into ``scope["user"]`` so that tool handlers can retrieve it
    via ``ctx.request_context.request.scope.get("user")``.
    """

    def __init__(self, app: ASGIApp) -> None:
        """Store the underlying ASGI app."""
        self.app = app

    async def __call__(  # noqa: D102
        self, scope: Scope, receive: Receive, send: Send
    ) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        # --- Authenticate ---
        try:
            user_ctx = _authenticate(scope)
        except _RateLimitError as exc:
            await send(
                {
                    "type": "http.response.start",
                    "status": 429,
                    "headers": [
                        (b"content-type", b"application/json"),
                        (b"retry-after", str(exc.retry_after).encode()),
                        (b"x-ratelimit-limit", str(exc.limit).encode()),
                        (b"x-ratelimit-remaining", str(exc.remaining).encode()),
                    ],
                }
            )
            await send(
                {
                    "type": "http.response.body",
                    "body": (b'{"error":"' + exc.detail.encode() + b'"}'),
                    "more_body": False,
                }
            )
            return

        if user_ctx is None:
            await send(
                {
                    "type": "http.response.start",
                    "status": 401,
                    "headers": [(b"content-type", b"application/json")],
                }
            )
            await send(
                {
                    "type": "http.response.body",
                    "body": (
                        b'{"error":"Unauthorized: Send your API key as the Authorization: Bearer header."}'
                    ),
                    "more_body": False,
                }
            )
            return

        # --- Inject user into scope ---
        scope["user"] = user_ctx

        # --- Hand off to MCP engine ---
        await self.app(scope, receive, send)


# ---------------------------------------------------------------------------
# Pre-wired ASGI app (imported by app.py)
# ---------------------------------------------------------------------------

mcp_asgi_app = mcp_server.streamable_http_app(streamable_http_path="/")
protected_mcp_app = AuthenticatedMCPMiddleware(mcp_asgi_app)
