import assert from 'node:assert/strict';
import { test } from 'node:test';
import { createServer } from 'vite';

test('API apps navigation is shown only when an API signal is available', async () => {
	const server = await createServer({ server: { middlewareMode: true }, appType: 'custom' });
	try {
		const { companySectionHasData } = await server.ssrLoadModule(
			'/src/lib/utils/companySectionAvailability.ts'
		);
		assert.equal(companySectionHasData('api-apps', null), false);
		assert.equal(companySectionHasData('api-apps', { has_api_signal: false }), false);
		assert.equal(companySectionHasData('api-apps', { has_api_signal: true }), true);
	} finally {
		await server.close();
	}
});
