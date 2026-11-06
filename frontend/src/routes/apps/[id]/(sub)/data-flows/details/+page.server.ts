import type { PageServerLoad } from './$types';

export const load: PageServerLoad = async ({ parent }) => {
	const { myapp } = await parent();

	return {
		myapp,
		// Meta Tags
		toFollow: 'noindex, follow',
		title: `API Calls for ${myapp.name}`,
		description: `Explore every API call made by ${myapp.name}. Filter by scan, company category, or captured ad creative.`,
		keywords: `tracking, data sharing, data flows, api calls, api, data`
	};
};
