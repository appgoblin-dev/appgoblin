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
	resource: string;
}

const DEFAULT_MACHINE_PAYMENT_AMOUNT = '0.10';

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
		offer: {
			amount: DEFAULT_MACHINE_PAYMENT_AMOUNT,
			description: 'AppGoblin app keywords page',
			resource: '/apps/{id}/keywords'
		}
	},
	{
		pattern: /^\/apps\/[^/]+\/keywords\/discovery\/?$/,
		offer: {
			amount: DEFAULT_MACHINE_PAYMENT_AMOUNT,
			description: 'AppGoblin app keyword discovery page',
			resource: '/apps/{id}/keywords/discovery'
		}
	},
	{
		pattern: /^\/apps\/[^/]+\/keywords\/ranking\/?$/,
		offer: {
			amount: DEFAULT_MACHINE_PAYMENT_AMOUNT,
			description: 'AppGoblin app keyword ranking page',
			resource: '/apps/{id}/keywords/ranking'
		}
	},
	{
		pattern: /^\/apps\/[^/]+\/keywords\/compare\/?$/,
		offer: {
			amount: DEFAULT_MACHINE_PAYMENT_AMOUNT,
			description: 'AppGoblin app keyword compare page',
			resource: '/apps/{id}/keywords/compare'
		}
	},
	{
		pattern: /^\/apps\/[^/]+\/sdks\/?$/,
		offer: {
			amount: DEFAULT_MACHINE_PAYMENT_AMOUNT,
			description: 'AppGoblin app SDK page',
			resource: '/apps/{id}/sdks'
		}
	},
	{
		pattern: /^\/apps\/[^/]+\/sdks\/permissions\/?$/,
		offer: {
			amount: DEFAULT_MACHINE_PAYMENT_AMOUNT,
			description: 'AppGoblin app permissions page',
			resource: '/apps/{id}/sdks/permissions'
		}
	},
	{
		pattern: /^\/apps\/[^/]+\/sdks\/queries\/?$/,
		offer: {
			amount: DEFAULT_MACHINE_PAYMENT_AMOUNT,
			description: 'AppGoblin app queries page',
			resource: '/apps/{id}/sdks/queries'
		}
	},
	{
		pattern: /^\/apps\/[^/]+\/sdks\/skadnetwork\/?$/,
		offer: {
			amount: DEFAULT_MACHINE_PAYMENT_AMOUNT,
			description: 'AppGoblin app SKAdNetwork page',
			resource: '/apps/{id}/sdks/skadnetwork'
		}
	},
	{
		pattern: /^\/apps\/[^/]+\/sdks\/unknowns\/?$/,
		offer: {
			amount: DEFAULT_MACHINE_PAYMENT_AMOUNT,
			description: 'AppGoblin app unmapped SDK page',
			resource: '/apps/{id}/sdks/unknowns'
		}
	},
	{
		pattern: /^\/apps\/comparison\/[^/]+\/?$/,
		offer: {
			amount: DEFAULT_MACHINE_PAYMENT_AMOUNT,
			description: 'AppGoblin app comparison page',
			resource: '/apps/comparison/{id}'
		}
	},
	{
		pattern: /^\/apps\/comparison\/[^/]+\/[^/]+\/?$/,
		offer: {
			amount: DEFAULT_MACHINE_PAYMENT_AMOUNT,
			description: 'AppGoblin app comparison page',
			resource: '/apps/comparison/{id1}/{id2}'
		}
	},
	{
		pattern: /^\/sdks\/[^/]+\/?$/,
		offer: {
			amount: DEFAULT_MACHINE_PAYMENT_AMOUNT,
			description: 'AppGoblin SDK pattern page',
			resource: '/sdks/{pattern}'
		}
	},
	{
		pattern: /^\/sdks\/mapped\/[^/]+\/?$/,
		offer: {
			amount: DEFAULT_MACHINE_PAYMENT_AMOUNT,
			description: 'AppGoblin SDK details page',
			resource: '/sdks/mapped/{sdkSlug}'
		}
	},
	{
		pattern: /^\/developers\/[^/]+\/sdks\/?$/,
		offer: {
			amount: DEFAULT_MACHINE_PAYMENT_AMOUNT,
			description: 'AppGoblin developer SDK page',
			resource: '/developers/{developer}/sdks'
		}
	},
	{
		pattern: /^\/reports\/app-ecosystem-report-Q2-2026\/download\/?$/,
		offer: {
			amount: DEFAULT_MACHINE_PAYMENT_AMOUNT,
			description: 'AppGoblin app ecosystem report download',
			resource: '/reports/app-ecosystem-report-Q2-2026/download'
		}
	}
];

/** URL templates for the dynamic search endpoint and one-off page offers. */
export function getMachinePaymentResources(origin: string): string[] {
	const baseUrl = new URL(origin);
	baseUrl.protocol = 'https:';
	return ['/search/{term}', ...PAGE_OFFERS.map(({ offer }) => offer.resource)].map(
		(resource) => `${baseUrl.origin}${resource}`
	);
}

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
		{
			amount: DEFAULT_MACHINE_PAYMENT_AMOUNT,
			description: 'AppGoblin search page',
			resource: '/search/{term}'
		},
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
