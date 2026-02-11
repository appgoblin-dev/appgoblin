import type { PageServerLoad } from '../../$types';
import { createApiClient } from '$lib/server/api';

export const csr = true;
export const ssr = true;

export const load: PageServerLoad = async ({ fetch }) => {
	const api = createApiClient(fetch);
	const companiesOverview = await api.get('/companies', 'Companies Overview');
	return { companiesOverview };
};
