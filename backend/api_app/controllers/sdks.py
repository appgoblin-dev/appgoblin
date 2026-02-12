"""API endoipoints for sdks.

/sdks/overview returns list of all sdks.
/sdks/user_requested returns list of user requested sdks.
/sdks/{value_pattern} returns list of sdks for a given pattern.
/sdks/{value_pattern}/companies returns list of companies for a given pattern.
"""

import time
from typing import Self

import pandas as pd
from litestar import Controller, get
from litestar.datastructures import State

from api_app.models import (
    SdkCompanies,
    SdkOverview,
    SdksLatestResults,
    SdksUserRequested,
)
from config import get_logger
from dbcon.queries import (
    get_latest_sdks,
    get_sdk_pattern,
    get_sdk_pattern_companies,
    get_user_requested_latest_sdks,
)

logger = get_logger(__name__)


class SdksController(Controller):
    """API EndPoint return for all sdk related paths."""

    path = "/api/sdks"

    @get(path="/latest", cache=12000)
    async def sdks_latest_results(self: Self, state: State) -> SdksLatestResults:
        """Handle GET request for all sdks.

        Returns
        -------
        SdksOverview
            An overview of sdks across different platforms and sources.

        """
        start = time.perf_counter() * 1000

        latest_apps = get_latest_sdks(state)

        is_success = latest_apps["crawl_result"] == 1

        is_google_apps = latest_apps["store"].str.startswith("Google")
        android_success_latest_apps = latest_apps[is_google_apps & is_success]
        ios_success_latest_apps = latest_apps[~is_google_apps & is_success]

        android_failed_latest_apps = latest_apps[is_google_apps & ~is_success]
        ios_failed_latest_apps = latest_apps[~is_google_apps & ~is_success]

        android_success_latest_apps_dict = android_success_latest_apps.to_dict(
            orient="records"
        )
        ios_success_latest_apps_dict = ios_success_latest_apps.to_dict(orient="records")
        android_failed_latest_apps_dict = android_failed_latest_apps.to_dict(
            orient="records"
        )
        ios_failed_latest_apps_dict = ios_failed_latest_apps.to_dict(orient="records")

        duration = round((time.perf_counter() * 1000 - start), 2)
        logger.info(f"{self.path}/overview took {duration}ms")

        return SdksLatestResults(
            android_success_latest_apps=android_success_latest_apps_dict,
            ios_success_latest_apps=ios_success_latest_apps_dict,
            android_failed_latest_apps=android_failed_latest_apps_dict,
            ios_failed_latest_apps=ios_failed_latest_apps_dict,
        )

    @get(path="/user_requested", cache=3600)
    async def sdks_user_requested(self: Self, state: State) -> SdksUserRequested:
        """Handle GET request for all sdks.

        Returns
        -------
        SdksUserRequested
            A list of user requested apps.

        """
        start = time.perf_counter() * 1000

        df = get_user_requested_latest_sdks(state)

        df = df.replace({pd.NaT: None})

        user_requested_latest_apps_dict = df.to_dict(orient="records")

        duration = round((time.perf_counter() * 1000 - start), 2)
        logger.info(f"{self.path}/user_requested took {duration}ms")

        return SdksUserRequested(
            user_requested_latest_apps=user_requested_latest_apps_dict
        )

    @get(path="/{value_pattern:str}", cache=3600)
    async def sdks_pattern(self: Self, state: State, value_pattern: str) -> SdkOverview:
        """Handle GET request for all sdks.

        Returns
        -------
        SdkOverview
            An overview of apps for a given sdk pattern.

        """
        start = time.perf_counter() * 1000

        overview = get_sdk_pattern(state, value_pattern)

        is_google = overview["store"].str.startswith("Google")
        android_overview = overview[is_google]
        ios_overview = overview[~is_google]

        ios_overview_dict = ios_overview.to_dict(orient="records")
        android_overview_dict = android_overview.to_dict(orient="records")

        overview_resp = SdkOverview(
            ios_overview=ios_overview_dict, android_overview=android_overview_dict
        )

        duration = round((time.perf_counter() * 1000 - start), 2)
        logger.info(f"{self.path}/{value_pattern} took {duration}ms")
        return overview_resp

    @get(path="/{value_pattern:str}/companies", cache=3600)
    async def sdks_companies(
        self: Self, state: State, value_pattern: str
    ) -> SdkCompanies:
        """Handle GET request for all sdks.

        Returns
        -------
        SdkOverview
            An overview of apps for a given sdk pattern.

        """
        start = time.perf_counter() * 1000

        overview = get_sdk_pattern_companies(state, value_pattern)

        overview_dict = overview.to_dict(orient="records")

        overview_resp = SdkCompanies(companies=overview_dict)

        duration = round((time.perf_counter() * 1000 - start), 2)
        logger.info(f"{self.path}/{value_pattern}/companies took {duration}ms")
        return overview_resp
