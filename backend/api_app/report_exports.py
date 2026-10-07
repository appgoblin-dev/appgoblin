"""Helpers for asynchronous report exports."""

from __future__ import annotations

import io
import json
import smtplib
import uuid
from datetime import UTC, datetime
from email.message import EmailMessage

import boto3
from litestar.datastructures import State
from sqlalchemy import text

from config import (
    CONFIG,
    SMTP_HOST,
    SMTP_PASSWORD,
    SMTP_PORT,
    SMTP_USER,
    get_logger,
)
from dbcon.queries import get_sdk_pattern_export, query_apps_crossfilter

logger = get_logger(__name__)

EXPORT_S3_CONFIG_KEY = "s3-signed-downloads"
SMTP_CONFIG_KEY = "smtp"
APP_EXPLORER_EXPORT_PREFIX = "user-reports/app-explorer"
SDK_PATTERN_EXPORT_PREFIX = "user-reports/sdk-patterns"
APP_EXPLORER_EXPORT_ROW_LIMIT = 2147483647
APP_EXPLORER_EXPORT_URL_TTL_SECONDS = 7 * 24 * 60 * 60


def validate_export_dependencies() -> None:
    """Ensure required export config is present before queueing a job."""
    missing_sections = []
    if EXPORT_S3_CONFIG_KEY not in CONFIG:
        missing_sections.append(EXPORT_S3_CONFIG_KEY)
    if SMTP_CONFIG_KEY not in CONFIG:
        missing_sections.append(SMTP_CONFIG_KEY)
    if missing_sections:
        msg = f"Missing config section(s): {', '.join(missing_sections)}"
        raise RuntimeError(msg)

    smtp_values = {
        "host": SMTP_HOST,
        "port": SMTP_PORT,
        "user": SMTP_USER,
        "password": SMTP_PASSWORD,
    }
    missing_smtp_keys = [key for key, value in smtp_values.items() if not value]
    if missing_smtp_keys:
        msg = f"Missing smtp config value(s): {', '.join(missing_smtp_keys)}"
        raise RuntimeError(msg)


def create_report_id() -> str:
    """Create a unique export job identifier."""
    return uuid.uuid4().hex


def build_export_filename(report_id: str, report_type: str = "app-explorer") -> str:
    """Build a stable CSV filename for a generated report."""
    date_part = datetime.now(UTC).strftime("%Y-%m-%d")
    short_id = report_id[:8]
    if report_type == "sdk-patterns":
        return f"appgoblin-sdk-pattern-{date_part}-{short_id}.csv"
    return f"appgoblin-crossfilter-{date_part}-{short_id}.csv"


def build_export_s3_key(report_id: str, report_type: str = "app-explorer") -> str:
    """Build the object key for a generated report."""
    prefix = (
        SDK_PATTERN_EXPORT_PREFIX
        if report_type == "sdk-patterns"
        else APP_EXPLORER_EXPORT_PREFIX
    )
    filename = build_export_filename(report_id, report_type)
    return f"{prefix}/{report_id}/{filename}"


def _get_public_s3_client():
    s3_config = CONFIG[EXPORT_S3_CONFIG_KEY]
    session = boto3.session.Session()
    return session.client(
        "s3",
        region_name=s3_config["region_name"],
        endpoint_url="https://" + s3_config["host"],
        aws_access_key_id=s3_config["access_key_id"],
        aws_secret_access_key=s3_config["secret_key"],
    )


def upload_report_csv(
    csv_bytes: bytes, report_id: str, report_type: str = "app-explorer"
) -> tuple[str, str]:
    """Upload a CSV report to S3 and return its URL and object key."""
    s3_config = CONFIG[EXPORT_S3_CONFIG_KEY]
    s3_key = build_export_s3_key(report_id, report_type)
    s3_client = _get_public_s3_client()
    s3_client.put_object(
        Bucket=s3_config["bucket"],
        Key=s3_key,
        Body=csv_bytes,
        ContentType="text/csv; charset=utf-8",
    )
    download_url = s3_client.generate_presigned_url(
        "get_object",
        Params={
            "Bucket": s3_config["bucket"],
            "Key": s3_key,
            "ResponseContentDisposition": (
                f'attachment; filename="{build_export_filename(report_id, report_type)}"'
            ),
        },
        ExpiresIn=APP_EXPLORER_EXPORT_URL_TTL_SECONDS,
    )
    return download_url, s3_key


def store_generated_report(
    *,
    state: State,
    user_id: int,
    s3_key: str,
    payload: dict,
    row_count: int,
    report_name: str | None = None,
) -> None:
    """Store metadata for a completed user-generated report."""
    if state.dbconwrite is None:
        raise RuntimeError("Write database connection is not available")

    report_name = report_name or (
        f"App Explorer CSV export {datetime.now(UTC).strftime('%Y-%m-%d')}"
    )
    filters = {
        key: value
        for key, value in payload.items()
        if key not in {"user_id", "recipient_email"}
    }
    with state.dbconwrite.engine.begin() as connection:
        connection.execute(
            text("""
                INSERT INTO user_generated_reports
                    (user_id, report_name, s3_key, filters, row_count)
                VALUES (
                    :user_id,
                    :report_name,
                    :s3_key,
                    CAST(:filters AS jsonb),
                    :row_count
                )
                """),
            {
                "user_id": user_id,
                "report_name": report_name,
                "s3_key": s3_key,
                "filters": json.dumps(filters),
                "row_count": row_count,
            },
        )


def send_report_ready_email(
    *,
    recipient_email: str,
    download_url: str,
    report_id: str,
    row_count: int,
    report_type: str = "app-explorer",
) -> None:
    """Send an email containing a finished export link."""
    from_address = SMTP_USER
    from_name = "AppGoblin Reports"
    expires_in_days = APP_EXPLORER_EXPORT_URL_TTL_SECONDS // (24 * 60 * 60)

    message = EmailMessage()
    message["From"] = f"{from_name} <{from_address}>"
    message["To"] = recipient_email
    report_label = "SDK pattern" if report_type == "sdk-patterns" else "App Explorer"
    message["Subject"] = f"AppGoblin {report_label} CSV export is ready"

    text_body = (
        f"Your {report_label} CSV export is ready.\n\n"
        f"This download link expires in {expires_in_days} days.\n"
        f"Download: {download_url}\n"
        f"Rows exported: {row_count}\n"
        f"Report ID: {report_id}\n"
    )
    html_body = (
        "<div>"
        f"<h2>{report_label} export ready</h2>"
        f"<p>This download link expires in {expires_in_days} days.</p>"
        f'<p><a href="{download_url}">Download your CSV report</a></p>'
        f"<p><strong>Rows exported:</strong> {row_count}</p>"
        "<h2>View all your reports:</h2>"
        f'<p><a href="https://appgoblin.info/account/reports">https://appgoblin.info/account/reports</a></p>'
        f"<p><strong>Report ID:</strong> {report_id}</p>"
        "</div>"
    )
    message.set_content(text_body)
    message.add_alternative(html_body, subtype="html")

    with smtplib.SMTP_SSL(
        host=SMTP_HOST,
        port=int(SMTP_PORT),
        timeout=30,
    ) as smtp:
        smtp.login(SMTP_USER, SMTP_PASSWORD)
        smtp.send_message(message)


def _normalize_export_frame_columns(df) -> None:
    """Apply user-facing cleanup for exported CSV columns."""
    if "store" in df.columns:
        df["store"] = df["store"].replace({1: "Google Play", 2: "Apple App Store"})


def create_crossfilter_export_csv(state: State, payload: dict) -> tuple[bytes, int]:
    """Run the export query and serialize the result to CSV bytes."""
    apps_df = query_apps_crossfilter(
        state,
        include_company_ids=payload.get("include_company_ids"),
        exclude_company_ids=payload.get("exclude_company_ids"),
        require_sdk_api=bool(payload.get("require_sdk_api", False)),
        require_iap=bool(payload.get("require_iap", False)),
        require_ads=bool(payload.get("require_ads", False)),
        ranking_country=payload.get("ranking_country"),
        mydate=payload.get("mydate", "2024-01-01"),
        category=payload.get("category"),
        store=payload.get("store"),
        min_installs=payload.get("min_installs"),
        max_installs=payload.get("max_installs"),
        min_rating_count=payload.get("min_rating_count"),
        max_rating_count=payload.get("max_rating_count"),
        min_installs_d30=payload.get("min_installs_d30"),
        max_installs_d30=payload.get("max_installs_d30"),
        limit=APP_EXPLORER_EXPORT_ROW_LIMIT,
    )
    _normalize_export_frame_columns(apps_df)

    internal_columns = [
        column
        for column in ("id", "app_icon_url", "icon_64")
        if column in apps_df.columns
    ]
    if internal_columns:
        apps_df = apps_df.drop(columns=internal_columns)

    buffer = io.StringIO()
    apps_df.to_csv(buffer, index=False)
    return buffer.getvalue().encode("utf-8"), len(apps_df.index)


def create_sdk_pattern_export_csv(state: State, pattern: str) -> tuple[bytes, int]:
    """Run an unrestricted SDK pattern query and serialize it to CSV."""
    apps_df = get_sdk_pattern_export(state, pattern)
    if "id" in apps_df.columns:
        apps_df = apps_df.drop(columns=["id"])

    buffer = io.StringIO()
    apps_df.to_csv(buffer, index=False)
    return buffer.getvalue().encode("utf-8"), len(apps_df.index)


def run_app_explorer_export_job(
    *, state: State, payload: dict, recipient_email: str, report_id: str, user_id: int
) -> None:
    """Generate, upload, and email a crossfilter report."""
    try:
        csv_bytes, row_count = create_crossfilter_export_csv(state, payload)
        download_url, s3_key = upload_report_csv(csv_bytes, report_id)
        store_generated_report(
            state=state,
            user_id=user_id,
            s3_key=s3_key,
            payload=payload,
            row_count=row_count,
        )
        send_report_ready_email(
            recipient_email=recipient_email,
            download_url=download_url,
            report_id=report_id,
            row_count=row_count,
        )
        logger.info(
            "Completed app explorer export %s for %s with %s rows",
            report_id,
            recipient_email,
            row_count,
        )
    except Exception:
        logger.exception(
            "Failed app explorer export %s for %s",
            report_id,
            recipient_email,
        )


def run_sdk_pattern_export_job(
    *, state: State, pattern: str, recipient_email: str, report_id: str, user_id: int
) -> None:
    """Generate, upload, and email an unrestricted SDK pattern report."""
    try:
        csv_bytes, row_count = create_sdk_pattern_export_csv(state, pattern)
        download_url, s3_key = upload_report_csv(
            csv_bytes, report_id, report_type="sdk-patterns"
        )
        store_generated_report(
            state=state,
            user_id=user_id,
            s3_key=s3_key,
            payload={"pattern": pattern},
            row_count=row_count,
            report_name=f"SDK pattern export {pattern}",
        )
        send_report_ready_email(
            recipient_email=recipient_email,
            download_url=download_url,
            report_id=report_id,
            row_count=row_count,
            report_type="sdk-patterns",
        )
        logger.info(
            "Completed SDK pattern export %s for %s with %s rows",
            report_id,
            recipient_email,
            row_count,
        )
    except Exception:
        logger.exception(
            "Failed SDK pattern export %s for %s", report_id, recipient_email
        )
