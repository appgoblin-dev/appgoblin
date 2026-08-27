import type { LayoutServerLoad } from './$types';
import { createApiClient } from '$lib/server/api';

export const load: LayoutServerLoad = async ({ fetch, params, parent, locals }) => {
	const { myapp, companyTypes } = await parent();
	const api = createApiClient(fetch);

	const id = params.id;

	let myPackageInfo: Record<string, any> = {};
	// Only fetch SDK package info for logged-in users to avoid wasted backend queries
	if (locals.user && myapp.sdk_successful_last_crawled) {
		myPackageInfo = await api.get(`/apps/${id}/sdks`, 'App Package Info');
	}

	return {
		myPackageInfo,
		companyTypes,
		myapp
	};
};
