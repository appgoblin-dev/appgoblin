"""API for creatives data.

/creatives/app/{store_id} creatives for a specific app
"""

import time
from typing import Self

import pandas as pd
from litestar import Controller, get
from litestar.datastructures import State

from config import get_logger
from dbcon.queries import (
    get_advertiser_creatives,
    get_company_creatives,
)
from dbcon.static import (
    get_advertiser_creative_rankings,
    get_advertiser_creative_rankings_top,
    get_company_logos_df,
)

logger = get_logger(__name__)


def append_ad_networks_dict_to_df(
    df: pd.DataFrame,
    state: State,
    company_domain_column_name: str = "ad_network_domains",
) -> pd.DataFrame:
    """Append a dictionary of company names, domains and logos to a dataframe."""
    company_logos_df = get_company_logos_df(state)

    def get_logo_url(domain: str) -> str:
        try:
            return company_logos_df[company_logos_df["company_domain"] == domain][
                "company_logo_url"
            ].iloc[0]
        except:  # noqa: E722
            return "default_company_logo.png"

    df["ad_networks"] = df[company_domain_column_name].apply(
        lambda x: [
            {"domain": d, "company_logo_url": get_logo_url(d)}
            for d in x
            if d is not None
        ]
    )
    return df


class CreativesController(Controller):
    """Controller holding all API endpoints for creatives."""

    path = "/api/creatives"

    @get(path="/", cache=86400)
    async def advertiser_creative_rankings(self: Self, state: State) -> dict:
        """Handle GET request for a list of apps.

        Returns
        -------
            A dictionary representation of the total counts

        """
        start = time.perf_counter() * 1000
        df = get_advertiser_creative_rankings(state)
        df = df.rename(
            columns={
                "advertiser_icon_url": "app_icon_url",
                "advertiser_name": "name",
                "advertiser_store_id": "store_id",
            }
        )
        df = append_ad_networks_dict_to_df(df=df, state=state)
        df["last_seen"] = df["last_seen"].dt.strftime("%Y-%m-%d")
        df = df.head(100)
        duration = round((time.perf_counter() * 1000 - start), 2)
        logger.info(f"{self.path} took {duration}ms")
        return df.to_dict(orient="records")

    @get(path="/top", cache=86400)
    async def top_advertiser_creative_rankings(self: Self, state: State) -> dict:
        """Handle GET request for a list of top advertiser creative rankings.

        Returns
        -------
            A dictionary representation of the total counts

        """
        start = time.perf_counter() * 1000
        df = get_advertiser_creative_rankings_top(state)
        df = df.rename(
            columns={
                "advertiser_icon_url": "app_icon_url",
                "advertiser_name": "name",
                "advertiser_store_id": "store_id",
            }
        )

        df = append_ad_networks_dict_to_df(state=state, df=df)
        df["last_seen"] = df["last_seen"].dt.strftime("%Y-%m-%d")

        df = df.sort_values(by="unique_publishers", ascending=False)

        duration = round((time.perf_counter() * 1000 - start), 2)
        logger.info(f"{self.path}/top took {duration}ms")
        return df.to_dict(orient="records")

    @get(path="/companies/{company_domain: str}", cache=86400)
    async def company_creatives(
        self: Self, state: State, company_domain: str, shortlist: bool = True
    ) -> dict:
        """Handle GET request for a list of top advertiser creative rankings.

        Returns
        -------
            A dictionary representation of the total counts

        """
        start = time.perf_counter() * 1000
        if shortlist:
            limit = 6
        else:
            limit = 30
        df = get_company_creatives(
            state=state, company_domain=company_domain, limit=limit
        )
        df["creative_thumb_url"] = (
            "https://media.appgoblin.info/creatives/thumbs/" + df["md5_hash"] + ".jpg"
        )
        if not df.empty:
            df["last_seen"] = df["last_seen"].dt.strftime("%Y-%m-%d")
        duration = round((time.perf_counter() * 1000 - start), 2)
        logger.info(f"{self.path}/companies/{company_domain} took {duration}ms")
        return df.to_dict(orient="records")

    @get(path="/apps/{store_id: str}/monetized", cache=3600)
    async def monetized_creatives(self: Self, state: State, store_id: str) -> dict:
        """Handle GET request for a list of creatives used for monetization by an app.

        Returns
        -------
            A dictionary representation of the total counts

        """
        df = get_advertiser_creatives(state=state, pub_store_id=store_id)
        if not df.empty:
            df["run_at"] = df["run_at"].dt.strftime("%Y-%m-%d")
        pdf = (
            df.groupby(
                [
                    "run_at",
                    "adv_name",
                    "adv_store_id",
                    "host_domain",
                    "host_domain_company_domain",
                    "host_domain_company_name",
                    "ad_domain",
                    "ad_domain_company_domain",
                    "ad_domain_company_name",
                    "vhash",
                    "file_extension",
                    "adv_icon_url",
                    "mmp_name",
                    "mmp_domain",
                ],
                dropna=False,
            )[["md5_hash", "additional_ad_domain_urls", "mmp_urls"]]
            .agg(
                {
                    "md5_hash": "first",
                    "additional_ad_domain_urls": lambda x: list(
                        set([item for sublist in x for item in sublist])
                    ),
                    "mmp_urls": lambda x: list(
                        set([item for sublist in x for item in sublist])
                    ),
                }
            )
            .sort_values(by="run_at", ascending=False)
            .reset_index()
        )
        cdf = (
            df.groupby(
                [
                    "vhash",
                    "file_extension",
                ]
            )[["md5_hash"]]
            .first()
            .reset_index()
        )
        return {
            "by_publisher": pdf.to_dict(orient="records"),
            "by_creative": cdf.to_dict(orient="records"),
        }

    @get(path="/apps/{store_id: str}/ads", cache=3600)
    async def advertiser_creatives(self: Self, state: State, store_id: str) -> dict:
        """Handle GET request for a list of creatives for an app.

        Returns
        -------
            A dictionary representation of the total counts

        """
        df = get_advertiser_creatives(state=state, advertiser_store_id=store_id)
        if not df.empty:
            df["run_at"] = df["run_at"].dt.strftime("%Y-%m-%d")

        df["pubs"] = df.apply(
            lambda row: {
                "store_id": row["pub_store_id"],
                "name": row["pub_name"],
                "app_icon_url": row["pub_icon_url"],
            },
            axis=1,
        )
        company_logos_df = get_company_logos_df(state)

        df = df.merge(
            company_logos_df,
            left_on="host_domain_company_domain",
            right_on="company_domain",
            how="left",
            validate="m:1",
        ).merge(
            company_logos_df,
            left_on="ad_domain_company_domain",
            right_on="company_domain",
            how="left",
            validate="m:1",
            suffixes=("_host_domain", "_ad_domain"),
        )

        pdf = (
            df.groupby(
                [
                    "vhash",
                    "host_domain",
                    "host_domain_company_domain",
                    "host_domain_company_name",
                    "ad_domain",
                    "ad_domain_company_domain",
                    "ad_domain_company_name",
                    "company_logo_url_ad_domain",
                    "company_logo_url_host_domain",
                    "file_extension",
                    "mmp_name",
                    "mmp_domain",
                ],
                dropna=False,
            )[
                [
                    "md5_hash",
                    "additional_ad_domain_urls",
                    "mmp_urls",
                    "run_at",
                    "pubs",
                ]
            ]
            .agg(
                {
                    "pubs": lambda x: list({d["store_id"]: d for d in x}.values()),
                    "md5_hash": "first",
                    "run_at": "max",
                    "additional_ad_domain_urls": lambda x: list(
                        {item for sublist in x for item in sublist}
                    ),
                    "mmp_urls": lambda x: list(
                        {item for sublist in x for item in sublist}
                    ),
                }
            )
            .reset_index()
            .sort_values(by="run_at", ascending=False)
        )

        pdf["pubs_count"] = pdf["pubs"].apply(lambda x: len(x))
        pdf = pdf.sort_values(by="pubs_count", ascending=False)

        cdf = (
            df.groupby(
                [
                    "vhash",
                    "file_extension",
                ]
            )[["md5_hash"]]
            .first()
            .reset_index()
        )
        return {
            "by_vhash": pdf.to_dict(orient="records"),
            "by_creative": cdf.to_dict(orient="records"),
        }

    @get(path="/apps/{store_id: str}/ads/{vhash: str}", cache=3600)
    async def get_advertiser_creative_records(
        self: Self, state: State, store_id: str, vhash: str
    ) -> dict:
        """Handle GET request for a list of creatives for an app.

        Returns
        -------
            A dictionary representation of the total counts

        """
        df = get_advertiser_creatives(state=state, advertiser_store_id=store_id)
        df["run_at"] = df["run_at"].dt.strftime("%Y-%m-%d")
        df = df[df["vhash"] == vhash]
        pdf = (
            df.groupby(
                [
                    "run_at",
                    "pub_name",
                    "pub_store_id",
                    "host_domain",
                    "host_domain_company_domain",
                    "host_domain_company_name",
                    "ad_domain",
                    "ad_domain_company_domain",
                    "ad_domain_company_name",
                    "vhash",
                    "file_extension",
                    "pub_icon_url",
                ]
            )[["md5_hash"]]
            .first()
            .reset_index()
        )

        return {
            "by_publisher": pdf.to_dict(orient="records"),
        }
