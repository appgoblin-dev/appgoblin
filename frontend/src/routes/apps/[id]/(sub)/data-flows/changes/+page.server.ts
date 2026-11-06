import type { PageServerLoad } from './$types';

export const load: PageServerLoad = async ({ parent }) => {
	const { myapp } = await parent();

	return {
		myapp,
		// Meta Tags
		toFollow: 'noindex, follow',
		title: `Data Flow Changes for ${myapp.name}`,
		description: `Compare the companies contacted by ${myapp.name} between its two most recent scans.`,
		keywords: `data flows, scan diff, changes, tracking, data sharing`
	};
};
