import type { PageServerLoad } from './$types';
import { createApiClient } from '$lib/server/api';
import { userHasTierAccess } from '$lib/server/subscription';

type Report = {
	file_key: string;
	report_name: string;
	row_count: number | null;
	last_modified: string;
	url?: string | null;
};

export const load: PageServerLoad = async ({ fetch, params, parent, locals }) => {
	const api = createApiClient(fetch);
	const parentData = await parent();
	const tree = parentData.companyTree as
		| { company_name?: string | null; company_domain?: string | null; queried_domain?: string }
		| undefined;
	const companyName =
		tree?.company_name ?? tree?.company_domain ?? tree?.queried_domain ?? params.domain ?? '';
	const reports = (await api.get(
		`/companies/${params.domain}/reports`,
		'Company Reports'
	)) as Report[];
	const canDownload = locals.user
		? await userHasTierAccess(locals.user.id, 'b2b_sdk', 'b2b_premium')
		: false;

	if (canDownload) {
		await Promise.all(
			reports.map(async (report) => {
				const query = new URLSearchParams({
					dataset: 'company-report',
					domain: params.domain,
					s3_key: report.file_key
				});
				const response = await fetch(
					`http://localhost:8000/api/public/exports/signed-url?${query.toString()}`
				);
				if (response.ok) report.url = ((await response.json()) as { url: string }).url;
			})
		);
	}

	return {
		companyName,
		reports,
		canDownload,
		userId: locals.user?.id ?? null
	};
};
