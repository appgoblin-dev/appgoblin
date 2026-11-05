"""Shared fixtures for backend API tests."""

import shutil
import socket
import subprocess
import time
from unittest.mock import MagicMock

import pytest


@pytest.fixture(scope="session")
def redis_server():
    """Start a disposable loopback-only Redis with persistence disabled."""
    executable = shutil.which("redis-server")
    if executable is None:
        pytest.skip("redis-server is not installed")
    redis = pytest.importorskip("redis")
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
    process = subprocess.Popen(
        [executable, "--bind", "127.0.0.1", "--port", str(port),
         "--save", "", "--appendonly", "no"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    client = redis.Redis(host="127.0.0.1", port=port, socket_connect_timeout=0.2)
    try:
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline:
            if process.poll() is not None:
                pytest.fail("ephemeral redis-server exited before becoming ready")
            try:
                if client.ping() and client.info("server")["process_id"] == process.pid:
                    break
            except redis.exceptions.ConnectionError:
                pass
            time.sleep(0.05)
        else:
            pytest.fail("ephemeral redis-server did not become ready")
        yield port
    finally:
        client.close()
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)


@pytest.fixture
def redis_client(redis_server):
    """Give each test a clean database on the disposable server only."""
    import redis

    client = redis.Redis(host="127.0.0.1", port=redis_server)
    client.flushdb()
    yield client
    client.flushdb()
    client.close()


@pytest.fixture
def isolated_guards(redis_client, monkeypatch):
    from api_app import guards

    limiter = guards._RateLimiter(redis_client)
    quota = guards._DailyQuotaTracker(redis_client)
    monkeypatch.setattr(guards, "_rate_limiter", limiter)
    monkeypatch.setattr(guards, "_daily_quota", quota)
    guards._KEY_CACHE.clear()
    guards._LAST_USED_UPDATES.clear()
    yield
    guards._KEY_CACHE.clear()
    guards._LAST_USED_UPDATES.clear()


@pytest.fixture
def mock_engine():
    """Create a mock SQLAlchemy engine with configurable query results."""

    def _make_engine(row=None):
        """Create a mock engine that returns `row` from fetchone().

        Set row=None to simulate a key not found.
        """
        mock_conn = MagicMock()
        mock_result = MagicMock()
        mock_result.fetchone.return_value = row
        mock_conn.execute.return_value = mock_result

        mock_engine = MagicMock()
        mock_engine.connect.return_value.__enter__ = MagicMock(return_value=mock_conn)
        mock_engine.connect.return_value.__exit__ = MagicMock(return_value=False)
        mock_engine.begin.return_value.__enter__ = MagicMock(return_value=mock_conn)
        mock_engine.begin.return_value.__exit__ = MagicMock(return_value=False)
        return mock_engine

    return _make_engine


@pytest.fixture
def mock_state(mock_engine):
    """Create a mock Litestar app state with a goblinadmin-write connection."""

    def _make_state(row=None):
        engine = mock_engine(row)
        dbcon = MagicMock()
        dbcon.engine = engine
        state = MagicMock()
        state.dbconwrite = dbcon
        return state

    return _make_state
