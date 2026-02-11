// src/routes/mypath/download/+server.ts
import type { RequestHandler } from '@sveltejs/kit';

export const GET: RequestHandler = async ({ fetch, params }) => {
	const domain = params.domain || '';
	const publisher_id = params.publisher_id || '';

	const response = await fetch(
		`http://localhost:8000/api/companies/${domain}/adstxt/publisher/${publisher_id}/download`
	);

	// Create response with appropriate headers
	return new Response(response.body, {
		headers: {
			'Content-Type': 'text/csv',
			'Content-Disposition': `attachment; filename="adstxt_${domain}_${publisher_id}.csv"`
		}
	});
};
