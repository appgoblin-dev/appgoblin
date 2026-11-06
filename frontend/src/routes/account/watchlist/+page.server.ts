import { fail } from '@sveltejs/kit';
import { requireAuthOr401 } from '#lib/server/auth/auth.js';
import { db } from '#lib/server/auth/db.js';
import { addRequestedSdkScan } from '#lib/server/requested-scans/action.js';

import type { Actions, PageServerLoadEvent, RequestEvent } from './$types';

export async function load(event: PageServerLoadEvent) {
	// user is provided by +layout.server.ts
	const { user } = await event.parent();
	interface FollowedApp {
		id: number;
		store_id: string;
		created_at: Date;
		app_name: null;
	}

	interface FollowedAppRow {
		id: number;
		store_id: string;
		created_at: Date;
	}

	interface FollowedCompany {
		id: number;
		company_id: number;
		created_at: Date;
		company_name: string | null;
		company_domain: string | null;
	}

	interface TrackedKeyword {
		id: number;
		store_id: string;
		keyword_text: string;
		created_at: Date;
		app_name: null;
	}

	interface TrackedKeywordRow {
		id: number;
		store_id: string;
		keyword_text: string;
		created_at: Date;
	}

	const [followedAppRows, followedCompanies, trackedKeywordRows] = await Promise.all([
		db.query<FollowedAppRow>(
			`SELECT
				ufa.id,
				ufa.store_id,
				ufa.created_at
			FROM public.user_followed_apps AS ufa
			WHERE ufa.user_id = $1
			ORDER BY ufa.created_at DESC
			LIMIT 100`,
			[user.id]
		),
		db.query<FollowedCompany>(
			`SELECT
				ufc.id,
				ufc.company_id,
				ufc.created_at,
				NULL ::text AS company_name,
				NULL ::text AS company_domain
			FROM public.user_followed_companies AS ufc
			WHERE ufc.user_id = $1
			ORDER BY ufc.created_at DESC
			LIMIT 100`,
			[user.id]
		),
		db.query<TrackedKeywordRow>(
			`SELECT
				utk.id,
				utk.store_id,
				utk.keyword_text,
				utk.created_at
			FROM public.user_tracked_keywords AS utk
			WHERE utk.user_id = $1
			ORDER BY utk.created_at DESC
			LIMIT 200`,
			[user.id]
		)
	]);

	const followedApps: FollowedApp[] = followedAppRows.map((app) => ({ ...app, app_name: null }));
	const trackedKeywords: TrackedKeyword[] = trackedKeywordRows.map((keyword) => ({
		...keyword,
		app_name: null
	}));
	return {
		followedApps,
		followedCompanies,
		trackedKeywords
	};
}

function getRequiredString(data: FormData, key: string): string {
	const value = data.get(key)?.toString().trim() ?? '';
	if (!value) throw new Error(`${key} is required`);
	return value;
}

function isUniqueViolation(error: unknown): boolean {
	return typeof error === 'object' && error !== null && 'code' in error && error.code === '23505';
}

export const actions: Actions = {
	addFollowedApp: async (event: RequestEvent) => {
		const { user } = requireAuthOr401(event);
		const data = await event.request.formData();

		let storeId = '';
		try {
			storeId = getRequiredString(data, 'store_id');
		} catch {
			return fail(400, { section: 'tracked-apps', message: 'App store ID is required' });
		}

		const result = await db.execute(
			`INSERT INTO public.user_followed_apps (user_id, store_id)
			 VALUES ($1, $2)
			 ON CONFLICT (user_id, store_id) DO NOTHING`,
			[user.id, storeId]
		);

		if (result.changes === 0) {
			return { section: 'tracked-apps', success: true, message: 'Already following this app' };
		}

		return { section: 'tracked-apps', success: true, message: 'App added to quick access' };
	},
	updateFollowedApp: async (event: RequestEvent) => {
		const { user } = requireAuthOr401(event);
		const data = await event.request.formData();
		const idRaw = data.get('id')?.toString() ?? '';
		const id = Number.parseInt(idRaw, 10);

		if (!Number.isInteger(id) || id <= 0) {
			return fail(400, { section: 'tracked-apps', message: 'Invalid app follow record ID' });
		}

		let storeId = '';
		try {
			storeId = getRequiredString(data, 'store_id');
		} catch {
			return fail(400, { section: 'tracked-apps', message: 'App store ID is required' });
		}

		try {
			const result = await db.execute(
				`UPDATE public.user_followed_apps
				 SET store_id = $1
				 WHERE id = $2 AND user_id = $3`,
				[storeId, id, user.id]
			);

			if (result.changes === 0) {
				return fail(404, { section: 'tracked-apps', message: 'Tracked app was not found' });
			}
		} catch (error) {
			if (isUniqueViolation(error)) {
				return fail(409, { section: 'tracked-apps', message: 'You already follow this app' });
			}

			throw error;
		}

		return { section: 'tracked-apps', success: true, message: 'Tracked app updated' };
	},
	deleteFollowedApp: async (event: RequestEvent) => {
		const { user } = requireAuthOr401(event);
		const data = await event.request.formData();
		const idRaw = data.get('id')?.toString() ?? '';
		const id = Number.parseInt(idRaw, 10);

		if (!Number.isInteger(id) || id <= 0) {
			return fail(400, { section: 'tracked-apps', message: 'Invalid app follow record ID' });
		}

		const result = await db.execute(
			'DELETE FROM public.user_followed_apps WHERE id = $1 AND user_id = $2',
			[id, user.id]
		);

		if (result.changes === 0) {
			return fail(404, { section: 'tracked-apps', message: 'Tracked app was not found' });
		}

		return { section: 'tracked-apps', success: true, message: 'Tracked app removed' };
	},
	addFollowedCompany: async (event: RequestEvent) => {
		const { user } = requireAuthOr401(event);
		const data = await event.request.formData();
		const companyIdRaw = data.get('company_id')?.toString() ?? '';
		const companyId = Number.parseInt(companyIdRaw, 10);

		if (!Number.isInteger(companyId) || companyId <= 0) {
			return fail(400, {
				section: 'tracked-companies',
				message: 'Company ID must be a positive integer'
			});
		}

		const result = await db.execute(
			`INSERT INTO public.user_followed_companies (user_id, company_id)
			 VALUES ($1, $2)
			 ON CONFLICT (user_id, company_id) DO NOTHING`,
			[user.id, companyId]
		);

		if (result.changes === 0) {
			return {
				section: 'tracked-companies',
				success: true,
				message: 'Already following this company'
			};
		}

		return {
			section: 'tracked-companies',
			success: true,
			message: 'Company added to quick access'
		};
	},
	updateFollowedCompany: async (event: RequestEvent) => {
		const { user } = requireAuthOr401(event);
		const data = await event.request.formData();
		const idRaw = data.get('id')?.toString() ?? '';
		const id = Number.parseInt(idRaw, 10);
		const companyIdRaw = data.get('company_id')?.toString() ?? '';
		const companyId = Number.parseInt(companyIdRaw, 10);

		if (!Number.isInteger(id) || id <= 0) {
			return fail(400, {
				section: 'tracked-companies',
				message: 'Invalid company follow record ID'
			});
		}

		if (!Number.isInteger(companyId) || companyId <= 0) {
			return fail(400, {
				section: 'tracked-companies',
				message: 'Company ID must be a positive integer'
			});
		}

		try {
			const result = await db.execute(
				`UPDATE public.user_followed_companies
				 SET company_id = $1
				 WHERE id = $2 AND user_id = $3`,
				[companyId, id, user.id]
			);

			if (result.changes === 0) {
				return fail(404, {
					section: 'tracked-companies',
					message: 'Tracked company was not found'
				});
			}
		} catch (error) {
			if (isUniqueViolation(error)) {
				return fail(409, {
					section: 'tracked-companies',
					message: 'You already follow this company'
				});
			}

			throw error;
		}

		return { section: 'tracked-companies', success: true, message: 'Tracked company updated' };
	},
	deleteFollowedCompany: async (event: RequestEvent) => {
		const { user } = requireAuthOr401(event);
		const data = await event.request.formData();
		const idRaw = data.get('id')?.toString() ?? '';
		const id = Number.parseInt(idRaw, 10);

		if (!Number.isInteger(id) || id <= 0) {
			return fail(400, {
				section: 'tracked-companies',
				message: 'Invalid company follow record ID'
			});
		}

		const result = await db.execute(
			'DELETE FROM public.user_followed_companies WHERE id = $1 AND user_id = $2',
			[id, user.id]
		);

		if (result.changes === 0) {
			return fail(404, { section: 'tracked-companies', message: 'Tracked company was not found' });
		}

		return { section: 'tracked-companies', success: true, message: 'Tracked company removed' };
	},
	addTrackedKeyword: async (event: RequestEvent) => {
		const { user } = requireAuthOr401(event);
		const data = await event.request.formData();

		let storeId = '';
		let keywordText = '';
		try {
			storeId = getRequiredString(data, 'store_id');
			keywordText = getRequiredString(data, 'keyword_text');
		} catch {
			return fail(400, {
				section: 'tracked-keywords',
				message: 'Store ID and keyword are required'
			});
		}

		const result = await db.execute(
			`INSERT INTO public.user_tracked_keywords (user_id, store_id, keyword_text)
			 VALUES ($1, $2, $3)
			 ON CONFLICT DO NOTHING`,
			[user.id, storeId, keywordText]
		);

		if (result.changes === 0) {
			return {
				section: 'tracked-keywords',
				success: true,
				message: 'Already tracking this keyword'
			};
		}

		return {
			section: 'tracked-keywords',
			success: true,
			message: 'Keyword added to tracking list'
		};
	},
	updateTrackedKeyword: async (event: RequestEvent) => {
		const { user } = requireAuthOr401(event);
		const data = await event.request.formData();
		const idRaw = data.get('id')?.toString() ?? '';
		const id = Number.parseInt(idRaw, 10);

		if (!Number.isInteger(id) || id <= 0) {
			return fail(400, {
				section: 'tracked-keywords',
				message: 'Invalid tracked keyword record ID'
			});
		}

		let storeId = '';
		let keywordText = '';
		try {
			storeId = getRequiredString(data, 'store_id');
			keywordText = getRequiredString(data, 'keyword_text');
		} catch {
			return fail(400, {
				section: 'tracked-keywords',
				message: 'Store ID and keyword are required'
			});
		}

		try {
			const result = await db.execute(
				`UPDATE public.user_tracked_keywords
				 SET store_id = $1, keyword_text = $2
				 WHERE id = $3 AND user_id = $4`,
				[storeId, keywordText, id, user.id]
			);

			if (result.changes === 0) {
				return fail(404, {
					section: 'tracked-keywords',
					message: 'Tracked keyword was not found'
				});
			}
		} catch (error) {
			if (isUniqueViolation(error)) {
				return fail(409, {
					section: 'tracked-keywords',
					message: 'You already track this keyword for that app'
				});
			}

			throw error;
		}

		return { section: 'tracked-keywords', success: true, message: 'Tracked keyword updated' };
	},
	deleteTrackedKeyword: async (event: RequestEvent) => {
		const { user } = requireAuthOr401(event);
		const data = await event.request.formData();
		const idRaw = data.get('id')?.toString() ?? '';
		const id = Number.parseInt(idRaw, 10);

		if (!Number.isInteger(id) || id <= 0) {
			return fail(400, {
				section: 'tracked-keywords',
				message: 'Invalid tracked keyword record ID'
			});
		}

		const result = await db.execute(
			'DELETE FROM public.user_tracked_keywords WHERE id = $1 AND user_id = $2',
			[id, user.id]
		);

		if (result.changes === 0) {
			return fail(404, { section: 'tracked-keywords', message: 'Tracked keyword was not found' });
		}

		return { section: 'tracked-keywords', success: true, message: 'Tracked keyword removed' };
	},
	addRequestedSdkScan
};
