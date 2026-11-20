import { json } from '@sveltejs/kit';
import { machineJsonExample, type MachineJsonKind } from '#lib/server/machine-json.js';

const APP_PAGE_OFFERS = [
	{
		summary: 'Get app keyword intelligence',
		description:
			'AppGoblin mobile app intelligence for Google Play and Apple App Store apps: app details and ranked or description-derived keyword scores for ASO research and competitor keyword analysis.'
	},
	{
		summary: 'Discover app keyword opportunities',
		description:
			'AppGoblin mobile app intelligence for Google Play and Apple App Store apps: description-derived keyword suggestions that are not currently ranked, useful for finding ASO opportunities.'
	},
	{
		summary: 'Get currently ranked app keywords',
		description:
			'AppGoblin mobile app intelligence for Google Play and Apple App Store apps: app details and currently ranked keyword scores for search visibility analysis and competitor benchmarking.'
	},
	{
		summary: 'Compare app keyword ranking histories',
		description:
			'AppGoblin mobile app intelligence for Google Play and Apple App Store apps: HTML comparison of selected keyword ranking histories for one app over time.'
	},
	{
		summary: 'Get app SDK intelligence',
		description:
			'AppGoblin mobile app intelligence for Google Play and Apple App Store apps: app details and detected SDKs, categories, permissions, app queries, and SKAdNetwork identifiers.'
	},
	{
		summary: 'Get app permissions',
		description:
			'AppGoblin mobile app intelligence for Google Play and Apple App Store apps: detected Android permissions and iOS usage declarations for competitor capability analysis.'
	},
	{
		summary: 'Get app query declarations',
		description:
			'AppGoblin mobile app intelligence for Google Play and Apple App Store apps: package or URL schemes queried for availability, indicating possible integrations and dependencies.'
	},
	{
		summary: 'Get app SKAdNetwork identifiers',
		description:
			'AppGoblin mobile app intelligence for Apple App Store apps: detected iOS SKAdNetwork identifiers for advertising attribution ecosystem research.'
	},
	{
		summary: 'Get unmapped app SDK patterns',
		description:
			'AppGoblin mobile app intelligence for Google Play and Apple App Store apps: unmapped package or path patterns detected during SDK analysis.'
	},
	{
		summary: 'Get app comparison overview',
		description:
			'AppGoblin mobile app intelligence for Google Play and Apple App Store apps: app metrics history, ratings, and SDK signals for competitor benchmarking.'
	}
];

/** Payment offers for one page: Stripe in cents, then Tempo in token units. */
const paymentInfo = (description: string, kind?: MachineJsonKind, path = '') => ({
	...(kind ? { output: { type: 'json', example: machineJsonExample(kind, path) } } : {}),
	offers: [
		{ amount: '10', currency: 'usd', description, intent: 'charge', method: 'stripe' },
		{
			amount: '100000',
			currency: '0x20c0000000000000000000000000000000000000',
			description,
			intent: 'charge',
			method: 'tempo'
		}
	]
});

type PathParameter = {
	name: string;
	in: 'path';
	required: true;
	description: string;
	schema: { type: 'string' };
	examples: { example: { value: string } };
};

const appPagePath = (
	description: string,
	kind?: MachineJsonKind,
	path = '',
	summary?: string,
	parameter: PathParameter | PathParameter[] = {
		name: 'storeId',
		in: 'path',
		required: true,
		description: 'App store identifier, for example com.example.app.',
		schema: { type: 'string' },
		examples: { example: { value: 'com.example.app' } }
	}
) => ({
	get: {
		summary: summary ?? description,
		description,
		parameters: Array.isArray(parameter) ? parameter : [parameter],
		'x-payment-info': paymentInfo(description, kind, path),
		responses: {
			'200': kind
				? {
						description: 'Machine-readable page data or HTML',
						content: {
							'application/json': { example: machineJsonExample(kind, path) },
							'text/html': {}
						}
					}
				: { description: 'HTML page data' },
			'401': { description: 'Sign in required (browsers)' },
			'402': { description: 'Machine payment required' }
		}
	}
});

export const GET = () =>
	json({
		openapi: '3.1.0',
		info: {
			title: 'AppGoblin Machine-Readable Pages',
			version: '1.1.0',
			description:
				'AppGoblin is a mobile app intelligence tool covering Google Play and Apple App Store app data, SDK usage, keyword rankings, app-store trends, and developer ecosystems. This catalog exposes machine-readable HTML and JSON endpoints for search and competitive intelligence. Non-browser clients can pay $0.10 using x402 or MPP; browser requests require account sign-in.'
		},
		'x-service-info': {
			categories: ['search', 'mobile-app-intelligence', 'sdk-intelligence'],
			docs: {
				homepage: 'https://appgoblin.info',
				apiReference: 'https://appgoblin.info/api-docs',
				llms: 'https://appgoblin.info/llms.txt',
				openapi: 'https://appgoblin.info/openapi.json'
			}
		},
		paths: {
			'/search/{term}': {
				get: {
					summary: 'Search AppGoblin apps and companies',
					description:
						'Search AppGoblin mobile app intelligence across Google Play and Apple App Store listings and matching company domains. Machine clients receive JSON with Accept: application/json; otherwise the page may return HTML.',
					parameters: [
						{
							name: 'term',
							in: 'path',
							required: true,
							description: 'App or company search term.',
							schema: { type: 'string' },
							examples: { example: { value: 'music' } }
						}
					],
					'x-payment-info': paymentInfo('AppGoblin search page', 'search'),
					responses: {
						'200': {
							description: 'Search results',
							content: {
								'application/json': { example: machineJsonExample('search', '/search/{term}') },
								'text/html': {}
							}
						},
						'402': { description: 'Machine payment required' }
					}
				}
			},
			'/reports/app-ecosystem-report-Q2-2026/download': {
				get: {
					summary: 'Download the Q2 2026 app ecosystem CSV',
					description:
						'AppGoblin mobile app intelligence for Google Play and Apple App Store data: CSV containing SDK and app-ads.txt company adoption and trends for market and competitor analysis.',
					'x-payment-info': paymentInfo(
						'Q2 2026 mobile app ecosystem report CSV',
						undefined,
						'/reports/app-ecosystem-report-Q2-2026/download'
					),
					responses: {
						'200': {
							description: 'CSV report download',
							content: { 'text/csv': {} }
						},
						'401': { description: 'Sign in required (browsers)' },
						'402': { description: 'Machine payment required' }
					}
				}
			},
			'/apps/{storeId}/keywords': appPagePath(
				APP_PAGE_OFFERS[0].description,
				'keywords',
				'',
				APP_PAGE_OFFERS[0].summary
			),
			'/apps/{storeId}/keywords/discovery': appPagePath(
				APP_PAGE_OFFERS[1].description,
				'keywords',
				'/discovery',
				APP_PAGE_OFFERS[1].summary
			),
			'/apps/{storeId}/keywords/ranking': appPagePath(
				APP_PAGE_OFFERS[2].description,
				'keywords',
				'/ranking',
				APP_PAGE_OFFERS[2].summary
			),
			'/apps/{storeId}/keywords/compare': appPagePath(
				APP_PAGE_OFFERS[3].description,
				undefined,
				'',
				APP_PAGE_OFFERS[3].summary
			),
			'/apps/{storeId}/sdks': appPagePath(
				APP_PAGE_OFFERS[4].description,
				'sdks',
				'',
				APP_PAGE_OFFERS[4].summary
			),
			'/apps/{storeId}/sdks/permissions': appPagePath(
				APP_PAGE_OFFERS[5].description,
				'sdks',
				'/permissions',
				APP_PAGE_OFFERS[5].summary
			),
			'/apps/{storeId}/sdks/queries': appPagePath(
				APP_PAGE_OFFERS[6].description,
				'sdks',
				'/queries',
				APP_PAGE_OFFERS[6].summary
			),
			'/apps/{storeId}/sdks/skadnetwork': appPagePath(
				APP_PAGE_OFFERS[7].description,
				'sdks',
				'/skadnetwork',
				APP_PAGE_OFFERS[7].summary
			),
			'/apps/{storeId}/sdks/unknowns': appPagePath(
				APP_PAGE_OFFERS[8].description,
				'sdks',
				'/unknowns',
				APP_PAGE_OFFERS[8].summary
			),
			'/apps/comparison/{storeId}': appPagePath(
				APP_PAGE_OFFERS[9].description,
				undefined,
				'',
				APP_PAGE_OFFERS[9].summary
			),
			'/apps/comparison/{storeId1}/{storeId2}': appPagePath(
				'AppGoblin mobile app intelligence for Google Play and Apple App Store apps: side-by-side metrics, ratings, and SDK comparison for two app-store identifiers.',
				undefined,
				'',
				'Compare two apps',
				[
					{
						name: 'storeId1',
						in: 'path',
						required: true,
						description: 'First app store identifier.',
						schema: { type: 'string' },
						examples: { example: { value: 'com.example.app' } }
					},
					{
						name: 'storeId2',
						in: 'path',
						required: true,
						description: 'Second app store identifier.',
						schema: { type: 'string' },
						examples: { example: { value: '123456789' } }
					}
				]
			),
			'/sdks/{pattern}': appPagePath(
				'AppGoblin mobile app intelligence for Google Play and Apple App Store apps: apps and companies associated with an SDK package or path pattern.',
				'pattern',
				'',
				'Get SDK pattern adoption',
				{
					name: 'pattern',
					in: 'path',
					required: true,
					description: 'SDK package or path pattern.',
					schema: { type: 'string' },
					examples: { example: { value: 'com.google.firebase' } }
				}
			),
			'/sdks/mapped/{sdkSlug}': appPagePath(
				'AppGoblin mobile app intelligence for Google Play and Apple App Store apps: SDK details, owner, mapped package patterns, and associated apps.',
				'mapped',
				'',
				'Get mapped SDK details',
				{
					name: 'sdkSlug',
					in: 'path',
					required: true,
					description: 'AppGoblin SDK slug.',
					schema: { type: 'string' },
					examples: { example: { value: 'firebase' } }
				}
			),
			'/developers/{developer}/sdks': appPagePath(
				"AppGoblin mobile app intelligence for Google Play and Apple App Store apps: SDKs detected across a developer's app portfolio.",
				undefined,
				'',
				'Get developer SDK portfolio',
				{
					name: 'developer',
					in: 'path',
					required: true,
					description: 'AppGoblin developer identifier or domain.',
					schema: { type: 'string' },
					examples: { example: { value: 'google.com' } }
				}
			)
		}
	});
