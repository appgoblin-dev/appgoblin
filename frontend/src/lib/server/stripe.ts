import Stripe from 'stripe';
import { db } from '$lib/server/auth/db';
import { error } from '@sveltejs/kit';

import {
	STRIPE_SECRET_KEY,
	STRIPE_PRICE_APP_DEV_ID,
	STRIPE_PRICE_B2B_SDK_ID,
	STRIPE_PRICE_B2B_APPADS_ID,
	STRIPE_PRICE_B2B_PREMIUM_ID,
	APPGOBLIN_ENDPOINT_URL
} from '$env/static/private';

export const stripe = new Stripe(STRIPE_SECRET_KEY, {
	apiVersion: '2026-01-28.clover'
});

export const STRIPE_PRICES = {
	app_dev: STRIPE_PRICE_APP_DEV_ID,
	b2b_sdk: STRIPE_PRICE_B2B_SDK_ID,
	b2b_appads: STRIPE_PRICE_B2B_APPADS_ID,
	b2b_premium: STRIPE_PRICE_B2B_PREMIUM_ID
} as const;

export type StripePriceKey = keyof typeof STRIPE_PRICES;

export async function createCheckoutSession(
	userId: number,
	email: string,
	priceKey: StripePriceKey
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
				email: email,
				metadata: {
					userId: userId.toString()
				}
			});
			stripeCustomerId = customer.id;
			await db.execute('UPDATE users SET provider_customer_id = $1 WHERE id = $2', [
				stripeCustomerId,
				userId
			]);
		}

		const priceId = STRIPE_PRICES[priceKey];

		if (!priceId) {
			throw error(400, 'Invalid Stripe price key');
		}

		const session = await stripe.checkout.sessions.create({
			customer: stripeCustomerId,
			billing_address_collection: 'auto',
			line_items: [
				{
					price: priceId,
					quantity: 1
				}
			],
			mode: 'subscription',
			success_url: `${APPGOBLIN_ENDPOINT_URL}/account?success=true`,
			cancel_url: `${APPGOBLIN_ENDPOINT_URL}/pricing?canceled=true`
		});

		return session.url;
	} catch (e) {
		console.error('Error creating checkout session:', e);
		throw error(500, 'Error creating checkout session');
	}
}

export async function createPortalSession(userId: number) {
	try {
		const user = await db.queryOne<{ provider_customer_id: string | null }>(
			'SELECT provider_customer_id FROM users WHERE id = $1',
			[userId]
		);

		if (!user?.provider_customer_id) {
			throw error(400, 'User does not have a Stripe customer ID');
		}

		const session = await stripe.billingPortal.sessions.create({
			customer: user.provider_customer_id,
			return_url: `${APPGOBLIN_ENDPOINT_URL}/account`
		});

		return session.url;
	} catch (e) {
		console.error('Error creating portal session:', e);
		throw error(500, 'Error creating portal session');
	}
}
