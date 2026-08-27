type TabularData = Array<Record<string, any>>;

export type Crumb<M = any> = {
	title?: string;
	url?: string;
	metadata?: M;
};
export type ModuleData = {
	pageTitle?: string;
	getPageTitle?: (data: any) => string;
};

export type MyCrumbMetadata = {
	extraValue: string;
};

export interface AppGroup {
	apps: AppFullDetail[];
	title: string;
}

export interface Category {
	key: string;
	google: AppGroup;
	ios: AppGroup;
}

export interface CategoryResponse {
	results?: Category;
	status?: number;
	error?: string;
}

export interface PlatformDeveloper {
	title: string;
	developer_id: string;
	developer_name: string;
	developer_url: string;
	pub_domain_url: string | null;
	apps: AppGroup;
	apps_by_url: AppGroup;
}

export interface DeveloperResponse {
	devs: {
		title: string;
		google: PlatformDeveloper;
		apple: PlatformDeveloper;
	};
	status?: number;
	error?: string;
}

export interface DeveloperSDKResponse {
	devs: {
		title: string;
		google: PlatformDeveloper;
		apple: PlatformDeveloper;
	};
	companyTypes: CompanyTypes;
	devSDKs: {
		sdks: {
			[key: string]: {
				company_name: string;
				company_domain: string;
				count: number;
				apps: {
					store: string;
					store_id: string;
					app_name: string;
				}[];
			}[];
		};
		success_store_ids: string[];
		failed_store_ids: string[];
	};
	status?: number;
	error?: string;
}

export interface AppGroupByStore {
	key: string;
	apple: AppGroup;
	google: AppGroup;
}

export interface CompanyApps {
	results: AppGroup;
	status?: number;
	error?: string;
}

export interface SearchResponse {
	appGroupByStore: AppGroupByStore;
	companiesResults: CompaniesSearchEntries[];
	status?: number;
	error?: string;
}

export interface PlaystoreSearchResponse {
	results: AppGroup;
	status?: number;
	error?: string;
}
export interface AppleStoreSearchResponse {
	results: AppGroup;
	status?: number;
	error?: string;
}

export interface CategoryInfo {
	id: string;
	name: string;
	android: boolean;
	ios: boolean;
}

export interface CatData {
	categories: Array<{ id: string; name: string; android: boolean; ios: boolean }>;
}

export interface SideBarCategoryItem {
	id: string;
	name: string;
	android: boolean | number;
	ios: boolean | number;
}

export interface SideBarCategoryData {
	categories: SideBarCategoryItem[];
}

export interface CategoriesInfo {
	appCats: Promise<CatData>;
	status?: number;
	error?: string;
}
export interface AppRankResponse {
	myranks?: AppRankDetail;
	status?: number;
	error?: string;
}

export interface HomeData {
	androidAppRanks: Promise<{ ranks: RankedApps[] }>;
	iOSAppRanks: Promise<{ ranks: RankedApps[] }>;
	androidGameRanks: Promise<{ ranks: RankedApps[] }>;
	iOSGameRanks: Promise<{ ranks: RankedApps[] }>;
	topCompanies: TopCompaniesShort;
	status?: number;
	error?: string;
}

export interface RankedAppList {
	ranks: RankedApps[];
}

export interface Countries {
	[key: string]: { langen: string; app_ranks: boolean; app_details: boolean };
}

export interface StoreCategoryRanks {
	ranks: Promise<{ ranks: RankedApps[] }>;
	// countries: { [key: string]: string };
	countries: Countries;
	status?: number;
	error?: string;
	history: Promise<{ history: RankedApps[] }>;
	storeIDLookup: StoreIDLookup;
	collectionIDLookup: Record<number, Record<number, CollectionRanks>>;
	categoryIDLookup: Record<number, Record<number, CategoryRanks>>;
}

export interface RankedApps {
	rank: number;
	store_link: string;
	name: string;
	developer_name?: string;
	store_id: string;
	icon_64?: string;
	store: number;
	installs: number;
	rating_count: number;
	rating: number;
	installs_sum_1w: number;
	installs_sum_4w: number;
	app_icon_url: string;
	phone_image_url_1?: string;
	tablet_image_url_1?: string;
	featured_image_url?: string;
}
export interface AppRankDetail {
	crawled_date: string;
	current_rank: number;
	best_rank: number;
	store: number;
	collection: string;
	category: string;
	country: string;
}

export interface UnknownSDKs {
	[key: string]: { [key: string]: string[] };
}

export interface CompanySDKParts {
	[key: string]: { [key: string]: { [key: string]: string[] } };
}

export interface AppHistoryInfo {
	crawled_date: string;
	rating: number;
	installs: number;
	country: string;
	rating_count: number;
}
export interface AdsTxtEntries {
	app_count: number;
	company_name: string;
	ad_domain: number;
	ad_domain_url: string;
	publisher_id: string;
	relationship: string;
	crawl_result: string;
	developer_domain_crawled_at: number;
}

export interface AdsTxtEntriesResult {
	myAdsTxt: {
		direct_entries: AdsTxtEntries[];
		reseller_entries: AdsTxtEntries[];
	};
}

export interface CompaniesOverviewEntries {
	company_domain: string;
	company_name: string;
	company_category?: string | null;
	parent_company_domain?: string | null;
	parent_company_name?: string | null;
	company_logo_url?: string | null;
	parent_company_logo_url?: string | null;
	country?: string | null;
	total_app_count?: number | null;
	google_app_count?: number | null;
	apple_app_count?: number | null;
	installs_d30?: number | null;
	google_installs_d30?: number | null;
	apple_installs_d30?: number | null;
	google_sdk_app_count?: number | null;
	apple_sdk_app_count?: number | null;
	google_api_call_app_count?: number | null;
	apple_api_call_app_count?: number | null;
	google_app_ads_direct_app_count?: number | null;
	apple_app_ads_direct_app_count?: number | null;
	google_app_ads_reseller_app_count?: number | null;
	apple_app_ads_reseller_app_count?: number | null;
	tag_source: string;
	store: string;
	app_count: number;
	percentage: number;
	percent_open_source: number;
	apple_app_ads_direct_percentage?: number | null;
	apple_app_ads_reseller_percentage?: number | null;
	apple_sdk_percentage?: number | null;
	google_api_call_percentage?: number | null;
	google_app_ads_direct_percentage?: number | null;
	google_app_ads_reseller_percentage?: number | null;
	google_sdk_percentage?: number | null;
	apple_app_ads_direct_installs_d30?: number | null;
	apple_app_ads_reseller_installs_d30?: number | null;
	apple_sdk_installs_d30?: number | null;
	google_api_call_installs_d30?: number | null;
	google_app_ads_direct_installs_d30?: number | null;
	google_app_ads_reseller_installs_d30?: number | null;
	google_sdk_installs_d30?: number | null;
	trends_latest_period?: string | null;
	google_sdk_latest_pct_market_share_change?: number | null;
	apple_sdk_latest_pct_market_share_change?: number | null;
	google_app_ads_direct_latest_pct_market_share_change?: number | null;
	apple_app_ads_direct_latest_pct_market_share_change?: number | null;
	google_sdk_latest_total_apps_change_pct?: number | null;
	apple_sdk_latest_total_apps_change_pct?: number | null;
	google_app_ads_direct_latest_total_apps_change_pct?: number | null;
	apple_app_ads_direct_latest_total_apps_change_pct?: number | null;
	google_sdk_latest_apps_added?: number | null;
	apple_sdk_latest_apps_added?: number | null;
	google_app_ads_direct_latest_apps_added?: number | null;
	apple_app_ads_direct_latest_apps_added?: number | null;
	google_sdk_latest_apps_lost?: number | null;
	apple_sdk_latest_apps_lost?: number | null;
	google_app_ads_direct_latest_apps_lost?: number | null;
	apple_app_ads_direct_latest_apps_lost?: number | null;
}

export interface CompaniesSearchEntries {
	company_domain: string;
	company_name: string;
	logo_url: string | null;
	has_api_signal: boolean;
	has_sdk_signal: boolean;
	has_publisher_signal: boolean;
	has_app_ads_direct: boolean;
	has_app_ads_reseller: boolean;
}

export interface CompaniesOverviewPlatforms {
	top: {
		group: string;
		value: number;
		company_domain?: string | null;
		company_logo_url?: string | null;
	}[];
}

export interface TopCompaniesOverview {
	sdk_ios: CompaniesOverviewPlatforms[];
	sdk_android: CompaniesOverviewPlatforms[];
	pub_ios: CompaniesOverviewPlatforms[];
	pub_android: CompaniesOverviewPlatforms[];
	adstxt_direct_ios: CompaniesOverviewPlatforms[];
	adstxt_direct_android: CompaniesOverviewPlatforms[];
}

export interface TopCompaniesShort {
	adnetworks: TopCompaniesOverview;
	attribution: TopCompaniesOverview;
	analytics: TopCompaniesOverview;
}

export interface CompaniesOverviewSections {
	companies_overview: CompaniesOverviewEntries[];
	top: TopCompaniesOverview;
	categories: CompaniesCategoryOverview;
}

export interface CompaniesOverview {
	status?: number;
	error?: string;
	companiesOverview: CompaniesOverviewSections;
}

export interface OverviewAppList {
	apps: SDKAppsOverview[];
}

export interface CompanyOverviewAppList {
	apps: CompanyOverviewApps[];
}

export interface SDKAppsOverview {
	name: string;
	store_id: string;
	store: number;
	installs: number;
	rating_count: number;
	requested_at: string;
	app_scanned_at: string;
	crawl_result: number;
	version_code: string;
	sdk_crawled_at: string;
	app_name: string;
	app_icon_url: string;
	developer_domain_url: string;
	relationship: string;
	developer_domain_crawled_at: string;
}

export interface CompanyOverviewApps {
	name: string;
	store_id: string;
	store: string | number;
	rank?: number | null;
	developer_name: string;
	icon_64: string;
	installs_d30: number;
	status?: string;
	sdk: boolean;
	publisher: boolean;
	api_call: boolean;
	app_ads_direct: boolean;
	year?: number;
	quarter?: number;
	is_removed?: boolean | null;
	country?: string | null;
}

export interface CompanyAppChangesOverview {
	status: string;
	year: number;
	quarter: number;
	android: CompanyOverviewAppList;
	ios: CompanyOverviewAppList;
}

export interface SdksOverview {
	store: string;
	company_name: string;
	company_domain: string;
	xml_path: string;
	value_name: string;
	app_count: number;
}

export interface SdkOverview {
	xml_path: string;
	value_name: string;
	store: string;
	store_id: string;
	app_name: string;
	installs: number;
	rating_count: number;
}

export interface CompanyOverviewPlatforms {
	android: OverviewAppList;
	ios: OverviewAppList;
}

export interface CompanyOverviewSections {
	sdk: CompanyOverviewPlatforms;
	adstxt_direct: CompanyOverviewPlatforms;
	adstxt_reseller: CompanyOverviewPlatforms;
}

export interface CategoryCompaniesStats {
	sdk_ios_total_companies: number;
	sdk_android_total_companies: number;
	adstxt_direct_ios_total_companies: number;
	adstxt_direct_android_total_companies: number;
	adstxt_reseller_ios_total_companies: number;
	adstxt_reseller_android_total_companies: number;
	total_companies: number;
	sdk_total_apps: number;
	sdk_ios_total_apps: number;
	sdk_android_total_apps: number;
	android_total_apps: number;
	ios_total_apps: number;
	android_total_companies: number;
	ios_total_companies: number;
}

export interface CategoryAppStats {
	sdk_ios_total_apps: number;
	sdk_android_total_apps: number;
	sdk_total_apps: number;
	api_ios_total_apps: number;
	api_android_total_apps: number;
	api_total_apps: number;
	adstxt_direct_ios_total_apps: number;
	adstxt_direct_android_total_apps: number;
	adstxt_reseller_ios_total_apps: number;
	adstxt_reseller_android_total_apps: number;
	total_apps: number;
	sdk_android_installs_d30: number;
	sdk_ios_installs_d30: number;
	adstxt_direct_android_installs_d30: number;
	adstxt_reseller_android_installs_d30: number;
	api_android_installs_d30: number;
	// Universe totals for market share / penetration computation
	sdk_android_universe_apps: number;
	sdk_ios_universe_apps: number;
	sdk_android_universe_installs_d30: number;
	sdk_ios_universe_installs_d30: number;
	api_android_universe_apps: number;
	api_ios_universe_apps: number;
	api_android_universe_installs_d30: number;
	// Totals for aggregated overview (multiple companies)
	total_companies?: number;
	sdk_ios_total_companies?: number;
	sdk_android_total_companies?: number;
	api_ios_total_companies?: number;
	api_android_total_companies?: number;
}

export interface CompanyDomain {
	domain_name: string;
	is_primary: boolean;
	country: string[];
	org: string[];
}

export interface ChildCompany {
	company_name: string;
	company_domain: string;
	company_logo_url: string | null;
	domains: CompanyDomain[];
}

export interface ParentCompanyContext {
	company_name: string;
	company_domain: string;
	company_logo_url: string | null;
}

export interface CompanyTree {
	queried_domain: string;
	is_secondary_domain: boolean;
	is_orphan: boolean;
	is_root: boolean; // derived property from Python, will be serialised
	company_name: string | null;
	company_domain: string | null;
	company_logo_url: string | null;
	domains: CompanyDomain[];
	parent: ParentCompanyContext | null;
	children: ChildCompany[];
}

export interface CompanyLookup {
	company_id: number;
	company_name: string;
	company_domain: string;
}

export interface CompanyTabIndicators {
	company_domain: string;
	domain_id: number | null;
	company_id: number | null;
	company_name: string | null;
	logo_url: string | null;
	parent_company_id: number | null;
	parent_domain: string | null;
	parent_domain_id: number | null;
	has_sdk_signal: boolean;
	has_api_signal: boolean;
	has_publisher_signal: boolean;
	has_app_ads_direct: boolean;
	has_app_ads_reseller: boolean;
	country: string | null;
	country_direct: string | null;
	creatives_app_count: number;
	has_trends: number;
	apps_sdk_added_count: number;
	apps_sdk_lost_count: number;
	apps_adstxt_direct_added_count: number;
	apps_adstxt_direct_lost_count: number;
	sdk_count: number;
	mediation_adapter_count: number;
	adstxt_direct_app_count: number;
	adstxt_parent_app_count: number;
	creatives_app_count_direct: number;
	has_trends_direct: number;
	apps_sdk_added_count_direct: number;
	apps_sdk_lost_count_direct: number;
	apps_adstxt_direct_added_count_direct: number;
	apps_adstxt_direct_lost_count_direct: number;
	sdk_count_direct: number;
	mediation_adapter_count_direct: number;
	is_parent_domain: boolean;
	linkedin_url?: string | null;
	github_user?: string | null;
	api_ip_resolved_country?: string | null;
}

export interface CompanyLayoutDetails {
	companyDetails: CompanyCategoryOverview;
	companyTree: CompanyTree;
	tabIndicators: CompanyTabIndicators;
}

export interface CompanyPatterns {
	package_patterns: string[];
	paths: string[];
}

export interface SDKPatterns {
	package_patterns: string[];
	paths: string[];
}

export interface CompanySDKs {
	[sdk_name: string]: SDKPatterns;
}

export interface CompanySDKsDict {
	companies: {
		[company_name: string]: CompanySDKs;
	};
}

export interface AdsTxtAdDomainDetails {
	publisher_id_count: number;
	develoepr_count: number;
	app_count: number;
}

export interface AdsTxtAdDomainOverview {
	google: {
		direct: AdsTxtAdDomainDetails;
		reseller: AdsTxtAdDomainDetails;
	};
	apple: {
		direct: AdsTxtAdDomainDetails;
		reseller: AdsTxtAdDomainDetails;
	};
}

export interface AdsTxtPublishersOverview {
	google: {
		direct: AdsTxtEntries[];
		reseller: AdsTxtEntries[];
	};
	apple: {
		direct: AdsTxtEntries[];
		reseller: AdsTxtEntries[];
	};
}

export interface CompanyOverviewScope {
	categories: {
		[key: string]: CategoryAppStats;
	};
	adstxt_ad_domain_overview?: AdsTxtAdDomainOverview | null;
	adstxt_publishers_overview?: AdsTxtPublishersOverview | null;
	trends_summary?: CompanyTrendsSummary | null;
}

export interface CompanyCategoryOverview {
	company_types: string[];
	adstxt_ad_domain_overview: AdsTxtAdDomainOverview | null;
	adstxt_publishers_overview: AdsTxtPublishersOverview | null;
	trends_summary?: CompanyTrendsSummary | null;
	domain_overview?: CompanyOverviewScope | null;
	parent_overview?: CompanyOverviewScope | null;
	mediation_adapters:
		| {
				adapter_string: string;
				adapter_company_domain: string;
				adapter_company_name: string;
				adapter_logo_url: string;
				app_category: string;
				app_count: number;
		  }[]
		| null;
	categories: {
		[key: string]: CategoryAppStats;
	};
}

export interface CompanyTrendPoint {
	source_key: string;
	platform: string;
	tag_source: string;
	period: string;
	year: number;
	quarter: number;
	total_apps: number;
	total_apps_in_quarter: number;
	apps_added: number;
	apps_lost: number;
	net_apps_change: number;
	pct_market_share?: number | null;
	previous_pct_market_share?: number | null;
	pct_market_share_change?: number | null;
	pct_market_share_change_pct?: number | null;
	pct_apps_added?: number | null;
	pct_apps_lost?: number | null;
	total_apps_change?: number | null;
	total_apps_change_pct?: number | null;
}

export interface CompanyTrendSummary {
	source_key?: string | null;
	platform?: string | null;
	tag_source?: string | null;
	latest_period?: string | null;
	latest_total_apps: number;
	previous_total_apps?: number | null;
	latest_apps_added: number;
	latest_apps_lost: number;
	latest_net_apps_change: number;
	latest_pct_market_share?: number | null;
	previous_pct_market_share?: number | null;
	latest_pct_market_share_change?: number | null;
	latest_pct_market_share_change_pct?: number | null;
	latest_pct_apps_added?: number | null;
	latest_pct_apps_lost?: number | null;
	qoq_total_apps_change?: number | null;
	qoq_total_apps_change_pct?: number | null;
	trailing_year_apps_added: number;
	trailing_year_apps_lost: number;
	trailing_year_net_apps_change: number;
	trailing_year_start_total_apps?: number | null;
	trailing_year_end_total_apps?: number | null;
}

export interface CompanyTrendsSummary {
	latest_period?: string | null;
	sources: {
		[key: string]: CompanyTrendSummary;
	};
}

export interface CompanyTrends {
	latest_period?: string | null;
	sources: {
		[key: string]: CompanyTrendSummary;
	};
	past_year: {
		[key: string]: CompanyTrendPoint[];
	};
	history: {
		[key: string]: CompanyTrendPoint[];
	};
}

export interface CompaniesCategoryOverview {
	categories: {
		[key: string]: CategoryCompaniesStats;
	};
}

export interface CompanyCreative {
	advertiser_name: string;
	advertiser_domain_name: string;
	publisher_name: string;
	store: number;
	company_domain: string;
	creative_thumb_url: string;
	md5_hash: string;
	file_extension: string;
	advertiser_store_id: string;
	publisher_store_id: string;
	advertiser_store_app_id: string;
	installs_sum_1w: number;
	installs_sum_4w: number;
	installs: number;
	rating_count: number;
	rating: number;
	advertiser_icon_url: string;
	publisher_icon_url: string;
	last_seen: string;
	store_link?: string;
}

type AppCategoriesByStore = {
	android: TabularData;
	ios: TabularData;
};

export interface CompanyFullDetails {
	status?: number;
	error?: string;
	companyDetails: CompanyCategoryOverview;
	companyTopApps: CompanyOverviewSections;
	appCats: CatData;

	companyTree: CompanyTree;
	companySdks: CompanySDKsDict;
	companyAppCategories: AppCategoriesByStore;
	parentAppCategories: AppCategoriesByStore | null;
	companyCreatives: CompanyCreative[];
	companyCountryApps?: CompanyCountryAppsByStore;
	hasB2BSdkAccess?: boolean;
}

export interface CompanyCountryAppItem {
	country: string;
	app_count: number;
}

export interface CompanyCountryAppsByStore {
	android: CompanyCountryAppItem[];
	ios: CompanyCountryAppItem[];
}

export interface CompanyTrendsDetails {
	status?: number;
	error?: string;
	companyDetails: CompanyCategoryOverview;
	companyTree: CompanyTree;
	companyTrends: CompanyTrends;
	companyLookup?: CompanyLookup | null;
}

export interface CompanyCategoryDetails {
	status?: number;
	error?: string;
	companyDetails: CompanyCategoryOverview;
	companyCategoryApps: CompanyOverviewSections;
	companyTree: CompanyTree;
	companyCountryApps?: CompanyCountryAppsByStore;
	hasB2BSdkAccess?: boolean;
}

export interface KeywordScore {
	keyword_id: number;
	keyword_text: string;
	app_count: number;
	total_apps: number;
	is_keyword_ranking?: boolean;
	is_keyword_generated?: boolean;
	is_keyword_user_added?: boolean;
	is_user_added?: boolean;
	competitiveness_score: number | null;
	d30_best_rank: number | string | null;
	latest_app_rank: number | string | null;
	volume_competition_score: number | null;
	keyword_difficulty: number | null;
	opportunity_score: number | null;
	median_competitor_installs: number | null;
	avg_competitor_rating: number | null;
	major_competitors: number;
	store?: number | string | null;
}

export interface AppSDKsOverview {
	company_categories: {
		[key: string]: Array<{
			company_name: string;
			company_domain: string;
			company_logo_url: string;
		}>;
	};
}

export type AppAPIs = Array<{ tld_url: string; url: string }>;

export interface AppAPIsOverview {
	apis: { apis: AppAPIs };
}

export interface AppSDKs {
	myPackageInfo: {
		permissions: string[];
		company_categories: { [key: string]: CompanySDKParts };
		android: string[];
		leftovers: UnknownSDKs;
		skadnetwork: string[];
		app_queries: string[];
	};
	companyTypes: CompanyTypes;
	myapp: AppFullDetail;
}

export interface AppCountryMetrics {
	week_start: string;
	country: string;
	rating: number;
	rating_count: number;
	one_star: number;
	two_star: number;
	three_star: number;
	four_star: number;
	five_star: number;
	new_rating: number;
	rating_rate_of_change: number;
	new_rating_count: number;
	rating_count_rate_of_change: number;
	rating_count_avg_per_day: number;
	new_one_star: number;
	one_star_rate_of_change: number;
	one_star_avg_per_day: number;
	new_two_star: number;
	two_star_rate_of_change: number;
	two_star_avg_per_day: number;
	new_three_star: number;
	three_star_rate_of_change: number;
	three_star_avg_per_day: number;
	new_four_star: number;
	four_star_rate_of_change: number;
	four_star_avg_per_day: number;
	new_five_star: number;
	five_star_rate_of_change: number;
	five_star_avg_per_day: number;
}

export interface AppGlobalMetrics {
	week_start: string;
	weekly_installs: number;
	rating: number;
	weekly_ratings: number;
	weekly_active_users: number;
	weekly_ad_revenue: number;
	weekly_iap_revenue: number;
	cumulative_installs: number;
	cumulative_ratings: number;
	one_star: number;
	two_star: number;
	three_star: number;
	four_star: number;
	five_star: number;
	weekly_installs_rate_of_change: number;
	weekly_installs_avg_per_day: number;
	new_rating: number;
	rating_rate_of_change: number;
	weekly_ratings_rate_of_change: number;
	weekly_ratings_avg_per_day: number;
	new_one_star: number;
	one_star_rate_of_change: number;
	one_star_avg_per_day: number;
	new_two_star: number;
	two_star_rate_of_change: number;
	two_star_avg_per_day: number;
	new_three_star: number;
	three_star_rate_of_change: number;
	three_star_avg_per_day: number;
	new_four_star: number;
	four_star_rate_of_change: number;
	four_star_avg_per_day: number;
	new_five_star: number;
	five_star_rate_of_change: number;
	five_star_avg_per_day: number;
}

export interface AppGlobalMetricsPlotData {
	changes: TabularData;
	installs: TabularData;
	ratings: TabularData;
	ratings_stars: TabularData;
	ratings_stars_new: TabularData;
}

export interface AppFullDetails {
	myapp: AppFullDetail;
	companyTypes: CompanyTypes;
	appCats: CatData;
	countries: { [key: string]: string };
	status?: number;
	error?: string;
	myranks: Promise<{ history: AppRankDetail[]; countries: string[] }>;
	myranksOverview: { countries: string[]; best_ranks: AppRankDetail[] };
	myhistory: Promise<{
		histogram: {
			one_star: number;
			two_star: number;
			three_star: number;
			four_star: number;
			five_star: number;
		};
		plot_data?: {
			changes: TabularData;
			installs: TabularData;
			ratings: TabularData;
			ratings_stars: TabularData;
			ratings_stars_new: TabularData;
		};
	}>;
	appSDKsOverview: AppSDKsOverview;
	myAdsTxtOverview: Promise<{
		direct_entries: AdsTxtEntries[];
		reseller_entries: AdsTxtEntries[];
	}>;
	myKeywords: Promise<{
		keywords: string[];
		keyword_scores: KeywordScore[];
	}>;
}

export interface Company {
	name: string;
	app_count: number;
	installs: number;
	ratings: number;
	installs_percent: number;
	ratings_percent: number;
	app_count_percent: number;
}

export interface CompanyTypes {
	types: companyType[];
}

export interface companyType {
	name: string;
	url_slug: string;
}

export interface CompaniesLayoutResponse {
	appCats: Promise<CatData>;
	companyTypes: Promise<{ types: companyType[] }>;
}

export interface AppFullDetail {
	// from cleaned -> string, maybe from db -> int, should rename to store_name and always use
	store: string;
	app_icon_url: string;
	name: string;
	installs?: number;
	store_id: string;
	id: number;
	developer_id?: string;
	developer_name?: string;
	store_link: string;
	store_developer_link?: string;
	developer_url?: string;
	last_crawled_at: string;
	rating?: number;
	rating_count: number;
	installs_sum_1w: number;
	installs_sum_4w: number;
	ratings_sum_1w: number;
	installs_z_score_2w: number;
	installs_z_score_4w: number;
	monthly_active_users: number;
	monthly_ad_revenue: number;
	monthly_iap_revenue: number;
	category: string;
	free: string;
	price: string;
	size?: string;
	minimum_android?: string;
	developer_email?: string;
	content_rating?: string;
	ad_supported?: string;
	in_app_purchases?: string;
	editors_choice?: string;
	crawl_result: number;
	release_date: string;
	store_last_updated: string;
	created_at: string;
	featured_image_url?: string;
	icon_128?: string;
	phone_image_url_1?: string;
	phone_image_url_2?: string;
	phone_image_url_3?: string;
	tablet_image_url_1?: string;
	tablet_image_url_2?: string;
	tablet_image_url_3?: string;
	description?: string;
	description_short?: string;
	adstxt_last_crawled: string;
	adstxt_crawl_result: number;
	version_code: string;
	sdk_last_crawled: string;
	sdk_last_crawl_result: number;
	sdk_successful_last_crawled: string;
	api_last_crawled?: string;
	api_successful_last_crawled?: string;
	run_result?: number;
	ad_creative_count?: number;
	ad_monetized_creative_count?: number;
	is_removed?: string;
	country_code?: string;
}

export type CategoryRanks = {
	category_id: number;
	category_name: string;
};

export type CollectionRanks = {
	collection_id: number;
	collection_name: string;
	categories: CategoryRanks[];
};

export type StoreIDLookup = {
	[key: number]: AppStore;
};

export type AppStore = {
	store_id: number;
	store_name: string;
	collections: CollectionRanks[];
};

export type StoreRankingsMap = {
	stores_rankings: AppStore[];
};

export type CrossfilterApp = {
	id: number;
	store_id: string;
	name: string;
	installs: number;
	rating_count: number;
	installs_d30: number;
	in_app_purchases: boolean;
	estimated_monthly_revenue: number;
	monthly_active_users: number;
	ad_supported: boolean;
	store: number;
	app_icon_url?: string;
};
