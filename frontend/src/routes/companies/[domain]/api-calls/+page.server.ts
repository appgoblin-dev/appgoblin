import type { PageServerLoad } from './$types';
import { createApiClient } from '#lib/server/api.js';

type CompanyApiApps = {
	response_types: {
		company_domain: string;
		tld_url: string | null;
		response_type: string;
		app_count_30d: number;
		observed_call_count_30d: number;
		app_count_alltime: number;
		observed_call_count_alltime: number;
	}[];
	recent_endpoints: { host: string; path: string; last_seen: string }[];
	recent_requests: {
		host: string;
		path: string;
		called_at: string;
		store_id: string;
		name: string | null;
		icon_64: string | null;
		response_mime_type: string | null;
	}[];
};

export const load: PageServerLoad = async ({ fetch, params }) => {
	const api = createApiClient(fetch);
	const apiApps = await api.get(`/companies/${params.domain}/api-apps`, 'Company API Apps');
	return { apiApps: apiApps as CompanyApiApps };
};
