import type { PageServerLoad } from './$types';
import { createApiClient } from '#lib/server/api.js';

export const load: PageServerLoad = async ({ fetch }) => {
	try {
		const summary = await createApiClient(fetch).get('/companies/summary', 'Company Summary');
		return { summary };
	} catch (error) {
		console.error('Unable to load company summary', error);
		return { summary: null };
	}
};
