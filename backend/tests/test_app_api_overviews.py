"""Tests for the data-flow overview builders used by /apps/{id}/apis."""

from unittest.mock import MagicMock

import pandas as pd
import pytest

from api_app.controllers.apps import (
    build_category_overviews,
    build_creative_overviews,
    build_scan_diff,
    build_scan_overviews,
)

COLUMNS = [
    "called_at",
    "run_id",
    "run_at",
    "version_code",
    "company_name",
    "company_domain",
    "company_logo_url",
    "tld_url",
    "url",
    "country",
    "servers",
    "request_mime_type",
    "response_mime_type",
    "creative_md5_hash",
    "creative_file_extension",
    "advertiser_store_id",
    "advertiser_icon_url_100",
]


def make_row(**overrides) -> dict:
    """Build a single API call row with sensible defaults."""
    row = dict.fromkeys(COLUMNS)
    row.update(
        called_at=pd.Timestamp("2026-01-01T10:00:00Z"),
        run_id=1,
        run_at=pd.Timestamp("2026-01-01T10:00:00Z"),
        version_code="1.0",
        tld_url="adjust.com",
        url="adjust.com/x",
        country="US",
        servers="aws",
        request_mime_type="application/json",
        response_mime_type="application/json",
    )
    row.update(overrides)
    return row


def make_df(rows: list[dict]) -> pd.DataFrame:
    """Build a DataFrame with the API call columns."""
    return pd.DataFrame(rows, columns=COLUMNS)


def make_state(categories: list[dict]) -> MagicMock:
    """Build a fake Litestar state with preloaded company categories."""
    state = MagicMock()
    state.static_data.company_categories = pd.DataFrame(
        categories, columns=["company_type", "company_type_slug", "company_domain"]
    )
    return state


def test_scan_overviews_are_newest_first():
    df = make_df(
        [
            make_row(run_id=1, run_at=pd.Timestamp("2026-01-01T10:00:00Z")),
            make_row(run_id=2, run_at=pd.Timestamp("2026-03-01T10:00:00Z"), tld_url="braze.com"),
            make_row(run_id=2, run_at=pd.Timestamp("2026-03-01T10:00:00Z"), tld_url="braze.com"),
        ]
    )

    scans = build_scan_overviews(df)

    assert [scan["run_id"] for scan in scans] == [2, 1]
    assert scans[0]["call_count"] == 2
    assert scans[0]["domain_count"] == 1
    assert scans[0]["run_at"] == "2026-03-01T10:00:00+00:00"


def test_scan_overviews_handles_empty_frame():
    assert build_scan_overviews(make_df([])) == []


def test_scan_diff_classifies_new_removed_and_unchanged():
    df = make_df(
        [
            make_row(run_id=1, company_name="Adjust", company_domain="adjust.com"),
            make_row(run_id=1, company_name="Braze", company_domain="braze.com"),
            make_row(run_id=2, company_name="Adjust", company_domain="adjust.com"),
            make_row(
                run_id=2,
                run_at=pd.Timestamp("2026-03-01T10:00:00Z"),
                company_name="Branch",
                company_domain="branch.io",
                tld_url="branch.io",
            ),
        ]
    )

    diff = build_scan_diff(df)

    assert diff is not None
    assert diff["previous_run_id"] == 1
    assert diff["latest_run_id"] == 2
    statuses = {row["vendor_key"]: row["status"] for row in diff["rows"]}
    assert statuses == {
        "adjust.com": "unchanged",
        "braze.com": "removed",
        "branch.io": "new",
    }
    assert diff["new_count"] == 1
    assert diff["removed_count"] == 1
    assert diff["unchanged_count"] == 1
    # New vendors are listed first so changes are easy to spot.
    assert diff["rows"][0]["vendor_key"] == "branch.io"


def test_scan_diff_requires_two_scans():
    df = make_df([make_row(run_id=1)])
    assert build_scan_diff(df) is None


def test_scan_diff_falls_back_to_tld_for_unmapped_domains():
    df = make_df(
        [
            make_row(run_id=1, tld_url="unknown.example", url="unknown.example/a"),
            make_row(
                run_id=2,
                run_at=pd.Timestamp("2026-03-01T10:00:00Z"),
                tld_url="unknown.example",
                url="unknown.example/a",
            ),
        ]
    )

    diff = build_scan_diff(df)

    assert diff is not None
    assert diff["rows"][0]["vendor_key"] == "unknown.example"
    assert diff["rows"][0]["status"] == "unchanged"


def test_category_overviews_group_companies_and_unmapped_domains():
    df = make_df(
        [
            make_row(company_name="Adjust", company_domain="adjust.com"),
            make_row(company_name="Adjust", company_domain="adjust.com"),
            make_row(
                company_name="Braze",
                company_domain="braze.com",
                tld_url="braze.com",
                url="braze.com/y",
            ),
            make_row(tld_url="unknown.example", url="unknown.example/z"),
        ]
    )
    state = make_state(
        [
            {
                "company_type": "Attribution",
                "company_type_slug": "attribution",
                "company_domain": "adjust.com",
            },
            {
                "company_type": "Messaging",
                "company_type_slug": "messaging",
                "company_domain": "braze.com",
            },
        ]
    )

    overviews = {item["category_slug"]: item for item in build_category_overviews(state, df)}

    assert overviews["attribution"]["category_name"] == "Attribution"
    assert overviews["attribution"]["call_count"] == 2
    assert overviews["attribution"]["companies"][0]["company_domain"] == "adjust.com"
    assert overviews["messaging"]["call_count"] == 1
    assert overviews["unmapped"]["companies"][0]["company_domain"] == "unknown.example"


def test_category_overviews_handles_empty_frame():
    assert build_category_overviews(make_state([]), make_df([])) == []


def test_creative_overviews_dedupe_by_hash():
    df = make_df(
        [
            make_row(
                creative_md5_hash="abc123",
                creative_file_extension="jpg",
                advertiser_store_id="com.foo",
            ),
            make_row(
                called_at=pd.Timestamp("2026-02-01T10:00:00Z"),
                run_id=2,
                creative_md5_hash="abc123",
                creative_file_extension="jpg",
            ),
            make_row(creative_md5_hash=None),
        ]
    )

    creatives = build_creative_overviews(df)

    assert len(creatives) == 1
    assert creatives[0]["creative_md5_hash"] == "abc123"
    assert creatives[0]["scan_count"] == 2
    assert creatives[0]["call_count"] == 2
    assert creatives[0]["first_seen"] == "2026-01-01T10:00:00+00:00"
    assert creatives[0]["last_seen"] == "2026-02-01T10:00:00+00:00"


def test_creative_overviews_returns_empty_without_creatives():
    assert build_creative_overviews(make_df([make_row()])) == []


@pytest.mark.parametrize("value", [None, float("nan")])
def test_scan_overviews_tolerates_missing_run_metadata(value):
    df = make_df([make_row(run_id=value, run_at=value, version_code=value)])

    scans = build_scan_overviews(df)

    assert len(scans) == 1
    assert scans[0]["run_id"] is None
    assert scans[0]["run_at"] is None
    assert scans[0]["version_code"] is None
