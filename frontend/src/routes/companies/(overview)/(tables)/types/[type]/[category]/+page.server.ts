import { createApiClient } from '#lib/server/api.js';
import { getAppCategories } from '#lib/server/appCategories.js';
import type { PageServerLoad } from './$types.js';

export const ssr: boolean = true;
export const csr: boolean = true;

export const load: PageServerLoad = async ({ fetch, params, parent }) => {
	const appCats = await getAppCategories();
	const api = createApiClient(fetch);
	const companiesOverview = await api.get(
		`/companies/types/${params.type}?category=${params.category}`,
		'Companies Type Category Overview'
	);

	return { companiesOverview, appCats };
};
