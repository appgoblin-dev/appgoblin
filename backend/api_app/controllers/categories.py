"""Return API endpoint for categories.

/categories/{category_id} a specific app
"""

import time
from typing import Self

import numpy as np
from litestar import Controller, get
from litestar.config.response_cache import CACHE_FOREVER
from litestar.datastructures import State

from api_app.models import CategoriesOverview
from config import get_logger
from dbcon.queries import (
    get_country_map,
)
from dbcon.static import get_appstore_categories

logger = get_logger(__name__)


def category_overview(state: State) -> CategoriesOverview:
    """Categories for apps."""
    cats = get_appstore_categories(state=state)
    cats = cats[cats["total_apps"] > 100]  # noqa: PLR2004 magic number ok

    cats["name"] = cats["category"]
    cats["name"] = (
        cats["name"]
        .str.replace("game_", "Games: ")
        .str.replace("_and_", " & ")
        .str.replace("_", " ")
        .str.title()
    )
    cats = cats.rename(columns={"category": "id"})

    summary = cats[["android", "ios", "total_apps"]].sum()
    summary["name"] = "Overall"
    summary["id"] = "overall"
    cats.loc["Overall"] = summary

    cats[["android", "ios", "total_apps"]] = cats[
        ["android", "ios", "total_apps"]
    ].astype(int)

    cats = cats.sort_values("total_apps", ascending=False)

    android_games_total = cats[cats.id.str.startswith("game")]["android"].sum()

    cats.loc[cats["id"] == "games", "android"] = android_games_total

    cats["type"] = np.where(
        cats.id.str.contains("_game|games", regex=True), "game", "app"
    )

    cats["sort_priority"] = 2
    cats.loc[cats["id"] == "overall", "sort_priority"] = 0
    cats.loc[(cats["id"] == "games") | (cats["name"] == "Games"), "sort_priority"] = 1

    cats = cats.sort_values(["sort_priority", "type", "name"])
    cats = cats.drop(columns=["sort_priority"])

    category_dicts = cats.to_dict(orient="records")

    overview = CategoriesOverview(categories=category_dicts)

    return overview


class CategoryController(Controller):
    """App Store Categories API."""

    path = "/api/categories"

    @get(path="/countries", cache=CACHE_FOREVER)
    async def get_countries(self: Self, state: State) -> dict:
        """Handle GET request for all countries."""
        df = get_country_map(state)
        country_dict = df.set_index("alpha2")["langen"].to_dict()
        return country_dict

    @get(path="/", cache=CACHE_FOREVER)
    async def get_categories_overview(self: Self, state: State) -> CategoriesOverview:
        """Handle GET request for a list of categories.

        Returns
        -------
            A dictionary representation of the list of categories
            each with an id, name, type and total of apps

        """
        start = time.perf_counter() * 1000
        overview = category_overview(state=state)
        duration = round((time.perf_counter() * 1000 - start), 2)
        logger.info(f"{self.path} took {duration}ms")
        return overview
