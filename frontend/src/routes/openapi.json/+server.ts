import { json } from '@sveltejs/kit';

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
const paymentInfo = (description: string) => ({
	offers: [
		{ amount: '50', currency: 'usd', description, intent: 'charge', method: 'stripe' },
		{
			amount: '500000',
			currency: '0x20c0000000000000000000000000000000000000',
			description,
			intent: 'charge',
			method: 'tempo'
		}
	]
});

const appPagePath = (description: string) => ({
	get: {
		summary: description,
		'x-payment-info': paymentInfo(description),
		responses: {
			'200': { description: 'Page data' },
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
					'x-payment-info': paymentInfo('AppGoblin search page'),
					responses: {
						'200': { description: 'Search results' },
						'402': { description: 'Machine payment required' }
					}
				}
			},
			'/apps/{storeId}/keywords': appPagePath(APP_PAGE_OFFERS[0].description),
			'/apps/{storeId}/keywords/discovery': appPagePath(APP_PAGE_OFFERS[1].description),
			'/apps/{storeId}/keywords/ranking': appPagePath(APP_PAGE_OFFERS[2].description),
			'/apps/{storeId}/keywords/compare': appPagePath(APP_PAGE_OFFERS[3].description),
			'/apps/{storeId}/sdks': appPagePath(APP_PAGE_OFFERS[4].description),
			'/apps/{storeId}/sdks/permissions': appPagePath(APP_PAGE_OFFERS[5].description),
			'/apps/{storeId}/sdks/queries': appPagePath(APP_PAGE_OFFERS[6].description),
			'/apps/{storeId}/sdks/skadnetwork': appPagePath(APP_PAGE_OFFERS[7].description),
			'/apps/{storeId}/sdks/unknowns': appPagePath(APP_PAGE_OFFERS[8].description),
			'/apps/comparison/{storeId}': appPagePath(APP_PAGE_OFFERS[9].description)
		}
	});
