import type { PageServerLoad } from './$types';
import { createApiClient } from '#lib/server/api.js';
import { getAnonymousSearchQuota } from '#lib/server/request-rate-limit.js';

export const load: PageServerLoad = async ({
	params,
	fetch,
	locals,
	request,
	getClientAddress
}) => {
	const api = createApiClient(fetch);
	const term = params.term;
	const searchTerm = decodeURIComponent(term);
	const userId = locals.user?.id;
	console.log(`search start term=${searchTerm} user=${userId}`);

	const appGroupByStore = await api.get(`/apps/search/${searchTerm}`, 'Apps Search', 30000, userId);
	const companiesResults = await api.get(`/companies/search/${searchTerm}`, 'Companies Search');

	return {
		appGroupByStore,
		companiesResults,
		searchQuota: getAnonymousSearchQuota({ locals, request, getClientAddress })
	};
};
