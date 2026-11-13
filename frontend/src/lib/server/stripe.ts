import Stripe from 'stripe';
import { db } from '#lib/server/auth/db.js';
import { error } from '@sveltejs/kit';

import {
	STRIPE_SECRET_KEY,
	APPGOBLIN_ENDPOINT_URL,
	STRIPE_PRICE_B2B_SDK_SEAT_MO,
	STRIPE_PRICE_B2B_SDK_SEAT_YR,
	STRIPE_PRICE_B2B_PREMIUM_SEAT_MO,
	STRIPE_PRICE_B2B_PREMIUM_SEAT_YR
} from '$app/env/private';

import { STRIPE_PLAN_LABELS, type BillingCycle, type StripePriceKey } from '#lib/plans.js';
export { STRIPE_PLAN_LABELS, type BillingCycle, type StripePriceKey } from '#lib/plans.js';

export const stripe = new Stripe(STRIPE_SECRET_KEY, {
	apiVersion: '2026-08-26.dahlia'
});

export async function createCheckoutSession(
	userId: number,
	email: string,
	priceKey: StripePriceKey,
	billingCycle: BillingCycle,
	origin: string
) {
	try {
		// Create or get customer
		let stripeCustomerId: string | null = null;

		const user = await db.queryOne<{ provider_customer_id: string | null }>(
			'SELECT provider_customer_id FROM users WHERE id = $1',
			[userId]
		);

		if (user?.provider_customer_id) {
			stripeCustomerId = user.provider_customer_id;
		} else {
			const customer = await stripe.customers.create({
				email,
				metadata: { userId: userId.toString() }
			});

			stripeCustomerId = customer.id;
			await db.execute('UPDATE users SET provider_customer_id = $1 WHERE id = $2', [
				stripeCustomerId,
				userId
			]);
		}

		// Look up the active Stripe price ID from the DB instead of hardcoded env vars.
		// This automatically picks up new prices and tolerates retired IDs
		// as long as they exist in tier_prices with is_current = TRUE.
		const priceRow = await db.queryOne<{ provider_price_id: string }>(
			`SELECT tp.provider_price_id
		 FROM public.tier_prices tp
		 JOIN public.tiers t ON t.id = tp.tier_id
		 WHERE t.slug = $1 AND tp.billing_cycle = $2
		   AND tp.provider_name = 'stripe' AND tp.is_current = TRUE`,
			[priceKey, billingCycle]
		);

		if (!priceRow) {
			error(400, 'No active Stripe price found for this plan');
		}
		const priceId = priceRow.provider_price_id;
		const seatPriceId =
			priceKey === 'b2b_sdk'
				? billingCycle === 'yearly'
					? STRIPE_PRICE_B2B_SDK_SEAT_YR
					: STRIPE_PRICE_B2B_SDK_SEAT_MO
				: priceKey === 'b2b_premium'
					? billingCycle === 'yearly'
						? STRIPE_PRICE_B2B_PREMIUM_SEAT_YR
						: STRIPE_PRICE_B2B_PREMIUM_SEAT_MO
					: null;

		const session = await stripe.checkout.sessions.create({
			customer: stripeCustomerId,
			billing_address_collection: 'auto',
			line_items: [{ price: priceId, quantity: 1 }],
			...(seatPriceId
				? {
						optional_items: [
							{
								price: seatPriceId,
								quantity: 1,
								adjustable_quantity: { enabled: true, minimum: 1, maximum: 100 }
							}
						]
					}
				: {}),
			mode: 'subscription',
			success_url: `${origin}/account?success=true`,
			cancel_url: `${origin}/pricing?canceled=true`
		});

		return session.url;
	} catch (e) {
		console.error('Error creating checkout session:', e);
		error(500, 'Error creating checkout session');
	}
}

export async function updateSubscriptionSeats(userId: number, totalSeats: number) {
	if (!Number.isInteger(totalSeats) || totalSeats < 1 || totalSeats > 110) {
		error(400, 'Total seats must be an integer between 1 and 110');
	}

	const subscription = await db.queryOne<{
		provider_subscription_id: string;
		organization_id: number;
		tier_slug: StripePriceKey;
		billing_cycle: BillingCycle;
	}>(
		`SELECT s.provider_subscription_id, t.slug AS tier_slug, tp.billing_cycle
		 FROM subscriptions s
		 JOIN tier_prices tp ON tp.id = s.tier_price_id
		 JOIN tiers t ON t.id = tp.tier_id
		 JOIN organization_members om ON om.organization_id = s.organization_id
		 WHERE om.user_id = $1
		   AND tp.provider_name = 'stripe'
		   AND s.status IN ('active', 'trialing')
		 ORDER BY s.updated_at DESC
		 LIMIT 1`,
		[userId]
	);

	if (
		!subscription ||
		(subscription.tier_slug !== 'b2b_sdk' && subscription.tier_slug !== 'b2b_premium')
	) {
		error(400, 'No eligible B2B subscription found');
	}

	const includedSeats = subscription.tier_slug === 'b2b_premium' ? 10 : 3;
	const additionalSeats = totalSeats - includedSeats;
	const seatPriceId =
		subscription.tier_slug === 'b2b_sdk'
			? subscription.billing_cycle === 'yearly'
				? STRIPE_PRICE_B2B_SDK_SEAT_YR
				: STRIPE_PRICE_B2B_SDK_SEAT_MO
			: subscription.billing_cycle === 'yearly'
				? STRIPE_PRICE_B2B_PREMIUM_SEAT_YR
				: STRIPE_PRICE_B2B_PREMIUM_SEAT_MO;
	const stripeSubscription = await stripe.subscriptions.retrieve(
		subscription.provider_subscription_id
	);
	const seatItem = stripeSubscription.items.data.find((item) => item.price.id === seatPriceId);

	if (additionalSeats <= 0) {
		if (seatItem) {
			await stripe.subscriptionItems.del(seatItem.id, { proration_behavior: 'create_prorations' });
		}
	} else if (seatItem) {
		await stripe.subscriptionItems.update(seatItem.id, {
			quantity: additionalSeats,
			proration_behavior: 'create_prorations'
		});
	} else {
		await stripe.subscriptionItems.create({
			subscription: subscription.provider_subscription_id,
			price: seatPriceId,
			quantity: additionalSeats,
			proration_behavior: 'create_prorations'
		});
	}
}

export async function createPortalSession(userId: number) {
	try {
		const user = await db.queryOne<{ provider_customer_id: string | null }>(
			'SELECT provider_customer_id FROM users WHERE id = $1',
			[userId]
		);

		if (!user?.provider_customer_id) {
			error(400, 'User does not have a Stripe customer ID');
		}

		const session = await stripe.billingPortal.sessions.create({
			customer: user.provider_customer_id,
			return_url: `${APPGOBLIN_ENDPOINT_URL}/account`
		});

		return session.url;
	} catch (e) {
		console.error('Error creating portal session:', e);
		error(500, 'Error creating portal session');
	}
}
