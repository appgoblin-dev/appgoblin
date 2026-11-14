import { json } from '@sveltejs/kit';
import { machineJsonExample, type MachineJsonKind } from '#lib/server/machine-json.js';

const APP_PAGE_OFFERS = [
	{ description: 'AppGoblin app keywords page' },
	{ description: 'AppGoblin app keyword discovery page' },
	{ description: 'AppGoblin app keyword ranking page' },
	{ description: 'AppGoblin app keyword compare page' },
	{ description: 'AppGoblin app SDK page' },
	{ description: 'AppGoblin app permissions page' },
	{ description: 'AppGoblin app queries page' },
	{ description: 'AppGoblin app SKAdNetwork page' },
	{ description: 'AppGoblin app unmapped SDK page' },
	{ description: 'AppGoblin app comparison page' }
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

const appPagePath = (description: string, kind?: MachineJsonKind, path = '') => ({
	get: {
		summary: description,
		'x-payment-info': paymentInfo(description, kind, path),
		responses: {
			'200': kind
				? {
						description: 'Page data',
						content: {
							'application/json': { example: machineJsonExample(kind, path) },
							'text/html': {}
						}
					}
				: { description: 'Page data' },
			'401': { description: 'Sign in required (browsers)' },
			'402': { description: 'Machine payment required' }
		}
	}
});

export const GET = () =>
	json({
		openapi: '3.1.0',
		info: {
			title: 'AppGoblin Search',
			version: '1.0.0'
		},
		'x-service-info': {
			categories: ['search'],
			docs: {
				homepage: 'https://appgoblin.info',
				apiReference: 'https://appgoblin.info/api-docs'
			}
		},
		paths: {
			'/search/{term}': {
				get: {
					summary: 'Search AppGoblin apps and companies',
					parameters: [
						{
							name: 'term',
							in: 'path',
							required: true,
							schema: { type: 'string' }
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
			'/apps/{storeId}/keywords': appPagePath(APP_PAGE_OFFERS[0].description, 'keywords'),
			'/apps/{storeId}/keywords/discovery': appPagePath(APP_PAGE_OFFERS[1].description, 'keywords'),
			'/apps/{storeId}/keywords/ranking': appPagePath(APP_PAGE_OFFERS[2].description, 'keywords'),
			'/apps/{storeId}/keywords/compare': appPagePath(APP_PAGE_OFFERS[3].description),
			'/apps/{storeId}/sdks': appPagePath(APP_PAGE_OFFERS[4].description, 'sdks'),
			'/apps/{storeId}/sdks/permissions': appPagePath(
				APP_PAGE_OFFERS[5].description,
				'sdks',
				'/permissions'
			),
			'/apps/{storeId}/sdks/queries': appPagePath(
				APP_PAGE_OFFERS[6].description,
				'sdks',
				'/queries'
			),
			'/apps/{storeId}/sdks/skadnetwork': appPagePath(
				APP_PAGE_OFFERS[7].description,
				'sdks',
				'/skadnetwork'
			),
			'/apps/{storeId}/sdks/unknowns': appPagePath(
				APP_PAGE_OFFERS[8].description,
				'sdks',
				'/unknowns'
			),
			'/apps/comparison/{storeId}': appPagePath(APP_PAGE_OFFERS[9].description),
			'/sdks/{pattern}': appPagePath('AppGoblin SDK pattern page', 'pattern'),
			'/sdks/mapped/{sdkSlug}': appPagePath('AppGoblin SDK details page', 'mapped')
		}
	});
