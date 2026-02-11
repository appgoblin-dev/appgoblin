/**
 * Parametrized download URL builder for data exports.
 * Base URL: set APPGOBLIN_DOWNLOADS_BASE in env, or defaults to https://media.appgoblin.info/
 * You can replace with loadConfig() and parsedConfig.cloud?.downloads_base if using config.toml.
 */

import { env } from '$env/dynamic/private';

const DEFAULT_BASE = 'https://media.appgoblin.info/';

function getDownloadsBaseUrl(): string {
	const base = env.APPGOBLIN_DOWNLOADS_BASE?.trim();
	if (base) return base.endsWith('/') ? base : `${base}/`;
	return DEFAULT_BASE;
}

/** app-ads.txt (both iOS and Android): downloads/app-ads-txt/domain=x/appgoblin_x_app_ads_txt.csv */
export function buildAppAdsTxtUrl(domain: string): string | null {
	if (!domain) return null;
	const base = getDownloadsBaseUrl();
	return `${base}downloads/app-ads-txt/domains/domain=${encodeURIComponent(domain)}/appgoblin_${encodeURIComponent(domain)}_app_ads_txt.csv`;
}

/** company-verified-apps by platform: downloads/company-verified-apps/domains/domain=x/platform=ios|android/source=all/appgoblin_x_latest.csv */
export function buildCompanyVerifiedAppsUrl(
	domain: string,
	platform: 'ios' | 'android'
): string | null {
	if (!domain || !platform) return null;
	const base = getDownloadsBaseUrl();
	return `${base}downloads/company-verified-apps/domains/domain=${encodeURIComponent(domain)}/source=all/appgoblin_${encodeURIComponent(domain)}_${platform}_verified_apps.csv`;
}

/** Specific SDK slug (both iOS and Android): downloads/dataset=sdk-apps/sdk_slug=xx-slug/latest.csv */
export function buildSdkAppsUrl(sdkSlug: string): string | null {
	if (!sdkSlug) return null;
	const base = getDownloadsBaseUrl();
	return `${base}downloads/sdk-apps/sdk_slug=${encodeURIComponent(sdkSlug)}/appgoblin_${encodeURIComponent(sdkSlug)}_latest.csv`;
}
