import type { PageServerLoad } from './$types';
import { createApiClient } from '$lib/server/api';

export const load: PageServerLoad = async ({ fetch, params, parent }) => {
	const api = createApiClient(fetch);
	const companyDomain = params.domain;

	const companySdks = await api.get(`/companies/${companyDomain}/sdks`, 'Company SDKs');

	// waiting for parent layout data
	const { companyDetails, companyTree } = await parent();

	return {
		companyDetails,
		companyTree,
		companySdks
	};
};
