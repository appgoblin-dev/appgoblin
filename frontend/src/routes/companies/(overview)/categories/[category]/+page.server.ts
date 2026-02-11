import type { PageServerLoad } from './$types';
import { createApiClient } from '$lib/server/api';

import { getCachedData } from '../../../../../hooks.server';

export const ssr: boolean = true;
export const csr: boolean = true;

export const load: PageServerLoad = async ({ fetch, params, parent }) => {
	const api = createApiClient(fetch);
	const companiesOverview = await api.get(
		`/companies/categories/${params.category}`,
		'Companies Category Overview'
	);

	const cachedData = await getCachedData();
	const { appCats } = cachedData;

	return { companiesOverview, appCats };
};
