import Stripe from 'stripe';
import { db } from '$lib/server/auth/db';
import { error } from '@sveltejs/kit';

import { STRIPE_SECRET_KEY, STRIPE_B2B_ID } from '$env/static/private';

console.log('Stripe secret key:', STRIPE_SECRET_KEY);

export const stripe = new Stripe(STRIPE_SECRET_KEY, {
	apiVersion: '2026-01-28.clover'
});

export async function createCheckoutSession(userId: number, email: string) {
	try {
		// Create or get customer
		let stripeCustomerId: string | null = null;

		const user = await db.queryOne<{ stripe_customer_id: string | null }>(
			'SELECT stripe_customer_id FROM users WHERE id = $1',
			[userId]
		);

		if (user?.stripe_customer_id) {
			stripeCustomerId = user.stripe_customer_id;
		} else {
			const customer = await stripe.customers.create({
				email: email,
				metadata: {
					userId: userId.toString()
				}
			});
			stripeCustomerId = customer.id;
			await db.execute('UPDATE users SET stripe_customer_id = $1 WHERE id = $2', [
				stripeCustomerId,
				userId
			]);
		}

		const session = await stripe.checkout.sessions.create({
			customer: stripeCustomerId,
			billing_address_collection: 'auto',
			line_items: [
				{
					price: STRIPE_B2B_ID,
					quantity: 1
				}
			],
			mode: 'subscription',
			success_url: `http://localhost:5173/account?success=true`, // TODO check base URL
			cancel_url: `http://localhost:5173/pricing?canceled=true`
		});

		return session.url;
	} catch (e) {
		console.error('Error creating checkout session:', e);
		throw error(500, 'Error creating checkout session');
	}
}

export async function createPortalSession(userId: number) {
	try {
		const user = await db.queryOne<{ stripe_customer_id: string | null }>(
			'SELECT stripe_customer_id FROM users WHERE id = $1',
			[userId]
		);

		if (!user?.stripe_customer_id) {
			throw error(400, 'User does not have a Stripe customer ID');
		}

		const session = await stripe.billingPortal.sessions.create({
			customer: user.stripe_customer_id,
			return_url: `http://localhost:5173/account`
		});

		return session.url;
	} catch (e) {
		console.error('Error creating portal session:', e);
		throw error(500, 'Error creating portal session');
	}
}
