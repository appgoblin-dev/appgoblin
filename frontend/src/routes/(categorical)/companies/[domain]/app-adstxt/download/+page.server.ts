import { redirect } from '@sveltejs/kit';
import { requirePaidSubscription } from '$lib/server/auth/auth';
import { buildAppAdsTxtUrl } from '$lib/server/downloads';

import type { PageServerLoad } from './$types';

export const load: PageServerLoad = async (event) => {
	await requirePaidSubscription(event);
	const domain = event.params.domain || '';
	const downloadUrl = buildAppAdsTxtUrl(domain);
	if (downloadUrl) throw redirect(302, downloadUrl);
	return { downloadUrl: null };
};
