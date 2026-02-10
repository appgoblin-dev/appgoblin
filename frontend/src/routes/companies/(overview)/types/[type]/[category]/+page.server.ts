import { createApiClient } from '$lib/server/api.js';
import type { PageServerLoad } from './$types.js';
import { getCachedData } from '../../../../../../hooks.server';

export const ssr: boolean = true;
export const csr: boolean = true;

export const load: PageServerLoad = async ({ fetch, params, parent }) => {
	const cachedData = await getCachedData();
	const { appCats } = cachedData;
	const api = createApiClient(fetch);
	const companiesOverview = await api.get(
		`/companies/types/${params.type}?category=${params.category}`,
		'Companies Type Category Overview'
	);

	return { companiesOverview, appCats };
};
