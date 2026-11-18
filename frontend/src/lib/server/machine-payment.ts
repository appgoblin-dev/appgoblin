import crypto from 'node:crypto';
import {
	AfterSettleAbortError,
	x402HTTPResourceServer,
	x402ResourceServer
} from '@x402/core/server';
import { createCdpFacilitatorClient } from '@coinbase/cdp-sdk/x402';
import { ExactEvmScheme } from '@x402/evm/exact/server';
import { bazaarResourceServerExtension, declareDiscoveryExtension } from '@x402/extensions/bazaar';
import { isAddress } from 'viem';
import { Mppx, Store } from 'mppx/server';
import { stripe as mppStripe } from 'mppx/stripe/server';
import {
	BLOCKCHAIN_NETWORK,
	CDP_API_KEY_ID,
	CDP_API_KEY_SECRET,
	STRIPE_BASE_DEPOSIT_ADDRESS,
	STRIPE_PROFILE_ID,
	STRIPE_SECRET_KEY,
	STRIPE_TEMPO_DEPOSIT_ADDRESS
} from '$app/env/private';

import { stripe } from './stripe.js';
import { machineJsonExample, machineJsonKind, wantsMachineJson } from './machine-json.js';
import { getMachinePaymentNetwork } from './machine-payment-network.js';
import { createX402Analytics } from './x402-analytics.js';

type X402Analytics = ReturnType<typeof createX402Analytics>;

function settlementAnalytics(transportContext: unknown): X402Analytics {
	return (
		(transportContext as { request?: { analytics?: X402Analytics } } | undefined)?.request
			?.analytics ?? null
	);
}

const BASE_PAYMENT_INTENT_NETWORK = 'base';
const DEFAULT_MACHINE_PAYMENT_AMOUNT = '0.10';
const STRIPE_API_VERSION = '2026-05-27.preview';
const BASE_USDC_ATOMIC_UNITS_PER_CENT = 10_000n;

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
			description:
				'App details and keyword scores, including ranked and description-derived keywords, for ASO research and competitor keyword analysis.',
			resource: '/apps/{id}/keywords'
		}
	},
	{
		pattern: /^\/apps\/[^/]+\/keywords\/discovery\/?$/,
		offer: {
			amount: DEFAULT_MACHINE_PAYMENT_AMOUNT,
			description:
				'App details and description-derived keyword suggestions not currently marked as ranking, for finding ASO opportunities and competitor ideas.',
			resource: '/apps/{id}/keywords/discovery'
		}
	},
	{
		pattern: /^\/apps\/[^/]+\/keywords\/ranking\/?$/,
		offer: {
			amount: DEFAULT_MACHINE_PAYMENT_AMOUNT,
			description:
				'App details and currently ranked keywords with scores, for assessing search visibility and benchmarking competitor ASO.',
			resource: '/apps/{id}/keywords/ranking'
		}
	},
	{
		pattern: /^\/apps\/[^/]+\/keywords\/compare\/?$/,
		offer: {
			amount: DEFAULT_MACHINE_PAYMENT_AMOUNT,
			description:
				'HTML comparison of selected keyword ranking histories for an app, useful for monitoring ASO performance over time.',
			resource: '/apps/{id}/keywords/compare'
		}
	},
	{
		pattern: /^\/apps\/[^/]+\/sdks\/?$/,
		offer: {
			amount: DEFAULT_MACHINE_PAYMENT_AMOUNT,
			description:
				'App details and detected SDKs, company categories, permissions, app queries and SKAdNetwork identifiers, for competitor technology and advertising analysis.',
			resource: '/apps/{id}/sdks'
		}
	},
	{
		pattern: /^\/apps\/[^/]+\/sdks\/permissions\/?$/,
		offer: {
			amount: DEFAULT_MACHINE_PAYMENT_AMOUNT,
			description:
				"App details and detected permissions, useful for comparing competitors' requested device capabilities.",
			resource: '/apps/{id}/sdks/permissions'
		}
	},
	{
		pattern: /^\/apps\/[^/]+\/sdks\/queries\/?$/,
		offer: {
			amount: DEFAULT_MACHINE_PAYMENT_AMOUNT,
			description:
				'App details and other apps queried for availability, offering clues for researching competitor integrations and ecosystem dependencies.',
			resource: '/apps/{id}/sdks/queries'
		}
	},
	{
		pattern: /^\/apps\/[^/]+\/sdks\/skadnetwork\/?$/,
		offer: {
			amount: DEFAULT_MACHINE_PAYMENT_AMOUNT,
			description:
				"App details and detected SKAdNetwork identifiers, useful for investigating an iOS app's advertising attribution ecosystem.",
			resource: '/apps/{id}/sdks/skadnetwork'
		}
	},
	{
		pattern: /^\/apps\/[^/]+\/sdks\/unknowns\/?$/,
		offer: {
			amount: DEFAULT_MACHINE_PAYMENT_AMOUNT,
			description:
				'App details and unmapped package or path patterns detected in an app, useful for further SDK and competitor technology research.',
			resource: '/apps/{id}/sdks/unknowns'
		}
	},
	{
		pattern: /^\/apps\/comparison\/[^/]+\/?$/,
		offer: {
			amount: DEFAULT_MACHINE_PAYMENT_AMOUNT,
			description:
				'HTML overview of an app, including metrics history, ratings and SDKs, for competitor benchmarking and selecting another app to compare.',
			resource: '/apps/comparison/{id}'
		}
	},
	{
		pattern: /^\/apps\/comparison\/[^/]+\/[^/]+\/?$/,
		offer: {
			amount: DEFAULT_MACHINE_PAYMENT_AMOUNT,
			description:
				"HTML comparison of two apps' metrics histories, ratings and SDKs, for competitor benchmarking.",
			resource: '/apps/comparison/{id1}/{id2}'
		}
	},
	{
		pattern: /^\/sdks\/[^/]+\/?$/,
		offer: {
			amount: DEFAULT_MACHINE_PAYMENT_AMOUNT,
			description:
				'Apps and companies associated with an SDK package or path pattern, for investigating technology adoption and competitor app stacks.',
			resource: '/sdks/{pattern}'
		}
	},
	{
		pattern: /^\/sdks\/mapped\/[^/]+\/?$/,
		offer: {
			amount: DEFAULT_MACHINE_PAYMENT_AMOUNT,
			description:
				'SDK details, owner, mapped patterns and associated apps, for researching vendors and comparing SDK adoption across apps.',
			resource: '/sdks/mapped/{sdkSlug}'
		}
	},
	{
		pattern: /^\/developers\/[^/]+\/sdks\/?$/,
		offer: {
			amount: DEFAULT_MACHINE_PAYMENT_AMOUNT,
			description:
				"HTML overview of SDKs detected across a developer's apps, for researching a competitor's portfolio and technology stack.",
			resource: '/developers/{developer}/sdks'
		}
	},
	{
		pattern: /^\/reports\/app-ecosystem-report-Q2-2026\/download\/?$/,
		offer: {
			amount: DEFAULT_MACHINE_PAYMENT_AMOUNT,
			description:
				'CSV from the Q2 2026 mobile app ecosystem report, covering SDK and app-ads.txt company adoption and trends for market and competitor analysis.',
			resource: '/reports/app-ecosystem-report-Q2-2026/download'
		}
	}
];

const stripeProfileId = STRIPE_PROFILE_ID?.trim();
const tempoDepositAddress = STRIPE_TEMPO_DEPOSIT_ADDRESS?.trim();
const baseDepositAddress = STRIPE_BASE_DEPOSIT_ADDRESS?.trim() ?? '';
const cdpApiKeyId = CDP_API_KEY_ID?.trim() ?? '';
const cdpApiKeySecret = CDP_API_KEY_SECRET?.trim() ?? '';
const paymentNetwork = BLOCKCHAIN_NETWORK?.trim()
	? getMachinePaymentNetwork(BLOCKCHAIN_NETWORK, STRIPE_SECRET_KEY)
	: null;

const missingConfiguration = (
	[
		['STRIPE_SECRET_KEY', STRIPE_SECRET_KEY],
		['BLOCKCHAIN_NETWORK', BLOCKCHAIN_NETWORK],
		['STRIPE_BASE_DEPOSIT_ADDRESS', baseDepositAddress],
		['CDP_API_KEY_ID', cdpApiKeyId],
		['CDP_API_KEY_SECRET', cdpApiKeySecret]
	] satisfies Array<[string, string | undefined]>
)
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
	paymentAddress !== null && paymentNetwork !== null
		? new x402ResourceServer(
				createCdpFacilitatorClient({ apiKeyId: cdpApiKeyId, apiKeySecret: cdpApiKeySecret })
			)
				.register(paymentNetwork.network, new ExactEvmScheme())
				.registerExtension(bazaarResourceServerExtension)
				.onAfterSettle(async ({ result, requirements, transportContext }) => {
					if (!result.success) return;
					const analytics = settlementAnalytics(transportContext);
					if (!result.transaction) {
						analytics?.settled('failed');
						analytics?.failed('stripe_recording');
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
							requirements.network !== paymentNetwork.network ||
							requirements.asset.toLowerCase() !== paymentNetwork.usdcAddress.toLowerCase()
						) {
							throw new Error('x402 settlement requires USDC on the configured Base network');
						}

						if (!paymentNetwork.recordInStripe) {
							analytics?.settled('disabled');
							console.info(
								'[MachinePayments] Base Sepolia settlement completed; Stripe recording is disabled for testnet'
							);
							return;
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

						analytics?.settled('recorded');
						console.log(
							`[MachinePayments] Recorded Stripe PaymentIntent ${paymentIntent.id} for x402 transaction ${result.transaction}`
						);
					} catch (error) {
						analytics?.settled('failed');
						analytics?.failed('stripe_recording');
						const message = error instanceof Error ? error.message : String(error);
						console.error(
							`[MachinePayments] Failed to process x402 settlement ${result.transaction}: ${message}`
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
		resourceServerInitialization = resourceServer
			.initialize()
			.then(() => {
				console.info('[MachinePayments] x402 facilitator initialized successfully');
			})
			.catch((error: unknown) => {
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

export function machinePaymentRoutePattern(resource: string, pathname: string): string {
	const route = resource.replace(/\{([a-zA-Z_][a-zA-Z0-9_]*)\}/g, ':$1');
	return `${route}${pathname.endsWith('/__data.json') ? '/__data.json' : ''}`;
}

export function isMachinePayablePath(pathname: string): boolean {
	const path = pagePath(pathname);
	return PAGE_OFFERS.some(({ pattern }) => pattern.test(path));
}

export function findPageOffer(pathname: string): MachinePageOffer | null {
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

const PATH_PARAMETER_DESCRIPTIONS: Record<string, string> = {
	term: 'Search term for apps and companies',
	id: 'App store id, eg. android com.example.app or ios 1234567890',
	id1: 'First app store id',
	id2: 'Second app store id',
	pattern: 'SDK package or path pattern',
	sdkSlug: 'AppGoblin SDK slug',
	developer: 'Developer identifier'
};

const JSON_OUTPUT_PROPERTIES: Record<string, Record<string, unknown>> = {
	search: {
		apps: {
			type: 'object',
			description: 'Matching apps grouped by Apple and Google stores, for identifying competitors.'
		},
		companies: {
			type: 'array',
			description: 'Companies matching the search term, for ecosystem and vendor research.'
		}
	},
	keywords: {
		app: { type: 'object', description: 'App details identifying the keyword subject.' },
		keywords: {
			type: ['object', 'string'],
			description:
				'Keyword terms and scores for ASO research; a message is returned when keyword data is unavailable.',
			properties: {
				keywords: { type: 'array', description: 'Keyword terms for the requested view.' },
				keyword_scores: {
					type: 'array',
					description: 'Keyword score records, including ranking and discovery indicators.'
				}
			}
		}
	},
	sdks: {
		app: { type: 'object', description: 'App details identifying the analyzed app.' },
		sdk: {
			type: 'object',
			description:
				'Detected SDK and package information, or the requested subsection, for technology analysis.',
			properties: {
				permissions: { description: 'Detected permissions requested by the app.' },
				company_categories: { description: 'Detected companies grouped by category.' },
				leftovers: { description: 'Unmapped package or path patterns for further investigation.' },
				app_queries: { description: 'Other apps queried for availability.' },
				skadnetwork: {
					description: 'Detected SKAdNetwork identifiers for advertising attribution research.'
				},
				company_details: { description: 'Details of companies associated with detected SDKs.' }
			}
		}
	},
	pattern: {
		apps: { type: 'object', description: 'Apps associated with the specified SDK pattern.' },
		companies: {
			type: 'object',
			description: 'Companies associated with the specified SDK pattern.'
		}
	},
	mapped: {
		sdk_id: { type: ['integer', 'null'], description: 'AppGoblin SDK identifier, if mapped.' },
		sdk_name: { type: 'string', description: 'Name of the SDK.' },
		apps: { type: 'array', description: 'Associated apps for researching SDK adoption.' },
		owner: { type: 'object', description: 'SDK owner details, when available.' },
		patterns: {
			type: 'object',
			description: 'Mapped package, path and mediation patterns used to identify the SDK.'
		}
	}
};

export function machinePaymentOutput(
	request: Request,
	resource: string
): {
	mimeType: string;
	serviceName: string;
	tags: string[];
	iconUrl: string;
	extensions: Record<string, unknown>;
} {
	const url = new URL(request.url);
	const kind = machineJsonKind(url.pathname);
	const isJson = kind !== null && wantsMachineJson(request);
	const isCsv = resource === '/reports/app-ecosystem-report-Q2-2026/download';
	const isDataRequest = url.pathname.endsWith('/__data.json');
	const pathProperties = Object.fromEntries(
		[...resource.matchAll(/\{([a-zA-Z_][a-zA-Z0-9_]*)\}/g)].map(([, name]) => [
			name,
			{ type: 'string', description: PATH_PARAMETER_DESCRIPTIONS[name] }
		])
	);
	const queryProperties: Record<string, unknown> = resource.endsWith('/keywords/compare')
		? { k: { type: 'string', description: 'Keywords to compare, separated by commas' } }
		: resource.startsWith('/apps/comparison/')
			? {
					search1: { type: 'string', description: 'Search term for the first app selector' },
					search2: { type: 'string', description: 'Search term for the second app selector' }
				}
			: {};
	return {
		mimeType: isDataRequest
			? 'application/json'
			: isCsv
				? 'text/csv'
				: isJson
					? 'application/json'
					: 'text/html',
		serviceName: 'AppGoblin',
		tags: ['mobile apps', 'app analytics', 'sdk'],
		iconUrl: 'https://appgoblin.info/favicon-32x32.png',
		extensions: declareDiscoveryExtension({
			inputSchema: { properties: queryProperties },
			...(Object.keys(pathProperties).length
				? {
						pathParamsSchema: { properties: pathProperties, required: Object.keys(pathProperties) }
					}
				: {}),
			...(isJson
				? {
						output: {
							example: machineJsonExample(kind, url.pathname),
							schema: { type: 'object', properties: JSON_OUTPUT_PROPERTIES[kind] }
						}
					}
				: {})
		})
	};
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

export async function initializePaymentFacilitator(
	initialize: () => Promise<void>,
	request: Request,
	mppChallenge: Response | null
): Promise<Response | null> {
	try {
		await initialize();
		return null;
	} catch (error) {
		console.error(
			'[MachinePayments] x402 facilitator initialization failed; x402 is unavailable',
			error
		);
		if (
			!request.headers.has('payment-signature') &&
			!request.headers.has('x-payment') &&
			mppChallenge
		) {
			console.warn('[MachinePayments] Returning an MPP-only challenge because x402 is unavailable');
			return mppChallenge;
		}
		return new Response(JSON.stringify({ error: 'x402_facilitator_unavailable' }), {
			status: 503,
			headers: {
				'Content-Type': 'application/json',
				'Cache-Control': 'no-store',
				'Retry-After': '60'
			}
		});
	}
}

export function unavailableX402Challenge(
	challenge: Response | null,
	missing: string[]
): Response | null {
	console.error(
		`[MachinePayments] x402 is not configured; missing configuration: ${missing.join(', ') || 'x402 resource server or payment address'}. ${challenge ? 'Returning an MPP-only challenge.' : 'No MPP challenge is available.'}`
	);
	return challenge;
}

async function chargePage(
	request: Request,
	resolve: () => Promise<Response>,
	offer: MachinePageOffer
): Promise<Response | null> {
	const analytics = createX402Analytics(request, offer.resource);
	analytics?.attempt();
	if (resourceServer === null && mppx === null) {
		analytics?.failed('configuration');
		return unavailableX402Challenge(null, missingConfiguration);
	}

	let mppPayment: Awaited<ReturnType<ReturnType<NonNullable<typeof mppx>['charge']>>> | null;
	try {
		mppPayment = mppx
			? await mppx.charge({
					amount: offer.amount,
					description: offer.description
				})(request)
			: null;
	} catch (error) {
		analytics?.failed('verification');
		throw error;
	}

	if (mppPayment !== null && mppPayment.status !== 402) {
		return mppPayment.withReceipt(await resolve());
	}

	if (resourceServer === null || paymentAddress === null || paymentNetwork === null) {
		analytics?.failed('configuration');
		return unavailableX402Challenge(mppPayment?.challenge ?? null, missingConfiguration);
	}

	const initializationFailure = await initializePaymentFacilitator(
		initializeResourceServer,
		request,
		mppPayment?.challenge ?? null
	);
	if (initializationFailure) {
		analytics?.failed('initialization');
		return initializationFailure;
	}

	const requestUrl = new URL(request.url);
	const routePattern = machinePaymentRoutePattern(offer.resource, requestUrl.pathname);
	const adapter = {
		getHeader: (name: string) => request.headers.get(name) ?? undefined,
		getMethod: () => request.method,
		getPath: () => requestUrl.pathname.replace(/\/$/, ''),
		getUrl: () => request.url,
		getAcceptHeader: () => request.headers.get('accept') ?? '',
		getUserAgent: () => request.headers.get('user-agent') ?? ''
	};
	const requestContext = {
		adapter,
		analytics,
		path: requestUrl.pathname,
		method: request.method,
		paymentHeader:
			request.headers.get('payment-signature') ?? request.headers.get('x-payment') ?? undefined
	};
	const httpServer = new x402HTTPResourceServer(resourceServer, {
		[routePattern]: {
			accepts: {
				scheme: 'exact',
				network: paymentNetwork.network,
				price: `$${offer.amount}`,
				payTo: paymentAddress
			},
			resource: request.url,
			description: offer.description,
			...machinePaymentOutput(request, offer.resource),
			unpaidResponseBody: () => ({
				contentType: 'application/json',
				body: { error: 'payment_required' }
			})
		}
	});

	let payment: Awaited<ReturnType<typeof httpServer.processHTTPRequest>>;
	try {
		payment = await httpServer.processHTTPRequest(requestContext);
	} catch (error) {
		analytics?.failed('verification');
		throw error;
	}
	if (payment.type === 'no-payment-required') {
		analytics?.failed('configuration');
		console.error('[MachinePayments] x402 route did not match the requested resource');
		return new Response(JSON.stringify({ error: 'payment_configuration_error' }), {
			status: 503,
			headers: { 'Content-Type': 'application/json', 'Cache-Control': 'no-store' }
		});
	}
	if (payment.type === 'payment-error') {
		analytics?.failed('verification');
		const x402Response = responseFromInstructions(payment.response);
		return mppPayment?.challenge
			? mergePaymentChallenges(mppPayment.challenge, x402Response)
			: x402Response;
	}

	let response: Response;
	try {
		response = await resolve();
	} catch (error) {
		analytics?.failed('handler');
		await payment.cancellationDispatcher.cancel({ reason: 'handler_threw', error });
		throw error;
	}

	if (response.status >= 400) {
		analytics?.failed('handler');
		await payment.cancellationDispatcher.cancel({
			reason: 'handler_failed',
			responseStatus: response.status
		});
		return response;
	}

	let settlement: Awaited<ReturnType<typeof httpServer.processSettlement>>;
	try {
		settlement = await httpServer.processSettlement(
			payment.paymentPayload,
			payment.paymentRequirements,
			payment.declaredExtensions,
			{ request: requestContext, responseHeaders: Object.fromEntries(response.headers.entries()) },
			undefined,
			payment.beforeHandlerSettlement
		);
	} catch (error) {
		analytics?.failed('settlement');
		throw error;
	}

	if (!settlement.success) {
		if (
			settlement.errorReason !== 'stripe_payment_intent_failed' &&
			settlement.errorReason !== 'stripe_transaction_hash_missing'
		) {
			analytics?.failed('settlement');
		}
		return responseFromInstructions(settlement.response);
	}

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

export const SEARCH_OFFER: MachinePageOffer = {
	amount: DEFAULT_MACHINE_PAYMENT_AMOUNT,
	description:
		'Search results for apps across Apple and Google stores and matching companies, useful for identifying competitors and researching the app ecosystem.',
	resource: '/search/{term}'
};

export async function machineSearchPayment(
	request: Request,
	resolve: () => Promise<Response>
): Promise<Response | null> {
	return chargePage(request, resolve, SEARCH_OFFER);
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
