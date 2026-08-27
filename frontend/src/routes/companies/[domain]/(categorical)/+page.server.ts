import { userHasTierAccess } from '$lib/server/subscription';
import type { PageServerLoad } from './$types';
import { createApiClient } from '$lib/server/api';

export const ssr: boolean = true;
export const csr: boolean = true;

export const load: PageServerLoad = async ({ fetch, parent, params, locals }) => {
	const api = createApiClient(fetch);
	const companyDomain = params.domain;

	const user = locals.user;
	let hasB2BSdkAccess = false;
	if (user) {
		hasB2BSdkAccess = await userHasTierAccess(user.id, 'b2b_sdk', 'b2b_premium');
	}

	const [
		companyAppCategories,
		companyTopApps,
		companyCountryApps,
		{ companyDetails, companyTree }
	] = await Promise.all([
		api.get(`/companies/${companyDomain}/parentcategories?rollup=false`, 'Company App Categories'),
		api.get(`/companies/${companyDomain}/topapps`, 'Company Top Apps'),
		api.get(`/companies/${companyDomain}/countries`, 'Company Country Apps'),
		parent()
	]);

	const parentAppCategories = companyDetails.parent_overview
		? await api.get(
				`/companies/${companyDomain}/parentcategories?rollup=true`,
				'Parent Company App Categories'
			)
		: null;

	return {
		companyDetails,
		companyTree,
		companyAppCategories,
		parentAppCategories,
		companyTopApps,
		companyCountryApps,
		companySdks: { companies: {} },
		companyCreatives: [],
		hasB2BSdkAccess
	};
};
