import type { PageServerLoad } from './$types';

import { _loadAdCreativesPage } from '../../+page.server';

export const ssr = true;
export const csr = true;

export const load: PageServerLoad = async ({ fetch, locals, params, url }) => {
	return _loadAdCreativesPage({
		fetch,
		isSignedIn: Boolean(locals.user),
		url,
		primaryFilter: 'app-category',
		category: params.category
	});
};
