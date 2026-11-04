import crypto from 'node:crypto';
import {
	AfterSettleAbortError,
	HTTPFacilitatorClient,
	x402HTTPResourceServer,
	x402ResourceServer
} from '@x402/core/server';
import { createFacilitatorConfig } from '@coinbase/x402';
import { ExactEvmScheme } from '@x402/evm/exact/server';
import { isAddress } from 'viem';
import { Mppx, Store } from 'mppx/server';
import { stripe as mppStripe } from 'mppx/stripe/server';
import {
	CDP_API_KEY_ID,
	CDP_API_KEY_SECRET,
	STRIPE_BASE_DEPOSIT_ADDRESS,
	STRIPE_PROFILE_ID,
	STRIPE_SECRET_KEY,
	STRIPE_TEMPO_DEPOSIT_ADDRESS
} from '$app/env/private';

import { stripe } from './stripe.js';

const BASE_NETWORK = 'eip155:8453';
const BASE_PAYMENT_INTENT_NETWORK = 'base';
const DEFAULT_MACHINE_PAYMENT_AMOUNT = '0.10';
const STRIPE_API_VERSION = '2026-05-27.preview';
const BASE_USDC_ATOMIC_UNITS_PER_CENT = 10_000n;
const BASE_USDC_TOKEN_ADDRESS = '0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913';

interface MachinePageOffer {
	amount: string;
	description: string;
	resource: string;
}

/** Only non-account-scoped pages are offered for one-off machine payments. */
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

const stripeProfileId = STRIPE_PROFILE_ID?.trim();
const tempoDepositAddress = STRIPE_TEMPO_DEPOSIT_ADDRESS?.trim();
const baseDepositAddress = STRIPE_BASE_DEPOSIT_ADDRESS?.trim() ?? '';
const cdpApiKeyId = CDP_API_KEY_ID?.trim() ?? '';
const cdpApiKeySecret = CDP_API_KEY_SECRET?.trim() ?? '';

const missingConfiguration = [
	['STRIPE_SECRET_KEY', STRIPE_SECRET_KEY],
	['STRIPE_BASE_DEPOSIT_ADDRESS', baseDepositAddress],
	['CDP_API_KEY_ID', cdpApiKeyId],
	['CDP_API_KEY_SECRET', cdpApiKeySecret]
]
	.filter(([, value]) => !value?.trim())
	.map(([name]) => name);

if (missingConfiguration.length > 0) {
	console.warn(
		`[MachinePayments] x402 payments are disabled; missing configuration: ${missingConfiguration.join(', ')}`
	);
}

const paymentAddress =
	missingConfiguration.length === 0 && isAddress(baseDepositAddress)
		? baseDepositAddress.toLowerCase()
		: null;

if (missingConfiguration.length === 0 && paymentAddress === null) {
	throw new Error('[MachinePayments] STRIPE_BASE_DEPOSIT_ADDRESS is not a valid EVM address');
}

const resourceServer =
	paymentAddress !== null
		? new x402ResourceServer(
				new HTTPFacilitatorClient(createFacilitatorConfig(cdpApiKeyId, cdpApiKeySecret))
			)
				.register(BASE_NETWORK, new ExactEvmScheme())
				.onAfterSettle(async ({ result, requirements }) => {
					if (!result.success) return;
					if (!result.transaction) {
						throw new AfterSettleAbortError(
							'stripe_transaction_hash_missing',
							'The facilitator settled the payment without returning a transaction hash'
						);
					}

					try {
						const atomicAmount = BigInt(requirements.amount);
						const cents = Number(
							(atomicAmount + BASE_USDC_ATOMIC_UNITS_PER_CENT / 2n) /
								BASE_USDC_ATOMIC_UNITS_PER_CENT
						);
						if (!Number.isSafeInteger(cents) || cents < 1) {
							throw new Error(`Unsupported Stripe amount derived from ${requirements.amount}`);
						}

						if (
							requirements.network !== BASE_NETWORK ||
							requirements.asset.toLowerCase() !== BASE_USDC_TOKEN_ADDRESS.toLowerCase()
						) {
							throw new Error('Stripe transaction verification requires Base USDC');
						}

						const paymentIntent = await stripe.rawRequest(
							'POST',
							'/v1/payment_intents',
							{
								amount: cents,
								currency: 'usd',
								confirm: true,
								payment_method_data: { type: 'crypto' },
								allowed_payment_method_types: ['crypto'],
								payment_method_options: {
									crypto: {
										mode: 'transaction_verification',
										transaction_verification_options: {
											network: BASE_PAYMENT_INTENT_NETWORK,
											transaction_hash: result.transaction
										}
									}
								}
							},
							{
								apiVersion: STRIPE_API_VERSION,
								idempotencyKey: result.transaction
							}
						);

						console.log(
							`[MachinePayments] Recorded Stripe PaymentIntent ${paymentIntent.id} for x402 transaction ${result.transaction}`
						);
					} catch (error) {
						const message = error instanceof Error ? error.message : String(error);
						console.error(
							`[MachinePayments] Failed to record x402 transaction ${result.transaction} with Stripe: ${message}`
						);
						throw new AfterSettleAbortError('stripe_payment_intent_failed', message);
					}
				})
		: null;

const machinePayments =
	STRIPE_SECRET_KEY.trim() && stripeProfileId
		? mppStripe.create({
				client: stripe,
				networkId: stripeProfileId,
				livemode: !STRIPE_SECRET_KEY.includes('_test_'),
				depositAddresses: tempoDepositAddress ? { tempo: tempoDepositAddress } : undefined,
				store: Store.memory()
			})
		: null;

if (machinePayments === null) {
	const missingMppConfiguration = [
		['STRIPE_SECRET_KEY', STRIPE_SECRET_KEY],
		['STRIPE_PROFILE_ID', stripeProfileId]
	]
		.filter(([, value]) => !value?.trim())
		.map(([name]) => name);
	console.warn(
		`[MachinePayments] MPP payments are disabled; missing configuration: ${missingMppConfiguration.join(', ')}`
	);
}

const mppx = machinePayments
	? Mppx.create({
			methods: machinePayments.defaultMethods(),
			secretKey: crypto
				.createHmac('sha256', STRIPE_SECRET_KEY)
				.update('mpp-challenge-signing')
				.digest('base64')
		})
	: null;

let resourceServerInitialization: Promise<void> | null = null;

async function initializeResourceServer(): Promise<void> {
	if (resourceServer === null) return;
	if (resourceServerInitialization === null) {
		resourceServerInitialization = resourceServer.initialize().catch((error: unknown) => {
			resourceServerInitialization = null;
			throw error;
		});
	}
	await resourceServerInitialization;
}

export function getMachinePaymentResources(origin: string): string[] {
	const baseUrl = new URL(origin);
	baseUrl.protocol = 'https:';
	return ['/search/{term}', ...PAGE_OFFERS.map(({ offer }) => offer.resource)].map(
		(resource) => `${baseUrl.origin}${resource}`
	);
}

// Match SvelteKit data requests to their page routes.
function pagePath(pathname: string): string {
	return pathname.replace(/\/__data\.json$/, '');
}

export function isMachinePayablePath(pathname: string): boolean {
	const path = pagePath(pathname);
	return PAGE_OFFERS.some(({ pattern }) => pattern.test(path));
}

function findPageOffer(pathname: string): MachinePageOffer | null {
	const path = pagePath(pathname);
	return PAGE_OFFERS.find(({ pattern }) => pattern.test(path))?.offer ?? null;
}

export function isMachinePaymentConfigured(): boolean {
	return resourceServer !== null || mppx !== null;
}

function responseFromInstructions(instructions: {
	status: number;
	headers: Record<string, string>;
	body?: unknown;
}): Response {
	const body =
		instructions.body === undefined || instructions.body === null
			? null
			: typeof instructions.body === 'string'
				? instructions.body
				: JSON.stringify(instructions.body);
	return new Response(body, {
		status: instructions.status,
		headers: instructions.headers
	});
}

function mergePaymentChallenges(mppChallenge: Response, x402Challenge: Response): Response {
	const headers = new Headers(x402Challenge.headers);
	const challenge = mppChallenge.headers.get('WWW-Authenticate');
	if (challenge) headers.append('WWW-Authenticate', challenge);
	headers.set('Cache-Control', 'no-store');
	return new Response(x402Challenge.body, {
		headers,
		status: x402Challenge.status,
		statusText: x402Challenge.statusText
	});
}

async function chargePage(
	request: Request,
	resolve: () => Promise<Response>,
	offer: MachinePageOffer
): Promise<Response | null> {
	if (resourceServer === null && mppx === null) return null;

	const mppPayment = mppx
		? await mppx.charge({
				amount: offer.amount,
				description: offer.description
			})(request)
		: null;

	if (mppPayment !== null && mppPayment.status !== 402) {
		return mppPayment.withReceipt(await resolve());
	}

	if (resourceServer === null || paymentAddress === null) {
		return mppPayment?.challenge ?? null;
	}

	await initializeResourceServer();

	const requestUrl = new URL(request.url);
	const adapter = {
		getHeader: (name: string) => request.headers.get(name) ?? undefined,
		getMethod: () => request.method,
		getPath: () => requestUrl.pathname,
		getUrl: () => request.url,
		getAcceptHeader: () => request.headers.get('accept') ?? '',
		getUserAgent: () => request.headers.get('user-agent') ?? ''
	};
	const requestContext = {
		adapter,
		path: requestUrl.pathname,
		method: request.method,
		paymentHeader:
			request.headers.get('payment-signature') ?? request.headers.get('x-payment') ?? undefined
	};
	const httpServer = new x402HTTPResourceServer(resourceServer, {
		'*': {
			accepts: {
				scheme: 'exact',
				network: BASE_NETWORK,
				price: `$${offer.amount}`,
				payTo: paymentAddress
			},
			resource: request.url,
			description: offer.description,
			mimeType: 'text/html',
			unpaidResponseBody: () => ({
				contentType: 'application/json',
				body: { error: 'payment_required' }
			})
		}
	});

	const payment = await httpServer.processHTTPRequest(requestContext);
	if (payment.type === 'no-payment-required') return resolve();
	if (payment.type === 'payment-error') {
		const x402Response = responseFromInstructions(payment.response);
		return mppPayment?.challenge
			? mergePaymentChallenges(mppPayment.challenge, x402Response)
			: x402Response;
	}

	let response: Response;
	try {
		response = await resolve();
	} catch (error) {
		await payment.cancellationDispatcher.cancel({ reason: 'handler_threw', error });
		throw error;
	}

	if (response.status >= 400) {
		await payment.cancellationDispatcher.cancel({
			reason: 'handler_failed',
			responseStatus: response.status
		});
		return response;
	}

	const settlement = await httpServer.processSettlement(
		payment.paymentPayload,
		payment.paymentRequirements,
		payment.declaredExtensions,
		{ request: requestContext, responseHeaders: Object.fromEntries(response.headers.entries()) },
		undefined,
		payment.beforeHandlerSettlement
	);

	if (!settlement.success) return responseFromInstructions(settlement.response);

	const headers = new Headers(response.headers);
	for (const [name, value] of Object.entries(settlement.headers)) {
		headers.set(name, value);
	}

	return new Response(response.body, {
		status: response.status,
		statusText: response.statusText,
		headers
	});
}

export async function machineSearchPayment(
	request: Request,
	resolve: () => Promise<Response>
): Promise<Response | null> {
	return chargePage(request, resolve, {
		amount: DEFAULT_MACHINE_PAYMENT_AMOUNT,
		description: 'AppGoblin search page',
		resource: '/search/{term}'
	});
}

export async function machinePagePayment(
	request: Request,
	resolve: () => Promise<Response>
): Promise<Response | null> {
	if (request.method !== 'GET' && request.method !== 'HEAD') return null;
	const offer = findPageOffer(new URL(request.url).pathname);
	if (offer === null) return null;
	return chargePage(request, resolve, offer);
}
