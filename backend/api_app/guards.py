"""API key authentication and rate limiting for the public API."""

import hashlib
import time
from dataclasses import dataclass
from threading import Lock

from litestar import Request
from litestar.exceptions import NotAuthorizedException, TooManyRequestsException
from sqlalchemy import Engine, text

from config import get_logger

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Tier configuration
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class TierLimits:
    """Rate limit configuration for a subscription tier."""

    requests_per_minute: int
    requests_per_day: int


TIER_LIMITS: dict[str, TierLimits] = {
    "free": TierLimits(requests_per_minute=30, requests_per_day=1_000),
    "b2b_sdk": TierLimits(requests_per_minute=2_000, requests_per_day=100_000),
    "b2b_appads": TierLimits(requests_per_minute=2_000, requests_per_day=100_000),
    "b2b_premium": TierLimits(requests_per_minute=10_000, requests_per_day=500_000),
}

REQUIRED_PRICE_MAPPED_TIERS = frozenset(tier for tier in TIER_LIMITS if tier != "free")

PRICE_ID_TO_TIER: dict[str, str] = {}


def validate_tier_mapping_config(price_map: dict[str, str] | None) -> None:
    """Validate the required Stripe price to tier mapping config."""
    if not price_map:
        raise ValueError(
            "Missing required [tier_prices] section in config.toml. "
            f"Expected mappings for: {', '.join(sorted(REQUIRED_PRICE_MAPPED_TIERS))}"
        )

    configured_tiers = set(price_map.values())
    unknown_tiers = sorted(configured_tiers - set(TIER_LIMITS))
    if unknown_tiers:
        raise ValueError(
            "Unknown tier label(s) in [tier_prices]: " + ", ".join(unknown_tiers)
        )

    missing_tiers = sorted(REQUIRED_PRICE_MAPPED_TIERS - configured_tiers)
    if missing_tiers:
        raise ValueError(
            "Missing required tier mapping(s) in [tier_prices]: "
            + ", ".join(missing_tiers)
        )


def configure_tier_mapping(price_map: dict[str, str]) -> None:
    """Call at startup with {stripe_price_id: tier_label} mapping.

    This is populated from the SvelteKit stripe.ts constant values so we
    don't duplicate them.  The keys come from ``STRIPE_PRICES`` in
    ``frontend/src/lib/server/stripe.ts``.
    """
    PRICE_ID_TO_TIER.update(price_map)


def get_tier_limits(tier: str) -> TierLimits:
    """Get limits for a tier, defaulting to free."""
    return TIER_LIMITS.get(tier, TIER_LIMITS["free"])


def _resolve_tier(price_id: str | None) -> str:
    """Resolve a subscription price identifier to a configured tier label."""
    if not price_id:
        return "free"

    if price_id in TIER_LIMITS:
        return price_id

    mapped_tier = PRICE_ID_TO_TIER.get(price_id)
    if mapped_tier in TIER_LIMITS:
        return mapped_tier

    logger.warning(
        "Unknown subscription price id %r for API rate limiting; defaulting to free",
        price_id,
    )
    return "free"


# ---------------------------------------------------------------------------
# In-memory rate limiter (refilling token bucket per key)
# ---------------------------------------------------------------------------


@dataclass
class _TokenBucket:
    tokens: float
    last_refill: float
    rate_per_second: float


class _RateLimiter:
    """Thread-safe refilling token bucket keyed by API key hash."""

    def __init__(self) -> None:
        self._buckets: dict[str, _TokenBucket] = {}
        self._lock = Lock()

    def check(self, key_hash: str, rate_per_minute: int) -> tuple[bool, int, int, int]:
        """Check and consume one token.

        Returns
        -------
        (allowed, limit, remaining, retry_after_seconds)
        """
        rate_per_second = rate_per_minute / 60.0
        now = time.monotonic()

        with self._lock:
            bucket = self._buckets.get(key_hash)
            if bucket is None or bucket.rate_per_second != rate_per_second:
                bucket = _TokenBucket(
                    tokens=float(rate_per_minute),
                    last_refill=now,
                    rate_per_second=rate_per_second,
                )
                self._buckets[key_hash] = bucket

            elapsed = now - bucket.last_refill
            bucket.tokens = min(
                float(rate_per_minute), bucket.tokens + elapsed * rate_per_second
            )
            bucket.last_refill = now

            if bucket.tokens >= 1.0:
                bucket.tokens -= 1.0
                remaining = int(bucket.tokens)
                return True, rate_per_minute, remaining, 0

            retry_after = int((1.0 - bucket.tokens) / rate_per_second) + 1
            return False, rate_per_minute, 0, retry_after


_rate_limiter = _RateLimiter()


# ---------------------------------------------------------------------------
# Daily quota tracker (in-memory, resets at UTC midnight)
# ---------------------------------------------------------------------------


@dataclass
class _DailyQuota:
    date: str  # YYYY-MM-DD
    count: int


class _DailyQuotaTracker:
    """Thread-safe daily request counter keyed by API key hash."""

    def __init__(self) -> None:
        self._counters: dict[str, _DailyQuota] = {}
        self._lock = Lock()

    def _today_utc(self) -> str:
        """Return today's date as YYYY-MM-DD (UTC)."""
        from datetime import UTC, datetime

        return datetime.now(UTC).strftime("%Y-%m-%d")

    def check(self, key_hash: str, daily_limit: int) -> tuple[bool, int, int]:
        """Check and consume one request from the daily quota.

        Returns
        -------
        (allowed, limit, remaining)
        """
        today = self._today_utc()

        with self._lock:
            counter = self._counters.get(key_hash)
            if counter is None or counter.date != today:
                counter = _DailyQuota(date=today, count=0)
                self._counters[key_hash] = counter

            counter.count += 1

            if counter.count <= daily_limit:
                return True, daily_limit, daily_limit - counter.count

            return False, daily_limit, 0


_daily_quota = _DailyQuotaTracker()


# ---------------------------------------------------------------------------
# Key cache (avoid hitting DB on every request)
# ---------------------------------------------------------------------------


@dataclass
class _CachedKey:
    user_id: int
    tier: str
    expires_at: float  # monotonic time when this cache entry expires


_KEY_CACHE: dict[str, _CachedKey] = {}
_KEY_CACHE_TTL = 300  # 5 minutes
_LAST_USED_UPDATES: dict[str, float] = {}  # key_hash -> monotonic timestamp


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------


@dataclass
class ApiKeyContext:
    """Returned by ``validate_api_key``."""

    user_id: int
    tier: str
    key_hash: str
    limits: TierLimits


def _query_key(engine: Engine, key_hash: str) -> _CachedKey | None:
    """Look up an API key and its owner's subscription tier."""
    query = text("""
        SELECT ak.user_id,
               COALESCE(s.provider_price_id, 'free') AS price_id
        FROM public.api_keys ak
        JOIN public.users u ON u.id = ak.user_id
        LEFT JOIN LATERAL (
            SELECT provider_price_id
            FROM public.subscriptions sub
            WHERE sub.user_id = ak.user_id
              AND sub.status IN ('active', 'trialing')
            ORDER BY sub.created_at DESC
            LIMIT 1
        ) s ON TRUE
        WHERE ak.key_hash = :key_hash
          AND ak.is_active = true
          AND (ak.expires_at IS NULL OR ak.expires_at > now())
        """)

    with engine.connect() as conn:
        row = conn.execute(query, {"key_hash": key_hash}).fetchone()

    if row is None:
        return None

    price_id = row.price_id or "free"
    tier = _resolve_tier(price_id)

    return _CachedKey(
        user_id=row.user_id,
        tier=tier,
        expires_at=time.monotonic() + _KEY_CACHE_TTL,
    )


def _update_last_used(engine: Engine, key_hash: str) -> None:
    """Throttled update of last_used_at (max once per 60 seconds per key)."""
    now = time.monotonic()
    last = _LAST_USED_UPDATES.get(key_hash, 0.0)
    if now - last < 60:
        return
    _LAST_USED_UPDATES[key_hash] = now
    stmt = text(
        "UPDATE public.api_keys SET last_used_at = now() WHERE key_hash = :key_hash"
    )
    try:
        with engine.begin() as conn:
            conn.execute(stmt, {"key_hash": key_hash})
    except Exception:
        logger.debug("Failed to update last_used_at for API key")


def _evict_expired_cache() -> None:
    """Remove expired entries from the key and last-used caches."""
    now = time.monotonic()
    expired = [k for k, v in _KEY_CACHE.items() if now >= v.expires_at]
    for k in expired:
        del _KEY_CACHE[k]
    # Clean last-used updates older than 1 hour
    stale = [k for k, v in _LAST_USED_UPDATES.items() if now - v > 3600]
    for k in stale:
        del _LAST_USED_UPDATES[k]


def validate_api_key(request: Request, state) -> ApiKeyContext:
    """Validate an API key from the X-API-Key header.

    Must be called from a guard or middleware where ``state`` is the
    Litestar application state (``app.state``).
    """
    raw_key = request.headers.get("x-api-key")
    if not raw_key:
        raise NotAuthorizedException(detail="Missing X-API-Key header")

    key_hash = hashlib.sha256(raw_key.encode()).hexdigest()

    # Resolve tier and limits
    cached = _KEY_CACHE.get(key_hash)
    if cached is not None and time.monotonic() < cached.expires_at:
        tier = cached.tier
        user_id = cached.user_id
    else:
        engine = state.dbconwrite.engine if state.dbconwrite else None
        if engine is None:
            logger.error("No goblinadmin connection available for API key validation")
            raise NotAuthorizedException(detail="API key validation unavailable")

        # Opportunistically evict expired cache entries on cache miss
        if len(_KEY_CACHE) > 1000:
            _evict_expired_cache()

        result = _query_key(engine, key_hash)
        if result is None:
            raise NotAuthorizedException(detail="Invalid or expired API key")

        _KEY_CACHE[key_hash] = result
        tier = result.tier
        user_id = result.user_id

    limits = get_tier_limits(tier)

    # --- Daily quota (checked first — no point allowing burst if over daily cap) ---
    daily_ok, daily_limit, daily_remaining = _daily_quota.check(
        key_hash, limits.requests_per_day
    )

    request.scope["_rate_limit_info"] = {
        "minute_limit": limits.requests_per_minute,
        "minute_remaining": 0,  # filled below
        "daily_limit": daily_limit,
        "daily_remaining": daily_remaining,
        "retry_after": 0,
    }

    if not daily_ok:
        request.scope["_rate_limit_info"]["minute_remaining"] = 0
        raise TooManyRequestsException(
            detail="Daily request quota exceeded",
            headers={
                "X-RateLimit-Limit": str(daily_limit),
                "X-RateLimit-Remaining": "0",
                "X-RateLimit-Policy": f"{daily_limit};w=86400",
            },
        )

    # --- Per-minute burst limit ---
    (
        minute_ok,
        minute_limit,
        minute_remaining,
        retry_after,
    ) = _rate_limiter.check(key_hash, limits.requests_per_minute)

    request.scope["_rate_limit_info"] = {
        "minute_limit": minute_limit,
        "minute_remaining": minute_remaining,
        "daily_limit": daily_limit,
        "daily_remaining": daily_remaining,
        "retry_after": retry_after,
    }

    if not minute_ok:
        raise TooManyRequestsException(
            detail="Rate limit exceeded",
            headers={
                "Retry-After": str(retry_after),
                "X-RateLimit-Limit": str(minute_limit),
                "X-RateLimit-Remaining": "0",
            },
        )

    # Throttled last_used update
    if state.dbconwrite:
        _update_last_used(state.dbconwrite.engine, key_hash)

    return ApiKeyContext(
        user_id=user_id,
        tier=tier,
        key_hash=key_hash,
        limits=limits,
    )
