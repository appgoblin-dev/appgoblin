"""Focused contract and SQL integration tests for inferred scan progress."""

import os
from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock

import pytest
from litestar import Litestar
from litestar.datastructures import State
from litestar.testing import TestClient
from sqlalchemy import create_engine, text

from api_app.controllers.scan_progress import (
    ScanProgressController,
    build_scan_progress,
)
from dbcon.utils import sql

REQUESTED = datetime(2026, 1, 1, tzinfo=UTC)
EMPTY = dict(
    version_code=None,
    version_created_at=None,
    version_updated_at=None,
    version_crawl_result=None,
    has_s3_key=False,
    sdk_at=None,
    sdk_result=None,
    waydroid_at=None,
    waydroid_result=None,
)


@pytest.mark.parametrize(
    ("result", "has_s3_key", "status"),
    [
        (None, False, "pending"),
        (0, False, "unknown"),
        (1, False, "unknown"),
        (2, False, "failure"),
        (3, False, "failure"),
        (4, False, "failure"),
        (5, False, "unknown"),
        (None, True, "success"),
        (2, True, "success"),
    ],
)
def test_download_uses_selected_version(result, has_s3_key, status):
    row = {
        **EMPTY,
        "version_code": "1",
        "version_created_at": REQUESTED,
        "version_updated_at": REQUESTED,
        "version_crawl_result": result,
        "has_s3_key": has_s3_key,
    }
    stage = build_scan_progress("app", REQUESTED, row).stages.download
    assert stage.status == status
    if has_s3_key:
        assert stage.at is None
        assert "time" in stage.note


def test_stage_states_and_import_estimate():
    row = {
        **EMPTY,
        "version_code": "2.1",
        "version_created_at": REQUESTED,
        "version_updated_at": REQUESTED,
        "version_crawl_result": 2,
        "sdk_at": REQUESTED + timedelta(hours=1),
        "sdk_result": 1,
        "waydroid_at": REQUESTED + timedelta(hours=2),
        "waydroid_result": None,
    }
    result = build_scan_progress("app", REQUESTED, row)
    assert result.version_code == "2.1"
    assert result.stages.download.status == "failure"
    assert result.stages.sdk_scan.status == "success"
    assert result.stages.data_import.status == "estimated"
    assert result.stages.data_import.at == REQUESTED + timedelta(hours=25)
    assert "not confirmed" in result.stages.data_import.note
    assert result.stages.waydroid.status == "pending"
    row["sdk_result"] = 0
    row["version_crawl_result"] = 1
    result = build_scan_progress("app", REQUESTED, row)
    assert result.stages.data_import.status == "pending"
    assert result.stages.download.status == "unknown"
    row["has_s3_key"] = True
    assert (
        build_scan_progress("app", REQUESTED, row).stages.download.status == "success"
    )


def test_endpoint_contract_and_validation():
    engine = MagicMock()
    engine.connect.return_value.__enter__.return_value.execute.return_value.mappings.return_value.one.return_value = EMPTY
    app = Litestar(
        route_handlers=[ScanProgressController],
        state=State({"dbcon": MagicMock(engine=engine)}),
    )
    with TestClient(app) as client:
        response = client.get(
            "/analytics/scan-progress",
            params={"store_id": "app", "requested_at": "2026-01-01T00:00:00Z"},
        )
        assert response.status_code == 200
        body = response.json()
        assert body["version_code"] is None
        assert set(body["stages"]) == {
            "request",
            "download",
            "sdk_scan",
            "data_import",
            "waydroid",
        }
        assert body["stages"]["waydroid"]["status"] == "optional"
        assert all(
            set(stage) == {"status", "at", "note"} for stage in body["stages"].values()
        )
        for timestamp in ("2026-01-01T00:00:00", "2999-01-01T00:00:00Z", "invalid"):
            assert (
                client.get(
                    "/analytics/scan-progress",
                    params={"store_id": "app", "requested_at": timestamp},
                ).status_code
                == 400
            )
        assert (
            client.get(
                "/analytics/scan-progress",
                params={"store_id": "", "requested_at": "2026-01-01T00:00:00Z"},
            ).status_code
            == 400
        )


@pytest.mark.skipif(
    not os.getenv("SCAN_PROGRESS_TEST_DATABASE_URL"),
    reason="requires isolated PostgreSQL test database",
)
def test_query_against_postgres():
    engine = create_engine(os.environ["SCAN_PROGRESS_TEST_DATABASE_URL"])
    with engine.begin() as conn:
        conn.execute(text("SET TIME ZONE 'UTC'"))
        conn.execute(text("CREATE SCHEMA logging"))
        for statement in (
            "CREATE TABLE store_apps (id int, store_id text)",
            "CREATE TABLE logging.store_app_downloads (store_app int, updated_at timestamptz, crawl_result int)",
            "CREATE TABLE version_codes (id int, store_app int, version_code text, created_at timestamptz, updated_at timestamptz, crawl_result int)",
            "CREATE TABLE s3_file_keys (version_code_id int)",
            "CREATE TABLE version_code_sdk_scan_results (version_code_id int, scanned_at timestamptz, scan_result int)",
            "CREATE TABLE version_code_api_scan_results (version_code_id int, run_at timestamptz, run_result int)",
            "INSERT INTO store_apps VALUES (1, 'app'), (2, 'other')",
            "INSERT INTO version_codes VALUES (1, 1, 'old', '2025-01-01', '2026-01-06', 1), (2, 1, '2.1', '2026-01-02', '2026-01-02', 1), (3, 2, 'other', '2026-01-02', '2026-01-02', 1), (4, 1, 'later', '2026-01-03', '2026-01-03', 1), (5, 1, 'tie', '2026-01-02', '2026-01-02', 1)",
            "INSERT INTO s3_file_keys VALUES (2)",
            "INSERT INTO logging.store_app_downloads VALUES (1, '2025-01-01', 1), (1, '2026-01-02', 0)",
            "INSERT INTO version_code_sdk_scan_results VALUES (1, '2026-01-07', 1), (2, '2025-01-01', 1), (2, '2026-01-03', 1), (2, '2026-01-04', 0), (4, '2026-01-08', 1)",
            "INSERT INTO version_code_api_scan_results VALUES (2, '2026-01-05', 1), (3, '2026-01-06', 1)",
        ):
            conn.execute(text(statement))
        row = dict(
            conn.execute(
                sql.scan_progress, {"store_id": "app", "requested_at": REQUESTED}
            )
            .mappings()
            .one()
        )
        assert row["version_code"] == "2.1"
        assert row["has_s3_key"] is True
        assert row["version_crawl_result"] == 1
        assert row["version_created_at"] == datetime(2026, 1, 2, tzinfo=UTC)
        assert row["version_updated_at"] == datetime(2026, 1, 2, tzinfo=UTC)
        assert (
            build_scan_progress("app", REQUESTED, row).stages.download.status
            == "success"
        )
        assert row["sdk_result"] == 0
        assert row["waydroid_result"] == 1
        empty = dict(
            conn.execute(
                sql.scan_progress,
                {"store_id": "app", "requested_at": datetime(2026, 2, 1, tzinfo=UTC)},
            )
            .mappings()
            .one()
        )
        assert empty == EMPTY
        missing = dict(
            conn.execute(
                sql.scan_progress, {"store_id": "missing", "requested_at": REQUESTED}
            )
            .mappings()
            .one()
        )
        assert missing == EMPTY
    engine.dispose()
