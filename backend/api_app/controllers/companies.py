"""API endoipoints for companies.

/companies/ returns list of top companies overall.
/companies/{company_domain} returns detail for a specific company.
/companies/{company_domain}/topapps returns top apps for a specific company.
/companies/{company_domain}/tree returns parent/child company tree for a specific company.
/companies/categories/{category} returns list of top companies for a specific category.
/companies/countries returns list of countries where companies are located.


"""

import io
import time
import urllib
from typing import Self

import numpy as np
import pandas as pd
from litestar import Controller, get
from litestar.config.response_cache import CACHE_FOREVER
from litestar.datastructures import State
from litestar.response import Stream

from api_app.models import (
    AppGroup,
    CompaniesCategoryOverview,
    CompaniesOverview,
    CompanyCategoryOverview,
    CompanyDetail,
    CompanyPatternsDict,
    CompanyPlatformOverview,
    CompanyPubIDOverview,
    CompanyPubIDTotals,
    CompanyTypes,
    ParentCompanyTree,
    TopCompaniesOverviewShort,
    TopCompaniesShort,
)
from config import get_logger
from dbcon.queries import (
    get_companies_category_tag_type_stats,
    get_companies_parent_category_stats,
    get_companies_tag_type_stats,
    get_companies_top,
    get_company_adstxt_ad_domain_overview,
    get_company_adstxt_publisher_id_apps_overview,
    get_company_adstxt_publisher_id_apps_raw,
    get_company_adstxt_publishers_overview,
    get_company_categories_topn,
    get_company_sdks,
    get_company_stats,
    get_company_tree,
    get_mediation_adapters,
    get_tag_source_category_totals,
    get_topapps_for_company,
    get_topapps_for_company_parent,
    get_topapps_for_company_secondary,
    search_companies,
)
from dbcon.static import (
    get_adtech_categories,
    get_company_api_call_countrys,
    get_company_countries,
    get_company_logos_df,
    get_company_open_source,
    get_company_secondary_domains,
    get_mediation_companies,
    get_parent_companies,
)

logger = get_logger(__name__)


def make_company_api_domains_dict(
    state: State, company_domains: list[str]
) -> list[dict]:
    """Make company api domains dict."""
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

    df["country"] = df["country"].apply(
        lambda x: x.tolist() if isinstance(x, np.ndarray) else x
    )
    df["org"] = df["org"].apply(
        lambda x: x.tolist() if isinstance(x, np.ndarray) else x
    )

    df["country"] = df["country"].apply(
        lambda x: x.tolist() if isinstance(x, np.ndarray) else x
    )

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
    countries_df = get_company_countries(state)
    df = df.merge(
        countries_df,
        on="company_domain",
        how="left",
        validate="1:1",
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
    if is_secondary_domain:
        df = get_topapps_for_company_secondary(
            state=state,
            company_domain=company_domain,
            mapped_category=category,
        )
    elif is_parent_company:
        df = get_topapps_for_company_parent(
            state=state,
            company_domain=company_domain,
            mapped_category=category,
        )
    else:
        df = get_topapps_for_company(
            state=state,
            company_domain=company_domain,
            mapped_category=category,
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


def make_top_companies(top_df: pd.DataFrame) -> TopCompaniesShort:
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
    top_ios_adstxt_direct_df = process_top_df(top_df, "app_ads_direct", "Apple")
    top_android_adstxt_direct_df = process_top_df(top_df, "app_ads_direct", "Google")

    top_companies_short = TopCompaniesShort(
        sdk_ios=top_ios_sdk_df.to_dict(orient="records"),
        sdk_android=top_android_sdk_df.to_dict(orient="records"),
        adstxt_direct_ios=top_ios_adstxt_direct_df.to_dict(orient="records"),
        adstxt_direct_android=top_android_adstxt_direct_df.to_dict(orient="records"),
    )
    return top_companies_short


def prep_companies_overview_df(
    state: State,
    overview_df: pd.DataFrame,
) -> tuple[pd.DataFrame, CompaniesCategoryOverview]:
    """Prep companies overview dataframe."""
    overview_df = (
        overview_df.groupby(
            ["company_name", "company_domain", "store", "tag_source"],
            dropna=False,
        )[["app_count", "cat_total_app_count", "installs_d30", "rating_count_d30"]]
        .sum()
        .reset_index()
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

    # NOTE: Crucial for SDK to be first
    # since it has more than just advertising data
    store_tag_source_cols = [
        f"{x}_percentage" for x in overview_df["store_tag_source"].unique().tolist()
    ]
    sdk_cols = [x for x in store_tag_source_cols if "sdk" in x]
    adstxt_cols = [x for x in store_tag_source_cols if "app_ads" in x]
    adstxt_direct_cols = [x for x in adstxt_cols if "direct" in x]

    # NOTE: Hacky way to handle iOS with no installs
    overview_df.loc[overview_df["installs_d30"] == 0, "installs_d30"] = (
        overview_df.loc[overview_df["installs_d30"] == 0, "rating_count_d30"] * 50
    )

    pivoted_df = overview_df.pivot(
        index=["company_name", "company_domain"],
        columns=["store_tag_source"],
        values=["percentage", "installs_d30"],
    )

    # Flatten the multi-level columns
    pivoted_df.columns = [f"{col[1]}_{col[0]}" for col in pivoted_df.columns]
    overview_df = pivoted_df.reset_index()

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
        countries_df,
        on="company_domain",
        how="left",
        validate="1:1",
    )
    overview_df = overview_df.merge(
        get_company_logos_df(state),
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
    # Get Top 5 Companies for Plots
    top_df = get_companies_top(
        state=state, type_slug=type_slug, app_category=category, limit=5
    )
    top_companies_short = make_top_companies(top_df)

    if type_slug:
        if category:
            overview_df = get_companies_category_tag_type_stats(
                state=state, type_slug=type_slug, app_category=category
            )
        else:
            overview_df = get_companies_tag_type_stats(state=state, type_slug=type_slug)

    else:
        overview_df = get_companies_parent_category_stats(
            state=state, app_category=category
        )

    tag_source_category_app_counts = get_tag_source_category_totals(
        state=state, app_category=category
    )

    overview_df = overview_df.merge(
        tag_source_category_app_counts,
        on=["app_category", "store", "tag_source"],
        validate="m:1",
    )

    category_overview = make_companies_stats(
        df=overview_df.copy(),
        tag_source_category_app_counts=tag_source_category_app_counts,
    )

    overview_df = prep_companies_overview_df(state, overview_df)

    results = CompaniesOverview(
        companies_overview=overview_df.to_dict(orient="records"),
        top=top_companies_short,
        categories=category_overview,
    )

    return results


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
    df: pd.DataFrame, tag_source_category_app_counts: pd.DataFrame
) -> CompaniesCategoryOverview:
    """Make category sums for overview."""
    overview = CompaniesCategoryOverview()

    # Precompute boolean masks
    is_apple = df["store"].str.contains("Apple")
    is_google = df["store"].str.contains("Google")
    is_sdk = df["tag_source"] == "sdk"
    is_app_ads_reseller = df["tag_source"] == "app_ads_reseller"
    is_app_ads_direct = df["tag_source"] == "app_ads_direct"

    # Function to calculate unique counts
    def get_unique_company_counts(mask: pd.Series) -> int:
        return df.loc[mask, "company_domain"].nunique()

    def get_installs_d30(mask: pd.Series) -> int:
        return df.loc[mask, "installs_d30"].sum()

    def get_rating_count_d30(mask: pd.Series) -> int:
        return df.loc[mask, "rating_count_d30"].sum()

    def get_app_count(mask: pd.Series) -> int:
        return int(df.loc[mask, "app_count"].sum())

    # Calculate overall stats
    overall_stats = {
        "total_companies": df["company_domain"].nunique(),
        "sdk_ios_total_apps": get_app_count(is_apple & is_sdk),
        "sdk_android_total_apps": get_app_count(is_google & is_sdk),
        "sdk_ios_total_companies": get_unique_company_counts(is_apple & is_sdk),
        "sdk_android_total_companies": get_unique_company_counts(is_google & is_sdk),
        "adstxt_direct_ios_total_companies": get_unique_company_counts(
            is_apple & is_app_ads_direct
        ),
        "adstxt_direct_android_total_companies": get_unique_company_counts(
            is_google & is_app_ads_direct,
        ),
        "adstxt_reseller_ios_total_companies": get_unique_company_counts(
            is_apple & is_app_ads_reseller,
        ),
        "adstxt_reseller_android_total_companies": get_unique_company_counts(
            is_google & is_app_ads_reseller,
        ),
        "sdk_android_installs_d30": get_installs_d30(is_google & is_sdk),
        "sdk_ios_rating_count_d30": get_rating_count_d30(is_apple & is_sdk),
        "adstxt_direct_android_installs_d30": get_installs_d30(
            is_google & is_app_ads_direct
        ),
        "adstxt_direct_ios_rating_count_d30": get_rating_count_d30(
            is_apple & is_app_ads_direct
        ),
        "adstxt_reseller_android_installs_d30": get_installs_d30(
            is_google & is_app_ads_reseller
        ),
        "adstxt_reseller_ios_rating_count_d30": get_rating_count_d30(
            is_apple & is_app_ads_reseller
        ),
    }
    overview.update_stats("all", **overall_stats)

    is_apple = tag_source_category_app_counts["store"].str.contains("Apple")
    is_google = tag_source_category_app_counts["store"].str.contains("Google")
    is_sdk = tag_source_category_app_counts["tag_source"] == "sdk"
    is_app_ads_reseller = (
        tag_source_category_app_counts["tag_source"] == "app_ads_reseller"
    )
    is_app_ads_direct = tag_source_category_app_counts["tag_source"] == "app_ads_direct"

    sdk_app_counts = {
        "sdk_total_apps": int(
            tag_source_category_app_counts[is_sdk]["cat_total_app_count"].sum()
        ),
        # This gives the same sum regardless of copmany type
        # "sdk_android_total_apps": int(
        #     tag_source_category_app_counts[is_sdk & is_google][
        #         "cat_total_app_count"
        #     ].sum()
        # ),
        # "sdk_ios_total_apps": int(
        #     tag_source_category_app_counts[is_sdk & is_apple][
        #         "cat_total_app_count"
        #     ].sum()
        # ),
    }

    overview.update_stats("all", **sdk_app_counts)

    return overview


def make_company_stats(df: pd.DataFrame) -> CompanyCategoryOverview:
    """Make category sums for overview."""
    overview = CompanyCategoryOverview()
    if df.empty:
        return overview
    conditions = {
        "sdk_ios": (df["store"].str.contains("Apple")) & (df["tag_source"] == "sdk"),
        "sdk_android": (df["store"].str.contains("Google"))
        & (df["tag_source"] == "sdk"),
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

    res_rating_count_d30 = {
        key: df.loc[condition, "rating_count_d30"].sum()
        for key, condition in conditions.items()
    }

    # Unpack results
    (
        sdk_ios_total_apps,
        sdk_android_total_apps,
        adstxt_direct_ios_total_apps,
        adstxt_direct_android_total_apps,
        adstxt_reseller_ios_total_apps,
        adstxt_reseller_android_total_apps,
    ) = (
        res_app_counts["sdk_ios"],
        res_app_counts["sdk_android"],
        res_app_counts["adstxt_direct_ios"],
        res_app_counts["adstxt_direct_android"],
        res_app_counts["adstxt_reseller_ios"],
        res_app_counts["adstxt_reseller_android"],
    )

    (
        sdk_android_installs_d30,
        adstxt_direct_android_installs_d30,
        adstxt_reseller_android_installs_d30,
    ) = (
        res_installs_d30["sdk_android"],
        res_installs_d30["adstxt_direct_android"],
        res_installs_d30["adstxt_reseller_android"],
    )

    (
        sdk_ios_rating_count_d30,
        adstxt_direct_ios_rating_count_d30,
        adstxt_reseller_ios_rating_count_d30,
    ) = (
        res_rating_count_d30["sdk_ios"],
        res_rating_count_d30["adstxt_direct_ios"],
        res_rating_count_d30["adstxt_reseller_ios"],
    )

    sdk_total_apps = sdk_ios_total_apps + sdk_android_total_apps
    total_apps = (
        sdk_total_apps
        + adstxt_direct_ios_total_apps
        + adstxt_direct_android_total_apps
        + adstxt_reseller_ios_total_apps
        + adstxt_reseller_android_total_apps
    )

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
        adstxt_direct_android_installs_d30=int(adstxt_direct_android_installs_d30),
        adstxt_reseller_android_installs_d30=int(adstxt_reseller_android_installs_d30),
        sdk_ios_rating_count_d30=int(sdk_ios_rating_count_d30),
        adstxt_direct_ios_rating_count_d30=int(adstxt_direct_ios_rating_count_d30),
        adstxt_reseller_ios_rating_count_d30=int(adstxt_reseller_ios_rating_count_d30),
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
        res_rating_count_d30 = {
            key: df.loc[condition, "rating_count_d30"].sum()
            for key, condition in conditions.items()
        }

        # Unpack results
        (
            sdk_ios_total_apps,
            sdk_android_total_apps,
            adstxt_direct_ios_total_apps,
            adstxt_direct_android_total_apps,
            adstxt_reseller_ios_total_apps,
            adstxt_reseller_android_total_apps,
        ) = (
            res_app_counts["sdk_ios"],
            res_app_counts["sdk_android"],
            res_app_counts["adstxt_direct_ios"],
            res_app_counts["adstxt_direct_android"],
            res_app_counts["adstxt_reseller_ios"],
            res_app_counts["adstxt_reseller_android"],
        )

        (
            sdk_android_installs_d30,
            adstxt_direct_android_installs_d30,
            adstxt_reseller_android_installs_d30,
        ) = (
            res_installs_d30["sdk_android"],
            res_installs_d30["adstxt_direct_android"],
            res_installs_d30["adstxt_reseller_android"],
        )

        (
            sdk_ios_rating_count_d30,
            adstxt_direct_ios_rating_count_d30,
            adstxt_reseller_ios_rating_count_d30,
        ) = (
            res_rating_count_d30["sdk_ios"],
            res_rating_count_d30["adstxt_direct_ios"],
            res_rating_count_d30["adstxt_reseller_ios"],
        )

        sdk_total_apps = sdk_ios_total_apps + sdk_android_total_apps
        total_apps = (
            sdk_total_apps
            + adstxt_direct_ios_total_apps
            + adstxt_direct_android_total_apps
            + adstxt_reseller_ios_total_apps
            + adstxt_reseller_android_total_apps
        )

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
            sdk_android_installs_d30=int(sdk_android_installs_d30),
            adstxt_direct_android_installs_d30=int(adstxt_direct_android_installs_d30),
            adstxt_reseller_android_installs_d30=int(
                adstxt_reseller_android_installs_d30
            ),
            sdk_ios_rating_count_d30=int(sdk_ios_rating_count_d30),
            adstxt_direct_ios_rating_count_d30=int(adstxt_direct_ios_rating_count_d30),
            adstxt_reseller_ios_rating_count_d30=int(
                adstxt_reseller_ios_rating_count_d30
            ),
        )
    return overview


def get_count(df: pd.DataFrame, condition: pd.Series, column: str) -> int:
    """Safely get count from filtered DataFrame."""
    filtered = df[condition][column]
    return int(filtered.iloc[0]) if not filtered.empty else 0


class CompaniesController(Controller):
    """API EndPoint return for all ad tech companies."""

    path = "/api/"

    @get(path="/companies", cache=86400)
    async def companies(self: Self, state: State) -> CompaniesOverview:
        """Handle GET request for all companies.

        Returns
        -------
        CompaniesOverview
            An overview of companies across different platforms and sources.

        """
        start = time.perf_counter() * 1000

        overview = get_overviews(state=state)
        duration = round((time.perf_counter() * 1000 - start), 2)
        logger.info(f"GET /api/companies took {duration}ms")
        return overview

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

        overview = get_overviews(state=state, category=category)
        duration = round((time.perf_counter() * 1000 - start), 2)
        logger.info(f"GET /api/companies/categories/{category} took {duration}ms")
        return overview

    @get(path="/companies/countries", cache=CACHE_FOREVER)
    async def companies_countries(self: Self, state: State) -> dict:
        """Handle GET request for all companies countries."""
        start = time.perf_counter() * 1000
        df = get_company_countries(state)
        duration = round((time.perf_counter() * 1000 - start), 2)
        logger.info(f"GET /api/companies/countries took {duration}ms")
        return df.to_dict(orient="records")

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

        df = get_company_stats(
            state=state, company_domain=company_domain, app_category=category
        )

        if df["tag_source"].str.contains("app_ads").any():
            ad_domain_overview = get_company_adstxt_ad_domain_overview(
                state=state, ad_domain_url=company_domain
            )
            final_ad_domain_overview = (
                ad_domain_overview.set_index(["store", "relationship"])
                .groupby(level=[0, 1])
                .apply(lambda x: x.iloc[0].dropna().to_dict())
                .unstack(level=0)
                .to_dict()
            )
            publishers_overview = get_company_adstxt_publishers_overview(
                state=state, ad_domain_url=company_domain
            )
            final_publishers_overview = (
                publishers_overview.set_index(["store", "relationship"])
                .groupby(level=[0, 1])
                .apply(lambda x: x.to_dict(orient="records"))
                .unstack(level=0)
                .to_dict()
            )
        else:
            final_ad_domain_overview = None
            final_publishers_overview = None

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
                mediation_adapters = mediation_adapters[
                    mediation_adapters["app_count"] > 1
                ]
            else:
                mediation_adapters = mediation_adapters[
                    mediation_adapters["app_category"] == category
                ]

            mediation_adapters = mediation_adapters.sort_values(
                by="app_count", ascending=False
            ).to_dict(orient="records")
        else:
            mediation_adapters = None

        overview = make_company_stats(df=df)

        overview.adstxt_ad_domain_overview = final_ad_domain_overview
        overview.adstxt_publishers_overview = final_publishers_overview
        overview.mediation_adapters = mediation_adapters
        duration = round((time.perf_counter() * 1000 - start), 2)
        logger.info(f"GET /api/companies/{company_domain} took {duration}ms")
        return overview

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
    ) -> dict:
        """Handle GET request for a specific company parent categories.

        Args:
        ----
        company_domain : str
            The domain of the company to retrieve apps for.

        Returns:
        -------
        dict
            A dictionary of parent categories for the specified company.

        """
        start = time.perf_counter() * 1000

        df = get_company_categories_topn(state=state, company_domain=company_domain)

        duration = round((time.perf_counter() * 1000 - start), 2)
        logger.info(
            f"GET /api/companies/{company_domain}/parentcategories took {duration}ms"
        )
        return df.to_dict(orient="records")

    @get(
        path="/companies/{queried_domain:str}/tree",
        cache=86400,
    )
    async def company_tree(
        self: Self,
        state: State,
        queried_domain: str,
    ) -> ParentCompanyTree:
        """Handle GET request for company tree.

        Args:
        ----
        queried_domain : str
            The name of the company to retrieve apps for.

        Returns:
        -------
        ParentCompanyTree
            An overview of companies, filtered for the specified company and category.

        """
        start = time.perf_counter() * 1000

        df = get_company_tree(state=state, company_domain=queried_domain)

        if df.empty:
            return ParentCompanyTree(
                is_secondary_domain=True,
                is_parent_company=False,
                parent_company_name=None,
                parent_company_domain=None,
                queried_company_domain=queried_domain,
                queried_company_name=queried_domain,
                domains=[],
                children_companies=[],
            )

        is_queried_company = queried_domain == df["company_domain"]
        queried_company_names = df[is_queried_company]["company_name"].tolist()

        queried_company_logo_urls = df[is_queried_company]["company_logo_url"].tolist()

        if len(queried_company_names) > 0:
            queried_company_name = queried_company_names[0]
        else:
            queried_company_name = queried_domain

        parent_company_name = df["parent_company_name"].tolist()[0]
        if parent_company_name == queried_company_name:
            parent_company_name = None
        parent_company_domain = df["parent_company_domain"].tolist()[0]
        if parent_company_domain == queried_domain:
            parent_company_domain = None
        parent_company_logo_url = df["parent_company_logo_url"].tolist()[0]

        if len(queried_company_logo_urls) > 0:
            queried_company_logo_url = queried_company_logo_urls[0]
        else:
            queried_company_logo_url = None

        if parent_company_name == queried_domain:
            parent_company_name = None

        parent_companies = get_parent_companies(state)
        secondary_domains = get_company_secondary_domains(state)
        is_secondary_domain = queried_domain in secondary_domains
        is_parent_company = queried_domain in parent_companies

        domains = (
            df[~(parent_company_name == df["company_name"])]["company_domain"]
            .unique()
            .tolist()
        )
        sub_domains = df["sub_domain"].unique().tolist()
        domains = list(set(domains + sub_domains))

        detailed_domains = make_company_api_domains_dict(state, domains)

        children_companies = (
            df[
                ~(parent_company_name == df["company_name"])
                & (queried_domain != df["company_domain"])
                & df["company_domain"].notna()
            ][["company_name", "company_domain", "company_logo_url"]]
            .drop_duplicates()
            .rename(columns={"company_domain": "domain"})
            .reset_index(drop=True)
            .to_dict(orient="records")
        )

        tree = ParentCompanyTree(
            is_secondary_domain=is_secondary_domain,
            is_parent_company=is_parent_company,
            parent_company_name=parent_company_name,
            parent_company_domain=parent_company_domain,
            queried_company_domain=queried_domain,
            queried_company_name=queried_company_name,
            queried_company_logo_url=queried_company_logo_url,
            parent_company_logo_url=parent_company_logo_url,
            domains=detailed_domains,
            children_companies=children_companies,
        )

        duration = round((time.perf_counter() * 1000 - start), 2)
        logger.info(f"GET /api/companies/{queried_domain}/tree took {duration}ms")

        return tree

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

        # Group by company_name and sdk_name
        for (company, sdk), group in df.groupby(["company_name", "sdk_name"]):
            # Create entry for company if it doesn't exist
            if company not in company_sdks:
                company_sdks[company] = {}

            # Add sdk data
            company_sdks[company][sdk] = {
                "package_patterns": group["package_pattern"].unique().tolist(),
                "paths": [
                    path
                    for path in group["path_pattern"].unique().tolist()
                    if pd.notna(path)
                ],
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
        adnetworks = get_companies_top(
            state=state, type_slug="ad-networks", app_category=None, limit=5
        )
        mmps = get_companies_top(
            state=state, type_slug="ad-attribution", app_category=None, limit=5
        )
        analytics = get_companies_top(
            state=state, type_slug="product-analytics", app_category=None, limit=5
        )
        top_ad_networks = make_top_companies(adnetworks)
        top_mmps = make_top_companies(mmps)
        top_analytics = make_top_companies(analytics)

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
        cache=86400,
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

        overview = CompanyPubIDOverview(
            totals=totals,
            apps=apps,
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
        cache=86400,
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
