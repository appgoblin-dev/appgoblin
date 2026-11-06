import type { RequestEvent } from '@sveltejs/kit';
import { error, redirect } from '@sveltejs/kit';
import { requireFullAuth } from '#lib/server/auth/auth.js';
import { userHasTierAccess } from '#lib/server/subscription.js';

export async function GET(event: RequestEvent) {
	const { user } = requireFullAuth(event);

	const hasB2B = await userHasTierAccess(user.id, 'b2b_sdk', 'b2b_appads', 'b2b_premium');
	if (!hasB2B) {
		error(403, 'A B2B Intelligence subscription is required to download this CSV.');
	}

	const pathParts = event.url.pathname.split('/').filter(Boolean);
	const reportsIdx = pathParts.indexOf('reports');
	if (reportsIdx === -1 || reportsIdx + 1 >= pathParts.length) {
		error(500, 'Could not determine report slug from request path.');
	}
	const slug = pathParts[reportsIdx + 1];

	let signingResponse: Response;
	try {
		signingResponse = await fetch(
			`http://localhost:8000/api/internal/exports/advertiser-report-signed-url?slug=${encodeURIComponent(slug)}`
		);
	} catch (err) {
		console.error('Signing request failed for advertiser CSV:', err);
		error(502, 'Unable to prepare the CSV download. Please try again later.');
	}

	if (!signingResponse.ok) {
		if (signingResponse.status === 404) {
			error(404, 'The advertiser CSV for this report has not been published yet.');
		}
		console.error(`Signing service returned ${signingResponse.status} for advertiser CSV`);
		error(502, 'Failed to prepare the CSV download.');
	}

	const { url } = (await signingResponse.json()) as { url?: string };
	if (!url) error(502, 'Signing service returned an invalid download URL.');
	redirect(303, url, { external: true });
}
