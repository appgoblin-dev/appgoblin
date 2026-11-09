"""Module-level authentication database engine reference for the MCP server."""

from __future__ import annotations

from typing import TYPE_CHECKING

from config import get_logger

if TYPE_CHECKING:
    from sqlalchemy import Engine

logger = get_logger(__name__)

_engine: Engine | None = None


def set_mcp_engine(engine: Engine | None) -> None:
    """Set or clear the write engine used for API-key authentication."""
    global _engine  # noqa: PLW0603
    _engine = engine
    if engine is not None:
        logger.info("MCP server received authentication engine reference")


class MCPDatabaseUnavailableError(RuntimeError):
    """Raised when the authentication database is unavailable."""


def get_engine() -> Engine:
    """Return the injected engine or raise."""
    if _engine is None:
        msg = (
            "MCP database engine not initialised - call set_mcp_engine()"
            " during lifespan"
        )
        raise MCPDatabaseUnavailableError(msg)
    return _engine
