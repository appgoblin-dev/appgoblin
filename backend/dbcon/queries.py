"""Query database for backend API."""

import datetime

import pandas as pd
from litestar.datastructures import State
from sqlalchemy import bindparam, text
from sqlalchemy.sql.elements import TextClause

from config import get_logger
from dbcon.connections import PostgresCon
from dbcon.static import (
    get_company_secondary_domains,
    get_country_map,
    get_parent_companies,
)
from dbcon.utils import cache_by_params, clean_app_df, sql

logger = get_logger(__name__)


def get_recent_apps(
    state: State, collection: str, store: int, category: str | None, limit: int = 20
) -> pd.DataFrame:
    """Get app collections by time."""
    logger.info(f"Query app_store for recent apps {collection=}")
    if collection == "new_weekly":
        query = sql.new_apps_weekly
    elif collection == "new_monthly":
        query = sql.new_apps_monthly
    elif collection == "new_yearly":
        query = sql.new_apps_yearly
    else:
        query = None
    if category == "overall":
        category = None
    df = pd.read_sql(
        query,
        con=state.dbcon.engine,
        params={"store": store, "category": category, "limit": limit},
    )
    if not category:
        df["app_category"] = "overall"
    if not df.empty:
        df = clean_app_df(df)
    return df


def get_advertiser_creatives(
    state: State,
    advertiser_store_id: str | None = None,
    pub_store_id: str | None = None,
) -> pd.DataFrame:
    """Get creatives."""
    if not advertiser_store_id and not pub_store_id:
        msg = "At least one of advertiser_store_id or pub_store_id must be provided"
        raise ValueError(msg)
    df = pd.read_sql(
        sql.creatives,
        con=state.dbcon.engine,
        params={
            "advertiser_store_id": advertiser_store_id,
            "pub_store_id": pub_store_id,
        },
    )
    return df


def get_company_creatives(
    state: State, company_domain: str, limit: int = 6
) -> pd.DataFrame:
    """Get company creatives."""
    df = pd.read_sql(
        sql.company_creatives,
        con=state.dbcon.engine,
        params={"company_domain": company_domain, "mylimit": limit},
    )
    return df


def get_company_s3_reports(state: State, company_domain: str) -> pd.DataFrame:
    """Get registered S3 export metadata for a company domain."""
    return pd.read_sql(
        sql.company_s3_reports,
        con=state.dbcon.engine,
        params={"company_domain": company_domain},
    )


def get_advertiser_creatives_by_host(state: State, host_domain: str) -> pd.DataFrame:
    """Get advertiser creatives for a host domain (public v1 endpoint)."""
    df = pd.read_sql(
        sql.advertiser_creatives_by_host,
        con=state.dbcon.engine,
        params={"host_domain": host_domain},
    )
    return df


def get_growth_apps(
    state: State, store: int, app_category: str | None = None
) -> pd.DataFrame:
    """Get fastest growing apps."""
    df = pd.read_sql(
        sql.growth_apps,
        con=state.dbcon.engine,
        params={"store": store, "app_category": app_category},
    )
    decimal_cols = [
        "installs_z_score_2w",
        "installs_z_score_4w",
    ]
    df[decimal_cols] = df[decimal_cols].round(2)
    return df


def get_companies_type_stats(
    state: State,
    type_slug: str,
    category: str | None = None,
) -> pd.DataFrame:
    """Get top companies for a company type, optionally filtered by app category."""
    if category == "games":
        category = "game%"
    tag_sources = None
    if type_slug == "app-publishers":
        tag_sources = ["publisher"]
    elif type_slug in ["ad-attribution", "business-tools", "development-tools"]:
        tag_sources = ["sdk", "api_call"]

    df = pd.read_sql(
        sql=sql.companies_tag_type_stats,
        con=state.dbcon.engine,
        params={
            "type_slug": type_slug,
            "app_category": category,
            "tag_sources": tag_sources,
            "mylimit": 500,
        },
    )

    # game% -> games label normalization handled in SQL via CASE,
    # but LIKE 'game%' returns multiple subcategories when filtering,
    # so normalize the label here if needed
    if category == "game%":
        df["app_category"] = "games"
    elif category is not None:
        df["app_category"] = category
    else:
        df["app_category"] = "all"

    df["store"] = df["store"].replace({1: "Google Play", 2: "Apple App Store"})
    return df


def get_ranks_for_app(
    state: State, store_id: str, country: str = "US", days: int = 30
) -> pd.DataFrame:
    """Get appstore ranks for a specific app."""
    start_date = (
        datetime.datetime.now(datetime.UTC) - datetime.timedelta(days=days)
    ).strftime("%Y-%m-%d")
    df = pd.read_sql(
        sql.ranks_for_app,
        con=state.dbcon.engine,
        params={"store_id": store_id, "start_date": start_date, "country": country},
    )
    return df


def get_ranks_for_app_overview(
    state: State, store_id: str, days: int = 30
) -> pd.DataFrame:
    """Get appstore ranks for a specific app."""
    start_date = (
        datetime.datetime.now(datetime.UTC) - datetime.timedelta(days=days)
    ).strftime("%Y-%m-%d")
    try:
        df = pd.read_sql(
            sql.ranks_for_app_overview,
            con=state.dbcon.engine,
            params={"store_id": store_id, "start_date": start_date},
        )
        return df
    except Exception as e:
        logger.warning(
            f"Query timeout or error for store_id={store_id}, days={days}: {e}"
        )
        # Return empty DataFrame with expected columns on timeout
        return pd.DataFrame(columns=["country", "collection", "category", "best_rank"])


def get_most_recent_top_ranks(
    state: State,
    collection_id: int,
    category_id: int,
    country: str = "US",
    limit: int = 25,
) -> pd.DataFrame:
    """Get the latest top ranks for a category."""
    df = pd.read_sql(
        sql.most_recent_top_ranks,
        con=state.dbcon.engine,
        params={
            "collection_id": collection_id,
            "category_id": category_id,
            "country": country,
            "mylimit": limit,
        },
    )
    df = df.sort_values("rank", ascending=True)
    return df


def get_country_id(state: State, country: str) -> int:
    """Get country id."""
    df = get_country_map(state)
    country_id = int(df[df["alpha2"] == country]["id"].to_numpy()[0])
    return country_id


def get_history_top_ranks(
    state: State,
    collection_id: int,
    category_id: int,
    country: str = "US",
    limit: int = 25,
    days: int = 30,
) -> pd.DataFrame:
    """Get appstore rank history for plotting."""
    country_id = get_country_id(state, country)
    start_date = (
        datetime.datetime.now(datetime.UTC) - datetime.timedelta(days=days)
    ).strftime("%Y-%m-%d")
    df = pd.read_sql(
        sql.history_top_ranks,
        con=state.dbcon.engine,
        params={
            "collection_id": collection_id,
            "category_id": category_id,
            "country_id": country_id,
            "start_date": start_date,
            "mylimit": limit,
        },
    )
    return df


def get_single_app(state: State, store_id: str) -> pd.DataFrame:
    """Get basic app details for a single store_id."""
    logger.info(f"Query for single app_id={store_id}")
    df = pd.read_sql(sql.single_app, state.dbcon.engine, params={"store_id": store_id})
    if not df.empty:
        df = clean_app_df(df)
    return df


def get_app_rating_histogram(state: State, store_id: str) -> pd.DataFrame:
    """Get app rating histogram for a single store_id."""
    df = pd.read_sql(
        sql.app_rating_histogram,
        state.dbcon.engine,
        params={"store_id": store_id},
    )
    return df


def get_app_sdk_details(state: State, store_id: str) -> pd.DataFrame:
    """Get basic app details for a single store_id."""
    df = pd.read_sql(
        sql.app_sdk_details,
        state.dbcon.engine,
        params={"store_id": store_id},
    )
    return df


def get_app_version_timeline(state: State, store_id: str) -> pd.DataFrame:
    """Get version timeline for a single store_id."""
    df = pd.read_sql(
        sql.app_version_timeline,
        state.dbcon.engine,
        params={"store_id": store_id},
    )
    return df


def get_app_api_details(state: State, store_id: str) -> pd.DataFrame:
    """Get app API details for a single store_id."""
    df = pd.read_sql(
        sql.app_api_details,
        state.dbcon.engine,
        params={"store_id": store_id},
    )
    return df


def get_apps_sdk_overview(state: State, store_ids: tuple[str, ...]) -> pd.DataFrame:
    """Get SDK overview for multiple store_ids."""
    query = sql.apps_sdk_overview.bindparams(bindparam("store_ids", expanding=True))
    df = pd.read_sql_query(
        query,
        state.dbcon.engine,
        params={"store_ids": store_ids},
    )
    df["store"] = df["store"].replace({1: "Google Play", 2: "Apple App Store"})
    return df


def get_app_sdk_overview(state: State, store_id: str) -> pd.DataFrame:
    """Get SDK overview for a single store_id."""
    df = pd.read_sql(
        sql.app_sdk_overview,
        state.dbcon.engine,
        params={"store_id": store_id},
    )
    return df


def get_app_adstxt_overview(state: State, store_id: str) -> pd.DataFrame:
    """Get app-ads.txt overview for a single store_id."""
    logger.info(f"Query app-ads.txt overview app_id={store_id}")
    df = pd.read_sql(
        sql.app_adstxt_overview,
        state.dbcon.engine,
        params={"store_id": store_id},
    )
    return df


@cache_by_params
def get_companies_stats(
    state: State,
    app_category: str | None = None,
) -> pd.DataFrame:
    """Get overview of companies from multiple tag sources like sdk and app-ads.txt.
    # This table has two types of potential rows that are merged
    # For example, example.com is a company that has it's own data
    # but if example.com is also a parent
    # Then it makes more sense to show the parent company data, and exclude the example.com only data
    # This make sense here where we are exporting a single flat overview DF data
    """
    # parent_company_domains = get_parent_companies(state)
    if app_category:
        if app_category == "games":
            app_category = "game%"

    df = pd.read_sql(
        sql.companies_tag_stats,
        state.dbcon.engine,
        params={"limitcompanies": 1000, "app_category": app_category},
    )

    if app_category == "game%":
        df["app_category"] = "games"
        df = (
            df.groupby(
                [
                    "company_domain",
                    "company_name",
                    "parent_company_domain",
                    "parent_company_name",
                    "store",
                    "app_category",
                    "tag_source",
                ]
            )[["app_count", "installs_d30"]]
            .sum()
            .reset_index()
        )

    df["store"] = df["store"].replace({1: "Google Play", 2: "Apple App Store"})
    df.loc[df["app_category"].isna(), "app_category"] = "None"
    # NULL domains come from IP addresses called directly in api calls
    df = df[df["company_domain"].notna()]
    # Filter out the no-xxx-found placeholder companies
    df = df[~df["company_domain"].str.startswith("no-")]
    return df


def get_company_directory(state: State) -> pd.DataFrame:
    """Get the mapped company IDs and names used by App Explorer selectors."""
    return pd.read_sql(sql.company_directory, state.dbcon.engine)


def get_companies_top(
    state: State,
    type_slug: str | None = None,
    category: str | None = None,
    limit: int = 10,
) -> pd.DataFrame:
    """Get overview of companies from multiple types like sdk and app-ads.txt."""
    if category == "games":
        category = "game%"
    if type_slug:
        df = pd.read_sql(
            sql.companies_category_type_top,
            state.dbcon.engine,
            params={
                "type_slug": type_slug,
                "app_category": category,
                "mylimit": limit,
            },
        )
    else:
        df = pd.read_sql(
            sql.companies_parent_top,
            state.dbcon.engine,
            params={"app_category": category, "mylimit": limit},
        )
    df["store"] = df["store"].replace({1: "Google Play", 2: "Apple App Store"})
    return df


def get_company_stats(
    state: State,
    company_domain: str,
    app_category: str | None = None,
    include_parent_rollup: bool = True,
) -> pd.DataFrame:
    """Get overview of companies from multiple types like sdk and app-ads.txt."""
    logger.info(f"query company overview: {company_domain=}")
    parent_companies = get_parent_companies(state)
    secondary_domains = get_company_secondary_domains(state)
    is_parent_company = company_domain in parent_companies and include_parent_rollup
    is_secondary_domain = company_domain in secondary_domains
    if is_secondary_domain:
        query = sql.company_secondary_category_tag_stats
    elif is_parent_company:
        query = sql.company_parent_category_tag_stats
    else:
        query = sql.company_category_tag_stats
    if app_category == "games":
        app_category = "game%"
    df = pd.read_sql(
        query,
        state.dbcon.engine,
        params={
            "company_domain": company_domain,
            "app_category": app_category,
        },
    )
    if app_category == "game%":
        df["app_category"] = "games"
        df = (
            df.groupby(
                [
                    "company_id",
                    "company_domain",
                    "company_name",
                    "store",
                    "tag_source",
                    "app_category",
                ],
                dropna=False,
            )[
                [
                    "app_count",
                    "installs_total",
                    "installs_d30",
                ]
            ]
            .sum()
            .reset_index()
        )
    df["store"] = df["store"].replace({1: "Google Play", 2: "Apple App Store"})
    df.loc[df["app_category"].isna(), "app_category"] = "None"
    return df


def get_company_app_changes(
    state: State,
    company_domain: str,
    tag_source: str,
    year: int,
    quarter: int,
    status: str | None = None,
    limit: int | None = None,
) -> pd.DataFrame:
    """Get quarter-over-quarter app additions or losses for a company domain."""
    logger.info(
        "query company app changes: "
        f"{company_domain=} {tag_source=} {year=} {quarter=} {status=}"
    )
    df = pd.read_sql(
        sql.company_app_changes,
        state.dbcon.engine,
        params={
            "mydomain": company_domain,
            "mytagsource": tag_source,
            "myyear": year,
            "myquarter": quarter,
            "mystatus": status,
        },
    )
    if df.empty:
        return df

    df = df[df["store_id"].notna()].copy()
    df["store"] = df["store"].replace({1: "Google Play", 2: "Apple App Store"})
    df["tag_source"] = tag_source
    df["status"] = (
        df["status"]
        .astype(str)
        .str.strip()
        .str.lower()
        .replace({"added_initial": "added", "removed": "lost"})
    )
    df["name"] = df["name"].astype(str)
    df["store_id"] = df["store_id"].astype(str)
    df["developer_name"] = df["developer_name"].fillna("")
    df["icon_64"] = df["icon_64"].fillna("")
    df["rank"] = pd.to_numeric(df["rank"], errors="coerce")
    df["installs_d30"] = pd.to_numeric(df["installs_d30"], errors="coerce").fillna(0)
    if limit is not None:
        df = df.head(limit)
    return df


def get_combined_companies_history(state: State, company_domain: str) -> pd.DataFrame:
    """Get quarterly company trend history for a company domain.

    Routes to the appropriate trend table based on domain type:
    - trend_domains for secondary domains (child companies)
    - trend_companies for regular company domains
    - trend_parent_companies for parent companies
    """
    logger.info(f"query combined company history: {company_domain=}")
    parent_companies = get_parent_companies(state)
    secondary_domains = get_company_secondary_domains(state)

    if company_domain in secondary_domains:
        query = sql.trend_domains
    elif company_domain in parent_companies:
        query = sql.trend_parent_companies
    else:
        query = sql.trend_companies

    df = pd.read_sql(
        query,
        state.dbcon.engine,
        params={"company_domain": company_domain},
    )
    return df


def get_company_adstxt_publisher_id_apps_overview(
    state: State, ad_domain_url: str, publisher_id: str
) -> pd.DataFrame:
    """Get ad domain publisher id."""
    df = pd.read_sql(
        sql.company_adstxt_publisher_id_apps_overview,
        state.dbcon.engine,
        params={
            "ad_domain_url": ad_domain_url,
            "publisher_id": publisher_id,
        },
    )
    df["store"] = df["store"].replace({1: "google", 2: "apple"})
    df["relationship"] = df["relationship"].str.lower()
    return df


def get_company_adstxt_publisher_id_apps_raw(
    state: State, ad_domain_url: str, publisher_id: str
) -> pd.DataFrame:
    """Get ad domain publisher id."""
    df = pd.read_sql(
        sql.company_adstxt_publisher_id,
        state.dbcon.engine,
        params={
            "ad_domain_url": ad_domain_url,
            "publisher_id": publisher_id,
        },
    )
    df["store"] = df["store"].replace({1: "Android", 2: "iOS"})
    df["developer_id"] = df["developer_id"].astype(str)
    return df


def get_company_adstxt_publishers_overview(
    state: State,
    ad_domain_url: str,
    publisher_id: str | None = None,
    limit: int = 5,
    include_parent_rollup: bool = True,
) -> pd.DataFrame:
    """Get ad domain publishers overview."""
    if include_parent_rollup and ad_domain_url in get_parent_companies(state):
        sql_query = sql.company_adstxt_publishers_parent_overview
    else:
        sql_query = sql.company_adstxt_publishers_overview

    df = pd.read_sql(
        sql_query,
        state.dbcon.engine,
        params={
            "ad_domain_url": ad_domain_url,
            "pubrank_limit": limit,
            "publisher_id": publisher_id,
        },
    )
    df["store"] = df["store"].replace({1: "google", 2: "apple"})
    df["relationship"] = df["relationship"].str.lower()
    return df


def get_company_adstxt_ad_domain_overview(
    state: State, ad_domain_url: str, include_parent_rollup: bool = True
) -> pd.DataFrame:
    """Get ad domain overview."""
    if include_parent_rollup and ad_domain_url in get_parent_companies(state):
        sql_query = sql.company_adstxt_ad_domain_parent_overview
    else:
        sql_query = sql.company_adstxt_ad_domain_overview

    df = pd.read_sql(
        sql_query,
        state.dbcon.engine,
        params={"ad_domain_url": ad_domain_url},
    )
    df["store"] = df["store"].replace({1: "google", 2: "apple"})
    df["relationship"] = df["relationship"].str.lower()
    return df


def get_company_tree_base(state: State, queried_domain: str) -> pd.DataFrame:
    """Get a company tree with parent companies and domains."""
    logger.info(f"query company tree: {queried_domain=}")
    df = pd.read_sql(
        sql.company_tree_base,
        state.dbcon.engine,
        params={"queried_domain": queried_domain},
    )
    return df


def get_company_tree_related_domains(
    state: State, company_id: int, is_parent: bool
) -> pd.DataFrame:
    """Get a company tree with parent companies and domains."""
    logger.info(f"query company tree related domains: {company_id=}")
    df = pd.read_sql(
        sql.company_tree_related_domains,
        state.dbcon.engine,
        params={"company_id": company_id, "is_parent": is_parent},
    )
    return df


def get_company_sdks(state: State, company_domain: str) -> pd.DataFrame:
    """Get a company tree with parent companies and domains."""
    logger.info(f"query company sdks: {company_domain=}")
    df = pd.read_sql(
        sql.company_sdks,
        state.dbcon.engine,
        params={"company_domain": company_domain},
    )
    return df


def _format_category_name(category: str) -> str:
    """Format a raw app_category into a human-readable display name."""
    if category in ("games", "apps", "others", "None"):
        return category.title()
    return (
        category.replace("game_", "Games: ")
        .replace("_and_", " & ")
        .replace("_", " ")
        .title()
    )


def get_company_categories_counts(
    state: State,
    company_domain: str,
    include_parent_rollup: bool = True,
) -> dict[str, pd.DataFrame]:
    """Get raw company categories plus Games and Apps aggregate rows."""
    logger.info(f"query company parent categories: {company_domain=}")
    parent_companies = get_parent_companies(state)
    secondary_domains = get_company_secondary_domains(state)
    is_parent_company = company_domain in parent_companies and include_parent_rollup
    is_secondary_domain = company_domain in secondary_domains
    if is_secondary_domain:
        query = sql.company_secondary_category_stats
    elif is_parent_company:
        query = sql.company_parent_category_stats
    else:
        query = sql.company_category_stats
    df = pd.read_sql(
        query,
        state.dbcon.engine,
        params={"company_domain": company_domain},
    )
    df.loc[df["app_category"].isna(), "app_category"] = "None"

    def _process_store(store_df: pd.DataFrame) -> pd.DataFrame:
        if store_df.empty:
            return pd.DataFrame()

        store_df = store_df.copy()

        def _is_game(category: object) -> bool:
            return category == "games" or (
                isinstance(category, str) and category.startswith("game_")
            )

        game_mask = store_df["app_category"].apply(_is_game)
        aggregate_rows = pd.DataFrame(
            [
                {
                    "group": "Games",
                    "category": "all_games",
                    "value": store_df.loc[game_mask, "app_count"].sum(),
                },
                {
                    "group": "Apps",
                    "category": "all_apps",
                    "value": store_df.loc[~game_mask, "app_count"].sum(),
                },
            ]
        )

        store_df = store_df.sort_values(by="app_count", ascending=False)
        result = store_df.rename(
            columns={"app_category": "category", "app_count": "value"}
        )
        result["group"] = result["category"].apply(_format_category_name)
        raw_result = result[["group", "category", "value"]]
        return pd.concat([aggregate_rows, raw_result], ignore_index=True)

    return {
        "android": _process_store(df[df["store"] == 1]),
        "ios": _process_store(df[df["store"] == 2]),
    }


def get_company_country_apps(
    state: State, company_domain: str, app_category: str | None = None
) -> pd.DataFrame:
    """Get a company's app counts by country, split by store (1=Android, 2=iOS).

    Returns rows with columns: store, country, app_count. The top 5 countries
    per store are kept individually; the remainder are rolled up into an
    'Others' row at the bottom of each store group.

    If app_category is provided, results are filtered to that category.
    """
    logger.info(f"query company country apps: {company_domain=} {app_category=}")
    return pd.read_sql(
        sql.company_country_apps,
        state.dbcon.engine,
        params={"company_domain": company_domain, "app_category": app_category},
    )


@cache_by_params
def get_category_type_stats(
    state: State, type_slug: str, category: str | None = None
) -> pd.DataFrame:
    """Get category type stats."""
    df = pd.read_sql(
        sql.category_tag_type_stats,
        state.dbcon.engine,
        params={"type_url_slug": type_slug},
    )
    if category:
        if category == "games":
            df = df[df["app_category"].str.startswith("game")]
            df["app_category"] = "games"
        df = df[df["app_category"] == category]
    else:
        df["app_category"] = "all"
    logger.info("Loading category tag type stats...")
    df = df.rename(
        columns={
            "app_count": "cat_total_app_count",
            "installs_d30": "cat_total_installs_d30",
        }
    )
    df = (
        df.groupby(["store", "tag_source", "app_category"])[
            ["cat_total_app_count", "cat_total_installs_d30"]
        ]
        .sum()
        .reset_index()
    )
    df["store"] = df["store"].replace({1: "Google Play", 2: "Apple App Store"})
    return df


@cache_by_params
def get_tag_source_company_counts(
    state: State, app_category: str | None = None
) -> pd.DataFrame:
    """Get distinct company counts per (store, tag_source, app_category).

    This queries the source table without the top-1000 cutoff that
    get_companies_stats applies, so the counts reflect all companies.
    """
    if app_category:
        if app_category == "games":
            app_category = "game%"
        df = pd.read_sql(
            sql.companies_counts,
            state.dbcon.engine,
            params={"app_category": app_category},
        )
        if app_category == "game%":
            df["app_category"] = "games"
            df = (
                df.groupby(["store", "tag_source", "app_category"])["company_count"]
                .sum()
                .reset_index()
            )
    else:
        df = pd.read_sql(
            sql.companies_counts,
            state.dbcon.engine,
            params={"app_category": "%"},
        )
        df["app_category"] = "all"

    df["store"] = df["store"].replace({1: "Google Play", 2: "Apple App Store"})
    return df


@cache_by_params
def get_tag_source_category_totals(
    state: State, app_category: str | None = None
) -> pd.DataFrame:
    """Get category totals."""
    if app_category:
        if app_category == "games":
            app_category = "game%"
        df = pd.read_sql(
            sql.category_totals,
            state.dbcon.engine,
            params={"app_category": app_category},
        )
        if app_category == "game%":
            df["app_category"] = "games"
            df = (
                df.groupby(["store", "tag_source", "app_category"])[
                    [
                        "app_count",
                        "installs_d30",
                        "installs_total",
                        "active_apps_universe",
                        "universe_installs_total",
                        "universe_installs_d30",
                    ]
                ]
                .sum()
                .reset_index()
            )
    else:
        df = pd.read_sql(
            sql.category_totals,
            state.dbcon.engine,
            params={"app_category": "%"},
        )
        df["app_category"] = "all"
    df.loc[df["app_category"].isna(), "app_category"] = "None"
    # Aggregate per-category counts (sum across categories for total),
    # but take the first universe value per (store, tag_source) since
    # universe totals are constants per store+tag_source, not per category.
    universe_cols = [
        "active_apps_universe",
        "universe_installs_total",
        "universe_installs_d30",
    ]
    count_cols = ["app_count", "installs_total", "installs_d30"]

    df_counts = df.groupby(["app_category", "store", "tag_source"], as_index=False)[
        count_cols
    ].sum()
    df_universe = df.groupby(["app_category", "store", "tag_source"], as_index=False)[
        universe_cols
    ].first()

    df = df_counts.merge(
        df_universe, on=["app_category", "store", "tag_source"], how="left"
    )

    df = df.rename(
        columns={
            "app_count": "cat_total_app_count",
            "installs_total": "cat_total_installs",
            "installs_d30": "cat_total_installs_d30",
            "active_apps_universe": "cat_active_apps_universe",
            "universe_installs_total": "cat_universe_installs_total",
            "universe_installs_d30": "cat_universe_installs_d30",
        }
    )
    df["store"] = df["store"].replace({1: "Google Play", 2: "Apple App Store"})
    return df


def get_app_country_metrics_history(state: State, store_id: str) -> pd.DataFrame:
    """Get country metrics history for an app."""
    df = pd.read_sql(
        sql.app_country_metrics_history,
        state.dbcon.engine,
        params={"store_id": store_id},
    )
    return df


def get_app_global_metrics_history(state: State, store_id: str) -> pd.DataFrame:
    """Get global metrics history for an app."""
    df = pd.read_sql(
        sql.app_global_metrics_history,
        state.dbcon.engine,
        params={"store_id": store_id},
    )
    return df


def get_single_developer(state: State, developer_id: str) -> pd.DataFrame:
    """Get single developer details."""
    logger.info(f"Developers: {developer_id=}")
    df = pd.read_sql(
        sql.single_developer,
        con=state.dbcon.engine,
        params={"developer_id": developer_id},
    )
    if not df.empty:
        df = clean_app_df(df)
    return df


def get_single_apps_adstxt(state: State, store_id: str) -> pd.DataFrame:
    """Get single developer's app ads txt entries."""
    logger.info(f"Query app's app-ads-txt: {store_id=}")
    df = pd.read_sql(
        sql.single_app_adstxt,
        con=state.dbcon.engine,
        params={"store_id": store_id},
    )
    return df


def get_topapps_for_company_secondary(
    state: State,
    company_domain: str,
    mapped_category: str | None = None,
    limit: int = 10,
) -> pd.DataFrame:
    """Get top apps for for a company."""
    if mapped_category == "games":
        mapped_category = "game%"

    if mapped_category:
        df = pd.read_sql(
            sql.company_secondary_top_apps_category,
            con=state.dbcon.engine,
            params={
                "company_domain": company_domain,
                "mapped_category": mapped_category,
                "mylimit": limit,
            },
        )
    else:
        df = pd.read_sql(
            sql.company_secondary_top_apps,
            con=state.dbcon.engine,
            params={"company_domain": company_domain, "mylimit": limit},
        )
    if not df.empty:
        df["rating"] = 5
        df["installs"] = 0
        df["rating_count"] = 0
        df = clean_app_df(df)
        df = df.sort_values(by="rank", ascending=True)
    return df


def get_creative_clusters(
    state: State,
    app_category: str | None = None,
    file_format: str | None = None,
    company: str | None = None,
    limit: int = 100,
) -> pd.DataFrame:
    """Get creative clusters."""
    if app_category == "games":
        app_category = "game%"
    if company:
        company = f"%{company}%"

    df = pd.read_sql(
        sql.creative_clusters,
        con=state.dbcon.engine,
        params={
            "mylimit": limit,
            "app_category": app_category,
            "file_format": file_format,
            "company": company,
        },
    )
    return df


def get_topapps_for_company_parent(
    state: State,
    company_domain: str,
    mapped_category: str | None = None,
    limit: int = 10,
) -> pd.DataFrame:
    """Get top apps for for a company."""
    if mapped_category == "games":
        mapped_category = "game%"

    if mapped_category:
        df = pd.read_sql(
            sql.company_top_apps_category_parent,
            con=state.dbcon.engine,
            params={
                "company_domain": company_domain,
                "mapped_category": mapped_category,
                "mylimit": limit,
            },
        )
    else:
        df = pd.read_sql(
            sql.company_top_apps_parent,
            con=state.dbcon.engine,
            params={"company_domain": company_domain, "mylimit": limit},
        )

    if not df.empty:
        df["rating"] = 5
        df["installs"] = 0
        df["rating_count"] = 0
        df = clean_app_df(df)
        df = df.sort_values(by="rank", ascending=True)
    return df


def get_topapps_for_company(
    state: State,
    company_domain: str,
    mapped_category: str | None = None,
    limit: int = 10,
) -> pd.DataFrame:
    """Get top apps for for a company."""
    if mapped_category == "games":
        mapped_category = "game%"

    if mapped_category:
        df = pd.read_sql(
            sql.company_top_apps_category,
            con=state.dbcon.engine,
            params={
                "company_domain": company_domain,
                "mapped_category": mapped_category,
                "mylimit": limit,
            },
        )
    else:
        df = pd.read_sql(
            sql.company_top_apps,
            con=state.dbcon.engine,
            params={"company_domain": company_domain, "mylimit": limit},
        )

    if not df.empty:
        df["rating"] = 5
        df["installs"] = 0
        df["rating_count"] = 0
        df = clean_app_df(df)
        df = df.sort_values(by="rank", ascending=True)
    return df


def search_companies(state: State, search_input: str, limit: int = 10) -> pd.DataFrame:
    """Search companies by term in database."""
    logger.info(f"Company search: {search_input=}")
    df = pd.read_sql(
        sql.search_companies,
        state.dbcon.engine,
        params={"searchinput": search_input, "mylimit": limit},
    )
    return df


def get_company_type_country_stats(
    state: State,
    type_url_slug: str,
    app_category: str | None = None,
) -> pd.DataFrame:
    """Get company count per country for a company type, optionally filtered by app category."""
    if app_category == "games":
        app_category = "game%"
    logger.info(f"query company type country stats: {type_url_slug=} {app_category=}")
    df = pd.read_sql(
        sql.company_type_country_stats,
        state.dbcon.engine,
        params={"type_url_slug": type_url_slug, "app_category": app_category},
    )
    if app_category == "game%":
        df = df.groupby(["country"], as_index=False)["company_count"].sum()
    return df


def get_company_follow_lookup(state: State, company_domain: str) -> pd.DataFrame:
    """Resolve company domain to canonical company metadata."""
    df = pd.read_sql(
        sql.company_follow_lookup,
        state.dbcon.engine,
        params={"company_domain": company_domain},
    )
    return df


def search_apps(state: State, search_input: str, limit: int = 100) -> pd.DataFrame:
    """Search apps by term in database."""
    logger.info(f"App search: {search_input=}")
    search_input = " & ".join(search_input.replace("+", " ").split())
    apps = pd.read_sql(
        sql.search_apps,
        state.dbcon.engine,
        params={"searchinput": search_input, "mylimit": limit},
    )
    logger.info(f"App search devs: {search_input=}")
    devapps = pd.read_sql(
        sql.search_devs,
        state.dbcon.engine,
        params={"searchinput": search_input, "mylimit": limit},
    )
    logger.info(f"App search finished: {search_input=}")
    df = pd.concat([apps, devapps]).drop_duplicates()
    if not df.empty:
        df = clean_app_df(df)
    return df


def get_latest_sdks(state: State) -> pd.DataFrame:
    """Get latest sdks."""
    df = pd.read_sql(sql.sdks_latest, state.dbcon.engine)
    df["store"] = df["store"].replace({1: "Google Play", 2: "Apple App Store"})
    return df


def get_user_requested_latest_sdks(state: State) -> pd.DataFrame:
    """Get user requested latest sdks."""
    df = pd.read_sql(sql.sdks_user_requested_latest, state.dbcon.engine)
    return df


def get_sdk_pattern(state: State, value_pattern: str) -> pd.DataFrame:
    """Get sdk pattern."""
    df = pd.read_sql(
        sql.sdk_pattern,
        state.dbcon.engine,
        params={"value_pattern": value_pattern},
    )
    df["store"] = df["store"].replace({1: "Google Play", 2: "Apple App Store"})
    return df


def get_sdk_pattern_export(state: State, value_pattern: str) -> pd.DataFrame:
    """Get every app matching an SDK pattern for a B2B export."""
    df = pd.read_sql(
        sql.sdk_pattern_export,
        state.dbcon.engine,
        params={"value_pattern": value_pattern},
    )
    df["store"] = df["store"].replace({1: "Google Play", 2: "Apple App Store"})
    return df


def get_keyword_details(state: State, keyword: str) -> pd.DataFrame:
    """Get keyword details."""
    df = pd.read_sql(
        sql.keyword_details,
        state.dbcon.engine,
        params={"keyword_text": keyword},
    )
    return df


def get_keyword_apps(state: State, keyword: str, rank: int = 20) -> pd.DataFrame:
    """Get keyword apps."""
    df = pd.read_sql(
        sql.keyword_apps,
        state.dbcon.engine,
        params={"keyword_text": keyword, "max_rank": rank},
    )
    return df


def query_apps_crossfilter(
    state: State,
    include_company_ids: list[int] | None,
    exclude_company_ids: list[int] | None,
    require_sdk_api: bool = False,
    require_iap: bool = False,
    require_ads: bool = False,
    ranking_country: str | None = None,
    mydate: str = "2024-01-01",
    category: str | None = None,
    store: int | None = None,
    min_installs: int | None = None,
    max_installs: int | None = None,
    min_rating_count: int | None = None,
    max_rating_count: int | None = None,
    min_installs_d30: int | None = None,
    max_installs_d30: int | None = None,
    limit: int = 100,
    log_query: bool = False,
) -> pd.DataFrame:
    """Query apps for analytics dashboard."""
    include_company_ids = include_company_ids or []
    exclude_company_ids = exclude_company_ids or []

    if category == "games":
        category = "game%"

    # Parse date with fallback
    try:
        parsed_date = datetime.datetime.strptime(mydate, "%Y-%m-%d").date()
    except (ValueError, TypeError):
        parsed_date = datetime.date(2024, 1, 1)

    params = {
        "require_iap": bool(require_iap),
        "require_ads": bool(require_ads),
        "ranking_country": ranking_country,
        "mydate": parsed_date,
        "category": category,
        "store": store,
        "min_installs": min_installs,
        "max_installs": max_installs,
        "min_rating_count": min_rating_count,
        "max_rating_count": max_rating_count,
        "min_installs_d30": min_installs_d30,
        "max_installs_d30": max_installs_d30,
        "limit": limit,
    }
    if include_company_ids:
        params.update(
            {
                "include_company_ids": include_company_ids,
                "require_sdk_api": bool(require_sdk_api),
            }
        )
    if exclude_company_ids:
        params["exclude_company_ids"] = exclude_company_ids

    query = _build_apps_crossfilter_query(
        include_companies=bool(include_company_ids),
        exclude_companies=bool(exclude_company_ids),
    )
    if log_query:
        logger.debug("Apps crossfilter query:\n%s", query.text)

    df = pd.read_sql(
        query,
        state.dbcon.engine,
        params=params,
    )
    return df


def _build_apps_crossfilter_query(
    *, include_companies: bool, exclude_companies: bool
) -> TextClause:
    """Compose the cross-filter query from SQL fragments.

    Company filters change both the CTE list and the driving table. Keeping
    those branches here avoids making PostgreSQL plan around no-op predicates.
    The individual SQL fragments remain in ``dbcon/sql`` and are loaded by the
    existing ``SQLLoader``.
    """
    ctes: list[str] = []
    if include_companies:
        ctes.append(str(sql.apps_crossfilter_include_cte))
    if exclude_companies:
        ctes.append(str(sql.apps_crossfilter_exclude_cte))

    parts: list[str] = []
    if ctes:
        parts.append("WITH\n" + ",\n".join(ctes))

    parts.extend(
        [
            str(sql.apps_crossfilter_select),
            str(
                sql.apps_crossfilter_from_include
                if include_companies
                else sql.apps_crossfilter_from
            ),
            str(sql.apps_crossfilter_where),
        ]
    )
    if exclude_companies:
        parts.append(str(sql.apps_crossfilter_exclusion))
    parts.append(str(sql.apps_crossfilter_order_limit))
    return text("\n".join(parts))


def get_single_app_keywords(
    state: State, store_id: str, keyword_texts: list[str] | None = None
) -> pd.DataFrame:
    """Get single app keywords."""
    if keyword_texts is None:
        keyword_texts = []

    keyword_texts = [
        text.strip().lower() for text in keyword_texts if text and text.strip()
    ]

    df = pd.read_sql(
        sql.single_app_keywords,
        state.dbcon.engine,
        params={"store_id": store_id, "keyword_texts": keyword_texts},
    )
    df = df.sort_values(by="d30_best_rank", ascending=True)
    return df


def get_sdk_pattern_companies(state: State, value_pattern: str) -> pd.DataFrame:
    """Get sdk pattern companies."""
    df = pd.read_sql(
        sql.sdk_pattern_companies,
        state.dbcon.engine,
        params={"value_pattern": value_pattern},
    )
    return df


def get_app_sdk_history(state: State, store_id: str) -> pd.DataFrame:
    """Get historical SDK changes (additions/removals) for an app."""
    df = pd.read_sql(
        sql.app_sdk_history,
        state.dbcon.engine,
        params={"store_id": store_id},
    )
    return df


def get_sitemap_companies(dbcon: PostgresCon) -> pd.DataFrame:
    """Get sitemap companies."""
    df = pd.read_sql(sql.sitemap_companies, dbcon.engine)
    return df


def get_sitemap_apps(dbcon: PostgresCon) -> pd.DataFrame:
    """Get sitemap apps."""
    df = pd.read_sql(sql.sitemap_apps, dbcon.engine)
    return df


def get_company_tab_indicators(state: State, company_domain: str) -> pd.DataFrame:
    """Get tab-level indicator flags from frontend.companies_overview MV."""
    df = pd.read_sql(
        sql.company_tab_indicators,
        state.dbcon.engine,
        params={"company_domain": company_domain},
    )
    return df


def get_mediation_adapters(state: State, company_domain: str) -> pd.DataFrame:
    """Get mediation adapters."""
    df = pd.read_sql(
        sql.mediation_adapters,
        state.dbcon.engine,
        params={"company_domain": company_domain},
    )
    return df


def insert_sdk_scan_request(
    state: State, store_id: str | list[str], user_id: int | None
) -> None:
    """Insert a new sdk scan request.

    Args:
        state (State): Database connection state.
        store_id (str | list[str]): A single/list of store_id as a string.
        user_id (int | None): The user id of the user requesting the sdk scan.

    The function inserts one or more records into the sdk scan request table.
    Each with a 'store_id' key.

    """
    logger.info(f"Inserting new sdk scan request: {store_id=} by {user_id=}")

    if state.dbconwrite is None:
        logger.error("Write connection not available, cannot insert SDK scan request")
        return

    if isinstance(store_id, str):
        data = [{"store_id": store_id, "user_id": user_id}]
    else:
        data = [{"store_id": s, "user_id": user_id} for s in store_id]

    with state.dbconwrite.engine.connect() as connection, connection.begin():
        connection.execute(sql.insert_sdk_scan_request, data)


def insert_search_query(state: State, search_term: str, user_id: int | None) -> None:
    """Insert a new search query.

    Args:
        state (State): Database connection state.
        search_term (str): The search term.
        user_id (int | None): The user id of the user searching.

    """
    logger.info(f"Inserting new search query: {search_term=} by {user_id=}")

    if state.dbconwrite is None:
        logger.error("Write connection not available, cannot insert search query")
        return

    data = [{"search_term": search_term, "user_id": user_id}]

    with state.dbconwrite.engine.connect() as connection, connection.begin():
        connection.execute(sql.insert_search_query, data)


def get_app_keywords_history(
    state: State, store_app_id: int, keyword_ids: tuple[int, ...], days: int = 120
) -> pd.DataFrame:
    """Get app keyword rank history."""
    start_date = (
        datetime.datetime.now(datetime.UTC) - datetime.timedelta(days=days)
    ).strftime("%Y-%m-%d")
    query = sql.app_keywords_history.bindparams(
        bindparam("keyword_ids", expanding=True)
    )
    df = pd.read_sql_query(
        query,
        state.dbcon.engine,
        params={
            "store_app_id": store_app_id,
            "keyword_ids": keyword_ids,
            "start_date": start_date,
        },
    )
    return df
