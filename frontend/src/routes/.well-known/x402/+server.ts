import type { RequestHandler } from './$types';

import { getMachinePaymentResources } from '#lib/server/machine-payment.js';

const headers = {
	'Access-Control-Allow-Origin': '*',
	'Access-Control-Allow-Methods': 'GET, OPTIONS',
	'Cache-Control': 'public, max-age=3600, stale-while-revalidate=86400',
	Vary: 'Host'
};

export const GET: RequestHandler = ({ url }) =>
	new Response(
		JSON.stringify({
			version: 1,
			resources: getMachinePaymentResources(url.origin)
		}),
		{
			status: 200,
			headers: {
				...headers,
				'Content-Type': 'application/json; charset=utf-8',
				'X-Content-Type-Options': 'nosniff'
			}
		}
	);

export const OPTIONS: RequestHandler = () =>
	new Response(null, {
		status: 204,
		headers
	});
