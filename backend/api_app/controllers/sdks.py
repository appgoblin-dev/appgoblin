"""API endoipoints for sdks.

/sdks/overview returns list of all sdks.
/sdks/user_requested returns list of user requested sdks.
/sdks/{value_pattern} returns list of sdks for a given pattern.
/sdks/{value_pattern}/companies returns list of companies for a given pattern.
"""

import time
from typing import Self

import pandas as pd
from litestar import Controller, Response, get, post
from litestar.background_tasks import BackgroundTask
from litestar.datastructures import State

from api_app.models import (
    SdkCompanies,
    SdkOverview,
    SdksLatestResults,
    SdksUserRequested,
)
from api_app.report_exports import (
    create_report_id,
    run_sdk_export_job,
    run_sdk_pattern_export_job,
    validate_export_dependencies,
)
from config import get_logger
from dbcon.queries import (
    get_latest_sdks,
    get_sdk,
    get_sdk_companies,
    get_sdk_pattern,
    get_sdk_pattern_companies,
    get_sdk_pattern_count,
    get_sdk_patterns,
    get_user_requested_latest_sdks,
)
from dbcon.static import get_company_logos_df

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

        overview_resp = SdkOverview(
            apps=overview.to_dict(orient="records"),
            total_count=get_sdk_pattern_count(state, value_pattern),
        )

        duration = round((time.perf_counter() * 1000 - start), 2)
        logger.info(f"{self.path}/{value_pattern} took {duration}ms")
        return overview_resp

    @get(path="/appgoblin/{sdk_slug:str}", cache=3600)
    async def sdk_detail(self: Self, state: State, sdk_slug: str) -> dict:
        """Return metadata, mapped patterns, the owner, and top apps for one SDK."""
        companies = get_sdk_companies(state, sdk_slug)
        sdk_id = (
            int(companies.iloc[0]["sdk_id"])
            if not companies.empty and pd.notna(companies.iloc[0]["sdk_id"])
            else None
        )
        apps = (
            get_sdk(state, sdk_id, limit=10) if sdk_id is not None else pd.DataFrame()
        )
        patterns = get_sdk_patterns(state, sdk_slug)
        owner = companies.iloc[0].to_dict() if not companies.empty else {}
        if owner.get("company_domain"):
            company_logos = get_company_logos_df(state).drop_duplicates(
                subset=["company_domain"], keep="first"
            )
            logo = company_logos[
                company_logos["company_domain"] == owner["company_domain"]
            ]
            if not logo.empty:
                owner["company_logo_url"] = logo.iloc[0].get("company_logo_url")

        def pattern_rows(pattern_type: str) -> list[dict]:
            rows = patterns[
                patterns["pattern_type"].astype(str).str.lower() == pattern_type
            ]
            return [
                {
                    "pattern": str(row.pattern_value),
                    "app_count": None if pd.isna(row.app_count) else int(row.app_count),
                }
                for row in rows.itertuples(index=False)
                if pd.notna(row.pattern_value)
            ]

        return {
            "sdk_id": sdk_id,
            "sdk_name": apps.iloc[0]["sdk_name"] if not apps.empty else sdk_slug,
            "apps": apps.to_dict(orient="records"),
            "owner": owner,
            "patterns": {
                "package_patterns": pattern_rows("package"),
                "paths": pattern_rows("path"),
                "mediation_patterns": pattern_rows("mediation"),
                "adapter_patterns": pattern_rows("adapter"),
            },
        }

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

        if not overview.empty:
            company_logos = get_company_logos_df(state).drop_duplicates(
                subset=["company_domain"], keep="first"
            )
            overview = overview.merge(
                company_logos[["company_domain", "company_logo_url"]],
                on="company_domain",
                how="left",
                validate="m:1",
            )

        overview_dict = overview.to_dict(orient="records")

        overview_resp = SdkCompanies(companies=overview_dict)

        duration = round((time.perf_counter() * 1000 - start), 2)
        logger.info(f"{self.path}/{value_pattern}/companies took {duration}ms")
        return overview_resp

    @post(path="/{value_pattern:str}/export")
    async def export_sdk_pattern(
        self: Self, state: State, value_pattern: str, data: dict
    ) -> Response:
        """Queue an unrestricted SDK pattern CSV export."""
        validate_export_dependencies()
        recipient_email = str(data.get("recipient_email", "")).strip()
        user_id = data.get("user_id")
        if not recipient_email or not isinstance(user_id, int) or user_id <= 0:
            return Response(
                {"success": False, "error": "recipient_email and user_id are required"},
                status_code=400,
            )

        report_id = create_report_id()
        return Response(
            {
                "success": True,
                "report_id": report_id,
                "message": "Export queued. A download link will be sent by email.",
            },
            background=BackgroundTask(
                run_sdk_pattern_export_job,
                state=state,
                pattern=value_pattern,
                recipient_email=recipient_email,
                report_id=report_id,
                user_id=user_id,
            ),
        )

    @post(path="/id/{sdk_id:int}/export")
    async def export_sdk(self: Self, state: State, sdk_id: int, data: dict) -> Response:
        """Queue an unrestricted exact SDK CSV export."""
        validate_export_dependencies()
        recipient_email = str(data.get("recipient_email", "")).strip()
        user_id = data.get("user_id")
        if not recipient_email or not isinstance(user_id, int) or user_id <= 0:
            return Response(
                {"success": False, "error": "recipient_email and user_id are required"},
                status_code=400,
            )

        report_id = create_report_id()
        sdk_label = (
            str(data.get("sdk_slug") or data.get("sdk_name") or "").strip() or None
        )
        latest_only = data.get("latest_only", False) is True
        return Response(
            {
                "success": True,
                "report_id": report_id,
                "message": "Export queued. A download link will be sent by email.",
            },
            background=BackgroundTask(
                run_sdk_export_job,
                state=state,
                sdk_id=sdk_id,
                sdk_label=sdk_label,
                recipient_email=recipient_email,
                report_id=report_id,
                user_id=user_id,
                latest_only=latest_only,
            ),
        )
