import { redirect, fail } from '@sveltejs/kit';
import type { Actions, PageServerLoadEvent } from './$types';
import {
	createCheckoutSession,
	STRIPE_PLAN_LABELS,
	type StripePriceKey,
	type BillingCycle
} from '#lib/server/stripe.js';
import { requireFullAuth } from '#lib/server/auth/auth.js';
import { db } from '#lib/server/auth/db.js';
import { sendPricingPlanSelectionEmail } from '#lib/server/contact.js';

const allowedKeys: StripePriceKey[] = ['b2b_sdk', 'b2b_appads', 'b2b_premium'];
const allowedCycles: BillingCycle[] = ['monthly', 'yearly'];

function parseBillingCycle(value: FormDataEntryValue | string | null): BillingCycle {
	return value === 'yearly' ? 'yearly' : 'monthly';
}

/** Resolve the user's current plan slug, cycle, and display fields from the DB. */
async function getCurrentPlan(userId: number) {
	const row = await db.queryOne<{
		slug: string | null;
		billing_cycle: string | null;
		status: string;
		current_period_end: Date | null;
		cancel_at: Date | null;
	}>(
		`SELECT t.slug, tp.billing_cycle, s.status,
		        s.current_period_end, s.cancel_at
		 FROM subscriptions s
		 LEFT JOIN tier_prices tp ON tp.id = s.tier_price_id
		 LEFT JOIN tiers t ON t.id = tp.tier_id
		 JOIN organization_members om ON om.organization_id = s.organization_id
		 WHERE om.user_id = $1
		   AND tp.provider_name = 'stripe'
		   AND (
		     (s.cancel_at IS NOT NULL AND s.cancel_at > NOW())
		     OR (s.cancel_at IS NULL AND s.status IN ('active', 'trialing'))
		   )
		 ORDER BY s.updated_at DESC
		 LIMIT 1`,
		[userId]
	);
	return row ?? null;
}

export async function load(event: PageServerLoadEvent) {
	// Check if user arrived here with a subscribe intent (after auth chain)
	const subscribe = event.url.searchParams.get('subscribe');
	const billingCycle = parseBillingCycle(event.url.searchParams.get('cycle'));
	if (subscribe && allowedKeys.includes(subscribe as StripePriceKey)) {
		// Not signed in — bounce through login (or email verification) preserving
		// the subscribe intent in the URL, matching the form-action path.
		if (event.locals.session === null || event.locals.user === null) {
			return redirect(
				302,
				`/auth/pricing-signup?redirectTo=${encodeURIComponent('/pricing?subscribe=' + encodeURIComponent(subscribe) + '&cycle=' + encodeURIComponent(billingCycle))}`
			);
		}
		if (!event.locals.user.emailVerified) {
			return redirect(
				302,
				`/auth/verify-email?redirectTo=${encodeURIComponent('/pricing?subscribe=' + encodeURIComponent(subscribe) + '&cycle=' + encodeURIComponent(billingCycle))}`
			);
		}

		// User is fully authenticated — check if they already have this exact plan+cycle
		const existingPlan = await getCurrentPlan(event.locals.user.id);
		if (
			existingPlan &&
			existingPlan.slug === subscribe &&
			existingPlan.billing_cycle === billingCycle
		) {
			return redirect(303, '/account/subscription');
		}

		// Proceed to checkout
		let url;
		try {
			url = await createCheckoutSession(
				event.locals.user.id,
				event.locals.user.email,
				subscribe as StripePriceKey,
				billingCycle
			);
		} catch (e) {
			console.error(e);
		}
		if (url) {
			return redirect(303, url, { external: true });
		}
	}

	// Resolve the signed-in user's current plan so we can surface it on the page.
	const currentPlan = event.locals.user ? await getCurrentPlan(event.locals.user.id) : null;
	const currentSubscription = currentPlan
		? {
				status: currentPlan.status,
				provider_name: 'stripe' as const,
				current_period_end: currentPlan.current_period_end,
				cancel_at: currentPlan.cancel_at
			}
		: null;

	const currentPlanLabel = currentPlan?.slug
		? (STRIPE_PLAN_LABELS[currentPlan.slug as StripePriceKey] ?? null)
		: null;
	const currentPlanKey = currentPlan?.slug?.startsWith('b2b_')
		? (currentPlan.slug as StripePriceKey)
		: null;
	const currentPlanCycle = currentPlan?.billing_cycle as BillingCycle | null;

	return {
		user: event.locals.user,
		currentSubscription,
		currentPlanKey,
		currentPlanLabel,
		currentPlanCycle
	};
}

export const actions: Actions = {
	subscribe: async (event) => {
		// Check auth early so we can encode the priceKey + cycle in the redirect
		if (event.locals.session === null || event.locals.user === null) {
			const formData = await event.request.formData();
			const priceKey = formData.get('priceKey');
			const cycle = parseBillingCycle(formData.get('billingCycle'));
			if (typeof priceKey === 'string' && allowedKeys.includes(priceKey as StripePriceKey)) {
				void sendPricingPlanSelectionEmail(
					priceKey as StripePriceKey,
					cycle,
					event.locals.user
				).catch((error) => {
					console.error('Failed to send pricing plan selection notification:', error);
				});
				return redirect(
					302,
					`/auth/pricing-signup?redirectTo=${encodeURIComponent('/pricing?subscribe=' + encodeURIComponent(priceKey) + '&cycle=' + encodeURIComponent(cycle))}`
				);
			}
			return redirect(302, '/auth/pricing-signup?redirectTo=' + encodeURIComponent('/pricing'));
		}
		if (!event.locals.user.emailVerified) {
			const formData = await event.request.formData();
			const priceKey = formData.get('priceKey');
			const cycle = parseBillingCycle(formData.get('billingCycle'));
			if (typeof priceKey === 'string' && allowedKeys.includes(priceKey as StripePriceKey)) {
				void sendPricingPlanSelectionEmail(
					priceKey as StripePriceKey,
					cycle,
					event.locals.user
				).catch((error) => {
					console.error('Failed to send pricing plan selection notification:', error);
				});
				return redirect(
					302,
					`/auth/verify-email?redirectTo=${encodeURIComponent('/pricing?subscribe=' + encodeURIComponent(priceKey) + '&cycle=' + encodeURIComponent(cycle))}`
				);
			}
			return redirect(302, '/auth/verify-email');
		}

		const { user } = requireFullAuth(event);

		const formData = await event.request.formData();
		const priceKey = formData.get('priceKey');
		const billingCycle = parseBillingCycle(formData.get('billingCycle'));

		if (typeof priceKey !== 'string') {
			return fail(400, { message: 'Missing price selection' });
		}

		if (!allowedKeys.includes(priceKey as StripePriceKey)) {
			return fail(400, { message: 'Invalid price selection' });
		}

		if (!allowedCycles.includes(billingCycle)) {
			return fail(400, { message: 'Invalid billing cycle' });
		}

		const normalizedKey = priceKey as StripePriceKey;
		void sendPricingPlanSelectionEmail(normalizedKey, billingCycle, user).catch((error) => {
			console.error('Failed to send pricing plan selection notification:', error);
		});

		// Check existing — short-circuit if already on this exact plan+cycle
		const existingPlan = await getCurrentPlan(user.id);
		if (
			existingPlan &&
			existingPlan.slug === normalizedKey &&
			existingPlan.billing_cycle === billingCycle
		) {
			return redirect(303, '/account/subscription');
		}

		let url;
		try {
			url = await createCheckoutSession(user.id, user.email, normalizedKey, billingCycle);
		} catch (e) {
			console.error(e);
			return fail(500, { message: 'An error occurred' });
		}

		if (!url) {
			return fail(500, { message: 'Failed to create checkout session' });
		}

		redirect(303, url, { external: true });
	}
};
