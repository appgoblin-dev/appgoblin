import { redirect, fail } from '@sveltejs/kit';
import type { Actions, PageServerLoadEvent } from './$types';
import { createCheckoutSession, type StripePriceKey } from '$lib/server/stripe';
import { requireFullAuth, loginUrl } from '$lib/server/auth/auth';
import { db } from '$lib/server/auth/db';

export const load = async (event: PageServerLoadEvent) => {
	// Optional: Pass user data if needed for the page UI
	return {};
};

export const actions: Actions = {
	subscribe: async (event) => {
		const { user } = requireFullAuth(event);

		if (!user) {
			return redirect(302, loginUrl('/pricing'));
		}

		const formData = await event.request.formData();
		const priceKey = formData.get('priceKey');

		if (typeof priceKey !== 'string') {
			return fail(400, { message: 'Missing price selection' });
		}

		const allowedKeys: StripePriceKey[] = ['app_dev', 'b2b_sdk', 'b2b_appads', 'b2b_premium'];

		if (!allowedKeys.includes(priceKey as StripePriceKey)) {
			return fail(400, { message: 'Invalid price selection' });
		}

		const normalizedKey = priceKey as StripePriceKey;

		// Check for existing active subscription (allow checkout if previously canceled)
		const existingSubscription = await db.queryOne<{
			status: string;
			cancel_at: Date | null;
			cancel_requested_at: Date | null;
		}>(
			`SELECT status, cancel_at, cancel_requested_at
             FROM subscriptions
             WHERE user_id = $1
             AND status IN ('active', 'trialing')
             ORDER BY current_period_end DESC
             LIMIT 1`,
			[user.id]
		);

		if (
			existingSubscription &&
			!existingSubscription.cancel_at &&
			!existingSubscription.cancel_requested_at
		) {
			return redirect(303, '/account');
		}

		let url;
		try {
			url = await createCheckoutSession(user.id, user.email, normalizedKey);
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
