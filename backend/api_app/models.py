"""Data models for APIs."""

from dataclasses import dataclass, field


@dataclass
class AppDetail:
    """All app details, mostly from store_app table.

    NOTE: not all details are listed in the class.
    """

    store_id: str
    name: str
    store_url: str


@dataclass
class AppHistory:
    """All app history details.

    NOTE: not all details are listed in the class.
    """

    plot_data: dict


@dataclass
class AdsTxtEntries:
    """App ads txt entries."""

    direct_entries: dict
    reseller_entries: dict


@dataclass
class AppSDKsOverview:
    """Lists of Package permissions, trackers etc from Manifest."""

    company_categories: dict


@dataclass
class DeveloperSDKsOverview:
    """Lists of Package permissions, trackers etc from Manifest."""

    sdks: dict
    failed_store_ids: list[str]
    success_store_ids: list[str]


@dataclass
class SDKsDetails:
    """Lists of Package permissions, trackers etc from Manifest."""

    permissions: list[str]
    company_categories: dict
    leftovers: dict[str, list[str]]
    app_queries: list[str]
    skadnetwork: list[str]


@dataclass
class AppGroup:
    """A Group of Apps by Platform."""

    title: str
    apps: list[AppDetail]


@dataclass
class AppGroupByStore:
    """A Group of Apps by Store."""

    key: str
    apple: AppGroup
    google: AppGroup


@dataclass
class PlatformDeveloper:
    """Developer details for a specific platform."""

    developer_id: str
    developer_name: str
    developer_url: str
    pub_domain_url: str | None
    apps: AppGroup
    apps_by_url: AppGroup


@dataclass
class DeveloperApps:
    """A developer's list of apps.

    Note: This is platform specific.
    """

    google: PlatformDeveloper
    apple: PlatformDeveloper
    title: str


@dataclass
class DeveloperSDKs:
    """A developer's list of sdks."""

    sdks: dict


@dataclass
class CategoryDetail:
    """Represents detailed information about a category.

    Includes its identifier, name, and app counts for
    both Android and iOS platforms, along with its type.
    """

    id: str
    name: str
    android: int
    ios: int
    type: str


@dataclass
class CategoriesOverview:
    """Holds a list of CategoryDetail objects.

    Providing an overview of all categories.
    """

    categories: list[CategoryDetail]


@dataclass
class CompanyTypes:
    """Holds a list of CategoryDetail objects.

    Providing an overview of all categories.
    """

    types: list[dict]


@dataclass
class SDKPatterns:
    """Holds a list of package patterns and paths for a company."""

    sdk_name: str
    package_patterns: list[str]
    paths: list[str]


@dataclass
class CompanySDKs:
    """Holds a list of package patterns and paths for a company."""

    company_name: str
    sdks: list[SDKPatterns]


@dataclass
class CompanyPatterns:
    """Holds a list of package patterns and paths for a company."""

    company_name: str
    sdks: list[CompanySDKs]


@dataclass
class CompanyPatternsDict:
    """Holds a list of package patterns and paths for a company."""

    companies: dict[str, CompanyPatterns]


@dataclass
class ChildrenCompanyTree:
    """A company tree with parent companies and domains."""

    company_name: str
    domains: list[str]


@dataclass
class ParentCompanyTree:
    """A company tree with parent companies and domains."""

    is_secondary_domain: bool
    is_parent_company: bool
    parent_company_name: str | None
    parent_company_domain: str | None
    queried_company_domain: str
    queried_company_name: str
    domains: list[str]
    children_companies: list[ChildrenCompanyTree]
    queried_company_logo_url: str | None = None
    parent_company_logo_url: str | None = None


@dataclass
class CompanyDetail:
    """Describes details of a tracker.

    Includes its db identifier, name, and the count of its occurrences.
    """

    company_id: int
    name: str
    count: int


@dataclass
class CompanyPubIDTotals:
    """Totals for a publisher ID."""

    direct_google_devs: int
    direct_apple_devs: int
    direct_google_apps: int
    direct_apple_apps: int

    reseller_google_devs: int
    reseller_apple_devs: int
    reseller_google_apps: int
    reseller_apple_apps: int


@dataclass
class CompanyPubIDAppsRelationship:
    """Apps for a publisher ID."""

    direct: list[dict]
    reseller: list[dict]


@dataclass
class CompanyPubIDApps:
    """Apps for a publisher ID."""

    google: CompanyPubIDAppsRelationship
    apple: CompanyPubIDAppsRelationship


@dataclass
class CompanyPubIDOverview:
    """Companies data for a specific platform (iOS/Android)."""

    totals: CompanyPubIDTotals
    apps: CompanyPubIDApps


@dataclass
class PlatformCompanies:
    """Companies data for a specific platform (iOS/Android)."""

    ios: list[dict]
    android: list[dict]


@dataclass
class TopCompaniesShort:
    """Represents top companies across different categories."""

    sdk_ios: PlatformCompanies
    sdk_android: PlatformCompanies
    adstxt_direct_ios: PlatformCompanies
    adstxt_direct_android: PlatformCompanies


@dataclass
class TopCompaniesOverviewShort:
    """Represents top companies across different categories."""

    adnetworks: TopCompaniesShort
    attribution: TopCompaniesShort
    analytics: TopCompaniesShort


@dataclass
class CategoryCompaniesStats:
    """Contains a list of total count objects.

    Representing various total counts.
    """

    total_companies: int = 0
    adstxt_direct_ios_total_companies: int = 0
    adstxt_direct_android_total_companies: int = 0
    adstxt_reseller_ios_total_companies: int = 0
    adstxt_reseller_android_total_companies: int = 0
    sdk_ios_total_companies: int = 0
    sdk_android_total_companies: int = 0
    sdk_total_apps: int = 0
    sdk_ios_total_apps: int = 0
    sdk_android_total_apps: int = 0
    sdk_android_installs_d30: int = 0
    sdk_ios_installs_d30: int = 0


@dataclass
class CategoryCompanyStats:
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
    sdk_android_installs_d30: int = 0
    adstxt_direct_android_installs_d30: int = 0
    adstxt_reseller_android_installs_d30: int = 0


@dataclass
class CompaniesCategoryOverview:
    """Contains a dictionary of categories, each with their associated statistics."""

    categories: dict[str, CategoryCompaniesStats] = field(default_factory=dict)

    def add_category(self, category: str) -> None:
        """Add a category to the overview."""
        if category not in self.categories:
            self.categories[category] = CategoryCompaniesStats()

    def update_stats(self, category: str, **kwargs: int) -> None:
        """Update the stats for a category."""
        if category not in self.categories:
            self.add_category(category)
        for key, value in kwargs.items():
            if hasattr(self.categories[category], key):
                setattr(self.categories[category], key, value)


@dataclass
class CompanyCategoryOverview:
    """Contains a dictionary of categories, each with their associated statistics."""

    categories: dict[str, CategoryCompanyStats] = field(default_factory=dict)
    adstxt_ad_domain_overview: dict | None = None
    adstxt_publishers_overview: dict | None = None
    mediation_adapters: dict | None = None

    def add_category(self, category: str) -> None:
        """Add a category to the overview."""
        if category not in self.categories:
            self.categories[category] = CategoryCompanyStats()

    def update_stats(self, category: str, **kwargs: int) -> None:
        """Update the stats for a category."""
        if category not in self.categories:
            self.add_category(category)
        for key, value in kwargs.items():
            if hasattr(self.categories[category], key):
                setattr(self.categories[category], key, value)


@dataclass
class CompaniesOverview:
    """Contains a list of CompanyDetail objects.

    Representing the top networks identified.
    """

    companies_overview: list[CompanyDetail]
    top: TopCompaniesShort
    categories: CompaniesCategoryOverview


@dataclass
class CompanyPlatformOverview:
    """Represents companies for a specific platform."""

    ios: AppGroup
    android: AppGroup


@dataclass
class CompanyAppsOverview:
    """Overview of a company's apps on different platforms."""

    sdk: CompanyPlatformOverview
    adstxt_direct: CompanyPlatformOverview
    adstxt_reseller: CompanyPlatformOverview


@dataclass
class StoreCategoryDetail:
    """Describes details of a store category, including its identifier and name."""

    category_id: int
    category_name: str


@dataclass
class StoreCollections:
    """Represents a collection within a store.

    Including its identifier, name, and the categories it contains.
    Categories are optional and can be added as a list.
    """

    collection_id: int
    collection_name: str
    categories: list[StoreCategoryDetail] = field(default_factory=list)


@dataclass
class StoreRankings:
    """Holds information about a store's rankings.

    Including its identifier, name, and the collections it contains.
    Collections are optional and can be added as a list.
    """

    store_id: int
    store_name: str
    collections: list[StoreCollections] = field(default_factory=list)


@dataclass
class RankingOverview:
    """Provides an overview of rankings across different stores.

    Containing a list of StoreRankings objects.
    """

    stores_rankings: list[StoreRankings] = field(default_factory=list)


@dataclass
class AppRankOverview:
    """Represents the ranking details of an app.

    Including its latest rankings and historical rankings data as dictionaries.
    """

    countries: list[str]
    best_ranks: dict


@dataclass
class AppRank:
    """Represents the ranking details of an app.

    Including its latest rankings and historical rankings data as dictionaries.
    """

    history: dict


@dataclass
class SdksLatestResults:
    """Contains a list of SDK objects.

    Representing the top sdks identified.
    """

    ios_success_latest_apps: list[dict]
    android_success_latest_apps: list[dict]
    ios_failed_latest_apps: list[dict]
    android_failed_latest_apps: list[dict]


@dataclass
class SdksUserRequested:
    """Contains a list of SDK objects.

    Representing the top sdks identified.
    """

    user_requested_latest_apps: list[dict]


@dataclass
class SdkOverview:
    """Contains a list of sdk overview objects."""

    ios_overview: list[dict]
    android_overview: list[dict]


@dataclass
class SdkCompanies:
    """Contains a list of sdk companies objects."""

    companies: list[dict]
