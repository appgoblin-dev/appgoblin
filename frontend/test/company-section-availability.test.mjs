/* eslint-disable @typescript-eslint/ban-ts-comment */
// @ts-nocheck
import assert from 'node:assert/strict';
import { after, before, test } from 'node:test';
import { createServer } from 'vite';

let server, hasData;
before(async () => {
	server = await createServer({ server: { middlewareMode: true }, appType: 'custom' });
	({ companySectionHasData: hasData } = await server.ssrLoadModule(
		'/src/lib/utils/companySectionAvailability.ts'
	));
});
after(async () => {
	await server?.close();
});

test('missing indicators retain navigation fallback and independently available mediation partners', () => {
	for (const slug of ['overview', 'app-adstxt', 'data-exports'])
		assert.equal(hasData(slug, null), true);
	for (const slug of ['sdks', 'trends', 'apps-added', 'mediation'])
		assert.equal(hasData(slug, null), false);
	assert.equal(hasData('mediation-partners', null, 1), true);
	assert.equal(hasData('mediation-partners', null, 0), false);
});

test('section links follow their corresponding data indicators', () => {
	const indicators = {
		creatives_app_count: 1,
		has_trends: 1,
		sdk_count: 0,
		mediation_adapter_count: 0,
		apps_sdk_added_count: 3,
		apps_sdk_lost_count: 0,
		apps_adstxt_direct_added_count: 0,
		apps_adstxt_direct_lost_count: 2,
		adstxt_direct_app_count: 0,
		adstxt_parent_app_count: 4,
		has_api_signal: false
	};
	for (const slug of [
		'creatives',
		'trends',
		'apps-added',
		'apps-lost-adstxt',
		'app-adstxt',
		'data-exports'
	])
		assert.equal(hasData(slug, indicators), true, slug);
	for (const slug of ['sdks', 'mediation', 'apps-lost', 'apps-added-adstxt'])
		assert.equal(hasData(slug, indicators), false, slug);
	assert.equal(hasData('mediation-partners', indicators, 1), true);
	assert.equal(hasData('data-exports', { ...indicators, adstxt_parent_app_count: 0 }), false);
	assert.equal(
		hasData('data-exports', { ...indicators, adstxt_parent_app_count: 0, has_api_signal: true }),
		true
	);
});
