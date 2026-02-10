import type { PageServerLoad } from './$types';
import { createApiClient } from '$lib/server/api';

export const ssr: boolean = true;
export const csr: boolean = true;

export const load: PageServerLoad = async ({ fetch, params }) => {
	const api = createApiClient(fetch);
	const companiesOverview = await api.get(
		`/companies/types/${params.type}`,
		'Companies Type Overview'
	);
	return { companiesOverview };
};
