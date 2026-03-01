import type { PageServerLoad } from './$types';
import { createApiClient } from '$lib/server/api';
import { db } from '$lib/server/auth/db';
import { STRIPE_PRICES } from '$lib/server/stripe';
import { getCachedData } from '../../hooks.server';

interface CompanyRaw {
	company_name: string | null;
	company_domain: string | null;
	total_apps: number;
}

interface ActiveSubscriptionRow {
	provider_price_id: string;
}

async function getSubscriptionAccess(userId: number) {
	const row = await db.queryOne<ActiveSubscriptionRow>(
		`SELECT provider_price_id FROM subscriptions
		 WHERE user_id = $1 AND status IN ('active', 'trialing')
		 ORDER BY created_at DESC LIMIT 1`,
		[userId]
	);

	const hasPaidAccess = !!row;
	const hasB2BSdkAccess =
		!!row && [STRIPE_PRICES.b2b_sdk, STRIPE_PRICES.b2b_premium].includes(row.provider_price_id);

	return { hasPaidAccess, hasB2BSdkAccess };
}

export const load: PageServerLoad = async ({ fetch, locals }) => {
	const user = locals.user;
	let hasPaidAccess = false;
	let hasB2BSdkAccess = false;

	if (user) {
		const access = await getSubscriptionAccess(user.id);
		hasPaidAccess = access.hasPaidAccess;
		hasB2BSdkAccess = access.hasB2BSdkAccess;
	}

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
	// const categoriesOverview = await api.get('/categories', 'Categories Overview');
	const { countries, appCats } = await getCachedData();
	const categories = appCats || [];

	return {
		companies,
		categories,
		countries,
		hasPaidAccess,
		hasB2BSdkAccess
	};
};

export const actions = {
	search: async ({ request, fetch, locals }) => {
		const data = await request.formData();
		const api = createApiClient(fetch);

		let hasB2BSdkAccess = false;
		if (locals.user) {
			const access = await getSubscriptionAccess(locals.user.id);
			hasB2BSdkAccess = access.hasB2BSdkAccess;
		}

		const includeDomains = data.get('include_domains')?.toString() || '[]';
		const excludeDomains = data.get('exclude_domains')?.toString() || '[]';
		const parsedIncludeDomains = JSON.parse(includeDomains);
		const parsedExcludeDomains = JSON.parse(excludeDomains);

		const payload = {
			include_domains: hasB2BSdkAccess ? parsedIncludeDomains : [],
			exclude_domains: hasB2BSdkAccess ? parsedExcludeDomains : [],
			require_sdk_api: data.get('require_sdk_api') === 'true',
			require_iap: data.get('require_iap') === 'true',
			require_ads: data.get('require_ads') === 'true',
			ranking_country: data.get('ranking_country')?.toString() || null,
			mydate: data.get('mydate')?.toString(),
			category: data.get('category')?.toString() || null,
			store: data.get('store') ? parseInt(data.get('store')!.toString()) : null,
			min_installs: data.get('min_installs')
				? parseInt(data.get('min_installs')!.toString())
				: null,
			max_installs: data.get('max_installs')
				? parseInt(data.get('max_installs')!.toString())
				: null,
			min_rating_count: data.get('min_rating_count')
				? parseInt(data.get('min_rating_count')!.toString())
				: null,
			max_rating_count: data.get('max_rating_count')
				? parseInt(data.get('max_rating_count')!.toString())
				: null,
			min_installs_d30: data.get('min_installs_d30')
				? parseInt(data.get('min_installs_d30')!.toString())
				: null,
			max_installs_d30: data.get('max_installs_d30')
				? parseInt(data.get('max_installs_d30')!.toString())
				: null
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
