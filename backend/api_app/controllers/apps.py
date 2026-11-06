"""API for app data.

/apps/{store_id} a specific app
/apps/search/{search_term} search for apps
"""

import datetime
import time
import urllib.parse
from typing import Self

import numpy as np
import pandas as pd
from litestar import Controller, Response, get, post
from litestar.background_tasks import BackgroundTask
from litestar.datastructures import State
from litestar.exceptions import NotFoundException
from litestar.params import Parameter

from api_app.models import (
    AdsTxtEntries,
    AppDetail,
    AppGroup,
    AppGroupByStore,
    AppRank,
    AppRankOverview,
    AppSdkHistory,
    AppSDKsOverview,
    SDKsDetails,
)
from api_app.report_exports import (
    create_report_id,
    run_app_explorer_export_job,
    validate_export_dependencies,
)
from api_app.utils import extend_app_icon_url
from config import get_logger
from dbcon.queries import (
    get_app_adstxt_overview,
    get_app_api_details,
    get_app_country_metrics_history,
    get_app_global_metrics_history,
    get_app_rating_histogram,
    get_app_sdk_details,
    get_app_sdk_history,
    get_app_sdk_overview,
    get_app_version_timeline,
    get_growth_apps,
    get_ranks_for_app,
    get_ranks_for_app_overview,
    get_recent_apps,
    get_single_app,
    get_single_app_keywords,
    get_single_app_summary,
    get_single_apps_adstxt,
    insert_sdk_scan_request,
    insert_search_query,
    query_apps_crossfilter,
    search_apps,
)
from dbcon.static import (
    get_company_categories,
    get_company_logos_df,
    get_total_counts,
)

logger = get_logger(__name__)

# Constants for URL truncation
MAX_URL_DISPLAY_LENGTH = 44
TRUNCATED_LENGTH = 41
MIN_SCANS_FOR_DIFF = 2


def has_crossfilter_export_filters(payload: dict) -> bool:
    """Return True when at least one meaningful export filter is set."""
    array_fields = ("include_company_ids", "exclude_company_ids")
    boolean_fields = ("require_sdk_api", "require_iap", "require_ads")
    value_fields = (
        "ranking_country",
        "category",
        "store",
        "min_installs",
        "max_installs",
        "min_rating_count",
        "max_rating_count",
        "min_installs_d30",
        "max_installs_d30",
    )

    for field in array_fields:
        value = payload.get(field)
        if isinstance(value, list) and len(value) > 0:
            return True

    for field in boolean_fields:
        if payload.get(field) is True:
            return True

    for field in value_fields:
        value = payload.get(field)
        if value is None:
            continue
        if isinstance(value, str) and not value.strip():
            continue
        return True

    return False


def api_call_dfs(state: State, store_id: str) -> pd.DataFrame:
    """Get the API calls for an app."""
    df = get_app_api_details(state, store_id)
    df["url"] = df["url"].str.replace("https://", "").replace("http://", "")
    df["tld_url"] = df["tld_url"].str.replace("https://", "").replace("http://", "")
    df["url"] = df["url"].str.split("/").str[:3].str.join("/")
    df["url"] = df["url"].str.replace(r"\?.*$", "", regex=True)
    df["url"] = np.where(
        df["url"].str.len() > MAX_URL_DISPLAY_LENGTH,
        df["url"].str[:TRUNCATED_LENGTH] + "...",
        df["url"],
    )
    df["request_mime_type"] = df["request_mime_type"].replace(r"\;.*$", "", regex=True)
    df["response_mime_type"] = df["response_mime_type"].replace(
        r"\;.*$", "", regex=True
    )
    return df


def _is_missing(value: object) -> bool:
    """Return True for None/NaN/NaT scalars, without raising on containers."""
    if value is None:
        return True
    try:
        return bool(pd.isna(value))
    except (TypeError, ValueError):
        return False


def _iso(value: object) -> str | None:
    """Convert a pandas/datetime scalar to an ISO string, or None."""
    if _is_missing(value):
        return None
    if isinstance(value, str):
        return value
    return pd.Timestamp(value).isoformat()


def _scalar(value: object) -> object:
    """Convert pandas scalars (NaN/NaT/numpy types) into JSON-safe values."""
    if isinstance(value, (list, tuple, dict)):
        return value
    if _is_missing(value):
        return None
    if isinstance(value, (pd.Timestamp, datetime.datetime, datetime.date)):
        return pd.Timestamp(value).isoformat()
    if isinstance(value, np.bool_ | np.integer | np.floating):
        return value.item()
    return value


def _records(df: pd.DataFrame) -> list[dict]:
    """Convert a DataFrame to JSON-safe records."""
    return [
        {key: _scalar(value) for key, value in row.items()}
        for row in df.to_dict(orient="records")
    ]


def _scan_sort_key(scan: dict) -> tuple[int, str]:
    """Sort scans newest first, keeping scans without a timestamp last."""
    run_at = scan.get("run_at")
    return (0 if run_at else 1, run_at or "")


def build_scan_overviews(df: pd.DataFrame) -> list[dict]:
    """Summarize API calls per scan run."""
    if df.empty:
        return []

    work = df.copy()
    work["run_id"] = work["run_id"].astype("Int64")
    scans: list[dict] = []
    for run_id, group in work.groupby("run_id", dropna=False):
        run_at = group["run_at"].dropna().max() if "run_at" in group else None
        version_codes = (
            group["version_code"].dropna() if "version_code" in group else []
        )
        scans.append(
            {
                "run_id": None if pd.isna(run_id) else int(run_id),
                "run_at": _iso(run_at),
                "version_code": str(version_codes.iloc[0])
                if len(version_codes) > 0
                else None,
                "call_count": len(group),
                "domain_count": int(group["tld_url"].nunique(dropna=True)),
                "company_count": int(group["company_domain"].nunique(dropna=True)),
                "creative_count": int(group["creative_md5_hash"].nunique(dropna=True)),
                "countries": sorted(
                    str(c) for c in group["country"].dropna().unique().tolist()
                ),
            }
        )

    scans.sort(key=_scan_sort_key, reverse=True)
    return scans


def build_category_overviews(state: State, df: pd.DataFrame) -> list[dict]:
    """Summarize API calls by adtech company category."""
    if df.empty:
        return []

    categories = get_company_categories(state)
    category_names = (
        categories.drop_duplicates("company_type_slug")
        .set_index("company_type_slug")["company_type"]
        .to_dict()
    )
    domain_categories: dict[str, list[str]] = {}
    for row in categories.dropna(
        subset=["company_domain", "company_type_slug"]
    ).itertuples(index=False):
        domain_categories.setdefault(str(row.company_domain), []).append(
            str(row.company_type_slug)
        )

    work = df.copy()
    work["category_slug"] = work["company_domain"].map(
        lambda domain: (
            domain_categories.get(str(domain), []) if pd.notna(domain) else []
        )
    )
    work = work.explode("category_slug")
    work["category_slug"] = work["category_slug"].fillna("unmapped")

    overviews: list[dict] = []
    for slug, group in work.groupby("category_slug"):
        if slug == "unmapped":
            # Unmapped traffic has no company, so group it by the called domain
            # instead so users can see (and request mappings for) each domain.
            companies = (
                group.dropna(subset=["tld_url"])
                .groupby("tld_url")
                .agg(
                    company_name=("company_name", "first"),
                    company_logo_url=("company_logo_url", "first"),
                    call_count=("url", "size"),
                    domain_count=("tld_url", "nunique"),
                )
                .reset_index()
                .rename(columns={"tld_url": "company_domain"})
                .sort_values("call_count", ascending=False)
            )
        else:
            companies = (
                group.dropna(subset=["company_domain"])
                .groupby("company_domain")
                .agg(
                    company_name=("company_name", "first"),
                    company_logo_url=("company_logo_url", "first"),
                    call_count=("url", "size"),
                    domain_count=("tld_url", "nunique"),
                )
                .reset_index()
                .sort_values("call_count", ascending=False)
            )
        overviews.append(
            {
                "category_slug": str(slug),
                "category_name": category_names.get(
                    str(slug), str(slug).replace("-", " ").title()
                ),
                "call_count": len(group),
                "domain_count": int(group["tld_url"].nunique(dropna=True)),
                "company_count": len(companies),
                "companies": _records(companies),
            }
        )

    overviews.sort(key=lambda item: item["call_count"], reverse=True)
    return overviews


def build_creative_overviews(df: pd.DataFrame) -> list[dict]:
    """Summarize the ad creatives captured during API scans."""
    if df.empty:
        return []

    creatives = df[df["creative_md5_hash"].notna()].copy()
    if creatives.empty:
        return []

    creatives["called_at"] = pd.to_datetime(creatives["called_at"], errors="coerce")
    grouped = (
        creatives.groupby("creative_md5_hash")
        .agg(
            file_extension=("creative_file_extension", "first"),
            first_seen=("called_at", "min"),
            last_seen=("called_at", "max"),
            scan_count=("run_id", "nunique"),
            call_count=("url", "size"),
            company_name=("company_name", "first"),
            company_domain=("company_domain", "first"),
            company_logo_url=("company_logo_url", "first"),
            advertiser_store_id=("advertiser_store_id", "first"),
            advertiser_icon_url_100=("advertiser_icon_url_100", "first"),
        )
        .reset_index()
        .sort_values("last_seen", ascending=False)
    )
    grouped["first_seen"] = grouped["first_seen"].map(_iso)
    grouped["last_seen"] = grouped["last_seen"].map(_iso)
    return _records(grouped)


def build_scan_diff(df: pd.DataFrame) -> dict | None:
    """Compare the companies observed in the two most recent scans."""
    scans = build_scan_overviews(df)
    if len(scans) < MIN_SCANS_FOR_DIFF:
        return None

    latest, previous = scans[0], scans[1]
    work = df.copy()
    work["run_id"] = work["run_id"].astype("Int64")
    work["vendor_key"] = work["company_domain"].fillna(work["tld_url"])

    def vendors_for(run_id: int | None) -> dict[str, dict]:
        if run_id is None:
            subset = work[work["run_id"].isna()]
        else:
            subset = work[work["run_id"] == run_id]
        vendors: dict[str, dict] = {}
        for row in subset.itertuples(index=False):
            key = row.vendor_key
            if pd.isna(key):
                continue
            key = str(key)
            if key in vendors:
                continue
            vendors[key] = {
                "company_domain": _scalar(row.company_domain),
                "company_name": _scalar(row.company_name),
                "company_logo_url": _scalar(row.company_logo_url),
                "tld_url": _scalar(row.tld_url),
            }
        return vendors

    previous_vendors = vendors_for(previous["run_id"])
    latest_vendors = vendors_for(latest["run_id"])

    rows: list[dict] = []
    for key in sorted(set(previous_vendors) | set(latest_vendors)):
        in_previous = key in previous_vendors
        in_latest = key in latest_vendors
        if in_previous and in_latest:
            status = "unchanged"
        elif in_latest:
            status = "new"
        else:
            status = "removed"
        details = latest_vendors.get(key) or previous_vendors[key]
        rows.append(
            {
                "vendor_key": key,
                **details,
                "previous": "Detected" if in_previous else "Not detected",
                "latest": "Detected" if in_latest else "Not detected",
                "status": status,
            }
        )

    order = {"new": 0, "removed": 1, "unchanged": 2}
    rows.sort(key=lambda row: (order[row["status"]], row["vendor_key"]))

    return {
        "previous_run_id": previous["run_id"],
        "previous_run_at": previous["run_at"],
        "latest_run_id": latest["run_id"],
        "latest_run_at": latest["run_at"],
        "new_count": sum(1 for row in rows if row["status"] == "new"),
        "removed_count": sum(1 for row in rows if row["status"] == "removed"),
        "unchanged_count": sum(1 for row in rows if row["status"] == "unchanged"),
        "rows": rows,
    }


def get_search_results(state: State, search_term: str) -> AppGroupByStore:
    """Parse search term and return resulting AppGroup."""
    decoded_input = urllib.parse.unquote(search_term)
    decoded_input = decoded_input.strip()
    if decoded_input[-1] == "+":
        decoded_input = decoded_input[:-1]
    df = search_apps(state, search_input=decoded_input, limit=60)
    df = extend_app_icon_url(df)
    logger.info(f"{decoded_input=} returned rows: {df.shape[0]}")
    apple_apps_dict: list[AppDetail] = df[df["store"].str.startswith("Apple")].to_dict(
        orient="records"
    )
    google_apps_dict: list[AppDetail] = df[
        df["store"].str.startswith("Google")
    ].to_dict(orient="records")
    app_group = AppGroupByStore(
        key=f"Apps matching '{search_term}'",
        apple=AppGroup(title="Apple", apps=apple_apps_dict),
        google=AppGroup(title="Google", apps=google_apps_dict),
    )
    logger.info(
        f"{search_term=} returned rows: {len(apple_apps_dict)} {len(google_apps_dict)}"
    )
    return app_group


def create_app_country_plot_dict(app_hist: pd.DataFrame) -> pd.DataFrame:
    """Create plot dicts for the app country history with linear interpolation.

    Processes each country independently using groupby to maintain separate time series.
    """
    star_cols = ["one_star", "two_star", "three_star", "four_star", "five_star"]
    metrics = ["rating", "rating_count", "installs", *star_cols]
    xaxis_col = "week_start"

    # Convert to datetime and sort by country and date
    app_hist[xaxis_col] = pd.to_datetime(app_hist[xaxis_col])
    app_hist = app_hist.sort_values(["country", xaxis_col])

    def process_country_group(group: pd.DataFrame) -> pd.DataFrame:
        """Process a single country's data independently."""
        # Store the country value before resampling
        country_value = group.name

        # Set date as index for resampling
        group = group.set_index(xaxis_col)

        # Resample to weekly frequency - creates missing weeks with NaN
        group = group.resample("W").last()

        # Replace zeros with NaN for cumulative metrics (zeros are data holes)
        cumulative_metrics = ["rating_count", "installs", *star_cols]

        # Metrics to turn numeric / clean
        nmetrics = [
            m
            # for m in [*cumulative_metrics, "rating", *weekly_metrics]
            for m in [*cumulative_metrics, "rating"]
            if m in group.columns
        ]
        group[nmetrics] = (
            group[nmetrics]
            .apply(pd.to_numeric, errors="coerce")
            .replace(0, np.nan)
            .interpolate(method="linear", limit_direction="forward")
        )

        group = group.reset_index()

        # Restore the country value for all rows (including interpolated ones)
        group["country"] = country_value

        # Calculate days between snapshots
        group["date_change"] = group[xaxis_col] - group[xaxis_col].shift(1)
        group["days_changed"] = group["date_change"].apply(
            lambda x: np.nan if pd.isna(x) else x.days,
        )

        # Calculate derived metrics
        for metric in metrics:
            change_metric = f"weekly_{metric}"
            if metric in ["installs", "rating_count"]:
                rate_of_change_metric = f"weekly_{metric}_rate_of_change"
            else:
                rate_of_change_metric = f"{metric}_rate_of_change"

            # Change (difference from previous period)
            group[change_metric] = group[metric] - group[metric].shift(1)

            # Rate of change: ((new - old) / old) * 100
            group[rate_of_change_metric] = (
                group[change_metric] / group[metric].shift(1)
            ) * 100

        group = group.rename(
            columns={
                "rating_count": "cumulative_ratings",
                "installs": "cumulative_installs",
            }
        )

        return group

    # Apply the processing function to each country group
    app_hist = app_hist.groupby("country", group_keys=False).apply(
        process_country_group
    )

    # Replace infinite values with NaN
    app_hist = app_hist.replace([np.inf, -np.inf], np.nan)

    # Drop columns that are all NaN
    app_hist = app_hist.dropna(axis="columns", how="all")

    if app_hist.empty:
        return app_hist.to_dict(orient="records")

    # Drop rating_avg_per_day as it's not useful (rating is an average, not cumulative)
    app_hist = app_hist.drop(["rating_avg_per_day"], axis=1, errors="ignore")

    # Drop temporary calculation columns
    app_hist = app_hist.drop(["date_change", "days_changed"], axis=1, errors="ignore")

    return app_hist


def create_app_plot_df(app_hist: pd.DataFrame) -> pd.DataFrame:
    """Create plot dicts for app history with linear interpolation.

    Interpolates missing weeks for all metrics.
    """
    star_cols = ["one_star", "two_star", "three_star", "four_star", "five_star"]
    cumulative_metrics = ["rating", *star_cols]
    weekly_metrics = [
        "weekly_installs",
        "weekly_ratings",
        "weekly_active_users",
        "weekly_ad_revenue",
        "weekly_iap_revenue",
    ]
    xaxis_col = "week_start"
    # Convert to datetime and sort
    app_hist[xaxis_col] = pd.to_datetime(app_hist[xaxis_col])
    app_hist = app_hist.sort_values(xaxis_col)

    metrics_to_add = []
    for metric in weekly_metrics:
        rate_of_change_metric = f"{metric}_rate_of_change"
        avg_per_day_metric = f"{metric}_avg_per_day"
        app_hist[rate_of_change_metric] = (
            app_hist[metric] / app_hist[metric].shift(1)
        ) * 100
        app_hist[avg_per_day_metric] = app_hist[metric] / 7
        metrics_to_add.append(rate_of_change_metric)
        metrics_to_add.append(avg_per_day_metric)

    for metric in cumulative_metrics:
        change_metric = f"weekly_{metric}"
        rate_of_change_metric = f"{metric}_rate_of_change"
        avg_per_day_metric = f"{metric}_avg_per_day"
        # Calculate the change (difference from previous period)
        app_hist[change_metric] = app_hist[metric] - app_hist[metric].shift(1)
        # Formula ((new - old) / old) * 100 noqa: ERA001
        app_hist[rate_of_change_metric] = (
            (app_hist[metric] - app_hist[metric].shift(1)) / app_hist[metric].shift(1)
        ) * 100
        # Avg Per Day (daily average of the change)
        app_hist[avg_per_day_metric] = app_hist[change_metric] / 7
        metrics_to_add.append(change_metric)
        metrics_to_add.append(rate_of_change_metric)
        metrics_to_add.append(avg_per_day_metric)

    # Include cumulative/base columns for charts (cumulative_installs,
    # cumulative_ratings, rating, star_cols)
    base_cols = ["cumulative_installs", "cumulative_ratings", "rating", *star_cols]
    available_base = [c for c in base_cols if c in app_hist.columns]
    # Select final columns and drop the first row (no previous data to compare)
    app_hist = app_hist[
        [xaxis_col, *weekly_metrics, *available_base, *metrics_to_add]
    ].drop(app_hist.index[0])
    # Replace infinite values with NaN
    app_hist = app_hist.replace([np.inf, -np.inf], np.nan)
    # Drop columns that are all NaN
    app_hist = app_hist.dropna(axis="columns", how="all")
    # Drop rating_avg_per_day as it's not useful (rating is an average, not cumulative)
    app_hist = app_hist.drop(["rating_avg_per_day"], axis=1, errors="ignore")
    return app_hist


def get_string_date_from_days_ago(days: int) -> str:
    """Get the stringified date from x days ago."""
    mydate = datetime.datetime.now(datetime.UTC) - datetime.timedelta(days=days)
    mydate_str = mydate.strftime("%Y-%m-%d")
    return mydate_str


def get_new_apps_dict(state: State, period: str, store: int, category: str) -> AppGroup:
    """Get collection overview."""
    category_limit = 20

    df = get_recent_apps(
        state, collection=period, store=store, category=category, limit=category_limit
    )
    df = extend_app_icon_url(df)
    df = df.sort_values(["installs", "rating_count"], ascending=False).head(
        category_limit
    )
    appgroup = AppGroup(
        title=COLLECTIONS[period]["title"],
        apps=df.to_dict(orient="records"),
    )
    return appgroup


class AppController(Controller):
    """Controller holding all API endpoints for an app."""

    path = "/api/apps"

    @get(path="/overview", cache=86400)
    async def get_overview(self: Self, state: State) -> dict:
        """Handle GET request for a list of apps.

        Returns
        -------
            A dictionary representation of the total counts

        """
        start = time.perf_counter() * 1000
        overview_df = get_total_counts(state)
        overview_dict = overview_df.to_dict(orient="records")[0]
        duration = round((time.perf_counter() * 1000 - start), 2)
        logger.info(f"{self.path}/overview took {duration}ms")
        return overview_dict

    @get(path="/new-apps/{period:str}/{store:int}/{category:str}", cache=86400)
    async def get_new_apps(
        self: Self, state: State, period: str, store: int, category: str
    ) -> AppGroup:
        """Handle GET request for a list of apps.

        Args:
        ----
            state: Application state
            period: Appgoblin specific collections of 'new' apps
            store: Which store to query
            category: App category

        Returns:
        -------
            A dictionary representation of the list of apps for homepage

        """
        start = time.perf_counter() * 1000
        home_dict = get_new_apps_dict(
            state=state, period=period, store=store, category=category
        )

        duration = round((time.perf_counter() * 1000 - start), 2)
        logger.info(f"{self.path}/collections/{period} took {duration}ms")
        return home_dict

    @get(path="/growth/{store:int}", cache=86400)
    async def get_growth_apps(
        self: Self, state: State, store: int, app_category: str | None = None
    ) -> dict:
        """Handle GET request for a list of fastest growing apps.

        Args:
        ----
            state: Application state
            store: The store to retrieve
            app_category: The category of apps to retrieve

        Returns:
        -------
            A dictionary representation of the list of apps for homepage

        """
        start = time.perf_counter() * 1000
        if app_category == "overall":
            app_category = None
        df = get_growth_apps(state, store=store, app_category=app_category)
        df = extend_app_icon_url(df)
        duration = round((time.perf_counter() * 1000 - start), 2)
        logger.info(f"{self.path}/growth took {duration}ms")
        return {"apps": df.to_dict(orient="records")}

    @get(path="/{store_id:str}", cache=3600)
    async def get_app_detail(self: Self, state: State, store_id: str) -> AppDetail:
        """Handle GET request for a specific app.

         store_id (str): The id of the app to retrieve.

        Returns
        -------
            json

        """
        start = time.perf_counter() * 1000
        app_df = get_single_app(state, store_id)
        if app_df.empty:
            msg = f"Store ID not found: {store_id!r}"
            raise NotFoundException(
                msg,
                status_code=404,
            )
        app_dict = app_df.to_dict(orient="records")[0]
        duration = round((time.perf_counter() * 1000 - start), 2)
        logger.info(f"{self.path}/{store_id} took {duration}ms")
        return app_dict

    @get(path="/{store_id:str}/summary", cache=3600)
    async def get_app_summary(self: Self, state: State, store_id: str) -> dict:
        """Return the lightweight app payload used by account watchlists."""
        start = time.perf_counter() * 1000
        app_df = get_single_app_summary(state, store_id)
        if app_df.empty:
            raise NotFoundException(
                f"Store ID not found: {store_id!r}",
                status_code=404,
            )

        duration = round((time.perf_counter() * 1000 - start), 2)
        logger.info(f"{self.path}/{store_id}/summary took {duration}ms")
        return app_df.to_dict(orient="records")[0]

    @get(path="/{store_id:str}/ratingHistogram", cache=3600)
    async def get_app_histogram(
        self: Self,
        state: State,
        store_id: str,
    ) -> dict:
        """Handle GET request for a specific app.

         store_id (str): The id of the app to retrieve.

        Returns
        -------
            json

        """
        df = get_app_rating_histogram(state=state, store_id=store_id)
        if df.empty:
            logger.info(f"App rating histogram not found: {store_id}")
            return {"histogram": {}}
        mydict = {"histogram": df.to_dict(orient="records")[0]}
        return mydict

    @get(path="/{store_id:str}/country-metrics-history", cache=3600)
    async def app_country_metrics_history(
        self: Self,
        state: State,
        store_id: str,
    ) -> dict:
        """Handle GET request for a specific app.

         store_id (str): The id of the app to retrieve.
         store (int): The store to retrieve.

        Returns
        -------
            json

        """
        start = time.perf_counter() * 1000

        hist_df = get_app_country_metrics_history(state=state, store_id=store_id)

        if hist_df.empty:
            logger.info(f"App country metrics history not found: {store_id}")
            return {}

        hist_df = create_app_country_plot_dict(hist_df)
        hist_dict = hist_df.to_dict(orient="records")
        duration = round((time.perf_counter() * 1000 - start), 2)
        logger.info(f"{self.path}/{store_id}/country-metrics-history took {duration}ms")
        return hist_dict

    @get(path="/{store_id:str}/global-metrics-history", cache=3600)
    async def app_global_metrics_history(
        self: Self,
        state: State,
        store_id: str,
    ) -> dict:
        """Handle GET request for a specific app.

         store_id (str): The id of the app to retrieve.

        Returns
        -------
            json

        """
        start = time.perf_counter() * 1000

        hist_df = get_app_global_metrics_history(state=state, store_id=store_id)
        if hist_df.empty:
            logger.info(f"App global metrics history not found: {store_id}")
            return {}

        hist_df = create_app_plot_df(hist_df)
        hist_dict = hist_df.to_dict(orient="records")
        duration = round((time.perf_counter() * 1000 - start), 2)
        logger.info(f"{self.path}/{store_id}/global-metrics-history took {duration}ms")
        return hist_dict

    @get(path="/{store_id:str}/sdksoverview", cache=3600)
    async def get_sdk_overview(
        self: Self, state: State, store_id: str
    ) -> AppSDKsOverview:
        """Handle GET request for overview of SDKs for a specific app.

         store_id (str): The id of the app to retrieve.

        Returns
        -------
            json

        """
        start = time.perf_counter() * 1000

        df = get_app_sdk_overview(state, store_id)

        df = df.merge(
            get_company_logos_df(state),
            left_on="company_domain",
            right_on="company_domain",
            how="left",
            validate="m:1",
        )

        cats = df.loc[df["category_slug"].notna(), "category_slug"].unique().tolist()
        company_cats = {}
        for cat in cats:
            company_cats[cat] = df[df["category_slug"] == cat][
                ["company_name", "company_domain", "company_logo_url"]
            ].to_dict(orient="records")

        sdk_overview_dict = AppSDKsOverview(
            company_categories=company_cats,
        )
        duration = round((time.perf_counter() * 1000 - start), 2)
        logger.info(f"{self.path}/{store_id}/sdksoverview took {duration}ms")
        return sdk_overview_dict

    @get(path="/{store_id:str}/versions", cache=7200)
    async def get_version_timeline(self: Self, state: State, store_id: str) -> dict:
        """Handle GET request for timeline of versions for a specific app.

         store_id (str): The id of the app to retrieve.

        Returns
        -------
            json

        """
        start = time.perf_counter() * 1000
        df = get_app_version_timeline(state, store_id)
        version_timeline = df.to_dict(orient="records")
        duration = round((time.perf_counter() * 1000 - start), 2)
        logger.info(f"{self.path}/{store_id}/versiontimeline took {duration}ms")
        return version_timeline

    @get(path="/{store_id:str}/sdks", cache=7200)
    async def get_sdk_details(self: Self, state: State, store_id: str) -> SDKsDetails:
        """Handle GET request for all SDKs for a specific app.

         store_id (str): The id of the app to retrieve.

        Returns
        -------
            json

        """
        start = time.perf_counter() * 1000

        df = get_app_sdk_details(state, store_id)

        if df.empty or df.isna().all().all():
            logger.info(f"SDK info not found: {store_id}")
            return SDKsDetails(
                company_categories={},
                permissions=[],
                app_queries=[],
                skadnetwork=[],
                leftovers={},
                company_details={},
            )

        df.loc[df["value_name"].isna(), "value_name"] = ""

        # NOTE WARNING only works for android packages
        # First medium short for com.google.analytics
        df["short_value_name"] = df.value_name.apply(
            lambda x: ".".join(x.split(".")[0:2])
        )

        cats = df.loc[df["category_slug"].notna(), "category_slug"].unique().tolist()
        company_sdk_dict = {}
        found_sdk_tlds: list = []
        # example: {"ad-networks":
        # {"bytedance.com":
        # {"com.bytedance.sdk":
        # {"application/acitivity":
        # ["com.bytedance.sdk.analytics"]}}}}
        for cat in cats:
            cat_dict = {
                company: {
                    short_value_name: dddf.groupby("xml_path")["value_name"]
                    .apply(list)
                    .to_dict()
                    for short_value_name, dddf in ddf.groupby("short_value_name")
                }
                for company, ddf in df[df["category_slug"] == cat].groupby(
                    "company_domain"
                )
            }
            company_sdk_dict[cat] = cat_dict
            # Collect all nested keys from each category
            found_sdk_tlds.extend(key for x in cat_dict for key in cat_dict[x])

        # Get unique SDK TLDs across all categories
        found_sdk_tlds = list(set(found_sdk_tlds))

        unwanted_value_names = ["smali", *found_sdk_tlds]

        is_permission = df["xml_path"] == "uses-permission"
        df.loc[df["xml_path"].str.contains("key", case=False), "value_name"] = (
            "redacted_key"
        )
        is_matching_store_id = df["value_name"].str.startswith(
            ".".join(store_id.split(".")[:2]),
        )

        # maybe try ~(?:com.android... to skip the match groups?
        is_android_activity = df["value_name"].str.contains(
            r"^(com\.android|android|kotlin|smali_)", regex=True
        )

        is_package_query = df["xml_path"].str.contains(
            r"^queries/package|LSApplicationQueriesSchemes"
        )

        is_value_empty = df["value_name"] == ""

        is_skadnetwork = df["xml_path"] == "SKAdNetworkItems"

        permissions_df = df[is_permission]

        leftovers_df = df[
            ~is_permission
            & ~is_matching_store_id
            & ~is_android_activity
            & ~is_value_empty
            & ~is_package_query
            & ~is_skadnetwork
            & df["company_name"].isna()
        ]

        leftovers_df = leftovers_df[
            ~leftovers_df["value_name"].isin(unwanted_value_names)
        ]

        # example: {"bytedance.com":
        # {"application/acitivity":
        # ["com.bytedance.sdk.analytics"] }}
        leftovers_dict: dict[str, dict[str, list[str]]] = {}
        for short_value_name, dddf in leftovers_df.groupby("short_value_name"):
            inner = dddf.groupby("xml_path")["value_name"].apply(list).to_dict()
            key = (
                "Raw Resources"
                if all("res.raw" in k for k in inner)
                else short_value_name
            )
            if key in leftovers_dict:
                leftovers_dict[key].update(inner)
            else:
                leftovers_dict[key] = inner

        permissions_list = permissions_df.value_name.tolist()
        permissions_list = [
            x.replace("android.permission.", "") for x in permissions_list
        ]

        app_queries = df[is_package_query].value_name.unique().tolist()

        skadnetwork_list = df[is_skadnetwork].value_name.unique().tolist()

        # Company display info (name + logo) keyed by company domain,
        # using the same cached logos as /sdksoverview
        company_logos_df = get_company_logos_df(state).drop_duplicates(
            subset=["company_domain"], keep="first"
        )
        company_info_df = (
            df.loc[df["company_domain"].notna(), ["company_domain", "company_name"]]
            .drop_duplicates(subset=["company_domain"], keep="first")
            .merge(company_logos_df, on="company_domain", how="left", validate="m:1")
        )
        company_details = {
            str(row["company_domain"]): {
                "company_name": (
                    str(row["company_name"]) if pd.notna(row["company_name"]) else None
                ),
                "company_logo_url": (
                    str(row["company_logo_url"])
                    if pd.notna(row["company_logo_url"])
                    else None
                ),
            }
            for row in company_info_df.to_dict(orient="records")
        }

        trackers_dict = SDKsDetails(
            company_categories=company_sdk_dict,
            permissions=permissions_list,
            leftovers=leftovers_dict,
            app_queries=app_queries,
            skadnetwork=skadnetwork_list,
            company_details=company_details,
        )
        duration = round((time.perf_counter() * 1000 - start), 2)
        logger.info(f"{self.path}/{store_id}/sdks took {duration}ms")
        return trackers_dict

    @get(path="/{store_id:str}/sdks/history", cache=3600)
    async def get_sdk_history(self: Self, state: State, store_id: str) -> AppSdkHistory:
        """Handle GET request for SDK change history for a specific app.

        Returns a list of SDK additions/removals across versions,
        ordered most recent first.

        Args:
        ----
            state: Application state
            store_id: The id of the app to retrieve

        Returns:
        -------
            AppSdkHistory

        """
        start = time.perf_counter() * 1000

        df = get_app_sdk_history(state, store_id)

        if not df.empty:
            # Merge cached company logos for better coverage
            company_logos_df = get_company_logos_df(state).drop_duplicates(
                subset=["company_domain"], keep="first"
            )
            df = df.merge(
                company_logos_df,
                on="company_domain",
                how="left",
                validate="m:1",
            )

            df = df.replace({pd.NaT: None})
            df = df.where(pd.notna(df), None)

        history = df.to_dict(orient="records")

        duration = round((time.perf_counter() * 1000 - start), 2)
        logger.info(f"{self.path}/{store_id}/sdks/history took {duration}ms")
        return AppSdkHistory(history=history)

    @get(path="/{store_id:str}/ranks/overview", cache=3600)
    async def app_ranks_overview(
        self: Self, state: State, store_id: str
    ) -> AppRankOverview:
        """Handle GET requests for a specific app ranks.

        Args:
        ----
            state: Application state
            store_id: The id of the store to retrieve

        Returns:
        -------
            json

        """
        start = time.perf_counter() * 1000
        df_overview = get_ranks_for_app_overview(state, store_id=store_id, days=90)
        if df_overview.empty:
            logger.info(f"No ranks found for {store_id!r}")
            return AppRankOverview(countries=[], best_ranks=[])
        countries = df_overview["country"].unique().tolist()
        countries = sorted(countries)
        duration = round((time.perf_counter() * 1000 - start), 2)
        logger.info(f"{self.path}/{store_id}/ranks/overview took {duration}ms")
        return AppRankOverview(
            countries=countries, best_ranks=df_overview.to_dict(orient="records")
        )

    @get(path="/{store_id:str}/ranks", cache=3600)
    async def app_ranks(
        self: Self, state: State, store_id: str, country: str = "US"
    ) -> AppRank:
        """Handle GET requests for a specific app ranks.

        Args:
        ----
            state: Application state
            store_id: The id of the store to retrieve
            country: The country to retrieve, alpha2 code (capitalized)

        Returns:
        -------
            json

        """
        start = time.perf_counter() * 1000
        df = get_ranks_for_app(state, store_id=store_id, country=country, days=90)
        if df.empty:
            logger.info(f"No ranks found for {store_id!r}")
            return AppRank(history={})
        df["rank_group"] = df["collection"] + ": " + df["category"]
        df["crawled_date"] = pd.to_datetime(df["crawled_date"]).dt.strftime("%Y-%m-%d")
        pdf = df[df["country"] == country][
            ["crawled_date", "rank", "rank_group"]
        ].sort_values("crawled_date")
        # This format is for echarts, expects data series as columns
        hist_dict = (
            pdf.pivot_table(
                columns=["rank_group"],
                index=["crawled_date"],
                values="rank",
            )
            .reset_index()
            .to_dict(orient="records")
        )
        rank_dict = AppRank(history=hist_dict)
        duration = round((time.perf_counter() * 1000 - start), 2)
        logger.info(f"{self.path}/{store_id}/ranks took {duration}ms")
        return rank_dict

    @get(path="/{store_id:str}/adstxt/overview", cache=3600)
    async def get_app_adstxt_overview(
        self: Self, state: State, store_id: str
    ) -> AdsTxtEntries:
        """Handle GET request for a store_id's related ads txt entries.

        Note these IDs are only connected to the app's developer's URL
        and thus are not app specific.

        Args:
        ----
            state: Application state
            store_id: The url of the store_id's ads txt to retrieve

        Returns:
        -------
            json

        """
        start = time.perf_counter() * 1000
        adstxt_df = get_app_adstxt_overview(state, store_id)

        direct_adstxt_dict = adstxt_df[
            adstxt_df["relationship"].str.upper() == "DIRECT"
        ].to_dict(orient="records")
        reseller_adstxt_dict = adstxt_df[
            adstxt_df["relationship"].str.upper() == "RESELLER"
        ].to_dict(orient="records")

        txts = AdsTxtEntries(
            direct_entries=direct_adstxt_dict,
            reseller_entries=reseller_adstxt_dict,
        )
        duration = round((time.perf_counter() * 1000 - start), 2)
        logger.info(f"{self.path}/{store_id}/adstxt/overview took {duration}ms")
        return txts

    @get(path="/{store_id:str}/adstxt", cache=3600)
    async def get_developer_adstxt(
        self: Self, state: State, store_id: str
    ) -> AdsTxtEntries:
        """Handle GET request for a store_id's related ads txt entries.

        Note these IDs are only connected to the app's developer's URL
        and thus are not app specific.

        Args:
        ----
            state: Application state
            store_id: The url of the store_id's ads txt to retrieve

        Returns:
        -------
            json

        """
        start = time.perf_counter() * 1000
        adstxt_df = get_single_apps_adstxt(state, store_id)

        if adstxt_df.empty:
            logger.info(f"No ads-txt entries found for {store_id!r}")
            return AdsTxtEntries(direct_entries=[], reseller_entries=[])
        direct_adstxt_dict = adstxt_df[
            adstxt_df["relationship"].str.upper() == "DIRECT"
        ].to_dict(orient="records")
        reseller_adstxt_dict = adstxt_df[
            adstxt_df["relationship"].str.upper() == "RESELLER"
        ].to_dict(orient="records")

        txts = AdsTxtEntries(
            direct_entries=direct_adstxt_dict,
            reseller_entries=reseller_adstxt_dict,
        )
        duration = round((time.perf_counter() * 1000 - start), 2)
        logger.info(f"{self.path}/{store_id}/adstxt took {duration}ms")
        return txts

    @get(path="/search/{search_term:str}")
    async def search(
        self: Self,
        state: State,
        search_term: str,
        user_id: int | None = Parameter(query="user_id", required=False),
    ) -> AppGroupByStore:
        """Search apps and developers.

        Args:
        ----
            state: Application state
            search_term: The search term to search for.
                Can search packages, developers and app names.
            user_id: The user id of the user searching.

        """
        start = time.perf_counter() * 1000
        apps_dict = get_search_results(state=state, search_term=search_term)
        duration = round((time.perf_counter() * 1000 - start), 2)
        logger.info(f"{self.path} took {duration}ms")
        return Response(
            apps_dict,
            background=BackgroundTask(
                insert_search_query,
                state=state,
                search_term=search_term,
                user_id=user_id,
            ),
        )

    @post(path="/{store_id:str}/requestSDKScan")
    async def request_sdk_scan(
        self: Self, state: State, store_id: str, data: dict
    ) -> dict:
        """Request a new SDK scan for an app."""
        user_id = data.get("user_id")
        logger.info(f"Requesting SDK scan for {store_id=} by {user_id=}")
        insert_sdk_scan_request(state, store_id, user_id)
        return {"status": "success"}

    @get(path="/{store_id:str}/keywords", cache=3600)
    async def get_app_keywords(
        self: Self,
        state: State,
        store_id: str,
        keyword_text: list[str] | None = Parameter(  # noqa: B008
            query="keyword_text", required=False
        ),
    ) -> dict:
        """Handle GET request for a list of apps.

        Returns
        -------
            A dictionary representation of the total counts

        """
        start = time.perf_counter() * 1000
        if keyword_text is None:
            keyword_text = []

        keywords_df = get_single_app_keywords(
            state, store_id, keyword_texts=keyword_text
        )
        keyword_scores = keywords_df.to_dict(orient="records")
        keywords_list = keywords_df["keyword_text"].tolist()
        keywords_dict = {"keywords": keywords_list, "keyword_scores": keyword_scores}
        duration = round((time.perf_counter() * 1000 - start), 2)
        logger.info(f"{self.path}/{store_id}/keywords took {duration}ms")
        return keywords_dict

    @get(path="/{store_id:str}/apis", cache=3600)
    async def get_app_apis(self: Self, state: State, store_id: str) -> dict:
        """Handle GET request for a list of apps.

        Returns
        -------
            A list of API calls plus scan, category and creative overviews

        """
        start = time.perf_counter() * 1000
        apis_df = api_call_dfs(state, store_id)
        apis_list = _records(apis_df)
        apis_dict = {
            "apis": apis_list,
            "scans": build_scan_overviews(apis_df),
            "categories": build_category_overviews(state, apis_df),
            "creatives": build_creative_overviews(apis_df),
            "scan_diff": build_scan_diff(apis_df),
        }
        duration = round((time.perf_counter() * 1000 - start), 2)
        logger.info(f"{self.path}/{store_id}/apis took {duration}ms")
        return apis_dict

    @post(path="/crossfilter")
    async def get_crossfilter_apps(self: Self, state: State, data: dict) -> dict:
        """Handle POST request for a list of apps for crossfilter.

        Returns
        -------
            A list of apps matching the filter criteria

        """
        start = time.perf_counter() * 1000

        # Extract and validate parameters
        include_company_ids = data.get("include_company_ids") or []
        exclude_company_ids = data.get("exclude_company_ids") or []
        require_sdk_api = bool(data.get("require_sdk_api", False))
        require_iap = bool(data.get("require_iap", False))
        require_ads = bool(data.get("require_ads", False))
        ranking_country = data.get("ranking_country")
        mydate = data.get("mydate", "2024-01-01")
        category = data.get("category")
        store = data.get("store")
        min_installs = data.get("min_installs")
        max_installs = data.get("max_installs")
        min_rating_count = data.get("min_rating_count")
        max_rating_count = data.get("max_rating_count")
        min_installs_d30 = data.get("min_installs_d30")
        max_installs_d30 = data.get("max_installs_d30")

        # Ensure company IDs are lists of integers.
        if isinstance(include_company_ids, (int, str)):
            include_company_ids = [include_company_ids]
        if isinstance(exclude_company_ids, (int, str)):
            exclude_company_ids = [exclude_company_ids]

        # Filter out empty strings
        include_company_ids = [int(value) for value in include_company_ids if value]
        exclude_company_ids = [int(value) for value in exclude_company_ids if value]
        if ranking_country is not None:
            ranking_country = str(ranking_country).strip() or None

        logger.info(
            f"Crossfilter query: include={len(include_company_ids)} companies, "
            f"exclude={len(exclude_company_ids)} companies, sdk_api={require_sdk_api}, "
            f"iap={require_iap}, ads={require_ads}, "
            f"ranking_country={ranking_country}, date={mydate}, "
            f"category={category}, store={store}"
        )

        try:
            apps_df = query_apps_crossfilter(
                state,
                include_company_ids=include_company_ids,
                exclude_company_ids=exclude_company_ids,
                require_sdk_api=require_sdk_api,
                require_iap=require_iap,
                require_ads=require_ads,
                ranking_country=ranking_country,
                mydate=mydate,
                category=category,
                store=store,
                min_installs=min_installs,
                max_installs=max_installs,
                min_rating_count=min_rating_count,
                max_rating_count=max_rating_count,
                min_installs_d30=min_installs_d30,
                max_installs_d30=max_installs_d30,
            )
            apps_df = extend_app_icon_url(apps_df)
            apps_list = apps_df.to_dict(orient="records")
        except Exception:
            logger.exception("Crossfilter query failed")
            apps_list = []

        apps_dict = {"apps": apps_list}
        duration = round((time.perf_counter() * 1000 - start), 2)
        logger.info(
            f"{self.path}/crossfilter returned {len(apps_list)} apps in {duration}ms"
        )
        return apps_dict

    @post(path="/crossfilter/export")
    async def export_crossfilter_apps(self: Self, state: State, data: dict) -> Response:
        """Queue an app explorer CSV export and email the download link."""
        validate_export_dependencies()

        recipient_email = str(data.get("recipient_email", "")).strip()
        user_id = data.get("user_id")
        if not recipient_email:
            return Response(
                {"success": False, "error": "recipient_email is required"},
                status_code=400,
            )

        if not isinstance(user_id, int) or user_id <= 0:
            return Response(
                {"success": False, "error": "user_id is required"},
                status_code=400,
            )

        if not has_crossfilter_export_filters(data):
            return Response(
                {
                    "success": False,
                    "error": "At least one filter must be set before exporting.",
                },
                status_code=400,
            )

        report_id = create_report_id()
        logger.info(
            "Queueing app explorer export %s for %s",
            report_id,
            recipient_email,
        )

        response = {
            "success": True,
            "report_id": report_id,
            "message": "Export queued. A download link will be sent by email.",
        }
        return Response(
            response,
            background=BackgroundTask(
                run_app_explorer_export_job,
                state=state,
                payload=data,
                recipient_email=recipient_email,
                report_id=report_id,
                user_id=user_id,
            ),
        )


COLLECTIONS = {
    "new_weekly": {"title": "New Apps this Week"},
    "new_monthly": {"title": "New Apps this Month"},
    "new_yearly": {"title": "New Apps this Year"},
}
