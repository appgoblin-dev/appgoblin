import { fail } from '@sveltejs/kit';
import type { RequestEvent } from '@sveltejs/kit';
import { requireAuthOr401 } from '#lib/server/auth/auth.js';
import { db } from '#lib/server/auth/db.js';
import { insertRequestedScan } from './service.js';

export async function addRequestedSdkScan(event: RequestEvent) {
	const { user } = requireAuthOr401(event);
	const data = await event.request.formData();
	const storeId = data.get('store_id')?.toString().trim() ?? '';
	if (!storeId) {
		return fail(400, { section: 'requested-scans', message: 'App store ID is required' });
	}
	await insertRequestedScan(db, user.id, storeId);
	return { section: 'requested-scans', success: true, message: 'SDK scan request submitted' };
}
