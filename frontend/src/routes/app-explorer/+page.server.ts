import type { PageServerLoad } from './$types';
import { createApiClient } from '$lib/server/api';
import { requireFullAuth } from '$lib/server/auth/auth';
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

interface CrossfilterPayload {
	include_domains: string[];
	exclude_domains: string[];
	require_sdk_api: boolean;
	require_iap: boolean;
	require_ads: boolean;
	ranking_country: string | null;
	mydate: string | null;
	category: string | null;
	store: number | null;
	min_installs: number | null;
	max_installs: number | null;
	min_rating_count: number | null;
	max_rating_count: number | null;
	min_installs_d30: number | null;
	max_installs_d30: number | null;
}

function parseJsonArrayField(value: FormDataEntryValue | null): string[] {
	if (value == null) return [];

	try {
		const parsed = JSON.parse(value.toString());
		return Array.isArray(parsed)
			? parsed.filter((entry): entry is string => typeof entry === 'string')
			: [];
	} catch {
		return [];
	}
}

function parseOptionalNumberField(value: FormDataEntryValue | null): number | null {
	if (value == null) return null;
	const stringValue = value.toString().trim();
	if (stringValue === '') return null;

	const parsed = Number.parseInt(stringValue, 10);
	return Number.isNaN(parsed) ? null : parsed;
}

function buildCrossfilterPayload(data: FormData, hasB2BSdkAccess: boolean): CrossfilterPayload {
	const parsedIncludeDomains = parseJsonArrayField(data.get('include_domains'));
	const parsedExcludeDomains = parseJsonArrayField(data.get('exclude_domains'));

	return {
		include_domains: hasB2BSdkAccess ? parsedIncludeDomains : [],
		exclude_domains: hasB2BSdkAccess ? parsedExcludeDomains : [],
		require_sdk_api: data.get('require_sdk_api') === 'true',
		require_iap: data.get('require_iap') === 'true',
		require_ads: data.get('require_ads') === 'true',
		ranking_country: data.get('ranking_country')?.toString() || null,
		mydate: data.get('mydate')?.toString() || null,
		category: data.get('category')?.toString() || null,
		store: parseOptionalNumberField(data.get('store')),
		min_installs: parseOptionalNumberField(data.get('min_installs')),
		max_installs: parseOptionalNumberField(data.get('max_installs')),
		min_rating_count: parseOptionalNumberField(data.get('min_rating_count')),
		max_rating_count: parseOptionalNumberField(data.get('max_rating_count')),
		min_installs_d30: parseOptionalNumberField(data.get('min_installs_d30')),
		max_installs_d30: parseOptionalNumberField(data.get('max_installs_d30'))
	};
}

function hasExportFilters(payload: CrossfilterPayload): boolean {
	return (
		payload.include_domains.length > 0 ||
		payload.exclude_domains.length > 0 ||
		payload.require_sdk_api ||
		payload.require_iap ||
		payload.require_ads ||
		payload.ranking_country != null ||
		payload.category != null ||
		payload.store != null ||
		payload.min_installs != null ||
		payload.max_installs != null ||
		payload.min_rating_count != null ||
		payload.max_rating_count != null ||
		payload.min_installs_d30 != null ||
		payload.max_installs_d30 != null
	);
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

		const payload = buildCrossfilterPayload(data, hasB2BSdkAccess);

		try {
			const response = await api.post('/apps/crossfilter', payload, 'Crossfilter Search');
			return { success: true, apps: response.apps };
		} catch (error) {
			console.error('Search Action Error:', error);
			return { success: false, error: 'Failed to fetch apps', apps: [] };
		}
	},
	emailCsv: async (event) => {
		const { user } = requireFullAuth(event);
		const { request, fetch } = event;
		const data = await request.formData();
		const api = createApiClient(fetch);
		const access = await getSubscriptionAccess(user.id);

		if (!access.hasPaidAccess) {
			return {
				success: false,
				error: 'A paid subscription is required to email CSV exports.',
				apps: []
			};
		}

		const payload = buildCrossfilterPayload(data, access.hasB2BSdkAccess);

		if (!hasExportFilters(payload)) {
			return {
				success: false,
				error: 'Set at least one filter before exporting a CSV.',
				apps: []
			};
		}

		try {
			const exportResponse = await api.post(
				'/apps/crossfilter/export',
				{ ...payload, recipient_email: user.email },
				'Crossfilter Export'
			);

			return {
				success: true,
				exportQueued: true,
				exportMessage: `CSV export queued. A download link will be sent to ${user.email} within the next 15 minutes.`,
				reportId: exportResponse.report_id
			};
		} catch (error) {
			console.error('Email CSV Action Error:', error);
			return {
				success: false,
				error: 'Failed to queue CSV export',
				apps: []
			};
		}
	}
};
