import type { LayoutServerLoad } from './$types';
import { error } from '@sveltejs/kit';
import { createApiClient } from '#lib/server/api.js';
import { getAppCategories } from '#lib/server/appCategories.js';
import { db } from '#lib/server/auth/db.js';

const PROTECTED_PREFIXES = ['/app-adstxt/publisher/', '/app-adstxt/download'];

export const load: LayoutServerLoad = async ({ fetch, params, parent, locals, url }) => {
	// If the child route requires authentication and the user isn't logged in,
	// bail early and return 401 so Googlebot understands this page requires auth.
	const path = url.pathname.replace(/\/$/, '');
	const isProtected = PROTECTED_PREFIXES.some((prefix) => path.includes(prefix));
	if (isProtected && !locals.user) {
		error(401, 'Please sign in to view this page.');
	}

	const api = createApiClient(fetch);
	const companyDomain = params.domain;
	const category = params.category;

	const appCats = await getAppCategories();

	if (category && !appCats.categories.find((cat) => cat.id === category)) {
		error(404, {
			message: `Category "${category}" not found`
		});
	}

	const companyDetails = await api.get(`/companies/${companyDomain}`, 'Company Details');

	const companyTree = await api.get(`/companies/${companyDomain}/tree`, 'Company Tree');

	const [mediationPartners, tabIndicators] = await Promise.all([
		api
			.get(`/companies/${companyDomain}/mediation-partners`, 'Mediation Partners')
			.catch(() => null),
		api.get(`/companies/${companyDomain}/tabs`, 'Company Tab Indicators').catch(() => null)
	]);

	return {
		companyDetails,
		companyTree,
		mediationPartners,
		tabIndicators
	};
};
