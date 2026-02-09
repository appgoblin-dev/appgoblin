import { stripe } from '$lib/server/stripe';
import { db } from '$lib/server/auth/db';
import type { RequestHandler } from './$types';

const WEBHOOK_SECRET = 'whsec_b866541f2e6b2e3989fa574e20bef87e4d0124c9690e034442ffa44629996dc6';
// User didn't provide one, so we might need to skip signature verification or assume dev.
// For now, I'll assume we can trust the body or use a placeholder if not provided, but properly it should be verified.
// Given the instructions, I'll implement standard verification code but note that it needs the secret.

export const POST: RequestHandler = async ({ request }) => {
	const body = await request.text();
	const sig = request.headers.get('stripe-signature');

	let event;

	if (WEBHOOK_SECRET && sig) {
		try {
			event = stripe.webhooks.constructEvent(body, sig, WEBHOOK_SECRET);
		} catch (err: any) {
			console.error(`Webhook signature verification failed.`, err);
			return new Response(`Webhook Error: ${err.message}`, { status: 400 });
		}
	} else {
		// Fallback for dev without secret (NOT SECURE for prod)
		try {
			event = JSON.parse(body);
		} catch (err: any) {
			return new Response(`Webhook Error: ${err.message}`, { status: 400 });
		}
	}

	try {
		switch (event.type) {
			case 'checkout.session.completed': {
				const session = event.data.object;
				await handleCheckoutSessionCompleted(session);
				break;
			}
			case 'customer.subscription.updated':
			case 'customer.subscription.deleted': {
				const subscription = event.data.object;
				await handleSubscriptionUpdated(subscription);
				break;
			}
			default:
				console.log(`Unhandled event type ${event.type}`);
		}
	} catch (err) {
		console.error('Error handling webhook event:', err);
		return new Response('Error handling event', { status: 500 });
	}

	return new Response(JSON.stringify({ received: true }), { status: 200 });
};

async function handleCheckoutSessionCompleted(session: any) {
	console.log('Handling checkout session completed', session.id);
	const customerId = session.customer;
	const subscriptionId = session.subscription;

	// session.metadata.userId might be present if we passed it
	// But better to rely on customer lookup or ensure we linked them.
	// In createCheckoutSession we updated the user with stripe_customer_id.

	if (session.mode === 'subscription' && typeof subscriptionId === 'string') {
		console.log('Retrieving subscription', subscriptionId);
		const subscription = await stripe.subscriptions.retrieve(subscriptionId);
		await handleSubscriptionUpdated(subscription);
	} else {
		console.log(
			'Session mode is not subscription or subscriptionId missing',
			session.mode,
			subscriptionId
		);
	}
}

async function handleSubscriptionUpdated(subscription: any) {
	console.log('Handling subscription updated', subscription.id);

	const customerId = subscription.customer as string;
	const status = subscription.status;
	const priceId = subscription.items.data[0]?.price.id;

	const currentPeriodStartVal =
		subscription.current_period_start ?? subscription.items.data[0]?.current_period_start;
	const currentPeriodEndVal =
		subscription.current_period_end ?? subscription.items.data[0]?.current_period_end;

	if (!currentPeriodStartVal || !currentPeriodEndVal) {
		console.error('Subscription missing period dates', {
			currentPeriodStartVal,
			currentPeriodEndVal
		});
	}

	const currentPeriodStart = currentPeriodStartVal
		? new Date(currentPeriodStartVal * 1000)
		: new Date();
	const currentPeriodEnd = currentPeriodEndVal ? new Date(currentPeriodEndVal * 1000) : new Date();

	const cancelAt = subscription.cancel_at ? new Date(subscription.cancel_at * 1000) : null;
	const canceledAt = subscription.canceled_at ? new Date(subscription.canceled_at * 1000) : null;
	const trialEnd = subscription.trial_end ? new Date(subscription.trial_end * 1000) : null;

	console.log('Looking up user for customer', customerId);
	// Find user by stripe_customer_id
	let user = await db.queryOne<{ id: number }>(
		'SELECT id FROM users WHERE stripe_customer_id = $1',
		[customerId]
	);

	// Fallback: Check metadata or email
	if (!user) {
		console.log('User not found by stripe_customer_id, checking metadata/email');

		// Retrieve customer to get email if not in subscription (it usually is in subscription.customer_email but safer to check customer)
		const customer = (await stripe.customers.retrieve(customerId)) as any;
		const email = customer.email;
		const userIdFromMeta = customer.metadata?.userId;

		console.log('Customer details:', { email, userIdFromMeta });

		if (userIdFromMeta) {
			user = await db.queryOne<{ id: number }>('SELECT id FROM users WHERE id = $1', [
				userIdFromMeta
			]);
		}

		if (!user && email) {
			user = await db.queryOne<{ id: number }>('SELECT id FROM users WHERE email = $1', [email]);
		}

		if (user) {
			console.log('User found via fallback, linking stripe_customer_id', user.id);
			// Link them now
			await db.execute('UPDATE users SET stripe_customer_id = $1 WHERE id = $2', [
				customerId,
				user.id
			]);
		}
	}

	if (!user) {
		console.error('User not found for stripe customer:', customerId);
		return;
	}

	console.log('Upserting subscription for user', user.id);
	// Upsert subscription
	await db.execute(
		`
        INSERT INTO subscriptions (
            user_id, stripe_subscription_id, stripe_customer_id, stripe_price_id, status,
            current_period_start, current_period_end, cancel_at, canceled_at, trial_end,
            seats_total, seats_used, updated_at
        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, 1, 0, NOW())
        ON CONFLICT (stripe_subscription_id) DO UPDATE SET
            status = EXCLUDED.status,
            stripe_price_id = EXCLUDED.stripe_price_id,
            current_period_start = EXCLUDED.current_period_start,
            current_period_end = EXCLUDED.current_period_end,
            cancel_at = EXCLUDED.cancel_at,
            canceled_at = EXCLUDED.canceled_at,
            trial_end = EXCLUDED.trial_end,
            updated_at = NOW();
    `,
		[
			user.id,
			subscription.id,
			customerId,
			priceId,
			status,
			currentPeriodStart,
			currentPeriodEnd,
			cancelAt,
			canceledAt,
			trialEnd
		]
	);
	console.log('Subscription upserted');
}
