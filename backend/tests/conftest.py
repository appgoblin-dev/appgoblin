"""Shared fixtures for backend API tests."""

from unittest.mock import MagicMock

import pytest


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
