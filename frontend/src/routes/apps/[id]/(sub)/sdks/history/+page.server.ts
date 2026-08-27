import type { PageServerLoad } from './$types';
import { createApiClient } from '$lib/server/api';
import { userHasTierAccess } from '$lib/server/subscription';

export const load: PageServerLoad = async (event) => {
	const { fetch, params, parent, locals } = event;
	const parentData = await parent();
	const { myapp } = parentData;
	const api = createApiClient(fetch);

	let hasB2BSdkAccess = false;
	if (locals.user) {
		hasB2BSdkAccess = await userHasTierAccess(locals.user.id, 'b2b_sdk', 'b2b_premium');
	}

	const id = params.id;
	const versionTimeline = await api.get(`/apps/${id}/versions`, 'App Version Timeline');
	let sdkHistory: Record<string, any> = { history: [] };
	// Only fetch SDK history data if user has B2B access — avoids unnecessary backend queries
	if (hasB2BSdkAccess && myapp.sdk_successful_last_crawled) {
		sdkHistory = await api.get(`/apps/${id}/sdks/history`, 'App SDK History');
	}

	return {
		sdkHistory,
		myapp,
		hasB2BSdkAccess,
		versionTimeline,
		// Meta Tags
		toFollow: 'noindex, nofollow',
		title: `SDK Change History for ${myapp.name}`,
		description: `Historical view of SDK additions and removals across versions of ${myapp.name}.`,
		keywords: `SDKs, history, changes, versions, trackers`
	};
};
