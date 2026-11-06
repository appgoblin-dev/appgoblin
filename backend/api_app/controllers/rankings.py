"""API endoipoints for app store rankings.

/rankings/ of all apps as pulled from stores
"""

import datetime
import time
from typing import Self

import pandas as pd
from litestar import Controller, get
from litestar.config.response_cache import CACHE_FOREVER
from litestar.datastructures import State

from api_app.models import (
    RankingOverview,
    StoreCategoryDetail,
    StoreCollections,
    StoreRankings,
)
from api_app.utils import extend_app_icon_url
from config import get_logger
from dbcon.queries import (
    get_ctv_app_ranks,
    get_history_top_ranks,
    get_most_recent_top_ranks,
)
from dbcon.static import get_store_collection_category_map

logger = get_logger(__name__)


def ranking_map(state: State) -> RankingOverview:
    """Get Ranking data and translate to RankingOverview class."""
    df = get_store_collection_category_map(state=state)
    overview = RankingOverview()
    groups = df.groupby(["store_id", "store_name"])
    for store_idx, group in groups:
        store_id = int(store_idx[0])
        store_name = store_idx[1]
        cgroups = group.groupby(["collection_id", "collection_name"])
        rankings = StoreRankings(store_id=store_id, store_name=store_name)
        for col_idx, cgroup in cgroups:
            collection_id = int(col_idx[0])
            collection_name = col_idx[1]
            category_details = [
                StoreCategoryDetail(
                    category_id=int(row["category_id"]),
                    category_name=row["category_name"],
                )
                for _, row in cgroup.iterrows()
                if row["category_id"]
            ]
            rankings.collections.append(
                StoreCollections(
                    collection_id=collection_id,
                    collection_name=collection_name,
                    categories=category_details,
                ),
            )
        overview.stores_rankings.append(rankings)
    return overview


class RankingsController(Controller):
    """Controller returns all ranking related API endpoints."""

    path = "/api/rankings/"

    @get(path="/", cache=CACHE_FOREVER)
    async def get_ranking_overview(self: Self, state: State) -> RankingOverview:
        """Handle GET request for a list of ranking collecitons and categories.

        Returns
        -------
            A dictionary representation of the list of categories
            each with an id, name, type and total of apps

        """
        logger.info(f"{self.path} start")
        overview = ranking_map(state=state)

        return overview

    @get(path="/ctv/{store:int}", cache=86400)
    async def get_ctv_app_ranks(
        self: Self,
        state: State,
        store: int,
        limit: int = 50,
    ) -> dict:
        """Handle GET request for the top CTV-supported apps in a store.

        Returns
        -------
            A dictionary of the top apps ranked by monthly installs

        """
        start = time.perf_counter() * 1000
        df = get_ctv_app_ranks(state, store=store, limit=limit)
        df = extend_app_icon_url(df)
        duration = round((time.perf_counter() * 1000 - start), 2)
        logger.info(f"{self.path}/ctv/{store} took {duration}ms")
        return {"apps": df.to_dict(orient="records")}

    @get(path="/{collection:int}/{category:int}/short", cache=86400)
    async def get_short_ranks_for_category(
        self: Self,
        state: State,
        collection: int,
        category: int,
    ) -> dict:
        """Handle GET request for a store/collection/category rank.

        Returns
        -------
            A dictionary representation of a category
            with ios and google apps

        """
        start = time.perf_counter() * 1000
        df = get_most_recent_top_ranks(
            state,
            collection_id=collection,
            category_id=category,
            limit=5,
        )
        ranks_dict = df.to_dict(orient="records")
        duration = round((time.perf_counter() * 1000 - start), 2)
        logger.info(f"{self.path}/{collection}/{category}/short took {duration}ms")
        return {"ranks": ranks_dict}

    @get(path="/{collection:int}/{category:int}", cache=86400)
    async def get_ranks_for_category(
        self: Self,
        state: State,
        collection: int,
        category: int,
        country: str = "US",
    ) -> dict:
        """Handle GET request for store/collection/category rank.

        Returns
        -------
            A dictionary representation of a category
            with ios and google apps

        """
        start = time.perf_counter() * 1000

        df = get_most_recent_top_ranks(
            state,
            collection_id=collection,
            category_id=category,
            country=country,
            limit=200,
        )
        ranks_dict = df.to_dict(orient="records")
        duration = round((time.perf_counter() * 1000 - start), 2)
        logger.info(f"{self.path}/{collection}/{category} took {duration}ms")
        return {"ranks": ranks_dict}

    @get(path="/{collection:int}/{category:int}/history", cache=86400)
    async def get_ranks_history_for_category(
        self: Self,
        state: State,
        collection: int,
        category: int,
        country: str = "US",
    ) -> dict:
        """Handle GET request for a store/collection/category rank.

        Returns
        -------
            A list of dictionary representation of a category history
            with ios or google apps

        """
        start = time.perf_counter() * 1000
        df = get_history_top_ranks(
            state,
            collection_id=collection,
            category_id=category,
            country=country,
            limit=10,
            days=40,
        )
        df["crawled_date"] = pd.to_datetime(df["crawled_date"])
        last_crawled_date = df["crawled_date"].max()
        # Sort by 'crawled_date' to make sure the latest dates are last
        df = df.sort_values("crawled_date", ascending=True)
        # NOTE: don't include 'rank' in group by as table is already unique by that
        # Need to get each apps location on that time
        df = (
            df.groupby([pd.Grouper(key="crawled_date", freq="1W"), "name"])
            .last()
            .reset_index()
        )
        df.loc[
            df["crawled_date"].dt.date >= datetime.datetime.now(datetime.UTC).date(),
            "crawled_date",
        ] = last_crawled_date
        df["crawled_date"] = pd.to_datetime(df["crawled_date"]).dt.strftime("%Y-%m-%d")
        hist_dict = (
            df.pivot_table(columns=["name"], index=["crawled_date"], values="rank")
            .reset_index()
            .to_dict(orient="records")
        )
        duration = round((time.perf_counter() * 1000 - start), 2)
        logger.info(f"{self.path}/{collection}/{category}/history took {duration}ms")
        return {"history": hist_dict}
