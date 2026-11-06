import { redirect } from '@sveltejs/kit';
import type { PageServerLoad } from './$types';
import { createApiClient } from '#lib/server/api.js';
import { sanitizeSearchTerm } from '#lib/search.js';

export const load: PageServerLoad = async ({ params, fetch, locals }) => {
	const api = createApiClient(fetch);
	const searchTerm = sanitizeSearchTerm(params.term);
	if (!searchTerm) {
		redirect(303, '/');
	}

	const userId = locals.user?.id;
	console.log(`search start term=${searchTerm} user=${userId}`);

	const encodedSearchTerm = encodeURIComponent(searchTerm);
	const appGroupByStore = await api.get(
		`/apps/search/${encodedSearchTerm}`,
		'Apps Search',
		30000,
		userId
	);
	const companiesResults = await api.get(
		`/companies/search/${encodedSearchTerm}`,
		'Companies Search'
	);

	return {
		appGroupByStore,
		companiesResults,
		searchQuota: locals.anonymousSearchQuota ?? null
	};
};
