"""Behavioral tests for SDK match queries."""

import sqlite3
from pathlib import Path
from unittest.mock import patch

import pandas as pd
import pytest
from litestar import Litestar
from litestar.testing import TestClient

from api_app.controllers.sdks import SdksController


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


@pytest.mark.parametrize("pattern", ["com.example", "COM.EXAMPLE", "missing"])
def test_pattern_preview_count_matches_unlimited_export(database, pattern):
    database.executescript("""
        CREATE TABLE version_strings (id INT, xml_path TEXT, value_name TEXT);
        CREATE TABLE adtech.app_sdk_strings (store_app INT, string_id INT, sdk_id INT);
        CREATE TABLE adtech.sdk_string_stats (string_id INT, sdk_id INT, app_count INT);
        INSERT INTO version_strings VALUES
            (1, 'manifest', 'com.example.sdk'),
            (2, 'file', 'com.example.adapter'),
            (3, 'file', 'other.sdk');
        INSERT INTO adtech.app_sdk_strings VALUES
            (1, 1, 10), (1, 2, 10), (2, 3, 10), (99, 1, 20);
    """)
    database.executemany(
        "INSERT INTO adtech.app_sdk_strings VALUES (?, 1, 10)", [(1,)] * 105
    )
    database.execute("""
        INSERT INTO adtech.sdk_string_stats
        SELECT string_id, sdk_id, COUNT(*) FROM adtech.app_sdk_strings
        GROUP BY string_id, sdk_id
    """)
    preview = query(database, "query_sdk_pattern.sql", value_pattern=pattern)
    export = query(database, "query_sdk_pattern_export.sql", value_pattern=pattern)
    count = query(database, "query_sdk_pattern_count.sql", value_pattern=pattern)
    assert len(preview) == min(100, len(export))
    assert count == [{"total_count": len(export)}]
    assert len(export) == (0 if pattern == "missing" else 108)
    assert all("total_count" not in row for row in preview)


@pytest.mark.parametrize("rows, total", [([{"store_id": "app.one"}], 108), ([], 7), ([], 0)])
def test_pattern_endpoint_returns_stats_count_independently_of_preview(rows, total):
    frame = pd.DataFrame(rows, columns=["store_id"])
    app = Litestar(route_handlers=[SdksController])
    with (
        patch("api_app.controllers.sdks.get_sdk_pattern", return_value=frame),
        patch("api_app.controllers.sdks.get_sdk_pattern_count", return_value=total) as count,
        TestClient(app=app, raise_server_exceptions=False) as client,
    ):
        response = client.get("/api/sdks/com.example")
    assert response.status_code == 200
    assert count.call_args.args[1] == "com.example"
    assert response.json() == {
        "apps": [{"store_id": "app.one"}] if rows else [],
        "total_count": total,
    }


def test_pattern_company_query_returns_sdk_slug(database):
    database.executescript("""
        DROP TABLE frontend.companies_sdks_overview;
        CREATE TABLE frontend.companies_sdks_overview (
            company_name TEXT, company_domain TEXT, parent_company_domain TEXT,
            sdk_name TEXT, sdk_slug TEXT, pattern_type TEXT, pattern_value TEXT,
            app_count INT, parent_company_name TEXT
        );
        INSERT INTO frontend.companies_sdks_overview VALUES
            ('Adjust', 'adjust.com', NULL, 'Adjust SDK', 'adjust-sdk',
             'package', 'com.adjust', 10, NULL);
    """)
    # SQLite uses LIKE in place of PostgreSQL's case-insensitive ILIKE.
    sql = (SQL_DIR / "query_sdk_pattern_companies.sql").read_text(encoding="utf-8")
    rows = [
        dict(row)
        for row in database.execute(
            sql.replace("ILIKE", "LIKE"), {"value_pattern": "com.adjust"}
        )
    ]
    assert [(row["sdk_name"], row["sdk_slug"]) for row in rows] == [
        ("Adjust SDK", "adjust-sdk")
    ]


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
