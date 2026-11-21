import type { PageServerLoad } from './$types';
import { createApiClient } from '#lib/server/api.js';
import { requireAuthOr401 } from '#lib/server/auth/auth.js';
import { userHasTierAccess } from '#lib/server/subscription.js';

export const ssr: boolean = true;
export const csr: boolean = true;

export const load: PageServerLoad = async (event) => {
	const { params, fetch } = event;
	const value_pattern = params.pattern;
	const user = event.locals.user;
	const api = createApiClient(fetch);
	const isSignedIn = user !== null;
	const hasB2BSdkAccess = user ? await userHasTierAccess(user.id, 'b2b_sdk', 'b2b_premium') : false;

	const matchedApps = isSignedIn
		? api.get(`/sdks/${value_pattern}`, 'Sdks Pattern')
		: Promise.resolve(null);
	const matchedCompanies = api.get(`/sdks/${value_pattern}/companies`, 'Sdks Pattern Companies');

	return {
		matchedCompanies,
		matchedApps,
		isSignedIn,
		hasB2BSdkAccess
	};
};

export const actions = {
	emailExport: async (event) => {
		const { user } = requireAuthOr401(event);
		const { params, fetch } = event;
		const hasB2BSdkAccess = await userHasTierAccess(user.id, 'b2b_sdk', 'b2b_premium');

		if (!hasB2BSdkAccess) {
			return { success: false, error: 'B2B SDK Intelligence access is required.' };
		}

		try {
			const api = createApiClient(fetch);
			const response = await api.post(
				`/sdks/${encodeURIComponent(params.pattern)}/export`,
				{ recipient_email: user.email, user_id: user.id },
				'SDK Pattern Export'
			);
			return {
				success: true,
				exportMessage:
					'Report queued, when finished a download link will be emailed and available in your Account Reports tab.',
				reportId: response.report_id
			};
		} catch (error) {
			console.error('SDK Pattern Export Action Error:', error);
			return { success: false, error: 'Failed to queue CSV export.' };
		}
	}
};
