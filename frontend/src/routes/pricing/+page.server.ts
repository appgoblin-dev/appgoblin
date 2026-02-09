import { redirect, fail } from '@sveltejs/kit';
import type { Actions, PageServerLoadEvent } from './$types';
import { createCheckoutSession } from '$lib/server/stripe';
import { requireFullAuth } from '$lib/server/auth/auth';
import { db } from '$lib/server/auth/db';

export const load = async (event: PageServerLoadEvent) => {
	// Optional: Pass user data if needed for the page UI
	return {};
};

export const actions: Actions = {
	subscribe: async (event) => {
		const { user } = requireFullAuth(event);

		if (!user) {
			return redirect(302, '/auth/login?redirectTo=/pricing');
		}

		// Check for existing active subscription
		const existingSubscription = await db.queryOne(
			`SELECT id FROM subscriptions 
             WHERE user_id = $1 
             AND status IN ('active', 'trialing') 
             LIMIT 1`,
			[user.id]
		);

		if (existingSubscription) {
			return redirect(303, '/account');
		}

		let url;
		try {
			url = await createCheckoutSession(user.id, user.email);
		} catch (e) {
			console.error(e);
			return fail(500, { message: 'An error occurred' });
		}

		if (!url) {
			return fail(500, { message: 'Failed to create checkout session' });
		}

		redirect(303, url);
	}
};
