import type { PageServerLoad } from './$types';
import { createApiClient } from '#lib/server/api.js';
import { db } from '#lib/server/auth/db.js';
import { requireAuthOrMachinePayment } from '#lib/server/auth/auth.js';

export const load: PageServerLoad = async (event) => {
	const { fetch, params, parent } = event;
	const { user } = requireAuthOrMachinePayment(event);
	const api = createApiClient(fetch);
	const id = params.id;
	// Load parent data first because it is cached
	const { myapp } = await parent();

	// Conditionally create myKeywords based on description length
	let myKeywords = 'No Keywords Result';
	if (myapp.description && myapp.description.length > 100) {
		myKeywords = await api.get(`/apps/${id}/keywords`, 'App Keywords');
	}

	const userTrackedKeywordsForApp = user
		? await db.query<{
				id: number;
				keyword_text: string;
				created_at: Date;
			}>(
				`SELECT id, keyword_text, created_at
		 FROM public.user_tracked_keywords
		 WHERE user_id = $1 AND store_id = $2
		 ORDER BY created_at DESC`,
				[user.id, id]
			)
		: [];

	return {
		// Meta Tags
		toFollow: 'noindex, nofollow',
		title: `Keywords for ${myapp.name}`,
		description: `Keywords used for ${myapp.name}. Browse the keyword rankings for ${myapp.name}.`,
		keywords: `keywords, aso`,
		// Data
		myKeywords,
		myapp,
		userTrackedKeywordsForApp
	};
};
