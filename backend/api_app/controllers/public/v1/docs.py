"""Public API v1 documentation endpoints."""

from copy import deepcopy
from typing import Any, Self

from litestar import Controller, Request, get
from litestar.enums import MediaType, OpenAPIMediaType
from litestar.openapi.plugins import ScalarRenderPlugin

V1_PATH_PREFIX = "/api/v1/"
V1_DOCS_PATH_PREFIX = "/api/v1/docs/"
V1_OPENAPI_JSON_PATH = "/api/v1/docs/openapi.json"
PUBLIC_API_SERVER_URL = "https://appgoblin.info"
PUBLIC_PRICING_URL = f"{PUBLIC_API_SERVER_URL}/pricing"
PUBLIC_OPENAPI_JSON_URL = f"{PUBLIC_API_SERVER_URL}{V1_OPENAPI_JSON_PATH}"
SCALAR_CSS_URL = "data:text/css,"
APP_BASICS_EXAMPLE_STORE_ID = "dev.thirdgate.appgoblin"
KEYWORD_OVERVIEW_EXAMPLE_KEYWORD = "app privacy"
APP_BASICS_EXAMPLE_RESPONSE = {
    "name": "AppGoblin: Scan Trackers & SDK",
    "store_id": APP_BASICS_EXAMPLE_STORE_ID,
    "store": "Google Play",
    "category": "tools",
    "rating": 0,
    "rating_count": 0,
    "installs": 37,
    "weekly_active_users": 3,
    "monthly_active_users": 4,
    "monthly_ad_revenue": 0.0,
    "monthly_iap_revenue": 0.0,
    "installs_weekly": 1,
    "installs_monthly": 6.0,
    "rating_count_weekly": None,
    "store_last_updated": "2026-03-14",
    "developer_id": "9106252563958903597",
    "developer_name": "3rd Gate",
    "developer_url": "appgoblin.info",
    "release_date": "2025-03-16",
    "ad_supported": False,
    "in_app_purchases": False,
    "tv_supported": False,
    "store_link": (
        "https://play.google.com/store/apps/details?id=dev.thirdgate.appgoblin"
    ),
}
COMPANIES_INDEX_EXAMPLE_RESPONSE = [
    {
        "name": "Unity",
        "company_domain": "unity.com",
        "parent_company_domain": None,
        "parent_company_name": None,
        "api_ip_resolved_country": "US",
        "total_app_count": 145_516,
        "installs_d30": 96_783_797_489,
        "trends_latest_period": "2026Q1",
        "google_sdk_latest_pct_market_share": 18.34,
        "apple_sdk_latest_pct_market_share": 7.91,
        "google_app_ads_direct_latest_pct_market_share": 2.06,
        "apple_app_ads_direct_latest_pct_market_share": 0.73,
        "google_sdk_latest_pct_market_share_change": 4.63,
        "apple_sdk_latest_pct_market_share_change": 1.82,
        "google_app_ads_direct_latest_pct_market_share_change": -0.57,
        "apple_app_ads_direct_latest_pct_market_share_change": 0.14,
        "google_sdk_latest_total_apps": 51_202,
        "apple_sdk_latest_total_apps": 16_887,
        "google_app_ads_direct_latest_total_apps": 1_904,
        "apple_app_ads_direct_latest_total_apps": 612,
        "google_sdk_latest_apps_added": 1487,
        "apple_sdk_latest_apps_added": 311,
        "google_app_ads_direct_latest_apps_added": 127,
        "apple_app_ads_direct_latest_apps_added": 42,
        "google_sdk_latest_apps_lost": 221,
        "apple_sdk_latest_apps_lost": 18,
        "google_app_ads_direct_latest_apps_lost": 406,
        "apple_app_ads_direct_latest_apps_lost": 27,
    }
]
COMPANY_OVERVIEW_EXAMPLE_DOMAIN = "unity.com"
COMPANY_OVERVIEW_EXAMPLE_RESPONSE = {
    "domain_is_mapped": True,
    "company_types": [
        "ad-networks",
        "development-tools",
        "mediation",
    ],
    "metrics": {
        "total_apps": 0,
        "adstxt_direct_android_total_apps": 99976,
        "adstxt_direct_ios_total_apps": 45540,
        "adstxt_reseller_android_total_apps": 40957,
        "adstxt_reseller_ios_total_apps": 19469,
        "sdk_android_total_apps": 39452,
        "sdk_ios_total_apps": 16381,
        "sdk_total_apps": 55833,
        "api_android_total_apps": 11175,
        "api_total_apps": 11175,
        "sdk_android_installs_d30": 86325326083,
        "sdk_ios_installs_d30": 31415926535,
        "adstxt_direct_android_installs_d30": 96783797489,
        "adstxt_reseller_android_installs_d30": 42347935007,
    },
    "trends": {
        "latest_period": "2026Q1",
        "android_app_ads_direct_market_share_change_pct": -0.57,
        "android_app_ads_direct_apps_lost": 406,
        "android_sdk_api_market_share_change_pct": 4.63,
        "android_sdk_api_apps_lost": 221,
        "ios_app_ads_direct_market_share_change_pct": 0.14,
        "ios_app_ads_direct_apps_lost": 27,
        "ios_sdk_api_market_share_change_pct": 1.82,
        "ios_sdk_api_apps_lost": 18,
    },
    "mapping_notice": None,
    "datasets": {
        "sdk_api_android": {
            "available": True,
            "estimated_rows": 39452,
            "url": "example.csv",
        },
        "sdk_api_ios": {
            "available": True,
            "estimated_rows": 16381,
            "url": "exampl.csv",
        },
    },
}
COMPANY_APPS_ADDED_EXAMPLE_RESPONSE = {
    "company_domain": "unity.com",
    "tag_source": "sdk",
    "year": 2026,
    "quarter": 1,
    "status": "added",
    "android_apps": ["com.example.first"],
    "ios_apps": ["id1234567890"],
}
KEYWORD_METRICS_EXAMPLE_RESPONSE = {
    "keyword": KEYWORD_OVERVIEW_EXAMPLE_KEYWORD,
    "country": "US",
    "android": {
        "app_count": 420,
        "total_apps": 1960,
        "median_competitor_installs": 250000,
        "avg_competitor_rating": 4.3,
        "major_competitors": 18,
        "volume_competition_score": 73.1,
        "keyword_difficulty": 61.2,
        "opportunity_score": 69.8,
        "competitiveness_score": 64.5,
    },
    "ios": {
        "app_count": 215,
        "total_apps": 910,
        "median_competitor_installs": 175000,
        "avg_competitor_rating": 4.6,
        "major_competitors": 11,
        "volume_competition_score": 68.4,
        "keyword_difficulty": 57.9,
        "opportunity_score": 71.3,
        "competitiveness_score": 59.4,
    },
}
KEYWORD_RANKS_EXAMPLE_RESPONSE = {
    "keyword": KEYWORD_OVERVIEW_EXAMPLE_KEYWORD,
    "country": "US",
    "android": [
        {
            "name": "AppGoblin: Scan Trackers & SDK",
            "store_id": "dev.thirdgate.appgoblin",
            "category": "tools",
            "installs": 37,
            "rating_count": 0,
            "app_icon_url": "https://media.appgoblin.info/app-icons/dev.thirdgate.appgoblin/icon.png",
            "latest_rank": 4,
            "best_rank_d30": 2,
        }
    ],
    "ios": [
        {
            "name": "AppGoblin for iPhone",
            "store_id": "id1234567890",
            "category": "utilities",
            "installs": 1200,
            "rating_count": 94,
            "app_icon_url": "https://media.appgoblin.info/app-icons/id1234567890/icon.png",
            "latest_rank": 6,
            "best_rank_d30": 3,
        }
    ],
}
CTV_APP_RANKS_EXAMPLE_RESPONSE = {
    "store": "Google Play",
    "country": "US",
    "apps": [
        {
            "rank": 1,
            "name": "YouTube",
            "store_id": "com.google.android.youtube",
            "store": "Google Play",
            "category": "video_players",
            "developer_name": "Google LLC",
            "rating": 4.12,
            "rating_count": 145_000_000,
            "installs": 12_000_000_000,
            "monthly_installs": 42_500_000.0,
            "monthly_revenue": 8_250_000.0,
            "installs_z_score_2w": 812.4,
            "country": "US",
            "app_icon_url": (
                "https://media.appgoblin.info/app-icons/"
                "com.google.android.youtube/icon.png"
            ),
        }
    ],
}
APP_VERSION_TIMELINE_EXAMPLE_STORE_ID = "dev.thirdgate.appgoblin"
APP_VERSION_TIMELINE_EXAMPLE_RESPONSE = [
    {
        "app_version_code": "42",
        "sdk_scan_result": "success",
        "sdks_last_scanned_at": "2026-07-22T10:15:00Z",
        "downloaded_at": "2026-07-21T14:32:08Z",
    }
]
APP_SDK_HISTORY_EXAMPLE_RESPONSE = {
    "history": [
        {
            "company_name": "Adjust",
            "company_domain": "adjust.com",
            "sdk_name": "Adjust SDK",
            "version_code": "42",
            "version_code_created_at": "2026-07-21T14:32:08Z",
            "sdk_scan_result": "success",
            "status": "added",
            "company_logo_url": "company-logos/adjust.png",
        },
        {
            "company_name": None,
            "company_domain": None,
            "sdk_name": None,
            "version_code": "41",
            "version_code_created_at": "2026-07-14T09:00:00Z",
            "sdk_scan_result": "success",
            "status": "no_change",
            "company_logo_url": None,
        },
    ]
}
ADVERTISER_CREATIVES_EXAMPLE_HOST_DOMAIN = "applovin.com"
ADVERTISER_CREATIVES_EXAMPLE_RESPONSE = {
    "host_domain": ADVERTISER_CREATIVES_EXAMPLE_HOST_DOMAIN,
    "creatives": [
        {
            "created_at": "2026-07-21T14:32:08.000Z",
            "ad_domain": "applovin.com",
            "host_domain_company_name": "AppLovin",
            "pub_store_id": "com.example.publisher",
            "pub_name": "Example Publisher",
            "vhash": "a1b2c3d4e5f6",
            "md5_hash": "9f8e7d6c5b4a39281827364554637281",
            "file_extension": "mp4",
            "adv_store_id": "com.applovin.app",
            "mmp_domain": "appsflyer.com",
            "creative_url": (
                "https://media.appgoblin.info/creatives/raw/9f8/"
                "9f8e7d6c5b4a39281827364554637281.mp4"
            ),
        }
    ],
}
V1_OPERATION_DOCS = {
    "/api/v1/apps/search": {
        "get": {
            "summary": "Search apps",
            "description": (
                "Search app names and identifiers with `q`. Results are limited "
                "by `limit` (1-100, default 20)."
            ),
        }
    },
    "/api/v1/apps/search/developers": {
        "get": {
            "summary": "Search apps by developer",
            "description": (
                "Find apps by developer name with `q`. Results are limited "
                "by `limit` (1-100, default 20)."
            ),
        }
    },
    "/api/v1/companies/search": {
        "get": {
            "summary": "[Paid] Search companies",
            "description": (
                "Search company names and domains with `q`. Paid tiers only. "
                "Results are limited by `limit` (1-100, default 20)."
            ),
        }
    },
    "/api/v1/companies": {
        "get": {
            "summary": "[Paid] /companies",
            "description": (
                "Endpoint: `GET /api/v1/companies`\n\n"
                "Access: Paid tiers only.\n\n"
                "Returns the public company index with queryable company domains, "
                "display names, parent mappings, installs, and the latest trend "
                "snapshot fields for market share, market-share change, total "
                "apps, apps added, and apps lost."
            ),
        }
    },
    "/api/v1/companies/{company_domain}/sdks": {
        "get": {
            "summary": "[Paid] /companies/{company_domain}/sdks",
            "description": (
                "Endpoint: `GET /api/v1/companies/{company_domain}/sdks`\n\n"
                "Access: Paid tiers only.\n\n"
                "Returns mapped SDK slugs, names, and basic app counts for a company domain."
            ),
        }
    },
    "/api/v1/sdks/{sdk_slug}": {
        "get": {
            "summary": "[Paid] /sdks/{sdk_slug}",
            "description": (
                "Endpoint: `GET /api/v1/sdks/{sdk_slug}`\n\n"
                "Access: Paid tiers only.\n\n"
                "Returns the SDK slug, its related company domain and name, and "
                "the public company overview. Private SDK and company database IDs "
                "and company logos are omitted."
            ),
        }
    },
    "/api/v1/companies/{company_domain}": {
        "get": {
            "summary": "[Paid] /companies/{company_domain}",
            "description": (
                "Endpoint: `GET /api/v1/companies/{company_domain}`\n\n"
                "Access: Paid tiers only.\n\n"
                "Returns the public company overview for a single domain, including "
                "mapping status, company types, key metrics, a latest-trends summary, "
                "and dataset availability."
            ),
        }
    },
    "/api/v1/companies/{company_domain}/app-changes": {
        "get": {
            "summary": "[Paid] /companies/{company_domain}/app-changes",
            "description": (
                "Endpoint: `GET /api/v1/companies/{company_domain}/app-changes`\n\n"
                "Access: Paid tiers only.\n\n"
                "Returns ordered Android and iOS app store IDs for a known company's "
                "quarterly churn and adoption slice. Use `status=lost` to review apps "
                "that removed the company in that year/quarter window, or `status=added` "
                "to review apps that newly added it, filtered by a single tag source. "
                "This is useful for prospecting, competitor monitoring, and compliance "
                "review when you already know the company domain you want to inspect. "
                "The response is scoped to one company's quarterly delta and does not "
                "directly correlate that company's removal with another company's "
                "addition in the same payload."
            ),
        }
    },
    "/api/v1/apps/{store_id}": {
        "get": {
            "summary": "/apps/{store_id}",
            "description": (
                "Endpoint: `GET /api/v1/apps/{store_id}`\n\n"
                "Returns stable public app metadata plus MAU, recent install, and "
                "estimated revenue signals for a single app."
            ),
        }
    },
    "/api/v1/apps/{store_id}/ranks": {
        "get": {
            "summary": "/apps/{store_id}/ranks",
            "description": (
                "Endpoint: `GET /api/v1/apps/{store_id}/ranks`\n\n"
                "Returns flat best-rank records by country, collection, and category "
                "for the last 90 days."
            ),
        }
    },
    "/api/v1/apps/{store_id}/mapped-sdks": {
        "get": {
            "summary": "[Paid] /apps/{store_id}/mapped-sdks",
            "description": (
                "Endpoint: `GET /api/v1/apps/{store_id}/mapped-sdks`\n\n"
                "Access: B2B SDK and B2B Premium tiers only.\n\n"
                "Returns mapped SDK slugs grouped by company domain for a single app."
            ),
        }
    },
    "/api/v1/apps/{store_id}/sdks": {
        "get": {
            "summary": "/apps/{store_id}/sdks",
            "description": (
                "Endpoint: `GET /api/v1/apps/{store_id}/sdks`\n\n"
                "Returns public SDK findings, permissions, package queries, SKAdNetwork "
                "entries, and unmapped evidence for a single app."
            ),
        }
    },
    "/api/v1/apps/{store_id}/versions": {
        "get": {
            "summary": "[Paid] /apps/{store_id}/versions",
            "description": (
                "Endpoint: `GET /api/v1/apps/{store_id}/versions`\n\n"
                "Access: B2B SDK and B2B Premium tiers only.\n\n"
                "Returns the crawled version timeline for an app, including the "
                "version code, download timestamp, SDK scan result, and latest "
                "SDK scan timestamp."
            ),
        }
    },
    "/api/v1/apps/{store_id}/sdks/history": {
        "get": {
            "summary": "[Paid] /apps/{store_id}/sdks/history",
            "description": (
                "Endpoint: `GET /api/v1/apps/{store_id}/sdks/history`\n\n"
                "Access: B2B SDK and B2B Premium tiers only.\n\n"
                "Returns SDK additions and removals across app versions, along "
                "with scan-status rows when a version had no detected SDK change. "
                "Change rows include SDK and company metadata when available."
            ),
        }
    },
    "/api/v1/rankings/ctv/{store}": {
        "get": {
            "summary": "/rankings/ctv/{store}",
            "description": (
                "Endpoint: `GET /api/v1/rankings/ctv/{store}`\n\n"
                "Returns the top 50 connected-TV (CTV) supported apps for a store, "
                "ranked by estimated monthly installs. Use `store=1` for Google Play "
                "or `store=2` for the Apple App Store. Rows include the app's rank, "
                "category, developer, rating, total installs, monthly installs, "
                "estimated monthly revenue, and 14-day installs growth score."
            ),
        }
    },
    "/api/v1/keywords/{keyword}": {
        "get": {
            "summary": "/keywords/{keyword}",
            "description": (
                "Endpoint: `GET /api/v1/keywords/{keyword}`\n\n"
                "Returns per-platform keyword difficulty, competition, and "
                "opportunity metrics for an exact keyword lookup in the US storefront dataset."
            ),
        }
    },
    "/api/v1/keywords/{keyword}/ranks": {
        "get": {
            "summary": "/keywords/{keyword}/ranks",
            "description": (
                "Endpoint: `GET /api/v1/keywords/{keyword}/ranks`\n\n"
                "Returns grouped latest top-ranked Android and iOS apps for an exact "
                "keyword lookup in the US storefront dataset."
            ),
        }
    },
    "/api/v1/advertisers/{host_domain}/creatives": {
        "get": {
            "summary": "[Paid] /advertisers/{host_domain}/creatives",
            "description": (
                "Endpoint: `GET /api/v1/advertisers/{host_domain}/creatives`\n\n"
                "Access: Paid tiers only.\n\n"
                "Returns advertiser creatives recorded for a host domain, including "
                "the creative's MD5 hash, file extension, ad domain, hosting company "
                "name, advertiser store ID, publisher store ID and name, vhash, MMP "
                "domain, capture timestamp, and a direct media URL for the raw "
                "creative asset."
            ),
        }
    },
}

SCALAR_OPTIONS = {
    "theme": "purple",
    "expandAllResponses": True,
    "hideClientButton": True,
    "hideModels": True,
    "hideSearch": True,
    "hideTestRequestButton": True,
    "showSidebar": True,
    "showDeveloperTools": "never",
    "showToolbar": "localhost",
    "operationTitleSource": "summary",
    "persistAuth": False,
    "telemetry": True,
    "externalUrls": {
        "dashboardUrl": "https://dashboard.scalar.com",
        "registryUrl": "https://registry.scalar.com",
        "proxyUrl": "https://proxy.scalar.com",
        "apiBaseUrl": "https://api.scalar.com",
    },
    "layout": "modern",
    "isEditable": False,
    "isLoading": False,
    "documentDownloadType": "both",
    "showOperationId": False,
    "hideDarkModeToggle": False,
    "withDefaultFonts": True,
    "defaultOpenFirstTag": True,
    "defaultOpenAllTags": False,
    "expandAllModelSections": False,
    "orderSchemaPropertiesBy": "alpha",
    "orderRequiredPropertiesFirst": True,
    "_integration": "html",
    "default": False,
    "slug": "api-1",
    "title": "API #1",
    "agent": {"disabled": True},
}


class V1ScalarRenderPlugin(ScalarRenderPlugin):
    """Render Scalar against the dedicated v1 schema endpoint."""

    @staticmethod
    def get_openapi_json_route(request: Request) -> str:
        return V1_OPENAPI_JSON_PATH


_SCALAR_PLUGIN = V1ScalarRenderPlugin(
    path="/",
    options=SCALAR_OPTIONS,
    css_url=SCALAR_CSS_URL,
)


def _set_companies_index_example(schema: dict[str, Any]) -> None:
    """Attach a concrete example to the public companies index endpoint."""
    path_item = schema.get("paths", {}).get("/api/v1/companies")
    if not isinstance(path_item, dict):
        return

    get_operation = path_item.get("get")
    if not isinstance(get_operation, dict):
        return

    responses = get_operation.get("responses", {})
    response_200 = responses.get("200")
    if not isinstance(response_200, dict):
        return

    content = response_200.get("content", {})
    json_content = content.get("application/json")
    if not isinstance(json_content, dict):
        return

    json_content["examples"] = {
        "companies_index": {
            "summary": "Companies index with latest trend snapshot fields",
            "value": COMPANIES_INDEX_EXAMPLE_RESPONSE,
        }
    }


def _set_app_basics_example(schema: dict[str, Any]) -> None:
    """Attach a concrete example to the public app basics endpoint."""
    path_item = schema.get("paths", {}).get("/api/v1/apps/{store_id}")
    if not isinstance(path_item, dict):
        return

    get_operation = path_item.get("get")
    if not isinstance(get_operation, dict):
        return

    for parameter in get_operation.get("parameters", []):
        if parameter.get("name") == "store_id":
            parameter["example"] = APP_BASICS_EXAMPLE_STORE_ID

    responses = get_operation.get("responses", {})
    response_200 = responses.get("200")
    if not isinstance(response_200, dict):
        return

    content = response_200.get("content", {})
    json_content = content.get("application/json")
    if not isinstance(json_content, dict):
        return

    json_content["examples"] = {
        "appgoblin_android_app": {
            "summary": "App basics for the AppGoblin Android app",
            "value": APP_BASICS_EXAMPLE_RESPONSE,
        }
    }


def _set_app_sdk_history_examples(schema: dict[str, Any]) -> None:
    """Attach examples to the B2B SDK timeline and history endpoints."""
    timeline_path = schema.get("paths", {}).get("/api/v1/apps/{store_id}/versions")
    history_path = schema.get("paths", {}).get("/api/v1/apps/{store_id}/sdks/history")

    if isinstance(timeline_path, dict):
        operation = timeline_path.get("get")
        if isinstance(operation, dict):
            for parameter in operation.get("parameters", []):
                if parameter.get("name") == "store_id":
                    parameter["example"] = APP_VERSION_TIMELINE_EXAMPLE_STORE_ID
            content = (
                operation.get("responses", {})
                .get("200", {})
                .get("content", {})
                .get("application/json")
            )
            if isinstance(content, dict):
                content["examples"] = {
                    "app_version_timeline": {
                        "summary": "Crawled versions and SDK scan status",
                        "value": APP_VERSION_TIMELINE_EXAMPLE_RESPONSE,
                    }
                }

    if isinstance(history_path, dict):
        operation = history_path.get("get")
        if isinstance(operation, dict):
            for parameter in operation.get("parameters", []):
                if parameter.get("name") == "store_id":
                    parameter["example"] = APP_VERSION_TIMELINE_EXAMPLE_STORE_ID
            content = (
                operation.get("responses", {})
                .get("200", {})
                .get("content", {})
                .get("application/json")
            )
            if isinstance(content, dict):
                content["examples"] = {
                    "app_sdk_history": {
                        "summary": "SDK additions, removals, and scan-status rows",
                        "value": APP_SDK_HISTORY_EXAMPLE_RESPONSE,
                    }
                }


def _set_company_overview_example(schema: dict[str, Any]) -> None:
    """Attach a concrete example to the public company detail endpoint."""
    path_item = schema.get("paths", {}).get("/api/v1/companies/{company_domain}")
    if not isinstance(path_item, dict):
        return

    get_operation = path_item.get("get")
    if not isinstance(get_operation, dict):
        return

    for parameter in get_operation.get("parameters", []):
        if parameter.get("name") == "company_domain":
            parameter["example"] = COMPANY_OVERVIEW_EXAMPLE_DOMAIN

    responses = get_operation.get("responses", {})
    response_200 = responses.get("200")
    if not isinstance(response_200, dict):
        return

    content = response_200.get("content", {})
    json_content = content.get("application/json")
    if not isinstance(json_content, dict):
        return

    json_content["examples"] = {
        "unity_company_overview": {
            "summary": "Company detail overview for Unity",
            "value": COMPANY_OVERVIEW_EXAMPLE_RESPONSE,
        }
    }


def _set_company_app_changes_examples(schema: dict[str, Any]) -> None:
    """Attach examples and parameter examples for public company app-change endpoints."""
    path_item = schema.get("paths", {}).get(
        "/api/v1/companies/{company_domain}/app-changes"
    )
    if not isinstance(path_item, dict):
        return

    get_operation = path_item.get("get")
    if not isinstance(get_operation, dict):
        return

    for parameter in get_operation.get("parameters", []):
        if parameter.get("name") == "company_domain":
            parameter["example"] = "unity.com"
        elif parameter.get("name") == "status":
            parameter["example"] = "added"
        elif parameter.get("name") == "tag_source":
            parameter["example"] = "sdk"
        elif parameter.get("name") == "year":
            parameter["example"] = 2026
        elif parameter.get("name") == "quarter":
            parameter["example"] = 1

    responses = get_operation.get("responses", {})
    response_200 = responses.get("200")
    if not isinstance(response_200, dict):
        return

    content = response_200.get("content", {})
    json_content = content.get("application/json")
    if not isinstance(json_content, dict):
        return

    json_content["examples"] = {
        "unity_company_app_changes_added": {
            "summary": "Store IDs for Unity apps added in 2026 Q1",
            "value": {
                **COMPANY_APPS_ADDED_EXAMPLE_RESPONSE,
                "status": "added",
            },
        },
        "unity_company_app_changes_lost": {
            "summary": "Store IDs for Unity apps lost in 2026 Q1",
            "value": {
                **COMPANY_APPS_ADDED_EXAMPLE_RESPONSE,
                "status": "removed",
            },
        },
    }


def _set_keyword_metrics_example(schema: dict[str, Any]) -> None:
    """Attach a concrete example to the public keyword metrics endpoint."""
    path_item = schema.get("paths", {}).get("/api/v1/keywords/{keyword}")
    if not isinstance(path_item, dict):
        return

    get_operation = path_item.get("get")
    if not isinstance(get_operation, dict):
        return

    for parameter in get_operation.get("parameters", []):
        if parameter.get("name") == "keyword":
            parameter["example"] = KEYWORD_OVERVIEW_EXAMPLE_KEYWORD

    responses = get_operation.get("responses", {})
    response_200 = responses.get("200")
    if not isinstance(response_200, dict):
        return

    content = response_200.get("content", {})
    json_content = content.get("application/json")
    if not isinstance(json_content, dict):
        return

    json_content["examples"] = {
        "keyword_metrics": {
            "summary": "Keyword metrics for a tracked ASO keyword",
            "value": KEYWORD_METRICS_EXAMPLE_RESPONSE,
        }
    }


def _set_keyword_ranks_example(schema: dict[str, Any]) -> None:
    """Attach a concrete example to the public keyword ranks endpoint."""
    path_item = schema.get("paths", {}).get("/api/v1/keywords/{keyword}/ranks")
    if not isinstance(path_item, dict):
        return

    get_operation = path_item.get("get")
    if not isinstance(get_operation, dict):
        return

    for parameter in get_operation.get("parameters", []):
        if parameter.get("name") == "keyword":
            parameter["example"] = KEYWORD_OVERVIEW_EXAMPLE_KEYWORD
        elif parameter.get("name") == "limit":
            parameter["example"] = 20

    responses = get_operation.get("responses", {})
    response_200 = responses.get("200")
    if not isinstance(response_200, dict):
        return

    content = response_200.get("content", {})
    json_content = content.get("application/json")
    if not isinstance(json_content, dict):
        return

    json_content["examples"] = {
        "keyword_ranks": {
            "summary": "Latest top-ranked apps for a tracked ASO keyword",
            "value": KEYWORD_RANKS_EXAMPLE_RESPONSE,
        }
    }


def _set_ctv_app_ranks_example(schema: dict[str, Any]) -> None:
    """Attach a concrete example to the public CTV app ranks endpoint."""
    path_item = schema.get("paths", {}).get("/api/v1/rankings/ctv/{store}")
    if not isinstance(path_item, dict):
        return

    get_operation = path_item.get("get")
    if not isinstance(get_operation, dict):
        return

    for parameter in get_operation.get("parameters", []):
        if parameter.get("name") == "store":
            parameter["example"] = 1

    responses = get_operation.get("responses", {})
    response_200 = responses.get("200")
    if not isinstance(response_200, dict):
        return

    content = response_200.get("content", {})
    json_content = content.get("application/json")
    if not isinstance(json_content, dict):
        return

    json_content["examples"] = {
        "ctv_app_ranks": {
            "summary": "Top CTV-supported Google Play apps by monthly installs",
            "value": CTV_APP_RANKS_EXAMPLE_RESPONSE,
        }
    }


def _set_advertiser_creatives_example(schema: dict[str, Any]) -> None:
    """Attach a concrete example to the public advertiser creatives endpoint."""
    path_item = schema.get("paths", {}).get(
        "/api/v1/advertisers/{host_domain}/creatives"
    )
    if not isinstance(path_item, dict):
        return

    get_operation = path_item.get("get")
    if not isinstance(get_operation, dict):
        return

    for parameter in get_operation.get("parameters", []):
        if parameter.get("name") == "host_domain":
            parameter["example"] = ADVERTISER_CREATIVES_EXAMPLE_HOST_DOMAIN

    responses = get_operation.get("responses", {})
    response_200 = responses.get("200")
    if not isinstance(response_200, dict):
        return

    content = response_200.get("content", {})
    json_content = content.get("application/json")
    if not isinstance(json_content, dict):
        return

    json_content["examples"] = {
        "advertiser_creatives": {
            "summary": "Advertiser creatives recorded for the AppLovin host domain",
            "value": ADVERTISER_CREATIVES_EXAMPLE_RESPONSE,
        }
    }


def _set_operation_docs(schema: dict[str, Any]) -> None:
    """Set stable Scalar-friendly summaries and descriptions for public v1 routes."""
    paths = schema.get("paths", {})
    if not isinstance(paths, dict):
        return

    for path, methods in V1_OPERATION_DOCS.items():
        path_item = paths.get(path)
        if not isinstance(path_item, dict):
            continue

        for method, metadata in methods.items():
            operation = path_item.get(method)
            if not isinstance(operation, dict):
                continue

            operation["summary"] = metadata["summary"]
            operation["description"] = metadata["description"]


def build_v1_openapi_schema(request: Request) -> dict[str, Any]:
    """Return a filtered OpenAPI schema containing only public v1 endpoints."""
    schema = deepcopy(request.app.openapi_schema.to_schema())
    schema["paths"] = {
        path: value
        for path, value in schema.get("paths", {}).items()
        if path.startswith(V1_PATH_PREFIX) and not path.startswith(V1_DOCS_PATH_PREFIX)
    }
    schema["info"] = {
        **schema.get("info", {}),
        "title": "AppGoblin Public API v1",
        "version": "0.1.0",
        "description": (
            "Interactive reference for AppGoblin public v1 endpoints.\n\n"
            "## Authentication\n"
            "Create or manage your API Token from the AppGoblin account dashboard, "
            "then send it as the `Authorization: Bearer <token>` header on each request. "
            "The legacy `X-API-Key` header is also accepted.\n\n"
            f"- Get a token: {PUBLIC_API_SERVER_URL}/account/api-keys\n"
            "\n"
            "## Plans & Access\n"
            f"> **Need higher tiers or access to all endpoints?** See [Pricing]({PUBLIC_PRICING_URL}).\n\n"
            "## Rate Limits\n"
            "Rate limits are shared by all API keys and members of an organization "
            "across REST and MCP, and vary by subscription tier. Users without an "
            "organization have a separate free-tier allowance. Daily quotas reset "
            "at UTC midnight. Requests rejected by the per-minute limit still count "
            "toward the daily quota.\n\n"
            "- Free and paid tiers have different per-minute and daily quotas\n"
            "- Responses include `X-RateLimit-Limit`, `X-RateLimit-Remaining`, "
            "`X-RateLimit-Policy`, and `X-RateLimit-Quota-Remaining` headers\n"
            "- Requests that exceed a limit return `429 Too Many Requests`; "
            "minute-limit responses may also include `Retry-After`\n"
            "\n"
            "## AI & Raw Spec\n"
            "Scalar does not expose a built-in copy-all-docs button in this setup. "
            f"For AI tools or bulk export, use the raw OpenAPI JSON at [{V1_OPENAPI_JSON_PATH}]({PUBLIC_OPENAPI_JSON_URL}) or the download button in the docs UI.\n"
            "\n"
            "- App basics include stable store metadata plus MAU, recent install, and "
            "estimated revenue metrics\n"
            "- Public app payloads intentionally omit internal IDs, app icon URLs, and "
            "creative inventory counters\n"
            "- App endpoints accept valid public API tokens\n"
            "- Company endpoints require a paid subscription tier"
        ),
    }
    components = schema.setdefault("components", {})
    security_schemes = components.setdefault("securitySchemes", {})
    security_schemes["BearerAuth"] = {
        "type": "http",
        "scheme": "bearer",
        "description": (
            "Generate an API Token from the AppGoblin dashboard and send it as the "
            "`Authorization: Bearer <token>` header. The legacy `X-API-Key` header "
            "is also accepted."
        ),
    }
    schema["security"] = [{"BearerAuth": []}]
    schema["servers"] = [{"url": PUBLIC_API_SERVER_URL}]
    _set_operation_docs(schema)
    _set_companies_index_example(schema)
    _set_app_basics_example(schema)
    _set_app_sdk_history_examples(schema)
    _set_company_overview_example(schema)
    _set_company_app_changes_examples(schema)
    _set_keyword_metrics_example(schema)
    _set_keyword_ranks_example(schema)
    _set_ctv_app_ranks_example(schema)
    _set_advertiser_creatives_example(schema)
    return schema


class V1DocsController(Controller):
    """Generated documentation views for the public v1 API."""

    path = "/api/v1/docs"
    include_in_schema = False

    @get(
        path="/openapi.json",
        media_type=OpenAPIMediaType.OPENAPI_JSON,
    )
    async def openapi_json(self: Self, request: Request) -> dict[str, Any]:
        """Return the public v1 OpenAPI schema."""
        return build_v1_openapi_schema(request)

    @get(path="/openapi", media_type=MediaType.HTML)
    async def openapi(self: Self, request: Request) -> bytes:
        """Render Scalar for the public v1 OpenAPI schema."""
        return _SCALAR_PLUGIN.render(request, build_v1_openapi_schema(request))
