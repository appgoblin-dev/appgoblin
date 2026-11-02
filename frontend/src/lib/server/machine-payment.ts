import crypto from 'node:crypto';
import Stripe from 'stripe';
import { Mppx, Store } from 'mppx/server';
import { stripe as mppStripe } from 'mppx/stripe/server';
import {
	STRIPE_SECRET_KEY,
	STRIPE_PROFILE_ID,
	STRIPE_TEMPO_DEPOSIT_ADDRESS
} from '$app/env/private';

import { stripe } from './stripe.js';

const machinePayments =
	STRIPE_SECRET_KEY && STRIPE_PROFILE_ID
		? mppStripe.create({
				client: stripe as Stripe,
				networkId: STRIPE_PROFILE_ID,
				livemode: !STRIPE_SECRET_KEY.includes('_test_'),
				depositAddresses: STRIPE_TEMPO_DEPOSIT_ADDRESS
					? { tempo: STRIPE_TEMPO_DEPOSIT_ADDRESS }
					: undefined,
				store: Store.memory()
			})
		: null;

const mppx = machinePayments
	? Mppx.create({
			methods: machinePayments.defaultMethods(),
			secretKey: crypto
				.createHmac('sha256', STRIPE_SECRET_KEY)
				.update('mpp-challenge-signing')
				.digest('base64')
		})
	: null;

export function isMachinePaymentConfigured(): boolean {
	return mppx !== null;
}

export async function machineSearchPayment(
	request: Request,
	resolve: () => Promise<Response>
): Promise<Response | null> {
	if (mppx === null) return null;
	const result = await mppx.charge({
		amount: '0.50',
		description: 'AppGoblin search page',
		scope: new URL(request.url).pathname
	})(request);

	if (result.status === 402) return result.challenge;
	return result.withReceipt(await resolve());
}
