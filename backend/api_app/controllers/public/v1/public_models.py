"""Data models for public user-facing API contracts."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TypeAlias

AppRankHistoryEntryValue: TypeAlias = str | int | None
AppRankHistoryEntry: TypeAlias = dict[str, AppRankHistoryEntryValue]
AppSdkEvidenceByPath: TypeAlias = dict[str, list[str]]
AppSdkEvidenceByPackage: TypeAlias = dict[str, AppSdkEvidenceByPath]
AppSdkEvidenceByCompany: TypeAlias = dict[str, AppSdkEvidenceByPackage]
AppSdkEvidenceByCategory: TypeAlias = dict[str, AppSdkEvidenceByCompany]
AppSdkUnmappedEvidence: TypeAlias = dict[str, AppSdkEvidenceByPath]


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
    api_ios_total_apps: int = 0
    api_total_apps: int = 0
    sdk_android_installs_d30: int = 0
    adstxt_direct_android_installs_d30: int = 0
    adstxt_reseller_android_installs_d30: int = 0


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


@dataclass
class PublicCompanyOverview:
    """Public company detail payload returned by the v1 API."""

    domain_is_mapped: bool = False
    company_types: list[str] = field(default_factory=list)
    metrics: PublicCategoryCompanyStats = field(
        default_factory=PublicCategoryCompanyStats
    )
    mapping_notice: str | None = None
    datasets: CompanyDatasets | None = None


@dataclass
class PublicAppBasics:
    """Stable public metadata returned for a single app."""

    id: int | None = None
    name: str | None = None
    store_id: str | None = None
    store: str | None = None
    category: str | None = None
    rating: float | None = None
    rating_count: int | None = None
    installs: int | None = None
    developer_id: str | None = None
    developer_name: str | None = None
    developer_url: str | None = None
    release_date: str | None = None
    ad_supported: bool | None = None
    in_app_purchases: bool | None = None
    app_icon_url: str | None = None
    store_link: str | None = None


@dataclass
class PublicAppBestRank:
    """Best rank achieved for a country/collection/category tuple."""

    country: str
    collection: str
    category: str
    best_rank: int


@dataclass
class PublicAppRanksOverview:
    """Country coverage and best-rank summary for an app."""

    countries: list[str] = field(default_factory=list)
    best_ranks: list[PublicAppBestRank] = field(default_factory=list)


@dataclass
class PublicAppRankHistory:
    """Rank history records keyed by derived rank-group names."""

    history: list[AppRankHistoryEntry] | dict[str, None] = field(default_factory=dict)


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
