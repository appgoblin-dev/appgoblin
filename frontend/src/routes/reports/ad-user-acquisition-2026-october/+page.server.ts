import type { PageServerLoad } from '../../$types';
import { db } from '#lib/server/auth/db.js';
import { userHasTierAccess } from '#lib/server/subscription.js';

const reportJsonModules = import.meta.glob('./*.json', {
	eager: true,
	import: 'default'
}) as Record<string, unknown>;

interface SummaryData {
	apps_analyzed: number;
	https_tracked: number;
	api_domains: number;
	adtech_companies: number;
	advertisers: number;
	advertisers_all: number;
	creative_count: number;
}

interface AppAdImpactGrowthData {
	best_week: string;
	app_name: string;
	store_id: string;
	icon_128: string;
	category: string;
	advertiser_country: string | null;
	in_app_purchases: boolean;
	ad_supported: boolean;
	weekly_installs: number;
	weekly_revenue_estimate: number;
	monthly_active_users: number;
	weekly_percent_increase: number;
	baseline_installs: number;
	baseline_installs_pct: number;
	installs_z_score_2w: number;
	installs_z_score_4w: number;
	installs_acceleration: number;
	wow_growth_pct: number;
	momentum_pct: number | null;
	composite_score: number;
	phash: string;
	file_extension: string;
	host_ad_domain: string | null;
	initial_ad_domain: string | null;
	host_company_logo_url: string | null;
	initial_company_logo_url: string | null;
	mmp_domain?: string | null;
	mmp_domains: string | null;
	md5_hash: string;
	pub_count: number;
}

interface MostPopularCreativeData {
	phash: string;
	md5_hash: string;
	file_extension: string;
	advertiser_count: number;
	publisher_count: number;
	first_seen: string;
	last_seen: string;
	advertiser_store_id: string;
	advertiser_icon_128: string;
	advertiser_name?: string | null;
}

interface AdNetworkData {
	ad_network_name: string;
	ad_network_domain: string;
	company_logo_url: string;
	all_domains: string[] | string | null;
	domains?: string[];
	publisher_count: number;
	advertiser_count: number;
	creatives_count: number;
}

interface NewAdvertiserData {
	name: string;
	store_id: string;
	store: number;
	category: string;
	advertiser_country: string | null;
	installs: number | null;
	rating: number | null;
	rating_count: number | null;
	installs_sum_1w: number | null;
	installs_sum_4w: number | null;
	installs_z_score_2w: number | null;
	installs_z_score_4w: number | null;
	release_date: string;
	icon_128: string | null;
	developer_name: string | null;
	developer_id: number | null;
	ad_supported: boolean | null;
	in_app_purchases: boolean | null;
	ad_network_names: string[] | string | null;
	ad_network_domains: string[] | string | null;
	ad_network_logo_urls: string[] | string | null;
	mmp_domains: string[] | string | null;
	creative_count: number;
	md5_hashes: string[] | string | null;
	md5_file_extensions: string[] | string | null;
}

interface ProcessedNewAdvertiser {
	name: string;
	store_id: string;
	store: number;
	category: string;
	advertiser_country: string | null;
	installs: number | null;
	rating: number | null;
	rating_count: number | null;
	installs_sum_1w: number | null;
	installs_sum_4w: number | null;
	installs_z_score_2w: number | null;
	installs_z_score_4w: number | null;
	release_date: string;
	icon_128: string | null;
	developer_name: string | null;
	developer_id: number | null;
	ad_supported: boolean | null;
	in_app_purchases: boolean | null;
	creative_count: number;
	is_game: boolean;
	ad_networks: Array<{ name: string; domain: string; logo_url: string }>;
	mmps: Array<{ domain: string; logo_url: string }>;
	md5_hashes: string[];
	md5_file_extensions: string[];
}

interface AdvertiserCountryItem {
	country_code: string;
	advertiser_count: number;
}

interface AppReachData {
	advertiser_name: string | null;
	advertiser_store_id: string;
	advertiser_icon_128: string | null;
	advertiser_category: string | null;
	advertiser_installs: number | null;
	unique_creatives: number;
	unique_publishers: number;
	estimated_buying_size_score: number;
	buying_size_tier: string;
	first_seen: string;
	last_seen: string;
	ad_network_domains: string;
	avg_publisher_installs: number;
	mmp_domains: string | null;
	top_md5_hashes: string;
}

interface ProcessedApp {
	app_name: string;
	store_id: string;
	category: string;
	advertiser_country: string | null;
	best_week: string;
	icon_128: string;
	weekly_installs: number;
	weekly_revenue_estimate: number;
	monthly_active_users: number;
	weekly_percent_increase: number;
	baseline_installs: number;
	baseline_installs_pct: number;
	installs_z_score_2w: number;
	installs_z_score_4w: number;
	installs_acceleration: number;
	wow_growth_pct: number;
	momentum_pct: number | null;
	composite_score: number;
	creative_count: number;
	pub_count: number;
	ad_networks: Array<{
		domain: string;
		logo_url: string;
	}>;
	mmp_domains: Set<string>;
	mmps: Array<{
		domain: string;
		logo_url: string;
	}>;
	creatives: Array<{
		md5_hash: string;
		phash: string;
		file_extension: string;
		host_ad_domain: string | null;
		host_company_logo_url: string | null;
		initial_ad_domain: string | null;
		initial_company_logo_url: string | null;
	}>;
}

function getLogoUrlForDomain(domain: string): string {
	const domainLowercase = domain.trim().toLowerCase();

	const specialMappings: Record<string, string> = {
		'abr.ge': 'company-logos/airbridge.io/logo_200x200.jpeg'
	};

	if (domainLowercase in specialMappings) {
		return specialMappings[domainLowercase];
	}

	return `company-logos/${domain.trim()}/logo_200x200.jpeg`;
}

function parsePgArray(value: string | string[] | null | undefined): string[] {
	if (!value) {
		return [];
	}

	if (Array.isArray(value)) {
		return value.filter((item) => item && item.toLowerCase() !== 'null');
	}

	return value
		.replace(/^[{]|[}]$/g, '')
		.split(',')
		.map((item) => item.trim())
		.filter((item) => item && item.toLowerCase() !== 'null');
}

async function readReportJson<T>(fileName: string, fallback: T): Promise<T> {
	const moduleKey = `./${fileName}`;
	const reportData = reportJsonModules[moduleKey];

	return (reportData as T | undefined) ?? fallback;
}

function processData(data: AppAdImpactGrowthData[]): ProcessedApp[] {
	const appsMap = new Map<string, ProcessedApp>();

	data.forEach((row) => {
		if (!appsMap.has(row.store_id)) {
			appsMap.set(row.store_id, {
				app_name: row.app_name,
				store_id: row.store_id,
				category: row.category,
				advertiser_country: row.advertiser_country ?? null,
				best_week: row.best_week,
				icon_128: row.icon_128,
				weekly_installs: row.weekly_installs,
				weekly_revenue_estimate: row.weekly_revenue_estimate,
				monthly_active_users: row.monthly_active_users,
				weekly_percent_increase: row.weekly_percent_increase,
				baseline_installs: row.baseline_installs,
				baseline_installs_pct: row.baseline_installs_pct,
				installs_z_score_2w: row.installs_z_score_2w,
				installs_z_score_4w: row.installs_z_score_4w,
				installs_acceleration: row.installs_acceleration,
				wow_growth_pct: row.wow_growth_pct,
				momentum_pct: row.momentum_pct,
				composite_score: row.composite_score,
				creative_count: 0,
				pub_count: 0,
				ad_networks: [],
				mmp_domains: new Set(),
				mmps: [],
				creatives: []
			});
		}

		const app = appsMap.get(row.store_id)!;
		app.creative_count++;
		app.pub_count += row.pub_count;

		if (row.host_ad_domain && row.host_company_logo_url) {
			const exists = app.ad_networks.some((net) => net.domain === row.host_ad_domain);
			if (!exists) {
				app.ad_networks.push({
					domain: row.host_ad_domain,
					logo_url: row.host_company_logo_url
				});
			}
		}

		if (
			row.initial_ad_domain &&
			row.initial_company_logo_url &&
			row.initial_ad_domain !== row.host_ad_domain
		) {
			const exists = app.ad_networks.some((net) => net.domain === row.initial_ad_domain);
			if (!exists) {
				app.ad_networks.push({
					domain: row.initial_ad_domain,
					logo_url: row.initial_company_logo_url
				});
			}
		}

		parsePgArray(row.mmp_domains).forEach((domain) => app.mmp_domains.add(domain));

		app.creatives.push({
			md5_hash: row.md5_hash,
			phash: row.phash,
			file_extension: row.file_extension,
			host_ad_domain: row.host_ad_domain,
			host_company_logo_url: row.host_company_logo_url,
			initial_ad_domain: row.initial_ad_domain,
			initial_company_logo_url: row.initial_company_logo_url
		});
	});

	const sortedApps = Array.from(appsMap.values()).sort(
		(a, b) => b.composite_score - a.composite_score
	);

	sortedApps.forEach((app) => {
		app.mmps = Array.from(app.mmp_domains).map((domain) => ({
			domain,
			logo_url: getLogoUrlForDomain(domain)
		}));
	});

	return sortedApps;
}

async function getB2BAccess(userId: number): Promise<boolean> {
	return userHasTierAccess(userId, 'b2b_sdk', 'b2b_appads', 'b2b_premium');
}

export const load: PageServerLoad = async ({ locals }) => {
	let hasB2BAccess = false;
	if (locals.user) {
		hasB2BAccess = await getB2BAccess(locals.user.id);
	}

	const [
		rawSummaryData,
		rawMostPopularCreatives,
		rawAdNetworkData,
		adImpactGrowthData,
		rawAppReachData,
		rawNewAdvertisers,
		advertisersSample,
		advertiserCountries
	] = await Promise.all([
		readReportJson<SummaryData[]>('summary_executive.json', []),
		readReportJson<MostPopularCreativeData[]>('creatives.json', []),
		readReportJson<AdNetworkData[]>('ad_networks_landscape.json', []),
		readReportJson<AppAdImpactGrowthData[]>('impact_growth.json', []),
		readReportJson<AppReachData[]>('reach.json', []),
		readReportJson<NewAdvertiserData[]>('new_advertisers.json', []),
		readReportJson<Record<string, unknown>[]>('advertisers_sample.json', []),
		readReportJson<AdvertiserCountryItem[]>('advertiser_countries.json', [])
	]);

	const apps = processData(adImpactGrowthData).filter((app) => (app.wow_growth_pct ?? 0) > 0);

	const totalInstalls = apps.reduce((sum, app) => sum + app.weekly_installs, 0);
	const appsWithWowGrowth = apps.filter((app) => app.wow_growth_pct != null);
	const avgGrowth =
		appsWithWowGrowth.length > 0
			? appsWithWowGrowth.reduce((sum, app) => sum + app.wow_growth_pct, 0) /
				appsWithWowGrowth.length
			: 0;
	const totalCreatives = apps.reduce((sum, app) => sum + app.creative_count, 0);

	const allNetworks = new Set<string>();
	apps.forEach((app) => app.ad_networks.forEach((net) => allNetworks.add(net.domain)));

	const topApps = apps.slice(0, 5);

	const adNetworks = [...rawAdNetworkData]
		.sort((a, b) => b.publisher_count - a.publisher_count)
		.map((network) => ({
			...network,
			domains: parsePgArray(network.all_domains)
		}));

	const totalPublishers = adNetworks.reduce((sum, net) => sum + net.publisher_count, 0);
	const totalNetworkCreatives = adNetworks.reduce((sum, net) => sum + net.creatives_count, 0);

	const reachTiers = {
		elite: apps.filter((app) => app.pub_count >= 3),
		wide: apps.filter((app) => app.pub_count >= 2 && app.pub_count < 3),
		targeted: apps.filter((app) => app.pub_count >= 1 && app.pub_count < 2),
		emerging: apps.filter((app) => app.pub_count < 1)
	};

	const reachStats = {
		elite: {
			count: reachTiers.elite.length,
			avgPubCount:
				reachTiers.elite.length > 0
					? Math.round(
							(reachTiers.elite.reduce((sum, app) => sum + app.pub_count, 0) /
								reachTiers.elite.length) *
								10
						) / 10
					: 0,
			totalInstalls: reachTiers.elite.reduce((sum, app) => sum + app.weekly_installs, 0)
		},
		wide: {
			count: reachTiers.wide.length,
			avgPubCount:
				reachTiers.wide.length > 0
					? Math.round(
							(reachTiers.wide.reduce((sum, app) => sum + app.pub_count, 0) /
								reachTiers.wide.length) *
								10
						) / 10
					: 0,
			totalInstalls: reachTiers.wide.reduce((sum, app) => sum + app.weekly_installs, 0)
		},
		targeted: {
			count: reachTiers.targeted.length,
			avgPubCount:
				reachTiers.targeted.length > 0
					? Math.round(
							(reachTiers.targeted.reduce((sum, app) => sum + app.pub_count, 0) /
								reachTiers.targeted.length) *
								10
						) / 10
					: 0,
			totalInstalls: reachTiers.targeted.reduce((sum, app) => sum + app.weekly_installs, 0)
		},
		emerging: {
			count: reachTiers.emerging.length,
			avgPubCount: 0,
			totalInstalls: reachTiers.emerging.reduce((sum, app) => sum + app.weekly_installs, 0)
		}
	};

	const topReachApps = [...rawAppReachData]
		.sort((a, b) => (b.estimated_buying_size_score ?? 0) - (a.estimated_buying_size_score ?? 0))
		.map((app) => ({
			...app,
			ad_networks: parsePgArray(app.ad_network_domains).map((domain) => ({
				domain,
				logo_url: getLogoUrlForDomain(domain)
			})),
			mmps: parsePgArray(app.mmp_domains).map((domain) => ({
				domain,
				logo_url: getLogoUrlForDomain(domain)
			}))
		}));

	const advertiserNameByStoreId = new Map<string, string>();
	rawAppReachData.forEach((app) => {
		if (app.advertiser_name) {
			advertiserNameByStoreId.set(app.advertiser_store_id, app.advertiser_name);
		}
	});
	apps.forEach((app) => {
		advertiserNameByStoreId.set(app.store_id, app.app_name);
	});

	const popularCreatives = rawMostPopularCreatives.map((creative) => ({
		...creative,
		advertiser_name: advertiserNameByStoreId.get(creative.advertiser_store_id) ?? null,
		advertiser_icon_url_100: creative.advertiser_icon_128
	}));

	const exec = rawSummaryData[0] ?? null;

	const newAdvertisers: ProcessedNewAdvertiser[] = rawNewAdvertisers.map((app) => {
		const networkNames = parsePgArray(app.ad_network_names);
		const networkDomains = parsePgArray(app.ad_network_domains);
		const networkLogoUrls = parsePgArray(app.ad_network_logo_urls);

		return {
			name: app.name,
			store_id: app.store_id,
			store: app.store,
			category: app.category,
			advertiser_country: app.advertiser_country ?? null,
			installs: app.installs,
			rating: app.rating,
			rating_count: app.rating_count,
			installs_sum_1w: app.installs_sum_1w,
			installs_sum_4w: app.installs_sum_4w,
			installs_z_score_2w: app.installs_z_score_2w,
			installs_z_score_4w: app.installs_z_score_4w,
			release_date: app.release_date,
			icon_128: app.icon_128,
			developer_name: app.developer_name,
			developer_id: app.developer_id,
			ad_supported: app.ad_supported,
			in_app_purchases: app.in_app_purchases,
			creative_count: app.creative_count,
			is_game: app.category.startsWith('game_'),
			ad_networks: networkNames.map((_name, i) => ({
				name: networkNames[i] ?? '',
				domain: networkDomains[i] ?? '',
				logo_url: networkLogoUrls[i] ?? getLogoUrlForDomain(networkDomains[i] ?? '')
			})),
			mmps: parsePgArray(app.mmp_domains).map((domain) => ({
				domain,
				logo_url: getLogoUrlForDomain(domain)
			})),
			md5_hashes: parsePgArray(app.md5_hashes),
			md5_file_extensions: parsePgArray(app.md5_file_extensions)
		};
	});

	const newGames = newAdvertisers.filter((a) => a.is_game);
	const newApps = newAdvertisers.filter((a) => !a.is_game);

	return {
		apps,
		adNetworks,
		popularCreatives,
		newAdvertisers,
		newGames,
		newApps,
		reachTiers,
		reachStats,
		appReachData: topReachApps,
		networkStats: {
			totalPublishers,
			totalNetworkCreatives,
			totalNetworks: adNetworks.length
		},
		summary: {
			totalApps: exec?.apps_analyzed ?? apps.length,
			totalInstalls,
			avgGrowth: Math.round(avgGrowth * 10) / 10,
			totalCreatives: exec?.creative_count ?? totalCreatives,
			advertisers: exec?.advertisers_all ?? exec?.advertisers ?? null,
			adtechCompanies: exec?.adtech_companies ?? null,
			httpsTracked: exec?.https_tracked ?? null,
			apiDomains: exec?.api_domains ?? null,
			uniqueNetworks: allNetworks.size,
			reportPeriod: 'October 2026',
			generatedDate: 'November 6, 2026'
		},
		advertisersSample,
		advertiserCountries,
		topApps,
		title: 'User Acquisition Report - October 2026 | AppGoblin',
		description:
			'See October 2026 mobile ad campaigns, ad networks, and creatives behind the fastest-rising apps.',
		keywords:
			'user acquisition, october 2026, mobile ad campaigns, app marketing, mobile advertising, ad creatives, install growth',
		hasB2BAccess
	};
};
