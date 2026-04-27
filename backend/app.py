"""Main start point for LiteStar API."""

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from datetime import UTC, datetime, timedelta

from litestar import Litestar, Request
from litestar.config.cors import CORSConfig
from litestar.logging import LoggingConfig
from litestar.middleware import DefineMiddleware
from litestar.openapi import OpenAPIConfig, OpenAPIController

from api_app.controllers.apps import AppController
from api_app.controllers.categories import CategoryController
from api_app.controllers.companies import CompaniesController
from api_app.controllers.creatives import CreativesController
from api_app.controllers.developers import DeveloperController
from api_app.controllers.exports import ExportsController
from api_app.controllers.health import HealthController
from api_app.controllers.keywords import KeywordsController
from api_app.controllers.rankings import RankingsController
from api_app.controllers.scry import ScryController
from api_app.controllers.sdks import SdksController
from api_app.controllers.v1_apps import V1AppsController
from api_app.controllers.v1_companies import V1CompaniesController
from api_app.controllers.v1_docs import V1DocsController
from api_app.guards import configure_tier_mapping
from config import CONFIG
from dbcon.connections import get_db_connection
from dbcon.static import load_static_data

logger = logging.getLogger(__name__)


cors_config = CORSConfig(
    allow_origins=[
        "localhost",
        "appgoblin.info",
    ],
)


class MyOpenAPIController(OpenAPIController):
    """Set Path for API docs."""

    path = "/api/docs"


logging_config = LoggingConfig(
    root={"level": logging.getLevelName(logging.INFO), "handlers": ["console"]},
    formatters={
        "standard": {"format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"},
    },
)


def restrict_access(request: Request, route_handler) -> None:
    """Guard to restrict access.

    - ScryController endpoints are always public
    - Other endpoints are open to localhost, but require an API key otherwise

    """
    if route_handler.owner.__class__ == ScryController:
        return

    # Check if the request is from localhost
    client_host = request.client.host if request.client else None
    is_localhost = client_host in ("127.0.0.1", "localhost")

    if is_localhost:
        return


# Apply the guard to specific controllers
private_controllers = [
    AppController,
    DeveloperController,
    CategoryController,
    RankingsController,
    CompaniesController,
    SdksController,
    CreativesController,
]

# Set the guard on private controllers
for controller in private_controllers:
    setattr(controller, "guards", [restrict_access])


class RateLimitMiddleware:
    """Adds X-RateLimit-* headers to V1 API responses."""

    def __init__(self, app) -> None:
        self.app = app

    async def __call__(self, scope, receive, send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        async def send_with_rate_limit_headers(message):
            if message["type"] == "http.response.start":
                rate_info = scope.get("_rate_limit_info")
                if rate_info:
                    headers = list(message.get("headers", []))
                    # Per-minute headers (standard)
                    headers.append(
                        (b"x-ratelimit-limit", str(rate_info["minute_limit"]).encode())
                    )
                    headers.append(
                        (
                            b"x-ratelimit-remaining",
                            str(rate_info["minute_remaining"]).encode(),
                        )
                    )
                    # Daily quota headers (IETF RateLimit-Fields draft)
                    headers.append(
                        (
                            b"x-ratelimit-policy",
                            f"{rate_info['daily_limit']};w=86400".encode(),
                        )
                    )
                    headers.append(
                        (
                            b"x-ratelimit-quota-remaining",
                            str(rate_info["daily_remaining"]).encode(),
                        )
                    )
                    message = {**message, "headers": headers}
            await send(message)

        await self.app(scope, receive, send_with_rate_limit_headers)


async def cleanup_expired_responses(request: Request) -> None:
    """Periodically clean up expired entries from the response cache store.

    Litestar's MemoryStore doesn't automatically evict expired entries. This
    handler runs after each response and checks if cleanup is needed (at most
    every 10 minutes). This prevents the cache dict from growing unbounded.

    At 1M requests/day, this results in ~144 cleanup cycles/day, which is
    minimal overhead. The timestamp check on each request is negligible
    (~microseconds), only the cleanup cycle (every 10 min) has material cost.

    This pattern is from the official Litestar documentation:
    https://docs.litestar.dev/2/usage/stores.html#deleting-expired-values
    """
    now = datetime.now(UTC)
    last_cleared = request.app.state.get("store_last_cleared")

    # Only run cleanup every 10 minutes at most
    if last_cleared is None or now - last_cleared > timedelta(seconds=600):
        try:
            store = request.app.stores.get("response_cache")
            if hasattr(store, "delete_expired"):
                await store.delete_expired()
                logger.debug("Purged expired response cache entries")
        except Exception:
            logger.exception("Error during response cache cleanup")

        request.app.state["store_last_cleared"] = now


@asynccontextmanager
async def db_lifespan(app: Litestar) -> AsyncGenerator[None]:
    """Manage database connections for the application lifespan.

    This context manager:
    1. Creates database connections on startup
    2. Stores them in app.state for access throughout the app
    3. Ensures proper cleanup on shutdown, even if errors occur
    """
    logger.info("Starting database connections...")

    # Load Stripe price → tier mapping from config
    tier_prices = CONFIG.get("tier_prices", {})
    if tier_prices:
        configure_tier_mapping(tier_prices)
        logger.info(f"Loaded {len(tier_prices)} tier price mappings")

    # Initialize connections
    try:
        dbcon = getattr(app.state, "dbcon", None)
        if dbcon is None:
            app.state.dbcon = get_db_connection(server_name="madrone")
        logger.info("Connected to madrone (read)")

        # Preload all static data
        logger.info("Preloading static data...")
        app.state.static_data = load_static_data(app.state.dbcon.engine)
        logger.info("Static data preloading complete")

        try:
            dbconwrite = getattr(app.state, "dbconwrite", None)
            if dbconwrite is None:
                app.state.dbconwrite = get_db_connection(
                    server_name="goblinadmin-write"
                )
            logger.info("Connected to goblinadmin-write")
        except Exception:
            logger.exception("Failed to connect to goblinadmin-write")
            app.state.dbconwrite = None
    except Exception:
        logger.exception("Failed to initialize database connections")
        raise

    try:
        # Application runs here
        yield
    finally:
        # Cleanup - always runs, even if there's an error
        logger.info("Closing database connections...")

        if hasattr(app.state, "dbcon") and app.state.dbcon:
            try:
                app.state.dbcon.engine.dispose()
                logger.info("Disposed madrone connection")
            except Exception:
                logger.exception("Error disposing madrone connection")

        if hasattr(app.state, "dbconwrite") and app.state.dbconwrite:
            try:
                app.state.dbconwrite.engine.dispose()
                logger.info("Disposed madrone-write connection")
            except Exception:
                logger.exception("Error disposing madrone-write connection")


app = Litestar(
    route_handlers=[
        AppController,
        DeveloperController,
        CategoryController,
        RankingsController,
        CompaniesController,
        SdksController,
        KeywordsController,
        ScryController,
        CreativesController,
        ExportsController,
        HealthController,
        V1AppsController,
        V1CompaniesController,
        V1DocsController,
    ],
    cors_config=cors_config,
    openapi_config=OpenAPIConfig(
        title="App Store API",
        version="0.0.1",
        openapi_controller=MyOpenAPIController,
    ),
    lifespan=[db_lifespan],
    logging_config=logging_config,
    after_response=cleanup_expired_responses,
    middleware=[DefineMiddleware(RateLimitMiddleware)],
)
