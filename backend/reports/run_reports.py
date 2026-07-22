"""Run monthly report SQL files and export JSON artifacts."""

from __future__ import annotations

import argparse
import calendar
import importlib
import json
import pathlib
import sys
from dataclasses import dataclass
from datetime import date, timedelta
from typing import TYPE_CHECKING, Any

import pandas as pd
from sqlalchemy import text

if TYPE_CHECKING:
    from sqlalchemy.engine import Engine

try:
    from config import MODULE_DIR, get_logger
    from dbcon.connections import get_db_connection
except ModuleNotFoundError:
    backend_dir = pathlib.Path(__file__).resolve().parents[1]
    backend_dir_text = str(backend_dir)
    if backend_dir_text not in sys.path:
        sys.path.insert(0, backend_dir_text)

    config_module = importlib.import_module("config")
    MODULE_DIR = config_module.MODULE_DIR
    get_logger = config_module.get_logger
    get_db_connection = importlib.import_module("dbcon.connections").get_db_connection

logger = get_logger(__name__, log_name="reports")
QUERY_ROOT = MODULE_DIR / "reports" / "queries"
REPORT_ROUTE_ROOT = MODULE_DIR.parent / "frontend" / "src" / "routes" / "reports"
DEFAULT_REPORT_PREFIX = "ad-user-acquisition-"
MIN_SLUG_PARTS = 2

# Z-score pre-computation step (runs before individual report SQL files)
Z_SCORE_SQL_PATH = QUERY_ROOT / "query_report_z_scores.sql"
Z_SCORE_TABLE = "store_app_z_scores_history_2026"

# SQL section that generates the premium advertiser CSV (not committed to git)
ADVERTISER_CSV_SECTION = "all_advertisers"
# S3 prefix under PUBLIC_DATA_URL for report advertiser CSVs
REPORTS_S3_PREFIX = "downloads/reports"


@dataclass(frozen=True)
class ReportContext:
    """Resolved metadata and paths for a report export run."""

    slug: str
    query_dir: pathlib.Path
    route_dir: pathlib.Path
    start_date: date
    next_month_start_date: date
    first_target_week: date


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(
        description=(
            "Run monthly report SQL and export JSON into the frontend report route."
        ),
    )
    parser.add_argument(
        "report",
        help=(
            "Report slug or YYYY-month value. Examples: "
            "ad-user-acquisition-2026-february or 2026-february"
        ),
    )
    parser.add_argument(
        "--server",
        default="madrone",
        help="Database server key from config.toml. Defaults to madrone.",
    )
    parser.add_argument(
        "--section",
        action="append",
        dest="sections",
        default=[],
        help="Only run a specific section filename stem. Can be passed multiple times.",
    )
    return parser.parse_args()


def normalize_report_slug(report_value: str) -> str:
    """Resolve a CLI report argument to a report slug."""
    if report_value.startswith("report="):
        report_value = report_value.split("=", maxsplit=1)[1]

    query_candidate = QUERY_ROOT / report_value
    route_candidate = REPORT_ROUTE_ROOT / report_value
    if query_candidate.is_dir() or route_candidate.is_dir():
        return report_value

    prefixed_value = f"{DEFAULT_REPORT_PREFIX}{report_value}"
    prefixed_query_candidate = QUERY_ROOT / prefixed_value
    prefixed_route_candidate = REPORT_ROUTE_ROOT / prefixed_value
    if prefixed_query_candidate.is_dir() or prefixed_route_candidate.is_dir():
        return prefixed_value

    message = (
        f"Could not resolve report '{report_value}'. Expected a directory under "
        f"{QUERY_ROOT} or {REPORT_ROUTE_ROOT}."
    )
    raise FileNotFoundError(message)


def parse_month_from_slug(slug: str) -> tuple[int, int]:
    """Extract year and month number from the trailing slug components."""
    parts = slug.split("-")
    if len(parts) < MIN_SLUG_PARTS:
        message = f"Report slug '{slug}' does not include a year and month."
        raise ValueError(message)

    year_str = parts[-2]
    month_name = parts[-1].lower()

    try:
        year = int(year_str)
    except ValueError as exc:
        message = f"Report slug '{slug}' has an invalid year component."
        raise ValueError(message) from exc

    month_lookup = {
        month.lower(): month_number
        for month_number, month in enumerate(calendar.month_name)
        if month
    }
    if month_name not in month_lookup:
        message = f"Report slug '{slug}' has an invalid month component."
        raise ValueError(message)

    return year, month_lookup[month_name]


def add_months(value: date, month_count: int) -> date:
    """Add whole calendar months to a date aligned to the first of the month."""
    month_index = value.month - 1 + month_count
    year = value.year + month_index // 12
    month = month_index % 12 + 1
    return date(year, month, 1)


def build_report_context(report_value: str) -> ReportContext:
    """Resolve filesystem paths and derived date parameters for a report run."""
    slug = normalize_report_slug(report_value)
    query_dir = QUERY_ROOT / slug
    route_dir = REPORT_ROUTE_ROOT / slug

    if not query_dir.is_dir():
        message = f"Missing query directory: {query_dir}"
        raise FileNotFoundError(message)
    if not route_dir.is_dir():
        message = f"Missing frontend report directory: {route_dir}"
        raise FileNotFoundError(message)

    year, month = parse_month_from_slug(slug)
    start_date = date(year, month, 1)
    next_month_start_date = add_months(start_date, 1)
    # First Monday of month
    first_target_week = start_date + timedelta(days=(-start_date.weekday()) % 7)

    return ReportContext(
        slug=slug,
        query_dir=query_dir,
        route_dir=route_dir,
        start_date=start_date,
        next_month_start_date=next_month_start_date,
        first_target_week=first_target_week,
    )


def run_z_scores_step(context: ReportContext, engine: Engine) -> None:
    """Delete and repopulate z-score history for every Monday in the report month.

    Runs *before* individual report SQL files so that downstream queries
    (``impact_growth``, ``new_advertisers``, etc.) see fresh data for the
    ``store_app_z_scores_history_2026`` table.
    """
    if not Z_SCORE_SQL_PATH.is_file():
        logger.warning("Z-score SQL file not found at %s — skipping", Z_SCORE_SQL_PATH)
        return

    sql_text = Z_SCORE_SQL_PATH.read_text(encoding="utf-8")
    last_day = context.next_month_start_date - timedelta(days=1)

    with engine.begin() as conn:
        for week_ts in pd.date_range(
            start=context.start_date, end=last_day, freq="W-MON"
        ):
            week_date: date = week_ts.date()
            logger.info("Computing z-scores for target_week %s", week_date)

            conn.execute(
                text(f"DELETE FROM {Z_SCORE_TABLE} WHERE target_week = :week"),
                {"week": week_date},
            )

            frame = pd.read_sql(text(sql_text), conn, params={"target_week": week_date})
            if frame.empty:
                logger.info("No z-score rows for week %s", week_date)
                continue

            frame.to_sql(Z_SCORE_TABLE, conn, if_exists="append", index=False)
            logger.info("Inserted %s z-score rows for week %s", len(frame), week_date)


def get_sql_files(
    query_dir: pathlib.Path, selected_sections: list[str]
) -> list[pathlib.Path]:
    """Return the SQL files to execute in deterministic order."""
    sql_files = sorted(path for path in query_dir.glob("*.sql") if path.is_file())
    if not sql_files:
        message = f"No SQL files found in {query_dir}"
        raise FileNotFoundError(message)

    if not selected_sections:
        return sql_files

    section_set = set(selected_sections)
    filtered_files = [path for path in sql_files if path.stem in section_set]
    found_sections = {path.stem for path in filtered_files}
    missing_sections = sorted(section_set - found_sections)
    if missing_sections:
        missing_text = ", ".join(missing_sections)
        message = f"Unknown report section(s): {missing_text}"
        raise FileNotFoundError(message)

    return filtered_files


def build_query_params(context: ReportContext) -> dict[str, date]:
    """Build the default bind parameters shared across report SQL files."""
    return {
        "start_date": context.start_date,
        "next_month_start_date": context.next_month_start_date,
        "first_target_week": context.first_target_week,
    }


def execute_query(
    sql_path: pathlib.Path,
    params: dict[str, date],
    engine: Engine,
) -> pd.DataFrame:
    """Execute a single SQL file and return its result DataFrame."""
    sql_text = sql_path.read_text(encoding="utf-8")
    return pd.read_sql(text(sql_text), engine, params=params)


def dataframe_to_records(frame: pd.DataFrame) -> list[dict[str, Any]]:
    """Convert a DataFrame to JSON-safe records using ISO datetimes."""
    if frame.empty:
        return []
    return json.loads(frame.to_json(orient="records", date_format="iso"))


def write_json_output(output_path: pathlib.Path, records: list[dict[str, Any]]) -> None:
    """Write JSON records with stable pretty formatting."""
    output_path.write_text(f"{json.dumps(records, indent=2)}\n", encoding="utf-8")


def _build_advertiser_csv_s3_key(slug: str) -> str:
    """Build the S3 object key for a report's advertiser CSV."""
    return f"{REPORTS_S3_PREFIX}/{slug}/advertisers.csv"


def upload_advertiser_csv(csv_bytes: bytes, slug: str) -> str:
    """Upload the all-advertisers CSV to S3.

    Returns the public download URL for logging.
    """
    import boto3

    try:
        from config import CONFIG  # noqa: PLC0415
    except ModuleNotFoundError:
        backend_dir = pathlib.Path(__file__).resolve().parents[1]
        backend_dir_text = str(backend_dir)
        if backend_dir_text not in sys.path:
            sys.path.insert(0, backend_dir_text)
        CONFIG = importlib.import_module("config").CONFIG  # noqa: N806

    s3_config = CONFIG.get("digi-cloud")
    if not s3_config:
        message = (
            "S3 upload requested but [public-s3] section is missing from config.toml"
        )
        raise RuntimeError(message)

    s3_key = _build_advertiser_csv_s3_key(slug)
    session = boto3.session.Session()
    s3_client = session.client(
        "s3",
        region_name=s3_config["region_name"],
        endpoint_url="https://" + s3_config["host"],
        aws_access_key_id=s3_config["access_key_id"],
        aws_secret_access_key=s3_config["secret_key"],
    )
    s3_client.put_object(
        Bucket=s3_config["bucket"],
        Key=s3_key,
        Body=csv_bytes,
        ACL="public-read",
        ContentType="text/csv; charset=utf-8",
    )

    # Build public URL for logging (assumes PUBLIC_DATA_URL + key pattern)
    try:
        from config import PUBLIC_DATA_URL  # noqa: PLC0415
    except ModuleNotFoundError:
        PUBLIC_DATA_URL = importlib.import_module(  # noqa: N806
            "config"
        ).PUBLIC_DATA_URL
    return f"{PUBLIC_DATA_URL}{s3_key}"


def _pg_array_to_semicolons(value: Any) -> str:
    """Convert a PostgreSQL array string ``{a,b,c}`` to ``a; b``."""
    if value is None:
        return ""
    text = str(value)
    return text.strip("{}").replace(",", ";")


def _safe_float(value: Any) -> float:
    """Coerce *value* to float, treating NaN / None as 0."""
    if value is None:
        return 0.0
    try:
        result = float(value)
    except (ValueError, TypeError):
        return 0.0
    return 0.0 if result != result else result  # NaN check


def _estimate_buying_size(row: pd.Series) -> float:
    """Compute a rough ad buying size score for a single advertiser row."""
    import math

    installs = _safe_float(row.get("weekly_installs") or row.get("advertiser_installs"))
    publishers = _safe_float(row.get("unique_publishers"))
    creatives = _safe_float(row.get("unique_creatives"))
    networks = len(
        [
            x
            for x in str(row.get("ad_network_domains", "") or "").split(",")
            if x.strip()
        ]
    )

    install_score = math.log2(max(installs, 1)) * 2
    publisher_score = publishers * 3
    creative_score = creatives * 5
    network_score = networks * 10
    return round(install_score + publisher_score + creative_score + network_score)


def _maybe_add_buying_size(frame: pd.DataFrame) -> pd.DataFrame:
    """Add ``estimated_buying_size_score`` (0–100 normalised) if the frame has the expected columns."""
    needed = {"unique_publishers", "unique_creatives", "ad_network_domains"}
    has_installs = (
        "weekly_installs" in frame.columns or "advertiser_installs" in frame.columns
    )
    if needed.issubset(frame.columns) and has_installs:
        raw = frame.apply(_estimate_buying_size, axis=1)
        raw_min = raw.min()
        raw_max = raw.max()
        if raw_max > raw_min:
            normalized = (
                ((raw - raw_min) / (raw_max - raw_min) * 100).round(0).astype(int)
            )
            frame["estimated_buying_size_score"] = normalized
        else:
            frame["estimated_buying_size_score"] = 0
            normalized = pd.Series(0, index=frame.index)

        def _tier(score: int) -> str:
            if score >= 50:
                return "Top"
            if score >= 20:
                return "Big"
            return "Medium"

        frame["buying_size_tier"] = normalized.apply(_tier)
    return frame


def build_advertiser_csv(frame: pd.DataFrame, report_period: str) -> bytes:
    """Convert the raw ``all_advertisers`` DataFrame into the premium CSV format.

    Expects columns matching the SQL query and returns UTF-8 CSV bytes with the
    column schema shown on the report page (store_id, app_name, category, …).
    """
    if frame.empty:
        return b""

    out = frame.rename(
        columns={
            "advertiser_store_id": "store_id",
            "advertiser_name": "app_name",
            "advertiser_category": "category",
            "advertiser_installs": "total_estimated_installs",
            "developer_name": "developer",
            "ad_network_domains": "ad_networks",
            "mmp_domains": "mmp_providers",
            "unique_creatives": "unique_creatives_count",
        }
    )

    # Normalise PostgreSQL array columns to semicolon-separated strings
    for col in ("ad_networks", "mmp_providers"):
        if col in out.columns:
            out[col] = out[col].apply(_pg_array_to_semicolons)

    # Add computed columns
    out["report_period"] = report_period
    out["estimated_buying_size_score"] = out.apply(_estimate_buying_size, axis=1)

    # Keep only the columns expected by consumers
    csv_columns = [
        "store_id",
        "app_name",
        "category",
        "developer",
        "report_period",
        "weekly_installs",
        "total_estimated_installs",
        "unique_publishers",
        "unique_creatives_count",
        "ad_networks",
        "mmp_providers",
        "estimated_buying_size_score",
    ]
    out = out[[c for c in csv_columns if c in out.columns]]

    # Sort by buying size descending
    out = out.sort_values("estimated_buying_size_score", ascending=False)

    return out.to_csv(index=False).encode("utf-8")


def run_report(
    context: ReportContext,
    server_name: str,
    selected_sections: list[str],
) -> int:
    """Execute all selected report queries and write JSON artifacts.

    The ``all_advertisers`` section is uploaded as a CSV to S3 instead of
    being written as JSON into the route directory.
    """
    params = build_query_params(context)
    sql_files = get_sql_files(context.query_dir, selected_sections)
    dbcon = get_db_connection(server_name)

    logger.info("Running report %s", context.slug)
    logger.info("Using query directory %s", context.query_dir)
    logger.info("Writing JSON into %s", context.route_dir)

    # --- Step 0: pre-compute weekly z-scores for the month ---
    if len(selected_sections) == 1:
        pass
    else:
        run_z_scores_step(context, engine=dbcon.engine)

    try:
        for sql_path in sql_files:
            section_name = sql_path.stem

            # --- all_advertisers: CSV path via S3 ---
            if section_name == ADVERTISER_CSV_SECTION:
                logger.info("Executing %s (CSV → S3)", sql_path.name)
                frame = execute_query(sql_path, params=params, engine=dbcon.engine)
                report_period = (
                    calendar.month_name[context.start_date.month]
                    + " "
                    + str(context.start_date.year)
                )
                csv_bytes = build_advertiser_csv(frame, report_period)
                public_url = upload_advertiser_csv(csv_bytes, context.slug)
                logger.info("Uploaded %s rows to %s", len(frame), public_url)
                continue

            # --- default: JSON into route directory ---
            logger.info("Executing %s", sql_path.name)
            frame = execute_query(sql_path, params=params, engine=dbcon.engine)
            frame = _maybe_add_buying_size(frame)
            output_path = context.route_dir / f"{section_name}.json"
            records = dataframe_to_records(frame)
            write_json_output(output_path, records)
            logger.info("Wrote %s rows to %s", len(records), output_path)
    finally:
        dbcon.engine.dispose()

    return 0


def main() -> int:
    """CLI entrypoint."""
    args = parse_args()
    context = build_report_context(args.report)
    return run_report(
        context,
        server_name=args.server,
        selected_sections=args.sections,
    )


if __name__ == "__main__":
    raise SystemExit(main())
