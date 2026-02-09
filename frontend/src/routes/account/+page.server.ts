import { fail, redirect } from '@sveltejs/kit';
import { deleteSessionTokenCookie, invalidateSession } from '$lib/server/auth/session';
import { requireFullAuth } from '$lib/server/auth/auth';
import { db } from '$lib/server/auth/db';
import { createPortalSession } from '$lib/server/stripe';

import type { Actions, PageServerLoadEvent, RequestEvent } from './$types';

export async function load(event: PageServerLoadEvent) {
	// This route requires full authentication (opt-in protection)
	const { user } = requireFullAuth(event);

	interface Subscription {
		status: string;
		current_period_end: Date;
		cancel_at: Date | null;
	}

	const subscription = await db.queryOne<Subscription>(
		`SELECT status, current_period_end, cancel_at 
         FROM subscriptions 
         WHERE user_id = $1 
         ORDER BY created_at DESC LIMIT 1`,
		[user.id]
	);

	return {
		user,
		subscription
	};
}

export const actions: Actions = {
	logout: async (event: RequestEvent) => {
		if (event.locals.session === null) {
			return fail(401, {
				message: 'Not authenticated'
			});
		}
		invalidateSession(event.locals.session.id);
		deleteSessionTokenCookie(event);
		return redirect(302, '/auth/login');
	},
	portal: async (event: RequestEvent) => {
		const { user } = requireFullAuth(event);
		let url;
		try {
			url = await createPortalSession(user.id);
		} catch (e) {
			console.error(e);
			return fail(500, { message: 'An error occurred' });
		}

		if (!url) {
			return fail(500, { message: 'Failed to create portal session' });
		}

		redirect(303, url);
	}
};
