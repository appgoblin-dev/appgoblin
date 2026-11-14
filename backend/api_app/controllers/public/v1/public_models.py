"""Data models for public user-facing API contracts."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TypeAlias

AppSdkEvidenceByPath: TypeAlias = dict[str, list[str]]
AppSdkEvidenceByPackage: TypeAlias = dict[str, AppSdkEvidenceByPath]
AppSdkEvidenceByCompany: TypeAlias = dict[str, AppSdkEvidenceByPackage]
AppSdkEvidenceByCategory: TypeAlias = dict[str, AppSdkEvidenceByCompany]
AppSdkUnmappedEvidence: TypeAlias = dict[str, AppSdkEvidenceByPath]


@dataclass
class PublicAppSearchResult:
    """An app matching a public app or developer search."""

    store: str
    store_id: str
    name: str | None = None
    developer_name: str | None = None
    featured_image_url: str | None = None
    installs: int | None = None
    rating: float | None = None
    rating_count: int | None = None
    store_link: str | None = None


@dataclass
class PublicCompanySearchResult:
    """A company matching a public company search."""

    company_domain: str
    company_name: str | None = None
    has_api_signal: bool | None = None
    has_sdk_signal: bool | None = None
    has_publisher_signal: bool | None = None
    has_app_ads_direct: bool | None = None
    has_app_ads_reseller: bool | None = None


@dataclass
class PublicCompanyListItem:
    """Minimal company entry returned by the public companies index."""

    name: str | None = None
    company_domain: str | None = None
    parent_company_domain: str | None = None
    parent_company_name: str | None = None
    api_ip_resolved_country: str | None = None
    total_app_count: int | None = None
    installs_d30: int | None = None
    google_sdk_app_count: int | None = None
    apple_sdk_app_count: int | None = None
    google_api_call_app_count: int | None = None
    apple_api_call_app_count: int | None = None
    google_app_ads_direct_app_count: int | None = None
    apple_app_ads_direct_app_count: int | None = None
    google_app_ads_reseller_app_count: int | None = None
    apple_app_ads_reseller_app_count: int | None = None
    trends_latest_period: str | None = None
    google_sdk_latest_pct_market_share: float | None = None
    apple_sdk_latest_pct_market_share: float | None = None
    google_app_ads_direct_latest_pct_market_share: float | None = None
    apple_app_ads_direct_latest_pct_market_share: float | None = None
    google_sdk_latest_pct_market_share_change: float | None = None
    apple_sdk_latest_pct_market_share_change: float | None = None
    google_app_ads_direct_latest_pct_market_share_change: float | None = None
    apple_app_ads_direct_latest_pct_market_share_change: float | None = None
    google_sdk_latest_total_apps: int | None = None
    apple_sdk_latest_total_apps: int | None = None
    google_app_ads_direct_latest_total_apps: int | None = None
    apple_app_ads_direct_latest_total_apps: int | None = None
    google_sdk_latest_apps_added: int | None = None
    apple_sdk_latest_apps_added: int | None = None
    google_app_ads_direct_latest_apps_added: int | None = None
    apple_app_ads_direct_latest_apps_added: int | None = None
    google_sdk_latest_apps_lost: int | None = None
    apple_sdk_latest_apps_lost: int | None = None
    google_app_ads_direct_latest_apps_lost: int | None = None
    apple_app_ads_direct_latest_apps_lost: int | None = None


@dataclass
class PublicCategoryCompanyStats:
    """Public company metrics grouped by platform and signal source."""

    total_apps: int = 0
    adstxt_direct_android_total_apps: int = 0
    adstxt_direct_ios_total_apps: int = 0
    adstxt_reseller_android_total_apps: int = 0
    adstxt_reseller_ios_total_apps: int = 0
    sdk_android_total_apps: int = 0
    sdk_ios_total_apps: int = 0
    sdk_total_apps: int = 0
    api_android_total_apps: int = 0
    api_total_apps: int = 0
    sdk_android_installs_d30: int = 0
    sdk_ios_installs_d30: int = 0
    adstxt_direct_android_installs_d30: int = 0
    adstxt_reseller_android_installs_d30: int = 0


@dataclass
class PublicCompanyTrends:
    """Public quarterly trend summary flattened by platform and signal source."""

    latest_period: str | None = None
    android_app_ads_direct_market_share_change_pct: float | None = None
    android_app_ads_direct_apps_lost: int | None = None
    android_sdk_api_market_share_change_pct: float | None = None
    android_sdk_api_apps_lost: int | None = None
    ios_app_ads_direct_market_share_change_pct: float | None = None
    ios_app_ads_direct_apps_lost: int | None = None
    ios_sdk_api_market_share_change_pct: float | None = None
    ios_sdk_api_apps_lost: int | None = None


@dataclass
class CompanyDatasetTarget:
    """Download metadata for a single public company dataset."""

    available: bool
    estimated_rows: int
    url: str | None


@dataclass
class CompanyDatasets:
    """Public company dataset links grouped by platform."""

    sdk_api_android: CompanyDatasetTarget
    sdk_api_ios: CompanyDatasetTarget
    parent_company_android: CompanyDatasetTarget | None = None
    parent_company_ios: CompanyDatasetTarget | None = None


@dataclass
class PublicCompanyOverview:
    """Public company detail payload returned by the v1 API."""

    domain_is_mapped: bool = False
    company_types: list[str] = field(default_factory=list)
    metrics: PublicCategoryCompanyStats = field(
        default_factory=PublicCategoryCompanyStats
    )
    trends: PublicCompanyTrends | None = None
    mapping_notice: str | None = None
    datasets: CompanyDatasets | None = None


@dataclass
class PublicCompanySdk:
    """Basic public SDK mapping information for a company."""

    sdk_slug: str
    sdk_name: str | None = None
    app_count: int | None = None


@dataclass
class PublicCompanySdks:
    """Public SDK mappings for a company domain."""

    company_domain: str
    sdks: list[PublicCompanySdk] = field(default_factory=list)


@dataclass
class PublicSdkCompanyOverview:
    """Public SDK metadata and its related company overview."""

    sdk_slug: str
    company_domain: str | None = None
    company_name: str | None = None
    company: PublicCompanyOverview | None = None


@dataclass
class PublicCompanyAppChangeStoreIds:
    """Public paid response for a company app-change slice."""

    company_domain: str
    tag_source: str
    year: int
    quarter: int
    status: str
    android_apps: list[str] = field(default_factory=list)
    ios_apps: list[str] = field(default_factory=list)


@dataclass
class PublicAppBasics:
    """Stable public app metadata plus power-user adoption and revenue estimates."""

    name: str | None = None
    store_id: str | None = None
    store: str | None = None
    category: str | None = None
    rating: float | None = None
    rating_count: int | None = None
    installs: int | None = None
    weekly_active_users: int | None = None
    monthly_active_users: int | None = None
    monthly_ad_revenue: float | None = None
    monthly_iap_revenue: float | None = None
    installs_weekly: int | float | None = None
    installs_monthly: int | float | None = None
    rating_count_weekly: int | None = None
    store_last_updated: str | None = None
    developer_id: str | None = None
    developer_name: str | None = None
    developer_url: str | None = None
    release_date: str | None = None
    ad_supported: bool | None = None
    in_app_purchases: bool | None = None
    tv_supported: bool = False
    store_link: str | None = None


@dataclass
class PublicAppBestRank:
    """Best rank achieved for a country/collection/category tuple."""

    country: str
    collection: str
    category: str
    best_rank: int


@dataclass
class PublicAppMappedSdks:
    """Mapped SDK slugs grouped by their company domain."""

    store_id: str
    mapped_sdks: dict[str, list[str]] = field(default_factory=dict)


@dataclass
class PublicAppSdkDetails:
    """Detailed SDK and manifest findings for a single app.

    The nested keys below identifiers such as category slug, company domain, and
    SDK package prefix are dynamic. Evidence keys like ``smali`` or
    ``application/provider`` represent the file path or manifest/XML path where
    AppGoblin found the matched value, so they intentionally remain open-ended.
    """

    company_categories: AppSdkEvidenceByCategory = field(default_factory=dict)
    permissions: list[str] = field(default_factory=list)
    app_queries: list[str] = field(default_factory=list)
    skadnetwork: list[str] = field(default_factory=list)
    unmapped_sdks: AppSdkUnmappedEvidence = field(default_factory=dict)


@dataclass
class PublicAppSdkHistory:
    """SDK change-history rows returned for a B2B app."""

    history: list[dict] = field(default_factory=list)


@dataclass
class PublicKeywordPlatformMetrics:
    """Public keyword metrics for a single mobile platform."""

    app_count: int | None = None
    total_apps: int | None = None
    median_competitor_installs: int | None = None
    avg_competitor_rating: float | None = None
    major_competitors: int | None = None
    volume_competition_score: float | None = None
    keyword_difficulty: float | None = None
    opportunity_score: float | None = None
    competitiveness_score: float | None = None


@dataclass
class PublicKeywordRankedApp:
    """Public app row for a keyword rankings response."""

    name: str | None = None
    store_id: str | None = None
    category: str | None = None
    installs: int | None = None
    rating_count: int | None = None
    app_icon_url: str | None = None
    latest_rank: int | None = None
    best_rank_d30: int | None = None


@dataclass
class PublicKeywordMetrics:
    """Public keyword metrics payload returned by the v1 API."""

    keyword: str
    country: str
    android: PublicKeywordPlatformMetrics | None = None
    ios: PublicKeywordPlatformMetrics | None = None


@dataclass
class PublicKeywordRanks:
    """Public latest keyword ranks payload returned by the v1 API."""

    keyword: str
    country: str
    android: list[PublicKeywordRankedApp] = field(default_factory=list)
    ios: list[PublicKeywordRankedApp] = field(default_factory=list)


@dataclass
class PublicCtvAppRank:
    """Public CTV app rank row returned by the v1 API."""

    rank: int | None = None
    name: str | None = None
    store_id: str | None = None
    store: str | None = None
    category: str | None = None
    developer_name: str | None = None
    rating: float | None = None
    rating_count: int | None = None
    installs: int | None = None
    monthly_installs: float | None = None
    monthly_revenue: float | None = None
    installs_z_score_2w: float | None = None
    country: str | None = None
    app_icon_url: str | None = None


@dataclass
class PublicCtvAppRanks:
    """Public top CTV app ranks payload returned by the v1 API."""

    store: str
    country: str
    apps: list[PublicCtvAppRank] = field(default_factory=list)


@dataclass
class PublicAdvertiserCreative:
    """Public advertiser creative row surfaced by host-domain lookup."""

    created_at: str | None = None
    ad_domain: str | None = None
    host_domain_company_name: str | None = None
    pub_store_id: str | None = None
    pub_name: str | None = None
    vhash: str | None = None
    md5_hash: str | None = None
    file_extension: str | None = None
    adv_store_id: str | None = None
    mmp_domain: str | None = None
    creative_url: str | None = None


@dataclass
class PublicAdvertiserCreatives:
    """Public advertiser creatives payload returned by the v1 API."""

    host_domain: str
    creatives: list[PublicAdvertiserCreative] = field(default_factory=list)
