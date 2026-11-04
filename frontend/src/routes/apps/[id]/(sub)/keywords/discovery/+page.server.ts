import type { PageServerLoad } from './$types';
import { createApiClient } from '#lib/server/api.js';
import { requireAuthOrMachinePayment } from '#lib/server/auth/auth.js';

export const load: PageServerLoad = async (event) => {
	const { fetch, params, parent } = event;
	requireAuthOrMachinePayment(event);
	const api = createApiClient(fetch);
	const id = params.id;
	const { myapp } = await parent();

	let myKeywords = 'No Keywords Result';
	if (myapp.description && myapp.description.length > 100) {
		myKeywords = await api.get(`/apps/${id}/keywords`, 'App Keywords');
	}

	return {
		toFollow: 'noindex, nofollow',
		title: `Discovery Keywords for ${myapp.name}`,
		description: `Description-derived keyword suggestions for ${myapp.name}.`,
		keywords: 'keywords, aso, discovery',
		myKeywords,
		myapp
	};
};
