/* eslint-disable @typescript-eslint/ban-ts-comment */
// @ts-nocheck
import assert from 'node:assert/strict';
import { test } from 'node:test';
import { createServer } from 'vite';

test('pattern company links each distinct mapped SDK and tolerates missing slugs', async () => {
	const server = await createServer({ server: { middlewareMode: true }, appType: 'custom' });
	try {
		const { default: Component } = await server.ssrLoadModule('/src/lib/SDKPatternCompany.svelte');
		const { render } = await server.ssrLoadModule('svelte/server');
		const match = {
			company_name: 'Example',
			company_domain: 'example.com',
			company_logo_url: null,
			parent_company_name: null,
			parent_company_domain: null,
			pattern_type: 'package',
			pattern_value: 'com.example',
			app_count: 10,
			sdk_name: 'Adjust SDK',
			sdk_slug: 'adjust-sdk'
		};
		const html = render(Component, {
			props: {
				pattern: 'example',
				matches: [
					match,
					match,
					{ ...match, sdk_slug: 'other-sdk', sdk_name: 'Other SDK' },
					{ ...match, sdk_slug: null }
				]
			}
		}).body;
		assert.equal((html.match(/href="\/sdks\/mapped\/adjust-sdk"/g) ?? []).length, 1);
		assert.match(html, /href="\/sdks\/mapped\/other-sdk"/);
		assert.match(html, /View Adjust SDK/);
		assert.match(html, /Most-matched SDK part/);
		assert.match(html, /Prefix \/ wildcard matches/);
		assert.match(html, /example\*/);
		assert.match(html, /10 apps/);
		assert.match(html, /grid-cols-1 sm:grid-cols-2 xl:grid-cols-3/);
		assert.ok(html.indexOf('10 apps') < html.indexOf('com.example'));
		const multipleCompanies = render(Component, {
			props: {
				pattern: 'example',
				matches: [
					match,
					{
						...match,
						company_name: 'Another Company',
						company_domain: 'another.example',
						sdk_name: 'Another SDK',
						sdk_slug: 'another-sdk',
						pattern_value: 'com.another'
					}
				]
			}
		}).body;
		assert.match(multipleCompanies, /Matching Companies \(2\)/);
		assert.match(multipleCompanies, /Another Company/);
		assert.match(multipleCompanies, /href="\/sdks\/mapped\/another-sdk"/);
		const noSlug = render(Component, {
			props: { pattern: 'example', matches: [{ ...match, sdk_slug: null }] }
		}).body;
		assert.doesNotMatch(noSlug, /\/sdks\/mapped\//);
		assert.match(noSlug, /Adjust SDK/);
	} finally {
		await server.close();
	}
});
