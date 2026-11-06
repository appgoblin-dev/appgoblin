import { error } from '@sveltejs/kit';
import { requireAuthOr401 } from '#lib/server/auth/auth.js';
import { db } from '#lib/server/auth/db.js';
import { addRequestedSdkScan } from '#lib/server/requested-scans/action.js';
import { listRequestedScans, parsePositiveInteger } from '#lib/server/requested-scans/service.js';
import type { Actions, PageServerLoad } from './$types';

export const load: PageServerLoad = async (event) => {
	const { user } = requireAuthOr401(event);
	const page = parsePositiveInteger(event.url.searchParams.get('page'), 1);
	const pageSize = parsePositiveInteger(event.url.searchParams.get('pageSize'), 20);
	if (
		page === null ||
		pageSize === null ||
		pageSize > 100 ||
		!Number.isSafeInteger((page - 1) * pageSize)
	) {
		error(400, 'Invalid pagination parameters');
	}
	return listRequestedScans(db, user.id, page, pageSize);
};

export const actions: Actions = { addRequestedSdkScan };
