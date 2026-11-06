import type { LayoutServerLoad } from './$types';
import { createApiClient } from '#lib/server/api.js';
import type { AppAPIsOverview } from '../../../../../types';

const EMPTY_APIS: AppAPIsOverview = {
	apis: [],
	scans: [],
	categories: [],
	creatives: [],
	scan_diff: null
};

export const load: LayoutServerLoad = async ({ fetch, params, parent }) => {
	const { myapp } = await parent();

	let apis: AppAPIsOverview = EMPTY_APIS;
	if (myapp.api_successful_last_crawled) {
		const api = createApiClient(fetch);
		const response = await api.get(`/apps/${params.id}/apis`, 'App APIs');
		if (response && Array.isArray(response.apis)) {
			apis = {
				apis: response.apis,
				scans: response.scans ?? [],
				categories: response.categories ?? [],
				creatives: response.creatives ?? [],
				scan_diff: response.scan_diff ?? null
			};
		}
	}

	return { apis, myapp };
};
