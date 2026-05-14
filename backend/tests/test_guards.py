"""Tests for api_app.guards — rate limiting, daily quota, and key validation."""

import hashlib
import time
from unittest.mock import MagicMock

import pytest

from api_app.guards import (
    REQUIRED_PRICE_MAPPED_TIERS,
    TIER_LIMITS,
    ApiKeyContext,
    TierLimits,
    _DailyQuotaTracker,
    _RateLimiter,
    _resolve_tier,
    configure_tier_mapping,
    get_tier_limits,
    validate_tier_mapping_config,
    validate_api_key,
)

# ---------------------------------------------------------------------------
# Tier configuration
# ---------------------------------------------------------------------------


class TestTierConfig:
    def test_all_tiers_have_limits(self):
        for tier in ("free", "premium_access", "b2b_sdk", "b2b_appads", "b2b_premium"):
            assert tier in TIER_LIMITS

    def test_tiers_are_frozen(self):
        limits = TIER_LIMITS["free"]
        with pytest.raises(AttributeError):
            limits.requests_per_minute = 999

    def test_get_tier_limits_known(self):
        limits = get_tier_limits("b2b_premium")
        assert limits.requests_per_minute == 10_000
        assert limits.requests_per_day == 500_000

    def test_get_tier_limits_unknown_defaults_to_free(self):
        limits = get_tier_limits("nonexistent_tier")
        assert limits == TIER_LIMITS["free"]

    def test_free_is_most_restrictive(self):
        free = TIER_LIMITS["free"]
        for tier, limits in TIER_LIMITS.items():
            if tier == "free":
                continue
            assert limits.requests_per_minute >= free.requests_per_minute
            assert limits.requests_per_day >= free.requests_per_day

    def test_daily_greater_than_minute(self):
        for tier, limits in TIER_LIMITS.items():
            assert limits.requests_per_day > limits.requests_per_minute, (
                f"{tier}: daily ({limits.requests_per_day}) must exceed "
                f"minute ({limits.requests_per_minute})"
            )


class TestConfigureTierMapping:
    def test_maps_price_ids(self, monkeypatch):
        from api_app import guards as guards_mod

        monkeypatch.setattr(guards_mod, "PRICE_ID_TO_TIER", {})
        configure_tier_mapping({"price_abc": "b2b_premium", "price_def": "free"})
        assert guards_mod.PRICE_ID_TO_TIER == {
            "price_abc": "b2b_premium",
            "price_def": "free",
        }


class TestValidateTierMappingConfig:
    def test_missing_section_raises(self):
        with pytest.raises(ValueError, match="Missing required \[tier_prices\]"):
            validate_tier_mapping_config(None)

    def test_missing_required_tiers_raises(self):
        with pytest.raises(ValueError, match="Missing required tier mapping"):
            validate_tier_mapping_config({"price_sdk": "b2b_sdk"})

    def test_unknown_tier_label_raises(self):
        with pytest.raises(ValueError, match="Unknown tier label"):
            validate_tier_mapping_config(
                {
                    "price_unknown": "enterprise",
                    "price_app_dev": "premium_access",
                    "price_sdk": "b2b_sdk",
                    "price_appads": "b2b_appads",
                    "price_premium": "b2b_premium",
                }
            )

    def test_complete_paid_tier_mapping_passes(self):
        price_map = {
            f"price_{tier}": tier for tier in sorted(REQUIRED_PRICE_MAPPED_TIERS)
        }

        validate_tier_mapping_config(price_map)


class TestResolveTier:
    def test_accepts_direct_tier_label(self, monkeypatch):
        from api_app import guards as guards_mod

        monkeypatch.setattr(guards_mod, "PRICE_ID_TO_TIER", {})

        assert _resolve_tier("b2b_sdk") == "b2b_sdk"

    def test_maps_known_price_id(self, monkeypatch):
        from api_app import guards as guards_mod

        monkeypatch.setattr(guards_mod, "PRICE_ID_TO_TIER", {"price_sdk": "b2b_sdk"})

        assert _resolve_tier("price_sdk") == "b2b_sdk"

    def test_unknown_price_id_defaults_to_free(self, monkeypatch):
        from api_app import guards as guards_mod

        monkeypatch.setattr(guards_mod, "PRICE_ID_TO_TIER", {})

        assert _resolve_tier("price_unknown") == "free"


# ---------------------------------------------------------------------------
# Rate limiter (per-minute token bucket)
# ---------------------------------------------------------------------------


class TestRateLimiter:
    def test_allows_within_limit(self):
        limiter = _RateLimiter()
        for _ in range(10):
            allowed, limit, remaining, retry = limiter.check("key1", 30)
            assert allowed is True
            assert limit == 30
        assert remaining == 20  # 30 - 10

    def test_blocks_over_limit(self):
        limiter = _RateLimiter()
        for _ in range(30):
            allowed, _, _, _ = limiter.check("key1", 30)
            assert allowed is True

        # 31st request should be blocked
        allowed, limit, remaining, retry = limiter.check("key1", 30)
        assert allowed is False
        assert remaining == 0
        assert retry > 0

    def test_independent_keys(self):
        limiter = _RateLimiter()
        for _ in range(30):
            limiter.check("key1", 30)

        # key2 should not be affected
        allowed, _, remaining, _ = limiter.check("key2", 30)
        assert allowed is True
        assert remaining == 29

    def test_refills_over_time(self, monkeypatch):
        limiter = _RateLimiter()
        base_time = time.monotonic()
        monkeypatch.setattr(time, "monotonic", lambda: base_time)

        # Exhaust tokens
        for _ in range(30):
            limiter.check("key1", 30)

        # Advance time by 60 seconds (full refill)
        monkeypatch.setattr(time, "monotonic", lambda: base_time + 60)
        allowed, limit, remaining, _ = limiter.check("key1", 30)
        assert allowed is True
        assert limit == 30
        # Bucket refilled to 30, we consumed 1, so remaining = 29
        assert remaining == 29

    def test_different_rate_limits(self):
        limiter = _RateLimiter()
        # 30/min key
        for _ in range(30):
            limiter.check("free_key", 30)
        allowed, _, _, _ = limiter.check("free_key", 30)
        assert allowed is False

        # 10000/min key — still has plenty
        allowed, limit, _, _ = limiter.check("b2b_key", 10_000)
        assert allowed is True
        assert limit == 10_000


# ---------------------------------------------------------------------------
# Daily quota tracker
# ---------------------------------------------------------------------------


class TestDailyQuotaTracker:
    def test_counts_requests(self):
        tracker = _DailyQuotaTracker()
        for i in range(100):
            allowed, limit, remaining = tracker.check("key1", 1000)
            assert allowed is True
            assert remaining == 1000 - i - 1

    def test_blocks_at_limit(self):
        tracker = _DailyQuotaTracker()
        for _ in range(1000):
            allowed, _, _ = tracker.check("key1", 1000)
            assert allowed is True

        allowed, limit, remaining = tracker.check("key1", 1000)
        assert allowed is False
        assert remaining == 0

    def test_independent_keys(self):
        tracker = _DailyQuotaTracker()
        for _ in range(1000):
            tracker.check("key1", 1000)

        # key2 should be fresh
        allowed, limit, remaining = tracker.check("key2", 1000)
        assert allowed is True
        assert remaining == 999

    def test_resets_at_midnight(self):
        tracker = _DailyQuotaTracker()

        # Force "today" to 2026-03-31
        tracker._today_utc = lambda: "2026-03-31"

        for _ in range(1000):
            tracker.check("key1", 1000)

        allowed, _, _ = tracker.check("key1", 1000)
        assert allowed is False

        # Advance to next day
        tracker._today_utc = lambda: "2026-04-01"

        allowed, limit, remaining = tracker.check("key1", 1000)
        assert allowed is True
        assert remaining == 999


# ---------------------------------------------------------------------------
# API key validation (validate_api_key)
# ---------------------------------------------------------------------------


def _make_request(api_key: str | None = None):
    """Create a mock Litestar Request with an X-API-Key header."""
    request = MagicMock()
    request.headers = {}
    if api_key:
        request.headers["x-api-key"] = api_key
    request.scope = {}
    return request


def _make_db_row(user_id: int = 1, price_id: str | None = None):
    """Create a mock DB row as returned by _query_key."""
    row = MagicMock()
    row.user_id = user_id
    row.price_id = price_id
    return row


class TestValidateApiKey:
    def test_missing_header_raises_401(self, mock_state):
        from litestar.exceptions import NotAuthorizedException

        request = _make_request(api_key=None)
        state = mock_state()

        with pytest.raises(NotAuthorizedException, match="Missing X-API-Key"):
            validate_api_key(request, state)

    def test_invalid_key_raises_401(self, mock_state):
        from litestar.exceptions import NotAuthorizedException

        request = _make_request(api_key="ag_badkey")
        # DB returns None (key not found)
        state = mock_state(row=None)

        with pytest.raises(NotAuthorizedException, match="Invalid or expired"):
            validate_api_key(request, state)

    def test_valid_key_returns_context(self, mock_state):
        row = _make_db_row(user_id=42, price_id=None)
        request = _make_request(api_key="ag_testkey123")
        state = mock_state(row=row)

        ctx = validate_api_key(request, state)
        assert ctx.user_id == 42
        assert ctx.tier == "free"  # no price_id maps to free
        assert ctx.limits.requests_per_minute == 30
        assert ctx.limits.requests_per_day == 1000

    def test_paid_tier_lookup(self, mock_state, monkeypatch):
        from api_app import guards as guards_mod

        monkeypatch.setattr(
            guards_mod, "PRICE_ID_TO_TIER", {"price_premium": "b2b_premium"}
        )
        row = _make_db_row(user_id=7, price_id="price_premium")
        request = _make_request(api_key="ag_premiumkey")
        state = mock_state(row=row)

        ctx = validate_api_key(request, state)
        assert ctx.tier == "b2b_premium"
        assert ctx.limits.requests_per_minute == 10_000

    def test_direct_tier_label_lookup(self, mock_state, monkeypatch):
        from api_app import guards as guards_mod

        monkeypatch.setattr(guards_mod, "PRICE_ID_TO_TIER", {})
        row = _make_db_row(user_id=7, price_id="b2b_sdk")
        request = _make_request(api_key="ag_b2bsdk")
        state = mock_state(row=row)

        ctx = validate_api_key(request, state)
        assert ctx.tier == "b2b_sdk"
        assert ctx.limits.requests_per_minute == 2_000

    def test_no_goblinadmin_connection_raises(self):
        from litestar.exceptions import NotAuthorizedException

        request = _make_request(api_key="ag_somekey")
        state = MagicMock()
        state.dbconwrite = None

        with pytest.raises(NotAuthorizedException, match="unavailable"):
            validate_api_key(request, state)

    def test_daily_quota_exceeded_raises_429(self, mock_state):
        from api_app import guards as g_mod
        from litestar.exceptions import TooManyRequestsException

        row = _make_db_row(user_id=1, price_id=None)
        state = mock_state(row=row)
        raw_key = "ag_dailytest429"
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()

        # Exhaust daily quota directly on the tracker (free = 1000/day)
        # using the hash because validate_api_key hashes the raw key
        for _ in range(1000):
            g_mod._daily_quota.check(key_hash, 1000)

        req = _make_request(api_key=raw_key)
        with pytest.raises(TooManyRequestsException, match="Daily request quota"):
            validate_api_key(req, state)

    def test_per_minute_limit_raises_429(self, mock_state):
        from litestar.exceptions import TooManyRequestsException

        row = _make_db_row(user_id=1, price_id=None)
        state = mock_state(row=row)

        # Use a different key so daily quota doesn't interfere
        for _ in range(30):  # free = 30/min
            req = _make_request(api_key="ag_minutetest")
            validate_api_key(req, state)

        req = _make_request(api_key="ag_minutetest")
        with pytest.raises(TooManyRequestsException, match="Rate limit exceeded"):
            validate_api_key(req, state)

    def test_scope_receives_rate_limit_info(self, mock_state):
        row = _make_db_row(user_id=1, price_id=None)
        request = _make_request(api_key="ag_scopetest")
        state = mock_state(row=row)

        validate_api_key(request, state)

        info = request.scope["_rate_limit_info"]
        assert info["minute_limit"] == 30
        assert info["minute_remaining"] == 29
        assert info["daily_limit"] == 1000
        assert info["daily_remaining"] == 999
