import type { RequestHandler } from './$types';

// Never prerender or cache: this must reflect the live session cookie so the
// login button shows the correct state even on prerendered/cached pages.
export const prerender = false;

const NO_CACHE_HEADERS = {
	'Cache-Control': 'no-store, no-cache, must-revalidate',
	Pragma: 'no-cache',
	Expires: '0',
	'Content-Type': 'application/json'
};

export const GET: RequestHandler = async ({ locals }) => {
	const user = locals.user
		? {
				id: locals.user.id,
				username: locals.user.username,
				emailVerified: locals.user.emailVerified
			}
		: null;

	return new Response(JSON.stringify({ user }), {
		status: 200,
		headers: NO_CACHE_HEADERS
	});
};
