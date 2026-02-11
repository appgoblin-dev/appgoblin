import type { LayoutServerLoad } from './$types';
import { error } from '@sveltejs/kit';
import { createApiClient } from '$lib/server/api';

import { getCachedData } from '../../../hooks.server';

export const load: LayoutServerLoad = async ({ fetch, params, parent }) => {
	const api = createApiClient(fetch);
	const companyDomain = params.domain;
	const category = params.category;

	const { appCats } = await getCachedData();

	if (category && !appCats.categories.find((cat) => cat.id === category)) {
		error(404, {
			message: `Category "${category}" not found`
		});
	}

	let url;

	if (category) {
		url = `/companies/${companyDomain}?category=${category}`;
	} else {
		url = `/companies/${companyDomain}`;
	}

	const companyDetails = await api.get(url, 'Company Details');

	const companyTree = await api.get(`/companies/${companyDomain}/tree`, 'Company Tree');

	return {
		companyDetails,
		companyTree
	};
};
