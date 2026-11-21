/* eslint-disable @typescript-eslint/ban-ts-comment */
// @ts-nocheck
import assert from 'node:assert/strict';
import { test } from 'node:test';
import { createServer } from 'vite';

test('company API overview displays recent observations without iOS or monthly installs', async () => {
	const server = await createServer({ server: { middlewareMode: true }, appType: 'custom' });
	try {
		const { default: Page } = await server.ssrLoadModule(
			'/src/routes/companies/[domain]/api-calls/+page.svelte'
		);
		const { render } = await server.ssrLoadModule('svelte/server');
		const data = {
			companyTree: { company_name: 'Example', is_secondary_domain: false },
			tabIndicators: { is_parent_domain: false },
			companyDetails: { domain_overview: { categories: { all: { api_android_total_apps: 42 } } } },
			apiApps: {
				android: { apps: [] },
				response_types: [
					{
						company_domain: 'example.com',
						tld_url: 'api.example.com',
						response_type: 'image/png',
						app_count_30d: 1250,
						observed_call_count_30d: 2400,
						app_count_alltime: 1500,
						observed_call_count_alltime: 3000
					},
					{
						company_domain: 'example.com',
						tld_url: null,
						response_type: '(unknown)',
						app_count_30d: 0,
						observed_call_count_30d: 0,
						app_count_alltime: 3,
						observed_call_count_alltime: 8
					}
				],
				recent_endpoints: [
					{ host: 'api.example.com', path: '/api/users', last_seen: '2026-01-01T00:00:00Z' }
				],
				recent_requests: [
					{
						store_id: 'com.example.app',
						name: 'Example App',
						icon_64: 'icon.png',
						host: 'api.example.com',
						path: '/v1/other',
						response_mime_type: 'application/json',
						called_at: '2026-01-02T00:00:00Z'
					},
					{
						store_id: 'com.example.app',
						name: 'Example App',
						icon_64: null,
						host: 'api.example.com',
						path: '/v1/second',
						response_mime_type: null,
						called_at: '2026-01-01T12:00:00Z'
					}
				]
			}
		};
		const html = render(Page, { props: { data } }).body;
		assert.match(html, /API response types/);
		assert.doesNotMatch(html, /Company domain/);
		assert.match(html, /image\/png/);
		assert.match(html, /1,250/);
		assert.match(html, /2,400/);
		assert.match(html, /\(unknown\)/);
		assert.match(html, /api\.example\.com\/api\/users/);
		assert.match(html, /Example App/);
		assert.match(html, /app-icons\/com\.example\.app\/icon\.png/);
		assert.match(html, /api\.example\.com\/v1\/other/);
		assert.match(html, /api\.example\.com\/v1\/second/);
		assert.match(html, /application\/json/);
		assert.match(html, /\/apps\/com\.example\.app\/data-flows/);
		assert.match(html, /42 apps with API calls/);
		assert.doesNotMatch(html, /API activity overview/);
		assert.doesNotMatch(html, /iOS|Monthly Android installs|Top Apps/);
		data.apiApps.response_types = [];
		data.apiApps.recent_endpoints = [];
		data.apiApps.recent_requests = [];
		const emptyHtml = render(Page, { props: { data } }).body;
		assert.match(emptyHtml, /No response type data available/);
		assert.match(emptyHtml, /No recent endpoints available/);
		assert.match(emptyHtml, /No recent requests available/);
	} finally {
		await server.close();
	}
});
