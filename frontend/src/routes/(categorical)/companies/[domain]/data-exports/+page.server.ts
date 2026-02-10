import { db } from '$lib/server/auth/db';

import type { PageServerLoad } from './$types';

export const load: PageServerLoad = async ({ locals, params, parent }) => {
	const user = locals.user;
	let canDownload = false;

	if (user) {
		const row = await db.queryOne<{ status: string }>(
			`SELECT status FROM subscriptions
			 WHERE user_id = $1 AND status IN ('active', 'trialing')
			 ORDER BY created_at DESC LIMIT 1`,
			[user.id]
		);
		canDownload = !!row;
	}

	const parentData = await parent();
	const tree = parentData.companyTree as { queried_company_name?: string } | undefined;
	const companyName = tree?.queried_company_name ?? params.domain ?? '';

	return { canDownload, companyName };
};
