"""Scry API controllers.

PUBLIC

"""

import time
from typing import Self

import pandas as pd
from litestar import Controller, Response, post
from litestar.background_tasks import BackgroundTask
from litestar.datastructures import State

from config import CONFIG, get_logger
from dbcon.queries import (
    get_apps_sdk_overview,
    insert_sdk_scan_request,
)
from dbcon.static import get_company_logos_df

logger = get_logger(__name__)


def log_umami_event(ip: str | None, url: str) -> None:
    """Log an umami event.

    This function is called when a user requests SDKs.
    This is only for seeing how often the backend is calleda
    and not needed if you are recreating for other reasons.

    """
    import umami

    umami_base_url = CONFIG["umami"].get("base_url")
    umami_site_id = CONFIG["umami"].get("site_id")
    umami.set_url_base(umami_base_url)
    umami.set_website_id(umami_site_id)
    umami.set_hostname("dev.thirdgate.appgoblin")
    umami.new_page_view(
        page_title="User Requested SDKs",
        url=url,
        referrer="dev.thirdgate.appgoblin",
        ip_address=ip,
    )


def process_sdk_scan_request(
    state, store_ids: list[str], ip: str | None, user_id: int | None
) -> None:
    """Process a sdk scan request."""
    url = "/api/public/sdks/apps/requestSDKScan"
    try:
        log_umami_event(ip, url)
        logger.info("logged umami event")
    except Exception:
        logger.exception("Error logging umami event")
    try:
        insert_sdk_scan_request(state, store_ids, user_id)
        logger.info(f"inserted sdk scan request for {len(store_ids)} store_ids")
    except Exception:
        logger.exception("Error inserting sdk scan request")


def process_get_sdks(state: State, store_ids_dict: list[dict], ip: str | None) -> None:
    """Process a sdk request."""
    url = "/api/public/sdks/apps"
    try:
        log_umami_event(ip, url)
        logger.info("logged umami event")
    except Exception:
        logger.exception("Error logging umami event")
    try:
        add_store_ids(state, store_ids_dict)
    except Exception:
        logger.exception("Error adding store ids")


class ScryController(Controller):
    """API EndPoint return for all sdk related paths."""

    path = "/api/public/"

    @post(path="sdks/apps")
    async def lookup_apps(
        self: Self, state: State, headers: dict[str, str], data: dict
    ) -> dict:
        """Lookup apps' SDKs by store_ids."""
        start = time.perf_counter() * 1000
        store_ids = data.get("store_ids", [])

        df = get_apps_sdk_overview(state, store_ids=tuple(store_ids))
        df = df.merge(
            get_company_logos_df(state),
            left_on="company_domain",
            right_on="company_domain",
            how="left",
            validate="m:1",
        )
        df["company_logo_url"] = df["company_logo_url"].fillna(
            "default_company_logo.png"
        )
        df["company_logo_url"] = df["company_logo_url"].apply(
            lambda x: f"https://media.appgoblin.info/{x}"
        )
        duration = round((time.perf_counter() * 1000 - start), 2)
        logger.info(f"Scry: lookup_apps db query took {duration}ms")

        if df["company_domain"].isna().sum() > 0:
            logger.error(
                f"Scry: {df[df['company_domain'].isna()]} SDKs have no company domain"
            )
            df = df[df["company_domain"].notna()]

        store_ids_df = df[["store_id"]].drop_duplicates()
        store_ids_df["store"] = 1
        store_ids_dict = store_ids_df.to_dict(orient="records")
        success_store_ids = store_ids_df["store_id"].unique().tolist()
        failed_store_ids = [
            store_id for store_id in store_ids if store_id not in success_store_ids
        ]
        cats = df.loc[df["category_slug"].notna(), "category_slug"].unique().tolist()
        company_cats = {}
        for cat in cats:
            company_cats[cat] = (
                df[df["category_slug"] == cat]
                .groupby(
                    [
                        "company_name",
                        "company_domain",
                        "percent_open_source",
                        "company_logo_url",
                    ]
                )
                .apply(
                    lambda x: pd.Series(
                        {
                            "count": len(x),
                            "apps": x[["store", "store_id", "app_name"]].to_dict(
                                orient="records"
                            ),
                        }
                    )
                )
                .reset_index()
                .sort_values("count", ascending=False)
                .to_dict(orient="records")
            )
        if df.shape[0] > 0:
            by_store_id_dict = (
                df.groupby(["store_id"])[
                    [
                        "category_slug",
                        "company_name",
                        "company_domain",
                        "company_logo_url",
                        "percent_open_source",
                    ]
                ]
                .apply(lambda x: x.to_dict(orient="records"))
                .to_dict()
            )
        else:
            by_store_id_dict = {}

        my_dict = {
            "sdks_by_store_id": by_store_id_dict,
            "company_categories": cats,
            "sdks_by_company_category": company_cats,
            "failed_store_ids": failed_store_ids,
            "success_store_ids": success_store_ids,
        }

        if headers and "X-Forwarded-For" in headers:
            ip = headers["X-Forwarded-For"]
        elif headers and "x-forwarded-for" in headers:
            ip = headers["x-forwarded-for"]
        else:
            ip = None

        logger.info(
            f"Scry: store_ids:{len(success_store_ids)} found SDKs:{df.shape[0]}"
        )
        duration = round((time.perf_counter() * 1000 - start), 2)
        logger.info(f"Scry: lookup_apps response took {duration}ms")
        return Response(
            my_dict,
            background=BackgroundTask(process_get_sdks, state, store_ids_dict, ip),
        )

    @post(path="sdks/apps/requestSDKScan")
    async def lookup_apps_request(
        self: Self, state: State, headers: dict[str, str], data: dict
    ) -> dict:
        """Lookup apps' SDKs by store_ids."""
        store_ids = data.get("store_ids", [])

        if headers and "X-Forwarded-For" in headers:
            ip = headers["X-Forwarded-For"]
        elif headers and "x-forwarded-for" in headers:
            ip = headers["x-forwarded-for"]
        else:
            ip = None

        logger.info(f"Scry: store_ids:{len(store_ids)} request SDK Scan")
        return Response(
            {"status": "ok"},
            background=BackgroundTask(
                process_sdk_scan_request, state, store_ids, ip, user_id=None
            ),
        )
