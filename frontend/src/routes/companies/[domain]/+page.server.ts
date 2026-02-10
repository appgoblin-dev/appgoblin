import type { PageServerLoad } from './$types';
import { createApiClient } from '$lib/server/api';

import { getCachedData } from '../../../hooks.server';

export const ssr: boolean = true;
export const csr: boolean = true;

export const load: PageServerLoad = async ({ fetch, parent, params }) => {
	const api = createApiClient(fetch);
	const companyDomain = params.domain;
	const { appCats } = await getCachedData();
	const companyParentCategories = await api.get(
		`/companies/${companyDomain}/parentcategories`,
		'Company Parent Categories'
	);
	const companyTopApps = await api.get(`/companies/${companyDomain}/topapps`, 'Company Top Apps');

	const { companyDetails, companyTree } = await parent();

	return {
		companyDetails,
		companyTree,
		companyParentCategories,
		companyTopApps,
		companySdks: { companies: {} },
		companyCreatives: [],
		appCats
	};
};
