import { db } from '$lib/server/auth/db';
import { buildAppAdsTxtUrl, buildCompanyVerifiedAppsUrl } from '$lib/server/downloads';

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
	const domain = params.domain ?? '';

	const downloadUrls = canDownload
		? {
				appAdsTxt: buildAppAdsTxtUrl(domain),
				companyVerifiedAndroid: buildCompanyVerifiedAppsUrl(domain, 'android'),
				companyVerifiedIos: buildCompanyVerifiedAppsUrl(domain, 'ios')
			}
		: null;

	return { canDownload, companyName, downloadUrls };
};
