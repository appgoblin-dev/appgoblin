import type { RequestHandler } from './$types';
import { requireAuthOrMachinePayment } from '#lib/server/auth/auth.js';

export const GET: RequestHandler = async (event) => {
	requireAuthOrMachinePayment(event);

	const csvResponse = await event.fetch(
		'/reports/mobile-apps-growth-sdks-q2-2026/AppGoblin Mobile Ecosystem 2026 Q2.csv'
	);

	if (!csvResponse.ok) {
		return new Response('CSV not available', { status: 502 });
	}

	return new Response(csvResponse.body, {
		status: 200,
		headers: {
			'Content-Type': 'text/csv; charset=utf-8',
			'Content-Disposition': 'attachment; filename="appgoblin-mobile-ecosystem-2026-q2.csv"',
			Link: '<https://creativecommons.org/licenses/by/4.0/>; rel="license", <https://appgoblin.info>; rel="canonical"',
			'X-Attribution': 'Data provided by AppGoblin (https://appgoblin.info).'
		}
	});
};
