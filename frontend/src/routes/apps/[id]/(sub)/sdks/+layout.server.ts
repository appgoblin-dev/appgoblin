import type { LayoutServerLoad } from './$types';
import { createApiClient } from '#lib/server/api.js';

export const load: LayoutServerLoad = async ({ fetch, params, parent, locals }) => {
	const { myapp, companyTypes } = await parent();
	const api = createApiClient(fetch);

	const id = params.id;
	const versionTimeline = await api.get(`/apps/${id}/versions`, 'App Version Timeline');
	const latestVersion = Array.isArray(versionTimeline) ? versionTimeline[0] : undefined;
	const latestSdkDownloadedAt = Array.isArray(versionTimeline)
		? versionTimeline.reduce(
				(latest: string | null, entry: Record<string, any>) =>
					!latest || new Date(entry.downloaded_at ?? 0) > new Date(latest)
						? (entry.downloaded_at ?? latest)
						: latest,
				null
			)
		: null;
	const latestSdkScannedAt = Array.isArray(versionTimeline)
		? versionTimeline.reduce(
				(latest: string | null, entry: Record<string, any>) =>
					!latest || new Date(entry.sdks_last_scanned_at ?? 0) > new Date(latest)
						? (entry.sdks_last_scanned_at ?? latest)
						: latest,
				null
			)
		: null;

	const sdkVersionSummary = {
		latest_sdk_downloaded_at: latestSdkDownloadedAt,
		latest_sdk_scanned_at: latestSdkScannedAt,
		latest_sdk_version_code: latestVersion?.app_version_code ?? null
	};

	let myPackageInfo: Record<string, any> = {};
	// Only fetch SDK package info for logged-in or paid machine requests to avoid
	// wasted backend queries
	if ((locals.user || locals.machinePaid) && myapp.sdk_successful_last_crawled) {
		myPackageInfo = await api.get(`/apps/${id}/sdks`, 'App Package Info');
	}

	return {
		myPackageInfo,
		sdkVersionSummary,
		versionTimeline,
		companyTypes,
		myapp
	};
};
