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
    AppSDKsOverview,
    SDKsDetails,
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
    get_app_sdk_overview,
    get_app_version_timeline,
    get_growth_apps,
    get_ranks_for_app,
    get_ranks_for_app_overview,
    get_recent_apps,
    get_single_app,
    get_single_app_keywords,
    get_single_apps_adstxt,
    insert_sdk_scan_request,
    insert_search_query,
    query_apps_crossfilter,
    search_apps,
)
from dbcon.static import get_company_logos_df, get_total_counts

logger = get_logger(__name__)


def api_call_dfs(state: State, store_id: str) -> pd.DataFrame:
    """Get the API calls for an app."""
    df = get_app_api_details(state, store_id)
    df["url"] = df["url"].str.replace("https://", "").replace("http://", "")
    df["tld_url"] = df["tld_url"].str.replace("https://", "").replace("http://", "")
    df["url"] = df["url"].apply(lambda x: "/".join(x.split("/")[0:3]))
    df["url"] = df["url"].str.replace(r"\?.*$", "", regex=True)
    df["url"] = np.where(
        df["url"].str.len() > 44, df["url"].str[:41] + "...", df["url"]
    )
    df["request_mime_type"] = df["request_mime_type"].replace(r"\;.*$", "", regex=True)
    df["response_mime_type"] = df["response_mime_type"].replace(
        r"\;.*$", "", regex=True
    )
    return df


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


def attach_rating_history(app_hist: pd.DataFrame, star_cols: list[str]) -> pd.DataFrame:
    """Get the rating history of an app."""
    df = app_hist[["snapshot_date"] + star_cols].copy()
    df = df.sort_values(["snapshot_date"])
    df = df.drop(columns=["snapshot_date"])
    change_df = df[star_cols].diff()
    change_df = change_df.rename(
        columns={col: "new_" + col for col in change_df.columns}
    )
    app_hist = pd.concat([app_hist, df, change_df], axis=1)
    return app_hist


def create_app_country_plot_dict(app_hist: pd.DataFrame) -> pd.DataFrame:
    """Create plot dicts for the app country history with linear interpolation for missing weeks.

    Processes each country independently using groupby to maintain separate time series.
    """
    star_cols = ["one_star", "two_star", "three_star", "four_star", "five_star"]
    metrics = ["rating", "review_count", "rating_count", *star_cols]
    xaxis_col = "snapshot_date"

    # Convert to datetime and sort by country and date
    app_hist[xaxis_col] = pd.to_datetime(app_hist[xaxis_col])
    app_hist = app_hist.sort_values(["country", xaxis_col])

    def process_country_group(group):
        """Process a single country's data independently."""
        # Store the country value before resampling
        country_value = group.name

        # Set date as index for resampling
        group = group.set_index(xaxis_col)

        # Resample to weekly frequency - creates missing weeks with NaN
        group = group.resample("W").last()

        # Replace zeros with NaN for cumulative metrics (zeros are data holes, not valid values)
        cumulative_metrics = ["rating_count", "review_count", *star_cols]

        # Metrics to turn numeric / clean
        nmetrics = [m for m in cumulative_metrics + ["rating"] if m in group.columns]
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
            change_metric = f"new_{metric}"
            rate_of_change_metric = f"{metric}_rate_of_change"
            avg_per_day_metric = f"{metric}_avg_per_day"

            # Change (difference from previous period)
            group[change_metric] = group[metric] - group[metric].shift(1)

            # Rate of change: ((new - old) / old) * 100
            group[rate_of_change_metric] = (
                (group[metric] - group[metric].shift(1)) / group[metric].shift(1)
            ) * 100

            # Avg per day (daily average of the change)
            group[avg_per_day_metric] = group[change_metric] / group["days_changed"]

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


def create_app_plot_dict(app_hist: pd.DataFrame) -> pd.DataFrame:
    """Create plot dicts for the app history with linear interpolation for missing weeks."""
    star_cols = ["one_star", "two_star", "three_star", "four_star", "five_star"]
    cumulative_metrics = ["rating", *star_cols]
    weekly_metrics = [
        "weekly_installs",
        "weekly_ratings",
        "weekly_reviews",
        "weekly_active_users",
        "monthly_active_users",
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
        # Formula: ((new - old) / old) * 100
        app_hist[rate_of_change_metric] = (
            app_hist[metric] / app_hist[metric].shift(1)
        ) * 100
        app_hist[avg_per_day_metric] = app_hist[metric] / 7
        metrics_to_add.append(rate_of_change_metric)
        metrics_to_add.append(avg_per_day_metric)

    for metric in cumulative_metrics:
        change_metric = f"new_{metric}"
        rate_of_change_metric = f"{metric}_rate_of_change"
        avg_per_day_metric = f"{metric}_avg_per_day"
        # Calculate the change (difference from previous period)
        app_hist[change_metric] = app_hist[metric] - app_hist[metric].shift(1)
        # Formula: ((new - old) / old) * 100
        app_hist[rate_of_change_metric] = (
            (app_hist[metric] - app_hist[metric].shift(1)) / app_hist[metric].shift(1)
        ) * 100
        # Avg Per Day (daily average of the change)
        app_hist[avg_per_day_metric] = app_hist[change_metric] / 7
        metrics_to_add.append(change_metric)
        metrics_to_add.append(rate_of_change_metric)
        metrics_to_add.append(avg_per_day_metric)

    # Include cumulative/base columns for charts (cumulative_installs, cumulative_ratings, rating, star_cols)
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
    if app_hist.empty:
        return app_hist.to_dict(orient="records")
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
            period: these are appgoblin specific collections of 'new' apps
            store: which store to query
            category: app category

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
            store (int): The store to retrieve.
            app_category (str): The category of apps to retrieve.

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

        hist_df = create_app_plot_dict(hist_df)
        hist_dict = hist_df.to_dict(orient="records")
        duration = round((time.perf_counter() * 1000 - start), 2)
        logger.info(f"{self.path}/{store_id}/metrics-history took {duration}ms")
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

    @get(path="/{store_id:str}/versions", cache=3600)
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

    @get(path="/{store_id:str}/sdks", cache=3600)
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
            found_sdk_tlds.extend(key for x in cat_dict for key in cat_dict[x].keys())

        # Get unique SDK TLDs across all categories
        found_sdk_tlds = list(set(found_sdk_tlds))

        unwanted_value_names = ["smali"] + found_sdk_tlds

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
        leftovers_dict = {
            short_value_name: dddf.groupby("xml_path")["value_name"]
            .apply(list)
            .to_dict()
            for short_value_name, dddf in leftovers_df.groupby("short_value_name")
        }

        permissions_list = permissions_df.value_name.tolist()
        permissions_list = [
            x.replace("android.permission.", "") for x in permissions_list
        ]

        app_queries = df[is_package_query].value_name.unique().tolist()

        skadnetwork_list = df[is_skadnetwork].value_name.unique().tolist()

        trackers_dict = SDKsDetails(
            company_categories=company_sdk_dict,
            permissions=permissions_list,
            leftovers=leftovers_dict,
            app_queries=app_queries,
            skadnetwork=skadnetwork_list,
        )
        duration = round((time.perf_counter() * 1000 - start), 2)
        logger.info(f"{self.path}/{store_id}/sdks took {duration}ms")
        return trackers_dict

    @get(path="/{store_id:str}/ranks/overview", cache=3600)
    async def app_ranks_overview(
        self: Self, state: State, store_id: str
    ) -> AppRankOverview:
        """Handle GET requests for a specific app ranks.

        Args:
        ----
            store_id (str): The id of the store to retrieve.

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
            store_id (str): The id of the store to retrieve.
            country (str): The country to retrieve, alpha2 code (capitalized)

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
            store_id (str): The url of the store_id's ads txt to retrieve

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
            store_id (str): The url of the store_id's ads txt to retrieve

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

    @get(path="/search/{search_term:str}", cache=3600)
    async def search(
        self: Self,
        state: State,
        search_term: str,
        user_id: int | None = Parameter(query="user_id", required=False),
    ) -> AppGroupByStore:
        """Search apps and developers.

        Args:
        ----
            search_term: str the search term to search for.
                Can search packages, developers and app names.
            user_id: int | None the user id of the user searching.

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
    async def get_app_keywords(self: Self, state: State, store_id: str) -> dict:
        """Handle GET request for a list of apps.

        Returns
        -------
            A dictionary representation of the total counts

        """
        start = time.perf_counter() * 1000
        keywords_df = get_single_app_keywords(state, store_id)
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
            A list of API calls

        """
        start = time.perf_counter() * 1000
        apis_df = api_call_dfs(state, store_id)
        apis_list = apis_df.to_dict(orient="records")
        apis_dict = {"apis": apis_list}
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
        include_domains = data.get("include_domains") or []
        exclude_domains = data.get("exclude_domains") or []
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

        # Ensure domains are lists of strings
        if isinstance(include_domains, str):
            include_domains = [include_domains]
        if isinstance(exclude_domains, str):
            exclude_domains = [exclude_domains]

        # Filter out empty strings
        include_domains = [d for d in include_domains if d and isinstance(d, str)]
        exclude_domains = [d for d in exclude_domains if d and isinstance(d, str)]
        if ranking_country is not None:
            ranking_country = str(ranking_country).strip() or None

        logger.info(
            f"Crossfilter query: include={len(include_domains)} domains, "
            f"exclude={len(exclude_domains)} domains, sdk_api={require_sdk_api}, "
            f"iap={require_iap}, ads={require_ads}, ranking_country={ranking_country}, date={mydate}, "
            f"category={category}, store={store}"
        )

        try:
            apps_df = query_apps_crossfilter(
                state,
                include_domains=include_domains,
                exclude_domains=exclude_domains,
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
        except Exception as e:
            logger.error(f"Crossfilter query failed: {e}")
            apps_list = []

        apps_dict = {"apps": apps_list}
        duration = round((time.perf_counter() * 1000 - start), 2)
        logger.info(
            f"{self.path}/crossfilter returned {len(apps_list)} apps in {duration}ms"
        )
        return apps_dict


COLLECTIONS = {
    "new_weekly": {"title": "New Apps this Week"},
    "new_monthly": {"title": "New Apps this Month"},
    "new_yearly": {"title": "New Apps this Year"},
}
