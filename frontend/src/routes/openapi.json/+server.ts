import { json } from '@sveltejs/kit';

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
					'x-payment-info': {
						offers: [
							{
								amount: '50',
								currency: 'usd',
								description: 'AppGoblin search page',
								intent: 'charge',
								method: 'stripe'
							},
							{
								amount: '500000',
								currency: '0x20c0000000000000000000000000000000000000',
								description: 'AppGoblin search page',
								intent: 'charge',
								method: 'tempo'
							}
						]
					},
					responses: {
						'200': { description: 'Search results' },
						'402': { description: 'Machine payment required' }
					}
				}
			}
		}
	});
