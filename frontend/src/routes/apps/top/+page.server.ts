import type { PageServerLoad } from './$types';
import { createApiClient } from '$lib/server/api';

interface CompanyRaw {
	company_name: string | null;
	company_domain: string | null;
	total_apps: number;
}

export const load: PageServerLoad = async ({ fetch }) => {
	const api = createApiClient(fetch);

	// Load companies for the dropdown filters
	const companiesOverview = await api.get('/companies', 'Companies Overview');

	// Filter out companies with null names or domains, and sort by app count
	const companies = (companiesOverview.companies_overview || [])
		.filter(
			(c: CompanyRaw) =>
				c.company_name != null &&
				c.company_domain != null &&
				c.company_name.trim() !== '' &&
				c.company_domain.trim() !== ''
		)
		.sort((a: CompanyRaw, b: CompanyRaw) => (b.total_apps || 0) - (a.total_apps || 0));

	// Load categories
	const categoriesOverview = await api.get('/categories', 'Categories Overview');
	const categories = categoriesOverview.categories || [];

	return {
		companies,
		categories
	};
};

export const actions = {
	search: async ({ request, fetch }) => {
		const data = await request.formData();
		const api = createApiClient(fetch);

		const includeDomains = data.get('include_domains')?.toString() || '[]';
		const excludeDomains = data.get('exclude_domains')?.toString() || '[]';

		const payload = {
			include_domains: JSON.parse(includeDomains),
			exclude_domains: JSON.parse(excludeDomains),
			require_sdk_api: data.get('require_sdk_api') === 'true',
			require_iap: data.get('require_iap') === 'true',
			require_ads: data.get('require_ads') === 'true',
			mydate: data.get('mydate')?.toString(),
			category: data.get('category')?.toString() || null,
			store: data.get('store') ? parseInt(data.get('store')!.toString()) : null,
			min_installs: data.get('min_installs') ? parseInt(data.get('min_installs')!.toString()) : null,
			max_installs: data.get('max_installs') ? parseInt(data.get('max_installs')!.toString()) : null,
			min_rating_count: data.get('min_rating_count') ? parseInt(data.get('min_rating_count')!.toString()) : null,
			max_rating_count: data.get('max_rating_count') ? parseInt(data.get('max_rating_count')!.toString()) : null,
			min_installs_d30: data.get('min_installs_d30') ? parseInt(data.get('min_installs_d30')!.toString()) : null,
			max_installs_d30: data.get('max_installs_d30') ? parseInt(data.get('max_installs_d30')!.toString()) : null,
			sort_col: data.get('sort_col')?.toString() || 'installs',
			sort_order: data.get('sort_order')?.toString() || 'desc'
		};

		try {
			const response = await api.post('/apps/crossfilter', payload, 'Crossfilter Search');
			return { success: true, apps: response.apps };
		} catch (error) {
			console.error('Search Action Error:', error);
			return { success: false, error: 'Failed to fetch apps', apps: [] };
		}
	}
};
