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

interface MachinePageOffer {
	amount: string;
	description: string;
}

/**
 * Pages that sit behind the free account login but hold no account-scoped
 * data, so a machine client can buy a single view.
 *
 * Account pages, `/keywords/tracked`, subscription-only pages, and actions
 * that depend on a signed-in user are deliberately absent.
 */
const PAGE_OFFERS: Array<{ pattern: RegExp; offer: MachinePageOffer }> = [
	{
		pattern: /^\/apps\/[^/]+\/keywords\/?$/,
		offer: { amount: '0.50', description: 'AppGoblin app keywords page' }
	},
	{
		pattern: /^\/apps\/[^/]+\/keywords\/discovery\/?$/,
		offer: { amount: '0.50', description: 'AppGoblin app keyword discovery page' }
	},
	{
		pattern: /^\/apps\/[^/]+\/keywords\/ranking\/?$/,
		offer: { amount: '0.50', description: 'AppGoblin app keyword ranking page' }
	},
	{
		pattern: /^\/apps\/[^/]+\/keywords\/compare\/?$/,
		offer: { amount: '0.50', description: 'AppGoblin app keyword compare page' }
	},
	{
		pattern: /^\/apps\/[^/]+\/sdks\/?$/,
		offer: { amount: '0.50', description: 'AppGoblin app SDK page' }
	},
	{
		pattern: /^\/apps\/[^/]+\/sdks\/permissions\/?$/,
		offer: { amount: '0.50', description: 'AppGoblin app permissions page' }
	},
	{
		pattern: /^\/apps\/[^/]+\/sdks\/queries\/?$/,
		offer: { amount: '0.50', description: 'AppGoblin app queries page' }
	},
	{
		pattern: /^\/apps\/[^/]+\/sdks\/skadnetwork\/?$/,
		offer: { amount: '0.50', description: 'AppGoblin app SKAdNetwork page' }
	},
	{
		pattern: /^\/apps\/[^/]+\/sdks\/unknowns\/?$/,
		offer: { amount: '0.50', description: 'AppGoblin app unmapped SDK page' }
	},
	{
		pattern: /^\/apps\/comparison\/[^/]+\/?$/,
		offer: { amount: '0.50', description: 'AppGoblin app comparison page' }
	},
	{
		pattern: /^\/apps\/comparison\/[^/]+\/[^/]+\/?$/,
		offer: { amount: '0.50', description: 'AppGoblin app comparison page' }
	},
	{
		pattern: /^\/sdks\/[^/]+\/?$/,
		offer: { amount: '0.50', description: 'AppGoblin SDK pattern page' }
	},
	{
		pattern: /^\/sdks\/mapped\/[^/]+\/?$/,
		offer: { amount: '0.50', description: 'AppGoblin SDK details page' }
	},
	{
		pattern: /^\/developers\/[^/]+\/sdks\/?$/,
		offer: { amount: '0.50', description: 'AppGoblin developer SDK page' }
	},
	{
		pattern: /^\/reports\/app-ecosystem-report-Q2-2026\/download\/?$/,
		offer: { amount: '0.50', description: 'AppGoblin app ecosystem report download' }
	}
];

/** Strips SvelteKit's `__data.json` suffix so data requests match the page path. */
function pagePath(pathname: string): string {
	return pathname.replace(/\/__data\.json$/, '');
}

/** Whether `pathname` is a page an agent can buy without an account. */
export function isMachinePayablePath(pathname: string): boolean {
	const path = pagePath(pathname);
	return PAGE_OFFERS.some(({ pattern }) => pattern.test(path));
}

function findPageOffer(pathname: string): MachinePageOffer | null {
	const path = pagePath(pathname);
	return PAGE_OFFERS.find(({ pattern }) => pattern.test(path))?.offer ?? null;
}

export function isMachinePaymentConfigured(): boolean {
	return mppx !== null;
}

async function chargePage(
	request: Request,
	resolve: () => Promise<Response>,
	offer: MachinePageOffer,
	scope: string
): Promise<Response | null> {
	if (mppx === null) return null;
	const result = await mppx.charge({
		amount: offer.amount,
		description: offer.description,
		scope
	})(request);

	if (result.status === 402) return result.challenge;
	return result.withReceipt(await resolve());
}

export async function machineSearchPayment(
	request: Request,
	resolve: () => Promise<Response>
): Promise<Response | null> {
	return chargePage(
		request,
		resolve,
		{ amount: '0.50', description: 'AppGoblin search page' },
		new URL(request.url).pathname
	);
}

/**
 * Charge a signed-out machine client for one page instead of sending it to the
 * login screen. Returns `null` when the request is not for a payable page.
 */
export async function machinePagePayment(
	request: Request,
	resolve: () => Promise<Response>
): Promise<Response | null> {
	if (request.method !== 'GET' && request.method !== 'HEAD') return null;
	const pathname = new URL(request.url).pathname;
	const offer = findPageOffer(pathname);
	if (offer === null) return null;
	return chargePage(request, resolve, offer, pathname);
}
