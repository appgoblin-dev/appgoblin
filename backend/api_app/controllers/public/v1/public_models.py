"""Data models for public user-facing API contracts."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class PublicCategoryCompanyStats:
    """Contains a list of CompanyDetail objects.

    Representing the top networks identified.
    """

    total_apps: int = 0
    adstxt_direct_ios_total_apps: int = 0
    adstxt_direct_android_total_apps: int = 0
    adstxt_reseller_ios_total_apps: int = 0
    adstxt_reseller_android_total_apps: int = 0
    sdk_ios_total_apps: int = 0
    sdk_android_total_apps: int = 0
    sdk_total_apps: int = 0
    api_ios_total_apps: int = 0
    api_android_total_apps: int = 0
    api_total_apps: int = 0
    sdk_android_installs_d30: int = 0
    adstxt_direct_android_installs_d30: int = 0
    adstxt_reseller_android_installs_d30: int = 0


@dataclass
class CompanyDatasets:
    """Public company dataset links grouped by platform."""

    sdk_api_android: CompanyDatasetTarget
    sdk_api_ios: CompanyDatasetTarget


@dataclass
class CompanyDatasetTarget:
    """Download metadata for a single public company dataset."""

    available: bool
    estimated_rows: int
    url: str | None


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
