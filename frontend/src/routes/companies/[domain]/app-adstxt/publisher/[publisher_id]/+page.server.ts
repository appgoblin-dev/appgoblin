import type { PageServerLoad } from './$types';
import { createApiClient } from '$lib/server/api';
import { requireFullAuth } from '$lib/server/auth/auth';

export const ssr: boolean = true;
export const csr: boolean = true;

export const load: PageServerLoad = async (event) => {
	const { fetch, params } = event;
	const api = createApiClient(fetch);
	const companyDomain = params.domain;
	const publisher_id = params.publisher_id;
	requireFullAuth(event);
	const publishersApps = api.get(
		`/companies/${companyDomain}/adstxt/publisher/${publisher_id}`,
		'Company Publisher Apps'
	);
	return {
		publishersApps
	};
};
