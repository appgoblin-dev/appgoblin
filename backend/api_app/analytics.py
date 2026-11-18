"""Shared backend analytics helpers for Umami page views."""

from collections.abc import Mapping
from dataclasses import dataclass

import httpx
from litestar import Request
from litestar.background_tasks import BackgroundTask

from config import CONFIG, get_logger

try:
    import umami
except ModuleNotFoundError as exc:
    if exc.name != "umami":
        raise
    umami = None

logger = get_logger(__name__)

REQUEST_ANALYTICS_CONTEXT_KEY = "_analytics_context"
PUBLIC_API_HOSTNAME = "appgoblin.info"


@dataclass(slots=True)
class RequestAnalyticsContext:
    """Per-request analytics context collected during request processing."""

    user_id: int | None = None


def set_request_analytics_context(request: Request, *, user_id: int | None) -> None:
    """Persist analytics metadata on the request scope for later reuse."""
    request.scope[REQUEST_ANALYTICS_CONTEXT_KEY] = RequestAnalyticsContext(
        user_id=user_id
    )


def get_request_analytics_context(request: Request) -> RequestAnalyticsContext:
    """Return analytics metadata stored on the request scope."""
    context = request.scope.get(REQUEST_ANALYTICS_CONTEXT_KEY)
    if isinstance(context, RequestAnalyticsContext):
        return context

    return RequestAnalyticsContext()


def get_forwarded_ip(headers: Mapping[str, str] | None) -> str | None:
    """Return the first forwarded IP, if present."""
    if not headers:
        return None

    forwarded_for = headers.get("X-Forwarded-For") or headers.get("x-forwarded-for")
    if not forwarded_for:
        return None

    client_ip = forwarded_for.split(",", maxsplit=1)[0].strip()
    return client_ip or None


def get_request_ip(request: Request) -> str | None:
    """Resolve the client IP from forwarded headers or the socket peer."""
    forwarded_ip = get_forwarded_ip(request.headers)
    if forwarded_ip:
        return forwarded_ip

    client = request.client
    return client.host if client else None


def log_umami_page(
    *,
    url: str,
    ip: str | None = None,
    user_id: int | None = None,
    page_title: str | None = None,
    hostname: str | None = None,
    referrer: str | None = None,
) -> None:
    """Log a page view to Umami without surfacing analytics failures."""
    if umami is None:
        return

    try:
        normalized_hostname = (
            hostname.strip() if hostname and hostname.strip() else None
        )
        normalized_referrer = referrer.strip() if referrer and referrer.strip() else ""
        normalized_ip = ip.strip() if ip and ip.strip() else None
        normalized_distinct_id = (
            str(user_id).strip()
            if user_id is not None and str(user_id).strip()
            else None
        )

        umami.set_url_base(CONFIG["umami"].get("base_url"))
        umami.set_website_id(CONFIG["umami"].get("site_id"))
        umami.new_page_view(
            page_title=page_title or url,
            url=url,
            hostname=normalized_hostname,
            referrer=normalized_referrer,
            ip_address=normalized_ip,
            distinct_id=normalized_distinct_id,
        )
        logger.info("Logged Umami page view for %s", url)
    except httpx.HTTPStatusError as exc:
        response_text = exc.response.text.strip()
        logger.exception(
            "Error logging Umami page view for %s: %s",
            url,
            response_text or exc,
        )
    except Exception:
        logger.exception("Error logging Umami page view for %s", url)


def build_request_page_view_task(
    request: Request,
    *,
    url: str,
    page_title: str | None = None,
    hostname: str | None = None,
    referrer: str | None = None,
) -> BackgroundTask:
    """Return a background task that logs the current request to Umami."""
    context = get_request_analytics_context(request)
    return BackgroundTask(
        log_umami_page,
        url=url,
        ip=get_request_ip(request),
        user_id=context.user_id,
        page_title=page_title,
        hostname=hostname,
        referrer=referrer,
    )
