"""Behavioral tests for SDK match queries."""

import sqlite3
from pathlib import Path

import pytest


SQL_DIR = Path(__file__).resolve().parents[1] / "dbcon" / "sql"


@pytest.fixture
def database():
    db = sqlite3.connect(":memory:")
    db.row_factory = sqlite3.Row
    db.create_function("concat", -1, lambda *args: "".join(str(x or "") for x in args))
    db.executescript("""
        ATTACH DATABASE ':memory:' AS adtech;
        ATTACH DATABASE ':memory:' AS frontend;
        CREATE TABLE adtech.app_sdks (store_app INT, sdk_id INT, version_code_id INT, version_code_created_at TEXT);
        CREATE TABLE adtech.app_sdks_latest (store_app INT, sdk_id INT);
        CREATE TABLE adtech.sdks (id INT, sdk_name TEXT, company_id INT);
        CREATE TABLE adtech.companies (id INT, name TEXT, domain_id INT);
        CREATE TABLE domains (id INT, domain_name TEXT);
        CREATE TABLE frontend.store_apps_overview (
            id INT, store INT, store_id TEXT, name TEXT, category TEXT, is_removed INT,
            developer_name TEXT, installs INT, installs_sum_4w INT, icon_64 TEXT
        );
        CREATE TABLE frontend.companies_sdks_overview (sdk_id INT, company_domain TEXT, sdk_slug TEXT);
        CREATE TABLE version_codes (id INT, store_app INT, version_code TEXT, created_at TEXT);
        CREATE TABLE version_code_sdk_scan_results (version_code_id INT, scan_result INT, scanned_at TEXT);
        INSERT INTO frontend.store_apps_overview VALUES
            (1, 1, 'app.one', 'One', 'game', 0, 'Dev', 100, 10, 'icon'),
            (2, 1, 'app.two', 'Two', 'game', 0, 'Dev', 200, 20, 'icon');
        INSERT INTO adtech.sdks VALUES (10, 'SDK A', 1), (20, 'SDK B', 1);
        INSERT INTO adtech.companies VALUES (1, 'Company', 1);
        INSERT INTO domains VALUES (1, 'example.com');
        INSERT INTO frontend.companies_sdks_overview VALUES
            (10, 'example.com', 'sdk-a'), (20, 'example.com', 'sdk-b');
        INSERT INTO adtech.app_sdks_latest VALUES (1, 10), (2, 20);
        INSERT INTO adtech.app_sdks VALUES (1, 20, 1, '2026-01-01');
    """)
    yield db
    db.close()


def query(db, filename, **params):
    sql = (SQL_DIR / filename).read_text(encoding="utf-8")
    return [dict(row) for row in db.execute(sql, params)]


@pytest.mark.parametrize(
    "filename", ["query_sdk.sql", "query_sdk_latest.sql", "query_sdk_export_latest.sql"]
)
def test_latest_sdk_queries_filter_to_requested_sdk(database, filename):
    rows = query(database, filename, sdk_id=10, mylimit=10)
    assert [(row["sdk_name"], row["store_id"]) for row in rows] == [
        ("SDK A", "app.one")
    ]
    assert query(database, filename, sdk_id=99, mylimit=10) == []


def test_mapped_sdks_excludes_historical_matches(database):
    rows = query(database, "query_app_mapped_sdks.sql", store_id="app.one")
    assert rows == [{"company_domain": "example.com", "sdk_slug": "sdk-a"}]


def test_sdk_history_treats_successful_empty_scan_as_removal(database):
    database.executescript("""
        DELETE FROM adtech.app_sdks;
        INSERT INTO version_codes VALUES
            (1, 1, '1', '2026-01-01'),
            (2, 1, '2', '2026-01-02'),
            (3, 1, '3', '2026-01-03'),
            (4, 1, '4', '2026-01-04'),
            (5, 1, '5', '2026-01-05');
        INSERT INTO version_code_sdk_scan_results VALUES
            (1, 1, '2026-01-01'), (2, 0, '2026-01-02'),
            (3, 1, '2026-01-03'), (4, 1, '2026-01-04'),
            (5, 1, '2026-01-05');
        INSERT INTO adtech.app_sdks VALUES
            (1, 10, 1, '2026-01-01'), (1, 10, 5, '2026-01-05');
    """)
    rows = query(database, "query_app_sdk_history.sql", store_id="app.one")
    assert [(row["version_code"], row["status"]) for row in rows] == [
        ("5", "added"),
        ("4", None),
        ("3", "removed"),
        ("2", None),
        ("1", "added_initial"),
    ]
    assert (
        next(row for row in rows if row["version_code"] == "2")["sdk_scan_result"]
        is None
    )
