import { error, json } from '@sveltejs/kit';
import { requireAuthOr401 } from '#lib/server/auth/auth.js';
import { db } from '#lib/server/auth/db.js';
import {
	findRequestedScan,
	parsePositiveInteger,
	scanProgress
} from '#lib/server/requested-scans/service.js';
import type { RequestHandler } from './$types';

export const GET: RequestHandler = async (event) => {
	const { user } = requireAuthOr401(event);
	const id = parsePositiveInteger(event.params.id);
	if (id === null || id > 2147483647) error(400, 'Invalid request ID');
	const scan = await findRequestedScan(db, user.id, id);
	if (!scan) error(404, 'Scan request not found');
	if (!scan.created_at) {
		return json(scanProgress(scan), { headers: { 'cache-control': 'private, no-store' } });
	}

	const params = new URLSearchParams({
		store_id: scan.store_id,
		requested_at: scan.created_at.toISOString()
	});
	let response: Response;
	try {
		response = await event.fetch(`http://localhost:8000/analytics/scan-progress?${params}`, {
			signal: AbortSignal.timeout(15000)
		});
	} catch {
		error(503, 'Scan progress is temporarily unavailable');
	}
	if (!response.ok) error(503, 'Scan progress is temporarily unavailable');
	const result = await response.json();
	return json({ ...result, id: scan.id }, { headers: { 'cache-control': 'private, no-store' } });
};
