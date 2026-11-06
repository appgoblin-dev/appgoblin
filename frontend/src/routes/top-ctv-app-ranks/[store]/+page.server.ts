import { error } from '@sveltejs/kit';
import type { PageServerLoad } from './$types';
import { createApiClient } from '#lib/server/api.js';

export const ssr: boolean = true;
export const csr: boolean = true;

const STORE_IDS: Record<string, number> = {
	google: 1,
	apple: 2
};

export const load: PageServerLoad = async ({ params, fetch }) => {
	const storeId = STORE_IDS[params.store];
	if (!storeId) {
		error(404, `Unknown store: ${params.store}`);
	}

	const api = createApiClient(fetch);
	const ranks = await api.get(`/rankings/ctv/${storeId}`, 'CTV App Ranks');

	return { ranks, storeId };
};
