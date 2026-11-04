import type { PageServerLoad } from './$types';
import { createApiClient } from '#lib/server/api.js';
import { db } from '#lib/server/auth/db.js';
import { requireAuthOrMachinePayment } from '#lib/server/auth/auth.js';

export const load: PageServerLoad = async (event) => {
	const { fetch, url, parent } = event;
	const { user } = requireAuthOrMachinePayment(event);
	const api = createApiClient(fetch);
	const { myapp } = await parent();
	const storeId = myapp.store_id as string;

	// Parse comma-separated keyword texts from ?k=casino,slots,poker
	const kParam = url.searchParams.get('k') ?? '';
	const requestedKeywords = kParam
		.split(',')
		.map((s) => s.trim().toLowerCase())
		.filter(Boolean)
		.slice(0, 10); // max 10 keywords for safety

	// Fetch the full keyword list for this app to resolve texts → ids
	let myKeywords: any = null;
	try {
		myKeywords = await api.get(`/apps/${storeId}/keywords`, 'App Keywords');
	} catch (e) {
		console.error('Error fetching keywords for compare:', e);
	}

	// Build the available keyword list (text only, sorted by opportunity score desc)
	let availableKeywords: string[] = [];
	if (myKeywords && typeof myKeywords === 'object' && 'keyword_scores' in myKeywords) {
		const scores = (myKeywords as any).keyword_scores as any[];
		availableKeywords = [...scores]
			.sort((a, b) => (Number(b.opportunity_score) || 0) - (Number(a.opportunity_score) || 0))
			.map((s) => s.keyword_text as string)
			.filter(Boolean);
	}

	// Fetch user's personally tracked keywords for this app
	const rows = user
		? await db.query<{ keyword_text: string }>(
				`SELECT keyword_text FROM public.user_tracked_keywords
		 WHERE user_id = $1 AND store_id = $2
		 ORDER BY created_at DESC`,
				[user.id, storeId]
			)
		: [];
	const trackedKeywords = rows.map((r) => r.keyword_text);

	let keywordHistory: any[] = [];
	let resolvedKeywords: { keyword_id: number; keyword_text: string }[] = [];

	if (myKeywords && typeof myKeywords === 'object' && 'keyword_scores' in myKeywords) {
		const scores = (myKeywords as any).keyword_scores as any[];

		// Resolve keyword texts to their ids
		resolvedKeywords = scores
			.filter(
				(s) =>
					requestedKeywords.includes(s.keyword_text?.toLowerCase()) &&
					typeof s.keyword_id === 'number'
			)
			.map((s) => ({ keyword_id: s.keyword_id, keyword_text: s.keyword_text }))
			.slice(0, 10);

		if (resolvedKeywords.length > 0) {
			const queryParams = resolvedKeywords.map((k) => `keyword_ids=${k.keyword_id}`).join('&');
			try {
				keywordHistory = await api.get(
					`/keywords/app/${myapp.id}?${queryParams}`,
					'Keyword History'
				);
			} catch (e) {
				console.error('Error fetching keyword history for compare:', e);
			}
		}
	}

	const keywordTexts = resolvedKeywords.map((k) => k.keyword_text);

	return {
		toFollow: 'noindex, nofollow',
		title: `Compare Keywords for ${myapp.name}`,
		description: `Rank history comparison for ${keywordTexts.join(', ')} on ${myapp.name}.`,
		keywords: `keywords, aso, compare, ${keywordTexts.join(', ')}`,
		myapp,
		requestedKeywords,
		resolvedKeywords,
		keywordHistory,
		availableKeywords,
		trackedKeywords
	};
};
