"""API endoipoints for companies.

/companies/ returns list of top companies overall.
/companies/{company_domain} returns detail for a specific company.
/companies/{company_domain}/apps-added returns recently added apps for a specific company.
/companies/{company_domain}/apps-lost returns recently lost apps for a specific company.
/companies/{company_domain}/topapps returns top apps for a specific company.
/companies/{company_domain}/tree returns parent/child company tree for a specific company.
/companies/categories/{category} returns list of top companies for a specific category.
# /companies/countries returns list of countries where companies are located.


"""

import io
import re
import time
import urllib.parse
from collections import defaultdict
from typing import Self, SupportsFloat, SupportsIndex, SupportsInt

import numpy as np
import pandas as pd
from litestar import Controller, get
from litestar.config.response_cache import CACHE_FOREVER
from litestar.datastructures import State
from litestar.exceptions import NotFoundException
from litestar.response import Stream

from api_app.models import (
    AppGroup,
    ChildCompany,
    CompaniesCategoryOverview,
    CompaniesOverview,
    CompanyAppChangesOverview,
    CompanyCategoryOverview,
    CompanyDetail,
    CompanyDirectoryEntry,
    CompanyDomain,
    CompanyFollowLookup,
    CompanyOverviewScope,
    CompanyPatternsDict,
    CompanyPlatformOverview,
    CompanyPubIDApps,
    CompanyPubIDAppsRelationship,
    CompanyPubIDOverview,
    CompanyPubIDTotals,
    CompanyTabIndicators,
    CompanyTree,
    CompanyTrendPoint,
    CompanyTrends,
    CompanyTrendsSummary,
    CompanyTrendSummary,
    CompanyTypes,
    ParentCompanyContext,
    TopCompaniesOverviewShort,
    TopCompaniesShort,
)
from config import get_logger
from dbcon.queries import (
    get_category_type_stats,
    get_combined_companies_history,
    get_companies_stats,
    get_companies_top,
    get_companies_type_stats,
    get_company_adstxt_ad_domain_overview,
    get_company_adstxt_publisher_id_apps_overview,
    get_company_adstxt_publisher_id_apps_raw,
    get_company_adstxt_publishers_overview,
    get_company_app_changes,
    get_company_categories_counts,
    get_company_country_apps,
    get_company_follow_lookup,
    get_company_s3_reports,
    get_company_sdks,
    get_company_stats,
    get_company_tab_indicators,
    get_company_tree_base,
    get_company_tree_related_domains,
    get_company_type_country_stats,
    get_mediation_adapters,
    get_tag_source_category_totals,
    get_tag_source_company_counts,
    get_topapps_for_company,
    get_topapps_for_company_parent,
    get_topapps_for_company_secondary,
    search_companies,
)
from dbcon.queries import (
    get_company_directory as get_company_directory_df,
)
from dbcon.static import (
    get_adtech_categories,
    get_company_api_call_countrys,
    get_company_categories,
    get_company_countries,
    get_company_logos_df,
    get_company_open_source,
    get_company_secondary_domains,
    get_company_trends_overview,
    get_company_trends_summary,
    get_mediation_companies,
    get_parent_companies,
)

logger = get_logger(__name__)

TREND_HISTORY_WINDOW_QUARTERS = 4
TREND_PLATFORM_MAP = {1: "android", 2: "ios"}
TREND_TAG_SOURCE_ORDER = {"sdk": 0, "api_call": 1, "app_ads_direct": 2}
COMPANY_APP_CHANGES_LIMIT = 50
COMPANY_APP_CHANGE_TAG_SOURCES = ("sdk", "api_call", "app_ads_direct")
COMPANY_APP_CHANGE_SDK_API_TAG_SOURCES = ("sdk", "api_call")
COMPANY_APP_CHANGE_ADSTXT_TAG_SOURCES = ("app_ads_direct",)
COMPANY_APP_CHANGE_PERIOD_RE = re.compile(r"(?P<year>\d{4})-?Q(?P<quarter>[1-4])")


def _normalize_trend_platform(store: object) -> str:
    """Map backend store identifiers to stable trend platform slugs."""
    if pd.isna(store):
        return "unknown"

    if store in TREND_PLATFORM_MAP:
        return TREND_PLATFORM_MAP[int(store)]

    normalized = str(store).strip().lower()
    if "google" in normalized or normalized == "android":
        return "android"
    if "apple" in normalized or normalized == "ios":
        return "ios"
    return normalized or "unknown"


def _make_trend_source_key(platform: str, tag_source: str) -> str:
    """Build a stable key for a platform + tag source trend series."""
    return f"{platform}_{tag_source}"


def enrich_domains(
    domains: list[CompanyDomain], api_data: list[dict]
) -> list[CompanyDomain]:
    lookup = {d["tld_url"]: d for d in api_data}
    for domain in domains:
        if domain.domain_name in lookup:
            domain.country = lookup[domain.domain_name]["country"]
            domain.org = lookup[domain.domain_name]["org"]
    return domains


def make_company_api_domains_dict(
    state: State, company_domains: list[str]
) -> list[dict]:
    """Make company api domains dict."""

    def _to_string_list(value: object) -> list[str]:
        """Normalize pandas / numpy containers to plain list[str] for JSON responses."""
        if value is None:
            return []
        if isinstance(value, np.ndarray | pd.api.extensions.ExtensionArray):
            return [str(v) for v in value.tolist() if pd.notna(v)]
        if isinstance(value, list | tuple | set | pd.Index):
            return [str(v) for v in value if pd.notna(v)]
        if pd.isna(value):
            return []
        return [str(value)]

    df = get_company_api_call_countrys(state)
    reg_df = df[df["company_domain"].isin(company_domains)]
    p_df = df[df["parent_company_domain"].isin(company_domains)]
    df = pd.concat([reg_df, p_df]).drop_duplicates()
    if df.empty:
        return []
    df = (
        df.groupby(["tld_url"])[["country", "org"]]
        .agg(
            country=pd.NamedAgg(column="country", aggfunc="unique"),
            org=pd.NamedAgg(column="org", aggfunc="unique"),
        )
        .reset_index()
    )
    # Pandas 3.0 may return ArrowStringArray or StringArray here.
    df["org"] = df["org"].apply(_to_string_list)
    df["country"] = df["country"].apply(_to_string_list)
    missing_domains = [
        {"tld_url": x, "country": [], "org": []}
        for x in company_domains
        if x not in df["tld_url"].tolist()
    ]
    df = pd.concat([df, pd.DataFrame(missing_domains)])
    return df.to_dict(orient="records")


def get_search_results(state: State, search_term: str) -> pd.DataFrame:
    """Parse search term and return resulting AppGroup."""
    decoded_input = urllib.parse.unquote(search_term)
    df = search_companies(state, search_input=decoded_input, limit=20)
    df = df.merge(
        get_company_logos_df(state),
        on="company_domain",
        how="left",
        validate="m:1",
    )
    logger.info(f"{decoded_input=} returned rows: {df.shape[0]}")
    return df


def get_company_apps(
    state: State,
    company_domain: str,
    category: str | None = None,
) -> CompanyPlatformOverview:
    """Get the overview data from the database."""
    parent_companies = get_parent_companies(state)
    secondary_domains = get_company_secondary_domains(state)
    is_secondary_domain = company_domain in secondary_domains
    is_parent_company = company_domain in parent_companies
    limit = 5 if category else 10
    if is_secondary_domain:
        df = get_topapps_for_company_secondary(
            state=state,
            company_domain=company_domain,
            mapped_category=category,
            limit=limit,
        )
    elif is_parent_company:
        df = get_topapps_for_company_parent(
            state=state,
            company_domain=company_domain,
            mapped_category=category,
            limit=limit,
        )
    else:
        df = get_topapps_for_company(
            state=state,
            company_domain=company_domain,
            mapped_category=category,
            limit=limit,
        )

    df = df[~df["store"].isna()]

    android_df = df[(df["store"].str.startswith("Google"))]
    ios_df = df[(~df["store"].str.startswith("Google"))]

    results = CompanyPlatformOverview(
        android=AppGroup(
            apps=android_df.to_dict(orient="records"),
            title=company_domain,
        ),
        ios=AppGroup(
            apps=ios_df.to_dict(orient="records"),
            title=company_domain,
        ),
    )
    return results


def _parse_company_trends_period(latest_period: str | None) -> tuple[int, int] | None:
    """Parse a trends period string like 2026-Q1 or 2026Q1 into integers."""
    if latest_period is None:
        return None

    match = COMPANY_APP_CHANGE_PERIOD_RE.search(str(latest_period).strip().upper())
    if not match:
        return None

    return int(match.group("year")), int(match.group("quarter"))


def _resolve_company_app_changes_period(
    state: State,
    company_domain: str,
    year: int | None = None,
    quarter: int | None = None,
) -> tuple[int, int]:
    """Resolve the target quarter for company app-change lookups."""
    if year is not None and quarter is not None:
        return year, quarter

    trends_summary = get_company_trends_summary(
        state=state, company_domain=company_domain
    )
    resolved_period = _parse_company_trends_period(
        getattr(trends_summary, "latest_period", None)
    )
    if resolved_period is None:
        msg = f"No recent company change period found for {company_domain!r}"
        raise NotFoundException(msg, status_code=404)

    return resolved_period


def _shape_company_app_changes_df(
    app_changes_df: pd.DataFrame,
    *,
    limit: int,
) -> pd.DataFrame:
    """Collapse per-tag rows into one app row with source booleans for the frontend."""
    if app_changes_df.empty:
        return pd.DataFrame(
            columns=[
                "store",
                "name",
                "store_id",
                "developer_name",
                "icon_64",
                "rank",
                "installs_d30",
                "status",
                "sdk",
                "publisher",
                "api_call",
                "app_ads_direct",
                "is_removed",
                "country",
            ]
        )

    is_removed_col = "is_removed" in app_changes_df.columns
    country_col = "country" in app_changes_df.columns

    groupby_cols = [
        "store",
        "name",
        "store_id",
        "developer_name",
        "status",
    ]
    icon_col = "icon_64" if "icon_64" in app_changes_df.columns else "icon_url_100"
    groupby_cols.insert(4, icon_col)

    agg_dict: dict[str, object] = {
        "rank": pd.NamedAgg(column="rank", aggfunc="min"),
        "installs_d30": pd.NamedAgg(column="installs_d30", aggfunc="max"),
        "tag_sources": pd.NamedAgg(
            column="tag_source",
            aggfunc=lambda values: {
                str(value) for value in values.tolist() if pd.notna(value)
            },
        ),
    }
    if is_removed_col:
        agg_dict["is_removed"] = pd.NamedAgg(column="is_removed", aggfunc="first")
    if country_col:
        agg_dict["country"] = pd.NamedAgg(column="country", aggfunc="first")

    grouped = (
        app_changes_df.groupby(groupby_cols, dropna=False).agg(**agg_dict).reset_index()  # type: ignore[arg-type]
    )

    grouped["sdk"] = grouped["tag_sources"].apply(lambda values: "sdk" in values)
    grouped["api_call"] = grouped["tag_sources"].apply(
        lambda values: "api_call" in values
    )
    grouped["app_ads_direct"] = grouped["tag_sources"].apply(
        lambda values: "app_ads_direct" in values
    )
    grouped["publisher"] = False
    grouped = grouped.drop(columns=["tag_sources"])
    grouped = grouped.sort_values(
        by=["installs_d30", "name"],
        ascending=[False, True],
        na_position="last",
    ).head(limit)
    if icon_col != "icon_64":
        grouped = grouped.rename(columns={icon_col: "icon_64"})
    return grouped


def build_company_app_changes_payload(
    state: State,
    company_domain: str,
    status: str,
    *,
    year: int | None = None,
    quarter: int | None = None,
    limit: int = COMPANY_APP_CHANGES_LIMIT,
    tag_sources: tuple[str, ...] | None = None,
) -> CompanyAppChangesOverview:
    """Build frontend company app-change payloads for the latest or requested quarter."""
    resolved_year, resolved_quarter = _resolve_company_app_changes_period(
        state=state,
        company_domain=company_domain,
        year=year,
        quarter=quarter,
    )
    sources = tag_sources if tag_sources is not None else COMPANY_APP_CHANGE_TAG_SOURCES
    raw_frames = [
        get_company_app_changes(
            state=state,
            company_domain=company_domain,
            tag_source=tag_source,
            year=resolved_year,
            quarter=resolved_quarter,
            status=status,
        )
        for tag_source in sources
    ]
    non_empty_frames = [frame for frame in raw_frames if not frame.empty]
    collapsed_df = _shape_company_app_changes_df(
        (
            pd.concat(non_empty_frames, ignore_index=True)
            if non_empty_frames
            else pd.DataFrame()
        ),
        limit=limit,
    )

    android_df = collapsed_df[
        collapsed_df["store"].astype(str).str.startswith("Google")
    ]
    ios_df = collapsed_df[~collapsed_df["store"].astype(str).str.startswith("Google")]

    return CompanyAppChangesOverview(
        status=status,
        year=resolved_year,
        quarter=resolved_quarter,
        android=AppGroup(
            apps=android_df.to_dict(orient="records"),
            title=company_domain,
        ),
        ios=AppGroup(
            apps=ios_df.to_dict(orient="records"),
            title=company_domain,
        ),
    )


def get_company_app_change_store_ids(
    state: State,
    company_domain: str,
    tag_source: str,
    year: int,
    quarter: int,
    status: str,
) -> list[str]:
    """Return ordered store IDs for a single company/tag-source/status quarter slice."""
    df = get_company_app_changes(
        state=state,
        company_domain=company_domain,
        tag_source=tag_source,
        year=year,
        quarter=quarter,
        status=status,
    )
    if df.empty:
        return []

    df = df.sort_values(
        by=["installs_d30", "name"],
        ascending=[False, True],
        na_position="last",
    )
    return df["store_id"].dropna().astype(str).drop_duplicates().tolist()


def get_company_app_change_store_ids_by_platform(
    state: State,
    company_domain: str,
    tag_source: str,
    year: int,
    quarter: int,
    status: str,
) -> dict[str, list[str]]:
    """Return ordered store IDs split into Android and iOS lists."""
    df = get_company_app_changes(
        state=state,
        company_domain=company_domain,
        tag_source=tag_source,
        year=year,
        quarter=quarter,
        status=status,
    )
    if df.empty:
        return {"android_apps": [], "ios_apps": []}

    df = df.sort_values(
        by=["installs_d30", "name"],
        ascending=[False, True],
        na_position="last",
    )
    android_df = df[df["store"].astype(str).str.startswith("Google")]
    ios_df = df[~df["store"].astype(str).str.startswith("Google")]
    return {
        "android_apps": (
            android_df["store_id"].dropna().astype(str).drop_duplicates().tolist()
        ),
        "ios_apps": ios_df["store_id"].dropna().astype(str).drop_duplicates().tolist(),
    }


def top_companies_by_tag_source(top_df: pd.DataFrame) -> TopCompaniesShort:
    """Make top companies short."""

    def process_top_df(
        df: pd.DataFrame, tag_source: str, store_pattern: str
    ) -> pd.DataFrame:
        """Process dataframe for a specific tag source and store pattern."""
        return (
            df[
                (df["tag_source"] == tag_source)
                & (df["store"].str.contains(store_pattern))
            ]
            .copy()
            .rename(columns={"company_name": "group", "app_count": "value"})
            .sort_values(by=["value"], ascending=True)
        )

    top_ios_sdk_df = process_top_df(top_df, "sdk", "Apple")
    top_android_sdk_df = process_top_df(top_df, "sdk", "Google")
    top_ios_pub_df = process_top_df(top_df, "publisher", "Apple")
    top_android_pub_df = process_top_df(top_df, "publisher", "Google")
    top_ios_adstxt_direct_df = process_top_df(top_df, "app_ads_direct", "Apple")
    top_android_adstxt_direct_df = process_top_df(top_df, "app_ads_direct", "Google")

    top_companies_short = TopCompaniesShort(
        sdk_ios=top_ios_sdk_df.to_dict(orient="records"),
        sdk_android=top_android_sdk_df.to_dict(orient="records"),
        pub_ios=top_ios_pub_df.to_dict(orient="records"),
        pub_android=top_android_pub_df.to_dict(orient="records"),
        adstxt_direct_ios=top_ios_adstxt_direct_df.to_dict(orient="records"),
        adstxt_direct_android=top_android_adstxt_direct_df.to_dict(orient="records"),
    )
    return top_companies_short


def prep_companies_overview_df(
    state: State,
    overview_df: pd.DataFrame,
    *,
    include_trends_overview: bool = True,
    type_slug: str | None = None,
) -> pd.DataFrame:
    """Prep companies overview dataframe."""
    overview_df = (
        overview_df.groupby(
            [
                "company_name",
                "company_domain",
                "parent_company_domain",
                "parent_company_name",
                "store",
                "tag_source",
            ],
            dropna=False,
        )[["app_count", "cat_total_app_count", "installs_d30"]]
        .sum()
        .reset_index()
    )

    total_app_count_df = (
        overview_df.groupby(
            [
                "company_name",
                "company_domain",
                "parent_company_domain",
                "parent_company_name",
            ],
            dropna=False,
        )[["app_count"]]
        .sum()
        .reset_index()
        .rename(columns={"app_count": "total_app_count"})
    )
    total_installs_d30_df = (
        overview_df.groupby(
            [
                "company_name",
                "company_domain",
                "parent_company_domain",
                "parent_company_name",
            ],
            dropna=False,
        )[["installs_d30"]]
        .sum()
        .reset_index()
        .rename(columns={"installs_d30": "installs_d30"})
    )

    overview_df["percentage"] = (
        overview_df["app_count"] / overview_df["cat_total_app_count"]
    )
    overview_df["store_tag"] = np.where(
        overview_df["store"].str.contains("Google"),
        "google",
        "apple",
    )
    overview_df["store_tag_source"] = (
        overview_df["store_tag"] + "_" + overview_df["tag_source"]
    )

    # Per-store totals (across all tag sources) for app-publishers view
    store_totals_df = (
        overview_df.groupby(
            [
                "company_name",
                "company_domain",
                "parent_company_domain",
                "parent_company_name",
                "store_tag",
            ],
            dropna=False,
        )[["app_count", "installs_d30"]]
        .sum()
        .reset_index()
    )
    store_totals_pivoted = store_totals_df.pivot(
        index=[
            "company_name",
            "company_domain",
            "parent_company_domain",
            "parent_company_name",
        ],
        columns=["store_tag"],
        values=["app_count", "installs_d30"],
    )
    store_totals_pivoted.columns = [
        f"{col[1]}_{col[0]}" for col in store_totals_pivoted.columns
    ]
    store_totals_pivoted = store_totals_pivoted.reset_index()

    # NOTE: Crucial for SDK to be first
    # since it has more than just advertising data
    store_tag_source_cols = [
        f"{x}_percentage" for x in overview_df["store_tag_source"].unique().tolist()
    ]
    sdk_cols = [x for x in store_tag_source_cols if "sdk" in x]
    adstxt_cols = [x for x in store_tag_source_cols if "app_ads" in x]
    adstxt_direct_cols = [x for x in adstxt_cols if "direct" in x]
    publisher_cols = [x for x in adstxt_cols if "publisher" in x]

    pivoted_df = overview_df.pivot(
        index=[
            "company_name",
            "company_domain",
            "parent_company_domain",
            "parent_company_name",
        ],
        columns=["store_tag_source"],
        values=["app_count", "percentage", "installs_d30"],
    )

    # Flatten the multi-level columns so each source has raw app counts alongside
    # the existing market share and installs aggregates.
    pivoted_df.columns = [f"{col[1]}_{col[0]}" for col in pivoted_df.columns]
    overview_df = pivoted_df.reset_index()
    overview_df = overview_df.merge(
        total_app_count_df,
        on=[
            "company_name",
            "company_domain",
            "parent_company_domain",
            "parent_company_name",
        ],
        how="left",
        validate="1:1",
    )
    overview_df = overview_df.merge(
        total_installs_d30_df,
        on=[
            "company_name",
            "company_domain",
            "parent_company_domain",
            "parent_company_name",
        ],
        how="left",
        validate="1:1",
    )
    overview_df = overview_df.merge(
        store_totals_pivoted,
        on=[
            "company_name",
            "company_domain",
            "parent_company_domain",
            "parent_company_name",
        ],
        how="left",
        validate="1:1",
    )

    if type_slug == "app-publishers":
        overview_df["tempsort"] = overview_df[["installs_d30"]].fillna(0).sum(axis=1)
    else:
        overview_df["tempsort"] = (
            overview_df[sdk_cols + adstxt_direct_cols].fillna(0).mean(axis=1)
        )

    overview_df = (
        overview_df.sort_values(
            by="tempsort",
            ascending=False,
        )
        .drop(columns=["tempsort"])
        .head(1000)
    )
    open_source_df = get_company_open_source(state)
    overview_df = overview_df.merge(
        open_source_df, on="company_domain", how="left", validate="m:1"
    )
    overview_df["percent_open_source"] = overview_df["percent_open_source"].fillna(0)

    countries_df = get_company_countries(state)
    overview_df = overview_df.merge(
        countries_df, on="company_domain", how="left", validate="m:1"
    )
    # Coalesce HQ country first, fall back to IP-resolved country
    overview_df["country"] = overview_df["hq_country"].fillna(
        overview_df["api_ip_resolved_country"]
    )

    company_logos_df = get_company_logos_df(state)
    overview_df = overview_df.merge(
        company_logos_df,
        on="company_domain",
        how="left",
        validate="1:1",
    )
    parent_company_logos_df = company_logos_df.rename(
        columns={
            "company_domain": "parent_company_domain",
            "company_logo_url": "parent_company_logo_url",
        }
    )
    overview_df = overview_df.merge(
        parent_company_logos_df,
        on="parent_company_domain",
        how="left",
        validate="m:1",
    )
    company_categories_df = (
        _get_normalized_company_categories(state)
        .dropna(subset=["company_domain", "company_type"])
        .drop_duplicates(subset=["company_domain"], keep="first")
        .rename(columns={"company_type": "company_category"})[
            ["company_domain", "company_category"]
        ]
    )
    overview_df = overview_df.merge(
        company_categories_df,
        on="company_domain",
        how="left",
        validate="1:1",
    )

    if include_trends_overview:
        company_trends_overview_df = get_company_trends_overview(state)
        # TODO: The trends can have different values due to parent vs not parent grouping
        # Trends currently have no parent grouping
        # companies overview_df does have parent grouping
        tcols = company_trends_overview_df.columns
        if not company_trends_overview_df.empty:
            overview_df = overview_df.merge(
                company_trends_overview_df,
                on="company_domain",
                how="left",
                validate="1:1",
            )
    return overview_df


def get_overviews(
    state: State,
    category: str | None = None,
    type_slug: str | None = None,
) -> CompaniesOverview:
    """Get the overview data from the database."""
    company_logos_df = get_company_logos_df(state).drop_duplicates(
        subset=["company_domain"], keep="first"
    )

    # Get Top 5 Companies for Plots
    top_df = get_companies_top(
        state=state, type_slug=type_slug, category=category, limit=5
    )
    top_df = top_df.merge(
        company_logos_df,
        on="company_domain",
        how="left",
        validate="m:1",
    )
    top_companies_short = top_companies_by_tag_source(top_df)

    if type_slug:
        companies_df = get_companies_type_stats(
            state=state, type_slug=type_slug, category=category
        )
        category_app_counts = get_category_type_stats(
            state, type_slug=type_slug, category=category
        )
        # Type-filtered path already returns all companies (no limit)
        company_counts = None
    else:
        companies_df = get_companies_stats(state, app_category=category)
        category_app_counts = get_tag_source_category_totals(
            state, app_category=category
        )
        # Get real company counts without the top-1000 cutoff
        company_counts = get_tag_source_company_counts(state, app_category=category)

    companies_df = companies_df.merge(
        category_app_counts,
        on=["app_category", "store", "tag_source"],
        validate="m:1",
    )

    category_overview_stats = make_companies_stats(
        df=companies_df.copy(),
        tag_source_category_app_counts=category_app_counts,
        tag_source_company_counts=company_counts,
    )

    companies_df = prep_companies_overview_df(
        state,
        companies_df,
        include_trends_overview=category is None,
        type_slug=type_slug,
    )

    # Fetch country distribution stats when viewing a type
    country_stats: list[dict[str, object]] = []
    if type_slug:
        country_df = get_company_type_country_stats(
            state=state, type_url_slug=type_slug, app_category=category
        )
        if not country_df.empty:
            country_stats = country_df.to_dict(orient="records")

    results = CompaniesOverview(
        companies_overview=companies_df.to_dict(orient="records"),
        top=top_companies_short,
        categories=category_overview_stats,
        country_stats=country_stats,
    )

    return results


def get_company_directory(state: State) -> list[CompanyDirectoryEntry]:
    """Build a slim company directory payload for selectors and cached lookups."""
    companies_df = get_company_directory_df(state)
    if companies_df.empty:
        return []

    return [
        CompanyDirectoryEntry(
            name=str(row.name),
            company_id=int(row.company_id),
        )
        for row in companies_df.itertuples(index=False)
    ]


def append_overall_categories(df: pd.DataFrame) -> pd.DataFrame:
    """Add single row for overall category."""
    metrics = ["installs", "app_count", "ratings"]
    total_cols = ["total_ratings", "total_installs", "category_total_apps"]
    overall_totals = (
        df.groupby(["store", "mapped_category"])[total_cols]
        .first()
        .reset_index()
        .groupby(["store"])[total_cols]
        .sum()
    )
    overall_company_df = df.groupby(["store", "name"])[metrics].sum().reset_index()
    overall_df = overall_company_df.merge(
        overall_totals,
        how="left",
        on="store",
        validate="m:1",
    )
    overall_df["mapped_category"] = "overall"
    df = pd.concat([df, overall_df])
    """Append a consolidated games category.
    note this wouldn't work for Apple as not needed.
    """
    games_cat_df = (
        df.loc[(df["mapped_category"].str.contains(r"^game"))]
        .groupby(["store", "name"])[metrics + total_cols]
        .sum()
        .reset_index()
    )
    games_cat_df["mapped_category"] = "games"
    df = pd.concat([df, games_cat_df])
    return df


def make_companies_stats(
    df: pd.DataFrame,
    tag_source_category_app_counts: pd.DataFrame,
    tag_source_company_counts: pd.DataFrame | None = None,
) -> CompaniesCategoryOverview:
    """Make category sums for multiple companies overview."""
    overview = CompaniesCategoryOverview()

    # Precompute boolean masks
    df_is_apple = df["store"].str.contains("Apple")
    df_is_google = df["store"].str.contains("Google")
    df_is_sdk = df["tag_source"] == "sdk"
    df_is_api_call = df["tag_source"] == "api_call"
    df_is_app_ads_reseller = df["tag_source"] == "app_ads_reseller"
    df_is_app_ads_direct = df["tag_source"] == "app_ads_direct"

    # Use real company counts from a separate query (no top-1000 cutoff)
    # Falls back to nunique on the limited df if not provided.
    def _company_count(
        store_mask: pd.Series, tag_mask: pd.Series, store_label: str, tag_label: str
    ) -> int:
        if tag_source_company_counts is not None:
            mask = (tag_source_company_counts["store"] == store_label) & (
                tag_source_company_counts["tag_source"] == tag_label
            )
            vals = tag_source_company_counts.loc[mask, "company_count"]
            return int(vals.sum()) if not vals.empty else 0
        return int(df.loc[store_mask & tag_mask, "company_domain"].nunique())

    # Calculate overall stats
    overall_stats = {
        "total_companies": (
            int(tag_source_company_counts["company_count"].sum())
            if tag_source_company_counts is not None
            else df["company_domain"].nunique()
        ),
        "sdk_ios_total_companies": _company_count(
            df_is_apple, df_is_sdk, "Apple App Store", "sdk"
        ),
        "sdk_android_total_companies": _company_count(
            df_is_google, df_is_sdk, "Google Play", "sdk"
        ),
        "adstxt_direct_ios_total_companies": _company_count(
            df_is_apple, df_is_app_ads_direct, "Apple App Store", "app_ads_direct"
        ),
        "adstxt_direct_android_total_companies": _company_count(
            df_is_google, df_is_app_ads_direct, "Google Play", "app_ads_direct"
        ),
        "adstxt_reseller_ios_total_companies": _company_count(
            df_is_apple, df_is_app_ads_reseller, "Apple App Store", "app_ads_reseller"
        ),
        "adstxt_reseller_android_total_companies": _company_count(
            df_is_google, df_is_app_ads_reseller, "Google Play", "app_ads_reseller"
        ),
        "api_android_total_companies": _company_count(
            df_is_google, df_is_api_call, "Google Play", "api_call"
        ),
        "api_ios_total_companies": _company_count(
            df_is_apple, df_is_api_call, "Apple App Store", "api_call"
        ),
    }

    tag_source_category_app_counts_is_apple = tag_source_category_app_counts[
        "store"
    ].str.contains("Apple")
    tag_source_category_app_counts_is_google = tag_source_category_app_counts[
        "store"
    ].str.contains("Google")
    tag_source_category_app_counts_is_sdk = (
        tag_source_category_app_counts["tag_source"] == "sdk"
    )
    tag_source_category_app_counts_is_app_ads_reseller = (
        tag_source_category_app_counts["tag_source"] == "app_ads_reseller"
    )
    tag_source_category_app_counts_is_app_ads_direct = (
        tag_source_category_app_counts["tag_source"] == "app_ads_direct"
    )
    tag_source_category_app_counts_is_api_call = (
        tag_source_category_app_counts["tag_source"] == "api_call"
    )

    sdk_app_counts = {
        "sdk_total_apps": int(
            tag_source_category_app_counts[tag_source_category_app_counts_is_sdk][
                "cat_total_app_count"
            ].sum()
        ),
        # This is the unique total across all company types
    }
    sdk_app_counts.update(
        {
            "sdk_android_total_apps": int(
                tag_source_category_app_counts[
                    tag_source_category_app_counts_is_sdk
                    & tag_source_category_app_counts_is_google
                ]["cat_total_app_count"].sum()
            ),
            "sdk_ios_total_apps": int(
                tag_source_category_app_counts[
                    tag_source_category_app_counts_is_sdk
                    & tag_source_category_app_counts_is_apple
                ]["cat_total_app_count"].sum()
            ),
            "sdk_android_installs_d30": int(
                tag_source_category_app_counts[
                    tag_source_category_app_counts_is_sdk
                    & tag_source_category_app_counts_is_google
                ]["cat_total_installs_d30"].sum()
            ),
            "sdk_ios_installs_d30": int(
                tag_source_category_app_counts[
                    tag_source_category_app_counts_is_sdk
                    & tag_source_category_app_counts_is_apple
                ]["cat_total_installs_d30"].sum()
            ),
        }
    )

    # --- api_call app counts ---
    api_app_counts = {
        "api_total_apps": int(
            tag_source_category_app_counts[tag_source_category_app_counts_is_api_call][
                "cat_total_app_count"
            ].sum()
        ),
        "api_android_total_apps": int(
            tag_source_category_app_counts[
                tag_source_category_app_counts_is_api_call
                & tag_source_category_app_counts_is_google
            ]["cat_total_app_count"].sum()
        ),
        "api_android_installs_d30": int(
            tag_source_category_app_counts[
                tag_source_category_app_counts_is_api_call
                & tag_source_category_app_counts_is_google
            ]["cat_total_installs_d30"].sum()
        ),
    }
    # api_ios_total_apps — only SDK columns exist in cat totals, not api_call iOS
    api_app_counts["api_ios_total_apps"] = 0

    # --- app_ads_direct app counts ---
    adstxt_direct_app_counts = {
        "adstxt_direct_total_apps": int(
            tag_source_category_app_counts[
                tag_source_category_app_counts_is_app_ads_direct
            ]["cat_total_app_count"].sum()
        ),
        "adstxt_direct_android_total_apps": int(
            tag_source_category_app_counts[
                tag_source_category_app_counts_is_app_ads_direct
                & tag_source_category_app_counts_is_google
            ]["cat_total_app_count"].sum()
        ),
        "adstxt_direct_ios_total_apps": int(
            tag_source_category_app_counts[
                tag_source_category_app_counts_is_app_ads_direct
                & tag_source_category_app_counts_is_apple
            ]["cat_total_app_count"].sum()
        ),
        "adstxt_direct_android_installs_d30": int(
            tag_source_category_app_counts[
                tag_source_category_app_counts_is_app_ads_direct
                & tag_source_category_app_counts_is_google
            ]["cat_total_installs_d30"].sum()
        ),
    }

    # --- app_ads_reseller app counts ---
    adstxt_reseller_app_counts = {
        "adstxt_reseller_total_apps": int(
            tag_source_category_app_counts[
                tag_source_category_app_counts_is_app_ads_reseller
            ]["cat_total_app_count"].sum()
        ),
        "adstxt_reseller_android_total_apps": int(
            tag_source_category_app_counts[
                tag_source_category_app_counts_is_app_ads_reseller
                & tag_source_category_app_counts_is_google
            ]["cat_total_app_count"].sum()
        ),
        "adstxt_reseller_ios_total_apps": int(
            tag_source_category_app_counts[
                tag_source_category_app_counts_is_app_ads_reseller
                & tag_source_category_app_counts_is_apple
            ]["cat_total_app_count"].sum()
        ),
        "adstxt_reseller_android_installs_d30": int(
            tag_source_category_app_counts[
                tag_source_category_app_counts_is_app_ads_reseller
                & tag_source_category_app_counts_is_google
            ]["cat_total_installs_d30"].sum()
        ),
    }

    # Per-store totals (across all tag sources) for app-publishers-like views
    store_company_count = {}
    for store_label, store_mask in [("android", df_is_google), ("ios", df_is_apple)]:
        if tag_source_company_counts is not None:
            mask = tag_source_company_counts["store"].str.contains(
                "Google" if store_label == "android" else "Apple", na=False
            )
            store_company_count[store_label] = int(
                tag_source_company_counts.loc[mask, "company_count"].sum()
            )
        else:
            store_company_count[store_label] = int(
                df.loc[store_mask, "company_domain"].nunique()
            )

    store_totals = {
        "android_total_apps": int(
            tag_source_category_app_counts.loc[
                tag_source_category_app_counts_is_google, "cat_total_app_count"
            ].sum()
        ),
        "ios_total_apps": int(
            tag_source_category_app_counts.loc[
                tag_source_category_app_counts_is_apple, "cat_total_app_count"
            ].sum()
        ),
        "android_total_companies": store_company_count["android"],
        "ios_total_companies": store_company_count["ios"],
    }

    overview.update_stats("all", **overall_stats)
    overview.update_stats("all", **sdk_app_counts)
    overview.update_stats("all", **api_app_counts)
    overview.update_stats("all", **adstxt_direct_app_counts)
    overview.update_stats("all", **adstxt_reseller_app_counts)
    overview.update_stats("all", **store_totals)

    return overview


def make_company_stats(
    df: pd.DataFrame,
    category_totals: pd.DataFrame | None = None,
) -> CompanyCategoryOverview:
    """Make stats for a single company.

    Parameters
    ----------
    df : pd.DataFrame
        Company-specific tag stats with columns: app_count, installs_d30, etc.
    category_totals : pd.DataFrame, optional
        Category-wide totals from :func:`get_tag_source_category_totals`.
        Must contain columns: cat_total_app_count, cat_total_installs_d30,
        cat_active_apps_universe, cat_universe_installs_d30, store, tag_source.
        Used to compute market share / penetration metrics.

    """
    overview = CompanyCategoryOverview()
    if df.empty:
        return overview
    conditions = {
        "sdk_ios": (df["store"].str.contains("Apple")) & (df["tag_source"] == "sdk"),
        "sdk_android": (df["store"].str.contains("Google"))
        & (df["tag_source"] == "sdk"),
        "api_android": (df["store"].str.contains("Google"))
        & (df["tag_source"] == "api_call"),
        "api_ios": (df["store"].str.contains("Apple"))
        & (df["tag_source"] == "api_call"),
        "adstxt_direct_ios": (df["store"].str.contains("Apple"))
        & (df["tag_source"] == "app_ads_direct"),
        "adstxt_direct_android": (df["store"].str.contains("Google"))
        & (df["tag_source"] == "app_ads_direct"),
        "adstxt_reseller_ios": (df["store"].str.contains("Apple"))
        & (df["tag_source"] == "app_ads_reseller"),
        "adstxt_reseller_android": (df["store"].str.contains("Google"))
        & (df["tag_source"] == "app_ads_reseller"),
    }

    # Calculate sums for all conditions in one go
    res_app_counts = {
        key: df.loc[condition, "app_count"].sum()
        for key, condition in conditions.items()
    }

    res_installs_d30 = {
        key: df.loc[condition, "installs_d30"].sum()
        for key, condition in conditions.items()
    }

    # Unpack results
    (
        sdk_ios_total_apps,
        sdk_android_total_apps,
        api_ios_total_apps,
        api_android_total_apps,
        adstxt_direct_ios_total_apps,
        adstxt_direct_android_total_apps,
        adstxt_reseller_ios_total_apps,
        adstxt_reseller_android_total_apps,
    ) = (
        res_app_counts["sdk_ios"],
        res_app_counts["sdk_android"],
        res_app_counts["api_ios"],
        res_app_counts["api_android"],
        res_app_counts["adstxt_direct_ios"],
        res_app_counts["adstxt_direct_android"],
        res_app_counts["adstxt_reseller_ios"],
        res_app_counts["adstxt_reseller_android"],
    )

    (
        sdk_ios_installs_d30,
        sdk_android_installs_d30,
        api_android_installs_d30,
        adstxt_direct_android_installs_d30,
        adstxt_reseller_android_installs_d30,
    ) = (
        res_installs_d30["sdk_ios"],
        res_installs_d30["sdk_android"],
        res_installs_d30["api_android"],
        res_installs_d30["adstxt_direct_android"],
        res_installs_d30["adstxt_reseller_android"],
    )

    sdk_total_apps = sdk_ios_total_apps + sdk_android_total_apps
    api_total_apps = api_ios_total_apps + api_android_total_apps
    total_apps = (
        sdk_total_apps
        + api_total_apps
        + adstxt_direct_ios_total_apps
        + adstxt_direct_android_total_apps
        + adstxt_reseller_ios_total_apps
        + adstxt_reseller_android_total_apps
    )

    # Extract category-wide totals (sum across all companies) for market share denominators.
    # The category_totals DataFrame has cat_total_app_count and cat_total_installs_d30
    # which are the total_active_scanned_apps_with_tag and total_scanned_installs_d30_with_tag
    # summed across all companies for each store+tag_source+category.
    if category_totals is not None and not category_totals.empty:
        # When a specific category is requested, category_totals has per-category rows.
        # Sum across all rows to get the universe-wide total for that category.
        # Also works when no category filter is applied (app_category == "all").
        def _get_cat_total_val(store_pattern: str, tag_src: str, col: str) -> int:
            mask = category_totals["store"].str.contains(store_pattern, na=False) & (
                category_totals["tag_source"] == tag_src
            )
            vals = category_totals.loc[mask, col]
            return int(vals.sum()) if not vals.empty else 0

        sdk_android_universe_apps = _get_cat_total_val(
            "Google", "sdk", "cat_total_app_count"
        )
        sdk_ios_universe_apps = _get_cat_total_val(
            "Apple", "sdk", "cat_total_app_count"
        )
        sdk_android_universe_installs_d30 = _get_cat_total_val(
            "Google", "sdk", "cat_total_installs_d30"
        )
        sdk_ios_universe_installs_d30 = _get_cat_total_val(
            "Apple", "sdk", "cat_total_installs_d30"
        )
        api_android_universe_apps = _get_cat_total_val(
            "Google", "api_call", "cat_total_app_count"
        )
        api_ios_universe_apps = _get_cat_total_val(
            "Apple", "api_call", "cat_total_app_count"
        )
        api_android_universe_installs_d30 = _get_cat_total_val(
            "Google", "api_call", "cat_total_installs_d30"
        )
    else:
        sdk_android_universe_apps = 0
        sdk_ios_universe_apps = 0
        sdk_android_universe_installs_d30 = 0
        sdk_ios_universe_installs_d30 = 0
        api_android_universe_apps = 0
        api_ios_universe_apps = 0
        api_android_universe_installs_d30 = 0

    overview.update_stats(
        "all",
        total_apps=int(total_apps),
        adstxt_direct_ios_total_apps=int(adstxt_direct_ios_total_apps),
        adstxt_direct_android_total_apps=int(adstxt_direct_android_total_apps),
        adstxt_reseller_ios_total_apps=int(adstxt_reseller_ios_total_apps),
        adstxt_reseller_android_total_apps=int(adstxt_reseller_android_total_apps),
        sdk_ios_total_apps=int(sdk_ios_total_apps),
        sdk_android_total_apps=int(sdk_android_total_apps),
        sdk_total_apps=int(sdk_total_apps),
        sdk_android_installs_d30=int(sdk_android_installs_d30),
        sdk_ios_installs_d30=int(sdk_ios_installs_d30),
        api_ios_total_apps=int(api_ios_total_apps),
        api_android_total_apps=int(api_android_total_apps),
        api_total_apps=int(api_total_apps),
        adstxt_direct_android_installs_d30=int(adstxt_direct_android_installs_d30),
        adstxt_reseller_android_installs_d30=int(adstxt_reseller_android_installs_d30),
        api_android_installs_d30=int(api_android_installs_d30),
        sdk_android_universe_apps=int(sdk_android_universe_apps),
        sdk_ios_universe_apps=int(sdk_ios_universe_apps),
        sdk_android_universe_installs_d30=int(sdk_android_universe_installs_d30),
        sdk_ios_universe_installs_d30=int(sdk_ios_universe_installs_d30),
        api_android_universe_apps=int(api_android_universe_apps),
        api_ios_universe_apps=int(api_ios_universe_apps),
        api_android_universe_installs_d30=int(api_android_universe_installs_d30),
    )
    cats = df.app_category.unique().tolist()
    for cat in cats:
        conditions = {
            "sdk_ios": (df["store"].str.contains("Apple"))
            & (df["tag_source"] == "sdk")
            & (df["app_category"] == cat),
            "sdk_android": (df["store"].str.contains("Google"))
            & (df["tag_source"] == "sdk")
            & (df["app_category"] == cat),
            "api_ios": (df["store"].str.contains("Apple"))
            & (df["tag_source"] == "api_call")
            & (df["app_category"] == cat),
            "api_android": (df["store"].str.contains("Google"))
            & (df["tag_source"] == "api_call")
            & (df["app_category"] == cat),
            "adstxt_direct_ios": (df["store"].str.contains("Apple"))
            & (df["tag_source"] == "app_ads_direct")
            & (df["app_category"] == cat),
            "adstxt_direct_android": (df["store"].str.contains("Google"))
            & (df["tag_source"] == "app_ads_direct")
            & (df["app_category"] == cat),
            "adstxt_reseller_ios": (df["store"].str.contains("Apple"))
            & (df["tag_source"] == "app_ads_reseller")
            & (df["app_category"] == cat),
            "adstxt_reseller_android": (df["store"].str.contains("Google"))
            & (df["tag_source"] == "app_ads_reseller")
            & (df["app_category"] == cat),
        }

        # Calculate sums for all conditions in one go
        res_app_counts = {
            key: df.loc[condition, "app_count"].sum()
            for key, condition in conditions.items()
        }
        res_installs_d30 = {
            key: df.loc[condition, "installs_d30"].sum()
            for key, condition in conditions.items()
        }

        # Unpack results
        (
            sdk_ios_total_apps,
            sdk_android_total_apps,
            api_ios_total_apps,
            api_android_total_apps,
            adstxt_direct_ios_total_apps,
            adstxt_direct_android_total_apps,
            adstxt_reseller_ios_total_apps,
            adstxt_reseller_android_total_apps,
        ) = (
            res_app_counts["sdk_ios"],
            res_app_counts["sdk_android"],
            res_app_counts["api_ios"],
            res_app_counts["api_android"],
            res_app_counts["adstxt_direct_ios"],
            res_app_counts["adstxt_direct_android"],
            res_app_counts["adstxt_reseller_ios"],
            res_app_counts["adstxt_reseller_android"],
        )

        (
            sdk_android_installs_d30,
            api_android_installs_d30,
            adstxt_direct_android_installs_d30,
            adstxt_reseller_android_installs_d30,
        ) = (
            res_installs_d30["sdk_android"],
            res_installs_d30["api_android"],
            res_installs_d30["adstxt_direct_android"],
            res_installs_d30["adstxt_reseller_android"],
        )

        sdk_total_apps = sdk_ios_total_apps + sdk_android_total_apps
        api_total_apps = api_ios_total_apps + api_android_total_apps
        total_apps = (
            sdk_total_apps
            + adstxt_direct_ios_total_apps
            + adstxt_direct_android_total_apps
            + adstxt_reseller_ios_total_apps
            + adstxt_reseller_android_total_apps
        )

        # For per-category stats, look up per-category universe data if available
        if category_totals is not None and not category_totals.empty:
            # If category_totals has a row for this specific category, use it.
            # Otherwise fall back to the "all" row (which is used when the main
            # overview was built without a category filter).
            cat_mask = category_totals["app_category"] == cat
            if not cat_mask.any():
                cat_mask = category_totals["app_category"] == "all"
            cat_totals_row = category_totals[cat_mask]

            def _cat_total_val(store_pattern: str, tag_src: str, col: str) -> int:
                mask = cat_totals_row["store"].str.contains(store_pattern, na=False) & (
                    cat_totals_row["tag_source"] == tag_src
                )
                vals = cat_totals_row.loc[mask, col]
                return int(vals.sum()) if not vals.empty else 0

            cat_sdk_android_universe_apps = _cat_total_val(
                "Google", "sdk", "cat_total_app_count"
            )
            cat_sdk_ios_universe_apps = _cat_total_val(
                "Apple", "sdk", "cat_total_app_count"
            )
            cat_sdk_android_universe_installs_d30 = _cat_total_val(
                "Google", "sdk", "cat_total_installs_d30"
            )
            cat_sdk_ios_universe_installs_d30 = _cat_total_val(
                "Apple", "sdk", "cat_total_installs_d30"
            )
            cat_api_android_universe_apps = _cat_total_val(
                "Google", "api_call", "cat_total_app_count"
            )
            cat_api_ios_universe_apps = _cat_total_val(
                "Apple", "api_call", "cat_total_app_count"
            )
            cat_api_android_universe_installs_d30 = _cat_total_val(
                "Google", "api_call", "cat_total_installs_d30"
            )
        else:
            cat_sdk_android_universe_apps = 0
            cat_sdk_ios_universe_apps = 0
            cat_sdk_android_universe_installs_d30 = 0
            cat_sdk_ios_universe_installs_d30 = 0
            cat_api_android_universe_apps = 0
            cat_api_ios_universe_apps = 0
            cat_api_android_universe_installs_d30 = 0

        overview.update_stats(
            cat,
            total_apps=int(total_apps),
            adstxt_direct_ios_total_apps=int(adstxt_direct_ios_total_apps),
            adstxt_direct_android_total_apps=int(adstxt_direct_android_total_apps),
            adstxt_reseller_ios_total_apps=int(adstxt_reseller_ios_total_apps),
            adstxt_reseller_android_total_apps=int(adstxt_reseller_android_total_apps),
            sdk_ios_total_apps=int(sdk_ios_total_apps),
            sdk_android_total_apps=int(sdk_android_total_apps),
            sdk_total_apps=int(sdk_total_apps),
            api_ios_total_apps=int(api_ios_total_apps),
            api_android_total_apps=int(api_android_total_apps),
            api_total_apps=int(api_total_apps),
            sdk_android_installs_d30=int(sdk_android_installs_d30),
            api_android_installs_d30=int(api_android_installs_d30),
            adstxt_direct_android_installs_d30=int(adstxt_direct_android_installs_d30),
            adstxt_reseller_android_installs_d30=int(
                adstxt_reseller_android_installs_d30
            ),
            sdk_android_universe_apps=int(cat_sdk_android_universe_apps),
            sdk_ios_universe_apps=int(cat_sdk_ios_universe_apps),
            sdk_android_universe_installs_d30=int(
                cat_sdk_android_universe_installs_d30
            ),
            sdk_ios_universe_installs_d30=int(cat_sdk_ios_universe_installs_d30),
            api_android_universe_apps=int(cat_api_android_universe_apps),
            api_ios_universe_apps=int(cat_api_ios_universe_apps),
            api_android_universe_installs_d30=int(
                cat_api_android_universe_installs_d30
            ),
        )
    return overview


def get_count(df: pd.DataFrame, condition: pd.Series, column: str) -> int:
    """Safely get count from filtered DataFrame."""
    filtered = df[condition][column]
    return int(filtered.iloc[0]) if not filtered.empty else 0


def _get_normalized_company_categories(state: State) -> pd.DataFrame:
    """Return company categories with mediation rows removed."""
    company_categories = get_company_categories(state)
    return company_categories.loc[
        company_categories["company_type_slug"] != "mediation"
    ].copy()


def get_company_types_for_domain(state: State, company_domain: str) -> list[str]:
    """Get company category slugs for a domain, resolving secondary domains."""
    company_categories = get_company_categories(state)
    matching_rows = company_categories[
        company_categories["company_domain"] == company_domain
    ]

    if matching_rows.empty:
        tree_df = get_company_tree_base(state=state, queried_domain=company_domain)
        if not tree_df.empty and pd.notna(tree_df.iloc[0]["company_domain"]):
            canonical_domain = str(tree_df.iloc[0]["company_domain"])
            matching_rows = company_categories[
                company_categories["company_domain"] == canonical_domain
            ]

    if matching_rows.empty:
        return []

    company_types = (
        matching_rows["company_type_slug"].dropna().astype(str).unique().tolist()
    )
    return sorted(company_types)


def _optional_int(value: object) -> int | None:
    """Convert nullable pandas scalar values to plain ints."""
    if pd.isna(value):
        return None
    if isinstance(value, (str, bytes, bytearray, SupportsInt, SupportsIndex)):
        return int(value)
    raise TypeError(f"Expected integer-compatible scalar, got {type(value).__name__}")


def _optional_float(value: object, digits: int = 4) -> float | None:
    """Convert nullable pandas scalar values to rounded floats."""
    if pd.isna(value):
        return None
    if isinstance(value, (str, bytes, bytearray, SupportsFloat, SupportsIndex)):
        return round(float(value), digits)
    raise TypeError(f"Expected float-compatible scalar, got {type(value).__name__}")


def _make_company_trend_points(df: pd.DataFrame) -> list[CompanyTrendPoint]:
    """Convert aggregated quarterly rows into typed trend records."""
    points: list[CompanyTrendPoint] = []
    for row in df.to_dict(orient="records"):
        points.append(
            CompanyTrendPoint(
                source_key=str(row["source_key"]),
                platform=str(row["platform"]),
                tag_source=str(row["tag_source"]),
                period=str(row["period"]),
                year=int(row["year"]),
                quarter=int(row["quarter"]),
                total_apps=int(row["total_apps"]),
                total_apps_in_quarter=int(row["total_apps_in_quarter"]),
                apps_added=int(row["apps_added"]),
                apps_lost=int(row["apps_lost"]),
                net_apps_change=int(row["net_apps_change"]),
                pct_market_share=_optional_float(row.get("pct_market_share"), digits=6),
                previous_pct_market_share=_optional_float(
                    row.get("previous_pct_market_share"), digits=6
                ),
                pct_market_share_change=_optional_float(
                    row.get("pct_market_share_change"), digits=6
                ),
                pct_market_share_change_pct=_optional_float(
                    row.get("pct_market_share_change_pct")
                ),
                pct_apps_added=_optional_float(row.get("pct_apps_added")),
                pct_apps_lost=_optional_float(row.get("pct_apps_lost")),
                total_apps_change=_optional_int(row.get("total_apps_change")),
                total_apps_change_pct=_optional_float(row.get("total_apps_change_pct")),
            )
        )
    return points


def make_company_trends(df: pd.DataFrame) -> CompanyTrends | None:
    """Aggregate quarterly company history into dashboard-friendly trend slices."""
    if df.empty:
        return None

    trends_df = df.copy()
    trends_df["platform"] = trends_df["store"].apply(_normalize_trend_platform)
    trends_df["source_key"] = trends_df.apply(
        lambda row: _make_trend_source_key(
            str(row["platform"]), str(row["tag_source"])
        ),
        axis=1,
    )
    int_columns = [
        "year",
        "quarter",
        "total_apps",
        "total_apps_in_quarter",
        "apps_added",
        "apps_lost",
    ]
    for column in int_columns:
        trends_df[column] = pd.to_numeric(trends_df[column], errors="coerce").fillna(0)
        trends_df[column] = trends_df[column].astype(int)

    aggregated_df = (
        trends_df.groupby(
            ["year", "quarter", "platform", "tag_source", "source_key"],
            dropna=False,
        )[["total_apps", "total_apps_in_quarter", "apps_added", "apps_lost"]]
        .sum()
        .reset_index()
        .sort_values(
            ["year", "quarter", "platform", "tag_source"],
            key=lambda series: (
                series.map(TREND_TAG_SOURCE_ORDER)
                if series.name == "tag_source"
                else series
            ),
        )
        .reset_index(drop=True)
    )
    aggregated_df["period"] = (
        aggregated_df["year"].astype(str) + "-Q" + aggregated_df["quarter"].astype(str)
    )
    aggregated_df["previous_total_apps"] = aggregated_df.groupby("source_key")[
        "total_apps"
    ].shift(1)
    aggregated_df["net_apps_change"] = (
        aggregated_df["apps_added"] - aggregated_df["apps_lost"]
    )
    aggregated_df["pct_market_share"] = np.where(
        aggregated_df["total_apps_in_quarter"] > 0,
        aggregated_df["total_apps"] / aggregated_df["total_apps_in_quarter"] * 100,
        np.nan,
    )
    aggregated_df["previous_pct_market_share"] = aggregated_df.groupby("source_key")[
        "pct_market_share"
    ].shift(1)
    aggregated_df["pct_market_share_change"] = np.where(
        aggregated_df["previous_pct_market_share"].notna(),
        aggregated_df["pct_market_share"] - aggregated_df["previous_pct_market_share"],
        np.nan,
    )
    aggregated_df["pct_market_share_change_pct"] = np.where(
        aggregated_df["previous_pct_market_share"] > 0,
        aggregated_df["pct_market_share_change"]
        / aggregated_df["previous_pct_market_share"]
        * 100,
        np.nan,
    )
    aggregated_df["pct_apps_added"] = np.where(
        aggregated_df["previous_total_apps"] > 0,
        aggregated_df["apps_added"] / aggregated_df["previous_total_apps"] * 100,
        np.nan,
    )
    aggregated_df["pct_apps_lost"] = np.where(
        aggregated_df["previous_total_apps"] > 0,
        aggregated_df["apps_lost"] / aggregated_df["previous_total_apps"] * 100,
        np.nan,
    )
    aggregated_df["total_apps_change"] = np.where(
        aggregated_df["previous_total_apps"].notna(),
        aggregated_df["total_apps"] - aggregated_df["previous_total_apps"],
        np.nan,
    )
    aggregated_df["total_apps_change_pct"] = np.where(
        aggregated_df["previous_total_apps"] > 0,
        aggregated_df["total_apps_change"] / aggregated_df["previous_total_apps"] * 100,
        np.nan,
    )

    latest_period = str(aggregated_df.iloc[-1]["period"])
    history: dict[str, list[CompanyTrendPoint]] = {}
    past_year: dict[str, list[CompanyTrendPoint]] = {}
    summaries: dict[str, CompanyTrendSummary] = {}

    for source_key, source_df in aggregated_df.groupby("source_key", sort=False):
        source_df = source_df.sort_values(["year", "quarter"]).reset_index(drop=True)
        recent_df = source_df.tail(TREND_HISTORY_WINDOW_QUARTERS).reset_index(drop=True)
        latest = source_df.iloc[-1]

        history[str(source_key)] = _make_company_trend_points(source_df)
        past_year[str(source_key)] = _make_company_trend_points(recent_df)
        summaries[str(source_key)] = CompanyTrendSummary(
            source_key=str(source_key),
            platform=str(latest["platform"]),
            tag_source=str(latest["tag_source"]),
            latest_period=str(latest["period"]),
            latest_total_apps=int(latest["total_apps"]),
            previous_total_apps=_optional_int(latest["previous_total_apps"]),
            latest_apps_added=int(latest["apps_added"]),
            latest_apps_lost=int(latest["apps_lost"]),
            latest_net_apps_change=int(latest["net_apps_change"]),
            latest_pct_market_share=_optional_float(
                latest["pct_market_share"], digits=6
            ),
            previous_pct_market_share=_optional_float(
                latest["previous_pct_market_share"], digits=6
            ),
            latest_pct_market_share_change=_optional_float(
                latest["pct_market_share_change"], digits=6
            ),
            latest_pct_market_share_change_pct=_optional_float(
                latest["pct_market_share_change_pct"]
            ),
            latest_pct_apps_added=_optional_float(latest["pct_apps_added"]),
            latest_pct_apps_lost=_optional_float(latest["pct_apps_lost"]),
            qoq_total_apps_change=_optional_int(latest["total_apps_change"]),
            qoq_total_apps_change_pct=_optional_float(latest["total_apps_change_pct"]),
            trailing_year_apps_added=int(recent_df["apps_added"].sum()),
            trailing_year_apps_lost=int(recent_df["apps_lost"].sum()),
            trailing_year_net_apps_change=int(recent_df["net_apps_change"].sum()),
            trailing_year_start_total_apps=int(recent_df.iloc[0]["total_apps"]),
            trailing_year_end_total_apps=int(recent_df.iloc[-1]["total_apps"]),
        )

    return CompanyTrends(
        latest_period=latest_period,
        sources=summaries,
        past_year=past_year,
        history=history,
    )


def make_company_trends_summary(df: pd.DataFrame) -> CompanyTrendsSummary | None:
    """Return only trend summary metrics for lightweight overview payloads."""
    trends = make_company_trends(df)
    if trends is None:
        return None

    return CompanyTrendsSummary(
        latest_period=trends.latest_period,
        sources=trends.sources,
    )


def build_company_trends_payload(state: State, company_domain: str) -> CompanyTrends:
    """Build the full quarterly company trends payload."""
    df = get_combined_companies_history(state=state, company_domain=company_domain)
    trends = make_company_trends(df)
    if trends is None:
        return CompanyTrends()
    return trends


def _shape_company_ad_domain_overview(df: pd.DataFrame) -> dict | None:
    """Convert ad-domain overview rows into the nested API response shape."""
    if df.empty:
        return None
    return (
        df.set_index(["store", "relationship"])
        .groupby(level=[0, 1])
        .apply(lambda rows: rows.iloc[0].dropna().to_dict())
        .unstack(level=0)
        .to_dict()
    )


def _shape_company_publishers_overview(df: pd.DataFrame) -> dict | None:
    """Convert publishers overview rows into the nested API response shape."""
    if df.empty:
        return None
    return (
        df.set_index(["store", "relationship"])
        .groupby(level=[0, 1])
        .apply(lambda rows: rows.to_dict(orient="records"))
        .unstack(level=0)
        .to_dict()
    )


def _build_company_overview_scope(
    state: State,
    company_domain: str,
    category: str | None = None,
    include_parent_rollup: bool = True,
    include_trends: bool = True,
) -> CompanyOverviewScope:
    """Build a single scoped company overview for a direct domain or parent rollup."""
    df = get_company_stats(
        state=state,
        company_domain=company_domain,
        app_category=category,
        include_parent_rollup=include_parent_rollup,
    )
    # Lightweight callers (including the public/MCP adapters) may provide the
    # legacy company-stat shape without category denominator columns. In that
    # case market-share denominators cannot be computed and no category-total
    # query is needed.
    category_totals = (
        get_tag_source_category_totals(state, category)
        if {"cat_total_app_count", "cat_total_installs_d30"}.issubset(df.columns)
        else None
    )
    stats_overview = make_company_stats(df=df, category_totals=category_totals)

    if df.empty or not df["tag_source"].str.contains("app_ads").any():
        ad_domain_overview = None
        publishers_overview = None
    else:
        ad_domain_overview = _shape_company_ad_domain_overview(
            get_company_adstxt_ad_domain_overview(
                state=state,
                ad_domain_url=company_domain,
                include_parent_rollup=include_parent_rollup,
            )
        )
        publishers_overview = _shape_company_publishers_overview(
            get_company_adstxt_publishers_overview(
                state=state,
                ad_domain_url=company_domain,
                include_parent_rollup=include_parent_rollup,
            )
        )

    return CompanyOverviewScope(
        categories=stats_overview.categories,
        adstxt_ad_domain_overview=ad_domain_overview,
        adstxt_publishers_overview=publishers_overview,
        trends_summary=(
            get_company_trends_summary(
                state=state,
                company_domain=company_domain,
            )
            if include_trends
            else None
        ),
    )


def build_company_overview_base(
    state: State, company_domain: str, category: str | None = None
) -> CompanyCategoryOverview:
    """Compute company overview data shared by private and public endpoints."""
    is_parent_company = company_domain in get_parent_companies(state)
    domain_overview = _build_company_overview_scope(
        state=state,
        company_domain=company_domain,
        category=category,
        include_parent_rollup=False,
        include_trends=True,
    )
    parent_overview = (
        _build_company_overview_scope(
            state=state,
            company_domain=company_domain,
            category=category,
            include_parent_rollup=True,
            include_trends=False,
        )
        if is_parent_company
        else None
    )
    active_overview = parent_overview or domain_overview

    mediation_companies = get_mediation_companies(state)

    if company_domain in mediation_companies["company_domain"].tolist():
        mediation_adapters = get_mediation_adapters(state, company_domain)
        if category is None:
            mediation_adapters = (
                mediation_adapters.groupby(
                    [
                        "adapter_company_domain",
                        "adapter_company_name",
                        "adapter_logo_url",
                    ],
                    dropna=False,
                )[["app_count"]]
                .sum()
                .reset_index()
            )
            mediation_adapters = mediation_adapters[mediation_adapters["app_count"] > 1]
        else:
            mediation_adapters = mediation_adapters[
                mediation_adapters["app_category"] == category
            ]

        mediation_adapters = mediation_adapters.sort_values(
            by="app_count", ascending=False
        ).to_dict(orient="records")
    else:
        mediation_adapters = None

    overview = CompanyCategoryOverview(
        categories=active_overview.categories,
        adstxt_ad_domain_overview=active_overview.adstxt_ad_domain_overview,
        adstxt_publishers_overview=active_overview.adstxt_publishers_overview,
        trends_summary=domain_overview.trends_summary,
        domain_overview=domain_overview,
        parent_overview=parent_overview,
    )
    overview.company_types = get_company_types_for_domain(
        state=state, company_domain=company_domain
    )
    overview.mediation_adapters = mediation_adapters
    return overview


def build_private_company_overview_payload(
    state: State, company_domain: str, category: str | None = None
) -> CompanyCategoryOverview:
    """Build the private company overview payload."""
    return build_company_overview_base(
        state=state, company_domain=company_domain, category=category
    )


def _strip_private_companies_overview_metrics(
    overview: CompaniesOverview,
) -> CompaniesOverview:
    """Remove unstable QoQ app-scan metrics from private companies overview rows."""
    dropped_keys = {
        "google_sdk_latest_apps_added",
        "apple_sdk_latest_apps_added",
        "google_api_call_latest_apps_added",
        "apple_api_call_latest_apps_added",
        "google_app_ads_direct_latest_apps_added",
        "apple_app_ads_direct_latest_apps_added",
    }
    overview.companies_overview = [
        {key: value for key, value in company.items() if key not in dropped_keys}
        for company in overview.companies_overview
    ]
    return overview


class CompaniesController(Controller):
    """API EndPoint return for all ad tech companies."""

    path = "/api/"

    @get(path="/companies/{company_domain:str}/reports", cache=3600)
    async def company_reports(
        self: Self, state: State, company_domain: str
    ) -> list[dict[str, object]]:
        """Return available S3 export metadata for a company domain."""
        reports = get_company_s3_reports(state=state, company_domain=company_domain)
        if reports.empty:
            return []

        reports["last_modified"] = pd.to_datetime(
            reports["last_modified"], utc=True
        ).dt.strftime("%Y-%m-%dT%H:%M:%SZ")
        return reports.where(pd.notna(reports), None).to_dict(orient="records")

    @get(path="/companies", cache=86400)
    async def companies(self: Self, state: State) -> CompaniesOverview:
        """Handle GET request for all companies.

        Returns
        -------
        CompaniesOverview
            An overview of companies across different platforms and sources.

        """
        start = time.perf_counter() * 1000

        overview = _strip_private_companies_overview_metrics(get_overviews(state=state))
        duration = round((time.perf_counter() * 1000 - start), 2)
        logger.info(f"GET /api/companies took {duration}ms")
        return overview

    @get(path="/companies/list", cache=86400)
    async def companies_list(self: Self, state: State) -> list[CompanyDirectoryEntry]:
        """Handle GET request for a slim cached companies directory."""
        start = time.perf_counter() * 1000
        directory = get_company_directory(state=state)
        duration = round((time.perf_counter() * 1000 - start), 2)
        logger.info(f"GET /api/companies/list took {duration}ms")
        return directory

    @get(path="/companies/categories/{category:str}", cache=86400)
    async def companies_categories(
        self: Self, state: State, category: str
    ) -> CompaniesOverview:
        """Handle GET request for all companies in a category.

        Returns
        -------
        CompaniesOverview
            An overview of companies across different platforms and sources.

        """
        start = time.perf_counter() * 1000

        overview = _strip_private_companies_overview_metrics(
            get_overviews(state=state, category=category)
        )
        duration = round((time.perf_counter() * 1000 - start), 2)
        logger.info(f"GET /api/companies/categories/{category} took {duration}ms")
        return overview

    @get(
        path="/companies/{company_domain:str}",
        cache=86400,
    )
    async def company_overview(
        self: Self,
        state: State,
        company_domain: str,
        category: str | None = None,
    ) -> CompanyCategoryOverview:
        """Handle GET request for a specific company.

        Args:
        ----
        company_domain : str
            The domain of the company to retrieve apps for.
        category : str | None
            The category to retrieve apps for.

        Returns:
        -------
        CompanyCategoryOverview
            An overview of companies, filtered for the specified company and category.

        """
        start = time.perf_counter() * 1000

        overview = build_private_company_overview_payload(
            state=state, company_domain=company_domain, category=category
        )
        duration = round((time.perf_counter() * 1000 - start), 2)
        logger.info(f"GET /api/companies/{company_domain} took {duration}ms")
        return overview

    @get(path="/companies/{company_domain:str}/tabs", cache=86400)
    async def company_tabs(
        self: Self,
        state: State,
        company_domain: str,
    ) -> CompanyTabIndicators:
        """Return tab-availability indicators for a company domain.

        Uses the frontend.companies_overview materialized view.
        Each count is coalesced (child → parent → 0) so the frontend
        can show/hide or grey-out sub-page links.

        Args:
        ----
        company_domain : str
            The domain to look up indicators for.

        Returns:
        -------
        CompanyTabIndicators
            Per-tab indicators plus raw signal flags.

        """
        start = time.perf_counter() * 1000
        df = get_company_tab_indicators(state=state, company_domain=company_domain)
        if df.empty:
            # Return a mostly-empty row so the frontend always gets a response
            result = CompanyTabIndicators(company_domain=company_domain)
        else:
            row = df.iloc[0]

            def _nan(val: object) -> int | None:
                return None if pd.isna(val) else int(val)  # type: ignore[call-overload]

            def _nan_str(val: object) -> str | None:
                return None if pd.isna(val) else str(val)

            result = CompanyTabIndicators(
                company_domain=str(row.company_domain),
                domain_id=_nan(row.domain_id),
                company_id=_nan(row.company_id),
                company_name=_nan_str(row.company_name),
                logo_url=_nan_str(row.logo_url),
                parent_company_id=_nan(row.parent_company_id),
                parent_domain=_nan_str(row.parent_domain),
                parent_domain_id=_nan(row.parent_domain_id),
                has_sdk_signal=bool(row.has_sdk_signal),
                has_api_signal=bool(row.has_api_signal),
                has_publisher_signal=bool(row.has_publisher_signal),
                has_app_ads_direct=bool(row.has_app_ads_direct),
                has_app_ads_reseller=bool(row.has_app_ads_reseller),
                country=_nan_str(row.country),
                country_direct=_nan_str(row.country_direct),
                creatives_app_count=int(row.creatives_app_count),
                has_trends=int(row.has_trends),
                apps_sdk_added_count=int(row.apps_sdk_added_count),
                apps_sdk_lost_count=int(row.apps_sdk_lost_count),
                apps_adstxt_direct_added_count=int(row.apps_adstxt_direct_added_count),
                apps_adstxt_direct_lost_count=int(row.apps_adstxt_direct_lost_count),
                sdk_count=int(row.sdk_count),
                mediation_adapter_count=int(row.mediation_adapter_count),
                adstxt_direct_app_count=int(row.adstxt_direct_app_count),
                adstxt_parent_app_count=_nan(row.get("adstxt_parent_app_count")) or 0,
                creatives_app_count_direct=int(row.creatives_app_count_direct),
                has_trends_direct=int(row.has_trends_direct),
                apps_sdk_added_count_direct=int(row.apps_sdk_added_count_direct),
                apps_sdk_lost_count_direct=int(row.apps_sdk_lost_count_direct),
                apps_adstxt_direct_added_count_direct=int(
                    row.apps_adstxt_direct_added_count_direct
                ),
                apps_adstxt_direct_lost_count_direct=int(
                    row.apps_adstxt_direct_lost_count_direct
                ),
                sdk_count_direct=int(row.sdk_count_direct),
                mediation_adapter_count_direct=int(row.mediation_adapter_count_direct),
                is_parent_domain=bool(row.is_parent_domain),
                linkedin_url=_nan_str(row.linkedin_url),
                github_user=_nan_str(row.github_user),
                api_ip_resolved_country=_nan_str(row.api_ip_resolved_country),
            )
        duration = round((time.perf_counter() * 1000 - start), 2)
        logger.info(f"GET /api/companies/{company_domain}/tabs took {duration}ms")
        return result

    @get(path="/companies/{company_domain:str}/apps-added", cache=86400)
    async def company_apps_added(
        self: Self,
        state: State,
        company_domain: str,
        year: int | None = None,
        quarter: int | None = None,
    ) -> CompanyAppChangesOverview:
        """Return recently added apps (SDK + API-call signals only)."""
        start = time.perf_counter() * 1000
        payload = build_company_app_changes_payload(
            state=state,
            company_domain=company_domain,
            status="added",
            year=year,
            quarter=quarter,
            tag_sources=COMPANY_APP_CHANGE_SDK_API_TAG_SOURCES,
        )
        duration = round((time.perf_counter() * 1000 - start), 2)
        logger.info(f"GET /api/companies/{company_domain}/apps-added took {duration}ms")
        return payload

    @get(path="/companies/{company_domain:str}/apps-lost", cache=86400)
    async def company_apps_lost(
        self: Self,
        state: State,
        company_domain: str,
        year: int | None = None,
        quarter: int | None = None,
    ) -> CompanyAppChangesOverview:
        """Return recently lost apps (SDK + API-call signals only)."""
        start = time.perf_counter() * 1000
        payload = build_company_app_changes_payload(
            state=state,
            company_domain=company_domain,
            status="removed",
            year=year,
            quarter=quarter,
            tag_sources=COMPANY_APP_CHANGE_SDK_API_TAG_SOURCES,
        )
        duration = round((time.perf_counter() * 1000 - start), 2)
        logger.info(f"GET /api/companies/{company_domain}/apps-lost took {duration}ms")
        return payload

    @get(path="/companies/{company_domain:str}/apps-added-adstxt", cache=86400)
    async def company_apps_added_adstxt(
        self: Self,
        state: State,
        company_domain: str,
        year: int | None = None,
        quarter: int | None = None,
    ) -> CompanyAppChangesOverview:
        """Return recently added apps (app-ads.txt direct signals only)."""
        start = time.perf_counter() * 1000
        payload = build_company_app_changes_payload(
            state=state,
            company_domain=company_domain,
            status="added",
            year=year,
            quarter=quarter,
            tag_sources=COMPANY_APP_CHANGE_ADSTXT_TAG_SOURCES,
        )
        duration = round((time.perf_counter() * 1000 - start), 2)
        logger.info(
            f"GET /api/companies/{company_domain}/apps-added-adstxt took {duration}ms"
        )
        return payload

    @get(path="/companies/{company_domain:str}/apps-lost-adstxt", cache=86400)
    async def company_apps_lost_adstxt(
        self: Self,
        state: State,
        company_domain: str,
        year: int | None = None,
        quarter: int | None = None,
    ) -> CompanyAppChangesOverview:
        """Return recently lost apps (app-ads.txt direct signals only)."""
        start = time.perf_counter() * 1000
        payload = build_company_app_changes_payload(
            state=state,
            company_domain=company_domain,
            status="removed",
            year=year,
            quarter=quarter,
            tag_sources=COMPANY_APP_CHANGE_ADSTXT_TAG_SOURCES,
        )
        duration = round((time.perf_counter() * 1000 - start), 2)
        logger.info(
            f"GET /api/companies/{company_domain}/apps-lost-adstxt took {duration}ms"
        )
        return payload

    @get(path="/companies/{company_domain:str}/trends", cache=86400)
    async def company_trends(
        self: Self,
        state: State,
        company_domain: str,
    ) -> CompanyTrends:
        """Handle GET request for full quarterly trends for a specific company."""
        start = time.perf_counter() * 1000
        trends = build_company_trends_payload(
            state=state, company_domain=company_domain
        )
        duration = round((time.perf_counter() * 1000 - start), 2)
        logger.info(f"GET /api/companies/{company_domain}/trends took {duration}ms")
        return trends

    @get(path="/companies/{company_domain:str}/lookup", cache=3600)
    async def company_lookup(
        self: Self,
        state: State,
        company_domain: str,
    ) -> CompanyFollowLookup:
        """Resolve a company domain to company_id metadata for follow actions."""
        start = time.perf_counter() * 1000
        df = get_company_follow_lookup(state=state, company_domain=company_domain)
        if df.empty:
            msg = f"Company domain not found: {company_domain!r}"
            raise NotFoundException(msg, status_code=404)

        row = df.to_dict(orient="records")[0]
        duration = round((time.perf_counter() * 1000 - start), 2)
        logger.info(f"GET /api/companies/{company_domain}/lookup took {duration}ms")
        return CompanyFollowLookup(
            company_id=int(row["company_id"]),
            company_name=str(row["company_name"]),
            company_domain=str(row["company_domain"]),
        )

    @get(
        path="/companies/{company_domain:str}/topapps",
        cache=86400,
    )
    async def company_apps(
        self: Self,
        state: State,
        company_domain: str,
        category: str | None = None,
    ) -> CompanyPlatformOverview:
        """Handle GET request for a specific company top apps.

        Args:
        ----
        company_domain : str
            The domain of the company to retrieve apps for.
        category : str | None
            The category to retrieve apps for.

        Returns:
        -------
        CompanyAppsOverview
            An overview of companies, filtered for the specified company and category.

        """
        start = time.perf_counter() * 1000
        results = get_company_apps(
            state=state, company_domain=company_domain, category=category
        )

        duration = round((time.perf_counter() * 1000 - start), 2)
        logger.info(
            f"GET /api/companies/{company_domain}/topapps {category=} took {duration}ms"
        )
        return results

    @get(
        path="/companies/{company_domain:str}/parentcategories",
        cache=86400,
    )
    async def company_parent_categories(
        self: Self,
        state: State,
        company_domain: str,
        rollup: bool = True,
    ) -> dict:
        """Handle GET request for a specific company parent categories.

        Args:
        ----
        company_domain : str
            The domain of the company to retrieve apps for.
        rollup : bool
            Whether to include parent company rollup data.

        Returns:
        -------
        dict
            A dictionary with 'android' and 'ios' keys containing category data.

        """
        start = time.perf_counter() * 1000

        dfs = get_company_categories_counts(
            state=state,
            company_domain=company_domain,
            include_parent_rollup=rollup,
        )

        duration = round((time.perf_counter() * 1000 - start), 2)
        logger.info(
            f"GET /api/companies/{company_domain}/parentcategories took {duration}ms"
        )
        return {
            store: df.to_dict(orient="records") if not df.empty else []
            for store, df in dfs.items()
        }

    @get(
        path="/companies/{company_domain:str}/countries",
        cache=86400,
    )
    async def company_countries(
        self: Self,
        state: State,
        company_domain: str,
        category: str | None = None,
    ) -> dict[str, list[dict[str, object]]]:
        """Handle GET request for a company's app counts by country.

        Returns a dict keyed by store ('android' and 'ios'), each containing
        rows with 'country' and 'app_count'. The top 5 countries per store are
        kept individually; the remainder are rolled up into an 'Others' row.

        Not all companies will have this data — stores without any rows are
        returned as empty lists.

        Args:
        ----
        company_domain : str
            The domain of the company to retrieve country data for.
        category : str | None
            Optional category to filter the country data by.

        Returns:
        -------
        dict
            A dictionary with 'android' and 'ios' keys containing country data.

        """
        start = time.perf_counter() * 1000

        df = get_company_country_apps(
            state=state,
            company_domain=company_domain,
            app_category=category,
        )

        duration = round((time.perf_counter() * 1000 - start), 2)
        logger.info(f"GET /api/companies/{company_domain}/countries took {duration}ms")
        store_map = {1: "android", 2: "ios"}
        result: dict[str, list[dict[str, object]]] = {}
        for store, store_df in df.groupby("store", sort=True):
            result[store_map.get(int(store), str(store))] = (
                store_df.to_dict(orient="records") if not store_df.empty else []
            )
        return result

    @get(
        path="/companies/{queried_domain:str}/tree",
        cache=86400,
    )
    async def company_tree(
        self: Self,
        state: State,
        queried_domain: str,
    ) -> CompanyTree:
        """Handle GET request for company tree.

        Args:
        ----
        queried_domain : str
            The name of the company to retrieve apps for.

        Returns:
        -------
        CompanyTree
            An overview of companies, filtered for the specified company and category.

        """
        df = get_company_tree_base(state=state, queried_domain=queried_domain)

        if df.empty:
            # queried domain is not associated with any company
            return CompanyTree(
                queried_domain=queried_domain,
                is_secondary_domain=False,
                is_orphan=True,
                company_name=None,
                company_domain=None,
                company_logo_url=None,
                domains=[],
                parent=None,
                children=[],
            )

        is_orphan = False
        anchor = df.iloc[0]
        company_id = anchor["company_id"]
        parent_id = anchor["parent_id"]
        is_secondary_domain = bool(anchor["is_secondary_domain"])

        children = []
        own_domains = []
        # Secondary domain has no children
        if not is_secondary_domain:
            # not secondary domain we are looking at a main company domain
            # fill out own_domains and children companies (if there are any)
            related = get_company_tree_related_domains(
                state=state, company_id=company_id, is_parent=parent_id is None
            )
            child_domain_map = defaultdict(list)
            child_meta_map = {}
            # First pass: collect all domain mappings and metadata
            for _, r in related.iterrows():
                if r["company_id"] == company_id:
                    own_domains.append(
                        CompanyDomain(
                            domain_name=r["domain_name"], is_primary=r["is_primary"]
                        )
                    )
                else:
                    child_domain_map[r["company_id"]].append(
                        CompanyDomain(
                            domain_name=r["domain_name"], is_primary=r["is_primary"]
                        )
                    )
                    if r["company_id"] not in child_meta_map:
                        child_meta_map[r["company_id"]] = {
                            "company_name": r["company_name"],
                            "company_logo_url": r["company_logo"],
                        }
            # Collect all domain names from own domains and all children
            all_domain_names = [d.domain_name for d in own_domains] + [
                d.domain_name for domains in child_domain_map.values() for d in domains
            ]
            # Make one API call to enrich all domains
            if all_domain_names:
                api_data = make_company_api_domains_dict(state, all_domain_names)
                # Enrich own domains with country / org
                enrich_domains(own_domains, api_data)
            else:
                api_data = []
            # Build children with enriched domains
            children = [
                ChildCompany(
                    company_name=str(meta["company_name"]),
                    company_domain=next(
                        (d.domain_name for d in domains if d.is_primary),
                        domains[0].domain_name if domains else "",
                    ),
                    company_logo_url=meta["company_logo_url"],
                    domains=enrich_domains(domains, api_data),
                )
                for _cid, (meta, domains) in {
                    cid: (child_meta_map[cid], child_domain_map[cid])
                    for cid in child_meta_map
                }.items()
            ]

        parent = None
        # Build parent context if this is a child company
        if parent_id is not None:
            parent = ParentCompanyContext(
                company_name=anchor["parent_name"],
                company_domain=anchor["parent_domain"],
                company_logo_url=anchor["parent_logo_url"],
            )

        return CompanyTree(
            queried_domain=queried_domain,
            is_orphan=is_orphan,
            is_secondary_domain=is_secondary_domain,
            company_name=anchor["company_name"],
            company_domain=anchor["company_domain"],
            company_logo_url=anchor["company_logo_url"],
            domains=own_domains,
            parent=parent,
            children=children,
        )

    @get(
        path="/companies/{company_domain:str}/sdks",
        cache=3600,
    )
    async def company_sdks(
        self: Self,
        state: State,
        company_domain: str,
    ) -> CompanyPatternsDict:
        """Handle GET request for company sdks.

        Args:
        ----
        company_domain : str
            The domain of the company to retrieve apps for.

        Returns:
        -------
        ParentCompanySDKs
            An overview of companies, filtered for the specified company and category.

        """
        start = time.perf_counter() * 1000

        df = get_company_sdks(state=state, company_domain=company_domain)

        company_sdks: dict = {}

        def _pattern_rows(group: pd.DataFrame, pattern_type: str) -> list[dict]:
            """Shape query pattern rows while preserving nullable app counts."""
            rows = group[group["pattern_type"].astype(str).str.lower() == pattern_type]
            return [
                {
                    "pattern": str(row.pattern_value),
                    "app_count": (
                        None if pd.isna(row.app_count) else int(row.app_count)
                    ),
                }
                for row in rows.itertuples(index=False)
                if pd.notna(row.pattern_value)
            ]

        # Group by company name and SDK name. The query now returns one row per
        # pattern, with pattern_type replacing the old package/path columns.
        for (company, sdk), group in df.groupby(["company_name", "sdk_name"]):
            # Create entry for company if it doesn't exist
            if company not in company_sdks:
                company_sdks[company] = {}

            # Add sdk data
            company_sdks[company][sdk] = {
                "package_patterns": _pattern_rows(group, "package"),
                "paths": _pattern_rows(group, "path"),
                "mediation_patterns": _pattern_rows(group, "mediation"),
            }
        mydict = CompanyPatternsDict(
            companies=company_sdks,
        )

        duration = round((time.perf_counter() * 1000 - start), 2)
        logger.info(f"GET /api/companies/{company_domain}/sdks took {duration}ms")

        return mydict

    @get(path="/companies/types/", cache=CACHE_FOREVER)
    async def all_adtech_types(self: Self, state: State) -> CompanyTypes:
        """Handle GET request for a list of adtech company categories.

        Returns
        -------
            A dictionary representation of the list of categories
            each with an id, name, type and total of apps

        """
        start = time.perf_counter() * 1000
        company_types_df = get_adtech_categories(state=state)

        company_types = CompanyTypes(types=company_types_df.to_dict(orient="records"))

        duration = round((time.perf_counter() * 1000 - start), 2)
        logger.info(f"GET /api/companies/types took {duration}ms")

        return company_types

    @get(path="/companies/types/{type_slug:str}", cache=86400)
    async def adtech_type(
        self: Self,
        state: State,
        type_slug: str,
        category: str | None = None,
    ) -> CompaniesOverview:
        """Handle GET request for a list of adtech company categories.

        Returns
        -------
            A dictionary representation of the list of categories
            each with an id, name, type and total of apps

        """
        start = time.perf_counter() * 1000
        overview = get_overviews(state=state, category=category, type_slug=type_slug)

        duration = round((time.perf_counter() * 1000 - start), 2)
        logger.info(f"/companies/types/{type_slug}?{category=} took {duration}ms")

        return overview

    @get(path="/companies/topshort/", cache=CACHE_FOREVER)
    async def get_companies_shortlist_top(
        self: Self, state: State
    ) -> TopCompaniesOverviewShort:
        """Handle GET request for a list of adtech company categories.

        Returns
        -------
            A dictionary representation of the list of categories
            each with an id, name, type and total of apps

        """
        start = time.perf_counter() * 1000
        company_logos_df = get_company_logos_df(state).drop_duplicates(
            subset=["company_domain"], keep="first"
        )
        logger.info(
            f"get_companies_shortlist_top: company_logos_df took "
            f"{round((time.perf_counter() * 1000 - start), 2)}ms"
        )

        adnetworks_start = time.perf_counter() * 1000
        adnetworks = get_companies_top(
            state=state, type_slug="ad-networks", category=None, limit=5
        )
        adnetworks = adnetworks.merge(
            company_logos_df,
            on="company_domain",
            how="left",
            validate="m:1",
        )
        logger.info(
            f"get_companies_shortlist_top: adnetworks took "
            f"{round((time.perf_counter() * 1000 - adnetworks_start), 2)}ms"
        )

        mmps_start = time.perf_counter() * 1000
        mmps = get_companies_top(
            state=state, type_slug="ad-attribution", category=None, limit=5
        )
        mmps = mmps.merge(
            company_logos_df,
            on="company_domain",
            how="left",
            validate="m:1",
        )
        logger.info(
            f"get_companies_shortlist_top: mmps took "
            f"{round((time.perf_counter() * 1000 - mmps_start), 2)}ms"
        )

        analytics_start = time.perf_counter() * 1000
        analytics = get_companies_top(
            state=state, type_slug="product-analytics", category=None, limit=5
        )
        analytics = analytics.merge(
            company_logos_df,
            on="company_domain",
            how="left",
            validate="m:1",
        )
        logger.info(
            f"get_companies_shortlist_top: analytics took "
            f"{round((time.perf_counter() * 1000 - analytics_start), 2)}ms"
        )

        top_ad_networks = top_companies_by_tag_source(adnetworks)
        top_mmps = top_companies_by_tag_source(mmps)
        top_analytics = top_companies_by_tag_source(analytics)

        top_companies = TopCompaniesOverviewShort(
            adnetworks=top_ad_networks,
            attribution=top_mmps,
            analytics=top_analytics,
        )

        duration = round((time.perf_counter() * 1000 - start), 2)
        logger.info(f"{self.path} took {duration}ms")

        return top_companies

    @get(path="/companies/search/{search_term:str}", cache=86400)
    async def get_companies_search(
        self: Self, state: State, search_term: str
    ) -> list[CompanyDetail]:
        """Handle GET request for a list of adtech company categories.

        Returns
        -------
            A list of CompanyDetail objects

        """
        start = time.perf_counter() * 1000
        results = get_search_results(state, search_term=search_term)

        duration = round((time.perf_counter() * 1000 - start), 2)
        logger.info(f"{self.path}/{search_term} took {duration}ms")

        return results.to_dict(orient="records")

    @get(
        path="/companies/{company_domain:str}/adstxt/publisher/{publisher_id:str}",
        cache=3600,
    )
    async def adstxt_company_overview(
        self: Self,
        state: State,
        company_domain: str,
        publisher_id: str,
    ) -> CompanyPubIDOverview:
        """Handle GET request for a company adstxt publisher id.

        Args:
        ----
        company_domain : str
            The domain of the company to retrieve apps for.
        publisher_id: str
            The publisher id to retrieve apps for.

        Returns:
        -------
        ListOfAppsRelatedToPublisher
            A list of apps related to the publisher.

        """
        start = time.perf_counter() * 1000

        df_apps = get_company_adstxt_publisher_id_apps_overview(
            state=state,
            ad_domain_url=company_domain,
            publisher_id=publisher_id,
        )

        df_pub_id_overview = get_company_adstxt_publishers_overview(
            state=state,
            ad_domain_url=company_domain,
            publisher_id=publisher_id,
        )

        # Define default structure once
        def default_structure() -> dict:
            return {
                "apple": {"direct": [], "reseller": []},
                "google": {"direct": [], "reseller": []},
            }

        apps_raw = (
            df_apps.sort_values(["installs", "rating_count"], ascending=False)
            .set_index(["store", "relationship"])
            .groupby(level=[0, 1])
            .apply(lambda x: x.to_dict(orient="records"))
            .unstack(level=0)
            .to_dict()
        )
        apps = default_structure()

        for store in ["apple", "google"]:
            for relationship in ["direct", "reseller"]:
                if (
                    store in apps_raw
                    and relationship in apps_raw[store]
                    and apps_raw[store][relationship]
                ):
                    apps[store][relationship] = apps_raw[store][relationship]

        stats_raw = (
            df_pub_id_overview.set_index(["store", "relationship"])
            .groupby(level=[0, 1])
            .apply(lambda x: x.to_dict(orient="records"))
            .unstack(level=0)
            .to_dict()
        )

        stats = default_structure()
        for store in ["apple", "google"]:
            for relationship in ["direct", "reseller"]:
                if (
                    store in stats_raw
                    and relationship in stats_raw[store]
                    and stats_raw[store][relationship]
                ):
                    stats[store][relationship] = stats_raw[store][relationship]

        is_apple = df_pub_id_overview["store"] == "apple"
        is_google = df_pub_id_overview["store"] == "google"
        is_direct = df_pub_id_overview["relationship"] == "direct"
        is_reseller = df_pub_id_overview["relationship"] == "reseller"

        df_pub_id_overview[is_apple & is_direct]

        # Get developer and app counts
        totals = CompanyPubIDTotals(
            direct_google_devs=get_count(
                df_pub_id_overview, is_google & is_direct, "developer_count"
            ),
            direct_apple_devs=get_count(
                df_pub_id_overview, is_apple & is_direct, "developer_count"
            ),
            direct_google_apps=get_count(
                df_pub_id_overview, is_google & is_direct, "app_count"
            ),
            direct_apple_apps=get_count(
                df_pub_id_overview, is_apple & is_direct, "app_count"
            ),
            reseller_google_devs=get_count(
                df_pub_id_overview, is_google & is_reseller, "developer_count"
            ),
            reseller_apple_devs=get_count(
                df_pub_id_overview, is_apple & is_reseller, "developer_count"
            ),
            reseller_google_apps=get_count(
                df_pub_id_overview, is_google & is_reseller, "app_count"
            ),
            reseller_apple_apps=get_count(
                df_pub_id_overview, is_apple & is_reseller, "app_count"
            ),
        )

        typed_apps = CompanyPubIDApps(
            google=CompanyPubIDAppsRelationship(
                direct=apps["google"]["direct"],
                reseller=apps["google"]["reseller"],
            ),
            apple=CompanyPubIDAppsRelationship(
                direct=apps["apple"]["direct"],
                reseller=apps["apple"]["reseller"],
            ),
        )

        overview = CompanyPubIDOverview(
            totals=totals,
            apps=typed_apps,
        )

        duration = round((time.perf_counter() * 1000 - start), 2)
        endpoint = (
            f"GET /api/companies/{company_domain}/adstxt/publisher/{publisher_id}"
        )
        msg = f"{endpoint} took {duration}ms"
        logger.info(msg)
        return overview

    @get(
        path="/companies/{company_domain:str}/adstxt/publisher/{publisher_id:str}/download",
        cache=3600,
    )
    async def adstxt_company_publisher_download(
        self: Self,
        state: State,
        company_domain: str,
        publisher_id: str,
    ) -> CompanyPubIDOverview:
        """Handle GET request for a company adstxt publisher id.

        Args:
        ----
        company_domain : str
            The domain of the company to retrieve apps for.
        publisher_id: str
            The publisher id to retrieve apps for.

        Returns:
        -------
        ListOfAppsRelatedToPublisher
            A list of apps related to the publisher.

        """
        df = get_company_adstxt_publisher_id_apps_raw(
            state,
            ad_domain_url=company_domain,
            publisher_id=publisher_id,
        )

        buffer = io.StringIO()
        df.to_csv(buffer, index=False)
        buffer.seek(0)

        filename = f"adstxt_{company_domain}_{publisher_id}.csv"

        return Stream(
            iter([buffer.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )
