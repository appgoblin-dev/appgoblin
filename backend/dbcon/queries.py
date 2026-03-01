"""Query database for backend API."""

import datetime

import pandas as pd
from litestar.datastructures import State
from sqlalchemy import bindparam

from config import get_logger
from dbcon.connections import PostgresCon
from dbcon.static import get_child_companies, get_country_map, get_parent_companies
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


def get_companies_tag_type_stats(
    state: State,
    type_slug: str,
) -> pd.DataFrame:
    """Get top companies for a category type."""
    df = pd.read_sql(
        sql.companies_tag_type_stats,
        con=state.dbcon.engine,
        params={"type_slug": type_slug},
    )
    df["app_category"] = "all"
    df["type_url_slug"] = type_slug
    df["store"] = df["store"].replace({1: "Google Play", 2: "Apple App Store"})
    return df


def get_companies_category_tag_type_stats(
    state: State,
    type_slug: str,
    app_category: str,
) -> pd.DataFrame:
    """Get top companies for a category type."""
    if app_category == "games":
        app_category = "game%"
    df = pd.read_sql(
        sql.companies_category_tag_type_stats,
        con=state.dbcon.engine,
        params={"type_slug": type_slug, "app_category": app_category},
    )
    df.loc[df["app_category"].isna(), "app_category"] = "None"
    if app_category == "game%":
        df.loc[
            df["app_category"].str.contains("game"),
            "app_category",
        ] = "games"
    df = (
        df.groupby(
            [
                "store",
                "tag_source",
                "company_domain",
                "company_name",
                "app_category",
                "type_url_slug",
            ]
        )[["app_count", "installs_d30"]]
        .sum()
        .reset_index()
    )
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


@cache_by_params
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
def get_companies_parent_category_stats(
    state: State,
    app_category: str | None = None,
) -> pd.DataFrame:
    """Get overview of companies from multiple types like sdk and app-ads.txt."""
    parent_company_domains = get_parent_companies(state)
    child_company_domains = get_child_companies(state)
    if app_category:
        if app_category == "games":
            app_category = "game%"
        parents_df = pd.read_sql(
            sql.companies_parent_category_tag_stats,
            state.dbcon.engine,
            params={"app_category": app_category},
        )
        child_df = pd.read_sql(
            sql.companies_category_tag_stats,
            state.dbcon.engine,
            params={"app_category": app_category},
        )
        child_df = child_df[
            ~child_df["company_domain"].isin(
                parent_company_domains + child_company_domains
            )
        ]
        df = pd.concat([parents_df, child_df], axis=0)
        if app_category == "game%":
            df["app_category"] = "games"
            df = (
                df.groupby(
                    [
                        "company_domain",
                        "company_name",
                        "store",
                        "app_category",
                        "tag_source",
                    ]
                )[["app_count", "installs_d30"]]
                .sum()
                .reset_index()
            )
    else:
        parents_df = pd.read_sql(sql.companies_parent_tag_stats, state.dbcon.engine)
        child_df = pd.read_sql(sql.companies_tag_stats, state.dbcon.engine)
        child_df = child_df[
            ~child_df["company_domain"].isin(
                parent_company_domains + child_company_domains
            )
        ]
        df = pd.concat([parents_df, child_df], axis=0)
    df["store"] = df["store"].replace({1: "Google Play", 2: "Apple App Store"})
    df.loc[df["app_category"].isna(), "app_category"] = "None"
    # NULL domains come from IP addresses called directly in api calls
    df = df[df["company_domain"].notna()]
    # Filter out the no-xxx-found placeholder companies
    df = df[~df["company_domain"].str.startswith("no-")]
    return df


def get_companies_top(
    state: State,
    type_slug: str | None = None,
    app_category: str | None = None,
    limit: int = 10,
) -> pd.DataFrame:
    """Get overview of companies from multiple types like sdk and app-ads.txt."""
    if app_category == "games":
        app_category = "game%"
    if type_slug:
        df = pd.read_sql(
            sql.companies_category_type_top,
            state.dbcon.engine,
            params={
                "type_slug": type_slug,
                "app_category": app_category,
                "mylimit": limit,
            },
        )
    else:
        df = pd.read_sql(
            sql.companies_parent_top,
            state.dbcon.engine,
            params={"app_category": app_category, "mylimit": limit},
        )
    df["store"] = df["store"].replace({1: "Google Play", 2: "Apple App Store"})
    return df


def get_company_stats(
    state: State, company_domain: str, app_category: str | None = None
) -> pd.DataFrame:
    """Get overview of companies from multiple types like sdk and app-ads.txt."""
    logger.info(f"query company overview: {company_domain=}")
    parent_companies = get_parent_companies(state)
    is_parent_company = company_domain in parent_companies
    query = (
        sql.company_parent_category_tag_stats
        if is_parent_company
        else sql.company_category_tag_stats
    )
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
                    "rating_count_total",
                ]
            ]
            .sum()
            .reset_index()
        )
    df["store"] = df["store"].replace({1: "Google Play", 2: "Apple App Store"})
    df.loc[df["app_category"].isna(), "app_category"] = "None"
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
    state: State, ad_domain_url: str, publisher_id: str | None = None, limit: int = 5
) -> pd.DataFrame:
    """Get ad domain publishers overview."""
    df = pd.read_sql(
        sql.company_adstxt_publishers_overview,
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
    state: State, ad_domain_url: str
) -> pd.DataFrame:
    """Get ad domain overview."""
    df = pd.read_sql(
        sql.company_adstxt_ad_domain_overview,
        state.dbcon.engine,
        params={"ad_domain_url": ad_domain_url},
    )
    df["store"] = df["store"].replace({1: "google", 2: "apple"})
    df["relationship"] = df["relationship"].str.lower()
    return df


@cache_by_params
def get_company_tree(state: State, company_domain: str) -> pd.DataFrame:
    """Get a company tree with parent companies and domains."""
    logger.info(f"query company tree: {company_domain=}")
    df = pd.read_sql(
        sql.company_tree,
        state.dbcon.engine,
        params={"company_domain": company_domain},
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


def get_company_categories_topn(
    state: State, company_domain: str, num_categories: int = 9
) -> pd.DataFrame:
    """Get a company parent categories."""
    logger.info(f"query company parent categories: {company_domain=}")
    parent_companies = get_parent_companies(state)
    is_parent_company = company_domain in parent_companies
    query = (
        sql.company_parent_category_stats
        if is_parent_company
        else sql.company_category_stats
    )
    df = pd.read_sql(
        query,
        state.dbcon.engine,
        params={"company_domain": company_domain},
    )
    df.loc[df["app_category"].isna(), "app_category"] = "None"

    top_cats = (
        df.sort_values(by="app_count", ascending=False)
        .head(num_categories)
        .app_category.tolist()
    )
    game_cat_count = sum(["game" in x for x in top_cats])
    is_mostly_games = game_cat_count > num_categories / 2
    is_mostly_non_games = game_cat_count <= 1

    if is_mostly_games:
        df.loc[~df["app_category"].str.contains("game"), "app_category"] = "apps"
        top_cats = (
            df.sort_values(by="app_count", ascending=False)
            .head(num_categories)
            .app_category.tolist()
        )
    if is_mostly_non_games:
        df.loc[df["app_category"].str.contains("game"), "app_category"] = "games"
        top_cats = (
            df.sort_values(by="app_count", ascending=False)
            .head(num_categories)
            .app_category.tolist()
        )

    df.loc[~df["app_category"].isin(top_cats), "app_category"] = "others"
    df = df.groupby(["app_category"])["app_count"].sum().reset_index()
    df["name"] = df["app_category"]
    df["name"] = (
        df["name"]
        .str.replace("game_", "Games: ")
        .str.replace("_and_", " & ")
        .str.replace("_", " ")
        .str.title()
    )

    df = df.rename(columns={"name": "group", "app_count": "value"})

    return df


@cache_by_params
def get_category_tag_type_stats(
    state: State, type_slug: str, category: str | None = None
) -> pd.DataFrame:
    """Get category tag type stats."""
    df = pd.read_sql(sql.category_tag_type_stats, state.dbcon.engine)
    df = df[df["type_url_slug"] == type_slug]
    if category:
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
            df.loc[
                df["app_category"].str.contains("game"),
                "app_category",
            ] = "games"
    else:
        df = pd.read_sql(
            sql.category_totals,
            state.dbcon.engine,
            params={"app_category": "%"},
        )
        df["app_category"] = "all"
    df.loc[df["app_category"].isna(), "app_category"] = "None"
    df = (
        df.groupby(["app_category", "store", "tag_source"])[
            [
                "app_count",
                "installs_total",
                "installs_d30",
            ]
        ]
        .sum()
        .reset_index()
    )
    df = df.rename(
        columns={
            "app_count": "cat_total_app_count",
            "installs_total": "cat_total_installs",
            "installs_d30": "cat_total_installs_d30",
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


def search_apps(state: State, search_input: str, limit: int = 100) -> pd.DataFrame:
    """Search apps by term in database."""
    logger.info(f"App search: {search_input=}")
    search_input = search_input.replace("+", " & ")
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
    include_domains: list[str] | None,
    exclude_domains: list[str] | None,
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
) -> pd.DataFrame:
    """Query apps for analytics dashboard."""
    # Ensure domains are lists, not None
    include_domains = include_domains or []
    exclude_domains = exclude_domains or []

    if category == "games":
        category = "game%"

    # Parse date with fallback
    try:
        parsed_date = datetime.datetime.strptime(mydate, "%Y-%m-%d").date()
    except (ValueError, TypeError):
        parsed_date = datetime.date(2024, 1, 1)

    df = pd.read_sql(
        sql.apps_crossfilter,
        state.dbcon.engine,
        params={
            "include_domains": include_domains,
            "exclude_domains": exclude_domains,
            "require_sdk_api": bool(require_sdk_api),
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
        },
    )
    return df


def get_single_app_keywords(state: State, store_id: str) -> pd.DataFrame:
    """Get single app keywords."""
    df = pd.read_sql(
        sql.single_app_keywords, state.dbcon.engine, params={"store_id": store_id}
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


def get_sitemap_companies(dbcon: PostgresCon) -> pd.DataFrame:
    """Get sitemap companies."""
    df = pd.read_sql(sql.sitemap_companies, dbcon.engine)
    return df


def get_sitemap_apps(dbcon: PostgresCon) -> pd.DataFrame:
    """Get sitemap apps."""
    df = pd.read_sql(sql.sitemap_apps, dbcon.engine)
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
